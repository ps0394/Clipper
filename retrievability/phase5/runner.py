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
from .reviewer import ReviewRecord, approved_pairs, persist_review, review_pair
from .schemas import QAPair
from .scorer import persist_scores, score_page


USER_AGENT = "Clipper-Phase5-Pilot/0.1"
DEFAULT_TIMEOUT = 30.0
MAX_DOCUMENT_CHARS = 40_000   # keep prompts under ~30 k tokens


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
) -> List[PilotPageSummary]:
    out_dir.mkdir(parents=True, exist_ok=True)
    started_at = datetime.now(timezone.utc).isoformat()

    generator = FoundryGeneratorClient(config)
    primary = FoundryScoringClient(config, deployment=config.scorer_primary_deployment)
    secondary: Optional[FoundryScoringClient] = None
    if use_secondary and config.scorer_secondary_deployment:
        secondary = FoundryScoringClient(config, deployment=config.scorer_secondary_deployment)

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
        summary = PilotPageSummary(
            slug=slug,
            url=url,
            profile=profile,
            num_pairs=len(ground_truth),
            accuracy=acc,
            tokens_in_total=tokens_in,
            tokens_out_total=tokens_out,
        )
        (page_dir / "summary.json").write_text(json.dumps(asdict(summary), indent=2), encoding="utf-8")
        summaries.append(summary)
        dt = time.time() - t0
        print(f"  done: accuracy={acc:.0%}  pairs={len(ground_truth)}  {dt:.1f}s")

    manifest = {
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "generator": config.generator_deployment,
        "scorer_primary": config.scorer_primary_deployment,
        "scorer_secondary": config.scorer_secondary_deployment if use_secondary else None,
        "review_mode": "interactive" if review else "auto-accept",
        "pages": [asdict(s) for s in summaries],
        "mean_accuracy": (sum(s.accuracy for s in summaries) / len(summaries)) if summaries else 0.0,
    }
    (out_dir / "pilot-summary.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return summaries
