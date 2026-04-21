"""Tests for failure-mode transparency and environment metadata (Phase 0.2 / 0.3).

These tests exercise the orchestrator-level behavior introduced in Phase 0.2:
when a pillar raises PillarEvaluationError, the final score must be
renormalized over the surviving pillars (not zeroed), the failed pillar must
be listed in ``failed_pillars``, and ``partial_evaluation`` must be True.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from retrievability.access_gate_evaluator import (
    AccessGateEvaluator,
    PillarEvaluationError,
)
from retrievability.parse import _parse_html_file


FIXTURE = Path(__file__).parent / "fixtures" / "semantic_html_good.html"


def _baseline():
    """Run a full offline evaluation — every pillar succeeds."""
    evaluator = AccessGateEvaluator()
    parse_result = _parse_html_file(FIXTURE)
    return evaluator.evaluate_access_gate(parse_result.to_dict(), url=None, crawl_data=None)


def test_full_run_is_not_partial():
    result = _baseline()
    assert result.partial_evaluation is False
    assert result.failed_pillars == []
    assert set(result.component_scores.keys()) == {
        'semantic_html', 'content_extractability', 'structured_data',
        'dom_navigability', 'metadata_completeness', 'http_compliance',
    }


def test_pillar_failure_is_excluded_not_zeroed(monkeypatch):
    """A failing pillar must be dropped from the weighted average entirely."""
    baseline = _baseline()

    def _broken(self, *args, **kwargs):
        raise PillarEvaluationError('semantic_html', 'simulated failure')

    monkeypatch.setattr(AccessGateEvaluator, '_evaluate_semantic_html', _broken)

    evaluator = AccessGateEvaluator()
    parse_result = _parse_html_file(FIXTURE)
    result = evaluator.evaluate_access_gate(parse_result.to_dict(), url=None, crawl_data=None)

    assert result.partial_evaluation is True
    assert result.failed_pillars == ['semantic_html']
    assert 'semantic_html' not in result.component_scores
    assert result.failure_mode == 'partial_evaluation'

    # Key property: surviving pillars should score the same numeric value as
    # in the baseline run. Renormalization does not distort them.
    for pillar, value in result.component_scores.items():
        assert value == pytest.approx(baseline.component_scores[pillar])

    # The renormalized final score must be a weighted average over the
    # surviving pillars and strictly greater than the pre-Phase-0.2 behavior
    # of multiplying the semantic-html zero into the sum. Exact formula:
    surviving_weights = {
        'content_extractability': 0.20,
        'structured_data': 0.20,
        'dom_navigability': 0.15,
        'metadata_completeness': 0.10,
        'http_compliance': 0.10,
    }
    denom = sum(surviving_weights.values())
    expected = sum(
        result.component_scores[p] * w for p, w in surviving_weights.items()
    ) / denom
    assert result.parseability_score == pytest.approx(expected)


def test_all_pillars_failing_produces_evaluation_error(monkeypatch):
    """If every pillar raises, the run is an evaluation_error with score 0."""
    pillars = [
        '_evaluate_semantic_html',
        '_evaluate_content_extractability',
        '_evaluate_structured_data',
        '_evaluate_wcag_accessibility',
        '_evaluate_metadata_completeness',
        '_evaluate_http_compliance_enhanced',
    ]

    def _always_fail(name):
        def _inner(self, *args, **kwargs):
            raise PillarEvaluationError(name, 'simulated')
        return _inner

    for method_name in pillars:
        monkeypatch.setattr(AccessGateEvaluator, method_name, _always_fail(method_name))

    evaluator = AccessGateEvaluator()
    parse_result = _parse_html_file(FIXTURE)
    result = evaluator.evaluate_access_gate(parse_result.to_dict(), url=None, crawl_data=None)

    assert result.partial_evaluation is True
    assert len(result.failed_pillars) == 6
    assert result.component_scores == {}
    assert result.parseability_score == 0.0
    assert result.failure_mode == 'evaluation_error'


def test_audit_trail_includes_environment_metadata():
    result = _baseline()
    env = result.audit_trail.get('_environment')
    assert isinstance(env, dict)
    # Required keys for reproducibility
    for key in ('clipper_version', 'python_version', 'platform'):
        assert key in env and env[key]
    # Library versions should at least be recorded (value may be "unknown"
    # on odd installs, but the key must be present).
    for pkg in ('beautifulsoup4', 'extruct', 'httpx',
                'axe-selenium-python', 'selenium'):
        assert pkg in env


def test_failed_pillar_audit_records_reason(monkeypatch):
    def _broken(self, *args, **kwargs):
        raise PillarEvaluationError('structured_data', 'schema parse boom')

    monkeypatch.setattr(AccessGateEvaluator, '_evaluate_structured_data', _broken)

    evaluator = AccessGateEvaluator()
    parse_result = _parse_html_file(FIXTURE)
    result = evaluator.evaluate_access_gate(parse_result.to_dict(), url=None, crawl_data=None)

    pillar_audit = result.audit_trail.get('structured_data')
    assert pillar_audit is not None
    assert pillar_audit.get('status') == 'could_not_evaluate'
    assert 'schema parse boom' in pillar_audit.get('reason', '')
