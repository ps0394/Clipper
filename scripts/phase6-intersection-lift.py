"""F4.2 Track B intersection-lift analysis.

Consumes ``intersection-regrade-summary.json`` (produced by
``python main.py phase5 regrade-intersection <pilot_dir>``) and reports
the **rendered-vs-markdown delta** computed on Q/A generated from the
content intersection of the two formats — i.e. the bias-corrected
version of the F4.2 Track A test in scripts/phase6-markdown-lift.py.

Comparison points
-----------------
- Track A delta (HTML-anchored Q/A): from
  ``markdown-lift.json``: overall mean = -0.0640 on n=25.
- Track B delta (intersection-Q/A): the question we're answering here.

Per-vendor and per-resolution-path breakdowns are produced where the
data supports it. Pages with skipped_reason are reported but excluded
from delta aggregates.

Usage:
    python scripts/phase6-intersection-lift.py \
        --regrade evaluation/phase5-results/corpus-002/intersection-regrade-summary.json \
        --baseline evaluation/phase5-results/corpus-002/markdown-regrade-summary.json \
        --out evaluation/phase5-results/corpus-002-analysis/intersection-lift.json
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _agg(deltas: list[float]) -> dict:
    if not deltas:
        return {"n": 0}
    return {
        "n": len(deltas),
        "mean": round(statistics.fmean(deltas), 4),
        "median": round(statistics.median(deltas), 4),
        "stdev": round(statistics.stdev(deltas), 4) if len(deltas) > 1 else 0.0,
        "min": round(min(deltas), 4),
        "max": round(max(deltas), 4),
        "n_positive": sum(1 for d in deltas if d > 0),
        "n_negative": sum(1 for d in deltas if d < 0),
        "n_zero": sum(1 for d in deltas if d == 0),
    }


_VENDOR_PREFIXES = {
    "anthropic": "docs-anthropic",
    "aws": "docs-aws",
    "docker": "docs-docker",
    "github": ("docs-github", "help-github"),
    "gcp": "cloud-google",
    "k8s": "kubernetes-io",
    "learn": "learn-microsoft",
    "mdn": "developer-mozilla",
    "nodejs": "nodejs-org",
    "openai": "platform-openai",
    "perplexity": "docs-perplexity",
    "postgres": "www-postgresql",
    "python": "docs-python",
    "snowflake": "docs-snowflake",
    "stripe": "docs-stripe",
    "wikipedia": "en-wikipedia",
}


def _vendor_for(slug: str) -> str:
    for vendor, prefix in _VENDOR_PREFIXES.items():
        if isinstance(prefix, tuple):
            if any(slug.startswith(p) for p in prefix):
                return vendor
        elif slug.startswith(prefix):
            return vendor
    return "other"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--regrade", required=True, type=Path,
                   help="Path to intersection-regrade-summary.json.")
    p.add_argument("--baseline", type=Path, default=None,
                   help="Optional Track A markdown-regrade-summary.json for "
                        "side-by-side comparison.")
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()

    regrade = _load_json(args.regrade)
    pages = regrade.get("per_page", [])

    judged_deltas: list[float] = []
    substring_deltas: list[float] = []
    by_vendor_judged: dict[str, list[float]] = defaultdict(list)
    by_vendor_substring: dict[str, list[float]] = defaultdict(list)

    per_page_out: list[dict] = []
    for page in pages:
        slug = page["slug"]
        vendor = _vendor_for(slug)
        skipped = page.get("skipped_reason")
        rj = page.get("accuracy_rendered_intersection_judged")
        mj = page.get("accuracy_markdown_intersection_judged")
        rs = page.get("accuracy_rendered_intersection_substring")
        ms = page.get("accuracy_markdown_intersection_substring")

        entry = {
            "slug": slug,
            "vendor": vendor,
            "skipped_reason": skipped,
            "intersection_chars": page.get("intersection_chars"),
            "overlap_ratio_rendered": page.get("overlap_ratio_rendered"),
            "overlap_ratio_markdown": page.get("overlap_ratio_markdown"),
            "rendered_judged": rj,
            "markdown_judged": mj,
            "rendered_substring": rs,
            "markdown_substring": ms,
            "delta_judged": None,
            "delta_substring": None,
        }
        if not skipped and rj is not None and mj is not None:
            entry["delta_judged"] = round(mj - rj, 4)
            judged_deltas.append(mj - rj)
            by_vendor_judged[vendor].append(mj - rj)
        if not skipped and rs is not None and ms is not None:
            entry["delta_substring"] = round(ms - rs, 4)
            substring_deltas.append(ms - rs)
            by_vendor_substring[vendor].append(ms - rs)
        per_page_out.append(entry)

    report = {
        "n_pages_seen": len(pages),
        "n_pages_scored": sum(1 for p in pages if not p.get("skipped_reason")),
        "skipped_reasons": _count_skipped(pages),
        "delta_judged": _agg(judged_deltas),
        "delta_substring": _agg(substring_deltas),
        "by_vendor_judged": {
            v: _agg(vs) for v, vs in sorted(by_vendor_judged.items())
        },
        "by_vendor_substring": {
            v: _agg(vs) for v, vs in sorted(by_vendor_substring.items())
        },
        "per_page": per_page_out,
    }

    if args.baseline is not None and args.baseline.is_file():
        baseline = _load_json(args.baseline)
        baseline_deltas = []
        for bp in baseline.get("per_page", []):
            mj = bp.get("accuracy_markdown_judged")
            rj = bp.get("accuracy_rendered")
            if mj is not None and rj is not None:
                baseline_deltas.append(mj - rj)
        report["baseline_track_a_judged"] = _agg(baseline_deltas)
        report["track_a_minus_track_b_mean"] = (
            round(report["baseline_track_a_judged"].get("mean", 0)
                  - report["delta_judged"].get("mean", 0), 4)
            if baseline_deltas and judged_deltas else None
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Console summary
    print(f"Pages seen:    {report['n_pages_seen']}")
    print(f"Pages scored:  {report['n_pages_scored']}")
    if report["skipped_reasons"]:
        print(f"Skipped:       {report['skipped_reasons']}")
    print()
    if judged_deltas:
        agg = report["delta_judged"]
        print(
            f"Track B (intersection-Q/A, judged): n={agg['n']}  "
            f"mean={agg['mean']:+.4f}  median={agg['median']:+.4f}  "
            f"pos/neg/zero={agg['n_positive']}/{agg['n_negative']}/{agg['n_zero']}"
        )
    if "baseline_track_a_judged" in report:
        a = report["baseline_track_a_judged"]
        print(
            f"Track A (HTML-Q/A, judged):         n={a['n']}  "
            f"mean={a['mean']:+.4f}  median={a['median']:+.4f}  "
            f"pos/neg/zero={a['n_positive']}/{a['n_negative']}/{a['n_zero']}"
        )
        print(
            f"Track A minus Track B (mean):       {report['track_a_minus_track_b_mean']:+.4f}  "
            "(positive = bias removed by intersection-Q/A)"
        )
    print()
    if by_vendor_judged:
        print("By vendor (judged):")
        for v, vs in sorted(by_vendor_judged.items()):
            agg = _agg(vs)
            print(
                f"  {v:<12} n={agg['n']:>2}  mean={agg['mean']:+.4f}  "
                f"median={agg['median']:+.4f}  pos/neg={agg['n_positive']}/{agg['n_negative']}"
            )
    print()
    print(f"Wrote {args.out}")
    return 0


def _count_skipped(pages: list[dict]) -> dict:
    counts: dict[str, int] = defaultdict(int)
    for p in pages:
        r = p.get("skipped_reason")
        if r:
            # Strip parenthesized detail so the counter is readable.
            tag = r.split(" ")[0]
            counts[tag] += 1
    return dict(counts)


if __name__ == "__main__":
    raise SystemExit(main())
