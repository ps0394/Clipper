"""Scoring LLM runner for Phase 5.

SCAFFOLDING — defines the interface and prompt builder. The pilot
runner will instantiate a concrete client (Azure OpenAI, local Llama)
and drive this module.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Protocol

from .schemas import QAPair, ScoringAnswer
from .templates import load_template, render


class ScoringClient(Protocol):
    """Interface for the scoring LLM (GPT-4o primary, Llama secondary)."""

    model_id: str

    def answer(self, prompt: str) -> tuple[str, int, int]:
        """Return (answer_text, tokens_in, tokens_out)."""
        ...


def build_scoring_prompt(*, document_text: str, question: str) -> str:
    template = load_template("scorer")
    return render(template, {"DOCUMENT_TEXT": document_text, "QUESTION": question})


def score_page(
    *,
    client: ScoringClient,
    document_text: str,
    ground_truth: List[QAPair],
    runs_per_question: int,
) -> List[ScoringAnswer]:
    """Run the scoring LLM against each ground-truth question.

    For each question, repeat `runs_per_question` times for variance.
    In the pilot `runs_per_question=1`; the full run uses 3.
    """
    out: List[ScoringAnswer] = []
    for i, pair in enumerate(ground_truth):
        prompt = build_scoring_prompt(document_text=document_text, question=pair.question)
        for run in range(runs_per_question):
            text, tin, tout = client.answer(prompt)
            out.append(
                ScoringAnswer(
                    pair_index=i,
                    answer=text.strip(),
                    run_index=run,
                    tokens_in=tin,
                    tokens_out=tout,
                )
            )
    return out


def persist_scores(answers: List[ScoringAnswer], out_path: Path) -> None:
    """Write scoring-LLM output for one page to disk."""
    import json
    out_path.parent.mkdir(parents=True, exist_ok=True)
    data = [a.to_dict() for a in answers]
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
