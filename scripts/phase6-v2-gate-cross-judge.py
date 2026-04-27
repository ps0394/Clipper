"""F3.5 — Does the v2 ship gate (+0.35 Pearson r) survive judge replacement?

The v2 release was tagged `v2-evidence-partial` after corpus-002 produced
r = +0.6181 between the v2 composite and accuracy_rendered (single judge,
Llama-3.3-70B). F3.5 asks: if we re-grade with GPT-4o or DeepSeek-V3.2,
does that correlation stay above the +0.35 ship gate?

If yes -> v2 ship status is judge-robust; F3.5 closes as a caveat amendment.
If no  -> the ship gate is judge-dependent; v2 status needs reconsideration.

Reads per-judge grades from `evaluation/phase5-results/corpus-002/<slug>/
grades.<judge>.judged.rendered.json` and v2 composite from the existing
`v2-regression.json` artifact.

Usage:
    python scripts/phase6-v2-gate-cross-judge.py \
        --corpus evaluation/phase5-results/corpus-002 \
        --regression evaluation/phase5-results/corpus-002-analysis/v2-regression.json \
        --out evaluation/phase5-results/corpus-002-analysis/v2-gate-cross-judge.json
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path


GATE = 0.35
GRADES_RE = re.compile(r"^grades\.(?P<judge>[^.]+)\.judged\.rendered\.json$")


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


def per_page_accuracy(grades_path: Path) -> float | None:
    data = json.loads(grades_path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("answers") or data.get("graded") or []
    correct = 0
    total = 0
    for a in data:
        if not isinstance(a, dict):
            continue
        verdict = a.get("label") or a.get("verdict")
        if verdict is None:
            continue
        v = str(verdict).strip().lower()
        total += 1
        if v in ("correct", "true", "yes", "pass", "1"):
            correct += 1
    if total == 0:
        return None
    return correct / total


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--corpus", required=True, type=Path)
    p.add_argument("--regression", required=True, type=Path,
                   help="v2-regression.json from F2.6")
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--gate", type=float, default=GATE)
    args = p.parse_args()

    reg = json.loads(args.regression.read_text(encoding="utf-8"))
    v2_by_slug = {row["slug"]: row["v2_headline"] for row in reg["per_page"]}

    # Discover judges
    judges: dict[str, dict[str, Path]] = {}
    for page_dir in sorted(args.corpus.iterdir()):
        if not page_dir.is_dir():
            continue
        for fp in page_dir.iterdir():
            m = GRADES_RE.match(fp.name)
            if m:
                judges.setdefault(m.group("judge"), {})[page_dir.name] = fp

    if not judges:
        raise SystemExit("No grades.<judge>.judged.rendered.json files found")

    print(f"Judges: {sorted(judges)}")
    print(f"v2 composite source: {args.regression}")
    print(f"Gate threshold: r >= {args.gate}")
    print()

    result = {
        "gate_threshold": args.gate,
        "n_pages_v2": len(v2_by_slug),
        "per_judge": {},
        "all_judges_pass_gate": True,
    }

    for judge in sorted(judges):
        xs = []  # v2 composite
        ys = []  # accuracy under this judge
        n_missing_v2 = 0
        for slug, grades_path in judges[judge].items():
            v2 = v2_by_slug.get(slug)
            if v2 is None:
                n_missing_v2 += 1
                continue
            acc = per_page_accuracy(grades_path)
            if acc is None:
                continue
            xs.append(v2)
            ys.append(acc)
        r = pearson_r(xs, ys)
        passes = (not math.isnan(r)) and r >= args.gate
        result["per_judge"][judge] = {
            "n": len(xs),
            "n_missing_v2": n_missing_v2,
            "pearson_r": round(r, 4) if not math.isnan(r) else None,
            "mean_accuracy": round(sum(ys) / len(ys), 4) if ys else None,
            "gate_passes": passes,
        }
        if not passes:
            result["all_judges_pass_gate"] = False

        print(f"  {judge:12s}  n={len(xs):2d}  r={r:+.4f}  "
              f"acc={sum(ys)/len(ys):.4f}  "
              f"{'PASS' if passes else 'FAIL'} (gate {args.gate})")

    print()
    if result["all_judges_pass_gate"]:
        print("RESULT: v2 ship gate is JUDGE-ROBUST. r remains above "
              f"{args.gate} under every judge. F3.5 closes as caveat-amendment.")
    else:
        print("RESULT: v2 ship gate is JUDGE-DEPENDENT. At least one judge "
              "drives r below the ship gate. F3.5 trigger fires; v2 status "
              "should be reconsidered.")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nWrote {args.out}")
    return 0 if result["all_judges_pass_gate"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
