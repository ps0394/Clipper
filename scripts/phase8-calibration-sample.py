"""Sample Q/A pairs from corpus-003 for human-judge calibration.

Stratified sampling across three buckets so we can answer:
  (a) do all judges agree on easy cases?
  (b) when Llama disagrees with the two frontier judges, which side is right?
  (c) when the two frontier judges disagree, which side is right?

Outputs three artifacts under evaluation/phase5-results/corpus-003-analysis/:
  - calibration-sheet.md     : human-readable grading sheet, judge labels hidden
  - calibration-blank.csv    : fill-in CSV (slug, pair_index, human_label)
  - calibration-keys.json    : judge labels by (slug, pair_index), for the
                                comparison script. Keep this hidden until
                                you've graded the CSV.

Usage:
    python scripts/phase8-calibration-sample.py [--seed 20260428] [--n-unanimous 5]
        [--n-llama-vs-frontier 10] [--n-frontier-vs-frontier 5]
        [--pilot-dir evaluation/phase5-results/corpus-003]
"""
from __future__ import annotations

import argparse
import csv
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

JUDGES = ["primary", "gpt4o", "deepseek"]
JUDGE_DISPLAY = {"primary": "Llama-3.3", "gpt4o": "GPT-4o", "deepseek": "DeepSeek-V3.2"}

GRADE_FILES = {
    "primary": "grades.primary.judged.rendered.json",
    "gpt4o": "grades.gpt4o.judged.rendered.json",
    "deepseek": "grades.deepseek.judged.rendered.json",
}


@dataclass(frozen=True)
class PairRecord:
    slug: str
    pair_index: int
    question: str
    ground_truth: str
    candidate: str
    supporting_sentences: List[str]
    labels: Dict[str, str]  # judge_id -> label
    page_excerpt: str

    @property
    def all_unanimous(self) -> bool:
        vals = set(self.labels.values())
        return len(vals) == 1

    @property
    def llama_vs_frontier(self) -> bool:
        # Llama disagrees with both gpt4o and deepseek, AND gpt4o == deepseek
        if not all(j in self.labels for j in JUDGES):
            return False
        return (
            self.labels["gpt4o"] == self.labels["deepseek"]
            and self.labels["primary"] != self.labels["gpt4o"]
        )

    @property
    def frontier_vs_frontier(self) -> bool:
        if not all(j in self.labels for j in ("gpt4o", "deepseek")):
            return False
        return self.labels["gpt4o"] != self.labels["deepseek"]


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _grade_lookup(judged: List[dict]) -> Dict[int, str]:
    """First run_index per pair_index -> label."""
    out: Dict[int, str] = {}
    for g in judged:
        if g.get("run_index", 0) != 0:
            continue
        out[g["pair_index"]] = g["label"]
    return out


def _page_excerpt(page_dir: Path, supporting: List[str], max_chars: int = 1200) -> str:
    """Return a snippet of the rendered page text, anchored on supporting
    sentences if they appear in the text; otherwise a head excerpt."""
    txt_path = page_dir / "page.rendered.txt"
    if not txt_path.is_file():
        txt_path = page_dir / "page.raw.txt"
    if not txt_path.is_file():
        return "(no extracted text on disk)"
    text = txt_path.read_text(encoding="utf-8", errors="replace")
    if supporting:
        first = supporting[0]
        idx = text.find(first[:80]) if first else -1
        if idx >= 0:
            start = max(0, idx - 200)
            end = min(len(text), idx + max_chars - 200)
            snippet = text[start:end]
            if start > 0:
                snippet = "…" + snippet
            if end < len(text):
                snippet = snippet + "…"
            return snippet
    return text[:max_chars] + ("…" if len(text) > max_chars else "")


def collect_pairs(pilot_dir: Path) -> List[PairRecord]:
    records: List[PairRecord] = []
    for page_dir in sorted(pilot_dir.iterdir()):
        if not page_dir.is_dir():
            continue
        qapairs_path = page_dir / "qapairs.json"
        scoring_path = page_dir / "scoring.primary.rendered.json"
        if not qapairs_path.is_file() or not scoring_path.is_file():
            continue
        try:
            qapairs = _load_json(qapairs_path)
            answers = _load_json(scoring_path)
        except (json.JSONDecodeError, OSError):
            continue
        # judge label maps
        judge_maps: Dict[str, Dict[int, str]] = {}
        for j, fname in GRADE_FILES.items():
            p = page_dir / fname
            if p.is_file():
                try:
                    judge_maps[j] = _grade_lookup(_load_json(p))
                except (json.JSONDecodeError, OSError):
                    continue
        if not all(j in judge_maps for j in JUDGES):
            continue  # need all three for stratification
        # candidate answers indexed
        cand_by_idx: Dict[int, str] = {}
        for a in answers:
            if a.get("run_index", 0) == 0:
                cand_by_idx[a["pair_index"]] = a.get("answer", "")
        for idx, qa in enumerate(qapairs):
            if idx not in cand_by_idx:
                continue
            labels = {j: judge_maps[j].get(idx) for j in JUDGES}
            if any(v is None for v in labels.values()):
                continue
            records.append(
                PairRecord(
                    slug=page_dir.name,
                    pair_index=idx,
                    question=qa.get("question", ""),
                    ground_truth=qa.get("answer", ""),
                    candidate=cand_by_idx[idx],
                    supporting_sentences=qa.get("supporting_sentences", []),
                    labels=labels,  # type: ignore[arg-type]
                    page_excerpt=_page_excerpt(
                        page_dir, qa.get("supporting_sentences", [])
                    ),
                )
            )
    return records


