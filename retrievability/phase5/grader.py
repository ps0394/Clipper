"""Binary grading of scoring-LLM answers against ground truth.

Grading is deliberately simple: the scoring LLM's answer is compared
to the ground-truth answer with a tolerant substring / normalized
equality check. Borderline cases are flagged for reviewer spot-check
(per design doc §5, 20 percent of grades are spot-checked).

SCAFFOLDING — the automatic grader is a first-pass heuristic. The
pilot will calibrate it against hand-graded answers before the full
run relies on it.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import List

from .schemas import QAPair, ScoringAnswer, Grade


_NOT_IN_DOC = "not in document"


def _normalize(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[\"'`]", "", s)
    return s


def grade_answer(
    *,
    ground_truth: QAPair,
    scored: ScoringAnswer,
) -> Grade:
    """Grade one scoring-LLM answer against its ground-truth pair.

    Heuristic (pilot-grade, to be calibrated):
    - Exact match on normalized strings → correct.
    - Ground-truth answer appears as a substring of the scored answer
      after normalization → correct.
    - Scored answer equals "not in document" (normalized) while ground
      truth is non-empty → not_in_document (a miss; the scoring LLM
      couldn't find content that's supposedly in the document).
    - Otherwise → incorrect.
    """
    gt = _normalize(ground_truth.answer)
    got = _normalize(scored.answer)
    label: str
    notes: str | None = None
    if got == _NOT_IN_DOC and gt:
        label = "not_in_document"
    elif got == gt:
        label = "correct"
    elif gt and gt in got:
        label = "correct"
        notes = "substring match"
    else:
        label = "incorrect"
    return Grade(
        pair_index=scored.pair_index,
        run_index=scored.run_index,
        label=label,  # type: ignore[arg-type]
        grader_notes=notes,
    )


def grade_page(
    *,
    ground_truth: List[QAPair],
    answers: List[ScoringAnswer],
) -> List[Grade]:
    return [
        grade_answer(ground_truth=ground_truth[a.pair_index], scored=a)
        for a in answers
    ]


def persist_grades(grades: List[Grade], out_path: Path) -> None:
    import json
    out_path.parent.mkdir(parents=True, exist_ok=True)
    data = [g.to_dict() for g in grades]
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def page_accuracy(grades: List[Grade]) -> float:
    """Fraction of grades labeled 'correct'. Empty input → 0.0."""
    if not grades:
        return 0.0
    correct = sum(1 for g in grades if g.label == "correct")
    return correct / len(grades)
