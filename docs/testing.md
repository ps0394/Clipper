# Testing Clipper

Clipper's test suite is intentionally narrow. It does not try to validate the
*whole* scoring engine against real pages — those answers are subjective and
live in `evaluation/`. Instead, it locks in the behavior of each scoring
**pillar** against small, hand-built HTML fixtures. When a refactor breaks a
pillar, these tests fail fast.

## Running the suite

```bash
pip install -r requirements-dev.txt
pytest -q
```

The suite is offline: no URLs, no network, no live browser. It takes under a
second.

## Layout

```
tests/
  conftest.py          # shared fixtures, helper that parses + scores one file
  test_pillars.py      # per-pillar assertions (ranges + ordering)
  _calibrate.py        # one-off script for picking range bounds (not a test)
  fixtures/
    semantic_html_good.html
    semantic_html_bad.html
    structured_data_complete.html
    structured_data_missing.html
    metadata_full.html
    metadata_empty.html
    agent_hints_markdown.html
    agent_hints_none.html
    readability_clean.html
    readability_chrome_heavy.html
    robots_noindex.html
```

Each fixture targets **one** pillar's success or failure shape. Pairs (good /
bad) exist so the suite can assert both an absolute range and an ordering
relationship — an ordering regression catches weight or sign errors that a
range alone would miss.

## Why ranges, not exact scores

Scoring is continuous. The engine's heuristics (heading density, boilerplate
estimation, Readability's confidence) will legitimately drift by a point or
two between versions of their upstream libraries. Exact assertions would
force meaningless test updates on every dependency bump.

Ranges are picked so that:

- a normal run sits in the middle of the range,
- a real regression (broken pillar, inverted signal, weight error) falls
  outside,
- small heuristic drift does not fail the test.

## Adding a new fixture

1. Drop the HTML file under `tests/fixtures/`.
2. Run `python -m tests._calibrate` to see the component scores it produces.
3. Add assertions to `test_pillars.py` using ranges wide enough to absorb
   normal drift but tight enough to catch real regressions. Prefer a pair
   (good + bad) so you can assert ordering, not just an absolute value.
4. Keep the fixture minimal: only include the markup that exercises the
   pillar you care about.

## Regression-check sanity test

To confirm the tests actually catch regressions, sabotage a pillar evaluator
temporarily and re-run:

```bash
python -c "
import retrievability.access_gate_evaluator as age
age.AccessGateEvaluator._evaluate_semantic_html = lambda self, h, s: (0.0, {})
import pytest
raise SystemExit(pytest.main(['-q']))
"
```

The semantic-HTML tests should fail. This check is not part of the suite — it
is a one-time sanity step when the suite is first built or substantially
modified.
