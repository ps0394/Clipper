"""Content-type detection and scoring profiles (Phase 1.1).

Clipper historically applied a single prose-biased weight set to every URL.
That over-penalized landing pages, API references, sample catalogs, and FAQ
pages on pillars that don't apply to them (long-form extractability on a
landing page, author metadata on an API reference, etc.).

This module introduces lightweight **content-type detection** and a table
of **profile-specific weight overrides**. Every evaluation now carries a
detected ``content_type`` and is scored twice:

* ``parseability_score`` — the weighted average using the profile's weights.
  This is the primary number.
* ``universal_score`` — the weighted average using the default (``article``)
  weights, preserved for backward compatibility and cross-profile comparison.

Detection precedence (first match wins):

1. ``<meta name="ms.topic">`` — explicit content-type declaration.
2. JSON-LD ``@type`` — Schema.org type on the top-level entity.
3. URL path heuristics — path contains ``/api/``, ``/reference/``, etc.
4. DOM heuristics — heading-to-body-text ratio, code-block density.
5. Default: ``article``.

Profiles are weight **overrides**, not wholesale pillar swaps. All six
pillars are still evaluated for every content type.
"""

from __future__ import annotations

import json
import re
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

from bs4 import BeautifulSoup


# Canonical profile names. ``article`` is the default and matches the
# pre-Phase-1.1 weights exactly, so existing scores stay comparable via
# ``universal_score``.
PROFILE_ARTICLE = 'article'
PROFILE_LANDING = 'landing'
PROFILE_REFERENCE = 'reference'
PROFILE_SAMPLE = 'sample'
PROFILE_FAQ = 'faq'
PROFILE_TUTORIAL = 'tutorial'

PROFILE_NAMES = (
    PROFILE_ARTICLE, PROFILE_LANDING, PROFILE_REFERENCE,
    PROFILE_SAMPLE, PROFILE_FAQ, PROFILE_TUTORIAL,
)


# Profile-specific weight overrides. Each profile must sum to 1.0.
# Column order matches the six pillars used throughout the evaluator.
PROFILE_WEIGHTS: Dict[str, Dict[str, float]] = {
    # Default matches the pre-1.1 weights exactly.
    PROFILE_ARTICLE: {
        'semantic_html':           0.25,
        'content_extractability':  0.20,
        'structured_data':         0.20,
        'dom_navigability':        0.15,
        'metadata_completeness':   0.10,
        'http_compliance':         0.10,
    },
    # Landing pages: short body, navigation and structure carry the signal.
    PROFILE_LANDING: {
        'semantic_html':           0.25,
        'content_extractability':  0.10,
        'structured_data':         0.30,
        'dom_navigability':        0.15,
        'metadata_completeness':   0.10,
        'http_compliance':         0.10,
    },
    # API reference / docs index: structure + metadata, not prose.
    PROFILE_REFERENCE: {
        'semantic_html':           0.30,
        'content_extractability':  0.10,
        'structured_data':         0.20,
        'dom_navigability':        0.15,
        'metadata_completeness':   0.15,
        'http_compliance':         0.10,
    },
    # Sample / code catalog: code blocks dominate, metadata matters.
    PROFILE_SAMPLE: {
        'semantic_html':           0.20,
        'content_extractability':  0.25,
        'structured_data':         0.20,
        'dom_navigability':        0.10,
        'metadata_completeness':   0.15,
        'http_compliance':         0.10,
    },
    # FAQ: Q&A structure expressed in JSON-LD matters more than prose length.
    PROFILE_FAQ: {
        'semantic_html':           0.25,
        'content_extractability':  0.15,
        'structured_data':         0.30,
        'dom_navigability':        0.15,
        'metadata_completeness':   0.05,
        'http_compliance':         0.10,
    },
    # Tutorial: prose + code, same as article but slightly more extractability.
    PROFILE_TUTORIAL: {
        'semantic_html':           0.25,
        'content_extractability':  0.25,
        'structured_data':         0.15,
        'dom_navigability':        0.15,
        'metadata_completeness':   0.10,
        'http_compliance':         0.10,
    },
}

# Runtime assertion: every profile must sum to 1.0 (with float tolerance).
for _name, _weights in PROFILE_WEIGHTS.items():
    assert abs(sum(_weights.values()) - 1.0) < 1e-6, (
        f"Profile {_name!r} weights do not sum to 1.0: {sum(_weights.values())}"
    )


