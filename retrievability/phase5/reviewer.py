"""CLI accept/edit/reject review loop for Phase 5 Q/A pairs.

SCAFFOLDING — the interactive loop is defined here but not yet wired
into the pilot runner. The reviewer sees each generated Q/A pair and
chooses accept / edit / reject with a free-text note.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Callable, Optional

from .schemas import QAPair, ReviewRecord


# Signature of an input provider; the default is `input`, tests pass a fake.
InputFn = Callable[[str], str]


def review_pair(
    pair: QAPair,
    pair_index: int,
    reviewer_id: str,
    *,
    input_fn: InputFn = input,
) -> ReviewRecord:
    """Run one interactive review of one Q/A pair.

    Control characters:
        a / [enter]  — accept verbatim
        e            — edit (prompts for Q and A replacements)
        r            — reject (prompts for reason)
    """
    print(f"\n--- Pair {pair_index} ---")
    print(f"Q: {pair.question}")
    print(f"A: {pair.answer}")
    if pair.supporting_sentences:
        print("Supporting sentences:")
        for s in pair.supporting_sentences:
            print(f"  - {s}")
    choice = (input_fn("[a]ccept / [e]dit / [r]eject > ") or "a").strip().lower()
    if choice in ("", "a", "accept"):
        return ReviewRecord(
            pair_index=pair_index,
            decision="accept",
            generated_pair=pair,
            edited_pair=pair,
            reject_reason=None,
            reviewer_id=reviewer_id,
        )
    if choice in ("e", "edit"):
        new_q = input_fn("new question (blank to keep) > ").strip() or pair.question
        new_a = input_fn("new answer (blank to keep) > ").strip() or pair.answer
        edited = QAPair(question=new_q, answer=new_a, supporting_sentences=pair.supporting_sentences)
        return ReviewRecord(
            pair_index=pair_index,
            decision="edit",
            generated_pair=pair,
            edited_pair=edited,
            reject_reason=None,
            reviewer_id=reviewer_id,
        )
    reason = input_fn("reject reason > ").strip() or "no reason given"
    return ReviewRecord(
        pair_index=pair_index,
        decision="reject",
        generated_pair=pair,
        edited_pair=None,
        reject_reason=reason,
    reviewer_id=reviewer_id,
    )


def review_all(
    pairs: List[QAPair],
    reviewer_id: str,
    *,
    input_fn: InputFn = input,
) -> List[ReviewRecord]:
    """Review each pair in order. Rejected pairs are not replaced here —
    the caller regenerates as needed."""
    return [
        review_pair(p, i, reviewer_id, input_fn=input_fn)
        for i, p in enumerate(pairs)
    ]


def persist_review(records: List[ReviewRecord], out_path: Path) -> None:
    """Write the review audit trail to disk."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    data = [r.to_dict() for r in records]
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def approved_pairs(records: List[ReviewRecord]) -> List[QAPair]:
    """Extract the final ground-truth pairs from a review trail."""
    out: List[QAPair] = []
    for r in records:
        if r.decision == "reject" or r.edited_pair is None:
            continue
        out.append(r.edited_pair)
    return out
