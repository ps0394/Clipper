"""LLM-as-judge grader for Phase 5.

Replaces the substring heuristic in grader.py for the semantic-equivalence
problem (e.g. ground truth "1099 in USD" vs candidate "1099, usd"). The
judge is a scoring LLM cross-family to the primary scorer — Llama 3.3 70B
grading GPT-4.1's answers — so grader bias is not a within-family effect.

The substring grader in grader.py is kept for cheap CI smoke tests and as
a comparison baseline during calibration.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Protocol, Tuple

from .schemas import GradeLabel, QAPair, ScoringAnswer
from .templates import load_template, render


class JudgeClient(Protocol):
    """Interface for the judge LLM. FoundryScoringClient satisfies this."""

    model_id: str

    def answer(self, prompt: str) -> Tuple[str, int, int]:
        """Return (text, tokens_in, tokens_out)."""
        ...


@dataclass(frozen=True)
class JudgedGrade:
    """Grader verdict from an LLM judge. Superset of schemas.Grade."""

    pair_index: int
    run_index: int
    label: GradeLabel
    rationale: str
    judge_model: str
    tokens_in: int
    tokens_out: int

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "JudgedGrade":
        return cls(**d)


def build_judge_prompt(*, question: str, ground_truth: str, candidate: str) -> str:
    template = load_template("judge")
    return render(
        template,
        {
            "QUESTION": question,
            "GROUND_TRUTH": ground_truth,
            "CANDIDATE": candidate,
        },
    )


def parse_judge_output(raw: str) -> Tuple[GradeLabel, str]:
    """Parse the two-line judge response into (label, rationale).

    Tolerant of leading/trailing whitespace and minor formatting drift
    (label on a line by itself, with or without trailing punctuation).
    Falls back to INCORRECT with an explanatory rationale if the first
    line cannot be mapped to a known label.
    """
    text = raw.strip()
    if not text:
        return "incorrect", "empty judge response"
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return "incorrect", "empty judge response"
    first = lines[0].upper().rstrip(".:,;!?")
    # strip any leading label like "VERDICT:" that a model might add
    if ":" in first:
        first = first.split(":", 1)[1].strip()
    label: GradeLabel
    if first.startswith("CORRECT"):
        label = "correct"
    elif first.startswith("NOT_IN_DOCUMENT") or first == "NOT IN DOCUMENT":
        label = "not_in_document"
    elif first.startswith("INCORRECT"):
        label = "incorrect"
    else:
        return "incorrect", f"unparseable judge verdict: {lines[0]!r}"
    rationale = " ".join(lines[1:]) if len(lines) > 1 else ""
    return label, rationale


def judge_answer(
    *,
    client: JudgeClient,
    pair_index: int,
    run_index: int,
    ground_truth: QAPair,
    candidate: ScoringAnswer,
) -> JudgedGrade:
    prompt = build_judge_prompt(
        question=ground_truth.question,
        ground_truth=ground_truth.answer,
        candidate=candidate.answer,
    )
    raw, tokens_in, tokens_out = client.answer(prompt)
    label, rationale = parse_judge_output(raw)
    return JudgedGrade(
        pair_index=pair_index,
        run_index=run_index,
        label=label,
        rationale=rationale,
        judge_model=client.model_id,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
    )


def judge_page(
    *,
    client: JudgeClient,
    ground_truth: List[QAPair],
    answers: List[ScoringAnswer],
) -> List[JudgedGrade]:
    return [
        judge_answer(
            client=client,
            pair_index=a.pair_index,
            run_index=a.run_index,
            ground_truth=ground_truth[a.pair_index],
            candidate=a,
        )
        for a in answers
    ]


def persist_judged_grades(grades: List[JudgedGrade], out_path: Path) -> None:
    import json
    out_path.parent.mkdir(parents=True, exist_ok=True)
    data = [g.to_dict() for g in grades]
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def judged_page_accuracy(grades: List[JudgedGrade]) -> float:
    if not grades:
        return 0.0
    correct = sum(1 for g in grades if g.label == "correct")
    return correct / len(grades)


def cohens_kappa(labels_a: List[GradeLabel], labels_b: List[GradeLabel]) -> float:
    """Cohen's kappa on two label sequences over the same items.

    Used for the calibration gate: hand-labels vs judge-labels.
    Returns 0.0 if either sequence is empty or if the labels are
    identical but constant (in which case kappa is undefined; we
    report 0 rather than NaN so the gate rejects).
    """
    if len(labels_a) != len(labels_b):
        raise ValueError("label sequences must be equal length")
    n = len(labels_a)
    if n == 0:
        return 0.0
    categories = sorted(set(labels_a) | set(labels_b))
    if len(categories) < 2:
        return 0.0
    agree = sum(1 for a, b in zip(labels_a, labels_b) if a == b)
    p_o = agree / n
    p_e = 0.0
    for c in categories:
        p_a = labels_a.count(c) / n
        p_b = labels_b.count(c) / n
        p_e += p_a * p_b
    if p_e >= 1.0:
        return 0.0
    return (p_o - p_e) / (1 - p_e)
