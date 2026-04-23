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
    page.html          raw HTML snapshot
    page.txt           cleaned document text (readability)
    generator.prompt.txt
    generator.raw.json
    qapairs.json       approved ground-truth pairs
    review.json        review audit trail
    scoring.json       scoring-LLM answers
    grades.json        per-answer grades
    summary.json       per-page accuracy + token totals

And a top-level <out_dir>/pilot-summary.json aggregating all pages.
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import httpx
from bs4 import BeautifulSoup
from readability import Document  # readability-lxml

from .clients import FoundryConfig, FoundryGeneratorClient, FoundryScoringClient
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
    accuracy: float
    tokens_in_total: int
    tokens_out_total: int


def _slugify(url: str) -> str:
    s = re.sub(r"^https?://", "", url)
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-")
    return s[:80] or "page"


def _fetch(url: str) -> str:
    with httpx.Client(follow_redirects=True, timeout=DEFAULT_TIMEOUT, headers={"User-Agent": USER_AGENT}) as c:
        r = c.get(url)
        r.raise_for_status()
        return r.text


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
    """One line → (url, profile). Format: `url[\\tprofile]`. # comments allowed."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    parts = re.split(r"[\t,]", line, maxsplit=1)
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
        print(f"  fetching {url}")
        t0 = time.time()
        try:
            html = _fetch(url)
        except Exception as exc:
            print(f"  [SKIP] fetch failed: {type(exc).__name__}: {exc}")
            continue
        (page_dir / "page.html").write_text(html, encoding="utf-8")
        title, text = _extract(html)
        (page_dir / "page.txt").write_text(text, encoding="utf-8")
        print(f"  extracted {len(text)} chars, title={title[:60]!r}")
        if len(text) < MIN_DOCUMENT_CHARS:
            print(f"  [SKIP] extracted document below {MIN_DOCUMENT_CHARS}-char minimum")
            continue

        print(f"  generating Q/A (Mistral)")
        pairs = generate_for_page(
            client=generator,
            title=title,
            url=url,
            profile=profile,
            document_text=text,
            out_dir=page_dir,
        )
        print(f"  generated {len(pairs)} pairs")

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

        print(f"  scoring (primary: {config.scorer_primary_deployment})")
        answers = score_page(
            client=primary,
            document_text=text,
            ground_truth=ground_truth,
            runs_per_question=1,
        )
        persist_scores(answers, page_dir / "scoring.primary.json")

        grades = grade_page(ground_truth=ground_truth, answers=answers)
        persist_grades(grades, page_dir / "grades.primary.json")
        acc = page_accuracy(grades)
        judged_acc: Optional[float] = None
        if judge_client is not None:
            print(f"  judging (judge: {judge_client.model_id})")
            judged = judge_page(
                client=judge_client,
                ground_truth=ground_truth,
                answers=answers,
            )
            persist_judged_grades(judged, page_dir / "grades.primary.judged.json")
            judged_acc = judged_page_accuracy(judged)
            print(f"    substring={acc:.0%}  judged={judged_acc:.0%}")

        if secondary is not None:
            print(f"  scoring (secondary: {config.scorer_secondary_deployment})")
            sec_answers = score_page(
                client=secondary,
                document_text=text,
                ground_truth=ground_truth,
                runs_per_question=1,
            )
            persist_scores(sec_answers, page_dir / "scoring.secondary.json")
            sec_grades = grade_page(ground_truth=ground_truth, answers=sec_answers)
            persist_grades(sec_grades, page_dir / "grades.secondary.json")

        tokens_in = sum(a.tokens_in for a in answers)
        tokens_out = sum(a.tokens_out for a in answers)
        headline_accuracy = judged_acc if judged_acc is not None else acc
        summary = PilotPageSummary(
            slug=slug,
            url=url,
            profile=profile,
            num_pairs=len(ground_truth),
            accuracy=headline_accuracy,
            tokens_in_total=tokens_in,
            tokens_out_total=tokens_out,
        )
        (page_dir / "summary.json").write_text(json.dumps(asdict(summary), indent=2), encoding="utf-8")
        summaries.append(summary)
        dt = time.time() - t0
        print(f"  done: accuracy={headline_accuracy:.0%}  pairs={len(ground_truth)}  {dt:.1f}s")

    manifest = {
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "generator": config.generator_deployment,
        "scorer_primary": config.scorer_primary_deployment,
        "scorer_secondary": config.scorer_secondary_deployment if use_secondary else None,
        "grader_mode": grader_mode,
        "judge_model": judge_client.model_id if judge_client is not None else None,
        "review_mode": "interactive" if review else "auto-accept",
        "pages": [asdict(s) for s in summaries],
        "mean_accuracy": (sum(s.accuracy for s in summaries) / len(summaries)) if summaries else 0.0,
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
        scpath = page_dir / "scoring.primary.json"
        if not qapath.is_file() or not scpath.is_file():
            continue
        qa_raw = json.loads(qapath.read_text(encoding="utf-8"))
        sc_raw = json.loads(scpath.read_text(encoding="utf-8"))
        ground_truth = [QAPair.from_dict(d) for d in qa_raw]
        answers = [ScoringAnswer.from_dict(d) for d in sc_raw]
        print(f"  judging {page_dir.name}: {len(answers)} answers")
        judged = judge_page(client=judge_client, ground_truth=ground_truth, answers=answers)
        persist_judged_grades(judged, page_dir / "grades.primary.judged.json")
        acc = judged_page_accuracy(judged)
        out["pages"].append({"slug": page_dir.name, "judged_accuracy": acc, "num_pairs": len(answers)})

    if out["pages"]:
        out["mean_judged_accuracy"] = sum(p["judged_accuracy"] for p in out["pages"]) / len(out["pages"])
    else:
        out["mean_judged_accuracy"] = 0.0
    (pilot_dir / "rejudge-summary.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    return out
