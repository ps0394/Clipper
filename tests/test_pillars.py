"""Pillar fixture tests for the Clipper scoring engine.

Each test targets one pillar by pairing a "good" fixture against a "bad"
fixture, then asserting both an absolute range for that pillar's score and
the expected ordering between fixtures. Ranges are deliberately wide —
scoring is continuous, and small heuristic changes should not break tests.
Real regressions (broken pillar, inverted signal, weight error) will still
fail both the range and the ordering assertions.

Non-pillar pillars are not asserted in each pair's test, because offline
scoring populates them identically or near-identically across fixtures and
the signal-to-noise is low. See ``test_full_pipeline_smoke`` for a coarse
overall-score sanity check.
"""

from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Semantic HTML (W3C HTML5 semantic elements)
# ---------------------------------------------------------------------------


def test_semantic_html_good_scores_high(score_fixture):
    result = score_fixture("semantic_html_good.html")
    assert 50.0 <= result.component_scores["semantic_html"] <= 100.0


def test_semantic_html_bad_scores_low(score_fixture):
    result = score_fixture("semantic_html_bad.html")
    assert 0.0 <= result.component_scores["semantic_html"] <= 15.0


def test_semantic_html_ordering(score_fixture):
    good = score_fixture("semantic_html_good.html").component_scores["semantic_html"]
    bad = score_fixture("semantic_html_bad.html").component_scores["semantic_html"]
    assert good > bad + 30, f"semantic HTML score collapse: good={good}, bad={bad}"


# ---------------------------------------------------------------------------
# Structured data (Schema.org)
# ---------------------------------------------------------------------------


def test_structured_data_complete_scores_high(score_fixture):
    result = score_fixture("structured_data_complete.html")
    assert 60.0 <= result.component_scores["structured_data"] <= 100.0


def test_structured_data_missing_scores_zero(score_fixture):
    result = score_fixture("structured_data_missing.html")
    assert 0.0 <= result.component_scores["structured_data"] <= 15.0


def test_structured_data_ordering(score_fixture):
    complete = score_fixture("structured_data_complete.html").component_scores["structured_data"]
    missing = score_fixture("structured_data_missing.html").component_scores["structured_data"]
    assert complete > missing + 40, (
        f"structured-data signal collapse: complete={complete}, missing={missing}"
    )


# ---------------------------------------------------------------------------
# Phase 4.1 — JSON-LD field completeness (per-type)
# ---------------------------------------------------------------------------


def test_faq_incomplete_scores_below_complete(score_fixture):
    """Exit criterion for Phase 4.1: an incomplete FAQPage (empty
    mainEntity) scores below a complete one."""
    complete = score_fixture("structured_data_faq_complete.html").component_scores["structured_data"]
    incomplete = score_fixture("structured_data_faq_incomplete.html").component_scores["structured_data"]
    assert complete > incomplete, (
        f"FAQ completeness signal missing: complete={complete}, incomplete={incomplete}"
    )
    # The difference should be meaningful, not a rounding artifact.
    assert complete - incomplete >= 10, (
        f"FAQ completeness delta too small: complete={complete}, incomplete={incomplete}"
    )


def test_faq_incomplete_logs_missing_mainentity(score_fixture):
    """Incomplete FAQPage must surface mainEntity in the audit trail's
    invalid-fields list so operators can diagnose the gap."""
    result = score_fixture("structured_data_faq_incomplete.html")
    detail = result.audit_trail["structured_data"]["field_completeness_detail"]
    all_missing = [f for m in detail["missing_fields"] for f in m["fields"]]
    all_invalid = [f for m in detail["invalid_fields"] for f in m["fields"]]
    assert "mainEntity" in (all_missing + all_invalid), (
        f"mainEntity not flagged: missing={all_missing}, invalid={all_invalid}"
    )


def test_howto_complete_scores_high(score_fixture):
    result = score_fixture("structured_data_howto_complete.html")
    assert result.component_scores["structured_data"] >= 60.0


def test_howto_validated_item_in_audit(score_fixture):
    result = score_fixture("structured_data_howto_complete.html")
    detail = result.audit_trail["structured_data"]["field_completeness_detail"]
    types = [item["type"] for item in detail["validated_items"]]
    assert "HowTo" in types


def test_article_validated_item_in_audit(score_fixture):
    result = score_fixture("structured_data_complete.html")
    detail = result.audit_trail["structured_data"]["field_completeness_detail"]
    types = [item["type"] for item in detail["validated_items"]]
    assert "Article" in types
    assert "BreadcrumbList" in types


# ---------------------------------------------------------------------------
# Metadata completeness (Dublin Core / OpenGraph / Schema.org)
# ---------------------------------------------------------------------------


def test_metadata_full_scores_high(score_fixture):
    result = score_fixture("metadata_full.html")
    assert 85.0 <= result.component_scores["metadata_completeness"] <= 100.0


