"""Tests for Phase 5 scaffolding (schemas, templates, and pure-Python analyzer)."""
from __future__ import annotations

import json

import pytest

from retrievability.phase5 import analyzer, grader, generator, reviewer
from retrievability.phase5.schemas import (
    QAPair,
    ReviewRecord,
    CorpusPage,
    ScoringAnswer,
    Grade,
    RunManifest,
)
from retrievability.phase5.templates import load_template, render


# --- schemas ---------------------------------------------------------------


def test_qapair_roundtrip():
    p = QAPair(
        question="What port does the service listen on?",
        answer="8080",
        supporting_sentences=["The service listens on port 8080."],
    )
    assert QAPair.from_dict(p.to_dict()) == p


def test_review_record_roundtrip_accept():
    pair = QAPair(question="q", answer="a", supporting_sentences=[])
    r = ReviewRecord(
        pair_index=0,
        decision="accept",
        generated_pair=pair,
        edited_pair=pair,
        reject_reason=None,
        reviewer_id="ps",
    )
    assert ReviewRecord.from_dict(r.to_dict()) == r


def test_review_record_roundtrip_reject():
    pair = QAPair(question="q", answer="a", supporting_sentences=[])
    r = ReviewRecord(
        pair_index=2,
        decision="reject",
        generated_pair=pair,
        edited_pair=None,
        reject_reason="requires outside knowledge",
        reviewer_id="ps",
    )
    assert ReviewRecord.from_dict(r.to_dict()) == r


def test_corpus_page_roundtrip():
    p = CorpusPage(
        slug="aks-faq",
        url="https://learn.microsoft.com/en-us/azure/aks/faq",
        profile="faq",
        vendor="learn",
        fetched_at="2026-05-01T10:00:00Z",
    )
    assert CorpusPage.from_dict(p.to_dict()) == p


def test_scoring_answer_and_grade_roundtrip():
    a = ScoringAnswer(pair_index=0, answer="8080", run_index=0, tokens_in=123, tokens_out=4)
    assert ScoringAnswer.from_dict(a.to_dict()) == a
    g = Grade(pair_index=0, run_index=0, label="correct", grader_notes=None)
    assert Grade.from_dict(g.to_dict()) == g


def test_run_manifest_roundtrip():
    m = RunManifest(
        run_id="2026-05-01-gpt4o-pilot",
        corpus_ref="phase5-corpus/_pilot",
        scoring_model="gpt-4o-2024-08-06",
        scoring_model_provider="azure_openai",
        generator_model="claude-3-5-sonnet-20241022",
        temperature=0.0,
        seed=42,
        runs_per_question=1,
        started_at="2026-05-01T10:00:00Z",
    )
    assert RunManifest.from_dict(m.to_dict()) == m


# --- templates -------------------------------------------------------------


def test_load_generator_template_has_tokens():
    t = load_template("generator")
    for tok in ("{{TITLE}}", "{{URL}}", "{{PROFILE}}", "{{DOCUMENT_TEXT}}"):
        assert tok in t, f"generator template missing {tok}"


def test_load_scorer_template_has_tokens():
    t = load_template("scorer")
    for tok in ("{{DOCUMENT_TEXT}}", "{{QUESTION}}"):
        assert tok in t, f"scorer template missing {tok}"


def test_render_substitutes_tokens():
    out = render("hello {{NAME}}, your age is {{AGE}}", {"NAME": "ada", "AGE": "36"})
    assert out == "hello ada, your age is 36"


def test_render_missing_token_raises():
    with pytest.raises(KeyError):
        render("hello {{NAME}}", {"NOT_NAME": "x"})


def test_load_template_missing_raises():
    with pytest.raises(FileNotFoundError):
        load_template("nonexistent_template_xyz")


# --- generator -------------------------------------------------------------


def test_parse_generator_output_valid():
    raw = json.dumps(
        [
            {"question": "q1", "answer": "a1", "supporting_sentences": ["s1"]},
            {"question": "q2", "answer": "a2", "supporting_sentences": []},
        ]
    )
    pairs = generator.parse_generator_output(raw)
    assert len(pairs) == 2
    assert pairs[0].question == "q1"


def test_parse_generator_output_not_array_raises():
    with pytest.raises(ValueError):
        generator.parse_generator_output(json.dumps({"question": "q"}))


def test_parse_generator_output_strips_code_fence():
    # Mistral Large 3 wraps JSON in a ```json fence despite the prompt.
    payload = json.dumps(
        [{"question": "q", "answer": "a", "supporting_sentences": []}]
    )
    raw = f"```json\n{payload}\n```"
    pairs = generator.parse_generator_output(raw)
    assert len(pairs) == 1 and pairs[0].answer == "a"


def test_build_generator_prompt_substitutes():
    p = generator.build_generator_prompt(
        title="T", url="https://example.com", profile="reference", document_text="DOC"
    )
    assert "T" in p and "https://example.com" in p and "DOC" in p
    assert "{{" not in p  # no unsubstituted tokens


# --- reviewer --------------------------------------------------------------


