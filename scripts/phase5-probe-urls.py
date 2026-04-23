"""Probe Phase 5 corpus candidates: dual-mode (raw + rendered), report survivors.

Reads urls/phase5-corpus-candidates.txt (tab-separated: url, profile, vendor),
fetches each TWICE — once with httpx (raw) and once with Playwright (rendered) —
runs readability extraction on each, and reports per-URL whether each mode
"passed" (fetch ok AND extracted >= MIN_DOCUMENT_CHARS).

The asymmetry between modes is the data Phase 5 measures, so a URL that passes
only one mode is not a failure — it's recorded with both results so corpus
selection can include it deliberately. The output JSON is consumed by the
corpus-assembly step.
"""
from __future__ import annotations

import json
import logging
import sys
from collections import Counter
from pathlib import Path

# Ensure the repo root is importable when invoked from scripts/.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Silence chatty loggers (httpx redirects, readability's "ruthless removal" notice).
for name in ("httpx", "readability", "readability.readability"):
    logging.getLogger(name).setLevel(logging.WARNING)

from retrievability.phase5.fetcher import fetch_raw, fetch_rendered
from retrievability.phase5.runner import MIN_DOCUMENT_CHARS, _extract


def _probe(url: str, fetcher) -> dict:
    """Run one fetcher and return a result dict (status, chars, passed, error)."""
    try:
        html, meta = fetcher(url)
        title, text = _extract(html)
        chars = len(text)
        return {
            "status": meta.get("status"),
            "extracted_chars": chars,
            "passed": chars >= MIN_DOCUMENT_CHARS,
            "elapsed_s": meta.get("elapsed_s"),
            "hydration_signal": meta.get("hydration_signal"),  # rendered only
            "error": None,
        }
    except Exception as exc:
        return {
            "status": None,
            "extracted_chars": 0,
            "passed": False,
            "elapsed_s": None,
            "hydration_signal": None,
            "error": f"{type(exc).__name__}: {str(exc)[:100]}",
        }


def main(argv: list[str]) -> int:
    candidates_path = Path(argv[1]) if len(argv) > 1 else Path("urls/phase5-corpus-candidates.txt")
    out_json_path = Path(argv[2]) if len(argv) > 2 else Path("evaluation/phase5-corpus/probe-results.json")

    candidates: list[tuple[str, str, str]] = []
    for raw in candidates_path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        parts = raw.split("\t")
        if len(parts) < 2:
            continue
        url = parts[0].strip()
        profile = parts[1].strip() if len(parts) > 1 else "article"
        vendor = parts[2].strip() if len(parts) > 2 else "unknown"
        candidates.append((url, profile, vendor))

    print(f"Probing {len(candidates)} candidate URL(s) in raw + rendered modes...\n")
    print(f"  {'#':>3} {'raw':>6} {'rend':>6} {'profile':10} {'vendor':12} {'url'}")
    print(f"  {'-'*3} {'-'*6} {'-'*6} {'-'*10} {'-'*12} {'-'*40}")

    results: list[dict] = []
    for i, (url, profile, vendor) in enumerate(candidates, 1):
        raw_res = _probe(url, fetch_raw)
        rendered_res = _probe(url, fetch_rendered)
        raw_tag = (
            f"{raw_res['extracted_chars']:>6}"
            if raw_res["passed"]
            else (f"{'X':>6}" if raw_res["error"] else f"{raw_res['extracted_chars']:>6}*")
        )
        rend_tag = (
            f"{rendered_res['extracted_chars']:>6}"
            if rendered_res["passed"]
            else (f"{'X':>6}" if rendered_res["error"] else f"{rendered_res['extracted_chars']:>6}*")
        )
        print(f"  {i:>3} {raw_tag} {rend_tag} {profile:10} {vendor:12} {url}")
        results.append(
            {
                "url": url,
                "profile_hint": profile,
                "vendor": vendor,
                "raw": raw_res,
                "rendered": rendered_res,
                "passed_either": raw_res["passed"] or rendered_res["passed"],
                "passed_both": raw_res["passed"] and rendered_res["passed"],
            }
        )

    out_json_path.parent.mkdir(parents=True, exist_ok=True)
    out_json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    raw_pass = [r for r in results if r["raw"]["passed"]]
    rend_pass = [r for r in results if r["rendered"]["passed"]]
    either = [r for r in results if r["passed_either"]]
    both = [r for r in results if r["passed_both"]]
    only_rendered = [r for r in results if r["rendered"]["passed"] and not r["raw"]["passed"]]
    blocked = [r for r in results if not r["passed_either"]]

    print(f"\n{'=' * 60}")
    print(f"Total: {len(results)}")
    print(f"  raw passes:        {len(raw_pass):3} ({100*len(raw_pass)//len(results)}%)")
    print(f"  rendered passes:   {len(rend_pass):3} ({100*len(rend_pass)//len(results)}%)")
    print(f"  both pass:         {len(both):3}")
    print(f"  rendered only:     {len(only_rendered):3}  ← 'JS-required' finding")
    print(f"  passes either:     {len(either):3}  ← usable in corpus")
    print(f"  blocked / broken:  {len(blocked):3}  ← excluded from QA corpus")
    print(f"\nBy profile (passing either):")
    for p, c in Counter(r["profile_hint"] for r in either).most_common():
        print(f"  {p:10} {c}")
    print(f"\nBy vendor (passing either):")
    for v, c in Counter(r["vendor"] for r in either).most_common():
        print(f"  {v:12} {c}")
    print(f"\nResults: {out_json_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

