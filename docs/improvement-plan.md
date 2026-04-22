# Clipper Improvement Plan

**Source:** [`evaluation/clipper-improvement-issues.md`](../evaluation/clipper-improvement-issues.md) (original proposal), plus the engineering audit in [`docs/engineering-audit.md`](engineering-audit.md).

**Purpose:** Sequenced execution plan for the next phase of Clipper work. Each phase has a clear exit criterion and is sized to land as one PR (or a small cluster of related PRs).

**Principle:** Every phase must leave the tool in a shippable state. No multi-PR branches that only work at the end.

**Effort unit:** Estimates below are given in **sessions** — one session being roughly an hour or two of focused Copilot-assisted work that produces a landed PR or a committed deliverable. This is the honest unit for how this work is being executed; conventional sprint sizing is not applicable.

---

## Sequencing rationale

The original issues list is good but mis-sequenced. The ordering here reflects the re-prioritization from the issues review:

1. **Foundation first.** Without tests and failure-mode transparency, every scoring change after this is a gamble.
2. **Model correctness before model tuning.** Content-type profiles (#3) fix a category error; extractability previews (#4) refine a number. The category error comes first.
3. **Usability with scale.** Template consistency (#6) transforms the report from unreadable to useful, which matters as the corpus grows.
4. **Agent-model alignment.** The no-JS dimension (#1+#2 merged) fixes the biggest real-world accuracy gap, but only after the model itself is sensible.
5. **Refinement and future-proofing.** JSON-LD validation, Azure migration stubs, LLM ground-truth.
6. **Rejected.** Competitive auto-discovery (#7) is not scoped in.

---

## Phase 0 — Foundation (prerequisite for everything else)

### 0.1 Pillar fixture test suite

**Status:** Completed (commit `52188e4`, 2026-04-21).

**Why:** Zero tests exist today. Every scoring change is shipped blind. This phase is non-negotiable before any scoring work.

**Scope:**
- Create `tests/` directory with `pytest` wired up.
- Commit 6–10 tiny HTML fixture files under `tests/fixtures/`, one per pillar's success and failure shapes:
  - `semantic_html_good.html`, `semantic_html_bad.html`
  - `structured_data_complete.html`, `structured_data_missing.html`
  - `metadata_full.html`, `metadata_empty.html`
  - `agent_hints_markdown.html`, `agent_hints_none.html`
  - `robots_noindex.html`
  - `readability_clean.html`, `readability_chrome_heavy.html`
- Write `test_pillars.py` asserting expected score ranges for each fixture (ranges, not exact values — scoring is continuous).
- Add `pytest` as a real dev dependency and document `pytest` in the contributor section.
- Add a CI workflow step that runs the tests.

**Exit criterion:** `pytest` passes locally and in CI. One failing assertion on a deliberate scoring break confirms tests actually catch regressions.

**Docs updates:** `README.md` contributor section gains a "Running tests" subsection (`pip install -r requirements-dev.txt`, `pytest`). `docs/` gets a short `testing.md` describing the fixture layout and how to add a new pillar fixture.

**Est. effort:** 1 session.

---

### 0.2 Failure-mode transparency

**Status:** Completed (commit `5aaab14`, 2026-04-21).

**Why:** Network timeouts (Stripe, Google redirect chains) currently score a URL as 0 on affected pillars. That 0 is indistinguishable from "the site is actually bad." Every downstream aggregation (average, trend, comparison) is skewed.

**Scope:**
- Extend `ScoreResult` with a `partial_evaluation: bool` field and a `failed_pillars: List[str]` field.
- In each pillar evaluator, distinguish three outcomes explicitly:
  - **Scored successfully** → numeric score, no partial flag.
  - **Scored with fallback** (e.g. static accessibility analysis because browser failed) → numeric score, note in audit trail.
  - **Could not evaluate** (network failure, timeout, parse error) → `None` score, pillar added to `failed_pillars`, `partial_evaluation=True`.
- Update the final-score calculation: exclude failed pillars and renormalize weights over the surviving ones, rather than treating the failure as a 0.
- Mark partial evaluations distinctly in the CLI summary (`[PARTIAL]` tag).

**Exit criterion:** A forced network failure on one pillar produces a score that reflects only the successful pillars, with the failure clearly surfaced.

**Docs updates:** `docs/scoring.md` gains a "Partial evaluations" section explaining the three outcomes (scored / fallback / could-not-evaluate), how weight renormalization works, and what the `[PARTIAL]` CLI tag means. `retrievability/schemas.py` docstrings updated for the new `partial_evaluation` and `failed_pillars` fields. `README.md` scoring summary notes that failed pillars are excluded, not zeroed.

**Est. effort:** 1–2 sessions.

---

### 0.3 Evaluator reproducibility

**Status:** Completed (landed with 0.2 in commit `5aaab14`, 2026-04-21).

**Why:** Chrome and axe-core silently version-drift between runs. Two evaluations of the same page can produce different scores, and there is no way to tell whether the page changed or the tooling did.

**Scope:**
- In every evaluation, capture:
  - Chrome / Chromium version (`driver.capabilities['browserVersion']`)
  - ChromeDriver version
  - axe-core version (`axe.run(...).testEngine.version` if available)
  - Clipper version (from `setup.py`)
- Persist under `ScoreResult.audit_trail['_environment']`.

**Exit criterion:** Every `*_scores.json` includes environment metadata. No scoring logic change.

**Docs updates:** `docs/scoring.md` documents the `audit_trail._environment` block and why it matters for comparing scores across runs. `README.md` output-format section lists the environment fields.

**Est. effort:** Folds into the 0.2 session.

---

## Phase 1 — Model correctness

### 1.1 Content-type-aware scoring profiles (original Issue #3)

**Status:** Completed (commit `7faf198`, 2026-04-22).

**Why:** This is the single biggest accuracy improvement available. Today, Clipper applies a prose-biased rubric uniformly to tutorials, landing pages, API references, and sample catalogs, producing systematic false negatives on non-prose content.

**Scope:**

1. **Detection layer** in `parse.py`:
   - Primary: `<meta name="ms.topic">` if present.
   - Schema.org `@type` from JSON-LD.
   - URL heuristics: `/api/`, `/reference/`, `/tutorial`, `/overview`, `/faq`, `/samples`, `/quickstart`.
   - DOM heuristics (fallback): heading density, code-block ratio, link-to-text ratio.
   - Default: `article` (matches current behavior, preserves backward compatibility).

2. **Profile definitions** — weight overrides only, not wholesale pillar swaps:

   | Profile | Semantic HTML | Extractability | Structured Data | DOM Nav | Metadata | HTTP |
   |---|---|---|---|---|---|---|
   | `article` (default) | 25 | 20 | 20 | 15 | 10 | 10 |
   | `landing` | 25 | 10 | 30 | 15 | 10 | 10 |
   | `reference` | 30 | 10 | 20 | 15 | 15 | 10 |
   | `sample` | 20 | 25 | 20 | 10 | 15 | 10 |
   | `faq` | 25 | 15 | 30 | 15 | 5 | 10 |
   | `tutorial` | 25 | 25 | 15 | 15 | 10 | 10 |

3. **Output contract:**
   - `ScoreResult.content_type: str` (detected type).
   - `ScoreResult.parseability_score: float` (type-adjusted, primary).
   - `ScoreResult.universal_score: float` (current weights, for backward compatibility and comparison).

**Exit criterion:** Running against a known landing page (Storage Samples) produces a meaningfully higher `parseability_score` than `universal_score`, and the type is detected correctly. Tutorial pages unchanged vs. today.

**Docs updates:** `docs/scoring.md` gets a new "Content-type profiles" section with the full weight table, detection rules (including precedence: `ms.topic` > JSON-LD `@type` > URL heuristics > DOM fallback), and an explanation of `parseability_score` vs. `universal_score`. `README.md` updated so the headline scoring description mentions type-adjusted scoring as the primary number. `USER-INSTRUCTIONS.md` gains a "How the score is chosen for a page" walkthrough.

**Dependencies:** Phase 0.1 (need pillar tests before messing with weights).

**Est. effort:** 2–3 sessions (detection, profiles, calibration against real URLs).

---

### 1.2 Extraction preview (original Issue #4)

**Status:** Completed (commit `a408f51`, 2026-04-22).

**Why:** Extractability scores are opaque in isolation. A 33/100 makes instant sense when you see the three sentences that were extracted.

**Scope:**
- In `_evaluate_content_extractability`, persist:
  - First ~300 characters of the extracted text → `audit_trail.content_extractability.extracted_preview`.
  - Total extracted character count → `audit_trail.content_extractability.extracted_chars`.
- Optional secondary output: write the full extracted text to `<snapshot>_extracted.txt` alongside the HTML snapshot. Feature-flag this since it doubles snapshot storage.
- Update the markdown report template to surface the preview per URL.

**Exit criterion:** The generated markdown report shows an "Extracted preview" block under each URL's extractability score.

**Docs updates:** `docs/scoring.md` extractability section notes that a text preview is now persisted and surfaced in the report. If the full-text snapshot feature flag is added, document the flag and its storage implications in `USER-INSTRUCTIONS.md`.

**Est. effort:** 1 session.

---

## Phase 2 — Report usability at scale

### 2.1 Template consistency analysis (original Issue #6)

**Status:** Completed (commit `b1a7f89`, 2026-04-22).

**Why:** On Learn-scale evaluations (15+ URLs), per-page findings drown the report. Clustering identical sub-scores turns 96 findings into ~6 template issues plus 10 content issues. This is a report-level change, not a scoring change.

**Scope:**

1. **Cluster detection** in `report.py`:
   - Group URLs by identical (or near-identical, within ~1 pt) per-pillar score tuples.
   - Require ≥3 URLs in a cluster to be called "template-level."
   - Record cluster membership in the report data model.

2. **Report restructuring:**
   - New top section: "Template findings" — one entry per cluster, showing the shared issue and the list of affected URLs.
   - Existing per-page section becomes "Page-specific findings," filtered to issues *not* in any template cluster.
   - Include estimated impact: "Fixing this template lifts N pages by ~X points."

3. **No change to `ScoreResult`.** This is purely a report-generation layer change.

**Exit criterion:** A Learn evaluation of 16 URLs produces a report where the top section lists template issues by count, and per-page findings only show page-specific variation.

**Docs updates:** `USER-INSTRUCTIONS.md` "Reading a report" section gains a description of the Template findings vs. Page-specific findings split, with a short example. No schema change, so `schemas.py` docs are untouched.

**Est. effort:** 1–2 sessions.

---

## Phase 3 — Agent-model alignment

### 3.1 Rendering-mode dimension (merged Issues #1 + #2)

**Status:** Completed (commit `f80b749`, 2026-04-22).

**Implementation notes:**

- `ScoreResult` gained a `render_mode: 'raw' | 'rendered'` field (default `'rendered'`). Evaluator signatures (`AccessGateEvaluator.evaluate_access_gate`, `PerformanceEvaluator.evaluate_access_gate_async`, `score_parse_results_fast`) accept `render_mode`; invalid values raise `ValueError`.
- CLI gained `--render-mode raw|rendered|both` on both `express` and `score`. `both` produces two `ScoreResult` entries per URL.
- `raw` mode forces the DOM Navigability pillar through static analysis (no browser, no axe). All other pillars run unchanged — they already operate on the raw server HTML snapshot.
- Report gains a "Rendering-Mode Deltas" section (only when `render_mode='both'`) with a per-URL table, `[FLAG]` suffix when `|delta| >= 15`, and a per-page "Rendering Delta" line in the individual findings.
- **Scoping decision documented in `docs/scoring.md`:** today's "rendered" mode is a hybrid — dom_navigability runs in a live browser (axe-core), text pillars score the server HTML. True JS-rendered text-pillar scoring is a follow-up. Static pages therefore show a small delta even when JS doesn't materially change text content; a large delta (≥15) is still a strong signal of JS-dependence.

**Why:** Majority of agents (RAG crawlers, search indexers, API-based agents) don't render JavaScript. Clipper systematically overstates these pages' quality today. This is the biggest real-world accuracy gap.

**Scope:**

1. **Treat rendering mode as an evaluation dimension**, not two separate reports:
   - `RenderMode = Literal['rendered', 'raw']`
   - Every evaluation produces `ScoreResult` tagged with `render_mode`.
   - Default run produces both (two `ScoreResult` entries per URL), configurable via `--render-mode rendered|raw|both`.

2. **Raw-fetch implementation:**
   - Use `httpx` (already a dep) with no browser, no axe.
   - DOM Navigability pillar degrades gracefully in raw mode: static analysis only (axe-core requires a browser).
   - All other pillars work unchanged on raw HTML.

3. **Delta reporting:**
   - `parseability_delta = rendered_score - raw_score` surfaced in the report.
   - Flag URLs with delta > 15 points as "JS-dependent content."
   - Overall score defaults to `min(rendered, raw)` — the pessimistic view. Consumers can opt in to one or the other.

4. **Storage impact:** In the Azure migration, this doubles the write volume to Cosmos DB. Factor into the storage design but don't let it block this phase.

**Exit criterion:** A page with JS-heavy content (e.g. modern SPA docs site) shows a meaningful delta; a static HTML page shows ~0 delta. Report flags the gap.

**Docs updates:** `README.md` and `USER-INSTRUCTIONS.md` document the new `--render-mode rendered|raw|both` flag with recommended defaults for different agent classes (RAG crawlers → `raw`, browser-based agents → `rendered`, audits → `both`). `docs/scoring.md` gains a "Rendering modes" section explaining the pessimistic default (`min(rendered, raw)`), the `parseability_delta` metric, and when a large delta is expected vs. a red flag.

**Dependencies:** Phase 1.1 (content-type detection works identically for raw HTML). Phase 0.2 (raw fetch needs graceful failure for pillars it can't fully score).

**Est. effort:** 3–4 sessions. This phase is the sneaky one — "add a second score per URL" touches every pillar, adds a report axis, and doubles storage volume.

---

## Phase 4 — Refinement

### 4.1 JSON-LD field completeness (original Issue #5, scoped down)

**Status:** Completed (commit `c366d60`, 2026-04-22).

**Why:** Today structured_data awards points for presence, not quality. A JSON-LD block with just `@type: Article` scores the same as one with all required Article fields.

**Scope:**

1. Validate only the four `@type` values actually observed in the current corpora:
   - `Article`, `FAQPage`, `HowTo`, `BreadcrumbList`.

2. Field expectations (per type):
   - `Article`: required `headline`, `datePublished`; recommended `author`, `dateModified`, `description`, `publisher`.
   - `FAQPage`: required `mainEntity` (non-empty list of `Question`/`acceptedAnswer` pairs); completeness = detected FAQs / on-page question count.
   - `HowTo`: required `name`, `step` (non-empty); recommended `description`, `totalTime`.
   - `BreadcrumbList`: required `itemListElement` with ≥2 valid items.

3. Scoring:
   - Current structured_data point allocation unchanged.
   - Field Completeness sub-signal (30 pts) becomes: `min(30, 30 × (fields_present / fields_expected))`.
   - Invalid fields (e.g., empty `mainEntity`) logged in the audit trail.

**Exit criterion:** AKS FAQ's incomplete `FAQPage` now scores below a page with a complete one, with the audit trail explaining which fields are missing.

**Docs updates:** `docs/scoring.md` structured-data section gains per-type field expectation tables (Article / FAQPage / HowTo / BreadcrumbList) and the field-completeness formula. Clarify that only these four types are validated and that other `@type` values still count for presence but not completeness.

**Dependencies:** Phase 0.1 (needs a JSON-LD fixture per type).

**Est. effort:** 1 session.

---

### 4.2 Historical storage (original Issue #8, subsumed into Azure migration)

**Status:** Not started.

**Why:** Trend analysis has real value, but the proposed local SQLite store duplicates what Cosmos DB will provide and wastes migration effort.

**Scope:**

1. **Define the result contract now**, even before Azure exists:
   - Add `StorageBackend` protocol in a new `retrievability/storage.py`.
   - Default implementation: `LocalJSONStorage` (current behavior).
   - Stub implementation: `CosmosStorage` (raises `NotImplementedError` until Phase 5).

2. **Add `clipper history <url>` command** that reads from whichever backend is configured. If backend is JSON, walks `evaluation/*/` directories for historical score files matching the URL. If backend is Cosmos, queries by URL + time range.

3. **Do not build local SQLite.** The `LocalJSONStorage` + directory-walk path is enough for single-developer trend checking; real trending lives in Cosmos.

**Exit criterion:** `clipper history <url>` works against local JSON result files. The storage abstraction is in place for Phase 5 to drop in Azure implementations.

**Docs updates:** `README.md` and `USER-INSTRUCTIONS.md` document the new `history` command with examples. `docs/` gets a short `storage.md` describing the `StorageBackend` protocol so Phase 5 has a clear extension point.

**Est. effort:** 1 session.

---

## Phase 5 — Azure migration

**Status:** Not started.

See [`docs/engineering-audit.md`](engineering-audit.md) Section 5.4 for the full migration plan. At this point in the sequence, the prerequisites from that plan are already done:

- Test suite ✓ (Phase 0.1)
- Failure modes handled ✓ (Phase 0.2)
- Reproducibility captured ✓ (Phase 0.3)
- Storage abstraction ✓ (Phase 4.2)

The migration can proceed through Phases 1–6 of the audit plan without scoring-code changes.

**Docs updates:** A new `docs/deployment.md` covers the Azure architecture, service responsibilities (Container Apps, Cosmos DB, Blob Storage, Key Vault), environment variables, and operational runbook. `README.md` gains a "Running Clipper as a service" section pointing at the deployment doc. The `StorageBackend` documentation from Phase 4.2 is extended with the Cosmos implementation contract.

**Est. effort:** Not feasible through Copilot-assisted sessions alone. Requires an Azure subscription, infrastructure decisions, deployment pipelines, and live-system troubleshooting that sit outside this workflow. The code changes (Playwright swap, Cosmos/Blob backends, FastAPI wrapper, Dockerfile, OpenTelemetry instrumentation) can be authored here — call it ~8–12 sessions of code work — but the deployment, scaling tune, and hardening are human-driven.

---

## Phase 6 — Ground-truth validation

### 6.1 LLM extraction quality test (original Issue #9)

**Status:** Not started.

**Why:** Every other item in this plan is proxy measurement — structural signals that *should* correlate with agent retrievability. This is the only item that measures it directly. If the structural-to-LLM correlation turns out to be weak, the whole pillar-weight debate changes.

**Deliberately deferred to Phase 6** because:
- Requires an Azure OpenAI (or equivalent) deployment, cheapest after Phase 5.
- Requires at least one full scoring run with historical data to correlate against.
- Depends on Phase 0.1 tests to be confident scoring changes don't invalidate the LLM benchmark.

**Scope:**

1. `ScoreResult` gains an optional `llm_retrievability_score: Optional[float]` field. Default `None` until this phase ships.
2. New worker class `LLMRetrievabilityEvaluator`:
   - Sends the extracted text (from Phase 1.2) to a configured LLM with 2–3 standardized prompts per content type.
   - Grades responses automatically: ROUGE-L against the page, fact-overlap against extracted entities, hallucination rate (claims in response with no substring match in source).
3. Gated behind `--llm-validate` flag. Cost-conscious by default.
4. Correlation study: once enough data exists, report per-pillar correlation coefficients against the LLM score. This is the only way to empirically tune pillar weights.

**Exit criterion:** An LLM score is producible for any evaluated URL. A small correlation report validates (or doesn't) that the structural score predicts LLM performance.

**Docs updates:** `docs/scoring.md` gains a "LLM ground-truth validation" section covering the prompt set, grading metrics (ROUGE-L, fact-overlap, hallucination rate), and cost expectations. `README.md` documents the `--llm-validate` flag with a caveat that it requires LLM credentials. If the correlation study changes pillar weights, publish the findings as `docs/scoring-calibration.md` and link it from the scoring doc.

**Est. effort:** 2–3 sessions to scaffold the evaluator, prompts, and scoring metrics. The correlation study itself is a research activity, not a coding task — size it against available data, not sessions.

---

## What is explicitly not being done

### Rejected: Competitive auto-discovery (original Issue #7)

Clipper's value is measurement, not discovery. A search-API integration adds maintenance burden, external dependencies, approval-workflow UX, and a heuristic that will drift. The existing manual URL curation is not a real pain point. If competitive URL discovery is genuinely needed, it's a separate tool.

---

## Summary sequencing

| Phase | Item | Original issue | Priority | Sessions | Status |
|---|---|---|---|---|---|
| 0.1 | Pillar fixture test suite | — (audit) | P0 prerequisite | 1 | Completed (`52188e4`) |
| 0.2 | Failure-mode transparency | — (audit) | P0 prerequisite | 1–2 | Completed (`5aaab14`) |
| 0.3 | Evaluator reproducibility | — (audit) | P0 prerequisite | folded into 0.2 | Completed (`5aaab14`) |
| 1.1 | Content-type-aware profiles | #3 | P0 | 2–3 | Completed (`7faf198`) |
| 1.2 | Extraction preview | #4 | P1 | 1 | Completed |
| 2.1 | Template consistency | #6 | P0 | 1–2 | Completed |
| 3.1 | Rendering-mode dimension | #1 + #2 (merged) | P1 | 3–4 | Completed |
| 4.1 | JSON-LD field completeness | #5 | P2 | 1 | Completed |
| 4.2 | Storage abstraction | #8 (subsumed) | P2 | 1 | Not started |
| 5 | Azure migration | see audit | P2 | ~8–12 code sessions + human deployment work | Not started |
| 6.1 | LLM ground-truth | #9 | P2 (strategic) | 2–3 to scaffold; research time on top | Not started |
| — | Auto-discovery | #7 | Won't do | — | Rejected |

**Phases 0–4 total: roughly 13–18 sessions.** That's the executable portion through this workflow. Phases 5 and 6 have code components I can author but cannot fully complete without infrastructure access and research time outside the session model.

---

## Notes for future execution

- **Never ship a scoring change without a fixture test that exercises it.** This is the single rule that prevents this plan from producing another generation of drift.
- **Preserve the `universal_score`** through Phase 1 onward so existing consumers and historical comparisons don't break.
- **Azure migration (Phase 5) is a natural gate.** Everything before it should be doable in the CLI; everything from Phase 6 onward benefits from cloud resources. Don't attempt Phase 6 before Phase 5.
- **Each phase should land as a PR with a CHANGELOG entry.** The repo doesn't have a CHANGELOG today; Phase 0 or Phase 1 is a good moment to start one.
