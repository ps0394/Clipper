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

## Classifier lockdown (Phase 4.3)

Unlike the per-pillar fixture tests (which lock score **ranges** on
synthetic HTML), `tests/test_classifier_lockdown.py` locks the exact
**classification output** of `retrievability.profiles.detect_content_type`
against real captured HTML from the `evaluation/learn-analysis-v3` and
`evaluation/competitive-analysis-v3` snapshot directories.

The golden file at `tests/fixtures/classifier_corpus_golden.json` records,
for every URL in those corpora, the `(profile, source, matched_value)`
tuple the classifier produces today. CI fails with the offending URL
and signal named if the classifier drifts.

### When to regenerate

Only when you have **deliberately** changed classifier behavior:

- adjusted `URL_HEURISTICS`, `MS_TOPIC_TO_PROFILE`, `SCHEMA_TYPE_TO_PROFILE`, or the DOM-based fallback in `retrievability/profiles.py`;
- added new snapshot corpora that should be locked in;
- fixed a classifier bug and want to lock the fixed behavior.

### How to regenerate

```bash
# Write a fresh golden from the current classifier + snapshots
python scripts/generate-classifier-golden.py

# Review the diff, make sure every change is intentional
git diff tests/fixtures/classifier_corpus_golden.json

# Commit the golden alongside the classifier change in one PR
```

### How to check without writing

```bash
python scripts/generate-classifier-golden.py --check
```

Exits non-zero and prints a per-URL diff if the classifier has drifted
from the committed golden. Useful in pre-commit hooks and local
development loops.

### Extending the corpus

Corpora are declared in `scripts/generate-classifier-golden.py` via the
`CORPORA` list. Add more snapshot directories there when new evaluation
runs produce HTML worth locking down. The test enforces that every
canonical profile (`article`, `landing`, `reference`, `sample`, `faq`,
`tutorial`) is represented in the golden; extend the corpus rather than
silently shrink coverage.

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
