"""Projected correlation gate for F1.2.

Re-weights existing corpus-002 pillar values with multiple candidate weight sets
and computes Pearson r between the re-weighted composite and rendered accuracy.

Gate: at least one candidate must reach r >= +0.35 for v2 to be worth shipping.

Usage:
    python scripts/projected-correlation-gate.py \
        --corpus evaluation/phase5-results/corpus-002 \
        --analysis evaluation/phase5-results/corpus-002-analysis \
        --out evaluation/phase5-results/corpus-002-analysis/projected-gate.json
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


PILLAR_KEYS = [
    "semantic_html",
    "content_extractability",
    "structured_data",
    "dom_navigability",
    "metadata_completeness",
    "http_compliance",
]


# Candidate weight sets. Keys must match PILLAR_KEYS and sum to 1.0.
CANDIDATE_WEIGHTS = {
    # v1 baseline (article profile — current universal weights)
    "v1_baseline_article": {
        "semantic_html": 0.25,
        "content_extractability": 0.20,
        "structured_data": 0.20,
        "dom_navigability": 0.15,
        "metadata_completeness": 0.10,
        "http_compliance": 0.10,
    },
    # Candidate A: strongly boost content_extractability, cut semantic_html
    "A_extractability_40": {
        "semantic_html": 0.10,
        "content_extractability": 0.40,
        "structured_data": 0.10,
        "dom_navigability": 0.10,
        "metadata_completeness": 0.15,
        "http_compliance": 0.15,
    },
    # Candidate B: moderate boost
    "B_extractability_35": {
        "semantic_html": 0.10,
        "content_extractability": 0.35,
        "structured_data": 0.15,
        "dom_navigability": 0.10,
        "metadata_completeness": 0.15,
        "http_compliance": 0.15,
    },
    # Candidate C: conservative boost
    "C_extractability_30": {
        "semantic_html": 0.15,
        "content_extractability": 0.30,
        "structured_data": 0.15,
        "dom_navigability": 0.10,
        "metadata_completeness": 0.15,
        "http_compliance": 0.15,
    },
    # Candidate D: drop negative-correlation pillars harder
    "D_drop_semantic_and_dom": {
        "semantic_html": 0.05,
        "content_extractability": 0.40,
        "structured_data": 0.15,
        "dom_navigability": 0.05,
        "metadata_completeness": 0.20,
        "http_compliance": 0.15,
    },
    # Candidate E: lead with HTTP + metadata (both positive correlates)
    "E_http_metadata_lift": {
        "semantic_html": 0.05,
        "content_extractability": 0.30,
        "structured_data": 0.15,
        "dom_navigability": 0.05,
        "metadata_completeness": 0.20,
        "http_compliance": 0.25,
    },
}


def pearson_r(xs: list[float], ys: list[float]) -> tuple[float, int]:
    n = len(xs)
    if n < 3:
        return (float("nan"), n)
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return (float("nan"), n)
    return (num / (dx * dy), n)


def load_pillars(corpus_root: Path, slug: str) -> dict[str, float] | None:
    path = corpus_root / slug / "clipper-scores.rendered.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    cs = data.get("component_scores")
    if not isinstance(cs, dict):
        return None
    out = {}
    for k in PILLAR_KEYS:
        v = cs.get(k)
        if v is None:
            return None
        try:
            out[k] = float(v)
        except (TypeError, ValueError):
            return None
    return out


def composite(pillars: dict[str, float], weights: dict[str, float]) -> float:
    return sum(pillars[k] * weights[k] for k in PILLAR_KEYS)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--corpus", required=True, type=Path)
    p.add_argument("--analysis", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--gate", type=float, default=0.35, help="Minimum Pearson r gate")
    args = p.parse_args()

    per_page_csv = args.analysis / "per-page.csv"
    rows = list(csv.DictReader(per_page_csv.open(encoding="utf-8")))

    # Build aligned lists: (slug, pillars_dict, accuracy_rendered)
    samples = []
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
        pillars = load_pillars(args.corpus, slug)
        if pillars is None:
            skipped.append({"slug": slug, "reason": "missing_pillars"})
            continue
        samples.append({"slug": slug, "pillars": pillars, "accuracy_rendered": acc})

    results = {}
    for name, weights in CANDIDATE_WEIGHTS.items():
        wsum = sum(weights.values())
        if abs(wsum - 1.0) > 1e-6:
            raise SystemExit(f"Weights for {name} do not sum to 1.0 (sum={wsum})")
        composites = [composite(s["pillars"], weights) for s in samples]
        accs = [s["accuracy_rendered"] for s in samples]
        r, n = pearson_r(composites, accs)
        results[name] = {
            "weights": weights,
            "pearson_r": None if math.isnan(r) else round(r, 4),
            "n": n,
            "composite_mean": round(sum(composites) / n, 2) if n else None,
            "composite_min": round(min(composites), 2) if n else None,
            "composite_max": round(max(composites), 2) if n else None,
            "passes_gate": (not math.isnan(r)) and r >= args.gate,
        }

    summary = {
        "corpus": str(args.corpus),
        "gate_threshold": args.gate,
        "n_samples": len(samples),
        "n_skipped": len(skipped),
        "skipped": skipped,
        "candidates": results,
        "any_candidate_passes_gate": any(v["passes_gate"] for v in results.values()),
        "best_candidate": max(
            (k for k in results if results[k]["pearson_r"] is not None),
            key=lambda k: results[k]["pearson_r"],
            default=None,
        ),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # Console report
    print(f"N = {summary['n_samples']}  (skipped: {summary['n_skipped']})")
    print(f"Gate: r >= {args.gate}")
    print()
    print(f"{'candidate':<28} {'r':>8} {'mean':>7} {'min':>7} {'max':>7}  gate")
    print("-" * 70)
    for name in CANDIDATE_WEIGHTS:
        row = results[name]
        r_str = f"{row['pearson_r']:+.3f}" if row["pearson_r"] is not None else "  n/a "
        gate_str = "PASS" if row["passes_gate"] else "fail"
        print(
            f"{name:<28} {r_str:>8} "
            f"{row['composite_mean']:>7.2f} "
            f"{row['composite_min']:>7.2f} "
            f"{row['composite_max']:>7.2f}  {gate_str}"
        )
    print()
    if summary["any_candidate_passes_gate"]:
        best = summary["best_candidate"]
        print(f"RESULT: gate PASSED. Best: {best} (r={results[best]['pearson_r']:+.3f})")
    else:
        print("RESULT: gate FAILED. No candidate reaches r >= "
              f"{args.gate}. Do not ship v2 weights without re-investigation.")

    print(f"\nWrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
