"""F2.6 v2 regression check against corpus-002.

Recomputes each page's v2 headline score by:
  1. Subtracting the agent_content_hints subscore from http_compliance
     (v2 demotes those signals to diagnostic-only; see PRD F2.2/F2.3).
     Applies the min(sum, 100) cap that the scorer uses.
  2. Applying V2_WEIGHTS (content_extractability=0.50, http_compliance=0.50).

Then correlates the recomputed composite with accuracy_rendered from the
per-page CSV and reports pass/fail against the +0.35 ship gate.

Also writes a per-page diff table so individual pages can be inspected.

Usage:
    python scripts/v2-regression-corpus002.py \
        --corpus evaluation/phase5-results/corpus-002 \
        --analysis evaluation/phase5-results/corpus-002-analysis \
        --out evaluation/phase5-results/corpus-002-analysis/v2-regression.json
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


V2_WEIGHTS = {
    'semantic_html':           0.00,
    'content_extractability':  0.50,
    'structured_data':         0.00,
    'dom_navigability':        0.00,
    'metadata_completeness':   0.00,
    'http_compliance':         0.50,
}
GATE_THRESHOLD = 0.35


def pearson_r(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 3:
        return float("nan")
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return float("nan")
    return num / (dx * dy)


def load_v1_scores(corpus_root: Path, slug: str) -> dict | None:
    path = corpus_root / slug / "clipper-scores.rendered.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def recompute_v2(scores_json: dict) -> dict:
    """Arithmetically derive the v2 pillar scores and headline composite
    from the v1 on-disk score JSON. Used by the F2.6 regression check so we
    don't need to re-run the full scorer pipeline across 43 pages."""

    component_scores = dict(scores_json["component_scores"])
    audit = scores_json.get("audit_trail", {})

    # http_compliance in v2 = v1 http_compliance minus agent_content_hints,
    # capped at 100 (matching the scorer's min(sum, 100) cap). We
    # reconstruct the uncapped sum from the audit breakdown, subtract
    # the hint contribution, then recap.
    http_audit = audit.get("http_compliance", {})
    breakdown = http_audit.get("score_breakdown", {})
    hints_points = float(breakdown.get("agent_content_hints", 0) or 0)

    if breakdown:
        uncapped_v1 = sum(float(v or 0) for v in breakdown.values())
        uncapped_v2 = uncapped_v1 - hints_points
        component_scores["http_compliance"] = min(max(uncapped_v2, 0.0), 100.0)
        http_adjust_note = (
            f"v1_uncapped={uncapped_v1:.1f} - hints={hints_points:.1f} = "
            f"v2_uncapped={uncapped_v2:.1f} (capped at 100)"
        )
    else:
        # Fall-through: breakdown missing. Leave http_compliance as-is and
        # flag the page in the output.
        http_adjust_note = "no_score_breakdown_available"

    # v2 headline composite
    composite = sum(
        component_scores[p] * V2_WEIGHTS[p] for p in V2_WEIGHTS
    )

    return {
        "component_scores_v2": component_scores,
        "headline_v2": composite,
        "hints_points_subtracted": hints_points,
        "http_adjust_note": http_adjust_note,
        "headline_v1_parseability": scores_json.get("parseability_score"),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--corpus", required=True, type=Path)
    p.add_argument("--analysis", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--gate", type=float, default=GATE_THRESHOLD)
    args = p.parse_args()

    per_page_csv = args.analysis / "per-page.csv"
    rows = list(csv.DictReader(per_page_csv.open(encoding="utf-8")))

    per_page_results = []
    accs = []
    v2_heads = []
    v1_heads = []
    skipped = []

    for row in rows:
        slug = row["slug"]
        acc_str = row.get("accuracy_rendered") or ""
        if not acc_str:
            skipped.append({"slug": slug, "reason": "no_accuracy_rendered"})
            continue
        try:
            acc = float(acc_str)
        except ValueError:
            skipped.append({"slug": slug, "reason": "bad_accuracy_value"})
            continue
        scores_json = load_v1_scores(args.corpus, slug)
        if scores_json is None:
            skipped.append({"slug": slug, "reason": "missing_scores_json"})
            continue

        v2 = recompute_v2(scores_json)
        per_page_results.append({
            "slug": slug,
            "accuracy_rendered": acc,
            "v1_parseability": v2["headline_v1_parseability"],
            "v2_headline": v2["headline_v2"],
            "delta_v2_minus_v1": (
                v2["headline_v2"] - v2["headline_v1_parseability"]
                if v2["headline_v1_parseability"] is not None else None
            ),
            "hints_points_subtracted": v2["hints_points_subtracted"],
            "http_adjust_note": v2["http_adjust_note"],
            "component_scores_v2": v2["component_scores_v2"],
        })
        accs.append(acc)
        v2_heads.append(v2["headline_v2"])
        if v2["headline_v1_parseability"] is not None:
            v1_heads.append(v2["headline_v1_parseability"])

    r_v2 = pearson_r(v2_heads, accs)
    r_v1 = pearson_r(v1_heads, accs) if len(v1_heads) == len(accs) else float("nan")

    summary = {
        "gate_threshold": args.gate,
        "n_samples": len(accs),
        "n_skipped": len(skipped),
        "skipped": skipped,
        "headline_pearson_r": {
            "v1_parseability_vs_accuracy": None if math.isnan(r_v1) else round(r_v1, 4),
            "v2_composite_vs_accuracy":    None if math.isnan(r_v2) else round(r_v2, 4),
        },
        "v2_gate_passes": (not math.isnan(r_v2)) and r_v2 >= args.gate,
        "v2_stats": {
            "mean": round(sum(v2_heads) / len(v2_heads), 2) if v2_heads else None,
            "min":  round(min(v2_heads), 2) if v2_heads else None,
            "max":  round(max(v2_heads), 2) if v2_heads else None,
        },
        "v1_stats": {
            "mean": round(sum(v1_heads) / len(v1_heads), 2) if v1_heads else None,
            "min":  round(min(v1_heads), 2) if v1_heads else None,
            "max":  round(max(v1_heads), 2) if v1_heads else None,
        },
        "per_page": per_page_results,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # Console summary
    print(f"N = {summary['n_samples']} pages (skipped {summary['n_skipped']})")
    print(f"Gate: r >= {args.gate}")
    print()
    print(f"{'metric':<40} {'value':>8}")
    print("-" * 52)
    print(f"{'v1 parseability mean':<40} {summary['v1_stats']['mean']:>8.2f}")
    print(f"{'v2 headline mean':<40} {summary['v2_stats']['mean']:>8.2f}")
    print(f"{'Pearson r (v1_parseability vs acc)':<40} {r_v1:>+8.4f}")
    print(f"{'Pearson r (v2 vs acc)':<40} {r_v2:>+8.4f}")
    print()
    if summary["v2_gate_passes"]:
        print(f"RESULT: v2 gate PASSED (r={r_v2:+.4f} >= {args.gate})")
    else:
        print(f"RESULT: v2 gate FAILED (r={r_v2:+.4f} < {args.gate}). "
              f"Do not ship; investigate before proceeding.")

    print(f"\nWrote {args.out}")
    return 0 if summary["v2_gate_passes"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
