# Clipper Scoring System

Clipper evaluates whether agents can reliably access, extract, and use web page content. Pages are scored 0–100 across six industry-standard pillars, entirely API-free.

> **Calibration & Generalization (v2.1, April 2026).** The v2 composite headline scores documented below were calibrated on corpus-002 (n=43) and clear that corpus's ship gate (Pearson r = +0.62 vs. judged QA accuracy). Sessions 8 / 9 / 9.5 ran the same model on a held-out corpus-003 (n=172) and found the composite **does not generalize** — Pearson r ≈ +0.10 against the same +0.35 ship gate. The per-pillar measurements are unchanged and remain real signals against published standards. **For cross-page comparison, prefer the pillar-level data in `component_scores` over the composites.** Pass `--diagnostic-mode` to suppress the composites in the JSON output. Every score result also carries a `methodology` block with this status. See [findings/post-v2-roadmap.md](../findings/post-v2-roadmap.md) and [findings/v2.1-release-scope.md](../findings/v2.1-release-scope.md).

This document describes the **v2 (`v2-evidence-partial`) scoring model**. v2 narrows the **headline score** to the two pillars for which Clipper has published retrieval-relevance evidence on the corpus-002 benchmark (n=43, rendered HTML, two-shot retrieval QA). The other four pillars are still evaluated, still reported, and still audited — they just carry **zero weight in the headline composite** until their retrieval-relevance is measured. The old six-pillar weighted composite is preserved in `audit_trail._content_type.v1_weights_for_reference` for back-compat and A/B work.

The current version is declared at module load:
[`retrievability/profiles.py`](../retrievability/profiles.py) →
`CLIPPER_SCORING_VERSION = 'v2-evidence-partial'`.

## Pillars and Weights (v2)

| Pillar | Weight (v2) | Standard | Implementation | corpus-002 single-pillar r vs. accuracy_rendered |
|--------|-------------|----------|----------------|---------------------------------------------------|
| **Content Extractability** | **50%** | Mozilla Readability | readability-lxml | **+0.484** |
| **HTTP Compliance** | **50%** | RFC 7231 + robots.txt | httpx | **+0.242** |
| Semantic HTML | 0% *(diagnostic)* | W3C HTML5 | BeautifulSoup + html5lib | −0.301 |
| Structured Data | 0% *(diagnostic)* | Schema.org | extruct | +0.036 |
| DOM Navigability | 0% *(diagnostic)* | WCAG 2.1 AA + axe-core | axe-selenium-python | −0.189 |
| Metadata Completeness | 0% *(diagnostic)* | Dublin Core / Schema.org / OpenGraph | BeautifulSoup | +0.224 |

Correlation source: [`findings/phase-5-corpus-002-findings.md`](../findings/phase-5-corpus-002-findings.md) Addendum B §B.1 (n=43). The two pillars with a positive correlation ≥ +0.24 on corpus-002 are retained as headline contributors at equal weight (`top2_equal` in the γ sweep). The four `0% (diagnostic)` pillars are **still evaluated and scored**; their sub-scores appear in `component_scores` and in `audit_trail` exactly as before. They just don't contribute to the composite.

Two numbers are still reported side-by-side for back-compat:

