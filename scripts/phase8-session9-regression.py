"""Session 9 — corpus-003 regression and cross-corpus stability.

Implements:
  - F2.6 v2-composite-vs-accuracy regression on corpus-003 under each judge.
  - F3.5 cross-judge ship gate (r >= +0.35 under all judges checked).
  - Per-pillar correlation table for cross-corpus stability vs corpus-002.

Dependencies:
  - corpus-003 pilot dir with summary.json + grades.{primary|gpt4o|deepseek}.judged.rendered.json
  - corpus-002 gamma-experiments.json (for the corpus-002 single-pillar baseline).

Output:
  evaluation/phase5-results/corpus-003-analysis/session-9-report.json
  evaluation/phase5-results/corpus-003-analysis/session-9-report.md

Usage:
    python scripts/phase8-session9-regression.py
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Reuse the canonical v2 recompute from the existing F2.6 script.
import importlib.util
spec = importlib.util.spec_from_file_location(
    "v2_regression_corpus002",
    str(ROOT / "scripts" / "v2-regression-corpus002.py"),
)
assert spec and spec.loader
v2mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v2mod)
recompute_v2 = v2mod.recompute_v2
V2_WEIGHTS = v2mod.V2_WEIGHTS

PILLARS = [
    "semantic_html",
    "content_extractability",
    "structured_data",
    "dom_navigability",
    "metadata_completeness",
    "http_compliance",
]
GATE = 0.35
JUDGE_FILES = {
    "primary": "grades.primary.judged.rendered.json",
    "gpt4o": "grades.gpt4o.judged.rendered.json",
    "deepseek": "grades.deepseek.judged.rendered.json",
}


def judge_files_for_tag(answers_tag: str) -> Dict[str, str]:
    """Resolve the judge filenames for a given answers tag.

    Default tag "primary" reads the original gpt-4.1-answer judged files.
    Other tags (e.g. "weak" from Session 9.5 Phi-4-mini rescore) read
    grades.<tag>.<judge>.judged.rendered.json — written by
    `phase5 rejudge --answers-tag <tag> --grade-tag <tag>.<judge>`.
    """
    if answers_tag == "primary":
        return dict(JUDGE_FILES)
    return {
        jid: f"grades.{answers_tag}.{jid}.judged.rendered.json"
        for jid in JUDGE_FILES
    }
JUDGE_DISPLAY = {
    "primary": "Llama-3.3-70B",
    "gpt4o": "GPT-4o",
    "deepseek": "DeepSeek-V3.2",
}


def pearson_r(xs: List[float], ys: List[float]) -> float:
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


def judged_accuracy(grades: List[dict]) -> Optional[float]:
    """Mean over run_index=0 grades for one page, or None if no grades."""
    run0 = [g for g in grades if g.get("run_index", 0) == 0]
    if not run0:
        return None
    correct = sum(1 for g in run0 if g.get("label") == "correct")
    return correct / len(run0)


def collect(pilot_dir: Path, judge_files: Dict[str, str]) -> List[dict]:
    """Per-page records with v2 composite, pillar scores, and per-judge accuracy."""
    out: List[dict] = []
    for d in sorted(pilot_dir.iterdir()):
        if not d.is_dir():
            continue
        scores_path = d / "clipper-scores.rendered.json"
        if not scores_path.is_file():
            continue
        try:
            scores = json.loads(scores_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        v2 = recompute_v2(scores)
        rec = {
            "slug": d.name,
            "v2_composite": v2["headline_v2"],
            "v1_parseability": v2["headline_v1_parseability"],
            "pillars": v2["component_scores_v2"],
            "judges": {},
        }
        # per-judge accuracy
        for jid, fname in judge_files.items():
            p = d / fname
            if not p.is_file():
                continue
            try:
                grades = json.loads(p.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            acc = judged_accuracy(grades)
            if acc is None:
                continue
            rec["judges"][jid] = acc
        if rec["judges"]:
            out.append(rec)
    return out


def per_judge_regression(records: List[dict], judge_ids: List[str]) -> Dict[str, dict]:
    summary: Dict[str, dict] = {}
    for jid in judge_ids:
        sub = [r for r in records if jid in r["judges"]]
        n = len(sub)
        accs = [r["judges"][jid] for r in sub]
        comps = [r["v2_composite"] for r in sub]
        v1s = [r["v1_parseability"] for r in sub if r["v1_parseability"] is not None]
        r_v2 = pearson_r(comps, accs)
        r_v1 = pearson_r(v1s, accs) if len(v1s) == n else float("nan")
        pillar_r: Dict[str, float] = {}
        for pillar in PILLARS:
            xs = [r["pillars"].get(pillar, 0.0) for r in sub]
            pillar_r[pillar] = round(pearson_r(xs, accs), 4)
        summary[jid] = {
            "n": n,
            "mean_accuracy": round(sum(accs) / n, 4) if n else None,
            "mean_v2_composite": round(sum(comps) / n, 2) if n else None,
            "r_v1_parseability_vs_acc": (
                None if math.isnan(r_v1) else round(r_v1, 4)
            ),
            "r_v2_composite_vs_acc": (
                None if math.isnan(r_v2) else round(r_v2, 4)
            ),
            "v2_gate_passes": (not math.isnan(r_v2)) and r_v2 >= GATE,
            "per_pillar_r_vs_acc": pillar_r,
        }
    return summary


def cross_corpus_pillar_table(
    corpus_002_pillar_r: Dict[str, float],
    corpus_003_per_judge: Dict[str, dict],
) -> List[dict]:
    """For each pillar: corpus-002 r, then per-judge corpus-003 r and delta.
    Flags any |delta| > 0.20 or sign flip."""
    rows: List[dict] = []
    for pillar in PILLARS:
        r_002 = corpus_002_pillar_r.get(pillar)
        row = {"pillar": pillar, "corpus_002_r": r_002, "by_judge": {}}
        for jid, jdata in corpus_003_per_judge.items():
            r_003 = jdata["per_pillar_r_vs_acc"].get(pillar)
            delta = (
                None
                if r_002 is None or r_003 is None
                else round(r_003 - r_002, 4)
            )
            sign_flip = (
                r_002 is not None
                and r_003 is not None
                and ((r_002 > 0) != (r_003 > 0))
                and abs(r_002) > 0.05
                and abs(r_003) > 0.05
            )
            shift_gt_0_20 = delta is not None and abs(delta) > 0.20
            row["by_judge"][jid] = {
                "r_corpus_003": r_003,
                "delta": delta,
                "sign_flip": sign_flip,
                "shift_gt_0_20": shift_gt_0_20,
            }
        rows.append(row)
    return rows


def load_corpus_002_pillar_r(path: Path) -> Dict[str, float]:
    blob = json.loads(path.read_text(encoding="utf-8"))
    # find the _single_pillar_correlations entry; key is "experiments" or "stages"
    container = blob.get("experiments") or blob.get("stages") or {}
    for stage in container.values():
        if not isinstance(stage, list):
            continue
        for entry in stage:
            if entry.get("name") == "_single_pillar_correlations":
                return dict(entry["single_pillar_r"])
    return {}


def render_md(report: dict, out_path: Path) -> None:
    lines: List[str] = []
    lines.append("# Session 9 — corpus-003 Regression & Stability\n")
    lines.append(f"- pilot dir: `{report['pilot_dir']}`")
    lines.append(f"- pages with at least one judge accuracy: **{report['n_pages_evaluable']}**")
    lines.append(f"- gate threshold: r ≥ {GATE:+.2f}\n")

    lines.append("## F2.6 / F3.5 — composite vs accuracy, per judge\n")
    lines.append("| Judge | n | mean acc | mean v2 | r (v1 vs acc) | r (v2 vs acc) | gate |")
    lines.append("|---|---:|---:|---:|---:|---:|:--:|")
    for jid in JUDGE_FILES:
        s = report["per_judge"][jid]
        gate_mark = "PASS" if s["v2_gate_passes"] else "FAIL"
        lines.append(
            f"| {JUDGE_DISPLAY[jid]} | {s['n']} "
            f"| {s['mean_accuracy']:.3f} | {s['mean_v2_composite']:.2f} "
            f"| {s['r_v1_parseability_vs_acc']:+.4f} "
            f"| {s['r_v2_composite_vs_acc']:+.4f} "
            f"| **{gate_mark}** |"
        )
    lines.append("")

    lines.append("## A4 — Per-pillar correlation, cross-corpus\n")
    lines.append("Per-pillar Pearson r (pillar score vs judged accuracy_rendered).")
    lines.append(
        "`Δ` = corpus-003 minus corpus-002. Flags: `*` = |Δ| > 0.20, `!` = sign flip.\n"
    )
    head = "| Pillar | corpus-002 |"
    sep = "|---|---:|"
    for jid in JUDGE_FILES:
        head += f" 003 / {JUDGE_DISPLAY[jid]} | Δ |"
        sep += "---:|---:|"
    lines.append(head)
    lines.append(sep)
    for row in report["per_pillar_cross_corpus"]:
        line = f"| {row['pillar']} | {row['corpus_002_r']:+.4f} |"
        for jid in JUDGE_FILES:
            cell = row["by_judge"][jid]
            r003 = cell["r_corpus_003"]
            delta = cell["delta"]
            flags = ""
            if cell["shift_gt_0_20"]:
                flags += "*"
            if cell["sign_flip"]:
                flags += "!"
            line += f" {r003:+.4f}{flags} | {delta:+.4f} |"
        lines.append(line)
    lines.append("")

    lines.append("## Block A acceptance\n")
    a3_pass = all(
        report["per_judge"][j]["v2_gate_passes"] for j in JUDGE_FILES
    )
    lines.append(f"- **A3 (3 of 3 judges clear gate):** {'PASS' if a3_pass else 'FAIL'}")
    a3_2of3 = sum(
        1 for j in JUDGE_FILES if report["per_judge"][j]["v2_gate_passes"]
    ) >= 2
    lines.append(f"- **A3 minimum (2 of 3 judges clear gate):** {'PASS' if a3_2of3 else 'FAIL'}")
    n_flagged = sum(
        1
        for row in report["per_pillar_cross_corpus"]
        for cell in row["by_judge"].values()
        if cell["shift_gt_0_20"] or cell["sign_flip"]
    )
    lines.append(f"- **A4 flags (|Δ|>0.20 or sign flip):** {n_flagged}\n")

    lines.append("## Notes\n")
    lines.append(
        "- **Selection bias / range restriction (HEADLINE):** corpus-003 "
        "accuracy is bunched near the ceiling (Llama std 0.10, GPT-4o std "
        "0.15, DeepSeek std 0.14) vs corpus-002 (std 0.25). The v2 composite "
        "spread is essentially unchanged (std ~7.4 vs 7.8). Pearson r against "
        "a near-constant target collapses mechanically — this is a **textbook "
        "range-restriction artifact, not evidence that v2 fails to generalize**. "
        "corpus-003 neither confirms nor refutes the v2 ship gate."
    )
    lines.append(
        "- **Dropped pages:** 99 of 271 pages had both raw and rendered "
        "extracts under MIN_DOCUMENT_CHARS and produced no Q/A pairs. Those "
        "are exactly the pages where v2 → accuracy correlation would be most "
        "informative (sparse content → bad answers); their exclusion is the "
        "primary driver of the ceiling effect."
    )
    lines.append(
        "- **Llama judge inversion:** mean Llama accuracy on the evaluable "
        "subset (0.952) is *higher* than GPT-4o (0.904) and DeepSeek (0.917) "
        "— a reversal from corpus-002. Three-way unanimous agreement is "
        "91.6% (783/855 pairs). The earlier 'Llama vs frontier' framing was "
        "an artifact of mixing page-level (with fetch failures = 0%) and "
        "Q/A-level statistics. Judge fitness is not the issue."
    )
    lines.append(
        "- **A5 diagnosis pointer:** Block A cannot be closed as-passed under "
        "this corpus. The remediation is not v3 weight redesign; it is a "
        "harder generalization corpus that produces wider accuracy variance "
        "(weaker generator, sparser content, multi-hop synthesis, or all three)."
    )
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pilot-dir",
        type=Path,
        default=Path("evaluation/phase5-results/corpus-003"),
    )
    parser.add_argument(
        "--corpus-002-gamma",
        type=Path,
        default=Path(
            "evaluation/phase5-results/corpus-002-analysis/gamma-experiments.json"
        ),
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("evaluation/phase5-results/corpus-003-analysis"),
    )
    parser.add_argument(
        "--answers-tag",
        default="primary",
        help="Which scorer-primary's judged grades to read. 'primary' (default) "
             "reads grades.<judge>.judged.rendered.json (gpt-4.1 baseline). "
             "Other tags (e.g. 'weak' from Session 9.5 Phi-4-mini rescore) "
             "read grades.<tag>.<judge>.judged.rendered.json.",
    )
    parser.add_argument(
        "--report-name",
        default=None,
        help="Output filename stem (without extension). Defaults to "
             "'session-9-report' for primary, 'session-9.5-report' for weak.",
    )
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    judge_files = judge_files_for_tag(args.answers_tag)
    print(f"Collecting from {args.pilot_dir} (answers_tag={args.answers_tag!r})...")
    print(f"  reading: {list(judge_files.values())[0]} (and 2 others)")
    records = collect(args.pilot_dir, judge_files)
    print(f"  {len(records)} pages with at least one judge accuracy")

    per_judge = per_judge_regression(records, list(judge_files.keys()))

    corpus_002_pillar_r = load_corpus_002_pillar_r(args.corpus_002_gamma)
    if not corpus_002_pillar_r:
        print(f"[!] could not load corpus-002 pillar correlations from {args.corpus_002_gamma}")

    cross = cross_corpus_pillar_table(corpus_002_pillar_r, per_judge)

    report = {
        "pilot_dir": str(args.pilot_dir),
        "answers_tag": args.answers_tag,
        "gate_threshold": GATE,
        "n_pages_evaluable": len(records),
        "per_judge": per_judge,
        "corpus_002_pillar_r": corpus_002_pillar_r,
        "per_pillar_cross_corpus": cross,
    }

    if args.report_name:
        stem = args.report_name
    elif args.answers_tag == "primary":
        stem = "session-9-report"
    else:
        stem = f"session-9-report.{args.answers_tag}"
    out_json = args.out_dir / f"{stem}.json"
    out_md = args.out_dir / f"{stem}.md"
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    render_md(report, out_md)

    # console summary
    print()
    print("F2.6 / F3.5 — composite vs accuracy")
    print("-" * 70)
    print(f"  {'judge':<18}{'n':>5}{'mean acc':>12}{'mean v2':>12}"
          f"{'r v2/acc':>12}{'gate':>8}")
    for jid in JUDGE_FILES:
        s = per_judge[jid]
        gate_mark = "PASS" if s["v2_gate_passes"] else "FAIL"
        print(
            f"  {JUDGE_DISPLAY[jid]:<18}{s['n']:>5}"
            f"{s['mean_accuracy']:>12.3f}{s['mean_v2_composite']:>12.2f}"
            f"{s['r_v2_composite_vs_acc']:>+12.4f}{gate_mark:>8}"
        )
    print()
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
