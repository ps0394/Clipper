"""Pytest configuration and shared fixtures for Clipper pillar tests.

The tests in this directory are *pillar fixture tests*: each HTML file under
``tests/fixtures/`` exercises one pillar of the scoring model in isolation.
They assert score ranges (not exact values) because scoring is continuous and
sensitive to small heuristic changes. Ranges catch real regressions while
tolerating normal drift.

Tests are offline-only: no URLs and no crawl data are passed to the
evaluator, so no live browser, no network calls, and no axe-core injection
happen. WCAG evaluation falls through to static analysis, and HTTP
compliance runs against the static-fallback path for every pillar that
normally needs a live URL.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

import pytest

from retrievability.access_gate_evaluator import AccessGateEvaluator
from retrievability.parse import _parse_html_file
from retrievability.schemas import ScoreResult


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _score_fixture(fixture_name: str) -> ScoreResult:
    """Parse and score one HTML fixture without any live URL or crawl data."""
    fixture_path = FIXTURES_DIR / fixture_name
    assert fixture_path.exists(), f"Fixture not found: {fixture_path}"

    parse_result = _parse_html_file(fixture_path)
    evaluator = AccessGateEvaluator()
    return evaluator.evaluate_access_gate(parse_result.to_dict(), url=None, crawl_data=None)


@pytest.fixture(scope="session")
def score_fixture():
    """Return a callable that scores a fixture by filename."""
    return _score_fixture


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIXTURES_DIR
