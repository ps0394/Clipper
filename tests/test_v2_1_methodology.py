"""Tests for v2.1 methodology disclosure and --diagnostic-mode behavior.

v2.1 is an honest re-labeling release. It adds:
  1. A ``methodology`` block on every ScoreResult dict, always-on, stating
     the calibration corpus and the corpus-003 generalization status.
  2. A ``--diagnostic-mode`` CLI flag that nulls the composite headline
     scores (``parseability_score`` / ``universal_score``) in the JSON
     output. Pillar-level ``component_scores`` are unchanged.
  3. A ``diagnostic_mode`` boolean field on each result for downstream
     filtering.
  4. A banner in the markdown report when diagnostic mode is detected.

See findings/v2.1-release-scope.md.
"""

from __future__ import annotations

import json

from retrievability.schemas import (
    V2_1_METHODOLOGY_DISCLOSURE,
    apply_methodology_disclosure,
)
from retrievability.report import _generate_markdown_report


def _result(parseability: float = 70.0, universal: float = 65.0) -> dict:
    return {
        'parseability_score': parseability,
        'universal_score': universal,
        'failure_mode': 'clean',
        'html_path': '/tmp/x.html',
        'url': 'https://example.com',
        'component_scores': {
            'semantic_html': 80.0,
            'content_extractability': 75.0,
            'structured_data': 50.0,
            'dom_navigability': 60.0,
            'metadata_completeness': 70.0,
            'http_compliance': 90.0,
        },
        'audit_trail': {},
        'standards_authority': {},
        'evaluation_methodology': 'standards-based',
        'render_mode': 'rendered',
    }


# ---------------------------------------------------------------------------
# apply_methodology_disclosure
# ---------------------------------------------------------------------------

def test_methodology_block_added_in_default_mode():
    results = [_result()]
    out = apply_methodology_disclosure(results, diagnostic_mode=False)
    assert out[0]['methodology'] == V2_1_METHODOLOGY_DISCLOSURE
    assert out[0]['diagnostic_mode'] is False
    # Composites are preserved
    assert out[0]['parseability_score'] == 70.0
    assert out[0]['universal_score'] == 65.0


def test_diagnostic_mode_nulls_composites():
    results = [_result()]
    out = apply_methodology_disclosure(results, diagnostic_mode=True)
    assert out[0]['parseability_score'] is None
    assert out[0]['universal_score'] is None
    assert out[0]['diagnostic_mode'] is True
    # Pillars survive — that's the whole point
    assert out[0]['component_scores']['semantic_html'] == 80.0
    assert out[0]['component_scores']['http_compliance'] == 90.0


def test_methodology_disclosure_round_trips_through_json():
    results = apply_methodology_disclosure([_result()], diagnostic_mode=True)
    serialized = json.dumps(results)
    reloaded = json.loads(serialized)
    assert reloaded[0]['methodology']['scoring_version'] == 'v2-evidence-partial'
    assert reloaded[0]['methodology']['calibration_corpus'] == 'corpus-002'
    assert 'corpus-003' in reloaded[0]['methodology']['generalization_status']
    assert reloaded[0]['parseability_score'] is None


def test_methodology_block_is_per_result_independent_dict():
    """Mutating one result's methodology must not affect another's."""
    results = apply_methodology_disclosure([_result(), _result()], diagnostic_mode=False)
    results[0]['methodology']['scoring_version'] = 'mutated'
    assert results[1]['methodology']['scoring_version'] == 'v2-evidence-partial'


# ---------------------------------------------------------------------------
# Report banner
# ---------------------------------------------------------------------------

def test_report_emits_diagnostic_banner_when_mode_set():
    results = apply_methodology_disclosure([_result()], diagnostic_mode=True)
    md = _generate_markdown_report(results)
    assert 'Diagnostic mode is ON' in md
    assert 'Methodology disclosure' in md


def test_report_emits_methodology_banner_in_default_mode():
    results = apply_methodology_disclosure([_result()], diagnostic_mode=False)
    md = _generate_markdown_report(results)
    assert 'Methodology disclosure' in md
    assert 'Diagnostic mode is ON' not in md


def test_report_handles_null_parseability_in_diagnostic_mode():
    """Average / sort logic must not crash when parseability_score is None."""
    results = apply_methodology_disclosure(
        [_result(parseability=70.0), _result(parseability=50.0)],
        diagnostic_mode=True,
    )
    md = _generate_markdown_report(results)
    # No exception; report still renders. Average is 0.0 in diagnostic mode
    # because composites are nulled — that's acceptable for v2.1.
    assert '# Retrievability Evaluation Report' in md