# --- Clipper v2 scoring weights (Session 2, Phase 6 roadmap) ------------------
#
# v2 collapses all profile-specific weights to a single two-pillar composite.
# Evidence: corpus-002 single-pillar correlations vs accuracy_rendered
# (findings/phase-5-corpus-002-findings.md Addendum B §B.1):
#
#     content_extractability   r = +0.484
#     http_compliance          r = +0.242
#     metadata_completeness    r = +0.224
#     structured_data          r = +0.036
#     dom_navigability         r = -0.189
#     semantic_html            r = -0.301
#
# γ experiments (scripts/gamma-experiments.py, Addendum B §B.2) showed the
# top-2 equal-weighted composite reaches Pearson r = +0.548 on corpus-002,
# well above the +0.35 ship gate. All six pillars continue to be evaluated
# and reported; four of them carry zero headline weight in v2 but remain
# as first-class diagnostics for authors.
#
# v1 PROFILE_WEIGHTS above are retained for backward-compat, test fixtures,
# and the profile-detection audit trail. They are NOT used to compute the
# headline score in v2.
CLIPPER_SCORING_VERSION = 'v2-evidence-partial'

V2_WEIGHTS: Dict[str, float] = {
    'semantic_html':           0.00,
    'content_extractability':  0.50,
    'structured_data':         0.00,
    'dom_navigability':        0.00,
    'metadata_completeness':   0.00,
    'http_compliance':         0.50,
}

V2_HEADLINE_PILLARS = tuple(p for p, w in V2_WEIGHTS.items() if w > 0)
V2_DIAGNOSTIC_PILLARS = tuple(p for p, w in V2_WEIGHTS.items() if w == 0)

assert abs(sum(V2_WEIGHTS.values()) - 1.0) < 1e-6, (
    f"V2_WEIGHTS do not sum to 1.0: {sum(V2_WEIGHTS.values())}"
)


# ms.topic values used across Microsoft Learn and similar Microsoft-hosted
# docs. Mapped to Clipper profile names. Unknown ms.topic values fall
# through to the next detection stage.
MS_TOPIC_TO_PROFILE: Dict[str, str] = {
    'overview':            PROFILE_LANDING,
    'landing-page':        PROFILE_LANDING,
    'hub-page':            PROFILE_LANDING,
    'reference':           PROFILE_REFERENCE,
    'api-reference':       PROFILE_REFERENCE,
    'rest-api':            PROFILE_REFERENCE,
    'language-reference':  PROFILE_REFERENCE,
    'sample':              PROFILE_SAMPLE,
    'samples':             PROFILE_SAMPLE,
    'faq':                 PROFILE_FAQ,
    'tutorial':            PROFILE_TUTORIAL,
    'quickstart':          PROFILE_TUTORIAL,
    'how-to':              PROFILE_TUTORIAL,
    'how-to-guide':        PROFILE_TUTORIAL,
}

# Schema.org @type values that map cleanly to a profile. Anything else
# (``Article``, ``TechArticle``, etc.) falls through to the default.
SCHEMA_TYPE_TO_PROFILE: Dict[str, str] = {
    'faqpage':        PROFILE_FAQ,
    'howto':          PROFILE_TUTORIAL,
    'softwaresourcecode': PROFILE_SAMPLE,
    'collectionpage': PROFILE_LANDING,
    'webpage':        PROFILE_LANDING,
    'apireference':   PROFILE_REFERENCE,
    'techarticle':    PROFILE_ARTICLE,
    'article':        PROFILE_ARTICLE,
    'newsarticle':    PROFILE_ARTICLE,
    'blogposting':    PROFILE_ARTICLE,
}

# URL path fragments, checked in order. First hit wins.
URL_HEURISTICS: Tuple[Tuple[str, str], ...] = (
    ('/api/',         PROFILE_REFERENCE),
    ('/reference/',   PROFILE_REFERENCE),
    ('/samples/',     PROFILE_SAMPLE),
    ('/sample/',      PROFILE_SAMPLE),
    ('/faq',          PROFILE_FAQ),
    ('/tutorial',     PROFILE_TUTORIAL),
    ('/quickstart',   PROFILE_TUTORIAL),
    ('/how-to',       PROFILE_TUTORIAL),
    ('/overview',     PROFILE_LANDING),
    ('/landing',      PROFILE_LANDING),
)


