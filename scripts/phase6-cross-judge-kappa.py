"""F3.3 Cross-judge Cohen's kappa on corpus-002 grades.

Scans each corpus-002 page directory for JSON grade files matching
`grades.*.judged.rendered.json`, aligns their labels pair-by-pair on
(pair_index, run_index), and computes Cohen's kappa for every judge pair:
  - per-page kappa (on that page's <=N grades)
  - overall kappa (pooled across all pages)

Also reports per-judge accuracy (fraction labeled 'correct') so judge
severity differences are visible alongside agreement.

Writes a JSON report; prints a compact table.

Handles the degenerate case of a single judge:
  - Reports the one judge's pooled accuracy.
  - Emits `judge_pairs: []` (nothing to compare) and notes in the output
    that F3.2 needs to run before kappa numbers can be produced.

Usage:
    python scripts/phase6-cross-judge-kappa.py \
        --corpus evaluation/phase5-results/corpus-002 \
        --out evaluation/phase5-results/corpus-002-analysis/cross-judge-kappa.json
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from itertools import combinations
from pathlib import Path


# Matches e.g. `grades.primary.judged.rendered.json`,
# `grades.claude35.judged.rendered.json`, `grades.geminiPro.judged.rendered.json`.
GRADES_PATTERN = re.compile(r"^grades\.(?P<judge>[^.]+)\.judged\.rendered\.json$")


def cohens_kappa(labels_a: list[str], labels_b: list[str]) -> float:
    if len(labels_a) != len(labels_b):
        raise ValueError("sequences must be equal length")
    n = len(labels_a)
    if n == 0:
        return float("nan")
    cats = sorted(set(labels_a) | set(labels_b))
    if len(cats) < 2:
        return float("nan")  # agreement undefined with a single category
    agree = sum(1 for a, b in zip(labels_a, labels_b) if a == b)
    p_o = agree / n
    p_e = 0.0
    for c in cats:
        p_a = labels_a.count(c) / n
        p_b = labels_b.count(c) / n
        p_e += p_a * p_b
    if p_e >= 1.0:
        return float("nan")
    return (p_o - p_e) / (1.0 - p_e)


def load_judge_grades(path: Path) -> dict[tuple[int, int], str]:
    """Return {(pair_index, run_index): label} from a judged-grades JSON."""
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[tuple[int, int], str] = {}
    for g in data:
        key = (int(g["pair_index"]), int(g["run_index"]))
        out[key] = g["label"]
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--corpus", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()

    per_page_summary = []
    # judge_id -> list of labels in a fixed global ordering
    judge_label_streams: dict[str, list[str]] = defaultdict(list)
    # ordering key list for pooled stream
    pooled_keys: list[tuple[str, int, int]] = []
    # per-page per-pair kappa for downstream stats
    per_pair_kappa_samples: dict[tuple[str, str], list[float]] = defaultdict(list)

    page_dirs = sorted([d for d in args.corpus.iterdir() if d.is_dir()])
    for page_dir in page_dirs:
        judge_files = {}
        for f in page_dir.iterdir():
            m = GRADES_PATTERN.match(f.name)
            if m:
                judge_files[m.group("judge")] = f
        if not judge_files:
            continue

        judge_grades = {j: load_judge_grades(p) for j, p in judge_files.items()}
        # intersection of keys across this page's judges
        common_keys = set.intersection(*(set(g.keys()) for g in judge_grades.values()))
        ordered_keys = sorted(common_keys)

        page_entry = {
            "slug": page_dir.name,
            "judges": sorted(judge_grades.keys()),
            "n_items": len(ordered_keys),
            "per_judge_accuracy": {
                j: round(
                    sum(1 for k in ordered_keys if judge_grades[j][k] == "correct")
                    / len(ordered_keys), 4
                ) if ordered_keys else None
                for j in judge_grades
            },
            "pairwise_kappa": {},
        }

        for a, b in combinations(sorted(judge_grades.keys()), 2):
            la = [judge_grades[a][k] for k in ordered_keys]
            lb = [judge_grades[b][k] for k in ordered_keys]
            k = cohens_kappa(la, lb)
            k_out = None if (k != k) else round(k, 4)  # NaN check
            page_entry["pairwise_kappa"][f"{a}__vs__{b}"] = {
                "kappa": k_out,
                "n_items": len(la),
                "pct_agree": round(
                    sum(1 for x, y in zip(la, lb) if x == y) / len(la), 4
                ) if la else None,
            }
            if k_out is not None:
                per_pair_kappa_samples[(a, b)].append(k_out)

        per_page_summary.append(page_entry)

        for j, grades in judge_grades.items():
            for k in ordered_keys:
                judge_label_streams[j].append(grades[k])
                if j == sorted(judge_grades.keys())[0]:
                    pooled_keys.append((page_dir.name, k[0], k[1]))

    all_judges = sorted(judge_label_streams.keys())
    pooled_per_judge = {}
    for j in all_judges:
        labels = judge_label_streams[j]
        if labels:
            pooled_per_judge[j] = {
                "n_items": len(labels),
                "accuracy": round(sum(1 for l in labels if l == "correct") / len(labels), 4),
            }

    pooled_kappa = {}
    for a, b in combinations(all_judges, 2):
        la = judge_label_streams[a]
        lb = judge_label_streams[b]
        # align on the minimum length in case one judge failed on some pages
        n = min(len(la), len(lb))
        k = cohens_kappa(la[:n], lb[:n])
        k_out = None if (k != k) else round(k, 4)
        samples = per_pair_kappa_samples.get((a, b), [])
        below_cutoff = sum(1 for s in samples if s < 0.60)
        pct_below = round(below_cutoff / len(samples), 4) if samples else None
        pooled_kappa[f"{a}__vs__{b}"] = {
            "kappa_pooled": k_out,
            "n_items": n,
            "per_page_kappa_below_0.60": {
                "count": below_cutoff,
                "of_total": len(samples),
                "fraction": pct_below,
            },
        }

    if len(all_judges) < 2:
        warning = (
            "Only one judge found in corpus-002 grades. Cross-judge kappa "
            "is not computable until F3.2 runs (regrade corpus-002 with 2 "
            "additional judges). This script will emit kappa numbers "
            "automatically on the next run once those files exist."
        )
    else:
        warning = None

    out = {
        "n_pages": len(per_page_summary),
        "judges_found": all_judges,
        "pooled_per_judge": pooled_per_judge,
        "pooled_kappa": pooled_kappa,
        "warning": warning,
        "per_page": per_page_summary,
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2), encoding="utf-8")

    # Console
    print(f"Pages: {len(per_page_summary)}")
    print(f"Judges found: {', '.join(all_judges) if all_judges else '(none)'}")
    print()
    for j, s in pooled_per_judge.items():
        print(f"  {j:<12} n={s['n_items']:>3} accuracy={s['accuracy']:.3f}")
    print()
    if pooled_kappa:
        print("Pooled pairwise kappa:")
        for pair, info in pooled_kappa.items():
            k = info["kappa_pooled"]
            ks = f"{k:+.4f}" if k is not None else "undefined"
            below = info["per_page_kappa_below_0.60"]
            print(f"  {pair:<40} kappa={ks}  "
                  f"pages_kappa<0.60: {below['count']}/{below['of_total']}")
    else:
        print("(Pairwise kappa requires >=2 judges; warning recorded in output.)")
    if warning:
        print()
        print("WARNING:", warning)
    print()
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
