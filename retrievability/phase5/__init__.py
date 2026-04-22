"""Phase 5 — LLM ground-truth validation.

See docs/phase-5-design.md for the full design.

Module layout:
    schemas    — dataclasses for Q/A pairs, review records, scoring runs, grades
    prompts    — load prompt templates from disk
    generator  — Claude-based Q/A generation (stub)
    reviewer   — CLI accept/edit/reject review loop (stub)
    scorer     — run scoring LLMs against approved Q/A (stub)
    grader     — binary grading of scorer output vs. ground truth (stub)
    analyzer   — Spearman ρ + bootstrap CI against pillar scores (stub)

All external LLM calls are stubbed. The pilot runner will wire them up
once credentials are in place.
"""