def detect_content_type(
    soup: BeautifulSoup,
    url: Optional[str] = None,
) -> Tuple[str, Dict[str, str]]:
    """Detect the content type of a parsed page.

    Returns a ``(profile_name, detection_trace)`` tuple. ``detection_trace``
    records which signal matched (``ms_topic``, ``schema_type``, ``url``,
    ``dom``, or ``default``) and the matched value, so the audit trail can
    explain why a given profile was chosen.
    """
    trace: Dict[str, str] = {}

    # 1. <meta name="ms.topic">
    ms_topic_meta = soup.find('meta', attrs={'name': re.compile(r'^ms\.topic$', re.I)})
    if ms_topic_meta:
        value = (ms_topic_meta.get('content') or '').strip().lower()
        trace['ms_topic_raw'] = value
        if value in MS_TOPIC_TO_PROFILE:
            trace['source'] = 'ms_topic'
            trace['matched_value'] = value
            return MS_TOPIC_TO_PROFILE[value], trace

    # 2. JSON-LD @type
    schema_type = _extract_top_schema_type(soup)
    if schema_type:
        trace['schema_type_raw'] = schema_type
        key = schema_type.lower()
        if key in SCHEMA_TYPE_TO_PROFILE:
            trace['source'] = 'schema_type'
            trace['matched_value'] = schema_type
            return SCHEMA_TYPE_TO_PROFILE[key], trace

    # 3. URL path heuristics
    if url:
        path = (urlparse(url).path or '').lower()
        for fragment, profile in URL_HEURISTICS:
            if fragment in path:
                trace['source'] = 'url'
                trace['matched_value'] = fragment
                return profile, trace

    # 4. DOM heuristics — very cheap fallbacks. Only fire when the signal
    #    is strong enough to be interesting. The defaults are conservative:
    #    ambiguous pages stay on ``article``.
    dom_profile = _dom_heuristic_profile(soup)
    if dom_profile:
        trace['source'] = 'dom'
        trace['matched_value'] = dom_profile
        return dom_profile, trace

    trace['source'] = 'default'
    return PROFILE_ARTICLE, trace


def _extract_top_schema_type(soup: BeautifulSoup) -> Optional[str]:
    """Return the first recognizable @type from any JSON-LD block."""
    for script in soup.find_all('script', type='application/ld+json'):
        raw = script.string or script.get_text() or ''
        raw = raw.strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            continue

        for node in _iter_schema_nodes(data):
            if not isinstance(node, dict):
                continue
            type_value = node.get('@type')
            if isinstance(type_value, list):
                type_value = next((t for t in type_value if isinstance(t, str)), None)
            if isinstance(type_value, str) and type_value:
                return type_value
    return None


def _iter_schema_nodes(data):
    """Yield dict nodes from arbitrarily nested JSON-LD payloads."""
    if isinstance(data, dict):
        yield data
        for v in data.values():
            yield from _iter_schema_nodes(v)
    elif isinstance(data, list):
        for item in data:
            yield from _iter_schema_nodes(item)


def _dom_heuristic_profile(soup: BeautifulSoup) -> Optional[str]:
    """Very cheap structural fallbacks.

    Only returns a non-default profile when the signal is strong. Keeps
    ambiguous pages on the default ``article`` profile so small drift in
    heading counts doesn't flip profiles.
    """
    body = soup.find('body')
    if not body:
        return None

    text = body.get_text(' ', strip=True)
    if not text:
        return None

    paragraphs = body.find_all('p')
    total_paragraph_chars = sum(len(p.get_text(strip=True)) for p in paragraphs)

    # Heuristic 1: landing page — lots of headings, very little paragraph prose.
    headings = body.find_all(['h1', 'h2', 'h3'])
    if len(headings) >= 6 and total_paragraph_chars < 600:
        return PROFILE_LANDING

    # Heuristic 2: sample / reference — code dominates.
    code_chars = sum(
        len((tag.get_text() or '')) for tag in body.find_all(['pre', 'code'])
    )
    if code_chars > 0 and total_paragraph_chars > 0:
        if code_chars / (code_chars + total_paragraph_chars) > 0.6:
            return PROFILE_SAMPLE

    return None
