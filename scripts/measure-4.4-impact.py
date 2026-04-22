"""Phase 4.4 impact measurement.

Re-scores both v3 corpora (learn-analysis-v3 and competitive-analysis-v3)
from committed HTML snapshots using the CURRENT evaluator (with ms.topic
removed from the metadata pillar's topic-field check).

Measures the **isolated metadata-pillar delta** by rescoring offline
(url=None, crawl_data=None) so HTTP and WCAG pillars run in their
static-fallback path and don't contaminate the delta. Only the metadata
pillar's topic-field scoring changed in Phase 4.4, so the parseability
delta for each page is analytically:

    parseability_delta = metadata_delta * (metadata_pillar_weight * 0.01)

…where ``metadata_pillar_weight`` is 10 for the ``article`` / ``landing`` /
``reference`` / ``faq`` / ``tutorial`` / ``http`` profiles and 15 for the
``sample`` profile. So the per-page headline-score impact is bounded at
metadata_delta * 0.15 at absolute worst.

Offline only: no network.

Usage:
    python scripts/measure-4.4-impact.py
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from retrievability.access_gate_evaluator import AccessGateEvaluator  # noqa: E402
from retrievability.parse import _parse_html_file  # noqa: E402

CORPORA = [
    ("learn-v3", REPO_ROOT / "evaluation" / "learn-analysis-v3"),
    ("competitive-v3", REPO_ROOT / "evaluation" / "competitive-analysis-v3"),
]


def rescore_corpus(corpus_dir: Path, name: str) -> dict:
    crawl_results_path = corpus_dir / "snapshots" / "crawl_results.json"
    before_scores_path = corpus_dir / f"{name}_scores.json"
    crawl_results = json.loads(crawl_results_path.read_text(encoding="utf-8"))
    before = {e["url"]: e for e in json.loads(before_scores_path.read_text(encoding="utf-8"))}

    evaluator = AccessGateEvaluator()
    rows = []
    for entry in crawl_results:
        url = entry["url"]
        snapshot = Path(entry["html_path"])
        if not snapshot.is_absolute():
            snapshot = corpus_dir / "snapshots" / snapshot
        # Offline re-score: url=None so HTTP/WCAG pillars don't fetch the
        # live URL. Metadata pillar is deterministic from HTML alone, so
        # the metadata-pillar delta we measure here is exactly the 4.4
        # impact.
        parse_result = _parse_html_file(snapshot)
        after_result = evaluator.evaluate_access_gate(
            parse_result.to_dict(), url=None, crawl_data=None
        )
        # For before: also re-score offline with ms.topic preserved. Easier:
        # compare to the on-disk scores file's metadata_completeness, which
        # WAS computed with url=url + crawl_data but the metadata pillar
        # doesn't use either. So metadata_completeness in the on-disk file
        # is directly comparable to ours.
        before_entry = before.get(url)
        if not before_entry:
            continue
        before_meta = before_entry["component_scores"]["metadata_completeness"]
        after_meta = after_result.component_scores["metadata_completeness"]
        rows.append({
            "url": url,
            "metadata_before": round(before_meta, 2),
            "metadata_after": round(after_meta, 2),
            "metadata_delta": round(after_meta - before_meta, 2),
        })
    return {"name": name, "rows": rows}


def summarize(corpus: dict) -> None:
    rows = corpus["rows"]
    print(f"\n=== {corpus['name']} ({len(rows)} URLs) ===")
    print(f"{'URL':<80} {'before':>8} {'after':>8} {'delta':>8}")
    for r in rows:
        print(
            f"{r['url'][:78]:<80} "
            f"{r['metadata_before']:>8.2f} "
            f"{r['metadata_after']:>8.2f} "
            f"{r['metadata_delta']:>+8.2f}"
        )
    deltas = [r["metadata_delta"] for r in rows]
    if deltas:
        affected = sum(1 for d in deltas if d != 0)
        print(
            f"\nmetadata mean delta = {statistics.mean(deltas):+.2f}   "
            f"median delta = {statistics.median(deltas):+.2f}   "
            f"min/max = {min(deltas):+.2f}/{max(deltas):+.2f}   "
            f"pages affected = {affected}/{len(deltas)}"
        )
        # Translate to bounded parseability delta (article profile, 10% weight).
        print(
            f"bounded parseability delta (article profile, 10% metadata weight): "
            f"mean = {statistics.mean(deltas) * 0.10:+.2f}, "
            f"min/max = {min(deltas) * 0.10:+.2f}/{max(deltas) * 0.10:+.2f}"
        )


def main() -> int:
    for label, corpus_dir in CORPORA:
        result = rescore_corpus(corpus_dir, label)
        summarize(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



def main() -> int:
    for label, corpus_dir in CORPORA:
        result = rescore_corpus(corpus_dir, label)
        summarize(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
