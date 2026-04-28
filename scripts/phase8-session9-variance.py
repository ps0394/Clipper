"""Variance check: is corpus-003 r-collapse a range-restriction artifact?

Compares the spread of accuracy and v2 composite scores on corpus-002 vs
corpus-003 (per judge). If corpus-003 has noticeably tighter spread on
either axis, that's the simplest explanation for the r-collapse.
"""
from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import importlib.util
spec = importlib.util.spec_from_file_location(
    "v2mod", str(ROOT / "scripts" / "v2-regression-corpus002.py")
)
assert spec and spec.loader
v2mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v2mod)
recompute_v2 = v2mod.recompute_v2

JUDGE_FILES = {
    "primary": "grades.primary.judged.rendered.json",
    "gpt4o": "grades.gpt4o.judged.rendered.json",
    "deepseek": "grades.deepseek.judged.rendered.json",
}


def stats(xs):
    if not xs:
        return None
    n = len(xs)
    m = sum(xs) / n
    s = math.sqrt(sum((x - m) ** 2 for x in xs) / n)
    xs_s = sorted(xs)
    return {
        "n": n,
        "mean": m,
        "std": s,
        "min": xs_s[0],
        "max": xs_s[-1],
        "iqr": xs_s[3 * n // 4] - xs_s[n // 4],
    }


def show(name, accs, comps, ces):
    a = stats(accs)
    c = stats(comps)
    e = stats(ces)
    print(f"\n=== {name} (n={a['n']}) ===")
    print(f"  accuracy_rendered : mean={a['mean']:.3f}  std={a['std']:.3f}  min={a['min']:.2f}  max={a['max']:.2f}  iqr={a['iqr']:.2f}")
    print(f"  v2_composite      : mean={c['mean']:.2f}  std={c['std']:.2f}  min={c['min']:.2f}  max={c['max']:.2f}  iqr={c['iqr']:.2f}")
    print(f"  content_extract   : mean={e['mean']:.2f}  std={e['std']:.2f}  min={e['min']:.2f}  max={e['max']:.2f}  iqr={e['iqr']:.2f}")


def corpus_002():
    accs, comps, ces = [], [], []
    csv_path = Path("evaluation/phase5-results/corpus-002-analysis/per-page.csv")
    with csv_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not row.get("accuracy_rendered"):
                continue
            slug = row["slug"]
            sp = Path("evaluation/phase5-results/corpus-002") / slug / "clipper-scores.rendered.json"
            if not sp.is_file():
                continue
            sj = json.loads(sp.read_text(encoding="utf-8"))
            v2 = recompute_v2(sj)
            accs.append(float(row["accuracy_rendered"]))
            comps.append(v2["headline_v2"])
            ces.append(sj["component_scores"]["content_extractability"])
    show("corpus-002 (Llama judge, per-page.csv)", accs, comps, ces)


def corpus_003_per_judge():
    pilot = Path("evaluation/phase5-results/corpus-003")
    for jid, fname in JUDGE_FILES.items():
        accs, comps, ces = [], [], []
        for d in sorted(pilot.iterdir()):
            if not d.is_dir():
                continue
            sp = d / "clipper-scores.rendered.json"
            gp = d / fname
            if not sp.is_file() or not gp.is_file():
                continue
            grades = json.loads(gp.read_text(encoding="utf-8"))
            run0 = [g for g in grades if g.get("run_index", 0) == 0]
            if not run0:
                continue
            acc = sum(1 for g in run0 if g.get("label") == "correct") / len(run0)
            sj = json.loads(sp.read_text(encoding="utf-8"))
            v2 = recompute_v2(sj)
            accs.append(acc)
            comps.append(v2["headline_v2"])
            ces.append(sj["component_scores"]["content_extractability"])
        show(f"corpus-003 ({jid})", accs, comps, ces)


if __name__ == "__main__":
    corpus_002()
    corpus_003_per_judge()
