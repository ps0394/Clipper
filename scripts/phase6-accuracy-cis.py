"""F3.4 90% confidence intervals on corpus-002 accuracy.

Bootstrap (percentile) CIs at 90% for `accuracy_rendered` on corpus-002:
- overall (n=43)
- per vendor
- per content-type profile
- per tier

Reads `per-page.csv`. Writes a JSON blob and prints a summary table.

This uses the *single-judge* accuracy numbers that shipped on corpus-002.
When F3.2 lands 2 additional judges, a companion script will compute
cross-judge accuracy CIs; the two CIs should be compared, not merged.

Usage:
    python scripts/phase6-accuracy-cis.py \
        --csv evaluation/phase5-results/corpus-002-analysis/per-page.csv \
        --out evaluation/phase5-results/corpus-002-analysis/accuracy-cis.json
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import defaultdict
from pathlib import Path


def bootstrap_ci(values: list[float], n_iter: int, alpha: float, rng: random.Random) -> dict:
    n = len(values)
    if n == 0:
        return {"n": 0, "mean": None, "ci_low": None, "ci_high": None}
    if n == 1:
        v = values[0]
        return {"n": 1, "mean": v, "ci_low": v, "ci_high": v,
                "note": "n=1; no interval"}
    means = []
    for _ in range(n_iter):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo_idx = int(n_iter * alpha / 2)
    hi_idx = int(n_iter * (1 - alpha / 2)) - 1
    return {
        "n": n,
        "mean": round(sum(values) / n, 4),
        "ci_low": round(means[lo_idx], 4),
        "ci_high": round(means[hi_idx], 4),
        "alpha": alpha,
        "n_bootstrap": n_iter,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--csv", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--n-bootstrap", type=int, default=10000)
    p.add_argument("--alpha", type=float, default=0.10,
                   help="tail probability (default 0.10 => 90 percent CI)")
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    rng = random.Random(args.seed)

    rows = list(csv.DictReader(args.csv.open(encoding="utf-8")))

    # Use accuracy_rendered (where present) as the primary target.
    scored = []
    for r in rows:
        acc = r.get("accuracy_rendered") or ""
        if not acc:
            continue
        try:
            scored.append({
                "slug":    r["slug"],
                "vendor":  r["vendor"],
                "profile": r["profile"],
                "tier":    r["tier"],
                "acc":     float(acc),
            })
        except (ValueError, KeyError):
            continue

    overall = bootstrap_ci([r["acc"] for r in scored], args.n_bootstrap, args.alpha, rng)

    by_vendor = {}
    groups = defaultdict(list)
    for r in scored:
        groups[r["vendor"]].append(r["acc"])
    for k, v in sorted(groups.items()):
        by_vendor[k] = bootstrap_ci(v, args.n_bootstrap, args.alpha, rng)

    by_profile = {}
    groups = defaultdict(list)
    for r in scored:
        groups[r["profile"]].append(r["acc"])
    for k, v in sorted(groups.items()):
        by_profile[k] = bootstrap_ci(v, args.n_bootstrap, args.alpha, rng)

    by_tier = {}
    groups = defaultdict(list)
    for r in scored:
        groups[r["tier"]].append(r["acc"])
    for k, v in sorted(groups.items()):
        by_tier[k] = bootstrap_ci(v, args.n_bootstrap, args.alpha, rng)

    out = {
        "source_csv": str(args.csv).replace("\\", "/"),
        "metric": "accuracy_rendered",
        "judge": "single-judge (corpus-002 primary judge)",
        "alpha": args.alpha,
        "n_bootstrap": args.n_bootstrap,
        "seed": args.seed,
        "overall": overall,
        "by_vendor": by_vendor,
        "by_profile": by_profile,
        "by_tier": by_tier,
        "caveats": [
            "Single-judge CIs. Grader uncertainty across judges is not "
            "captured here; F3.2/F3.3 will add cross-judge variance.",
            "Percentile bootstrap over pages; assumes pages are "
            "exchangeable within each stratum.",
            "Small-n strata (anything with n<5) yield wide, uninformative "
            "intervals. Report them but treat as diagnostic only.",
        ],
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2), encoding="utf-8")

    def fmt(ci: dict) -> str:
        if ci["n"] == 0:
            return "n=0"
        if ci.get("note"):
            return f"n={ci['n']:>2} mean={ci['mean']:.3f} (n=1; no interval)"
        return (f"n={ci['n']:>2} mean={ci['mean']:.3f} "
                f"90% CI [{ci['ci_low']:.3f}, {ci['ci_high']:.3f}]")

    print(f"Overall:  {fmt(overall)}")
    print()
    print("By vendor:")
    for k, ci in by_vendor.items():
        print(f"  {k:<12} {fmt(ci)}")
    print()
    print("By profile:")
    for k, ci in by_profile.items():
        print(f"  {k:<12} {fmt(ci)}")
    print()
    print("By tier:")
    for k, ci in by_tier.items():
        print(f"  {k:<12} {fmt(ci)}")
    print()
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
