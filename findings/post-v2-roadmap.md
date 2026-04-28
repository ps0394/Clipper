# Clipper Post-v2 Roadmap

**Status:** Draft, April 27, 2026
**Author:** Phase 6 Session 6 close-out
**Supersedes:** the Block 5/6/7 sections of [v2-scoring-phase6-roadmap-prd.md](v2-scoring-phase6-roadmap-prd.md), which were written before cross-judge κ landed and before the served-markdown null finding.

---

## 1. Current Scoring Model — `v2-evidence-partial`

This section is the authoritative summary of what v2 scores and how. The implementation lives in [retrievability/access_gate_evaluator.py](../retrievability/access_gate_evaluator.py). The version string is declared in [retrievability/profiles.py](../retrievability/profiles.py) as `CLIPPER_SCORING_VERSION = 'v2-evidence-partial'`.

### 1.1 Headline composite

```
parseability_score = 0.50 × content_extractability + 0.50 × http_compliance
universal_score    = parseability_score   (equal by construction in v2)
```

The two contributing pillars are the only ones with a single-pillar Pearson r ≥ +0.24 against `accuracy_rendered` on corpus-002 (n=43). The four other pillars are still computed and reported in `component_scores`, but multiplied by 0 in the headline. The v1 profile-weighted composite is preserved in `audit_trail._content_type.v1_weights_for_reference` for back-compat A/B work.

### 1.2 The six pillars — what each one measures and how

Every pillar produces a 0-100 sub-score and an audit-trail dict. The pillars run in parallel against a single rendered HTML snapshot per URL.

#### Content Extractability — 50% headline weight

