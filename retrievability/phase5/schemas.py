"""Dataclasses for Phase 5 corpus and results.

Wire format is JSON. Every dataclass has `to_dict` / `from_dict` helpers
that are total and do not depend on third-party serializers. Keep this
module free of runtime dependencies so the schemas can be imported from
the CLI, the pilot runner, and tests without pulling in LLM clients.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any, Literal


ReviewDecision = Literal["accept", "edit", "reject"]


@dataclass(frozen=True)
class QAPair:
    """A single question/answer pair with supporting evidence."""
    question: str
    answer: str
    supporting_sentences: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "QAPair":
        return cls(
            question=_coerce_str(d["question"]),
            answer=_coerce_str(d["answer"]),
            supporting_sentences=[
                _coerce_str(s) for s in d.get("supporting_sentences", [])
            ],
        )


def _coerce_str(v: Any) -> str:
    """Normalize a generator output field to a plain string.

    Mistral Large 3 sometimes emits list-shaped answers (e.g. a
    multi-step answer rendered as ``["step 1", "step 2", ...]``) instead
    of the prose the prompt asks for. Downstream grader / judge code
    assumes strings, so coerce here. Lists are joined with "; " so
    substring-grader fallback still has a chance.
    """
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    if isinstance(v, list):
        return "; ".join(_coerce_str(item) for item in v)
    if isinstance(v, dict):
        # Unlikely but possible — flatten values.
        return "; ".join(_coerce_str(x) for x in v.values())
    return str(v)


@dataclass(frozen=True)
class ReviewRecord:
    """One reviewer decision for one generated Q/A pair.

    `edited_pair` is set when decision == 'edit' or 'accept' (a verbatim
    accept stores a copy of the generated pair). `reject_reason` is set
    when decision == 'reject'.
    """
    pair_index: int
    decision: ReviewDecision
    generated_pair: QAPair
    edited_pair: Optional[QAPair]
    reject_reason: Optional[str]
    reviewer_id: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pair_index": self.pair_index,
            "decision": self.decision,
            "generated_pair": self.generated_pair.to_dict(),
            "edited_pair": self.edited_pair.to_dict() if self.edited_pair else None,
            "reject_reason": self.reject_reason,
            "reviewer_id": self.reviewer_id,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ReviewRecord":
        return cls(
            pair_index=d["pair_index"],
            decision=d["decision"],
            generated_pair=QAPair.from_dict(d["generated_pair"]),
            edited_pair=QAPair.from_dict(d["edited_pair"]) if d.get("edited_pair") else None,
            reject_reason=d.get("reject_reason"),
            reviewer_id=d["reviewer_id"],
        )


@dataclass(frozen=True)
class CorpusPage:
    """Metadata for one page in the Phase 5 corpus."""
    slug: str
    url: str
    profile: str        # landing / reference / sample / faq / tutorial / article
    vendor: str         # learn / aws / gcp / wikipedia / mdn / stripe / other
    fetched_at: str     # ISO 8601

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CorpusPage":
        return cls(
            slug=d["slug"],
            url=d["url"],
            profile=d["profile"],
            vendor=d["vendor"],
            fetched_at=d["fetched_at"],
        )


@dataclass(frozen=True)
class ScoringAnswer:
    """One scoring-LLM answer to one Q/A pair on one run."""
    pair_index: int
    answer: str
    run_index: int       # 0, 1, 2 for the 3-run variance check
    tokens_in: int
    tokens_out: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ScoringAnswer":
        return cls(**d)


GradeLabel = Literal["correct", "incorrect", "not_in_document"]


@dataclass(frozen=True)
class Grade:
    """Grader verdict for one scoring answer vs. ground truth."""
    pair_index: int
    run_index: int
    label: GradeLabel
    grader_notes: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Grade":
        return cls(
            pair_index=d["pair_index"],
            run_index=d["run_index"],
            label=d["label"],
            grader_notes=d.get("grader_notes"),
        )


@dataclass(frozen=True)
class RunManifest:
    """Top-level config for one scoring run.

    Committed at evaluation/phase5-results/<run-id>/manifest.json.
    """
    run_id: str
    corpus_ref: str           # relative path to the corpus root used (e.g. "phase5-corpus/_pilot")
    scoring_model: str        # e.g. "gpt-4o-2024-08-06"
    scoring_model_provider: str  # "azure_openai" | "local_llama" | ...
    generator_model: str      # e.g. "claude-3.5-sonnet"
    temperature: float
    seed: Optional[int]
    runs_per_question: int    # 3 in full, typically 1 in pilot
    started_at: str           # ISO 8601

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "RunManifest":
        return cls(**d)
