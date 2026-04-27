"""F3.4 cross-judge 90% CIs on corpus-002 accuracy.

Companion to phase6-accuracy-cis.py (single-judge). This script reads all
`grades.<judge>.judged.rendered.json` files in the corpus and bootstraps:

- per-judge accuracy CI (one per judge, bootstrap over pages)
- majority-vote accuracy CI (per question: label = majority across judges; ties = mark wrong)
- "any-judge-correct" upper envelope CI
- "all-judges-correct" lower envelope CI

The union of per-judge CIs is the honest cross-judge uncertainty band on
corpus-002 headline accuracy. Should be reported alongside (not instead of)
the single-judge CI from phase6-accuracy-cis.py.

Usage:
    python scripts/phase6-cross-judge-cis.py \
        --corpus evaluation/phase5-results/corpus-002 \
        --out evaluation/phase5-results/corpus-002-analysis/cross-judge-cis.json
"""

from __future__ import annotations

import argparse
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path


GRADES_RE = re.compile(r"^grades\.(?P<judge>[^.]+)\.judged\.rendered\.json$")


def bootstrap_ci(values: list[float], n_iter: int, alpha: float, rng: random.Random) -> dict:
    n = len(values)
    if n == 0:
        return {"n": 0, "mean": None, "ci_low": None, "ci_high": None}
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


def extract_labels(grades_path: Path) -> dict[int, bool]:
    """Return {pair_index: correct_bool} for one judge on one page."""
    data = json.loads(grades_path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("answers") or data.get("graded") or []
    out: dict[int, bool] = {}
    for i, a in enumerate(data):
        if not isinstance(a, dict):
            continue
        key = a.get("pair_index", i)
        verdict = a.get("label") or a.get("verdict") or a.get("judge_verdict") or a.get("grade")
        if verdict is None:
            continue
        if isinstance(verdict, bool):
            out[key] = verdict
        elif isinstance(verdict, str):
            v = verdict.strip().lower()
            out[key] = v in ("correct", "true", "yes", "pass", "1")
        elif isinstance(verdict, (int, float)):
            out[key] = bool(verdict)
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--corpus", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--n-bootstrap", type=int, default=10000)
    p.add_argument("--alpha", type=float, default=0.10)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    rng = random.Random(args.seed)

    # Discover judges + pages
    pages: dict[str, dict[str, Path]] = defaultdict(dict)
    for page_dir in sorted(args.corpus.iterdir()):
        if not page_dir.is_dir():
            continue
        for fp in page_dir.iterdir():
            m = GRADES_RE.match(fp.name)
            if m:
                pages[page_dir.name][m.group("judge")] = fp

    if not pages:
        raise SystemExit("No grades.<judge>.judged.rendered.json files found")

    all_judges = sorted({j for p in pages.values() for j in p})
    print(f"Pages: {len(pages)}")
    print(f"Judges: {', '.join(all_judges)}")

    # Per-page per-judge accuracy + per-page majority-vote accuracy
    per_page_acc: dict[str, dict[str, float]] = {}
    per_page_majority_acc: dict[str, float] = {}
    per_page_any_acc: dict[str, float] = {}
    per_page_all_acc: dict[str, float] = {}

    for slug, judge_files in pages.items():
        judge_labels: dict[str, dict[int, bool]] = {
            j: extract_labels(fp) for j, fp in judge_files.items()
        }
        # Per-judge accuracy on this page
        per_page_acc[slug] = {}
        for j, labels in judge_labels.items():
            if labels:
                per_page_acc[slug][j] = sum(labels.values()) / len(labels)

        # Common question indices (intersection)
        if not judge_labels:
            continue
        common = set.intersection(*(set(d.keys()) for d in judge_labels.values()))
        if not common:
            continue

        n_correct_majority = 0
        n_correct_any = 0
        n_correct_all = 0
        for q in common:
            verdicts = [judge_labels[j][q] for j in judge_labels]
            n_yes = sum(1 for v in verdicts if v)
            if n_yes > len(verdicts) / 2:
                n_correct_majority += 1
            if n_yes >= 1:
                n_correct_any += 1
            if n_yes == len(verdicts):
                n_correct_all += 1
        per_page_majority_acc[slug] = n_correct_majority / len(common)
        per_page_any_acc[slug] = n_correct_any / len(common)
        per_page_all_acc[slug] = n_correct_all / len(common)

    # Bootstrap CIs over pages
    result = {
        "n_pages": len(pages),
        "judges": all_judges,
        "n_bootstrap": args.n_bootstrap,
        "alpha": args.alpha,
        "per_judge": {},
        "majority_vote": None,
        "any_judge_correct": None,
        "all_judges_correct": None,
    }
    for j in all_judges:
        vals = [per_page_acc[s][j] for s in pages if j in per_page_acc[s]]
        result["per_judge"][j] = bootstrap_ci(vals, args.n_bootstrap, args.alpha, rng)

    result["majority_vote"] = bootstrap_ci(
        list(per_page_majority_acc.values()), args.n_bootstrap, args.alpha, rng)
    result["any_judge_correct"] = bootstrap_ci(
        list(per_page_any_acc.values()), args.n_bootstrap, args.alpha, rng)
    result["all_judges_correct"] = bootstrap_ci(
        list(per_page_all_acc.values()), args.n_bootstrap, args.alpha, rng)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print()
    print("Per-judge 90% CI (bootstrap over pages):")
    for j in all_judges:
        ci = result["per_judge"][j]
        print(f"  {j:12s}  mean={ci['mean']:.4f}  CI=[{ci['ci_low']:.4f}, {ci['ci_high']:.4f}]  n={ci['n']}")
    print()
    mv = result["majority_vote"]
    print(f"  majority      mean={mv['mean']:.4f}  CI=[{mv['ci_low']:.4f}, {mv['ci_high']:.4f}]  n={mv['n']}")
    av = result["any_judge_correct"]
    print(f"  any-correct   mean={av['mean']:.4f}  CI=[{av['ci_low']:.4f}, {av['ci_high']:.4f}]  n={av['n']}")
    al = result["all_judges_correct"]
    print(f"  all-correct   mean={al['mean']:.4f}  CI=[{al['ci_low']:.4f}, {al['ci_high']:.4f}]  n={al['n']}")
    print()
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
