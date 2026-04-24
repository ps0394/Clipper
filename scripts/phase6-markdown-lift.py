"""F4.3 Served-markdown lift analysis.

Consumes (a) `tri-fetcher-probe.json` (HTTP-only probe, produced by
`scripts/phase6-tri-fetcher-probe.py`) and (b) optionally
`markdown-regrade-summary.json` (paired LLM grading, produced by
`python main.py phase5 regrade-markdown <corpus_dir>` once Foundry
deployments are approved).

Produces:
- Overall delta (accuracy_markdown - accuracy_rendered), with per-page,
  per-vendor, and overall aggregates.
- Per-resolution-path delta (accept_header vs link_alternate vs sibling_md).
- Explicit null-result output when only the probe has run. The probe
  hit-rate alone is a finding: it bounds the population for whom
  markdown lift can possibly matter.

Usage:
    python scripts/phase6-markdown-lift.py \
        --probe evaluation/phase5-results/corpus-002-analysis/tri-fetcher-probe.json \
        --regrade evaluation/phase5-results/corpus-002/markdown-regrade-summary.json \
        --out evaluation/phase5-results/corpus-002-analysis/markdown-lift.json

Run without --regrade to produce the probe-only report.
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


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--probe", required=True, type=Path,
                   help="Path to tri-fetcher-probe.json (always required).")
    p.add_argument("--regrade", type=Path, default=None,
                   help="Path to markdown-regrade-summary.json (optional; "
                        "omit for the probe-only null-result report).")
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--lift-threshold", type=float, default=0.10,
                   help="Delta threshold for the F4.4 promote-to-pillar "
                        "recommendation (default 0.10).")
    args = p.parse_args()

    probe = _load_json(args.probe)
    report: dict = {
        "probe": {
            "n_urls": probe.get("n_urls"),
            "hit_count": probe.get("hit_count"),
            "hit_rate": probe.get("hit_rate"),
            "by_probe": probe.get("by_probe"),
            "by_vendor": probe.get("by_vendor"),
        },
    }

    if args.regrade is None or not args.regrade.is_file():
        report["regrade"] = None
        report["status"] = "probe_only"
        report["f4_3_finding"] = (
            "Probe-only report: served-markdown is available on "
            f"{probe.get('hit_count')}/{probe.get('n_urls')} pages "
            f"({probe.get('hit_rate'):.1%}). Paired grading has not yet run; "
            "no lift evidence either way. F4.4 promote-to-pillar "
            "recommendation is NOT yet actionable."
        )
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Status: probe_only (no --regrade supplied).")
        print(f"Hit rate: {probe.get('hit_rate'):.1%} "
              f"({probe.get('hit_count')}/{probe.get('n_urls')})")
        print(f"By probe: {probe.get('by_probe')}")
        print()
        print(f"Wrote {args.out}")
        return 0

    regrade = _load_json(args.regrade)
    per_page = regrade.get("per_page", [])

    deltas_overall: list[float] = []
    deltas_by_vendor: dict[str, list[float]] = defaultdict(list)
    deltas_by_probe: dict[str, list[float]] = defaultdict(list)
    paired_rows: list[dict] = []

    # The regrade JSON has url but not vendor; look up vendor from probe.
    vendor_lookup = {r["url"]: r.get("vendor") for r in probe.get("results", [])}

    for entry in per_page:
        acc_md = entry.get("accuracy_markdown_judged")
        if acc_md is None:
            acc_md = entry.get("accuracy_markdown_substring")
        acc_ren = entry.get("accuracy_rendered")
        if acc_md is None or acc_ren is None:
            continue
        delta = float(acc_md) - float(acc_ren)
        rb = entry.get("resolved_by") or "(none)"
        vendor = vendor_lookup.get(entry.get("url"), "(unknown)")
        deltas_overall.append(delta)
        deltas_by_vendor[vendor].append(delta)
        deltas_by_probe[rb].append(delta)
        paired_rows.append({
            "slug": entry.get("slug"),
            "url": entry.get("url"),
            "vendor": vendor,
            "resolved_by": rb,
            "accuracy_rendered": acc_ren,
            "accuracy_markdown": acc_md,
            "delta": round(delta, 4),
        })

    overall = _agg(deltas_overall)
    by_vendor = {v: _agg(lst) for v, lst in sorted(deltas_by_vendor.items())}
    by_probe_path = {k: _agg(lst) for k, lst in sorted(deltas_by_probe.items())}

    # F4.4 recommendation
    lift_t = args.lift_threshold
    vendors_above = [v for v, a in by_vendor.items() if a.get("n", 0) and a["mean"] > lift_t]
    vendors_below = [v for v, a in by_vendor.items() if a.get("n", 0) and a["mean"] <= lift_t]
    if not overall.get("n"):
        recommendation = "no_paired_data"
        recommendation_rationale = (
            "Regrade summary present but produced no paired rows with both "
            "accuracy_markdown and accuracy_rendered. Check upstream pipeline."
        )
    elif overall["mean"] > lift_t and len(vendors_above) >= 2:
        recommendation = "promote_to_pillar_contribution"
        recommendation_rationale = (
            f"Overall mean lift {overall['mean']:+.3f} exceeds threshold "
            f"{lift_t} and ≥2 vendors show consistent lift "
            f"({vendors_above}). F4.4 condition satisfied: page-level "
            "markdown detection is recommended for promotion from "
            "diagnostic to pillar contribution in v3."
        )
    elif overall["mean"] <= 0 or (overall["mean"] <= lift_t and len(vendors_above) < 2):
        recommendation = "keep_as_diagnostic_only"
        recommendation_rationale = (
            f"Overall mean lift {overall['mean']:+.3f} does not exceed "
            f"threshold {lift_t}, or fewer than 2 vendors show consistent "
            "lift. F4.4 condition NOT satisfied. Served-markdown detection "
            "stays diagnostic-only."
        )
    else:
        recommendation = "insufficient_evidence"
        recommendation_rationale = (
            f"Overall mean lift {overall['mean']:+.3f}; vendors above "
            f"threshold: {vendors_above}. Evidence ambiguous; recommend "
            "widening corpus before promoting."
        )

    report["regrade"] = {
        "overall": overall,
        "by_vendor": by_vendor,
        "by_probe_path": by_probe_path,
        "paired": paired_rows,
    }
    report["status"] = "paired_grading_complete"
    report["f4_4_recommendation"] = recommendation
    report["f4_4_recommendation_rationale"] = recommendation_rationale
    report["lift_threshold"] = lift_t

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Status: paired_grading_complete")
    print(f"Overall (n={overall['n']}): mean delta "
          f"{overall.get('mean', 0):+.4f}  "
          f"pos={overall.get('n_positive')}  "
          f"neg={overall.get('n_negative')}  "
          f"zero={overall.get('n_zero')}")
    print()
    print("By vendor:")
    for v, a in by_vendor.items():
        if a.get("n"):
            print(f"  {v:<14} n={a['n']:>2} mean={a['mean']:+.4f}  "
                  f"median={a['median']:+.4f}  "
                  f"pos/neg={a.get('n_positive')}/{a.get('n_negative')}")
    print()
    print(f"F4.4 recommendation: {recommendation}")
    print(f"  {recommendation_rationale}")
    print()
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
