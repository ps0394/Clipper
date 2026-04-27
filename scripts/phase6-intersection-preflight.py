"""Pre-flight: compute intersection stats for every markdown-resolved page.

Reads ``page.rendered.txt`` and ``page.markdown.txt`` from each page dir
under a corpus directory, computes the sentence-level intersection, and
writes ``intersection.txt`` + ``intersection.stats.json`` per page plus
a top-level summary at ``<corpus_dir>/intersection-preflight.json``.

Pure Python — no LLM cost.

Usage:
    python scripts/phase6-intersection-preflight.py \
        --pilot-dir evaluation/phase5-results/corpus-002 \
        --min-chars 1500
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

# Allow running as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from retrievability.phase5.intersection import (  # noqa: E402
    compute_intersection,
    to_dict,
)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--pilot-dir", required=True, type=Path)
    p.add_argument(
        "--min-chars",
        type=int,
        default=1500,
        help="Minimum intersection char length to count as a survivor "
        "(matches MIN_DOCUMENT_CHARS in the runner).",
    )
    args = p.parse_args()

    pilot_dir: Path = args.pilot_dir
    if not pilot_dir.is_dir():
        print(f"ERROR: not a directory: {pilot_dir}", file=sys.stderr)
        return 2

    per_page: list[dict] = []
    for page_dir in sorted(p for p in pilot_dir.iterdir() if p.is_dir() and not p.name.startswith("_")):
        rendered_path = page_dir / "page.rendered.txt"
        md_path = page_dir / "page.markdown.txt"
        if not rendered_path.is_file() or not md_path.is_file():
            continue

        rendered = rendered_path.read_text(encoding="utf-8")
        md = md_path.read_text(encoding="utf-8")
        result = compute_intersection(rendered, md)
        stats = to_dict(result)

        # Persist per-page artifacts.
        (page_dir / "intersection.txt").write_text(result.text, encoding="utf-8")
        (page_dir / "intersection.stats.json").write_text(
            json.dumps(stats, indent=2), encoding="utf-8"
        )

        per_page.append({
            "slug": page_dir.name,
            **stats,
            "survives_min_chars": result.chars >= args.min_chars,
        })

    survivors = [e for e in per_page if e["survives_min_chars"]]
    chars = [e["chars"] for e in per_page]
    overlap_r = [e["overlap_ratio_rendered"] for e in per_page]
    overlap_m = [e["overlap_ratio_markdown"] for e in per_page]

    summary = {
        "pilot_dir": str(pilot_dir),
        "min_chars": args.min_chars,
        "n_pages_with_markdown": len(per_page),
        "n_survivors": len(survivors),
        "chars": {
            "min": min(chars) if chars else 0,
            "max": max(chars) if chars else 0,
            "mean": round(statistics.fmean(chars), 1) if chars else 0,
            "median": round(statistics.median(chars), 1) if chars else 0,
        },
        "overlap_ratio_rendered": {
            "min": round(min(overlap_r), 4) if overlap_r else 0,
            "max": round(max(overlap_r), 4) if overlap_r else 0,
            "mean": round(statistics.fmean(overlap_r), 4) if overlap_r else 0,
            "median": round(statistics.median(overlap_r), 4) if overlap_r else 0,
        },
        "overlap_ratio_markdown": {
            "min": round(min(overlap_m), 4) if overlap_m else 0,
            "max": round(max(overlap_m), 4) if overlap_m else 0,
            "mean": round(statistics.fmean(overlap_m), 4) if overlap_m else 0,
            "median": round(statistics.median(overlap_m), 4) if overlap_m else 0,
        },
        "per_page": per_page,
    }
    out_path = pilot_dir / "intersection-preflight.json"
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Pages with markdown: {len(per_page)}")
    print(f"Survivors (>= {args.min_chars} chars): {len(survivors)}")
    print(f"Intersection chars  min={summary['chars']['min']}  median={summary['chars']['median']}  max={summary['chars']['max']}")
    print(
        f"Overlap (rendered)  min={summary['overlap_ratio_rendered']['min']}  "
        f"median={summary['overlap_ratio_rendered']['median']}  "
        f"max={summary['overlap_ratio_rendered']['max']}"
    )
    print(
        f"Overlap (markdown)  min={summary['overlap_ratio_markdown']['min']}  "
        f"median={summary['overlap_ratio_markdown']['median']}  "
        f"max={summary['overlap_ratio_markdown']['max']}"
    )
    print()
    print(f"{'slug':60s}  chars  ovR    ovM    surv")
    for e in per_page:
        print(
            f"  {e['slug'][:58]:58s}  {e['chars']:5d}  "
            f"{e['overlap_ratio_rendered']:.2f}   "
            f"{e['overlap_ratio_markdown']:.2f}   "
            f"{'Y' if e['survives_min_chars'] else 'n'}"
        )
    print()
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
