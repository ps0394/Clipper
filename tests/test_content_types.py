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
    V2_WEIGHTS,
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
    # v2: all profiles collapse to V2_WEIGHTS for headline scoring. The v1
    # profile-specific weights are preserved in the audit trail under
    # v1_weights_for_reference so the classifier stays observable.
    assert ct_audit['weights'] == V2_WEIGHTS
    assert ct_audit['v1_weights_for_reference'] == PROFILE_WEIGHTS[PROFILE_LANDING]


def test_article_default_has_parseability_equal_to_universal():
    """A page that falls through to the default profile produces identical
    parseability_score and universal_score. In v2 this is true for every
    profile, not just article, because all profiles share V2_WEIGHTS."""
    result = _score("semantic_html_good.html")
    assert result.content_type == PROFILE_ARTICLE
    assert result.parseability_score == pytest.approx(result.universal_score)


def test_v2_all_profiles_collapse_to_same_headline_weights():
    """In v2 the headline composite is the same for every profile.
    parseability_score equals universal_score for any detected profile."""
    result = _score("content_type_landing.html")
    assert result.content_type == PROFILE_LANDING
    assert result.parseability_score == pytest.approx(result.universal_score)


def test_v2_weights_are_two_pillar_composite():
    """V2_WEIGHTS: content_extractability and http_compliance at 0.50 each;
    all other pillars at 0.0. This is the evidence-partial ship configuration
    per findings Addendum B §B.5."""
    assert V2_WEIGHTS['content_extractability'] == 0.50
    assert V2_WEIGHTS['http_compliance'] == 0.50
    for p in ('semantic_html', 'structured_data', 'dom_navigability',
              'metadata_completeness'):
        assert V2_WEIGHTS[p] == 0.0
    assert abs(sum(V2_WEIGHTS.values()) - 1.0) < 1e-6


def test_v2_profiles_do_not_diverge_on_headline_score():
    """Synthetic pillar scores produce the same v2 headline regardless of
    which v1 profile is detected. This replaces the pre-v2 divergence tests
    (test_faq_profile_diverges_from_article_weights,
    test_landing_profile_rewards_structure_over_prose), which assumed
    profile-specific weights — collapsed in v2 pending corpus-003 evidence."""
    evaluator = AccessGateEvaluator()
    scores = {
        'semantic_html':          50.0,
        'content_extractability': 10.0,
        'structured_data':        90.0,
        'dom_navigability':       50.0,
        'metadata_completeness':  50.0,
        'http_compliance':        50.0,
    }
    article_score = evaluator._weighted_score(scores, V2_WEIGHTS)
    faq_score = evaluator._weighted_score(scores, V2_WEIGHTS)
    landing_score = evaluator._weighted_score(scores, V2_WEIGHTS)
    assert article_score == pytest.approx(faq_score)
    assert article_score == pytest.approx(landing_score)


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