def test_review_accept_default(tmp_path):
    pair = QAPair(question="q", answer="a", supporting_sentences=[])
    inputs = iter([""])  # empty = accept
    r = reviewer.review_pair(pair, 0, "tester", input_fn=lambda _p: next(inputs))
    assert r.decision == "accept"
    assert r.edited_pair == pair


def test_review_reject_with_reason():
    pair = QAPair(question="q", answer="a", supporting_sentences=[])
    inputs = iter(["r", "requires outside knowledge"])
    r = reviewer.review_pair(pair, 3, "tester", input_fn=lambda _p: next(inputs))
    assert r.decision == "reject"
    assert r.reject_reason == "requires outside knowledge"
    assert r.edited_pair is None


def test_review_edit():
    pair = QAPair(question="q?", answer="wrong", supporting_sentences=["s"])
    inputs = iter(["e", "Q?", "right"])
    r = reviewer.review_pair(pair, 1, "tester", input_fn=lambda _p: next(inputs))
    assert r.decision == "edit"
    assert r.edited_pair is not None
    assert r.edited_pair.question == "Q?"
    assert r.edited_pair.answer == "right"
    assert r.edited_pair.supporting_sentences == ["s"]


def test_approved_pairs_excludes_rejects():
    pair = QAPair(question="q", answer="a", supporting_sentences=[])
    records = [
        ReviewRecord(0, "accept", pair, pair, None, "t"),
        ReviewRecord(1, "reject", pair, None, "bad", "t"),
        ReviewRecord(2, "edit", pair, QAPair("q2", "a2", []), None, "t"),
    ]
    kept = reviewer.approved_pairs(records)
    assert [p.question for p in kept] == ["q", "q2"]


# --- grader ----------------------------------------------------------------


def test_grade_exact_match_correct():
    gt = QAPair(question="q", answer="8080", supporting_sentences=[])
    scored = ScoringAnswer(pair_index=0, answer="8080", run_index=0, tokens_in=0, tokens_out=0)
    g = grader.grade_answer(ground_truth=gt, scored=scored)
    assert g.label == "correct"


def test_grade_substring_correct():
    gt = QAPair(question="q", answer="8080", supporting_sentences=[])
    scored = ScoringAnswer(pair_index=0, answer="The port is 8080.", run_index=0, tokens_in=0, tokens_out=0)
    g = grader.grade_answer(ground_truth=gt, scored=scored)
    assert g.label == "correct"
    assert g.grader_notes == "substring match"


def test_grade_not_in_document():
    gt = QAPair(question="q", answer="8080", supporting_sentences=[])
    scored = ScoringAnswer(pair_index=0, answer="not in document", run_index=0, tokens_in=0, tokens_out=0)
    g = grader.grade_answer(ground_truth=gt, scored=scored)
    assert g.label == "not_in_document"


def test_grade_incorrect():
    gt = QAPair(question="q", answer="8080", supporting_sentences=[])
    scored = ScoringAnswer(pair_index=0, answer="443", run_index=0, tokens_in=0, tokens_out=0)
    g = grader.grade_answer(ground_truth=gt, scored=scored)
    assert g.label == "incorrect"


def test_page_accuracy():
    gs = [
        Grade(0, 0, "correct", None),
        Grade(1, 0, "incorrect", None),
        Grade(2, 0, "correct", None),
        Grade(3, 0, "not_in_document", None),
    ]
    assert grader.page_accuracy(gs) == 0.5


# --- analyzer --------------------------------------------------------------


def test_spearman_perfect_positive():
    assert analyzer.spearman_rho([1.0, 2.0, 3.0, 4.0], [10.0, 20.0, 30.0, 40.0]) == pytest.approx(1.0)


def test_spearman_perfect_negative():
    assert analyzer.spearman_rho([1.0, 2.0, 3.0, 4.0], [40.0, 30.0, 20.0, 10.0]) == pytest.approx(-1.0)


def test_spearman_handles_ties():
    # ties in x only
    rho = analyzer.spearman_rho([1.0, 1.0, 2.0, 3.0], [10.0, 20.0, 30.0, 40.0])
    assert 0.7 <= rho <= 1.0


def test_bootstrap_ci_brackets_rho():
    x = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
    y = [1.1, 2.0, 2.9, 4.2, 5.1, 6.0, 6.9, 8.1]
    lo, hi = analyzer.bootstrap_ci(x, y, resamples=500, seed=1)
    rho = analyzer.spearman_rho(x, y)
    assert lo <= rho <= hi


def test_correlate_shapes_output():
    pillars = {
        "semantic_html": [50.0, 60.0, 70.0, 80.0, 90.0],
        "structured_data": [10.0, 20.0, 30.0, 40.0, 50.0],
    }
    acc = [0.2, 0.4, 0.6, 0.8, 1.0]
    results = analyzer.correlate(pillars, acc, resamples=200)
    assert {c.pillar for c in results} == {"semantic_html", "structured_data"}
    for c in results:
        assert c.n == 5
        assert -1.0 <= c.rho <= 1.0
        assert c.ci_low <= c.rho <= c.ci_high
