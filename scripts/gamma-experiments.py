"""Gamma experiments: expanded composite formulations for Session 1 decision gate.

Runs 5 families of experiments on corpus-002 pillar data to test whether
composite *function* (not weights alone) is the bottleneck on r >= +0.35.

Decision rule (committed before run):
  best_r >= 0.35           -> ship v2 with best gamma composite (alpha)
  0.32 <= best_r < 0.35    -> ship v2 with Candidate D weights (alpha-with-D)
  best_r < 0.32            -> defer v2; jump to Session 3 (beta)

Usage:
    python scripts/gamma-experiments.py \
        --corpus evaluation/phase5-results/corpus-002 \
        --analysis evaluation/phase5-results/corpus-002-analysis \
        --out evaluation/phase5-results/corpus-002-analysis/gamma-experiments.json
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from pathlib import Path


PILLAR_KEYS = [
    "semantic_html",
    "content_extractability",
    "structured_data",
    "dom_navigability",
    "metadata_completeness",
    "http_compliance",
]

# Candidate D from F1.2 (best from prior gate), used as reference weights.
CAND_D = {
    "semantic_html": 0.05,
    "content_extractability": 0.40,
    "structured_data": 0.15,
    "dom_navigability": 0.05,
    "metadata_completeness": 0.20,
    "http_compliance": 0.15,
}

V1_WEIGHTS = {
    "semantic_html": 0.25,
    "content_extractability": 0.20,
    "structured_data": 0.20,
    "dom_navigability": 0.15,
    "metadata_completeness": 0.10,
    "http_compliance": 0.10,
}

# Gate thresholds
GATE_SHIP = 0.35
GATE_DIRECTIONAL = 0.32


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


def load_samples(corpus: Path, analysis: Path) -> list[dict]:
    rows = list(csv.DictReader((analysis / "per-page.csv").open(encoding="utf-8")))
    samples = []
    for row in rows:
        acc_str = row.get("accuracy_rendered") or ""
        if not acc_str:
            continue
        try:
            acc = float(acc_str)
        except ValueError:
            continue
        pillars = load_pillars(corpus, row["slug"])
        if pillars is None:
            continue
        samples.append({"slug": row["slug"], "pillars": pillars, "accuracy_rendered": acc})
    return samples


def weighted_composite(pillars: dict[str, float], weights: dict[str, float]) -> float:
    return sum(pillars[k] * weights[k] for k in weights)


def normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    s = sum(weights.values())
    if s == 0:
        return weights
    return {k: v / s for k, v in weights.items()}


# ---------------------------------------------------------------------------
# Experiment 1: pillar drop-outs with remaining weights renormalized (using D)
# ---------------------------------------------------------------------------
def experiment_dropouts(samples: list[dict]) -> list[dict]:
    accs = [s["accuracy_rendered"] for s in samples]
    results = []
    for drop in PILLAR_KEYS:
        remaining = {k: CAND_D[k] for k in PILLAR_KEYS if k != drop}
        remaining = normalize_weights(remaining)
        composites = [weighted_composite(s["pillars"], remaining) for s in samples]
        r = pearson_r(composites, accs)
        results.append({
            "name": f"dropout_{drop}",
            "dropped_pillar": drop,
            "weights": remaining,
            "pearson_r": None if math.isnan(r) else round(r, 4),
        })
    return results


# ---------------------------------------------------------------------------
# Experiment 2: top-k pillars by F1.2 single-pillar correlation
# ---------------------------------------------------------------------------
def experiment_topk(samples: list[dict]) -> list[dict]:
    accs = [s["accuracy_rendered"] for s in samples]
    single_r = {}
    for k in PILLAR_KEYS:
        xs = [s["pillars"][k] for s in samples]
        single_r[k] = pearson_r(xs, accs)

    ranked = sorted(PILLAR_KEYS, key=lambda k: single_r[k], reverse=True)

    results = []
    for k_count in (2, 3, 4):
        top = ranked[:k_count]
        # Equal weights
        eq_weights = normalize_weights({k: 1.0 for k in top})
        eq_comp = [weighted_composite(s["pillars"], eq_weights) for s in samples]
        r_eq = pearson_r(eq_comp, accs)
        results.append({
            "name": f"top{k_count}_equal",
            "pillars": top,
            "weights": eq_weights,
            "pearson_r": None if math.isnan(r_eq) else round(r_eq, 4),
        })

        # Correlation-proportional weights (only positive r's)
        pos = {k: max(single_r[k], 0.0) for k in top}
        if sum(pos.values()) > 0:
            prop_weights = normalize_weights(pos)
            prop_comp = [weighted_composite(s["pillars"], prop_weights) for s in samples]
            r_prop = pearson_r(prop_comp, accs)
            results.append({
                "name": f"top{k_count}_corr_proportional",
                "pillars": top,
                "weights": prop_weights,
                "pearson_r": None if math.isnan(r_prop) else round(r_prop, 4),
            })

    results.append({
        "name": "_single_pillar_correlations",
        "single_pillar_r": {k: round(v, 4) for k, v in single_r.items()},
        "ranked": ranked,
    })
    return results


# ---------------------------------------------------------------------------
# Experiment 3: z-score normalized composite
# ---------------------------------------------------------------------------
def experiment_zscore(samples: list[dict]) -> list[dict]:
    accs = [s["accuracy_rendered"] for s in samples]
    # Compute per-pillar mean and stdev across corpus-002
    means = {}
    stdevs = {}
    for k in PILLAR_KEYS:
        vals = [s["pillars"][k] for s in samples]
        means[k] = statistics.mean(vals)
        stdevs[k] = statistics.pstdev(vals) or 1.0

    def z_pillars(p: dict[str, float]) -> dict[str, float]:
        return {k: (p[k] - means[k]) / stdevs[k] for k in PILLAR_KEYS}

    results = []
    for label, weights in (("z_v1", V1_WEIGHTS), ("z_candidate_D", CAND_D)):
        composites = [weighted_composite(z_pillars(s["pillars"]), weights) for s in samples]
        r = pearson_r(composites, accs)
        results.append({
            "name": f"zscore_{label}",
            "weights": weights,
            "pearson_r": None if math.isnan(r) else round(r, 4),
        })
    return results


# ---------------------------------------------------------------------------
# Experiment 4: rank-based composite
# ---------------------------------------------------------------------------
def experiment_rank(samples: list[dict]) -> list[dict]:
    accs = [s["accuracy_rendered"] for s in samples]
    n = len(samples)

    # For each pillar, rank samples (1 = highest pillar value). Ties get average rank.
    ranks_per_pillar: dict[str, list[float]] = {}
    for k in PILLAR_KEYS:
        pairs = sorted(enumerate(samples), key=lambda it: it[1]["pillars"][k], reverse=True)
        rank_list = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and pairs[j + 1][1]["pillars"][k] == pairs[i][1]["pillars"][k]:
                j += 1
            avg_rank = (i + j) / 2 + 1  # 1-indexed average
            for m in range(i, j + 1):
                rank_list[pairs[m][0]] = avg_rank
            i = j + 1
        ranks_per_pillar[k] = rank_list

    # Weighted average rank with Candidate D. Lower rank = better, so negate for r sign.
    avg_ranks = []
    for idx in range(n):
        r_val = sum(CAND_D[k] * ranks_per_pillar[k][idx] for k in PILLAR_KEYS)
        avg_ranks.append(r_val)

    # Correlate NEGATED rank with accuracy (so positive r means "better rank -> higher acc")
    neg_ranks = [-x for x in avg_ranks]
    r = pearson_r(neg_ranks, accs)
    return [{
        "name": "rank_based_candidate_D",
        "weights": CAND_D,
        "pearson_r": None if math.isnan(r) else round(r, 4),
        "note": "Per-pillar rank with D weights; sign flipped so higher = better.",
    }]


# ---------------------------------------------------------------------------
# Experiment 5: binary-gate composite (per-pillar threshold at median)
# ---------------------------------------------------------------------------
def experiment_binary(samples: list[dict]) -> list[dict]:
    accs = [s["accuracy_rendered"] for s in samples]
    medians = {k: statistics.median(s["pillars"][k] for s in samples) for k in PILLAR_KEYS}

    composites = []
    for s in samples:
        score = sum(CAND_D[k] * (1.0 if s["pillars"][k] >= medians[k] else 0.0) for k in PILLAR_KEYS)
        composites.append(score)
    r = pearson_r(composites, accs)
    return [{
        "name": "binary_median_gate_candidate_D",
        "weights": CAND_D,
        "medians": {k: round(v, 2) for k, v in medians.items()},
        "pearson_r": None if math.isnan(r) else round(r, 4),
    }]


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
def flat_candidates(all_results: dict) -> list[tuple[str, float]]:
    """Return (name, r) for every candidate that has a numeric pearson_r."""
    out = []
    for group_name, entries in all_results.items():
        for e in entries:
            if e.get("pearson_r") is None:
                continue
            out.append((f"{group_name}::{e['name']}", e["pearson_r"]))
    return out


def decide(best_r: float) -> str:
    if best_r >= GATE_SHIP:
        return "alpha_ship_best_gamma"
    if best_r >= GATE_DIRECTIONAL:
        return "alpha_ship_candidate_D"
    return "beta_defer_to_session_3"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--corpus", required=True, type=Path)
    p.add_argument("--analysis", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()

    samples = load_samples(args.corpus, args.analysis)
    n = len(samples)

    groups = {
        "1_dropouts": experiment_dropouts(samples),
        "2_topk": experiment_topk(samples),
        "3_zscore": experiment_zscore(samples),
        "4_rank": experiment_rank(samples),
        "5_binary": experiment_binary(samples),
    }

    flat = flat_candidates(groups)
    best_name, best_r = max(flat, key=lambda t: t[1]) if flat else ("n/a", float("nan"))

    summary = {
        "n_samples": n,
        "gate_ship": GATE_SHIP,
        "gate_directional": GATE_DIRECTIONAL,
        "experiments": groups,
        "best_candidate": {"name": best_name, "pearson_r": best_r},
        "decision_branch": decide(best_r),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # Console report
    print(f"N = {n}")
    print(f"Gates: ship >= {GATE_SHIP}, directional >= {GATE_DIRECTIONAL}")
    print()
    for group_name, entries in groups.items():
        print(f"[{group_name}]")
        for e in entries:
            if "pearson_r" not in e:
                # meta row
                continue
            r_str = f"{e['pearson_r']:+.4f}" if e['pearson_r'] is not None else "  n/a "
            print(f"  {e['name']:<38} r = {r_str}")
        print()

    print(f"BEST: {best_name}  r = {best_r:+.4f}")
    print(f"DECISION BRANCH: {summary['decision_branch']}")
    print(f"\nWrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
