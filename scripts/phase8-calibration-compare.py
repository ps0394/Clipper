"""Compare human-labels against each judge on the corpus-003 calibration sample.

Reads:
  evaluation/phase5-results/corpus-003-analysis/calibration-blank.csv  (filled-in)
  evaluation/phase5-results/corpus-003-analysis/calibration-keys.json

Prints per-judge:
  - exact agreement % vs human
  - Cohen's kappa
  - per-bucket breakdown (unanimous / llama_vs_frontier / frontier_vs_frontier)
  - disagreement detail

Usage:
    python scripts/phase8-calibration-compare.py [--analysis-dir <dir>]
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List, Tuple

# import kappa from the Phase 5 module
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from retrievability.phase5.judge import cohens_kappa  # noqa: E402

JUDGES = ["primary", "gpt4o", "deepseek"]
JUDGE_DISPLAY = {
    "primary": "Llama-3.3",
    "gpt4o": "GPT-4o",
    "deepseek": "DeepSeek-V3.2",
}
VALID_LABELS = {"correct", "incorrect", "not_in_document"}


def load_human_labels(csv_path: Path) -> Dict[Tuple[str, int], str]:
    out: Dict[Tuple[str, int], str] = {}
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = (row.get("human_label") or "").strip().lower()
            if not label:
                continue
            if label not in VALID_LABELS:
                print(
                    f"[!] Invalid label {label!r} for {row.get('slug')} "
                    f"pair {row.get('pair_index')}; skipping."
                )
                continue
            out[(row["slug"], int(row["pair_index"]))] = label
    return out


def load_keys(keys_path: Path) -> Dict[Tuple[str, int], dict]:
    payload = json.loads(keys_path.read_text(encoding="utf-8"))
    return {(it["slug"], it["pair_index"]): it for it in payload["items"]}


def per_judge_stats(
    items: List[dict], human: Dict[Tuple[str, int], str]
) -> Dict[str, dict]:
    out: Dict[str, dict] = {}
    for j in JUDGES:
        h_seq: List[str] = []
        j_seq: List[str] = []
        per_bucket: Dict[str, List[Tuple[str, str]]] = {}
        disagreements: List[dict] = []
        for it in items:
            key = (it["slug"], it["pair_index"])
            if key not in human:
                continue
            h = human[key]
            jl = it["labels"][j]
            h_seq.append(h)
            j_seq.append(jl)
            bucket = it.get("bucket", "other")
            per_bucket.setdefault(bucket, []).append((h, jl))
            if h != jl:
                disagreements.append(
                    {
                        "slug": it["slug"],
                        "pair_index": it["pair_index"],
                        "human": h,
                        "judge": jl,
                        "bucket": bucket,
                    }
                )
        n = len(h_seq)
        agree = sum(1 for a, b in zip(h_seq, j_seq) if a == b)
        kappa = cohens_kappa(h_seq, j_seq) if n else 0.0
        bucket_stats = {}
        for bk, pairs in per_bucket.items():
            bn = len(pairs)
            ba = sum(1 for h, jl in pairs if h == jl)
            bucket_stats[bk] = {"n": bn, "agree": ba, "rate": ba / bn if bn else 0.0}
        out[j] = {
            "n": n,
            "agree": agree,
            "rate": agree / n if n else 0.0,
            "kappa": kappa,
            "buckets": bucket_stats,
            "disagreements": disagreements,
        }
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--analysis-dir",
        type=Path,
        default=Path("evaluation/phase5-results/corpus-003-analysis"),
    )
    args = parser.parse_args()

    csv_path = args.analysis_dir / "calibration-blank.csv"
    keys_path = args.analysis_dir / "calibration-keys.json"
    if not csv_path.is_file():
        print(f"Missing: {csv_path}")
        return 1
    if not keys_path.is_file():
        print(f"Missing: {keys_path}")
        return 1

    human = load_human_labels(csv_path)
    keys_map = load_keys(keys_path)
    items = list(keys_map.values())

    n_total = len(items)
    n_graded = len(human)
    print(f"Items in keys:  {n_total}")
    print(f"Items graded:   {n_graded}")
    if n_graded == 0:
        print("No human labels found. Fill in human_label column in calibration-blank.csv.")
        return 1

    stats = per_judge_stats(items, human)

    print()
    print("Per-judge agreement vs human")
    print("-" * 60)
    print(f"  {'judge':<18}{'n':>4}{'agree':>10}{'rate':>10}{'kappa':>10}")
    for j in JUDGES:
        s = stats[j]
        print(
            f"  {JUDGE_DISPLAY[j]:<18}{s['n']:>4}{s['agree']:>10}"
            f"{s['rate']:>10.0%}{s['kappa']:>10.3f}"
        )

    print()
    print("Per-bucket breakdown (agreement rate)")
    print("-" * 60)
    buckets = ["unanimous", "llama_vs_frontier", "frontier_vs_frontier", "other"]
    header = "  judge             " + "".join(f"{b[:18]:>20}" for b in buckets)
    print(header)
    for j in JUDGES:
        s = stats[j]
        row = f"  {JUDGE_DISPLAY[j]:<18}"
        for b in buckets:
            bs = s["buckets"].get(b)
            if bs is None:
                row += f"{'-':>20}"
            else:
                row += f"{bs['agree']}/{bs['n']} ({bs['rate']:.0%})".rjust(20)
        print(row)

    print()
    print("Disagreements")
    print("-" * 60)
    for j in JUDGES:
        s = stats[j]
        if not s["disagreements"]:
            print(f"  {JUDGE_DISPLAY[j]}: none")
            continue
        print(f"  {JUDGE_DISPLAY[j]}:")
        for d in s["disagreements"]:
            print(
                f"    [{d['bucket']:<22}] {d['slug']} pair {d['pair_index']}  "
                f"human={d['human']:<16} judge={d['judge']}"
            )

    out_json = args.analysis_dir / "calibration-results.json"
    out_json.write_text(
        json.dumps(
            {
                "n_total": n_total,
                "n_graded": n_graded,
                "judges": {
                    j: {
                        "n": stats[j]["n"],
                        "agree": stats[j]["agree"],
                        "rate": stats[j]["rate"],
                        "kappa": stats[j]["kappa"],
                        "buckets": stats[j]["buckets"],
                    }
                    for j in JUDGES
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print()
    print(f"Wrote {out_json}")
    print()
    print("Interpretation guide:")
    print("  kappa >= 0.80  : judge calibrated (strong agreement)")
    print("  kappa  0.60-0.80: substantial agreement")
    print("  kappa  0.40-0.60: moderate; treat with caution")
    print("  kappa  < 0.40  : judge unreliable for this task")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
