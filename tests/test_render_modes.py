"""Phase 3.1 rendering-mode tests.

Two layers:

1. Offline evaluator tests — assert that `render_mode` round-trips through
   ``ScoreResult`` and that raw mode produces a result with dom_navigability
   scored by static fallback (no browser call).
2. Report-layer unit tests — the delta detector must pair raw/rendered by
   URL, compute the signed delta, and flag pages whose |delta| meets the
   15-point threshold.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from retrievability.access_gate_evaluator import AccessGateEvaluator
from retrievability.parse import _parse_html_file
from retrievability.report import (
    _RENDER_DELTA_FLAG_THRESHOLD,
    _detect_render_deltas,
    _format_render_delta_section,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Evaluator wiring
# ---------------------------------------------------------------------------


def _score(fixture: str, render_mode: str):
    parse_result = _parse_html_file(FIXTURES_DIR / fixture)
    evaluator = AccessGateEvaluator()
    return evaluator.evaluate_access_gate(
        parse_result.to_dict(), url=None, crawl_data=None, render_mode=render_mode
    )


def test_render_mode_defaults_to_rendered_and_is_tagged_on_result():
    parse_result = _parse_html_file(FIXTURES_DIR / "semantic_html_good.html")
    evaluator = AccessGateEvaluator()
    result = evaluator.evaluate_access_gate(
        parse_result.to_dict(), url=None, crawl_data=None
    )
    assert result.render_mode == 'rendered'


def test_raw_mode_tags_result_and_scores_dom_navigability_without_axe():
    result = _score("semantic_html_good.html", 'raw')
    assert result.render_mode == 'raw'
    # dom_navigability was scored through static analysis — the audit entry
    # must reflect that path, NOT a live browser/axe evaluation.
    dom_audit = result.audit_trail.get('dom_navigability', {})
    method = (dom_audit.get('method') or '').lower()
    assert 'static' in method or 'fallback' in method, (
        f"raw mode should use static fallback for dom_navigability; got method={method!r}"
    )


def test_rendered_and_raw_modes_produce_comparable_but_distinct_results():
    """Both paths complete successfully and tag render_mode correctly.

    Offline (url=None) both modes route dom_navigability through the same
    static fallback, so absolute scores will match — the distinguishing
    assertion is on the tag, not on a pillar-score diff.
    """
    raw = _score("semantic_html_good.html", 'raw')
    rendered = _score("semantic_html_good.html", 'rendered')
    assert raw.render_mode == 'raw'
    assert rendered.render_mode == 'rendered'
    # Both must produce a numeric score.
    assert 0.0 <= raw.parseability_score <= 100.0
    assert 0.0 <= rendered.parseability_score <= 100.0


def test_invalid_render_mode_raises():
    parse_result = _parse_html_file(FIXTURES_DIR / "semantic_html_good.html")
    evaluator = AccessGateEvaluator()
    with pytest.raises(ValueError):
        evaluator.evaluate_access_gate(
            parse_result.to_dict(), url=None, crawl_data=None, render_mode='neither'
        )


# ---------------------------------------------------------------------------
# Report-layer delta detection
# ---------------------------------------------------------------------------


def _result(url: str, mode: str, score: float) -> dict:
    return {
        'url': url,
        'render_mode': mode,
        'parseability_score': score,
        'failure_mode': 'moderate_issues',
        'component_scores': {},
    }


def test_render_delta_pairs_by_url_and_signs_the_delta():
    results = [
        _result('https://x/a', 'raw', 40.0),
        _result('https://x/a', 'rendered', 72.0),
    ]
    deltas = _detect_render_deltas(results)
    assert len(deltas) == 1
    d = deltas[0]
    assert d['raw_score'] == 40.0
    assert d['rendered_score'] == 72.0
    assert d['delta'] == pytest.approx(32.0)
    assert d['flagged'] is True


def test_render_delta_flag_uses_absolute_value():
    # Rare but possible: rendered lower than raw (e.g. JS injects chrome).
    results = [
        _result('https://x/a', 'raw', 80.0),
        _result('https://x/a', 'rendered', 60.0),
    ]
    deltas = _detect_render_deltas(results)
    assert deltas[0]['delta'] == pytest.approx(-20.0)
    assert deltas[0]['flagged'] is True


def test_render_delta_below_threshold_is_not_flagged():
    results = [
        _result('https://x/a', 'raw', 70.0),
        _result('https://x/a', 'rendered', 78.0),
    ]
    deltas = _detect_render_deltas(results)
    assert deltas[0]['delta'] == pytest.approx(8.0)
    assert deltas[0]['flagged'] is False
    assert abs(deltas[0]['delta']) < _RENDER_DELTA_FLAG_THRESHOLD


def test_render_delta_ignores_unpaired_urls():
    results = [
        _result('https://x/single', 'rendered', 80.0),
        _result('https://x/a', 'raw', 40.0),
        _result('https://x/a', 'rendered', 80.0),
    ]
    deltas = _detect_render_deltas(results)
    assert [d['url'] for d in deltas] == ['https://x/a']


def test_render_delta_section_renders_table_and_flag():
    deltas = _detect_render_deltas([
        _result('https://x/a', 'raw', 40.0),
        _result('https://x/a', 'rendered', 72.0),
        _result('https://x/b', 'raw', 70.0),
        _result('https://x/b', 'rendered', 75.0),
    ])
    lines = _format_render_delta_section(deltas)
    rendered = "\n".join(lines)
    assert "## Rendering-Mode Deltas" in rendered
    assert "https://x/a" in rendered and "+32.0" in rendered and "[FLAG]" in rendered
    assert "https://x/b" in rendered and "+5.0" in rendered


def test_render_delta_section_empty_when_no_pairs():
    assert _format_render_delta_section([]) == []