def stratified_sample(
    records: List[PairRecord],
    n_unanimous: int,
    n_llama_vs_frontier: int,
    n_frontier_vs_frontier: int,
    seed: int,
) -> Tuple[List[PairRecord], Dict[str, int]]:
    rng = random.Random(seed)
    unanimous = [r for r in records if r.all_unanimous]
    llama_v_front = [r for r in records if r.llama_vs_frontier]
    front_v_front = [r for r in records if r.frontier_vs_frontier]

    rng.shuffle(unanimous)
    rng.shuffle(llama_v_front)
    rng.shuffle(front_v_front)

    sample = (
        unanimous[:n_unanimous]
        + llama_v_front[:n_llama_vs_frontier]
        + front_v_front[:n_frontier_vs_frontier]
    )
    rng.shuffle(sample)  # randomize presentation order so grader can't infer bucket
    pool_sizes = {
        "unanimous_pool": len(unanimous),
        "llama_vs_frontier_pool": len(llama_v_front),
        "frontier_vs_frontier_pool": len(front_v_front),
        "total_pairs_with_all_three_judges": len(records),
    }
    return sample, pool_sizes


def write_sheet_md(records: List[PairRecord], out_path: Path) -> None:
    lines: List[str] = []
    lines.append("# corpus-003 Calibration Grading Sheet")
    lines.append("")
    lines.append(
        "Grade each candidate answer against the ground truth, "
        "using only the source excerpt as evidence."
    )
    lines.append("")
    lines.append("**Labels (Phase 5 schema):**")
    lines.append(
        "- `correct` — candidate conveys the same fact as ground truth "
        "(paraphrase OK, extra correct detail OK)"
    )
    lines.append(
        "- `incorrect` — candidate states a different fact, contradicts ground truth, "
        "or omits a required element"
    )
    lines.append(
        "- `not_in_document` — candidate or ground-truth fact is not "
        "supported by the source excerpt"
    )
    lines.append("")
    lines.append(
        "Fill in `human_label` in the companion CSV "
        "(`calibration-blank.csv`). Do not open `calibration-keys.json` "
        "until you've finished grading."
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    for i, r in enumerate(records, 1):
        lines.append(f"## Item {i}  —  `{r.slug}` / pair {r.pair_index}")
        lines.append("")
        lines.append(f"**Question:** {r.question}")
        lines.append("")
        lines.append(f"**Ground-truth answer:** {r.ground_truth}")
        lines.append("")
        lines.append(f"**Candidate answer:** {r.candidate}")
        lines.append("")
        if r.supporting_sentences:
            lines.append("**Supporting sentence(s) cited by Q/A generator:**")
            for s in r.supporting_sentences:
                lines.append(f"> {s}")
            lines.append("")
        lines.append("**Source-page excerpt:**")
        lines.append("")
        lines.append("```")
        lines.append(r.page_excerpt.strip())
        lines.append("```")
        lines.append("")
        lines.append("**Your label:** `_____` (correct / incorrect / not_in_document)")
        lines.append("")
        lines.append("---")
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def write_blank_csv(records: List[PairRecord], out_path: Path) -> None:
    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["item", "slug", "pair_index", "question", "human_label"])
        for i, r in enumerate(records, 1):
            w.writerow([i, r.slug, r.pair_index, r.question, ""])


def write_keys_json(
    records: List[PairRecord], pool_sizes: Dict[str, int], out_path: Path, seed: int
) -> None:
    payload = {
        "seed": seed,
        "n_items": len(records),
        "pool_sizes": pool_sizes,
        "items": [
            {
                "item": i,
                "slug": r.slug,
                "pair_index": r.pair_index,
                "labels": r.labels,
                "bucket": (
                    "unanimous"
                    if r.all_unanimous
                    else (
                        "llama_vs_frontier"
                        if r.llama_vs_frontier
                        else (
                            "frontier_vs_frontier"
                            if r.frontier_vs_frontier
                            else "other"
                        )
                    )
                ),
            }
            for i, r in enumerate(records, 1)
        ],
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pilot-dir",
        type=Path,
        default=Path("evaluation/phase5-results/corpus-003"),
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("evaluation/phase5-results/corpus-003-analysis"),
    )
    parser.add_argument("--seed", type=int, default=20260428)
    parser.add_argument("--n-unanimous", type=int, default=5)
    parser.add_argument("--n-llama-vs-frontier", type=int, default=10)
    parser.add_argument("--n-frontier-vs-frontier", type=int, default=5)
    args = parser.parse_args()

    if not args.pilot_dir.is_dir():
        print(f"Pilot dir not found: {args.pilot_dir}")
        return 1
    args.out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Scanning {args.pilot_dir}...")
    records = collect_pairs(args.pilot_dir)
    print(f"  {len(records)} Q/A pairs with all three judge labels")

    sample, pools = stratified_sample(
        records,
        args.n_unanimous,
        args.n_llama_vs_frontier,
        args.n_frontier_vs_frontier,
        args.seed,
    )
    for k, v in pools.items():
        print(f"  pool: {k} = {v}")
    print(f"  sampled: {len(sample)}")

    sheet = args.out_dir / "calibration-sheet.md"
    csv_path = args.out_dir / "calibration-blank.csv"
    keys = args.out_dir / "calibration-keys.json"
    write_sheet_md(sample, sheet)
    write_blank_csv(sample, csv_path)
    write_keys_json(sample, pools, keys, args.seed)

    print()
    print(f"Sheet:    {sheet}")
    print(f"CSV:      {csv_path}")
    print(f"Keys:     {keys}  (DO NOT OPEN until graded)")
    print()
    print("Next: fill in human_label in the CSV, then run")
    print("  python scripts/phase8-calibration-compare.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