- **Standard:** Mozilla Readability (the algorithm that powers Firefox Reader View).
- **Library:** [`readability-lxml`](https://pypi.org/project/readability-lxml/).
- **Implementation:** `_evaluate_content_extractability` ([retrievability/access_gate_evaluator.py](../retrievability/access_gate_evaluator.py)).
- **Sub-scores (sum to 100):**
  - **Signal-to-noise ratio (0-40)** — `len(extracted_text) / len(raw_page_text)`. Optimal range is 0.15-0.85; below 5% means Readability couldn't find content; above 85% means the page is mostly content (still good).
  - **Structure preservation (0-30)** — fraction of `<h1>`-`<h6>`, `<ul>`/`<ol>`, and `<pre>`/`<code>` elements that survive extraction (10 pts each). Pages with no original headings/lists/code get neutral credit (5/10 each).
  - **Boundary detection (0-30)** — does the algorithm produce a non-empty title (10), > 100 chars of content (10), and meaningful overlap between the extracted text and any `<main>`/`<article>` region in the source (10)?
- **corpus-002 single-pillar r:** **+0.484**.
- **Why it predicts retrieval:** if Readability can cleanly extract a page, an LLM agent using the same heuristics for chunking/summarization gets a clean input. Pages that fail Readability are typically chrome-heavy, dialog-heavy, or JS-rendered with low static signal.

#### HTTP Compliance — 50% headline weight

- **Standard:** RFC 7231 + robots.txt + cache-header semantics.
- **Library:** `httpx` (live HTTP) + `BeautifulSoup` (in-page declarations).
- **Implementation:** `_evaluate_http_compliance_enhanced` ([retrievability/access_gate_evaluator.py](../retrievability/access_gate_evaluator.py)).
- **Sub-scores (sum capped at 100):**
  - **HTML reachability (0-15)** — `GET <url>` with `Accept: text/html`. 200 → 15; 3xx → 11; other 2xx → 8; 4xx/5xx → 0.
  - **Redirect efficiency (0-25)** — measured from `crawl_data['redirect_chain']`. 0-1 hops = full credit; degrades with chain length and cross-origin hops.
  - **Crawl permissions (0-20)** — `<meta name="robots">` parsed for `noindex`/`nofollow` (12 pts permissive, 10 with nofollow, 0 with noindex), plus `robots.txt` allow/deny check for the page's path (+8 if allowed).
  - **Cache headers (0-20)** — `HEAD` request inspects `ETag` (+8), `Last-Modified` (+8), and `Cache-Control` (+4 unless `no-store`).
  - **Agent content hints (0 — diagnostic-only in v2)** — detects markdown alternates, `llms.txt` references, and `data-llm-hint` attributes. Recorded with `scoring_contribution: 0` and `diagnostic_only: true`. Phase 4.4 fix; explicitly does *not* contribute to the headline pending Phase 7 retrieval-mode evidence.
- **corpus-002 single-pillar r:** **+0.242**.
- **Why it predicts retrieval:** clean HTTP semantics correlate with reproducible fetches across agent runs. Pages with broken redirect chains, missing cache validators, or noindex-but-publicly-listed contradictions are operationally unreliable for an agent.

#### Semantic HTML — 0% headline weight (diagnostic-only)

- **Standard:** W3C HTML5 semantic elements + ARIA landmarks.
- **Library:** `BeautifulSoup` with `html5lib` parser.
- **Implementation:** `_evaluate_semantic_html` ([retrievability/access_gate_evaluator.py](../retrievability/access_gate_evaluator.py)).
- **Sub-scores (sum to 100):**
  - **Semantic coverage (0-60)** — fraction of HTML5 semantic elements present out of 11 candidates: `header`, `nav`, `main`, `article`, `section`, `aside`, `footer`, `figure`, `figcaption`, `time`, `mark`. Each element also gets a "proper usage" check (e.g., exactly one `<main>`, `<nav>` inside `<header>`, etc.).
  - **ARIA bonus (0-20)** — 5 pts per element with a `role=` attribute, capped at 20.
  - **Heading bonus (0-20)** — 2 pts per `<h1>`-`<h6>`, capped at 20.
- **corpus-002 single-pillar r:** **−0.301** (negative).
- **Why it's diagnostic-only:** the negative correlation indicates that pages with more "semantic markup" on corpus-002 tend to score *worse* on agent retrieval. Suspected mechanism: heavy semantic markup correlates with template-driven CMS pages that are chrome-dense rather than content-dense. The pillar still runs because semantic markup is a documented W3C standard worth measuring; it just doesn't earn headline points until corpus-003 gives a clean signal.

#### Structured Data — 0% headline weight (diagnostic-only)

- **Standard:** Schema.org (Google/Microsoft/Yahoo consortium).
- **Library:** [`extruct`](https://pypi.org/project/extruct/) — extracts JSON-LD, microdata, RDFa, Open Graph in one pass.
- **Implementation:** `_evaluate_structured_data` ([retrievability/access_gate_evaluator.py](../retrievability/access_gate_evaluator.py)).
- **Sub-scores (sum to 100):**
  - **Type appropriateness (0-20)** — does the declared `@type` match the detected content profile? `Article`/`TechArticle` for `article`, `FAQPage` for `faq`, `HowTo` for `tutorial`, `SoftwareSourceCode` for `sample`, etc.
  - **Field completeness (0-30)** — required fields per type are populated (e.g., `Article` requires `headline`, `author`, `datePublished`; `FAQPage` requires non-empty `mainEntity` of `Question`/`Answer` pairs). Phase 4.1 added per-type validation.
  - **Multiple formats bonus (0-20)** — pages declaring structured data in ≥ 2 formats (e.g., JSON-LD + microdata) earn full credit.
  - **Schema validation (0-30)** — basic shape validation: required properties present, expected value types, no obviously broken declarations.
- **corpus-002 single-pillar r:** **+0.036** (near-zero).
- **Why it's diagnostic-only:** the corpus-002 signal is too weak to authorize headline weight. Many high-accuracy pages have no structured data; many low-accuracy pages have rich JSON-LD. Either the metric is poorly calibrated to retrieval, or structured data is genuinely orthogonal to comprehension-mode accuracy. Phase 7 retrieval-mode benchmark is where this pillar most plausibly recovers signal (structured data should help retrieval where it doesn't help comprehension).

#### DOM Navigability — 0% headline weight (diagnostic-only)

- **Standard:** WCAG 2.1 AA via axe-core (Deque Systems).
- **Library:** [`axe-selenium-python`](https://pypi.org/project/axe-selenium-python/) injects axe-core JavaScript into a headless Chrome session and runs the standard rule set.
- **Implementation:** `_evaluate_wcag_accessibility` ([retrievability/access_gate_evaluator.py](../retrievability/access_gate_evaluator.py) line 364) with `_evaluate_static_accessibility` fallback when Selenium is unavailable.
- **Sub-scores:**
  - axe-core returns counts of violations, passes, incompletes, and inapplicables across ~90 WCAG rules. The score is a normalized function of `passes / (passes + violations)` weighted by rule severity (`critical` × 4, `serious` × 3, `moderate` × 2, `minor` × 1).
  - When the live browser path fails, the static fallback uses BeautifulSoup to count `aria-*` attributes, `<label>` associations, alt text on images, and tab-index hygiene.
- **corpus-002 single-pillar r:** **−0.189** (negative).
- **Why it's diagnostic-only:** strict WCAG compliance penalizes the rendered HTML differently than agents care about. axe-core flags missing alt text, low contrast, and aria-label gaps that an LLM doesn't experience. The negative correlation suggests pages with *more* WCAG violations are sometimes *easier* for LLMs (because they're plain HTML rather than complex SPA scaffolding). This pillar may need outright redefinition in v3.
- **Operational note:** WCAG evaluation requires Chrome and ChromeDriver. CI installs both via `copilot-setup-steps.yml`. Each WCAG run takes ~3-5 seconds per URL. The Phase 5 dual-fetcher captures separate `accuracy_raw` (no JS) and `accuracy_rendered` (Selenium-rendered) values; only `accuracy_rendered` is used as the v2 calibration target.

#### Metadata Completeness — 0% headline weight (diagnostic-only)

- **Standard:** Dublin Core + Schema.org + OpenGraph.
- **Library:** `BeautifulSoup` + JSON-LD parsing.
- **Implementation:** `_evaluate_metadata_completeness` ([retrievability/access_gate_evaluator.py](../retrievability/access_gate_evaluator.py) line 1258).
- **Sub-scores (sum to 100):** seven required fields, each worth 15 points (plus a 10-point language field):
  - **title (15)** — `<title>` element OR `<meta property="og:title">` OR Schema.org `name`/`headline`.
  - **description (15)** — `<meta name="description">` OR `<meta property="og:description">` OR Schema.org `description`.
  - **author (15)** — `<meta name="author">` OR Schema.org `author` OR `publisher`.
  - **date (15)** — `<meta name="*date*">` OR `<time datetime="…">` OR Schema.org `datePublished`/`dateModified`.
  - **topic (15)** — `<meta name="topic">` / `<meta name="category">` OR Schema.org `articleSection` OR `<meta name="keywords">`. **`ms.topic` is explicitly excluded** (Phase 4.4 commit `3c71ce2`, April 22 2026): it's a Microsoft Learn CMS template signal consumed by the classifier in `profiles.py`, not a semantic topic declaration. Accepting it here gave Learn a vendor-specific 15-point credit no other doc system could earn.
  - **language (10)** — `<html lang="…">` OR `<meta http-equiv="Content-Language">` OR Schema.org `inLanguage`.
  - **canonical (15)** — `<link rel="canonical">` href.
- **corpus-002 single-pillar r:** **+0.224** (just below the +0.24 ship threshold).
- **Why it's diagnostic-only:** corpus-002 r = +0.224 is a strong candidate to promote into the v3 headline if corpus-003 confirms it. It missed the v2 cut by 0.016. Several of these fields (canonical, date, language) plausibly do help agent retrieval; corpus-002 just wasn't large enough to separate that signal from noise above the ship gate.

### 1.3 Content-type profile detection (active, but not weighted in v2)

`detect_content_type()` ([retrievability/profiles.py](../retrievability/profiles.py)) classifies every page as one of `article` / `landing` / `reference` / `sample` / `faq` / `tutorial`. Detection still runs and the label is reported in `content_type.profile`, but profile-specific weight tables are inactive in v2 — every profile collapses to the same 50/50 composite.

The classifier consults signals in this order, stopping at the first hit:

1. **`<meta name="ms.topic">`** — authoritative on Microsoft Learn (`overview` → landing, `quickstart`/`tutorial` → tutorial, `reference`/`api-reference` → reference, etc.). Phase 4.4 made `ms.topic` *classifier-only*; it no longer earns metadata-pillar points.
2. **JSON-LD `@type`** — `FAQPage` → faq, `HowTo` → tutorial, `SoftwareSourceCode` → sample.
3. **URL path heuristics** — `/samples/`, `/api/`, `/reference/`, `/quickstart/`, `/faq/`, etc.
4. **DOM heuristics** — large `<dl>` lists → reference; dense `<Question>`/`<Answer>` pairs → faq.
5. **Default** — `article`.

The full detection trace (winning signal, matched value) is recorded in `audit_trail._content_type.detection`. Classifier output is locked against `tests/fixtures/classifier_corpus_golden.json`; CI's `tests/test_classifier_lockdown.py` fails the build on any drift.

### 1.4 Calibration evidence (corpus-002, n=43)

| Metric | Value | Source |
|---|---|---|
| v2 composite vs `accuracy_rendered` | **r = +0.6181** | [evaluation/phase5-results/corpus-002-analysis/v2-regression.json](../evaluation/phase5-results/corpus-002-analysis/v2-regression.json) |
| Llama-3.3-70B mean accuracy | 0.698 | Addendum D §D.4 |
| GPT-4o mean accuracy | 0.595 | Addendum G §G.1 |
| DeepSeek-V3.2 mean accuracy | 0.591 | Addendum G §G.1 |
| Pooled cross-judge κ | 0.706-0.817 | Addendum G §G.2 |
| Per-judge composite r (cross-judge robustness) | +0.440 / +0.497 / +0.618 | [evaluation/phase5-results/corpus-002-analysis/v2-gate-cross-judge.json](../evaluation/phase5-results/corpus-002-analysis/v2-gate-cross-judge.json) |
| Single-judge 90% CI on accuracy | [0.633, 0.758] | Addendum D §D.4 |
| Cross-judge union 90% CI on accuracy | [0.530, 0.758] | Addendum G §G.4 |
| Majority-vote 90% CI on accuracy | [0.567, 0.688] | Addendum G §G.4 |
| Ship gate (PRD F2.6) | r ≥ +0.35 — **passes under all three judges** | F3.5 / Addendum G §G.5 |

The `confidence_range` field on every `ScoreResult` carries: scoring version, evidence tier (`partial`), the `V2_WEIGHTS` dict, the calibration-corpus pointer, and the caveats listed in `retrievability/access_gate_evaluator.py` (single-corpus / four-pillar diagnostic-only / cross-judge variance / no temporal variance).

### 1.5 What v2 explicitly does not measure

- **Served markdown / `llms.txt`** — detected and recorded as agent content hints with `scoring_contribution: 0`. Phase 4.4 / F4.4 verdict: `keep_as_diagnostic_only` until Phase 7 retrieval-mode evidence is available. The conventional "markdown is more token-efficient" claim does not survive corpus-002 (median 1.4× more tokens than a Readability extract).
- **Fetch Integrity** — server `Accept` honour, redirect determinism under agent UAs, cache consistency across fetches. Scoped for v3 if corpus-003 produces signal.
- **Cross-agent variance** — `accuracy_rendered` is single-evaluator ground truth on corpus-002. Generalization to other agents/prompting modes/long-horizon tasks is open.
- **Profile-specific weighting** — collapsed in v2 by design. v1 weights are recorded in audit trails for back-compat and A/B work.

### 1.6 Five-second runbook

```bash
# Single URL, structured output
python main.py express --urls https://example.com --out results --quiet

# Multi-URL
python main.py express urls/clipper-demo-urls.txt --out results --name eval-name --quiet

# Outputs:
# results/<name>_scores.json — structured per-URL results (use parseability_score
#                              for same-content-type comparisons; use
#                              universal_score for cross-vendor or cross-corpus)
# results/<name>.md          — human-readable report
```

For cross-vendor, cross-corpus, or cross-content-type comparisons, **always use `universal_score`** and disclose the per-page profile, the detection source, and the cross-judge CI. Methodology rules in [.github/copilot-instructions.md](../.github/copilot-instructions.md) → *When Asked to Write a Comparison or Analysis Report*.

---

## 2. Problem Statement

Clipper's v2 scoring model ships under the tag `v2-evidence-partial` because the evidence base is a single corpus (corpus-002, n=43, curated). As of Phase 6 Session 6, four of the five validation axes that gate the `-evidence-partial` qualifier have been settled:

| Validation axis | Status | Evidence |
|---|---|---|
| 1. Single-corpus correlation | ✅ Settled | r = +0.618 (Llama-3.3-70B, corpus-002, F2.6) |
| 2. Cross-judge robustness | ✅ Settled | r = +0.44 to +0.62 across Llama / GPT-4o / DeepSeek-V3.2 (F3.2-F3.5, Addendum G) |
| 3. Format robustness (served markdown) | ✅ Settled | Null on comprehension; F4.4 verdict `keep_as_diagnostic_only` |
| 4. Temporal robustness | ⏸ Optional hygiene | Re-fetch + hash-compare; pipeline is offline-deterministic by design |
| 5. **Generalization beyond corpus-002** | ❌ **Open and blocking** | Untested |
| 6. Retrieval-mode validity (vs comprehension) | ❌ **Open, blocking for v3** | F4.4 explicitly deferred to "Phase 7" |

The two open axes (5 and 6) are external-validity questions that corpus-002 cannot answer architecturally — corpus-002 is curated, comprehension-mode-only, and capped at 43 pages. **No additional corpus-002 work will move them.**

The risk if we ship v2 unqualified now without closing axes 5 and 6:

- **Selection-bias risk.** The +0.618 correlation might be a property of corpus-002's curation (14 vendors × 5 profiles, hand-picked for diversity) rather than a property of the v2 model. A reviewer with access to a fresh URL set could disprove the headline.
- **Regime-validity risk.** v2 is validated on comprehension-mode QA — the LLM has the full page in its context. Real agent retrieval is RAG: chunk + embed + retrieve. v2 has no evidence in that regime; F4.4's null finding on served markdown does not generalize.

The risk if we keep grinding on corpus-002 polish (more judges, more temporal replications, more weight tuning):

- **Diminishing returns.** v2 ships 50/50 weights; there is no fractional-weight knob left to turn. Four of six pillars already carry 0% headline weight. Cross-judge robustness is settled across three model families. The remaining corpus-002 work surfaces second-order effects, not first-order ones.

This document defines the work that closes axes 5 and 6 and moves Clipper from `v2-evidence-partial` to a `v2` baseline plus a v3 design path.

---

## 3. Objective

Move the v2 scoring model from internally-validated to externally-validated by:

1. **Generalizing v2 beyond corpus-002** — a fresh corpus (corpus-003) with non-overlapping URLs and a methodologically pre-registered selection process.
2. **Establishing retrieval-mode validity** — a Phase 7 RAG benchmark on top of corpus-003 to test whether v2 predicts retrieval performance, not just comprehension.
3. **Designing v3 from those two new evidence bases** — pillar selection, weight tuning, and confidence ranges all calibrated against corpus-002 ∪ corpus-003 evidence in both retrieval and comprehension modes.

The end state is:

- v2 ships without the `-evidence-partial` suffix once corpus-003 generalization is confirmed.
- v3 ships once Phase 7 retrieval-mode evidence is in hand and the pillar architecture has been updated against it.
- The `keep_as_diagnostic_only` verdict on served markdown either survives the retrieval-mode test or gets explicitly reopened.

---

## 4. Acceptance Criteria

### Block A — Corpus-003 Generalization

- [ ] **A1.** Corpus-003 spec doc published with URL list under `evaluation/corpus-003/` *before* fetching, so selection is auditable.
- [ ] **A2.** Corpus-003 fetched (Tier 1 raw + Tier 2 rendered) and scored through the v2 pipeline. Tri-fetcher records served-markdown availability per page as diagnostic-only.
- [ ] **A3.** Cross-judge regression check: pooled per-judge mean **r ≥ +0.35** between v2 composite and `accuracy_rendered`, computed under at least 2 judges (Llama + one other). 3 judges if Foundry budget permits.
- [ ] **A4.** Cross-corpus stability table published: per-pillar r on corpus-002 vs corpus-003. Identifies any pillar whose correlation flips sign or drops > 0.20 between corpora.
- [ ] **A5.** If A3 passes, drop `-evidence-partial` from the release tag. If A3 fails, do not ship v3; diagnose first (which pillar, which vendor distribution, which profile).
- [ ] **A6.** *(Added April 28, 2026 after Session 9.)* If the Session 9 A3 failure is diagnosed as range-restriction in the dependent variable rather than a v2 generalization failure, run a Session 9.5 retry on a corpus engineered to produce wider accuracy variance, and reuse A3/A4 as the acceptance gate. A6 is satisfied when one of: (a) A3 passes on the variance-producing retry, (b) A3 fails on the retry and a v3-redesign sub-session is opened, or (c) A3 retry data shows v2 is uncorrelated with accuracy under any tested generator, in which case v2 is downgraded to a static-quality score with no comprehension claim and the roadmap fork to Block D bypasses Block C.

### Block B — Temporal Hygiene (Parallel, Lower Priority)

- [ ] **B1.** corpus-002 re-fetched at T+4 (Apr 27), T+14 (May 7), and T+30 (May 23) without any code changes. HTML hash compared per page.
- [ ] **B2.** Drift report published: per-vendor and per-page page-content stability over each window. Identifies pages with content drift vs pages where the score moved without content change.
- [ ] **B3.** If > 20% of pages show |Δuniversal_score| > 10 points without content changes, investigate before any v3 announcement.

### Block C — Phase 7 Retrieval-Mode Benchmark

- [ ] **C1.** Phase 7 design doc published: chunker config, embedder, retriever, top-k, grading protocol. Pre-registered before any runs.
- [ ] **C2.** `retrievability/phase7/` module mirrors the `phase5/` shape: generator, scorer, judge.
- [ ] **C3.** Phase 7 run against corpus-003 with the same Q/A pairs used in Block A, so paired comprehension ↔ retrieval comparison is possible.
- [ ] **C4.** Format question revisited: does served markdown lift accuracy in retrieval mode? If lift > +0.10 on ≥ 2 vendors → F4.4 reopens; markdown becomes a candidate v3 signal. If not → `keep_as_diagnostic_only` is now defended in both regimes.

### Block D — v3 Design

- [ ] **D1.** Pillar-selection note: which pillars carry retrieval-relevance evidence in *both* corpus-003 comprehension *and* Phase 7 retrieval, above an explicit threshold (proposal: r ≥ +0.20 in both regimes).
- [ ] **D2.** v3 weight table with weight ranges (not point values) calibrated against corpus-002 ∪ corpus-003 ∪ Phase 7. Profile-specific reweighting if and only if per-profile correlations differ by > 0.15.
- [ ] **D3.** v3 confidence ranges replace the coarse 50/50 v2 composite. Bootstrap CIs over corpora *and* judges *and* regimes — not just pages.
- [ ] **D4.** `docs/scoring.md` rewritten for v3. Migration guide from v2.
- [ ] **D5.** Optional: a Fetch Integrity pillar if challenged-fetch corpus-003 pages produce a separable signal.

---

## 5. Session-Level Breakdown

Sessions are dependency-ordered, not time-boxed. Entry and exit criteria below; do not start a session before its entry criteria pass.

### Session 7 — Corpus-003 Spec (F6.1)

- **Entry:** Phase 6 Session 6 closed (current state).
- **Work:**
  - Define corpus composition: 5 vendors × 5 profiles × 5 pages floor (n=125); 6 × 5 × 20 (n=600) stretch.
  - Vendor selection rule: ≤ 5 overlap with corpus-002. Document why each vendor is in.
  - Profile balance: equal cells if possible; otherwise per-profile floor of 5 pages.
  - Include challenged-fetch pages per F6.2 (Cloudflare-challenged, robots-blocked, UA-allowlisted) — these are what allow a Fetch Integrity pillar to be evaluated in v3.
  - Pre-register URL list in `evaluation/corpus-003/urls.txt` and the spec in `evaluation/corpus-003/spec.md` *before* fetching.
- **Exit:** spec doc and URL list committed; methodology reviewed.
- **Risk:** if URL list changes after fetching, all generalization claims become post-hoc and must be re-run.

### Session 8 — Corpus-003 Fetch & Score

- **Entry:** Session 7 spec + URL list locked.
- **Work:**
  - Run `python main.py phase5 run` against corpus-003 URLs.
  - Tri-fetcher logs served-markdown availability (diagnostic-only).
  - Generator produces 5 Q/A per page using the same prompt as corpus-002 for parity.
  - Primary judge (Llama-3.3-70B) grades all pages.
  - Run cross-judge rejudge on at least one additional judge (GPT-4o or DeepSeek-V3.2). 3-judge panel if Foundry budget permits.
- **Exit:** all per-page artifacts on disk under `evaluation/phase5-results/corpus-003/`.
- **Cost note:** at corpus-003 floor (n=125), expect roughly 3× the LLM cost of corpus-002 per pass. Budget accordingly.

### Session 9 — Corpus-003 Regression & Stability Analysis

- **Entry:** Session 8 grading complete.
- **Work:**
  - Run F2.6 regression check: v2 composite vs accuracy_rendered on corpus-003.
  - Run F3.5 cross-judge gate check: composite-vs-accuracy r per judge, all clear +0.35 ship gate.
  - Cross-corpus per-pillar stability table: which pillar correlations move > 0.20 between corpus-002 and corpus-003.
  - Identify any pillar whose correlation flips sign — that's a v3 design signal, possibly a v2 demotion.
- **Exit:** Block A acceptance criteria A3 and A4 either pass or fail.
  - **A3 passes** → strip `-evidence-partial`; release v2 as `v2`.
  - **A3 fails** → do not strip the suffix; open a diagnosis sub-session before continuing to Block C.
- **Outcome (Apr 28, 2026, commit `ba7d832`):** **A3 FAILED on all three judges** (Llama r=+0.10, GPT-4o r=-0.03, DeepSeek r=+0.06; all below the +0.35 ship gate). Diagnosis: range restriction in the dependent variable, not a v2 generalization failure. corpus-003 accuracy std collapsed to 0.10–0.15 (vs corpus-002 std 0.25) because (a) 99/271 pages dropped under `MIN_DOCUMENT_CHARS` were exactly the pages most likely to produce poor answers and (b) Mistral-Large-3 hits ~95% accuracy on extractable text regardless of page quality. v2 composite spread is essentially unchanged (std ~7.4 vs 7.8). Three-judge per-Q/A unanimity is 91.6% (783/855); judge fitness is not the issue. corpus-003 **neither confirms nor refutes** v2 generalization. Remediation deferred to Session 9.5 below. Full report: [evaluation/phase5-results/corpus-003-analysis/session-9-report.md](../evaluation/phase5-results/corpus-003-analysis/session-9-report.md).

### Session 9.5 — A3 Retry on a Variance-Producing Corpus (A6)

- **Entry:** Session 9 closed with A3 failure diagnosed as range restriction (current state).
- **Goal:** produce a regression dataset where `accuracy_rendered` has std ≥ 0.20 so the F2.6 gate is statistically meaningful.
- **Approach (Option A):** swap the Phase 5 **scorer primary** from gpt-4.1 to a weaker reader model (e.g. GPT-3.5-turbo, Llama-3.1-8B, or any sub-frontier comprehension model available in Foundry). The scorer primary is the model that *answers* the Q/A pairs given the page text — its accuracy is the dependent variable in the F2.6 regression. Reuse the existing 271 corpus-003 fetches and Mistral-Large-3 Q/A pairs on disk; rerun only the answering stage + 3-judge panel. The generator and the page text stay constant so we are testing only the comprehension-side spread, not Q/A quality.
- **Acceptance:** before computing the F2.6 gate, verify accuracy std ≥ 0.20 on at least one judge. If std stays under 0.20 even with a weaker generator, escalate to Option B (sparse-content corpus with relaxed `MIN_DOCUMENT_CHARS`) before declaring v2 untestable.
- **Work:**
  - Pick a weaker scorer-primary deployment available in Foundry; pre-register the choice.
  - Re-run the answering stage against existing corpus-003 fetches + Q/A pairs (new tooling: `phase5 rescore`).
  - Re-run the 3-judge panel against the new answers.
  - Re-run Session 9's regression and stability scripts ([scripts/phase8-session9-regression.py](../scripts/phase8-session9-regression.py), [scripts/phase8-session9-variance.py](../scripts/phase8-session9-variance.py)).
- **Exit:** A3 / A4 either pass or fail on the variance-producing dataset; A6 closes accordingly.

### Session 10 — Temporal Replication Pass (B1, B2, B3)

- **Entry:** can run in parallel with Sessions 8-9; no dependency.
- **Work:**
  - Re-fetch corpus-002 at T+4 (Apr 27), T+14 (May 7), T+30 (May 23). No code changes between runs.
  - Per-page rendered-HTML hash comparison.
  - Per-page score deltas, separated into "content changed" vs "score moved without content change."
  - If the latter exceeds 20% of pages, investigate.
- **Exit:** Drift report published. If clean, append a temporal-stability section to corpus-002 findings doc. If dirty, open a sub-session to diagnose.
- **Note:** no new judging required; this is HTML/score stability, not accuracy stability. Cheap.

### Session 11 — Phase 7 Design Doc (C1)

- **Entry:** Block A closed with A3 PASS (via Session 9 or Session 9.5).
- **Work:**
  - Pick chunker (proposal: `langchain.text_splitter.RecursiveCharacterTextSplitter`, chunk_size=1000, overlap=100).
  - Pick embedder (proposal: a single fixed embedding model, `text-embedding-3-small` or equivalent on Foundry).
  - Pick retriever: top-k=5, cosine similarity, no rerank in v1.
  - Pick grading protocol: same 3-judge panel as Block A, but on retrieved chunks instead of full pages.
  - Define metrics: answer accuracy given retrieved context; recall@k against ground-truth chunk.
  - Pre-register all hyperparameters in `findings/phase-7/00-design.md` *before* implementation.
- **Exit:** design doc committed and reviewed.

### Session 12 — Phase 7 Implementation (C2)

- **Entry:** Session 11 design committed.
- **Work:**
  - New module `retrievability/phase7/` mirrors the `phase5/` shape: generator, scorer, judge.
  - Reuses Foundry deployments from Phase 5/6.
  - New CLI subcommand `python main.py phase7 ...` with the same surface (run, rejudge, etc.).
  - Unit tests for chunker, retriever, and grading wiring.
- **Exit:** module passes 179+ tests; can run end-to-end on a 3-page smoke corpus.

### Session 13 — Phase 7 Run on Corpus-003 (C3, C4)

- **Entry:** Session 12 implementation green.
- **Work:**
  - Run Phase 7 against corpus-003 with the same Q/A pairs used in Block A.
  - Produce paired comprehension-mode and retrieval-mode accuracy per page.
  - Cross-format analysis: served-markdown lift in retrieval mode.
  - If lift > +0.10 on ≥ 2 vendors, F4.4 reopens; markdown becomes a v3 candidate signal. If not, the `keep_as_diagnostic_only` verdict is now defended in both regimes.
- **Exit:** Phase 7 findings doc published.

### Session 14 — v3 Pillar Architecture (D1, D2)

- **Entry:** Sessions 9 and 13 closed.
- **Work:**
  - Pillar selection rule: pillar carries weight in v3 if r ≥ +0.20 against accuracy in *both* corpus-003 comprehension and Phase 7 retrieval.
  - Build the v3 weight table with weight *ranges* (not point values), computed via bootstrap over corpora ∪ judges ∪ regimes.
  - If challenged-fetch pages in corpus-003 produce signal, propose a Fetch Integrity pillar.
  - Profile-specific reweighting only if per-profile correlations differ by > 0.15.
- **Exit:** v3 weight table + pillar selection note committed.

### Session 15 — v3 Confidence Ranges + Doc (D3, D4)

- **Entry:** Session 14 closed.
- **Work:**
  - Replace the coarse 50/50 v2 composite with calibrated v3 weights per Session 14.
  - `ScoreResult.confidence_range` populated from real bootstrap intervals.
  - Rewrite `docs/scoring.md` for v3. Migration guide from v2 included.
  - Tag release as `v3`.
- **Exit:** v3 ships.

---

## 6. Sequencing Diagram

```
Now ────► Session 7 (corpus-003 spec)
            │
            ├──► Session 10 (temporal, parallel)
            │
            ▼
         Session 8 (fetch + grade)
            │
            ▼
         Session 9 (regression + stability)
            │
            ▼  [A3 fails → Session 9.5; A3 passes → skip 9.5]
            │
         Session 9.5 (A3 retry on variance-producing corpus)
            │
            ▼  [A3 passes → strip -evidence-partial]
            │
            ▼
         Session 11 (Phase 7 design)
            │
            ▼
         Session 12 (Phase 7 impl)
            │
            ▼
         Session 13 (Phase 7 run on corpus-003)
            │
            ▼
         Session 14 (v3 pillar arch)
            │
            ▼
         Session 15 (v3 ship)
```

---

## 7. What This Roadmap Explicitly Does Not Do

- **No more corpus-002 polish.** Per-vendor cross-judge CIs, second-order κ analyses, additional judges beyond the existing 3 — all rounding error. Corpus-002 is closed evidence.
- **No 4th judge on corpus-002.** The Llama / GPT-4o / DeepSeek panel already represents three model families and three severity calibrations. A 4th would reduce the per-judge CI by ~0.02.
- **No new pillars on corpus-002 alone.** Any v3 pillar promotion must be evidenced in corpus-003 + Phase 7. corpus-002 is the existence case, not the generalization case.
- **No `parseability_score` revival in v3.** Profile-weighted scoring stays collapsed until per-profile corpora are large enough to defend per-profile weights — which corpus-003 alone may not achieve. That's a v4 question.
- **No agent-customization scoring (e.g. custom user-agent allowlist credit) until corpus-003 has challenged-fetch pages and Phase 7 measures their retrieval impact.**

---

## 8. Decision Points Worth Flagging Now

These are choices that should be made deliberately, not by default:

- **Corpus-003 size.** 125-floor vs 600-stretch is a 4-5× cost decision. Recommendation: 125 if Foundry budget is the constraint; 250 if it's not.
- **Vendor overlap with corpus-002.** ≤ 5 overlapping vendors keeps the generalization claim clean but limits per-vendor stability analysis. ≥ 8 lets us build per-vendor cross-corpus CIs at the cost of weakening "fresh" claims. Recommendation: 5.
- **Phase 7 chunker choice.** The chunker is the single biggest free parameter in the retrieval-mode benchmark. Pre-registering one config closes design freedom; running an A/B opens it back up. Recommendation: pre-register one config, document the assumption, defer A/B to v4.
- **3-judge panel on corpus-003.** Triples the LLM cost of grading. Recommendation: run only Llama on the first pass, add GPT-4o on the second pass once the regression has passed; defer DeepSeek unless cross-judge variance specifically becomes a story.

---

## 9. Cross-References

- v2 specification and weight table: [`docs/scoring.md`](../docs/scoring.md)
- v2 calibration evidence: [`findings/phase-5-corpus-002-findings.md`](phase-5-corpus-002-findings.md)
- v2 cross-judge evidence (latest): [`findings/phase-5-corpus-002-findings.md`](phase-5-corpus-002-findings.md) Addendum G
- v2 ship gate (cross-judge): [`evaluation/phase5-results/corpus-002-analysis/v2-gate-cross-judge.json`](../evaluation/phase5-results/corpus-002-analysis/v2-gate-cross-judge.json)
- Original PRD this roadmap supersedes (Blocks 5+): [`findings/v2-scoring-phase6-roadmap-prd.md`](v2-scoring-phase6-roadmap-prd.md)
- Phase 5 topical findings index: [`findings/phase-5/README.md`](phase-5/README.md)

---

## 10. External Literature Anchors

This roadmap was originally written from internal Clipper evidence only. The following external sources were verified during Session 9.5 (April 28, 2026) by direct fetch of each URL — abstract, authors, and headline numbers were confirmed before citation. They are the defensible reference set for any Clipper-next ("post-v3") direction discussion. **Practitioner sources not on this list (Ahrefs/BrightEdge/SimilarWeb/iPullRank/etc.) were considered but not included because they could not be confirmed against a stable URL with verified findings.**

### 10.1 Verified citation set

| Ref | Source | URL | Relevance to Clipper |
|-----|--------|-----|----------------------|
| L1 | Liu et al. 2023 — *Lost in the Middle: How Language Models Use Long Contexts* (TACL) | https://arxiv.org/abs/2307.03172 | LM attention degrades for relevant info in middle of long contexts. Implies page-level scoring is the wrong unit; the first ~N tokens dominate what gets used. |
| L2 | Aggarwal et al. 2024 — *GEO: Generative Engine Optimization* (KDD) | https://arxiv.org/abs/2311.09735 | Introduces GEO-bench and demonstrates content-side interventions can boost generative-engine visibility by up to **40%**. Domain-specific. Frames AI-citation-share as a tractable, manipulable DV. |
| L3 | Liu, Zhang, Liang 2023 — *Evaluating Verifiability in Generative Search Engines* (EMNLP Findings) | https://arxiv.org/abs/2304.09848 | Across Bing Chat / NeevaAI / Perplexity / YouChat: only **51.5%** of generated sentences are fully supported by their citations; only **74.5%** of citations support their associated sentence. Establishes the noise floor for any "AI citation" outcome variable. |
| L4 | Bevendorff, Wiegmann, Potthast, Stein 2024 — *Is Google Getting Worse? A Longitudinal Investigation of SEO Spam in Search Engines* (ECIR) | https://downloads.webis.de/publications/papers/bevendorff_2024a.pdf · https://dl.acm.org/doi/10.1007/978-3-031-56063-7_4 | One-year longitudinal monitoring of Google/Bing/DuckDuckGo on 7,392 product-review queries against ClueWeb22 baseline. SEO-optimized affiliate content over-represented in all three engines. Cautions that any "structure correlates with retrieval" result must be separated from "structure correlates with SEO optimization." |
| L5 | Thakur et al. 2021 — *BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models* (NeurIPS Datasets & Benchmarks) | https://arxiv.org/abs/2104.08663 | 18 datasets, 10 retrieval architectures. Headline finding: **BM25 is a robust zero-shot baseline**; dense retrievers often underperform out-of-distribution. Important sanity check before Clipper-next adopts dense retrieval as default. |
| L6 | Bajaj et al. 2016/2018 — *MS MARCO: A Human Generated MAchine Reading COmprehension Dataset* | https://arxiv.org/abs/1611.09268 | Foundational passage-level QA dataset (1M+ Bing queries, 8.8M passages, 3.5M docs). Reference template for any passage-granularity retrieval benchmark Clipper-next builds. |
| L7 | Petroni et al. 2021 — *KILT: a Benchmark for Knowledge Intensive Language Tasks* (NAACL) | https://arxiv.org/abs/2009.02252 | Wikipedia-grounded benchmark that explicitly evaluates **provenance** (does the model point to the supporting span). Methodological template for a Track-B "groundedness" diagnostic. |
| L8 | Liang et al. 2023 — *Holistic Evaluation of Language Models (HELM)* (TMLR) | https://arxiv.org/abs/2211.09110 | 7 metrics × 16 core scenarios × 30 models. Methodologically the closest existing template for what Clipper-next's evaluation harness should look like: multi-metric, no single composite, full prompt/completion logging. |
| P1 | Semrush 2026 — *How We Built a Content Optimization Tool for AI Search [Study]* | https://www.semrush.com/blog/content-optimization-ai-search-study/ | 11,882 prompts × 304k LLM-cited URLs vs 922k Google-ranked-but-not-cited URLs. Content-side correlations with AI citation: clarity/summarization +33%, E-E-A-T +31%, Q&A format +25%, section structure +23%, structured-data text signals +22%. Practitioner study, not peer-reviewed, but largest published sample on this DV. |

### 10.2 Implications already adopted by this roadmap

None of the above changes the v2 ship plan or the Phase 7 / corpus-003 design. The implications matter only for what comes *after* the corpus-003 retest is complete (i.e., post-v3 direction).

### 10.3 Implications to evaluate at the Session 9.5 / 11 decision point

If A3 still fails the r ≥ +0.35 ship gate after Session 9.5 (currently in flight: weak-scorer rescore on corpus-003), the literature above suggests the post-v3 redesign should consider:

1. **Outcome-variable reframe.** Reader-comprehension-accuracy (the corpus-002/003 DV) measures whether a model can answer questions given a page. The commercially relevant DV — and the one Semrush (P1) and GEO (L2) measure at scale — is **whether the page gets cited when an AI search system answers a relevant prompt**. These are different outcomes; Clipper has been measuring the harder, less-actionable one. Track A of any rewrite should consider citation-as-DV as the primary measurement, with comprehension as a secondary "quality of citation" diagnostic.
2. **Sub-page unit of analysis.** L1 ("Lost in the Middle") implies that scoring whole pages obscures the part of the page that actually drives retrieval. A first-N-tokens diagnostic and a per-section self-containedness diagnostic are both supported by L1 + L6 (MS MARCO passage granularity).
3. **Groundedness as a separate axis.** L3 quantifies how often production generative search engines fail at attribution (~50% sentence support, ~75% citation support). L7 (KILT) provides the methodological template for measuring provenance directly. Worth a Track-B diagnostic.
4. **No single composite.** L8 (HELM) is the most credible existing precedent for evaluation harness design and explicitly argues against collapsing multiple desiderata into one number. v2's `parseability_score` already moved this way (50/50 of two pillars rather than 6-pillar weighted sum); Clipper-next should make the no-composite stance explicit.
5. **Confound with SEO optimization.** L4 (Webis) shows SEO-optimized content is over-represented in retrieval baselines beyond what its share of the web justifies. Any Clipper-next finding of the form "structured pages get cited more" must control for "structured pages also get SEO-optimized more" before being reported as a structure effect.
6. **GEO manipulability ceiling.** L2 demonstrates content-side interventions can move citation share by ~40% in published experiments. This is the ceiling Clipper-next's recommendations could plausibly target — and also the noise floor below which any observed structural effect is plausibly a GEO-style surface manipulation rather than a substance-of-content effect.

These six points are **inputs for the Session 11 decision**, not commitments. They will be revisited if A3 passes (in which case v2-evidence-partial holds and Clipper-next is deferred) or restated as a rewrite spec if A3 fails again.
