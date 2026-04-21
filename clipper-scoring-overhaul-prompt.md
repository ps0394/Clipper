## Clipper Scoring System Overhaul — Agent Retrievability Reframe

### Context

Clipper (`C:\Repos\Clipper`, repo: ps0394/Clipper) is a standards-based agent retrievability scoring tool. The scoring engine lives in `retrievability/access_gate_evaluator.py` (class `AccessGateEvaluator`). It evaluates HTML pages across 5 weighted pillars and produces a 0-100 composite score.

The current scoring system was designed to measure web standards compliance, but it's being used to evaluate whether agents can access, crawl, retrieve, and use page content for grounding. Several pillars need fixes, and two new pillars need to be added to align the tool with its actual purpose.

### Current Architecture

- **Entry points**: `score.py` (standard mode), `performance_score.py` (async/fast mode)
- **Evaluator**: `access_gate_evaluator.py` — `AccessGateEvaluator` class
- **Each pillar**: A `_evaluate_*` method returning `Tuple[float, Dict]` (score 0-100, audit_trail)
- **Weights**: `WEIGHTS` dict at class level (must sum to 1.0)
- **Output schema**: `schemas.py` — `ScoreResult` dataclass

### Work Items (in order)

#### 1. Fix WCAG Scoring Formula (Bug Fix)

**File**: `access_gate_evaluator.py`, method `_run_axe_evaluation()`, lines ~280-289

**Current (broken)**:
```python
for violation in violations:
    impact = violation.get('impact', 'minor')
    node_count = len(violation.get('nodes', []))
    penalty += severity_weights.get(impact, 5) * node_count
score = max(0, 100 - penalty)
```