def test_metadata_empty_scores_low(score_fixture):
    result = score_fixture("metadata_empty.html")
    assert 0.0 <= result.component_scores["metadata_completeness"] <= 15.0


def test_metadata_ordering(score_fixture):
    full = score_fixture("metadata_full.html").component_scores["metadata_completeness"]
    empty = score_fixture("metadata_empty.html").component_scores["metadata_completeness"]
    assert full > empty + 50, f"metadata signal collapse: full={full}, empty={empty}"


# ---------------------------------------------------------------------------
# Content extractability (Mozilla Readability)
# ---------------------------------------------------------------------------


def test_readability_clean_scores_high(score_fixture):
    result = score_fixture("readability_clean.html")
    assert 70.0 <= result.component_scores["content_extractability"] <= 100.0


def test_readability_chrome_heavy_scores_low(score_fixture):
    result = score_fixture("readability_chrome_heavy.html")
    assert 0.0 <= result.component_scores["content_extractability"] <= 40.0


def test_readability_ordering(score_fixture):
    clean = score_fixture("readability_clean.html").component_scores["content_extractability"]
    chrome = score_fixture("readability_chrome_heavy.html").component_scores["content_extractability"]
    assert clean > chrome + 30, (
        f"readability signal collapse: clean={clean}, chrome-heavy={chrome}"
    )


def test_extraction_preview_is_persisted(score_fixture):
    """Phase 1.2: audit_trail must expose a text preview + char count so
    consumers (and the markdown report) can see *what* was extracted."""
    result = score_fixture("readability_clean.html")
    metrics = (
        result.audit_trail
        .get("content_extractability", {})
        .get("extraction_metrics", {})
    )
    preview = metrics.get("extracted_preview")
    chars = metrics.get("extracted_chars")
    assert isinstance(preview, str) and len(preview) > 0, "preview must be a non-empty string"
    assert len(preview) <= 303, f"preview capped at ~300 chars, got {len(preview)}"
    assert isinstance(chars, int) and chars > 0, f"extracted_chars must be a positive int, got {chars!r}"


# ---------------------------------------------------------------------------
# Agent content hints (hints raise HTTP compliance, not a dedicated pillar)
# ---------------------------------------------------------------------------


def test_agent_hints_markdown_boosts_http_compliance(score_fixture):
    with_hints = score_fixture("agent_hints_markdown.html").component_scores["http_compliance"]
    without = score_fixture("agent_hints_none.html").component_scores["http_compliance"]
    assert with_hints > without + 10, (
        f"agent-hints signal collapse: with_hints={with_hints}, without={without}"
    )


def test_agent_hints_markdown_detected(score_fixture):
    result = score_fixture("agent_hints_markdown.html")
    signals = (
        result.audit_trail.get("http_compliance", {})
        .get("agent_content_hints", {})
        .get("signals_found", {})
    )
    assert signals.get("has_markdown_alternate") is True
    assert signals.get("has_non_html_alternate") is True


# ---------------------------------------------------------------------------
# Robots / crawl permissions
# ---------------------------------------------------------------------------


def test_robots_noindex_lowers_http_compliance(score_fixture):
    blocked = score_fixture("robots_noindex.html").component_scores["http_compliance"]
    permissive = score_fixture("agent_hints_none.html").component_scores["http_compliance"]
    assert blocked < permissive, (
        f"noindex should score below permissive baseline: blocked={blocked}, permissive={permissive}"
    )


def test_robots_noindex_flagged_in_audit(score_fixture):
    result = score_fixture("robots_noindex.html")
    robots_audit = result.audit_trail.get("http_compliance", {}).get("crawl_permissions", {})
    meta_robots = (robots_audit.get("meta_robots") or "").lower()
    assert "noindex" in meta_robots
    assert robots_audit.get("blocked") is True


# ---------------------------------------------------------------------------
# Overall sanity checks
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "fixture",
    [
        "semantic_html_good.html",
        "semantic_html_bad.html",
        "structured_data_complete.html",
        "structured_data_missing.html",
        "structured_data_faq_complete.html",
        "structured_data_faq_incomplete.html",
        "structured_data_howto_complete.html",
        "metadata_full.html",
        "metadata_empty.html",
        "agent_hints_markdown.html",
        "agent_hints_none.html",
        "readability_clean.html",
        "readability_chrome_heavy.html",
        "robots_noindex.html",
    ],
)
def test_parseability_score_is_bounded(score_fixture, fixture):
    result = score_fixture(fixture)
    assert 0.0 <= result.parseability_score <= 100.0
    expected_pillars = {
        "semantic_html",
        "content_extractability",
        "structured_data",
        "dom_navigability",
        "metadata_completeness",
        "http_compliance",
    }
    assert set(result.component_scores.keys()) == expected_pillars
