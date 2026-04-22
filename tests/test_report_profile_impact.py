"""Tests for the Profile Impact section in report.py.

The Profile Impact table surfaces the difference between a page's
headline ``parseability_score`` (weighted under its detected content-type
profile) and its ``universal_score`` (weighted under the default article
profile). This makes the classifier's contribution to the headline
number visible so a profile shift cannot silently dominate the score.
"""

from __future__ import annotations

from retrievability.report import (
    _format_profile_impact_section,
    _profile_of,
)


def _mk(url: str, profile: str, parseability: float, universal: float) -> dict:
    return {
        'url': url,
        'parseability_score': parseability,
        'universal_score': universal,
        'failure_mode': 'moderate_issues',
        'component_scores': {},
        'audit_trail': {'_content_type': {'profile': profile}},
    }


def test_profile_of_reads_audit_trail():
    r = _mk('https://x', 'landing', 50.0, 55.0)
    assert _profile_of(r) == 'landing'


def test_profile_of_defaults_to_article_when_missing():
    assert _profile_of({}) == 'article'
    assert _profile_of({'audit_trail': {}}) == 'article'


def test_section_empty_when_all_default_profile():
    # Only article-profile pages — classifier made no non-default call, so
    # the section is noise and should be suppressed.
    results = [
        _mk('https://a', 'article', 60.0, 60.0),
        _mk('https://b', 'article', 55.0, 55.0),
    ]
    assert _format_profile_impact_section(results) == []


def test_section_rendered_when_any_non_default_profile():
    results = [
        _mk('https://a', 'article', 60.0, 60.0),
        _mk('https://b', 'tutorial', 65.0, 58.0),
    ]
    lines = _format_profile_impact_section(results)
    assert lines, "expected a Profile Impact section"
    assert any('## Profile Impact' in line for line in lines)
    # Both rows present; the tutorial row has the non-zero delta.
    body = "\n".join(lines)
    assert 'https://a' in body
    assert 'https://b' in body
    assert '`tutorial`' in body
    assert '+7.0' in body


def test_section_sorts_by_absolute_delta_desc():
    results = [
        _mk('https://small', 'landing', 50.0, 49.0),         # delta +1.0
        _mk('https://big', 'tutorial', 70.0, 55.0),          # delta +15.0
        _mk('https://medium', 'faq', 40.0, 50.0),            # delta -10.0
    ]
    lines = _format_profile_impact_section(results)
    body = "\n".join(lines)
    # big (|15|) should appear before medium (|10|) which should appear
    # before small (|1|).
    big_idx = body.index('https://big')
    medium_idx = body.index('https://medium')
    small_idx = body.index('https://small')
    assert big_idx < medium_idx < small_idx


def test_section_empty_when_universal_score_missing():
    results = [
        {
            'url': 'https://x',
            'parseability_score': 60.0,
            # no universal_score
            'failure_mode': 'moderate_issues',
            'component_scores': {},
            'audit_trail': {'_content_type': {'profile': 'landing'}},
        },
    ]
    assert _format_profile_impact_section(results) == []
