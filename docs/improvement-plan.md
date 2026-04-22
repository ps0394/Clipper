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
5. **Refinement.** JSON-LD field completeness (#5), storage abstraction (#8), and classifier lockdown close remaining integrity gaps before anything empirical.
6. **Empirical validation.** LLM ground-truth (#9) is the only direct measurement in the plan — gated behind classifier lockdown so correlations are interpretable.
7. **Deployment** is deferred to last. Azure migration has no current consumer and no dependency blocking it from the empirical work.
8. **Rejected.** Competitive auto-discovery (#7) is not scoped in.

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

**Status:** Completed (commit `<pending>`, 2026-04-22) — scoped down from the original plan. See "Scope" below.

**Why:** Trend analysis has real value, but the original plan — a `StorageBackend` protocol, a `LocalJSONStorage` wrapper, a `CosmosStorage` stub that raises `NotImplementedError`, and a new `docs/storage.md` — builds scaffolding for a second backend (Cosmos) that may never land. YAGNI.

**Scope (delivered):**

1. A plain `retrievability/history.py` module with a `collect_history(url, root)` function that walks `<root>/**/*_scores.json`, filters entries by URL (with light normalization: trailing slash and fragment stripped), and returns rows sorted by score-file mtime.
2. A new `clipper history <url> [--root evaluation] [--json]` subcommand that prints a trend table (timestamp, corpus, profile, render mode, `parseability_score`, `universal_score`, delta vs. previous row) or JSON.
3. Seven hermetic unit tests in `tests/test_history.py` using `tmp_path` corpora — no dependency on the committed `evaluation/` output.

**Explicitly not delivered (deferred until a real second backend is needed):**

- No `StorageBackend` protocol / abstract class.
- No `CosmosStorage` stub.
- No `docs/storage.md`.

If/when Phase 6 (Azure migration) actually starts, the `history.collect_history()` function can be given a pluggable backend parameter at that time — when there's a second implementation to justify the abstraction.

**Exit criterion:** `clipper history <url>` returns a chronological trend table across all local `*_scores.json` files. Verified manually against the committed `evaluation/` corpus (6 evaluations of `learn-microsoft.com/en-us/azure/aks/faq` spanning 2026-04-16 to 2026-04-22).

**Docs updates:** `README.md` and `USER-INSTRUCTIONS.md` gain one-line examples of the history command. No separate `storage.md` — there is no abstraction to document.

**Est. effort:** 1 session (delivered in ~30 minutes, which is itself useful evidence that the original phase spec was over-scoped).

---

### 4.3 Content-type detector lockdown test

**Status:** Completed (commit `8868753`, 2026-04-22).

**Why:** The content-type classifier in `retrievability/profiles.py` silently shapes every headline score via `PROFILE_WEIGHTS`. A classification shift (article → landing, tutorial → reference) changes weights and therefore `parseability_score`. Today the classifier has zero test coverage against real corpora. That is the single largest hidden dependency in the scoring system and the most likely source of unexplained score drift between runs.

Phase 3.1's Profile Impact report surfaces the *effect* of a classification, but nothing asserts the *classification itself* is stable. This phase converts that silent dependency into an asserted contract.

**Scope:**

1. Build a golden classifications file from the existing multi-URL corpora:
   - Start with the `evaluation/learn-analysis-v3/` and `evaluation/competitive-analysis-v3/` snapshot directories (these have real captured HTML).
   - Script generates `tests/fixtures/classifier_corpus_golden.json` mapping each URL → detected `(profile, detection_source, matched_value)` tuple.
   - The golden file is hand-reviewed and committed. Mis-classifications discovered during review are fixed in `profiles.py` before the lock lands.

2. New test `tests/test_classifier_lockdown.py`:
   - For each URL in the golden file, parse the snapshot, run `detect_content_type`, assert the result matches the recorded `(profile, source)` pair.
   - Test is offline — reads from committed snapshots, no network calls.
   - Failures point at the exact URL + which signal (`ms_topic` / `schema_type` / `url` / `dom` / `default`) changed.

3. No classifier behavior changes in this phase unless review of the golden file reveals clear bugs. The purpose is to lock current behavior, not tune it.

**Exit criterion:** Running the classifier against the captured corpora produces the same profile assignments on every CI run. A behavior change in `profiles.py` causes a test failure that names the affected URL and signal.

**Docs updates:** `docs/scoring.md` content-type section gains a short note that detector behavior is locked by a corpus test, with a pointer to `tests/test_classifier_lockdown.py`. `docs/testing.md` documents the golden-file regeneration workflow (`pytest --update-classifier-golden` or equivalent) so corpus refreshes are deliberate and reviewed.

**Dependencies:** Phase 1.1 (the classifier and profile table must exist).

**Prerequisite for:** Phase 5 (LLM validation). Correlation analysis across structural pillars and LLM behavior is meaningless if the pillar weights themselves are moving under you. Lock the classifier first, then correlate.

**Est. effort:** 1 session — small amount of golden-file generation code, hand review, one test file.

---

### 4.4 Metadata pillar vendor-neutrality audit

**Status:** Completed (commit `3c71ce2`, 2026-04-22).

**Why:** During the Phase 4.3 review a reviewer question surfaced a narrower but real bias: `ms.topic` — a Microsoft-Learn-internal authoring signal used to drive the Learn CMS (template selection, breadcrumb, TOC grouping) — is currently accepted by the metadata pillar's "topic/category" field as equivalent evidence to `meta:keywords`, `meta:category`, `meta:topic`, and `schema:articleSection`. See [access_gate_evaluator.py:1334](../retrievability/access_gate_evaluator.py#L1334).

`ms.topic` is legitimately used inside the classifier (Phase 1.1) as an authoritative content-type declaration — that's what it is for. Using it a second time inside the metadata **scoring** pillar, on the claim that the page "declares a topic," is a category error: it's a page-role tag, not a semantic topic declaration. It's also asymmetric — no other doc system's equivalent frontmatter is recognized, so Learn pages can pick up the 15-point topic-field credit from a signal competitors don't have.

This phase is an audit-and-prune pass across every pillar evaluator, looking for any vendor-specific signal accepted alongside generic ones where the vendor signal isn't semantically equivalent to the generic signals in the same check.

**Scope:**

1. Audit every pillar evaluator for vendor-specific signals accepted alongside generic ones:
   - `retrievability/access_gate_evaluator.py` — all six pillar methods.
   - `retrievability/parse.py` — signal extraction (llms.txt is a proposed open standard, not vendor-specific; left in scope as a check).
   - `retrievability/score.py` — any additional signal consumption.

2. For each vendor signal found, classify it:
   - **Semantically equivalent to the generic check it's grouped with** → keep, document the equivalence claim.
   - **Not semantically equivalent** (different meaning, different role) → remove from that pillar's check.
   - **Legitimate use in a different pillar** (e.g., classification) → not in scope for this phase; already handled.

3. Confirmed targets (from the Phase 4.3 review):
   - Remove `ms.topic` from the metadata pillar's "topic/category" field check. Leave `meta:topic`, `meta:category`, `meta:keywords`, `schema:articleSection` — all generic semantic topic signals.

4. Probable additional targets (confirm during audit):
   - Any acceptance of `ms.date` / `ms.author` / Microsoft-specific meta tags alongside Dublin Core / Schema.org equivalents.
   - Any URL-path heuristic that treats a Microsoft-owned host specially.

5. New test(s) in `tests/test_pillars.py`:
   - A fixture with **only** `ms.topic` set (no `meta:keywords`, no `articleSection`, no `meta:category`) should score **zero** on the topic/category field after the change.
   - A fixture with `ms.topic` + `meta:keywords` should score the same as a fixture with only `meta:keywords` (no double-credit, no penalty).

6. Impact measurement:
   - Re-run `evaluation/learn-analysis-v3` and `evaluation/competitive-analysis-v3` before and after. Report the score delta on the headline metric per page.
   - Expected outcome: Learn scores move by ≤ ~2 points on the affected field (15 points × its pillar weight × its profile weight). If the delta is larger, that's itself evidence the signal was carrying too much weight.

**Exit criterion:** No vendor-specific signal is accepted as evidence inside a pillar scoring check unless the audit documents why it is semantically equivalent to the generic signals in the same check. The metadata pillar's topic/category field no longer references `ms.topic`. Re-running the evaluation corpora produces score deltas consistent with the expected impact (small, bounded).

**Docs updates:**
- `docs/scoring.md` metadata-pillar subsection gains a "Vendor-neutrality principle" note: signals used inside pillars must be semantically equivalent across vendors; vendor-specific overrides belong in the classifier (Phase 1.1), not in scoring pillars.
- `docs/testing.md` gains the new fixture's purpose in the adjacent pillar section.
- `docs/improvement-plan.md` row flipped to Completed.

**Dependencies:** Phase 4.3 (classifier locked — so that when a signal moves out of the metadata pillar and into the classifier's territory, we can verify the classifier didn't shift as a side effect).

**Prerequisite for:** Phase 5 — vendor-neutral pillar scoring is required before any LLM-correlation claim can be made across Learn vs. non-Learn corpora. Correlations computed on a pillar that silently favors one vendor are not interpretable.

**Non-goals:**
- Not removing `ms.topic` from the classifier. That use is legitimate.
- Not adding symmetric vendor recognition for Docusaurus / GitBook / Mintlify. That's a separate, larger piece of work and belongs in a future classifier-extension phase, not here.
- Not a full vendor-neutrality overhaul of every signal Clipper consumes. Scope is limited to vendor-specific signals accepted as evidence inside a pillar scoring check.

**Est. effort:** 1 session — small audit, one or two localized removals, two new fixture tests, corpora re-run for impact report.

---

## Phase 5 — LLM ground-truth validation

**Reordered note (2026-04-22):** This was previously Phase 6. Swapped with the Azure migration phase because (a) it has a real consumer — empirical weight calibration — while the migration does not yet, and (b) LLM validation only requires an inference endpoint, not a deployed service. The old "6 depends on 5" coupling was false.

### 5.1 LLM retrievability evaluator (original Issue #9)

**Status:** Not started.

**Why:** Every other item in this plan is proxy measurement — structural signals that *should* correlate with agent retrievability. This is the only item that measures it directly. If the structural-to-LLM correlation turns out to be weak, the whole pillar-weight debate changes. Correlation analysis, not composite scoring, is the deliverable; the LLM score is an instrument, not a verdict.

**Design principles (learned from the external proposal review):**

- LLM-as-judge is **not ground truth** — it's another heuristic wearing LLM clothing. Self-preference bias, verbosity bias, and run-to-run instability are all real. Mitigations are mandatory, not optional.
- Report **three axes separately** (grounding, completeness, unsupported-claim rate). Do not collapse them into a hand-picked weighted composite. Let correlation analysis decide whether a composite is justified.
- **Extractability and retrievability are different measurements.** Running the LLM on the full extracted text measures *can the model answer when given everything*. Running it on top-k lexical chunks measures *can the model answer like a RAG agent does*. The gap between them is the RAG tax. Report both.
- **Determinism is a gate, not a nice-to-have.** `temperature=0`, pinned model versions, `seed` parameter where supported. A 5-run variance check must land before any correlation conclusion is drawn.

**Scope:**

1. Schema:
   - `ScoreResult` gains `llm_retrievability: Optional[LLMRetrievabilityResult]` field, default `None` until this phase ships.
   - New `LLMRetrievabilityResult` dataclass with per-prompt rows (grounding, completeness, unsupported-claim rate, answer text, judge reasoning) plus aggregate means and a `run_variance` field from the stability check.

2. New module `retrievability/llm_retrievability_evaluator.py`:
   - Generates prompts from templated, content-type-specific sets (FAQ → "What is X?", tutorial → "How do I do X?", reference → "What does parameter X do?"). **No LLM-generated prompts** at this phase — templates only, to keep the prompt distribution constant across runs.
   - Runs two measurements per URL:
     - **Extractability path:** full extracted text → answer LLM → judge LLM.
     - **Retrievability path:** chunk the extracted text (fixed size, configurable overlap), lexical top-k retrieval against prompt, retrieved chunks → answer LLM → judge LLM.
   - Graders return JSON with the three axes, parsed strictly. Malformed judge output is logged and the prompt is retried once, then skipped with an explicit marker.

3. LLM client abstraction:
   - Single `LLMClient` class that wraps an OpenAI-compatible interface.
   - Config via env vars. Supports two backends day-one:
     - **GitHub Models** (`OPENAI_BASE_URL=https://models.github.ai/inference`, auth via GitHub PAT). Default for prototyping — zero infra setup, free at Copilot Enterprise tier.
     - **Azure OpenAI** (endpoint + key + deployment name). Recommended for reproducible/customer-facing runs.
   - **Recommended models:** `gpt-4o-mini` for answer generation, `gpt-4o` (or `gpt-4.1`) for the judge. Judge must be at least as strong as the generator to reduce self-preference bias. Mini-on-mini is cheaper but produces weaker grading signal; document the tradeoff.
   - `temperature=0`, fixed `seed`, max-tokens ceilings for both roles.

4. CLI:
   - New flag `--llm-validate` on `express` and `score`. Disabled by default.
   - Additional flags: `--llm-model-answer`, `--llm-model-judge`, `--llm-cost-ceiling <dollars>`. Abort with clear error if projected cost exceeds ceiling (unless `--confirm-cost` is passed).
   - Results caching keyed on `(url, content_hash, answer_model, judge_model, prompt_version)`. A rerun on unchanged content with unchanged models is free.

5. Human calibration checkpoint (**mandatory gate**):
   - Hand-grade 20–30 URLs spanning all six content-type profiles.
   - Judge LLM must achieve ≥80% agreement with human grading on each axis.
   - If agreement is below threshold: stop, adjust prompts or switch judge model, re-measure. No correlation claims may be published until this gate passes.
   - Calibration fixtures committed to `tests/fixtures/llm_calibration/` so the gate is re-runnable.

6. Variance / stability check:
   - Same URL, same config, 5 runs. Report standard deviation on each axis.
   - If `σ > 5 points` on any axis, the system is too noisy to calibrate structural weights against. Phase blocks on reducing variance (stricter prompts, lower max-tokens, smaller chunks) before correlation analysis begins.

7. Correlation analysis:
   - Specified up front: **Spearman rank correlation** per structural pillar against each LLM axis, per content-type profile.
   - Minimum sample size: **N ≥ 50 per content-type profile** before any correlation is reported in a published artifact. Below threshold, the script outputs the numbers with a clear `PROVISIONAL — N too small` banner.
   - Output: `docs/scoring-calibration.md` with the correlation tables. If findings contradict current pillar weights, the document also lists proposed weight changes; actual weight changes are deferred to a follow-up phase.

8. Report:
   - New "LLM Validation" section in markdown report when `--llm-validate` was used.
   - Per-URL: three axes for extractability path, three axes for retrievability path, the gap (extractability - retrievability = RAG tax).
   - Per-prompt diagnostics: question, answer, judge reasoning, score per axis.

**Constraints:**

- Cost-conscious by default. Projected cost per URL at default models: ~$0.01–0.02 with `gpt-4o-mini` answer + `gpt-4o` judge.
- 3 prompts per URL (content-type dependent templates).
- 2 LLM calls per prompt (answer + judge) × 2 paths (extractability + retrievability) = 4 calls per prompt = 12 calls per URL.
- Caching makes reruns free. First run of a 100-URL corpus is ~1200 calls.

**Exit criteria (all must pass):**

1. `clipper express <url> --llm-validate` produces an LLM result on any URL.
2. Human calibration gate passes (≥80% agreement on 20–30 hand-graded URLs).
3. Variance check passes (σ ≤ 5 on each axis across 5-run repeats).
4. Correlation report generated on a corpus with N ≥ 50 per content-type profile, published as `docs/scoring-calibration.md`.

**Docs updates:** `docs/scoring.md` gains an "LLM ground-truth validation" section covering the two-path methodology, the three axes, the calibration gate, and cost expectations. `README.md` documents `--llm-validate` + the credential requirement (GitHub PAT for GitHub Models OR Azure OpenAI credentials) and is explicit that structural scoring remains zero-API — LLM validation is an opt-in layer. `USER-INSTRUCTIONS.md` gets a "When to use `--llm-validate`" section.

**Dependencies:** Phase 1.2 (extracted text is the input), Phase 4.3 (classifier lockdown — correlations against moving weights are worthless).

**Est. effort:** 3–4 sessions to scaffold the evaluator, client abstraction, CLI flags, caching, and variance check. Calibration gate (hand-grading + iteration) is additional real-world time outside the session model. Correlation analysis itself is a research activity sized against available data, not sessions.

---

## Phase 6 — Azure migration

**Reordered note (2026-04-22):** This was previously Phase 5. Demoted to Phase 6 because it has no current consumer — no operator, no SLA, no customer asking to run Clipper as a service. It stays in the plan as a future deliverable, not a next-up.

**Status:** Not started.

See [`docs/engineering-audit.md`](engineering-audit.md) Section 5.4 for the full migration plan. At this point in the sequence, the prerequisites from that plan are:

- Test suite ✓ (Phase 0.1)
- Failure modes handled ✓ (Phase 0.2)
- Reproducibility captured ✓ (Phase 0.3)
- Storage abstraction — **scoped-down trend command delivered in Phase 4.2**; the `StorageBackend` protocol and `CosmosStorage` stub were deliberately *not* built. When this phase actually begins, introduce the protocol by generalizing `retrievability/history.collect_history()` and adding a Cosmos-backed implementation alongside the existing file-walk path.

The migration can proceed through Phases 1–6 of the audit plan without scoring-code changes.

**Docs updates:** A new `docs/deployment.md` covers the Azure architecture, service responsibilities (Container Apps, Cosmos DB, Blob Storage, Key Vault), environment variables, and operational runbook. `README.md` gains a "Running Clipper as a service" section pointing at the deployment doc. Storage contract is documented at that time alongside the Cosmos implementation.

**Est. effort:** Not feasible through Copilot-assisted sessions alone. Requires an Azure subscription, infrastructure decisions, deployment pipelines, and live-system troubleshooting that sit outside this workflow. The code changes (Playwright swap, Cosmos/Blob backends, FastAPI wrapper, Dockerfile, OpenTelemetry instrumentation) can be authored here — call it ~8–12 sessions of code work — but the deployment, scaling tune, and hardening are human-driven.

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
| 4.2 | Storage abstraction | #8 (subsumed) | P2 | 1 | Completed (scoped down) |
| 4.3 | Content-type detector lockdown | — (review) | P1 | 1 | Completed |
| 4.4 | Metadata pillar vendor-neutrality | — (review) | P1 | 1 | Completed |
| 5.1 | LLM ground-truth validation | #9 | P1 (strategic) | 3–4 to scaffold; calibration + research time on top | Not started |
| 6 | Azure migration | see audit | P2 | ~8–12 code sessions + human deployment work | Not started |
| — | Auto-discovery | #7 | Won't do | — | Rejected |

**Phases 0–4 total: roughly 15–20 sessions** (includes Phase 4.3 lockdown test and Phase 4.4 vendor-neutrality audit). That's the executable portion through this workflow. Phase 5 has code components I can author but depends on a human calibration gate that cannot be automated. Phase 6 has code I can author but cannot fully complete without infrastructure access.

---

## Notes for future execution

- **Never ship a scoring change without a fixture test that exercises it.** This is the single rule that prevents this plan from producing another generation of drift.
- **Preserve the `universal_score`** through Phase 1 onward so existing consumers and historical comparisons don't break.
- **Lock the classifier before correlating against it.** Phase 4.3 is a hard prerequisite for Phase 5 — correlations against weights that silently shift between runs are not evidence.
- **Keep pillar scoring vendor-neutral.** Phase 4.4 enforces this: vendor-specific signals belong in the classifier (where "authoritative declaration beats inference" is a defensible principle), not inside pillar scoring checks (where they create asymmetric scoring across corpora). LLM-correlation claims in Phase 5 are only interpretable on vendor-neutral pillars.
- **LLM validation is an instrument, not a verdict.** The LLM score does not replace structural scoring; it calibrates it. Report the three axes separately, gate correlation claims on a human calibration set and a variance check, and never ship a pillar-weight change without a published `docs/scoring-calibration.md` that justifies it.
- **Azure migration is a future deliverable, not a gate.** Nothing in Phases 1–5 depends on deploying Clipper as a service.
- **Each phase should land as a PR with a CHANGELOG entry.** The repo doesn't have a CHANGELOG today; Phase 0 or Phase 1 is a good moment to start one.