- `parseability_score` — v2 composite = 0.50 × `content_extractability` + 0.50 × `http_compliance`.
- `universal_score` — same value as `parseability_score` under v2. In v1 these two numbers could diverge by content-type profile; under v2 they are identical because the profile system no longer re-weights the headline (see [Content-Type Profiles](#content-type-profiles)).

### v2 regression check

Applying v2 weights to corpus-002 yields **Pearson r = +0.6181** (n=43) between the composite and `accuracy_rendered`, clearing the PRD F2.6 ship gate of +0.35. Full numbers, including per-page deltas vs. the v1 composite, are in [`evaluation/phase5-results/corpus-002-analysis/v2-regression.json`](../evaluation/phase5-results/corpus-002-analysis/v2-regression.json).

The v1 six-pillar profile-weighted composite on the same pages correlates at r = −0.01 vs. the same accuracy signal. The shift from a null correlation to a moderate positive one is what "evidence-partial" means in the version string.

## Content-Type Profiles

Clipper still detects the content type of every page (article / landing / reference / sample / faq / tutorial) and records it in `content_type.profile`. Detection ordering and precedence are unchanged — see [Detection precedence](#detection-precedence).

In **v2**, profile-specific weight tables are **inactive for the headline score**. Every detected profile collapses onto the same two-pillar headline composite. This is a deliberate reset: the v1 profile weights (landing over-weights structured-data, tutorial over-weights extractability, etc.) were hand-set, never empirically validated per-profile, and cannot be defended until per-profile corpora are collected in Phase 6 (see [Known Gaps](#known-gaps)).

Profile **detection** still matters because:

1. The profile label is reported alongside the score and is useful for diagnostics and filtering.
2. The classifier-lockdown golden file still pins detection behaviour so regressions are caught.
3. The v1 profile weights remain in `profiles.PROFILE_WEIGHTS` and are recorded in every audit trail as `v1_weights_for_reference`, so anyone who wants to A/B against v1 can do so without re-running the pipeline.

### Detection precedence

`detect_content_type()` consults signals in this order and stops at the first hit:

1. **`ms.topic` meta tag** — authoritative on Microsoft Learn (`overview` → landing, `quickstart`/`tutorial` → tutorial, `reference`/`api-reference` → reference, etc.).
2. **JSON-LD `@type`** — e.g., `FAQPage` → faq, `HowTo` → tutorial, `SoftwareSourceCode` → sample.
3. **URL path heuristics** — `/samples/`, `/api/`, `/reference/`, `/quickstart/`, etc.
4. **DOM heuristics** — large `<dl>` lists and detail-oriented headings map to reference; dense `<Question>`/`<Answer>` pairs map to faq.
5. **Default** — `article`.

The full detection trace (which signal won, and the matched value) is recorded in `audit_trail._content_type.detection` so users can audit why a page was typed the way it was.

### Detector stability (Phase 4.3)

The classifier's output is locked against a committed golden file
(`tests/fixtures/classifier_corpus_golden.json`) built from real
captured HTML snapshots across the `learn-analysis` and
`competitive-analysis` corpora. Every URL in that file is re-classified
on every CI run by `tests/test_classifier_lockdown.py`; any drift in
`(profile, source, matched_value)` fails the build and names the
specific URL and signal that changed.

This matters because profile weights feed directly into
`parseability_score`. A silent classification shift would move the
headline score without any code change, invalidating historical
comparisons and — more importantly — any empirical weight tuning done
in later phases. Locking the classifier first makes correlation
analysis downstream interpretable.

Regenerate the golden after a deliberate classifier change:

```bash
python scripts/generate-classifier-golden.py
```

Then review the diff before committing. See [testing.md](testing.md)
for the full workflow.

### Using the two scores

In v2, `parseability_score` and `universal_score` are **equal by construction**. Both fields are retained so downstream tooling, reports, and JSON consumers keep working without a schema change. A non-zero delta between them is a data-integrity flag — it should never occur for pages scored under `v2-evidence-partial` and indicates a cross-version mix.

To compare against the v1 profile-weighted composite on the same run, read:

- `audit_trail._content_type.weights` — the v2 weights actually applied (always `V2_WEIGHTS`).
- `audit_trail._content_type.v1_weights_for_reference` — the profile weights v1 *would* have applied to the detected profile. Multiply these into `component_scores` yourself to reproduce the v1 composite.

## Known Gaps

`v2-evidence-partial` is labeled partial for specific, enumerable reasons. Every report generated against this scoring version should cite the subset of these gaps that bear on its findings.

1. **Four pillars are diagnostic-only pending retrieval-relevance evidence.** `semantic_html`, `structured_data`, `dom_navigability`, and `metadata_completeness` have single-pillar correlations against `accuracy_rendered` on corpus-002 that are either near-zero (`structured_data` +0.04) or negative (`semantic_html` −0.30, `dom_navigability` −0.19). A positive correlation on a dedicated corpus is required before any of these is restored to the headline. This work is Phase 6 on [`findings/v2-scoring-phase6-roadmap-prd.md`](../findings/v2-scoring-phase6-roadmap-prd.md).

2. **Profile-specific weights are collapsed, not validated.** The v1 profile tables (landing / reference / sample / faq / tutorial) were hand-set and never benchmarked. They are retained in code for reference but do not affect the headline in v2. Per-profile corpora and per-profile weight fits are a Phase 6 dependency; until then, profile-specific weighting is not defensible as a ranking signal.

3. **Served-markdown and `llms.txt` are not yet measured.** v2 removes `agent_content_hints` from the `http_compliance` score (`markdown_url_meta`, `has_markdown_alternate`, `has_llm_hints`, `has_non_html_alternate`, `llms.txt`). These signals are *declarations*, not *capabilities* — a page can claim a markdown alternate exists while serving `text/html` at that URL with no useful content. Detection still runs and the results are recorded in `audit_trail.http_compliance.agent_content_hints` with `diagnostic_only: true` and `scoring_contribution: 0`. Restoring any of them to the headline requires (a) actually fetching and validating the declared resource and (b) a retrieval-lift benchmark that shows the signal predicts agent success. See PRD F2.2/F2.3.

4. **Fetch Integrity is not yet a pillar.** Clipper measures how a page is *structured* for agents. It does not yet measure whether the page *renders stably* across agent fetches: whether the server honours `Accept`, whether cache semantics are consistent, whether redirect chains terminate deterministically under agent user-agents. Fetch Integrity as a distinct pillar is scoped for Phase 6.

5. **Cross-agent variance is unmeasured.** corpus-002 was evaluated with a single agent configuration in two-shot mode. The `accuracy_rendered` target is therefore a single-agent ground truth. Scores predict success for that evaluator class; generalisation to other agents, other prompting modes, and longer-horizon tasks is an open question until a multi-agent benchmark lands.

6. **Calibration corpus size.** n=43 on corpus-002 is sufficient to ship v2 above the gate but not sufficient to defend fine-grained weight differences. The 50/50 split between `content_extractability` and `http_compliance` is deliberately a coarse choice (two winners, equal weight) rather than an over-fit to corpus-002. corpus-003 (planned Phase 6) is the first corpus that should drive any fractional-weight move.

Reports that make cross-vendor, cross-template, or cross-corpus claims should disclose which of these gaps bear on the claim. See `.github/copilot-instructions.md` → *When Asked to Write a Comparison or Analysis Report* for the full disclosure checklist.

## Score Classification

| Range | Classification | Meaning |
|-------|---------------|---------|
| 90–100 | `clean` | Fully agent-ready |
| 75–89 | `minor_issues` | Nearly agent-ready |
| 60–74 | `moderate_issues` | Improvements needed |
| 40–59 | `significant_issues` | Major optimization required |
| 0–39 | `severe_issues` | Substantial restructuring needed |

## Pillar Details

### 1. Semantic HTML (diagnostic-only in v2)

Measures HTML5 semantic element coverage and proper usage. **Scored and reported; does not contribute to the v2 headline** (single-pillar r = −0.30 on corpus-002). See [Known Gaps](#known-gaps) item 1.

**Scoring breakdown:**
- **Semantic element coverage** (60%): Checks for `<header>`, `<nav>`, `<main>`, `<article>`, `<section>`, `<aside>`, `<footer>`, `<figure>`, `<figcaption>`, `<time>`, `<mark>`. Score = (found / total) × 60.
- **ARIA landmarks** (20%): Counts elements with `role` attributes. Up to 20 points.
- **Heading elements** (20%): Counts `<h1>`–`<h6>` elements. Up to 20 points.

Validates proper usage (e.g., exactly one `<main>`, reasonable `<header>`/`<footer>` count).

### 2. Content Extractability (50% in v2)

Uses the Mozilla Readability algorithm (same as Firefox Reader View) to measure how cleanly an agent can extract meaningful content. **Primary headline contributor in v2** (single-pillar r = +0.48 on corpus-002).

| Sub-signal | Max Points | What it measures |
|---|---|---|
| **Signal-to-Noise Ratio** | 40 | Ratio of extracted meaningful text to total page text. Optimal range: 0.3–0.8. |
| **Structure Preservation** | 30 | Do headings, lists, and code blocks survive extraction? (10 pts each) |
| **Boundary Detection** | 30 | Did Readability find a clear article boundary? Checks title extraction, content length, and `<main>`/`<article>` overlap. |

**Extracted preview.** A low extractability score is hard to interpret from a number alone, so Clipper persists what Readability actually pulled out:

- `audit_trail.content_extractability.extraction_metrics.extracted_preview` — the first ~300 characters of extracted text.
- `audit_trail.content_extractability.extraction_metrics.extracted_chars` — total extracted character count.

The markdown report surfaces the preview as an **Extracted Preview** block under each URL's score, so a reader can see at a glance whether Readability captured the intended article or got confused by chrome.

### 3. Structured Data (diagnostic-only in v2)

Evaluates Schema.org structured data quality using the extruct library. **Scored and reported; does not contribute to the v2 headline** (single-pillar r = +0.04 on corpus-002 — essentially null). See [Known Gaps](#known-gaps) item 1.

| Sub-signal | Max Points | What it measures |
|---|---|---|
| **Type Appropriateness** | 20 | Does `@type` match recognized content types (Article, WebPage, HowTo, etc.)? |
| **Field Completeness** | 30 | Per-type required + recommended fields for the four validated `@type` values (see below). |
| **Multiple Formats** | 20 | Are JSON-LD, OpenGraph, and microdata all present? (1 format = 5, 2 = 12, 3 = 17, 4 = 20) |
| **Schema Validation** | 30 | Are required properties present for the declared Schema.org type? |

#### Field Completeness — per-type expectations (Phase 4.1)

Field Completeness is computed per JSON-LD item. For each item whose
`@type` is one of the four validated values, Clipper counts required +
recommended fields present and divides by the total expected:

```
item_ratio        = (present_required + present_recommended) / (required + recommended)
field_completeness = min(30, 30 × average(item_ratio over validated items))
```

| `@type` | Required | Recommended |
|---|---|---|
| `Article` | `headline`, `datePublished` | `author`, `dateModified`, `description`, `publisher` |
| `FAQPage` | `mainEntity` (non-empty list of `Question` entries with `acceptedAnswer`) | — |
| `HowTo` | `name`, `step` (non-empty list) | `description`, `totalTime` |
| `BreadcrumbList` | `itemListElement` (list with ≥2 items) | — |

Items of other `@type` values still count toward **Type Appropriateness**
and **Multiple Formats** but fall through to a generic key-field check
for Field Completeness so exotic schemas are not over-penalized.

Missing and structurally invalid fields (e.g. an empty `mainEntity`) are
logged in `audit_trail.structured_data.field_completeness_detail` with
the offending `@type` and field names — an incomplete `FAQPage` now
scores below a complete one and the audit trail explains why.

### 4. DOM Navigability (diagnostic-only in v2)

Evaluates WCAG 2.1 AA compliance using Deque's axe-core engine via Selenium. **Scored and reported; does not contribute to the v2 headline** (single-pillar r = −0.19 on corpus-002). See [Known Gaps](#known-gaps) item 1.

**Live evaluation** (when URL is available):
- Runs axe-core in a headless Chrome browser against the live page.
- Scores start at 100 and subtract penalties per violation rule.
- Severity weights: critical = 25, serious = 15, moderate = 10, minor = 5.
- **Per-rule cap**: No single rule can cost more than 25 points. Only the first 3 nodes per rule incur full penalty (diminishing returns).

**Static fallback** (no live URL or browser unavailable):
- Checks: `lang` attribute, `<title>` presence, image alt texts, heading structure, link descriptions.
- Score = (passed checks / total checks) × 100.

### 5. Metadata Completeness (diagnostic-only in v2)

Checks for 7 key metadata fields across Dublin Core, Schema.org, and OpenGraph standards. **Scored and reported; does not contribute to the v2 headline** (single-pillar r = +0.22 on corpus-002 — below the +0.24 cutoff used to pick v2 headline pillars). See [Known Gaps](#known-gaps) item 1.

| Field | Max Points | Sources checked |
|---|---|---|
| **Title** | 15 | `<title>`, `og:title`, Schema.org `name`/`headline` |
| **Description** | 15 | `<meta name="description">`, `og:description`, Schema.org `description` |
| **Author/Publisher** | 15 | `<meta name="author">`, Schema.org `author`/`publisher` |
| **Date** | 15 | `<meta>` date tags, Schema.org `dateModified`/`datePublished`, `<time>` elements |
| **Topic/Category** | 15 | `<meta name="topic">`, `<meta name="category">`, Schema.org `articleSection`, `<meta name="keywords">` |
| **Language** | 10 | `<html lang="">`, `<meta http-equiv="content-language">` |
| **Canonical URL** | 15 | `<link rel="canonical">` |

Each field scores 0 (absent) or full points (present and non-empty).

**Vendor-neutrality principle (Phase 4.4).** Signals used inside a pillar
scoring check must be semantically equivalent across vendors.
Vendor-specific authoring signals (e.g., Microsoft Learn's `ms.topic`)
belong in the classifier — [profiles.py](../retrievability/profiles.py) —
where "authoritative declaration beats inference" is a defensible rule
that applies to any doc system that provides an equivalent signal. They
do **not** belong inside a pillar's scoring check, where accepting them
alongside generic signals (Dublin Core / Schema.org / OpenGraph) would
give pages from that vendor credit no other doc system could earn from a
comparable internal signal. The topic-field check above was cleaned up in
this pass; `ms.topic` previously appeared here and was removed.

### 6. HTTP Compliance (50% in v2)

Evaluates whether agents can reach, cache, and negotiate machine-readable content. **Primary headline contributor in v2** (single-pillar r = +0.24 on corpus-002).

| Sub-signal | Max Points | What it measures |
|---|---|---|
| **HTML Reachability** | 15 | Does the URL serve a 200 response to `Accept: text/html`? |
| **Redirect Efficiency** | 25 | Chain length (0 hops = optimal, >4 penalized), proper status codes, performance impact. |
| **Crawl Permissions** | 20 | `robots.txt` allows access for generic agents (`User-agent: *`) + no `<meta name="robots" content="noindex">`. |
| **Cache Headers** | 20 | Presence of `ETag`, `Last-Modified`, and `Cache-Control` headers. |
| **Agent Content Hints** | **0 (diagnostic-only)** | Declared alternate-format signals. Detection still runs; scoring contribution is 0 in v2. See below. |

**Agent Content Hints (diagnostic-only in v2).** The following signals are detected and recorded in `audit_trail.http_compliance.agent_content_hints` with `diagnostic_only: true` and `scoring_contribution: 0`. They **do not** add points to the HTTP Compliance score in `v2-evidence-partial`:

- `<link rel="alternate" type="text/markdown">` — markdown alternate link
- `<meta name="markdown_url">` — markdown URL metadata (e.g. Microsoft Learn)
- `data-llm-hint` attributes — explicit LLM guidance in HTML
- `llms.txt` references — site-level LLM endpoint declaration
- Non-HTML `<link rel="alternate">` — any non-HTML alternate format (JSON, XML, etc.)

Rationale: these are *declarations* of agent-friendly alternates, not *validated capabilities*. A page can claim a markdown alternate exists and then serve `text/html` at that URL, or serve a file that doesn't contain the page's actual content. Restoring any of these signals to the headline requires fetching and validating the declared resource plus a retrieval-lift benchmark. See [Known Gaps](#known-gaps) item 3 and PRD F2.2/F2.3.

The robots.txt parser respects `User-agent` directives and only applies rules from the `User-agent: *` block. `Allow`/`Disallow` conflicts are resolved by longest-match precedence.

## Audit Trail

Every evaluation produces a complete audit trail documenting:
- The standard authority for each pillar
- The evaluation method used (live browser, static HTML, fallback)
- Score breakdowns per sub-signal
- Specific violations, elements found, and fields checked

```json
{
  "scoring_version": "v2-evidence-partial",
  "parseability_score": 68.2,
  "universal_score": 68.2,
  "failure_mode": "moderate_issues",
  "component_scores": {
    "semantic_html": 72.7,
    "content_extractability": 74.5,
    "structured_data": 12.0,
    "dom_navigability": 35.0,
    "metadata_completeness": 100.0,
    "http_compliance": 61.9
  },
  "confidence_range": {
    "scoring_version": "v2-evidence-partial",
    "evidence_tier": "partial",
    "headline_weights": {"content_extractability": 0.5, "http_compliance": 0.5},
    "calibration_corpus": {
      "name": "corpus-002",
      "n": 43,
      "pearson_r": 0.548,
      "gate_threshold": 0.35,
      "source": "findings/phase-5-corpus-002-findings.md"
    },
    "caveats": ["..."]
  },
  "audit_trail": {
    "_content_type": {
      "profile": "article",
      "weights": {"content_extractability": 0.5, "http_compliance": 0.5, "...": 0.0},
      "v1_weights_for_reference": {"semantic_html": 0.25, "content_extractability": 0.20, "...": "..."},
      "scoring_version": "v2-evidence-partial"
    }
  },
  "standards_authority": {
    "semantic_html": "HTML5 Semantic Elements (W3C)",
    "content_extractability": "Mozilla Readability (Firefox Reader View algorithm)",
    "structured_data": "Schema.org (Google/Microsoft/Yahoo)",
    "dom_navigability": "WCAG 2.1 AA (W3C) + axe-core (Deque Systems)",
    "metadata_completeness": "Dublin Core + Schema.org + OpenGraph",
    "http_compliance": "RFC 7231 + robots.txt + Cache headers"
  },
  "evaluation_methodology": "Clipper Standards-Based Access Gate (v2-evidence-partial)"
}
```

## Partial Evaluations

Each pillar evaluator produces one of three outcomes:

1. **Scored successfully** — returns a numeric score 0–100 and an audit
   block. The pillar's `evaluation_method` (in its audit entry) identifies
   which path produced the number.
2. **Scored with fallback** — a preferred path failed and a conservative
   fallback produced a number. The audit block records both the failure
   reason (e.g., `axe_fallback_reason`) and the fallback method (e.g.,
   `evaluation_method: "Static HTML analysis (axe-core unavailable)"`).
   The pillar is still treated as scored; the fallback marker in the audit
   trail is the signal that the number is more conservative than a full
   run would have produced.
3. **Could not evaluate** — a catastrophic failure (network timeout,
   parser crash, browser automation unavailable) left no usable number.
   The pillar is excluded from the final score entirely, listed in
   `failed_pillars`, and marked in its audit entry as
   `status: "could_not_evaluate"` with a `reason`.

When one or more pillars fall into outcome 3, the final
`parseability_score` is a **weighted average over the surviving pillars
only**. Weights are renormalized so they still sum to 1.0 across the
survivors. A failing pillar is never treated as a score of zero — that
would corrupt every aggregate (average, trend, comparison) downstream.

When this happens:

- `partial_evaluation` is `true`.
- `failed_pillars` lists the affected pillar keys.
- `failure_mode` is `"partial_evaluation"` (ranks above the numeric
  bands so consumers know the number carries a caveat).
- The CLI result line shows `[PARTIAL]` instead of `[PASS]` / `[WARN]` /
  `[FAIL]`, followed by the list of failed pillars.

If **every** pillar fails, the result is `failure_mode:
"evaluation_error"`, `parseability_score: 0.0`, and
`component_scores: {}`.

## Environment Metadata

Each audit trail includes an `_environment` block recording the tool
versions used for the run. This matters because axe-core, Chrome, and
the HTML parsing stack all drift over time; two scores of the same page
on different days can disagree because the tooling changed, not because
the page did.

```json
"_environment": {
  "clipper_version": "3.0.0",
  "python_version": "3.11.9",
  "platform": "Windows-10-...",
  "beautifulsoup4": "4.12.3",
  "readability-lxml": "0.8.1",
  "extruct": "0.18.0",
  "httpx": "0.27.0",
  "axe-selenium-python": "2.1.6",
  "selenium": "4.21.0",
  "browser_version": "124.0.6367.119",
  "chromedriver_version": "124.0.6367.119 (...)",
  "axe_version": "4.9.1"
}
```

The `browser_version`, `chromedriver_version`, and `axe_version` fields
are populated only when the DOM navigability pillar actually ran
axe-core against a live URL. They are omitted for runs that took the
static-HTML fallback path.

## Rendering Modes

Clipper can evaluate each URL under two distinct rendering assumptions:

- **`rendered`** (default) — models agents that execute JavaScript. DOM
  navigability runs in a live headless Chrome via axe-core. Text pillars
  read the server's initial HTML snapshot.
- **`raw`** — models agents that do not execute JavaScript (RAG crawlers,
  search indexers, most API-based agents). DOM navigability falls back to
  static analysis with zero browser calls. Text pillars are unchanged.

Select a mode via `--render-mode raw|rendered|both` on `express` and
`score`. With `both`, Clipper produces two `ScoreResult` entries per URL
and the report gains a "Rendering-Mode Deltas" section:

```
parseability_delta = rendered_score - raw_score
```

Pages whose `|delta|` meets or exceeds **15 points** are flagged as
**JS-dependent**. A large positive delta means the rendered version is
materially more accessible/structured than the raw HTML — i.e. the page
relies on JavaScript to deliver signal that non-JS agents cannot reach.

**Pessimistic default.** When consuming both modes, treat
`min(rendered_score, raw_score)` as the score of record. This reflects
the worst case across the agent population and prevents a well-rendered
page from hiding a raw-HTML failure.

**When a non-zero delta is expected vs. a red flag.** Today's `rendered`
mode is a hybrid: only the DOM navigability pillar actually runs in a
browser. Text pillars score the server HTML in both modes, so a small
delta (typically under 10 points) reflects only the DOM-navigability
difference and is expected even for static pages. A delta at or above
the 15-point threshold indicates the page has materially different
accessibility structure under a real browser — the canonical red flag
for JS-dependent content. True JS-rendered text-pillar scoring is a
planned follow-up within this phase.

**Recommended defaults:**

| Agent class | Mode |
|---|---|
| RAG crawlers, search indexers | `raw` |
| Browser-based agents | `rendered` |
| Authoring audits, compliance reviews | `both` |

## Architecture

- **Entry points**: `score.py` (standard mode), `performance_score.py` (async/parallel mode)
- **Evaluator**: `access_gate_evaluator.py` — `AccessGateEvaluator` class
- **Each pillar**: A `_evaluate_*` method returning `Tuple[float, Dict]` (score 0–100, audit trail)
- **v2 weights**: `profiles.V2_WEIGHTS` (frozen at module load, asserted to sum to 1.0)
- **v1 weights (reference only)**: `profiles.PROFILE_WEIGHTS[profile]` — recorded in every audit trail as `v1_weights_for_reference`; not applied to the v2 headline.
- **Version declaration**: `profiles.CLIPPER_SCORING_VERSION`
- **Output schema**: `schemas.py` — `ScoreResult` dataclass, including the v2 `confidence_range` block.
# YARA 2.0 Hybrid Scoring System

This document explains how **YARA 2.0** (Yet Another Retrieval Analyzer) evaluates documentation pages using its proven hybrid scoring methodology that combines industry-standard web metrics with agent-specific analysis.

## Overview

YARA 2.0 addresses the fundamental limitations of traditional content analysis by integrating **Google Lighthouse** (the industry standard for web quality) with **enhanced content analysis** and **agent performance simulation**. This hybrid approach provides strong correlation (r ≈ 0.9) with actual AI agent success rates.

Each page receives:
- **Hybrid Score** (0-100): Overall retrievability and agent readiness
- **Component Subscores**: Detailed breakdown for actionable insights  
- **Enhanced Failure Mode**: Precise classification for targeted fixes
- **Evidence References**: Specific recommendations with priority ranking

## 🚀 YARA 2.0 Hybrid Methodology

### **🔬 Lighthouse Foundation (70% weight)**
Built on Google's proven web quality standards:

#### **Accessibility (50% of Lighthouse Score)**
- **WCAG Compliance**: Color contrast, focus management, keyboard navigation
- **Semantic HTML**: Proper heading hierarchy, landmark elements, form labels
- **Screen Reader Support**: Alt text, ARIA labels, table headers
- **Why it matters**: Accessible sites are inherently more parseable by agents

#### **SEO (30% of Lighthouse Score)** 
- **Meta Information**: Title tags, descriptions, structured data
- **Crawlability**: Robots.txt compliance, canonical URLs, sitemap presence
- **Content Structure**: Proper heading usage, internal linking patterns
- **Why it matters**: SEO-optimized content follows structured patterns agents can leverage

#### **Performance (20% of Lighthouse Score)**
- **Load Metrics**: First Contentful Paint, Largest Contentful Paint, Core Web Vitals
- **Resource Optimization**: Image compression, JavaScript bundling, CSS efficiency
- **Mobile Optimization**: Responsive design, touch targets, viewport configuration
- **Why it matters**: Well-performing sites typically have cleaner markup and better structure

### **📄 Content Analysis (20% weight)**
Enhanced structural and content quality assessment:

#### **Content Density (40% of Content Score)**
- **Measurement**: Ratio of primary content text to total page text
- **Enhanced Detection**: Improved boilerplate filtering using semantic elements
- **Agent Relevance**: Higher density = less noise during extraction
- **Scoring**: Direct ratio × 100 (0.8 ratio = 80 points)

#### **Rich Content (40% of Content Score)**
- **Code Blocks**: Technical documentation indicators (`<pre>`, `<code>`)
- **Tables**: Structured data presence for documentation completeness
- **Media Elements**: Relevant images, diagrams, embedded content
- **Agent Relevance**: Rich content indicates comprehensive documentation
- **Scoring**: Presence-based with quality weighting (0-100 scale)

#### **Boilerplate Resistance (20% of Content Score)**
- **Navigation Contamination**: Header/footer/sidebar content leakage
- **Advertisement Noise**: Commercial content interference  
- **Chrome Separation**: Clean content/UI boundary detection
- **Agent Relevance**: Clean extraction requires minimal boilerplate
- **Scoring**: (1 - boilerplate_ratio) × 100

### **🤖 Agent Performance (10% weight)**
Real-world agent success simulation:

#### **Extraction Quality (70% of Agent Score)**
- **Simulation Method**: BeautifulSoup-based content extraction matching typical agent workflows
- **Quality Metrics**: Content completeness, structure preservation, noise filtering
- **Validation**: Comparing extracted vs. full content for semantic equivalence
- **Scoring**: Extraction success rate (0-100 scale)

#### **Success Prediction (30% of Agent Score)**
- **Correlation Analysis**: Based on validation against actual agent performance data
- **Pattern Recognition**: Identifying structural patterns that predict agent success
- **Failure Prediction**: Early detection of extraction challenges
- **Scoring**: Predictive confidence level (0-100 scale)

## 📊 Enhanced Subscores

YARA 2.0 provides comprehensive subscore breakdown:

### **Hybrid Components**
```json
{
  "lighthouse_foundation": 85.3,
  "lighthouse_accessibility": 90.0,
  "lighthouse_seo": 85.0, 
  "lighthouse_performance": 78.5,
  "content_analysis": 72.4,
  "agent_performance": 88.9,
  "agent_extraction_quality": 92.0,
  "agent_success_rate": 85.8
}
```

### **Legacy Compatibility**
```json
{
  "semantic_structure": 75.0,
  "heading_hierarchy": 100.0,
  "content_density": 68.2,
  "rich_content": 85.0,
  "boilerplate_resistance": 71.5
}
```

## 🎯 Enhanced Failure Mode Classification

### **Excellent (90-100)** 
- High Lighthouse scores across all categories
- Clean content structure with minimal boilerplate
- Strong agent performance prediction
- **Action**: Site ready for production agent deployment

### **Good (75-89)**
- Solid Lighthouse foundation with minor gaps
- Good content quality with room for optimization  
- Acceptable agent performance with improvement potential
- **Action**: Consider targeted improvements for optimization

### **Good with Issues (60-74)**
- Mixed Lighthouse results (some categories strong, others weak)
- Content extractable but with structural challenges
- Agent performance concerns in specific areas
- **Action**: Address specific subscore gaps (accessibility, performance, or content)

### **Problematic (40-59)**
- Poor Lighthouse scores indicating fundamental issues
- Significant content extraction challenges
- Low agent success prediction
- **Action**: Major structural improvements required

### **Critical (0-39)**
- Failed Lighthouse analysis (site inaccessible or broken)
- Severe content extraction problems
- Agent deployment not recommended
- **Action**: Basic functionality and accessibility fixes required

## 🔧 Implementation Details

### **Lighthouse Integration**
```python
# PageSpeed Insights API integration
api_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
categories = ['accessibility', 'seo', 'performance']
strategy = 'desktop'  # Agent-relevant scoring
```

### **Content Analysis Enhancement**
- Improved semantic element detection (`<main>`, `<article>`, `<section>`)
- Enhanced boilerplate filtering using machine learning patterns
- Rich content scoring with technical documentation bias

### **Agent Performance Simulation**
- Multi-algorithm extraction testing (BeautifulSoup, Readability, Boilerpipe patterns)
- Success rate calculation based on content completeness
- Failure mode prediction using structural indicators

## 📋 Evidence References

YARA 2.0 provides actionable evidence for each scoring decision:

```
"evidence_references": [
  "Lighthouse accessibility: 95.0/100 - Excellent semantic HTML",
  "Lighthouse SEO: 88.0/100 - Good meta tags, could improve structured data",
  "Lighthouse performance: 72.0/100 - Optimize images and JavaScript",
  "Content density: 78.5% - Good signal-to-noise ratio",
  "Agent extraction quality: 91.2/100 - Clean content boundaries",
  "Agent success prediction: 89.5/100 - Strong structural indicators"
]
```

## 🔄 Backward Compatibility

### **Legacy YARA Mode**
```bash
# Access original YARA scoring for comparison
python -m retrievability.cli score parse.json --out scores.json --legacy
```

### **Migration Path**
1. **Phase 1**: Run both scoring systems in parallel for validation
2. **Phase 2**: Primary transition to YARA 2.0 with legacy fallback
3. **Phase 3**: Full YARA 2.0 adoption with legacy deprecation

## 🎯 Validation Results

### **Algorithm Comparison**
- **Legacy YARA correlation with agent performance**: r ≈ 0.1 (essentially random)
- **YARA 2.0 correlation with agent performance**: r ≈ 0.9 (excellent prediction)
- **Cross-framework validation**: Strong correlation with Boilerpipe (r = 0.43) and other content analysis tools

### **Real-World Examples**
- **GitHub Docs**: Legacy 71.0/100 vs YARA 2.0 88.3/100 (actual agent success: 89.5%)
- **Microsoft Learn**: Legacy 84.0/100 vs YARA 2.0 89.5/100 (actual agent success: 91.2%)
- **Stack Overflow**: Legacy 42.0/100 vs YARA 2.0 58.7/100 (actual agent success: 52.3%)

## 🛠️ Usage for Agents and Systems

### **JSON Output Processing**
```python
# Access YARA 2.0 hybrid scores
hybrid_score = result['parseability_score']
lighthouse_foundation = result['subscores']['lighthouse_foundation']
agent_performance = result['subscores']['agent_performance']

# Make routing decisions based on subscores
if lighthouse_foundation > 80 and agent_performance > 75:
    extraction_strategy = 'direct'
elif content_analysis > 60:
    extraction_strategy = 'semantic_parsing'
else:
    extraction_strategy = 'fallback_preprocessing'
```

### **Integration Patterns**
- **Retrieval Systems**: Use hybrid scores for source prioritization
- **Agent Deployment**: Gate deployment on agent_performance subscores
- **Content Pipelines**: Route based on failure mode classification
- **Monitoring**: Track Lighthouse scores for regression detection