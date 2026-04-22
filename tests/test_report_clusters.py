"""Tests for Phase 2.1 template-cluster detection in report.py.

These are unit tests against the pure clustering helpers — they construct
synthetic score dicts rather than running the full evaluator, so they run
instantly and exercise edge cases the real pipeline rarely hits.

The detector groups URLs by *per-pillar* score rather than full-tuple
match, because on realistic corpora (Learn, competitive analysis, etc.)
the same six-tuple rarely repeats but individual weak pillar scores
(e.g. ``structured_data=12``) recur across many pages — that recurrence
is the template signal.
"""

from __future__ import annotations

from retrievability.report import (
    _CLUSTER_MIN_MEMBERS,
    _detect_template_clusters,
    _format_template_section,
)


def _mk(url: str, **pillars) -> dict:
    return {
        'url': url,
        'parseability_score': sum(pillars.values()) / len(pillars),
        'failure_mode': 'moderate_issues',
        'component_scores': pillars,
    }


_BASE_PILLARS = dict(
    semantic_html=73.0,
    content_extractability=80.0,
    structured_data=12.0,
    dom_navigability=35.0,
    metadata_completeness=100.0,
    http_compliance=84.0,
)


def test_shared_weak_pillar_clusters_across_pages():
    results = [
        _mk('https://x/a', **{**_BASE_PILLARS, 'content_extractability': 85.0}),
        _mk('https://x/b', **{**_BASE_PILLARS, 'content_extractability': 40.0}),
        _mk('https://x/c', **{**_BASE_PILLARS, 'content_extractability': 60.0}),
    ]
    clusters = _detect_template_clusters(results)
    pillars = {c['pillar'] for c in clusters}
    # Weak shared pillars (below the 70/100 threshold) should cluster:
    # structured_data=12, dom_navigability=35.
    assert 'structured_data' in pillars
    assert 'dom_navigability' in pillars
    # Non-weak shared pillars must not be surfaced as findings:
    # semantic_html=73, http_compliance=84, metadata_completeness=100.
    assert 'semantic_html' not in pillars
    assert 'http_compliance' not in pillars
    assert 'metadata_completeness' not in pillars


def test_shared_good_score_is_not_surfaced_as_a_finding():
    results = [_mk(f'https://x/{i}', **_BASE_PILLARS) for i in range(3)]
    clusters = _detect_template_clusters(results)
    assert not any(c['pillar'] == 'metadata_completeness' for c in clusters)


def test_fewer_than_three_pages_never_cluster():
    results = [_mk('https://x/a', **_BASE_PILLARS), _mk('https://x/b', **_BASE_PILLARS)]
    assert _detect_template_clusters(results) == []


def test_divergent_pillar_values_do_not_cluster_on_that_pillar():
    results = [
        _mk('https://x/a', **{**_BASE_PILLARS, 'structured_data': 15.0}),
        _mk('https://x/b', **{**_BASE_PILLARS, 'structured_data': 30.0}),
        _mk('https://x/c', **{**_BASE_PILLARS, 'structured_data': 45.0}),
    ]
    clusters = _detect_template_clusters(results)
    assert not any(c['pillar'] == 'structured_data' for c in clusters)
    # dom_navigability=35 is shared and below the weak threshold -> still clusters.
    assert any(c['pillar'] == 'dom_navigability' for c in clusters)


def test_near_identical_scores_within_one_point_cluster():
    results = [
        _mk('https://x/a', **{**_BASE_PILLARS, 'structured_data': 12.4}),
        _mk('https://x/b', **{**_BASE_PILLARS, 'structured_data': 11.6}),
        _mk('https://x/c', **{**_BASE_PILLARS, 'structured_data': 12.0}),
    ]
    clusters = _detect_template_clusters(results)
    sd = [c for c in clusters if c['pillar'] == 'structured_data']
    assert sd and sd[0]['shared_score'] == 12 and len(sd[0]['members']) == 3


def test_uplift_reflects_weight_and_gap():
    # structured_data weight = 0.20, gap = 70 - 12 = 58 -> uplift ~ 11.6
    results = [_mk(f'https://x/{i}', **_BASE_PILLARS) for i in range(3)]
    clusters = _detect_template_clusters(results)
    sd = next(c for c in clusters if c['pillar'] == 'structured_data')
    assert 11.0 < sd['estimated_uplift'] < 12.0


def test_missing_pillar_in_one_result_is_excluded_from_that_pillar_bucket():
    base_no_sd = {k: v for k, v in _BASE_PILLARS.items() if k != 'structured_data'}
    results = [
        _mk('https://x/a', **_BASE_PILLARS),
        _mk('https://x/b', **_BASE_PILLARS),
        _mk('https://x/partial', **base_no_sd),
    ]
    clusters = _detect_template_clusters(results)
    # Only 2 pages have structured_data -> below min=3, no cluster on that pillar.
    assert not any(c['pillar'] == 'structured_data' for c in clusters)
    # But dom_navigability, semantic_html, http_compliance are on all three.
    assert any(c['pillar'] == 'dom_navigability' for c in clusters)


def test_format_template_section_renders_expected_markdown():
    results = [_mk(f'https://x/{i}', **_BASE_PILLARS) for i in range(_CLUSTER_MIN_MEMBERS)]
    clusters = _detect_template_clusters(results)
    lines = _format_template_section(clusters)
    rendered = "\n".join(lines)
    assert "## Template Findings" in rendered
    assert "https://x/0" in rendered
    assert "Est. Uplift" in rendered
    assert "structured_data" in rendered


def test_format_template_section_empty_when_no_clusters():
    assert _format_template_section([]) == []
