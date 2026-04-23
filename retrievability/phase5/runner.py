"""Phase 5 pilot runner.

Drives the end-to-end LLM ground-truth pipeline against a small list
of URLs (pilot: N=5). For each URL:

    fetch HTML -> extract title + clean text
      -> generator (Mistral) -> Q/A pairs
      -> review (auto-accept by default; --review for interactive)
      -> scorer primary (GPT-4.1) -> answers
      -> grader -> per-page accuracy

No Spearman correlation yet — N=5 can't produce meaningful rho. That
step is added for the full N=60 run.

Outputs under <out_dir>/<slug>/:
    page.raw.html              raw httpx snapshot
    page.rendered.html         Playwright headless-Chromium snapshot
    page.raw.txt               readability extract from raw HTML
    page.rendered.txt          readability extract from rendered HTML
    fetch.raw.json             raw fetch metadata (status, bytes, elapsed_s)
    fetch.rendered.json        rendered fetch metadata (+ hydration_signal)
    generator.prompt.txt       Q/A generation prompt
    generator.raw.json         Q/A generator response
    qapairs.json               approved ground-truth pairs
    review.json                review audit trail
    scoring.primary.raw.json   scoring-LLM answers vs raw extract
    scoring.primary.rendered.json  scoring-LLM answers vs rendered extract
    grades.primary.raw.json    substring grades vs raw
    grades.primary.rendered.json   substring grades vs rendered
    grades.primary.judged.{raw,rendered}.json   LLM-judge grades
    clipper-scores.{raw,rendered}.json   six-pillar Clipper scoring per snapshot
    summary.json               per-page dual-mode accuracy + token totals

And a top-level <out_dir>/pilot-summary.json aggregating all pages.
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx  # noqa: F401  (kept for backward compat in test imports)
from bs4 import BeautifulSoup
from readability import Document  # readability-lxml

from ..access_gate_evaluator import AccessGateEvaluator
from ..parse import _parse_html_file  # single-file parse helper; internal but stable
from .clients import FoundryConfig, FoundryGeneratorClient, FoundryScoringClient
from .fetcher import fetch_raw, fetch_rendered
from .generator import generate_for_page
from .grader import grade_page, page_accuracy, persist_grades
from .judge import (
    JudgedGrade,
    judge_page,
    judged_page_accuracy,
    persist_judged_grades,
)
from .reviewer import ReviewRecord, approved_pairs, persist_review, review_pair
from .schemas import QAPair, ScoringAnswer
from .scorer import persist_scores, score_page


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0 Safari/537.36 Clipper-Phase5/0.1"
)
DEFAULT_TIMEOUT = 30.0
MAX_DOCUMENT_CHARS = 40_000   # keep prompts under ~30 k tokens
MIN_DOCUMENT_CHARS = 1_500    # below this, skip: too short for 5 non-clustered Qs


@dataclass
class PilotPageSummary:
    slug: str
    url: str
    profile: str
    num_pairs: int
    # Headline accuracy = rendered-mode accuracy (rendered is the canonical
    # ground-truth fetch; raw accuracy is reported alongside as the delta).
    accuracy: float
    tokens_in_total: int
    tokens_out_total: int
    # Dual-fetch / dual-score additions (Phase 5 dual-fetcher plan).
    accuracy_raw: Optional[float] = None
    accuracy_rendered: Optional[float] = None
    accuracy_delta: Optional[float] = None  # rendered - raw
    raw_fetch_status: Optional[str] = None        # "ok" | "failed" | "short"
    rendered_fetch_status: Optional[str] = None
    # Clipper pillar scoring per fetch mode. Keyed by mode ("raw" | "rendered").
    parseability_score_raw: Optional[float] = None
    parseability_score_rendered: Optional[float] = None
    universal_score_raw: Optional[float] = None
    universal_score_rendered: Optional[float] = None
    content_type: Optional[str] = None
    component_scores_raw: Dict[str, float] = field(default_factory=dict)
    component_scores_rendered: Dict[str, float] = field(default_factory=dict)


def _slugify(url: str) -> str:
    s = re.sub(r"^https?://", "", url)
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-")
    return s[:80] or "page"


def _fetch(url: str) -> str:
    """Legacy single-mode fetch (kept for tests / external callers).

    New code should use :func:`retrievability.phase5.fetcher.fetch_raw` directly.
    """
    html, _meta = fetch_raw(url)
    return html


def _extract(html: str) -> tuple[str, str]:
    """Return (title, cleaned_text)."""
    doc = Document(html)
    title = (doc.short_title() or "").strip()
    # readability returns HTML of the main content region
    content_html = doc.summary(html_partial=True)
    text = BeautifulSoup(content_html, "lxml").get_text(separator="\n")
    # collapse runs of blank lines
    text = re.sub(r"\n\s*\n+", "\n\n", text).strip()
    if len(text) > MAX_DOCUMENT_CHARS:
        text = text[:MAX_DOCUMENT_CHARS] + "\n\n[document truncated for prompt size]"
    return title, text


def _score_with_clipper(
    *, page_html_path: Path, url: str, page_dir: Path,
    output_name: str = "clipper-scores.json",
) -> Optional[Dict[str, Any]]:
    """Run Clipper's six-pillar scoring on a snapshotted page.

    Uses the same single-file parse + AccessGateEvaluator path as `main.py express`.
    Writes the full ScoreResult to ``<page_dir>/<output_name>`` and returns a
    compact dict ({parseability_score, universal_score, content_type,
    component_scores}) for the per-page pilot summary. Returns None on any
    failure so Clipper's browser/axe issues cannot kill the LLM pipeline.
    """
    try:
        parse_result = _parse_html_file(page_html_path)
        parse_data = parse_result.to_dict()
        evaluator = AccessGateEvaluator()
        score_result = evaluator.evaluate_access_gate(parse_data, url=url)
        full = score_result.to_dict()
        (page_dir / output_name).write_text(
            json.dumps(full, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return {
            "parseability_score": full.get("parseability_score"),
            "universal_score": full.get("universal_score"),
            "content_type": full.get("content_type"),
            "component_scores": full.get("component_scores", {}),
        }
    except Exception as exc:  # pragma: no cover - defensive
        print(f"  [WARN] Clipper scoring failed: {type(exc).__name__}: {exc}")
        return None


def _auto_accept_all(pairs: List[QAPair], reviewer_id: str) -> List[ReviewRecord]:
    return [
        ReviewRecord(
            pair_index=i,
            decision="accept",
            generated_pair=p,
            edited_pair=p,
            reject_reason=None,
            reviewer_id=reviewer_id,
        )
        for i, p in enumerate(pairs)
    ]


def _parse_pilot_line(line: str) -> Optional[tuple[str, str]]:
    """One line → (url, profile). Format: `url[\\tprofile[\\tvendor]][  # comment]`.

    Whole-line `#` comments and inline ` # ...` trailing comments are stripped.
    Any columns beyond profile are ignored (e.g. vendor, tier markers).
    """
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    # Strip inline trailing "  # comment" without breaking '#' inside URLs.
    # Anchor on whitespace-then-hash to avoid URL fragment collisions.
    line = re.split(r"\s+#", line, maxsplit=1)[0].strip()
    if not line:
        return None
    parts = re.split(r"[\t,]", line)
    url = parts[0].strip()
    profile = parts[1].strip() if len(parts) > 1 else "article"
    return url, profile


def load_pilot_urls(path: Path) -> List[tuple[str, str]]:
    out: List[tuple[str, str]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        parsed = _parse_pilot_line(raw)
        if parsed:
            out.append(parsed)
    return out


def run_pilot(
    *,
    urls: List[tuple[str, str]],
    out_dir: Path,
    config: FoundryConfig,
    review: bool = False,
    reviewer_id: str = "auto",
    use_secondary: bool = False,
    grader_mode: str = "substring",  # "substring" | "llm"
) -> List[PilotPageSummary]:
    out_dir.mkdir(parents=True, exist_ok=True)
    started_at = datetime.now(timezone.utc).isoformat()

    generator = FoundryGeneratorClient(config)
    primary = FoundryScoringClient(config, deployment=config.scorer_primary_deployment)
    secondary: Optional[FoundryScoringClient] = None
    if use_secondary and config.scorer_secondary_deployment:
        secondary = FoundryScoringClient(config, deployment=config.scorer_secondary_deployment)
    judge_client: Optional[FoundryScoringClient] = None
    if grader_mode == "llm":
        if not config.scorer_secondary_deployment:
            raise RuntimeError(
                "grader_mode='llm' requires PHASE5_SCORER_SECONDARY_DEPLOYMENT "
                "(Llama 3.3 70B) to be set; it is the cross-family judge."
            )
        judge_client = FoundryScoringClient(
            config, deployment=config.scorer_secondary_deployment
        )

    summaries: List[PilotPageSummary] = []
    for url, profile in urls:
        slug = _slugify(url)
        page_dir = out_dir / slug
        page_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n=== {slug} ({profile}) ===")
        t0 = time.time()

        # ----- Dual-mode fetch ----------------------------------------------
        raw_html: Optional[str] = None
        raw_text: Optional[str] = None
        raw_title: str = ""
        raw_status = "failed"
        try:
            print(f"  fetch raw      {url}")
            raw_html, raw_meta = fetch_raw(url)
            (page_dir / "page.raw.html").write_text(raw_html, encoding="utf-8")
            (page_dir / "fetch.raw.json").write_text(
                json.dumps(raw_meta, indent=2), encoding="utf-8"
            )
            raw_title, raw_text = _extract(raw_html)
            (page_dir / "page.raw.txt").write_text(raw_text, encoding="utf-8")
            if len(raw_text) >= MIN_DOCUMENT_CHARS:
                raw_status = "ok"
                print(f"    raw extract: {len(raw_text)} chars")
            else:
                raw_status = "short"
                print(f"    raw extract: {len(raw_text)} chars  [short — JS-required]")
        except Exception as exc:
            print(f"    raw fetch failed: {type(exc).__name__}: {str(exc)[:80]}")
            (page_dir / "fetch.raw.json").write_text(
                json.dumps({"mode": "raw", "error": f"{type(exc).__name__}: {exc}"}, indent=2),
                encoding="utf-8",
            )

        rendered_html: Optional[str] = None
        rendered_text: Optional[str] = None
        rendered_title: str = ""
        rendered_status = "failed"
        try:
            print(f"  fetch rendered {url}")
            rendered_html, rendered_meta = fetch_rendered(url)
            (page_dir / "page.rendered.html").write_text(rendered_html, encoding="utf-8")
            (page_dir / "fetch.rendered.json").write_text(
                json.dumps(rendered_meta, indent=2), encoding="utf-8"
            )
            rendered_title, rendered_text = _extract(rendered_html)
            (page_dir / "page.rendered.txt").write_text(rendered_text, encoding="utf-8")
            if len(rendered_text) >= MIN_DOCUMENT_CHARS:
                rendered_status = "ok"
                print(f"    rendered extract: {len(rendered_text)} chars  signal={rendered_meta.get('hydration_signal')}")
            else:
                rendered_status = "short"
                print(f"    rendered extract: {len(rendered_text)} chars  [short — bot-blocked or non-content page]")
        except Exception as exc:
            print(f"    rendered fetch failed: {type(exc).__name__}: {str(exc)[:80]}")
            (page_dir / "fetch.rendered.json").write_text(
                json.dumps({"mode": "rendered", "error": f"{type(exc).__name__}: {exc}"}, indent=2),
                encoding="utf-8",
            )

        # Skip the page entirely only if BOTH modes fail to produce usable
        # text. If only raw fails, the rendered branch carries the QA
        # pipeline; the asymmetry is recorded in the summary.
        if rendered_status != "ok" and raw_status != "ok":
            print(f"  [SKIP] both raw and rendered extracts below {MIN_DOCUMENT_CHARS}-char minimum")
            # Still emit a summary stub so downstream tooling sees the URL
            # was attempted. No accuracy fields populated.
            stub = PilotPageSummary(
                slug=slug, url=url, profile=profile, num_pairs=0, accuracy=0.0,
                tokens_in_total=0, tokens_out_total=0,
                raw_fetch_status=raw_status, rendered_fetch_status=rendered_status,
            )
            (page_dir / "summary.json").write_text(json.dumps(asdict(stub), indent=2), encoding="utf-8")
            summaries.append(stub)
            continue

        # ----- Clipper pillar scoring (per available snapshot) --------------
        clipper_raw: Optional[Dict[str, Any]] = None
        clipper_rendered: Optional[Dict[str, Any]] = None
        if raw_html is not None and raw_status == "ok":
            print(f"  clipper raw")
            clipper_raw = _score_with_clipper(
                page_html_path=page_dir / "page.raw.html", url=url, page_dir=page_dir,
                output_name="clipper-scores.raw.json",
            )
            if clipper_raw:
                print(
                    f"    parseability={clipper_raw.get('parseability_score'):.1f}  "
                    f"universal={clipper_raw.get('universal_score'):.1f}"
                )
        if rendered_html is not None and rendered_status == "ok":
            print(f"  clipper rendered")
            clipper_rendered = _score_with_clipper(
                page_html_path=page_dir / "page.rendered.html", url=url, page_dir=page_dir,
                output_name="clipper-scores.rendered.json",
            )
            if clipper_rendered:
                print(
                    f"    parseability={clipper_rendered.get('parseability_score'):.1f}  "
                    f"universal={clipper_rendered.get('universal_score'):.1f}"
                )

        # ----- Q/A generation: from RENDERED text (canonical content) -------
        # If rendered failed but raw succeeded, fall back to raw so the page
        # still contributes a data point (recorded in summary).
        if rendered_status == "ok":
            gen_text = rendered_text
            gen_title = rendered_title
            gen_source = "rendered"
        else:
            gen_text = raw_text
            gen_title = raw_title
            gen_source = "raw"
        print(f"  generating Q/A (Mistral) from {gen_source} text")
        pairs = generate_for_page(
            client=generator,
            title=gen_title,
            url=url,
            profile=profile,
            document_text=gen_text,
            out_dir=page_dir,
        )
        print(f"    generated {len(pairs)} pairs")

        if review:
            records = [review_pair(p, i, reviewer_id) for i, p in enumerate(pairs)]
        else:
            records = _auto_accept_all(pairs, reviewer_id)
        persist_review(records, page_dir / "review.json")
        ground_truth = approved_pairs(records)
        (page_dir / "qapairs.json").write_text(
            json.dumps([p.to_dict() for p in ground_truth], indent=2),
            encoding="utf-8",
        )

        # ----- Score the primary LLM against EACH extraction independently --
        # This is the core dual-fetcher measurement: same questions, same
        # ground truth, two different "what the agent saw" inputs.
        accuracy_raw: Optional[float] = None
        accuracy_rendered: Optional[float] = None
        all_answers: List[ScoringAnswer] = []  # for token totals

        for mode, mode_text, mode_status in [
            ("raw", raw_text, raw_status),
            ("rendered", rendered_text, rendered_status),
        ]:
            if mode_status != "ok":
                print(f"  scoring ({mode}): SKIPPED ({mode_status})")
                continue
            print(f"  scoring ({mode}, primary={config.scorer_primary_deployment})")
            answers = score_page(
                client=primary,
                document_text=mode_text,
                ground_truth=ground_truth,
                runs_per_question=1,
            )
            persist_scores(answers, page_dir / f"scoring.primary.{mode}.json")
            grades = grade_page(ground_truth=ground_truth, answers=answers)
            persist_grades(grades, page_dir / f"grades.primary.{mode}.json")
            substring_acc = page_accuracy(grades)
            mode_judged_acc: Optional[float] = None
            if judge_client is not None:
                judged = judge_page(
                    client=judge_client, ground_truth=ground_truth, answers=answers
                )
                persist_judged_grades(judged, page_dir / f"grades.primary.judged.{mode}.json")
                mode_judged_acc = judged_page_accuracy(judged)
                print(f"    substring={substring_acc:.0%}  judged={mode_judged_acc:.0%}")
            else:
                print(f"    substring={substring_acc:.0%}")
            mode_acc = mode_judged_acc if mode_judged_acc is not None else substring_acc
            if mode == "raw":
                accuracy_raw = mode_acc
            else:
                accuracy_rendered = mode_acc
            all_answers.extend(answers)

            # Optional: secondary-scorer pass on the rendered extraction only
            # (cheaper than 2x; secondary's role is cross-LLM agreement, not
            # raw-vs-rendered comparison, so once is enough).
            if secondary is not None and mode == "rendered":
                print(f"  scoring (secondary={config.scorer_secondary_deployment})")
                sec_answers = score_page(
                    client=secondary, document_text=mode_text,
                    ground_truth=ground_truth, runs_per_question=1,
                )
                persist_scores(sec_answers, page_dir / "scoring.secondary.rendered.json")
                sec_grades = grade_page(ground_truth=ground_truth, answers=sec_answers)
                persist_grades(sec_grades, page_dir / "grades.secondary.rendered.json")

        # Headline accuracy = rendered-mode (canonical). If rendered didn't
        # run, fall back to raw so the field is non-null.
        headline = accuracy_rendered if accuracy_rendered is not None else accuracy_raw
        if headline is None:
            headline = 0.0  # both modes failed to score; data point lost
        delta = (
            (accuracy_rendered - accuracy_raw)
            if (accuracy_raw is not None and accuracy_rendered is not None)
            else None
        )

        tokens_in = sum(a.tokens_in for a in all_answers)
        tokens_out = sum(a.tokens_out for a in all_answers)
        # Content type: prefer rendered, fall back to raw.
        ct = (clipper_rendered or {}).get("content_type") or (clipper_raw or {}).get("content_type")
        summary = PilotPageSummary(
            slug=slug,
            url=url,
            profile=profile,
            num_pairs=len(ground_truth),
            accuracy=headline,
            tokens_in_total=tokens_in,
            tokens_out_total=tokens_out,
            accuracy_raw=accuracy_raw,
            accuracy_rendered=accuracy_rendered,
            accuracy_delta=delta,
            raw_fetch_status=raw_status,
            rendered_fetch_status=rendered_status,
            parseability_score_raw=(clipper_raw or {}).get("parseability_score"),
            parseability_score_rendered=(clipper_rendered or {}).get("parseability_score"),
            universal_score_raw=(clipper_raw or {}).get("universal_score"),
            universal_score_rendered=(clipper_rendered or {}).get("universal_score"),
            content_type=ct,
            component_scores_raw=(clipper_raw or {}).get("component_scores", {}),
            component_scores_rendered=(clipper_rendered or {}).get("component_scores", {}),
        )
        (page_dir / "summary.json").write_text(json.dumps(asdict(summary), indent=2), encoding="utf-8")
        summaries.append(summary)
        dt = time.time() - t0
        delta_str = f"  delta={delta:+.0%}" if delta is not None else ""
        print(f"  done: rendered_acc={headline:.0%}  raw_acc={accuracy_raw if accuracy_raw is not None else 'n/a'}{delta_str}  {dt:.1f}s")

    manifest = {
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "generator": config.generator_deployment,
        "scorer_primary": config.scorer_primary_deployment,
        "scorer_secondary": config.scorer_secondary_deployment if use_secondary else None,
        "grader_mode": grader_mode,
        "judge_model": judge_client.model_id if judge_client is not None else None,
        "review_mode": "interactive" if review else "auto-accept",
        "fetcher": "dual (httpx raw + playwright rendered)",
        "pages": [asdict(s) for s in summaries],
        "mean_accuracy_rendered": (
            sum(s.accuracy_rendered for s in summaries if s.accuracy_rendered is not None)
            / max(1, sum(1 for s in summaries if s.accuracy_rendered is not None))
        ),
        "mean_accuracy_raw": (
            sum(s.accuracy_raw for s in summaries if s.accuracy_raw is not None)
            / max(1, sum(1 for s in summaries if s.accuracy_raw is not None))
        ),
        "pages_raw_only_failure": sum(
            1 for s in summaries if s.raw_fetch_status != "ok" and s.rendered_fetch_status == "ok"
        ),
        "pages_both_failed": sum(
            1 for s in summaries if s.raw_fetch_status != "ok" and s.rendered_fetch_status != "ok"
        ),
    }
    (out_dir / "pilot-summary.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return summaries


def rejudge_pilot(*, pilot_dir: Path, config: FoundryConfig) -> dict:
    """Re-grade an existing pilot directory with the LLM judge.

    Does not re-fetch pages or re-run the scorer. Reads
    `qapairs.json` and `scoring.primary.json` from each page
    subdirectory, calls the judge on each answer, writes
    `grades.primary.judged.json`, and updates a `rejudge-summary.json`
    at the pilot root.

    Used for the calibration gate: compare these judged labels against
    hand-labels stored at `<pilot_dir>/_calibration/hand-labels.json`.
    """
    if not config.scorer_secondary_deployment:
        raise RuntimeError(
            "rejudge requires PHASE5_SCORER_SECONDARY_DEPLOYMENT (Llama 3.3 70B)"
        )
    judge_client = FoundryScoringClient(
        config, deployment=config.scorer_secondary_deployment
    )
    out: dict = {"judge_model": judge_client.model_id, "pages": []}

    for page_dir in sorted(p for p in pilot_dir.iterdir() if p.is_dir() and not p.name.startswith("_")):
        qapath = page_dir / "qapairs.json"
        # Prefer the new dual-fetch rendered file; fall back to the legacy
        # single-mode file so older pilot directories still re-judge cleanly.
        scpath = page_dir / "scoring.primary.rendered.json"
        if not scpath.is_file():
            scpath = page_dir / "scoring.primary.json"
        if not qapath.is_file() or not scpath.is_file():
            continue
        qa_raw = json.loads(qapath.read_text(encoding="utf-8"))
        sc_raw = json.loads(scpath.read_text(encoding="utf-8"))
        ground_truth = [QAPair.from_dict(d) for d in qa_raw]
        answers = [ScoringAnswer.from_dict(d) for d in sc_raw]
        print(f"  judging {page_dir.name}: {len(answers)} answers (from {scpath.name})")
        judged = judge_page(client=judge_client, ground_truth=ground_truth, answers=answers)
        # Mirror the source-file naming so judged labels live next to the scoring file.
        judged_name = (
            "grades.primary.judged.rendered.json"
            if scpath.name.endswith(".rendered.json")
            else "grades.primary.judged.json"
        )
        persist_judged_grades(judged, page_dir / judged_name)
        acc = judged_page_accuracy(judged)
        out["pages"].append({"slug": page_dir.name, "judged_accuracy": acc, "num_pairs": len(answers)})

    if out["pages"]:
        out["mean_judged_accuracy"] = sum(p["judged_accuracy"] for p in out["pages"]) / len(out["pages"])
    else:
        out["mean_judged_accuracy"] = 0.0
    (pilot_dir / "rejudge-summary.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    return out