**Problem**: Penalty is per-node, not per-rule. A single repeated violation (e.g., Stripe's 104 unlabeled buttons = 2,600 penalty) instantly zeroes the score, even though it represents one fix. This makes scores uninformative for comparison.

**Fix**: Cap penalty per violation rule. Suggested approach:
```python
MAX_PENALTY_PER_RULE = 25  # No single rule can cost more than 25 points
for violation in violations:
    impact = violation.get('impact', 'minor')
    node_count = len(violation.get('nodes', []))
    rule_penalty = severity_weights.get(impact, 5) * min(node_count, 3)  # Diminishing returns
    penalty += min(rule_penalty, MAX_PENALTY_PER_RULE)
score = max(0, 100 - penalty)
```

Add `penalty_per_rule` breakdown to the audit trail for transparency.

#### 2. Add Content Extractability Pillar (New)

**Add method**: `_evaluate_content_extractability(self, html_content: str, signals: Dict) -> Tuple[float, Dict]`

**Standard**: Mozilla Readability algorithm (same algorithm used by Firefox Reader View)

**Install**: `pip install readability-lxml` (Python port of Mozilla Readability)

**Implementation**:
- Run readability extraction on the raw HTML
- Measure: extracted text length vs. raw page text length (signal-to-noise ratio)
- Measure: does the extraction preserve headings, code blocks, lists?
- Measure: what percentage of the page's `<main>` content survives extraction?
- Score 0-100 based on extraction completeness and cleanliness

**Scoring breakdown** (suggested):
- Signal-to-noise ratio: 40 points (extracted meaningful text / total page text)
- Structure preservation: 30 points (headings, lists, code blocks survive extraction)
- Content boundary detection: 30 points (did readability find a clear article boundary?)

**Audit trail** should include: extracted text length, raw text length, ratio, elements preserved, extraction confidence.

#### 3. Add Metadata Completeness Pillar (New)

**Add method**: `_evaluate_metadata_completeness(self, html_content: str, url: Optional[str]) -> Tuple[float, Dict]`

**Standards**: Dublin Core (`<meta>` tags), Schema.org (JSON-LD/microdata), OpenGraph

**Implementation**: Check for the presence and quality of these fields:
- Title (from `<title>`, `og:title`, or Schema.org `name`) — 15 points
- Description (from `<meta name="description">`, `og:description`) — 15 points
- Author/publisher (from `<meta name="author">`, Schema.org `author`) — 15 points
- Date published/modified (from `<meta>` tags, Schema.org, `<time>` elements) — 15 points
- Topic/category (from `<meta name="ms.topic">`, Schema.org `articleSection`, keywords) — 15 points
- Language (from `<html lang="">`, `<meta>` content-language) — 10 points
- Canonical URL (from `<link rel="canonical">`) — 15 points

**Score**: Sum of field scores. Each field scores 0 (absent) or full points (present and non-empty).

#### 4. Refine Structured Data Scoring

**File**: `access_gate_evaluator.py`, method `_evaluate_structured_data()`

**Current (too simple)**:
```python
score_components['json_ld'] = min(len(json_ld_data) * 10, 40)
```

**Fix**: Evaluate schema quality, not just count:
- Schema type appropriateness: Does the `@type` match the content? (20 points)
- Field completeness: Does the JSON-LD include key fields like `name`, `dateModified`, `author`, `description`? (30 points)
- Multiple formats: JSON-LD + OpenGraph + microdata present? (20 points)
- Schema.org validation: Are required properties present for the declared type? (30 points)

#### 5. Narrow HTTP Compliance

**File**: `access_gate_evaluator.py`, methods `_evaluate_http_compliance()` and `_test_content_negotiation()`

**Changes**:
- Remove content-negotiation tests for `application/json`, `text/xml`, `application/xhtml+xml` — agents don't request these
- Keep `text/html` test and redirect chain analysis
- Add: `robots.txt` fetch and parse (check if default user-agent and common bot user-agents are allowed)
- Add: `<meta name="robots">` tag check (noindex, nofollow detection)
- Add: Cache headers check (`Cache-Control`, `ETag`, `Last-Modified`) — agents benefit from caching

#### 6. Reweight Pillars

**File**: `access_gate_evaluator.py`, class-level `WEIGHTS` dict

**Current**:
```python
WEIGHTS = {
    'wcag_accessibility': 0.25,
    'semantic_html': 0.25,
    'structured_data': 0.20,
    'http_compliance': 0.15,
    'content_quality': 0.15
}
```

**New** (after adding pillars):
```python
WEIGHTS = {
    'semantic_html': 0.25,
    'content_extractability': 0.20,
    'structured_data': 0.20,
    'dom_navigability': 0.15,      # renamed from wcag_accessibility
    'metadata_completeness': 0.10,
    'http_compliance': 0.10
}
```

Remove the old `content_quality` pillar (its useful signals are absorbed by `content_extractability`). Rename `wcag_accessibility` to `dom_navigability` to accurately reflect its reframed scope.

Update `STANDARDS_AUTHORITY` dict, `evaluate_access_gate()` orchestration, and all console output strings accordingly.

#### 7. Re-run Evaluation

After all changes, re-run:
```bash
python main.py express learn-analysis-urls.txt --out evaluation/learn-analysis-v2 --name learn-v2 --standard
python main.py express competitive-analysis-urls.txt --out evaluation/competitive-analysis-v2 --name competitive-v2 --standard
```

Compare v1 vs v2 scores to validate the changes produce more meaningful differentiation.

### Testing

- Run existing tests: `python -m pytest` (if tests exist)
- Verify all 5 original Learn URLs still produce valid scores
- Verify the competitive set (Google Cloud, AWS, MDN, Stripe, Mintlify, Wikipedia) produces differentiated scores
- Check that the audit trail for each new pillar contains actionable detail

### Key Files

- `retrievability/access_gate_evaluator.py` — Main evaluator (all pillar methods)
- `retrievability/performance_evaluator.py` — Async version (mirror changes)
- `retrievability/score.py` — Standard scoring entry point
- `retrievability/performance_score.py` — Fast scoring entry point
- `retrievability/schemas.py` — ScoreResult dataclass
- `docs/scoring.md` — Documentation (outdated, needs full rewrite after changes)
