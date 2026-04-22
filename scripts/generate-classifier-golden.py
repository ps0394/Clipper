"""Generate the classifier lockdown golden file (Phase 4.3).

For each URL in the committed evaluation corpora, parse the captured
HTML snapshot and record the content-type classification that
``retrievability.profiles.detect_content_type`` produces today.

The output file ``tests/fixtures/classifier_corpus_golden.json`` is then
hand-reviewed and committed. ``tests/test_classifier_lockdown.py``
asserts that every URL in the golden still produces the same
``(profile, source)`` tuple, so any future classifier drift is caught at
CI time with the offending URL + signal named in the failure.

Usage:
    python scripts/generate-classifier-golden.py           # write golden
    python scripts/generate-classifier-golden.py --check   # diff only
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

from bs4 import BeautifulSoup

# Allow running the script from repo root without installing the package.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from retrievability.profiles import detect_content_type  # noqa: E402


# Corpora to include in the golden. Add more entries here as new
# evaluation runs produce snapshot directories worth locking down.
CORPORA = [
    REPO_ROOT / "evaluation" / "learn-analysis-v3" / "snapshots",
    REPO_ROOT / "evaluation" / "competitive-analysis-v3" / "snapshots",
]

GOLDEN_PATH = REPO_ROOT / "tests" / "fixtures" / "classifier_corpus_golden.json"


def _classify_snapshot(html_path: Path, url: str) -> Dict:
    """Run the classifier against one snapshot + URL pair."""
    html = html_path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(html, "html5lib")
    profile, trace = detect_content_type(soup, url=url)
    return {
        "url": url,
        "snapshot": str(html_path.relative_to(REPO_ROOT)).replace("\\", "/"),
        "profile": profile,
        "source": trace.get("source", "default"),
        "matched_value": trace.get("matched_value"),
    }


def _build_golden() -> List[Dict]:
    entries: List[Dict] = []
    for corpus_dir in CORPORA:
        crawl_results = corpus_dir / "crawl_results.json"
        if not crawl_results.exists():
            print(f"[skip] missing {crawl_results}")
            continue
        with crawl_results.open(encoding="utf-8") as fh:
            records = json.load(fh)
        for record in records:
            url = record.get("url")
            html_name = record.get("html_path")
            if not url or not html_name:
                continue
            html_path = corpus_dir / html_name
            if not html_path.exists():
                print(f"[skip] missing snapshot {html_path}")
                continue
            entries.append(_classify_snapshot(html_path, url))
    entries.sort(key=lambda e: e["url"])
    return entries


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="compare freshly-computed classifications against the "
             "committed golden without writing; exit non-zero on drift",
    )
    args = parser.parse_args()

    fresh = _build_golden()

    if args.check:
        if not GOLDEN_PATH.exists():
            print(f"[FAIL] golden file not found: {GOLDEN_PATH}")
            return 2
        with GOLDEN_PATH.open(encoding="utf-8") as fh:
            committed = json.load(fh)
        if fresh == committed:
            print(f"[PASS] classifier output matches golden ({len(fresh)} URLs)")
            return 0
        print("[FAIL] classifier output drifted from golden")
        fresh_by_url = {e["url"]: e for e in fresh}
        committed_by_url = {e["url"]: e for e in committed}
        for url in sorted(set(fresh_by_url) | set(committed_by_url)):
            a = committed_by_url.get(url)
            b = fresh_by_url.get(url)
            if a != b:
                print(f"  {url}")
                print(f"    committed: {a}")
                print(f"    fresh:     {b}")
        return 1

    GOLDEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    with GOLDEN_PATH.open("w", encoding="utf-8") as fh:
        json.dump(fresh, fh, indent=2)
        fh.write("\n")
    print(f"[PASS] wrote {GOLDEN_PATH.relative_to(REPO_ROOT)} "
          f"({len(fresh)} URLs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
