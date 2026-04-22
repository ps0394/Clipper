"""Tests for content-type-aware scoring profiles (Phase 1.1).

Covers the detection precedence (ms.topic > JSON-LD > URL > DOM > default),
the output-contract additions to ``ScoreResult`` (``content_type``,
``universal_score``), the audit-trail ``_content_type`` block, and the
parseability_score-vs-universal_score divergence a profile is supposed to
produce.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from bs4 import BeautifulSoup

from retrievability.access_gate_evaluator import AccessGateEvaluator
from retrievability.parse import _parse_html_file
from retrievability.profiles import (
    PROFILE_ARTICLE,
    PROFILE_FAQ,
    PROFILE_LANDING,
    PROFILE_REFERENCE,
    PROFILE_TUTORIAL,
    PROFILE_WEIGHTS,
    detect_content_type,
)


FIXTURES = Path(__file__).parent / "fixtures"


def _soup(fixture_name: str) -> BeautifulSoup:
    html = (FIXTURES / fixture_name).read_text(encoding='utf-8')
    return BeautifulSoup(html, 'html.parser')


def _score(fixture_name: str, url=None):
    evaluator = AccessGateEvaluator()
    parse_result = _parse_html_file(FIXTURES / fixture_name)
    return evaluator.evaluate_access_gate(parse_result.to_dict(), url=url, crawl_data=None)


# ---------------------------------------------------------------------------
# Pure detection tests (no scoring needed)
# ---------------------------------------------------------------------------


def test_detect_ms_topic_overview_is_landing():
    profile, trace = detect_content_type(_soup("content_type_landing.html"))
    assert profile == PROFILE_LANDING
    assert trace['source'] == 'ms_topic'
    assert trace['matched_value'] == 'overview'


def test_detect_json_ld_faqpage_is_faq():
    profile, trace = detect_content_type(_soup("content_type_faq.html"))
    assert profile == PROFILE_FAQ
    assert trace['source'] == 'schema_type'


def test_detect_ms_topic_quickstart_is_tutorial():
    profile, trace = detect_content_type(_soup("content_type_tutorial.html"))
    assert profile == PROFILE_TUTORIAL
    assert trace['source'] == 'ms_topic'
    assert trace['matched_value'] == 'quickstart'


def test_detect_url_path_reference():
    # No ms.topic, no JSON-LD — URL heuristic should catch /api/.
    profile, trace = detect_content_type(
        _soup("content_type_reference_urlonly.html"),
        url="https://example.com/api/widgets",
    )
    assert profile == PROFILE_REFERENCE
    assert trace['source'] == 'url'


def test_detect_default_is_article():
    profile, trace = detect_content_type(_soup("semantic_html_good.html"))
    assert profile == PROFILE_ARTICLE
    assert trace['source'] == 'default'


def test_ms_topic_beats_jsonld():
    """Detection order: ms.topic > JSON-LD. If both are present, ms.topic wins."""
    html = (
        '<html><head>'
        '<meta name="ms.topic" content="reference">'
        '<script type="application/ld+json">'
        '{"@context":"https://schema.org","@type":"FAQPage"}'
        '</script>'
        '</head><body></body></html>'
    )
    profile, trace = detect_content_type(BeautifulSoup(html, 'html.parser'))
    assert profile == PROFILE_REFERENCE
    assert trace['source'] == 'ms_topic'


# ---------------------------------------------------------------------------
# Integration — ScoreResult carries content_type, universal_score, audit
# ---------------------------------------------------------------------------


def test_scoreresult_has_content_type_and_universal_score():
    result = _score("content_type_landing.html")
    assert result.content_type == PROFILE_LANDING
    # universal_score must always be populated (backward-compat comparator).
    assert result.universal_score is not None
    assert 0.0 <= result.universal_score <= 100.0
    # Audit trail records detection so humans can see why a profile was picked.
    ct_audit = result.audit_trail.get('_content_type')
    assert ct_audit is not None
    assert ct_audit['profile'] == PROFILE_LANDING
    assert ct_audit['detection']['source'] == 'ms_topic'
    assert ct_audit['weights'] == PROFILE_WEIGHTS[PROFILE_LANDING]


def test_article_default_has_parseability_equal_to_universal():
    """A page that falls through to the default profile produces identical
    parseability_score and universal_score — no regression on existing URLs."""
    result = _score("semantic_html_good.html")
    assert result.content_type == PROFILE_ARTICLE
    assert result.parseability_score == pytest.approx(result.universal_score)


def test_faq_profile_diverges_from_article_weights():
    """Under synthetic component scores that are strong on structured_data
    and weak on content_extractability, the FAQ profile must score
    higher than the default article profile because FAQ up-weights
    structured_data and down-weights extractability."""
    evaluator = AccessGateEvaluator()
    scores = {
        'semantic_html':          50.0,
        'content_extractability': 10.0,
        'structured_data':        90.0,
        'dom_navigability':       50.0,
        'metadata_completeness':  50.0,
        'http_compliance':        50.0,
    }
    article_score = evaluator._weighted_score(scores, PROFILE_WEIGHTS[PROFILE_ARTICLE])
    faq_score = evaluator._weighted_score(scores, PROFILE_WEIGHTS[PROFILE_FAQ])
    assert faq_score > article_score + 3, (
        f"FAQ weights should lift this shape meaningfully: "
        f"article={article_score:.2f}, faq={faq_score:.2f}"
    )


def test_landing_profile_rewards_structure_over_prose():
    """Landing pages weight structured_data over content_extractability, so
    a page with strong structure and weak prose must score higher under the
    landing profile than under article."""
    evaluator = AccessGateEvaluator()
    scores = {
        'semantic_html':          60.0,
        'content_extractability': 10.0,
        'structured_data':        85.0,
        'dom_navigability':       70.0,
        'metadata_completeness':  70.0,
        'http_compliance':        70.0,
    }
    article_score = evaluator._weighted_score(scores, PROFILE_WEIGHTS[PROFILE_ARTICLE])
    landing_score = evaluator._weighted_score(scores, PROFILE_WEIGHTS[PROFILE_LANDING])
    assert landing_score > article_score + 3, (
        f"Landing profile should lift this shape: "
        f"article={article_score:.2f}, landing={landing_score:.2f}"
    )


def test_url_heuristic_works_when_html_has_no_hints():
    result = _score("content_type_reference_urlonly.html", url="https://example.com/api/widgets")
    assert result.content_type == PROFILE_REFERENCE
    assert result.audit_trail['_content_type']['detection']['source'] == 'url'


# ---------------------------------------------------------------------------
# Profile-table invariant
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("profile_name,weights", list(PROFILE_WEIGHTS.items()))
def test_every_profile_weights_sum_to_one(profile_name, weights):
    assert abs(sum(weights.values()) - 1.0) < 1e-6
    expected_pillars = {
        'semantic_html', 'content_extractability', 'structured_data',
        'dom_navigability', 'metadata_completeness', 'http_compliance',
    }
    assert set(weights.keys()) == expected_pillars
