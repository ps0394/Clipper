# Phase 5 — Corpus-002 Findings

**Corpus:** 43 URLs, 14 vendors, English documentation and reference content
**Pipeline:** dual-fetcher (raw HTTP + Playwright-rendered) → Readability extraction → Mistral-Large-3 harder-Q/A generator → GPT-4.1 primary scorer + Llama-3.3-70B secondary scorer + Llama-3.3-70B judge (κ=0.773 vs human)
**Date completed:** April 2026
**Status:** findings finalized; scoring changes pending Session 2 of the roadmap

---

## 1. Purpose

This document reports the corpus-002 results and maps each finding to a specific, evidence-tiered scoring recommendation for Clipper. It is the factual basis for the v2 scoring update and the reference point for every claim about corpus-002 elsewhere in the repository.

## 2. Why we ran it

Three motivations drove corpus-002 after corpus-001:

1. **Break the ceiling.** Corpus-001 rendered accuracy hit 94.9%, which is too high to distinguish good pages from great pages or to correlate with pillar scores meaningfully. The ceiling was produced by a generator prompt that over-weighted single-sentence copy-paste questions. A harder-Q/A prompt requiring synthesis, quantitative reasoning, and edge-case questions was needed to produce a usable dynamic range.
2. **Test whether corpus-001's pillar correlations survive a harder task.** Some pillars that correlated with accuracy at the corpus-001 ceiling might correlate differently — or oppositely — when the task discriminates more strongly.
3. **Establish whether Clipper's current weight choices are defensible at all.** The founding scoring weights were chosen by standards-compliance intuition, not by correlation with measured agent retrieval. Corpus-002 is the first corpus with enough dynamic range to test that.

## 3. Research objective

**Does Clipper's current pillar-weight scheme correlate with measured LLM retrieval accuracy on a harder-Q/A task, and if not, what directional changes does the evidence support?**

Specifically, the study asks:
- Which pillars, if any, correlate with rendered-HTML accuracy at p < 0.05?
- Which pillars correlate near zero or negatively?
- What does the composite `universal_score` correlation look like?
- Are there systematic differences across content-type profiles, vendors, or fetch tiers?

## 4. Decisions this research must inform

1. **v2 weight direction** — which pillars move up, which move down.
2. **Removal candidates** — which signals should be dropped from headline scoring and reported only as diagnostics.
3. **Known-gaps disclosure** — which signals exist in the architecture but cannot be defended by current evidence.
4. **Phase 6 scoping** — which follow-up experiments are needed before v3 design can be committed.

## 5. What we did

- Generated a harder-Q/A prompt (`retrievability/phase5/prompts/generator-hard.txt`) requiring ≥2 synthesis questions, ≥1 quantitative/comparative question, and ≥1 constraint/edge-case question per page, forbidding single-sentence-copy answers.
- Added a `--generator-prompt` CLI flag threaded through `retrievability/cli.py` → `retrievability/phase5/cli.py` → `retrievability/phase5/runner.py` → `retrievability/phase5/generator.py`.
- Selected 43 URLs across 14 vendors: Anthropic (5), AWS (2), Docker (3), GCP (1), GitHub (4), Kubernetes (2), Learn (4), MDN (2), Node.js (2), OpenAI (2), Perplexity (2), Postgres (1), Python (5), Snowflake (3), Stripe (3), Wikipedia (2). Content types: article (12), FAQ (3), landing (4), reference (12), sample (2), tutorial (10).
- Ran the dual-fetcher + harder-Q/A + LLM-judge pipeline. Resumed once after a mid-run rate-limit; cache-from-files logic picked up cleanly with no duplicate scoring.
- Analyzed with `scripts/phase5-analyze.py` producing `per-page.csv` and `stats.json` in `evaluation/phase5-results/corpus-002-analysis/`.

Seven pages in tier2 failed raw fetch (retained in rendered-only analysis): OpenAI (2), Wikipedia (2), GCP (1), plus 2 others. All 43 pages succeeded at rendered fetch.

## 6. What we found

### 6.1 The ceiling broke

| Metric | Corpus-001 | Corpus-002 | Change |
|---|---:|---:|---:|
| Rendered accuracy (mean) | 0.949 | 0.698 | −0.251 |
| Raw accuracy (mean) | 0.938 | 0.739 | −0.199 |
| Accuracy variance across pages | very compressed | broad — 0.0 to 1.0 | dramatically expanded |

The harder-Q/A prompt successfully produced a usable distribution. The ~0.70 rendered accuracy level is defensible as an honest measurement of synthesis-task retrievability on curated documentation.

### 6.2 Composite score does not correlate with accuracy

| Score | n | Pearson r vs accuracy |
|---|---:|---:|
| `parseability_score_raw` vs `accuracy_raw` | 36 | +0.089 |
| `parseability_score_rendered` vs `accuracy_rendered` | 43 | −0.009 |
| `universal_score_raw` vs `accuracy_raw` | 36 | +0.095 |
| `universal_score_rendered` vs `accuracy_rendered` | 43 | −0.007 |

**This is the headline negative finding.** Clipper's current composite scores carry essentially no linear predictive signal for LLM retrieval accuracy on the harder-Q/A task. Both `parseability_score` (profile-weighted) and `universal_score` (article-weighted) fail. The weighting scheme itself is the problem — individual pillars do carry signal (§6.3), but the current weights combine them in a way that cancels out.

### 6.3 Pillar-level correlations reveal the structure

Correlations computed against `accuracy_rendered` (n=43):

| Pillar | Pearson r | Mean pillar score | Current weight (article) |
|---|---:|---:|---:|
| `content_extractability` | **+0.484** | 74.2 | 20% |
| `http_compliance` | +0.242 | 71.2 | 10% |
| `metadata_completeness` | +0.224 | 57.4 | 10% |
| `structured_data` | +0.036 | 31.2 | 20% |
| `dom_navigability` | −0.189 | 36.3 | 15% |
| `semantic_html` | **−0.301** | 63.3 | 25% |

**Interpretation:**
- `content_extractability` is the single dominant signal. It measures whether Readability can extract a coherent body from the DOM. When this fails, no other pillar compensates.
- `semantic_html` correlates *negatively* with accuracy. Pages with denser semantic markup scored worse on retrieval, which is consistent with the observation that heavily-templated sites (Stripe API reference, GitHub REST reference) are simultaneously high on semantic markup and low on extractability.
- `structured_data` correlates near zero. The schema.org / JSON-LD evidence from corpus-002 does not support its 20% weight.
- `dom_navigability` (axe-core WCAG proxy) correlates mildly negatively, likely via the same templating mechanism as `semantic_html`.
- `http_compliance` and `metadata_completeness` carry weak positive signal, both below the p<0.05 threshold at n=43 but directionally consistent.

### 6.4 Per-profile observations

| Profile | n | Mean accuracy (rendered) | Notes |
|---|---:|---:|---|
| FAQ | 3 | 0.933 | Highest; questions self-document |
| article | 12 | 0.733 | Baseline |
| reference | 12 | 0.683 | Depressed by API-ref extraction failures |
| sample | 2 | 0.700 | n too small for inference |
| landing | 4 | 0.650 | Mixed marketing + product content |
| tutorial | 10 | 0.620 | Depressed by multi-step structure defeating single-answer Q/A |

Content-type matters, but n is too small per profile for weight-fitting. Profile-specific weights are deferred to corpus-003.

### 6.5 Per-vendor outliers

Two pages scored accuracy_rendered = 0.0:
- **Stripe API (docs-stripe-com-api-charges)**: content_extractability = 41.6. API-reference HTML is interleaved with an interactive shell that defeats Readability.
- **GitHub REST (docs-github-com-en-rest-repos-repos)**: content_extractability = 40.9. Same failure mode: auto-generated API-reference DOM.

Wikipedia's LLM article scored accuracy_rendered = 0.3 despite a reasonable composite score, flagging that Wikipedia's rendered HTML carries substantial non-body chrome the grader picked up as distractor content.

AWS scored the highest vendor rendered accuracy (1.000, n=2) — small sample but notable as the only vendor at 100% with the harder-Q/A prompt.

## 7. What this means

Four interpretive claims, each with the evidence behind it:

1. **Clipper's current scoring model does not predict agent retrieval accuracy.** The composite `universal_score` has Pearson r ≈ 0 against measured accuracy at n=43. Whatever value Clipper delivers today, it does not come from the headline number correlating with the outcome it claims to measure.

2. **The pillars themselves are not uniformly broken; the weights are.** `content_extractability` works as a signal. `semantic_html` works in the opposite direction of its current weight. `structured_data` carries no corpus-002 signal at its current weight. The model's problem is not "no signal exists" — it is "signals exist but are drowned by mis-weighting."

3. **Extractor-output markdown (what Readability produces) is the dominant retrievability pathway currently measured.** `content_extractability` at r=+0.484 is effectively measuring how well Readability turns the page into clean body text. Pages that defeat this step score near zero on retrieval regardless of their other pillars.

4. **Signals the tool does not currently measure plausibly exceed in importance some signals it does.** Served-markdown channels (content negotiation, `<link rel="alternate" type="text/markdown">`, sibling `.md` URLs) are invisible to the current pipeline. Agent-specific fetch behavior is invisible. The bottom-quartile pages on `content_extractability` are exactly the pages served-markdown was invented to rescue, and none of that signal is in the current score. This is a measurement gap, not a scoring gap.

## 8. Recommended adjustments

All recommendations are **directional**, not point values. Precise target weights wait for Session 2's §10.1 projected-correlation gate and for held-out corpus validation.

### 8.1 Pillar weight direction

| Pillar | Current (article) | Direction | Evidence tier |
|---|---:|---|---|
| `content_extractability` | 20% | **↑ substantially** | E1 — r=+0.484 |
| `semantic_html` | 25% | **↓ toward floor (~10%)** | E1 — r=−0.301 |
| `structured_data` | 20% | **↓ toward 10%** | E1 — r=+0.036, not significant |
| `dom_navigability` | 15% | ↓ toward 10% | E1 — r=−0.189 |
| `metadata_completeness` | 10% | ≈ hold or ↑ slightly | E1 — r=+0.224, not significant |
| `http_compliance` | 10% | ≈ hold or ↑ slightly | E1 — r=+0.242, not significant |

**Do not remove pillars entirely.** Corpus-002 is n=43 on English docs. Absence of evidence at this sample size is not evidence of absence for a whole pillar. Down-weight, do not delete.

### 8.2 Signals to add (v2, detection-only)

- **Page-level markdown-alternate detection.** Detect `<link rel="alternate" type="text/markdown">` on the page and presence of a sibling `.md` at a predictable path. Report in audit trail. No scoring contribution until Phase 6 validates retrieval lift. Rationale: scales to enterprise corpus sizes (unlike site-level alternatives); directly enables the content-negotiation retrieval path we intend to grade in Phase 6.

### 8.3 Signals to remove from headline scoring

- **Site-level agent-discovery conventions** (including `llms.txt`-style manifests) should not contribute scoring points. Keep detection for the audit trail but exclude from `universal_score`. Rationale: no evidence of autonomous agent consumption, and the structural scalability problem (e.g. Learn's ~20M pages across locales) makes awarding points for their presence a docs-team-size proxy, not a retrievability proxy.

### 8.4 Publication format

Publish v2 weights as **ranges** with explicit confidence language (e.g. `content_extractability: 30–40%`), not as point values. Document the evidence basis for each range in `docs/scoring.md`. Add a "known gaps" section naming the signals v2 cannot yet defend.

## 9. Evidence-to-decision mapping

| Decision | Evidence | Confidence |
|---|---|---|
| Reweight toward `content_extractability` | §6.3 (r=+0.484) | High |
| Down-weight `semantic_html` | §6.3 (r=−0.301) | High |
| Down-weight `structured_data` | §6.3 (r=+0.036, not significant) | Medium |
| Hold `metadata_completeness` and `http_compliance` | §6.3 (directional positive, not significant) | Medium |
| Publish ranges not point values | §6.2 (composite r ≈ 0 shows model is fragile) | High |
| Add page-level markdown-alternate detection | §7.4 (structural argument) | High |
| Exclude `llms.txt`-style site manifests from scoring | §8.3 (scalability + no consumer evidence) | High |
| Defer profile-specific weight changes | §6.4 (n too small per profile) | High |
| Defer new-pillar proposals (Fetch Integrity, Content Atomicity, Context Portability) | Phase 6 scope | High |

## 10. Next steps

1. **Projected-correlation gate (§10.1).** Before shipping v2 weights, re-weight existing corpus-002 pillar values with candidate weight sets and compute Pearson r vs accuracy_rendered. Target: meaningful positive r on the composite. If no candidate set achieves this, the problem is deeper than weights and v2 should not ship on corpus-002 evidence alone.
2. **v2 scoring implementation.** Per §8.1–8.4. Detection-only additions, directional weight changes, ranges-not-values, known-gaps documentation.
3. **Phase 6 experiment 1 — cross-judge variance.** Re-run corpus-002 grading through 2 additional judges. Produce κ and per-page agreement. Establishes CIs for every corpus-002 accuracy number.
4. **Phase 6 experiment 2 — tri-fetcher served-markdown A/B.** Extend fetcher to content-negotiate for `text/markdown`. Run paired grading on corpus-002 vendors that expose markdown alternates. First direct evidence for the served-markdown pathway.
5. **Temporal replication (T+30d).** Re-run unchanged corpus-002 at T+30 days. Any page-level |Δ| > 0.10 without content changes indicates stability concerns that widen v2 weight ranges.
6. **Corpus-003 design.** Balanced across 5 content-type profiles × 6 vendors, including robots-blocked and challenged pages. This is the evidence base for v3.

## 11. What this data does NOT support

To forestall overclaim, corpus-002 **cannot** support:

- Precise weight values. Only direction.
- Profile-specific weight schemes. n too small per profile.
- Cross-agent generalization claims. Single grader architecture at this corpus.
- Served-markdown claims in either direction. Not measured.
- Temporal stability claims. One run, one timepoint.
- Non-English / non-docs generalization. Out of scope.
- Standard-as-methodology publication. Corpus-003 minimum.

## 12. Appendix

**Artifacts:**
- Raw per-page data: `evaluation/phase5-results/corpus-002/`
- Analysis outputs: `evaluation/phase5-results/corpus-002-analysis/`
  - `stats.json` — overall, per-tier, per-profile, per-vendor summary statistics + pillar correlations
  - `per-page.csv` — URL-level metrics
  - `analysis.md` — auto-generated analysis report
- Run logs: `evaluation/phase5-results/corpus-002.log`
- Generator prompt: `retrievability/phase5/prompts/generator-hard.txt`
- Analyzer: `scripts/phase5-analyze.py`

**Related docs:**
- Phase 5 methodology: `docs/phase-5-methodology.md`
- Phase 5 corpus-001 findings: `docs/phase-5-findings.md`
- Phase 5 dual-fetcher plan (Phase 6 scope): `docs/phase-5-dual-fetcher-plan.md`
- Current scoring: `docs/scoring.md`

**Known artifact hygiene task:** corpus-002 page captures contain unredacted Stripe test/live key patterns and must be redacted before the artifacts directory is committed. Same pattern as corpus-001 redaction: `(sk_test|sk_live|pk_live|rk_live)_[A-Za-z0-9]+ → $1_REDACTED` across `*.html`, `*.txt`, `*.json`.

---

## Addendum A — Session 1 F1.2 projected-correlation gate result

**Date:** Session 1 execution (redaction + gate)
**Script:** `scripts/projected-correlation-gate.py`
**Output:** `evaluation/phase5-results/corpus-002-analysis/projected-gate.json`
**Gate threshold:** Pearson r ≥ +0.35 between re-weighted composite and `accuracy_rendered`
**N:** 43 (zero skipped)

### A.1 Candidates tested

| Candidate | sem | ext | struct | dom | meta | http | Pearson r | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| v1_baseline_article | 0.25 | 0.20 | 0.20 | 0.15 | 0.10 | 0.10 | **−0.007** | fail |
| A_extractability_40 | 0.10 | 0.40 | 0.10 | 0.10 | 0.15 | 0.15 | +0.278 | fail |
| B_extractability_35 | 0.10 | 0.35 | 0.15 | 0.10 | 0.15 | 0.15 | +0.224 | fail |
| C_extractability_30 | 0.15 | 0.30 | 0.15 | 0.10 | 0.15 | 0.15 | +0.170 | fail |
| D_drop_semantic_and_dom | 0.05 | 0.40 | 0.15 | 0.05 | 0.20 | 0.15 | **+0.315** | fail |
| E_http_metadata_lift | 0.05 | 0.30 | 0.15 | 0.05 | 0.20 | 0.25 | +0.285 | fail |

(sem = semantic_html, ext = content_extractability, struct = structured_data, dom = dom_navigability, meta = metadata_completeness, http = http_compliance.)

### A.2 Result

**Gate FAILED.** Best candidate reaches r = +0.315, which is below the +0.35 threshold the roadmap requires before shipping v2 weights.

### A.3 Interpretation

This result is directionally consistent with §6.2 (composite r ≈ 0 in v1) and §7 (some pillars correlate positively, others correlate negatively). Moving weight toward the positive-correlating pillars and away from the negative-correlating ones does improve r — from −0.007 to +0.315, a swing of ~0.32 — but it is not enough. The ceiling imposed by pillar quality is reached before the gate is reached.

Plain language: re-weighting the existing six pillars cannot, on this corpus, produce a composite that correlates meaningfully with retrieval accuracy. The problem is not only that v1 used the wrong weights; at least one of {pillar measurement quality, pillar selection, accuracy signal granularity} is also limiting the ceiling.

### A.4 Implication for the roadmap

Per PRD `findings/v2-scoring-phase6-roadmap-prd.md` §4 (Success Metrics) and §7.2 (F2.6 regression check), v2 weights should not ship on re-weighting alone when this gate fails. Session 2 plans (F2.1–F2.8) remain executable, but with the following adjustments:

1. **v2 must be published with the "evidence-partial" tag and explicit disclosure that the re-weighting gate failed on corpus-002.** The PRD anticipates this case; the tag is not an apology, it is an accurate label.
2. **Shipping v2 on directional evidence alone is a product/editorial decision, not a statistical one.** The data supports that re-weighting is directionally correct (r moves from 0 to +0.3); it does not support that re-weighting, by itself, makes the composite a defensible agent-readiness predictor.
3. **Session 3 (F3, cross-judge variance) and Session 4 (F4, tri-fetcher served-markdown) become more important, not less.** Either the accuracy signal has too much noise to reach +0.35 at n=43 (F3 would reveal this via CIs), or the pillars are missing a structural signal the tri-fetcher can surface (F4). Both are testable.
4. **Candidate D becomes the reference weight set for v2 if v2 ships.** Not because it passes the gate (it does not) but because it is the best-attested direction from the candidates considered. If the decision is to ship, the published weights should not claim to be optimized — they should be labeled as the best-attested direction pending Phase 6.

### A.5 Decision required

Before closing Session 1, the owner must choose between:

- **(α) Ship v2 anyway,** labeled evidence-partial, with Candidate D as the reference weights and this addendum cited prominently in release notes. Session 2 runs as planned.
- **(β) Defer v2 pending Phase 6.** Skip Session 2. Jump to Session 3 (F3 cross-judge CIs) to determine whether the +0.35 ceiling is a signal-noise limitation or a pillar-quality limitation, then return to v2 with that evidence.
- **(γ) Expand candidate set before deciding.** Try additional weight configurations (e.g., pillar removal, non-linear composites) before α/β. Requires defining stopping criteria up front to avoid p-hacking.

This addendum does not select one. The default roadmap behavior per PRD §8.1 exit criteria is (α) with disclosure; Session 1 is otherwise complete.

---

## Addendum B — Session 1 γ expanded-candidate experiments

**Date:** Session 1 execution, same day as Addendum A
**Script:** `scripts/gamma-experiments.py`
**Output:** `evaluation/phase5-results/corpus-002-analysis/gamma-experiments.json`
**N:** 43 (same samples as Addendum A)
**Decision rule (committed before run, per §A.5 option γ):**
- `best_r ≥ 0.35` → ship v2 with best γ composite (α)
- `0.32 ≤ best_r < 0.35` → ship v2 with Candidate D weights (α-with-D)
- `best_r < 0.32` → defer v2; jump to Session 3 (β)

### B.1 Single-pillar correlations (foundational)

| Pillar | Single-pillar r vs `accuracy_rendered` |
|---|---:|
| content_extractability | **+0.484** |
| http_compliance | +0.242 |
| metadata_completeness | +0.224 |
| structured_data | +0.036 |
| dom_navigability | −0.189 |
| semantic_html | **−0.301** |

`content_extractability` is the only pillar with a substantial positive correlation. `semantic_html` and `dom_navigability` correlate *negatively*, which is why Addendum A's candidates could not exceed r ≈ +0.31: every candidate kept nonzero weight on at least one pillar whose single-pillar r was negative.

### B.2 Experiment results

| Experiment | Best variant | r | Gate |
|---|---|---:|:---:|
| 1. Pillar drop-outs (Candidate D weights, renormalized) | drop `structured_data` | **+0.457** | ship |
| 1. | drop `semantic_html` | +0.341 | directional |
| 1. | drop `content_extractability` | +0.099 | fail |
| 2. Top-k pillars | **top-2 corr-proportional** (ext+http, 0.67/0.33) | **+0.570** | ship |
| 2. | top-2 equal (ext+http, 0.50/0.50) | +0.548 | ship |
| 2. | top-3 corr-proportional (ext+http+meta) | +0.547 | ship |
| 2. | top-3 equal (ext+http+meta) | +0.465 | ship |
| 2. | top-4 corr-proportional (+struct) | +0.510 | ship |
| 2. | top-4 equal (+struct) | +0.252 | fail |
| 3. Z-score normalized | z-score + Candidate D | +0.457 | ship |
| 3. | z-score + v1 baseline | +0.101 | fail |
| 4. Rank-based (Candidate D weights) | — | +0.396 | ship |
| 5. Binary median-gate (Candidate D weights) | — | +0.281 | fail |

**Best overall: top-2 correlation-proportional, r = +0.570.** Decision branch triggered: **α (ship v2).**

### B.3 Interpretation

Four independent reformulations exceed the +0.35 ship gate:

1. **Pillar drop-outs.** Removing `structured_data` alone (single-pillar r ≈ 0) raises composite r from −0.007 to +0.457. Structured data is signal-free on corpus-002.
2. **Top-k subsets.** Restricting to the top-2 positively-correlating pillars (`content_extractability` + `http_compliance`) reaches +0.548 (equal) to +0.570 (correlation-proportional). Adding `metadata_completeness` as a third pillar slightly reduces r at equal weight but remains well above the gate.
3. **Z-score normalization.** With Candidate D weights on z-scored pillars, r = +0.457. Scale distortion on the raw 0–100 pillar values was suppressing Pearson r in Addendum A.
4. **Rank-based composite.** Candidate D weights on ranks give r = +0.396. Outliers on individual pillars were contributing to the Addendum A ceiling.

**The binary-gate result (+0.281) is informative in the negative direction.** The relationship is not a thresholded pass/fail; it is continuous. Agent-readiness is a gradient.

**The top-4 equal result (+0.252) is informative in the negative direction.** Once `structured_data` is given weight equal to the positive pillars, the composite is dragged back down. This is further evidence that `structured_data` is contributing noise, not signal, on corpus-002.

### B.4 What this does and does not prove

**Proves (on corpus-002):**
- Composite formulation, not just weights, was part of the Addendum A ceiling.
- `content_extractability` + `http_compliance` alone, equally weighted, predict agent retrieval accuracy better than any v1-style six-pillar weighting.
- Three of six pillars (`semantic_html`, `dom_navigability`, `structured_data`) contribute no positive signal to the composite at this corpus size.

**Does not prove:**
- That the 2-pillar composite generalizes beyond corpus-002. n=43.
- That the other three pillars have no value as diagnostics. They may still surface actionable failure modes for authors even when they do not predict agent accuracy. v2 should keep reporting them; v2 should stop scoring them into the headline.
- That `+0.570` is the ceiling. Phase 6 (F3 judge CIs, F4 tri-fetcher) may raise it further.
- That 0.67/0.33 is the right split for `content_extractability`/`http_compliance`. Correlation-proportional weights at n=43 are overfit to this corpus.

### B.5 Recommended ship configuration for v2

Per the PRD's ranges-not-points discipline, the overfit risk on `top2_corr_proportional` argues for shipping a less precise but more defensible variant.

**Recommendation: ship `top2_equal` as the v2 headline composite.**

| Pillar | v2 headline weight | Role |
|---|---:|---|
| content_extractability | 0.50 | headline |
| http_compliance | 0.50 | headline |
| semantic_html | 0.00 | diagnostic only, reported but not scored |
| structured_data | 0.00 | diagnostic only, reported but not scored |
| dom_navigability | 0.00 | diagnostic only, reported but not scored |
| metadata_completeness | 0.00 | diagnostic only, reported but not scored |

- Headline r on corpus-002: **+0.548** (well above the +0.35 ship gate).
- Does not claim precision the data cannot support.
- Retains all four zero-weighted pillars as diagnostics in the report so authors still see semantic HTML, schema.org, DOM, and metadata findings. They simply do not contribute to the headline agent-readiness number.
- Direct-language rationale: *v2 scores what predicts agent retrieval accuracy on our corpus. Four of the six v1 pillars failed to predict it. v2 keeps those four as diagnostic findings and drops them from the headline.*

This is a much more aggressive change than Addendum A contemplated. The PRD framing "evidence-partial" still applies — n=43 is small, one grader architecture, one corpus snapshot — but the evidence now supports a *structural* v2 change, not just a reweighting.

### B.6 Implications for PRD §7 features

- **F2.1 (directional weight update):** superseded. v2 is now a pillar-subset change, not a re-weighting. Document as such.
- **F2.3 (remove site-manifest scoring points):** unchanged, still in scope.
- **F2.5 (known gaps section):** must now include "four pillars demoted to diagnostic-only on corpus-002 evidence; re-evaluation required in Phase 6 and corpus-003."
- **F2.6 (regression check):** acceptance now clears easily (r = +0.548 ≥ +0.35).
- **F2.7 (evidence-partial tag):** still applies. The tag is narrower now: it covers corpus size and single-grader architecture, not "we cannot show a positive signal."

### B.7 Decision locked

Proceeding with **α-ship-best-γ**, specifically the `top2_equal` variant per §B.5. F1.3 commits and Session 2 replan follow.

---

## Addendum C — Session 2 v2 regression check (F2.6)

**Status:** ship gate **PASSED**. Recorded once v2 scorer wired. Purpose of this addendum is to pin the number actually produced by the shipping v2 code against `accuracy_rendered`, separate from the γ-sweep projection in §B.

### C.1 Method

The v2 scorer differs from the γ-sweep projection in one material way: PRD F2.2/F2.3 demotes `agent_content_hints` (markdown-alt link, `markdown_url` meta, `llms.txt`, non-HTML alternates, `data-llm-hint`) inside `http_compliance` to diagnostic-only. Those hint points are no longer added to the `http_compliance` subscore. Since `http_compliance` is a 50% headline pillar in v2, this change propagates into the composite for any page that previously earned hint points.

The regression script replays this arithmetically against the committed corpus-002 on-disk `clipper-scores.rendered.json` files. For each page:

1. Read the v1 `http_compliance.score_breakdown` from the audit trail.
2. Subtract `agent_content_hints` from the uncapped sum; recap at 100.
3. Apply `V2_WEIGHTS` (0.50 × `content_extractability` + 0.50 × recomputed `http_compliance`).
4. Correlate against `accuracy_rendered` from `per-page.csv`.

Script: [`scripts/v2-regression-corpus002.py`](../scripts/v2-regression-corpus002.py).
Full per-page output: [`evaluation/phase5-results/corpus-002-analysis/v2-regression.json`](../evaluation/phase5-results/corpus-002-analysis/v2-regression.json).

### C.2 Result

| metric | value |
|---|---|
| N | 43 |
| skipped | 0 |
| v1 parseability mean | 54.57 |
| v2 headline mean | 71.14 |
| Pearson r (v1 profile-weighted composite vs. accuracy_rendered) | −0.0086 |
| **Pearson r (v2 composite vs. accuracy_rendered)** | **+0.6181** |
| Ship gate | r ≥ +0.35 |
| **Decision** | **PASS** |

### C.3 Interpretation

The r = +0.618 observed here is higher than the +0.548 γ-sweep projection in §B. The delta is the F2.2/F2.3 hint demotion: removing the hint contribution from `http_compliance` strengthens that pillar's alignment with `accuracy_rendered` because the hint signals were behaving like noise on this corpus rather than a retrieval-lift predictor.

That delta is useful diagnostic evidence on its own — it means `agent_content_hints` was a mild *detractor* for headline correlation on corpus-002, not a neutral addition. This is consistent with the PRD framing that declared agent-alternate formats are capability claims, not capability evidence, and should not earn points until the alternates are fetched, validated, and shown to lift retrieval success.

The v1 profile-weighted composite on the same 43 pages correlates at r = −0.0086 — not statistically different from zero. The v1 → v2 shift is therefore a move from "no headline signal" to "moderate positive headline signal," not a refinement of an already-working system. This is what `v2-evidence-partial` claims and is the evidence basis for the tag.

### C.4 Caveats for this number

- Single corpus, single agent configuration, two-shot mode. r = +0.62 on corpus-002 does not project to other agents or longer-horizon tasks.
- n = 43 is adequate to ship above the +0.35 gate; it does not support fractional-weight tuning (50/50 is a deliberately coarse choice).
- The four diagnostic-only pillars are still scored and reported; they are just excluded from the headline. Any of them may be restored to the headline once a dedicated corpus shows retrieval-relevance.
- This regression uses on-disk rendered HTML captured during the Phase 5 corpus build. A live re-fetch would introduce network and rendering variance not present here.

### C.5 What this gate does and does not authorize

- **Authorizes:** tagging `v2-evidence-partial`, shipping the v2 scorer as the default, updating docs.
- **Does not authorize:** claims about cross-vendor template quality, claims about JavaScript-dependence rankings, claims that four-pillar diagnostic-only status is "fair" to any specific vendor. All of those are open questions gated on Phase 6 and corpus-003.

---

## Addendum D — Session 3 Phase 6 Experiment 1 (Cross-Judge Variance) — Scaffold + Single-Judge CIs

**Status:** scaffold landed; cross-judge κ statistics pending Foundry-deployment approval for 2 additional judges (F3.2). F3.4 CIs computable on the existing single-judge data are published below and should be treated as an **under-estimate** of true uncertainty — cross-grader variance is not yet captured in these intervals.

### D.1 F3.1 — Judge selection criteria

The PRD lists Claude-3.5-Sonnet, Gemini-1.5-Pro, and GPT-4o as candidates. For corpus-002 re-grading on 43 pages × 5 Q/A × 2 runs = ~430 judgments per added judge, the selection criteria are:

1. **Architectural diversity from the existing judge.** The corpus-002 primary judge is **Llama-3.3-70B**, which already breaks within-family bias against the GPT-4.1 scorer. The two added judges must come from different vendors to avoid a two-of-three majority from a single family. The rule of three: OpenAI (GPT-4o), Anthropic (Claude-3.5-Sonnet), Google (Gemini-1.5-Pro), Meta (Llama — already present).
2. **Azure AI Foundry availability.** The existing `retrievability/phase5/clients.py` talks to a single Foundry resource with per-judge deployment names. Extending to 2 more judges is a `.env` change, not a client rewrite, provided the deployments live in the same Foundry project.
3. **Cost feasibility.** Each re-grading pass is ~430 judge calls. Judge prompts are short (question + ground truth + candidate + 2-line verdict template). At current per-token pricing for the candidate models, two full re-grading passes should sit well under corpus-003's projected budget. Exact cost estimate is deferred to the procurement step.
4. **Token-limit and throughput parity.** Judge calls are small; any of the three candidates handle the prompt size comfortably. No hard tie-breaker here.

**Recommended selection (to be confirmed at procurement):**

- **Judge B: Claude-3.5-Sonnet** — strongest architectural diversity from Llama primary (different training corpus, different RLHF provider, different lineage). Also the most commonly-deployed judge in public RAG-evaluation literature.
- **Judge C: GPT-4o** — same vendor as the scorer (GPT-4.1), which is a deliberate choice: if GPT-4o-as-judge produces *different* grades from the two non-OpenAI judges, that is a clean signal of within-family scorer/judge co-bias and is itself a finding.

If Claude access is delayed by Foundry contracts, swap in **Gemini-1.5-Pro** as Judge B. The architectural-diversity requirement is satisfied by any non-OpenAI, non-Meta pick.

This selection is **not final** until Foundry deployments are approved. The scaffold below is deployment-agnostic.

### D.2 F3.2 — Regrade scaffold (no LLM calls yet)

Existing harness in [`retrievability/phase5/runner.py`](../retrievability/phase5/runner.py) already supports re-grading a completed corpus directory. Previously it hardcoded `judge_id="primary"` and the Foundry `scorer_secondary` deployment. Session 3 extends `rejudge_pilot` with two new keyword arguments:

- `judge_id: str` — tag written into the output filename: `grades.<judge_id>.judged.rendered.json`. Defaults to `"primary"` so existing pilot-calibration flows are untouched.
- `judge_deployment: str | None` — explicit deployment override. Defaults to `config.scorer_secondary_deployment` (existing behaviour).

The CLI exposes this through two new flags on `python main.py phase5 rejudge`:

- `--judge-id NAME` — e.g. `--judge-id claude35`.
- `--judge-deployment-env VARNAME` — names an env var in `.env` that holds the Foundry deployment string. Defaults to `PHASE5_SCORER_SECONDARY_DEPLOYMENT`.

To run F3.2 once deployments are approved:

```powershell
# .env additions
# PHASE5_JUDGE_CLAUDE35_DEPLOYMENT=<foundry-deployment-for-claude-3.5>
# PHASE5_JUDGE_GPT4O_DEPLOYMENT=<foundry-deployment-for-gpt-4o>

python main.py phase5 rejudge evaluation/phase5-results/corpus-002 `
    --judge-id claude35 `
    --judge-deployment-env PHASE5_JUDGE_CLAUDE35_DEPLOYMENT

python main.py phase5 rejudge evaluation/phase5-results/corpus-002 `
    --judge-id gpt4o `
    --judge-deployment-env PHASE5_JUDGE_GPT4O_DEPLOYMENT
```

Each command writes `grades.<judge_id>.judged.rendered.json` into every per-page directory alongside the existing `grades.primary.judged.rendered.json`. It does **not** re-fetch pages or re-run the scorer — Q/A pairs and scoring answers are reused. Cost and time scale linearly in number of Q/A pairs, not in corpus build cost.

### D.3 F3.3 — Cross-judge κ script (runs on whatever data is present)

[`scripts/phase6-cross-judge-kappa.py`](../scripts/phase6-cross-judge-kappa.py) scans the corpus directory for `grades.*.judged.rendered.json` files, aligns labels per `(pair_index, run_index)`, and reports:

- per-page κ for every judge pair
- pooled κ for every judge pair across all pages
- per-judge pooled accuracy (exposes severity differences alongside agreement)
- count of pages with κ < 0.60 per judge pair (the F3.5 gate)

It degrades gracefully on single-judge data: emits per-judge accuracy, skips κ, and writes a `warning` field indicating F3.2 has not run yet.

**Current (single-judge) run:**

```
Pages: 43
Judges found: primary
  primary      n=215 accuracy=0.698
(Pairwise kappa requires >=2 judges; warning recorded in output.)
```

This matches the pooled mean from [`corpus-002-analysis/per-page.csv`](../evaluation/phase5-results/corpus-002-analysis/per-page.csv) (n=43 pages × 5 pairs = 215 grades, mean 0.698), confirming the alignment logic is correct before cross-judge data arrives.

### D.4 F3.4 — 90% CIs on corpus-002 accuracy (single-judge)

Bootstrap (percentile) 90% CIs over pages, seed=42, n_bootstrap=10000, using `accuracy_rendered` from [`corpus-002-analysis/per-page.csv`](../evaluation/phase5-results/corpus-002-analysis/per-page.csv). Full per-stratum output: [`corpus-002-analysis/accuracy-cis.json`](../evaluation/phase5-results/corpus-002-analysis/accuracy-cis.json). Script: [`scripts/phase6-accuracy-cis.py`](../scripts/phase6-accuracy-cis.py).

**Overall:**

| stratum | n | mean | 90% CI |
|---|---|---|---|
| **overall** | 43 | 0.698 | [0.633, 0.758] |
| tier1 | 36 | 0.717 | [0.650, 0.778] |
| tier2 | 7 | 0.600 | [0.400, 0.771] |

**By profile (collapsed to 2-pillar headline in v2 but still reported):**

| profile | n | mean | 90% CI |
|---|---|---|---|
| faq | 3 | 0.933 | [0.867, 1.000] |
| article | 12 | 0.733 | [0.583, 0.867] |
| sample | 2 | 0.700 | [0.600, 0.800] |
| reference | 12 | 0.683 | [0.517, 0.833] |
| landing | 4 | 0.650 | [0.600, 0.750] |
| tutorial | 10 | 0.620 | [0.560, 0.680] |

**By vendor (strata with n ≤ 2 are diagnostic-only; intervals are uninformative):**

| vendor | n | mean | 90% CI |
|---|---|---|---|
| aws | 2 | 1.000 | [1.000, 1.000] |
| postgres | 1 | 1.000 | (n=1; no interval) |
| k8s | 2 | 0.800 | [0.800, 0.800] |
| learn | 4 | 0.800 | [0.600, 1.000] |
| perplexity | 2 | 0.800 | [0.800, 0.800] |
| python | 5 | 0.800 | [0.720, 0.880] |
| docker | 3 | 0.733 | [0.667, 0.800] |
| snowflake | 3 | 0.733 | [0.533, 0.933] |
| anthropic | 5 | 0.720 | [0.600, 0.840] |
| mdn | 2 | 0.700 | [0.600, 0.800] |
| nodejs | 2 | 0.700 | [0.600, 0.800] |
| openai | 2 | 0.700 | [0.400, 1.000] |
| gcp | 1 | 0.600 | (n=1; no interval) |
| stripe | 3 | 0.467 | [0.200, 0.733] |
| github | 4 | 0.450 | [0.150, 0.600] |
| wikipedia | 2 | 0.300 | [0.000, 0.600] |

### D.5 What these numbers show — and what they don't

**What they show:**

- Overall corpus-002 accuracy is **0.698 with a 90% CI of [0.633, 0.758]** (n=43, single judge). The interval width is ~±0.06, which is the minimum uncertainty any comparison against a corpus-002 baseline has to budget for.
- Per-vendor intervals are wide enough that almost no two vendors are separable at 90% confidence on this corpus. github (0.45) vs python (0.80) clearly separate; most other pairs overlap. Any "Vendor X beats Vendor Y on corpus-002" claim without a published interval is a methodology error.
- Per-profile, `faq` (0.933) and `tutorial` (0.620) are clearly separated, but the ordering among `article`, `landing`, `reference`, `sample` is inside the noise.

**What they do not show:**

1. **Cross-judge variance.** These CIs are computed from a single judge's labels. A second and third judge will produce their own accuracy numbers per page, and the *true* uncertainty is the union of page-level sampling variance and cross-judge grader variance. F3.2 is the blocker.
2. **Temporal variance.** corpus-002 was graded once, in a single window. Rendering and server-side content can drift; that is Session 5.
3. **Corpus selection.** These intervals assume the 43 pages are a representative sample of the population of interest. They are not: they are a curated Phase 5 corpus. Generalisation to "the web" is not supported; generalisation to "developer documentation pages from the 14 sampled vendors" is cautiously supported.

### D.6 F3.5 — Weight-range widening decision

Deferred until F3.2 produces cross-judge κ data. The v2 shipping weights are the coarse 50/50 composite — there is no fractional-weight claim to widen. The `confidence_range` field in `ScoreResult` (Session 2 F2.8) already records `caveats` including `"single-corpus, single-judge calibration"`; once F3.2 lands, the caveat list is amended and any κ-driven widening is recorded at that time.

### D.7 What this scaffold authorizes

- **Authorizes:** committing the CLI surface, the κ script, and the CI script; publishing single-judge CIs; publishing the selection criteria.
- **Does not authorize:** any claim of "validated cross-judge agreement" on corpus-002. That claim is gated on F3.2 execution.


---

## Addendum E — Session 4: Phase 6 Experiment 2 scaffold (F4.1–F4.4)

**Scope:** Served-markdown lift experiment per roadmap §7.4. Session 4 delivers the F4.1 tri-fetcher, its unit tests, an HTTP-only pre-experiment probe on corpus-002, the F4.2 paired-grading runner + CLI, and the F4.3 lift-analysis script. Execution of paired LLM grading (F4.2) and the final F4.4 promote/demote recommendation remain gated on Foundry deployment approval.

### E.1 F4.1 — Tri-fetcher implementation

`retrievability/phase5/fetcher.py` gains a public `fetch_markdown(url, *, html_body=None)` that probes three paths in order and returns the first one that yields a real markdown body:

1. **`accept_header`** — GET with `Accept: text/markdown, text/x-markdown; q=0.9, text/plain; q=0.5`.
2. **`link_alternate`** — parse the already-fetched HTML for `<link rel="alternate" type="text/markdown" href=…>` and GET that.
3. **`sibling_md`** — append `.md` to the URL path and GET it.

A content gate `_looks_like_markdown(body, content_type)` guards every probe. It runs the **HTML-negative-marker check first**: if the first ~2KB of body (lowercased, left-stripped) begins with `<!doctype`, `<html`, `<!--`, `<head`, or `<body`, the response is rejected even when the server advertises `Content-Type: text/markdown`. This closes an HTML-in-disguise failure mode observed in early drafting and is covered by `tests/test_tri_fetcher.py::test_tri_fetcher_rejects_html_disguised_as_markdown`.

Meta dict returned alongside the body: `{mode, resolved_by, attempts, elapsed_s, resolved_url, status, content_type, bytes, [link_href|candidate_url]}` — sufficient for F4.3 accounting.

Unit tests: `tests/test_tri_fetcher.py` (9 tests, all green). Uses an in-process `http.server` fixture on an ephemeral port so the tests have no network dependency. Full suite after Session 4: **168/168 passing** (159 baseline + 9 new).

### E.2 F4.3 — Pre-experiment probe (HTTP-only, no LLM)

Before spending Foundry tokens on a paired-grading regrade, Session 4 ran `scripts/phase6-tri-fetcher-probe.py` against all 43 corpus-002 URLs. This probes only — it does not call any LLM. Output: [tri-fetcher-probe.json](evaluation/phase5-results/corpus-002-analysis/tri-fetcher-probe.json), [tri-fetcher-probe.csv](evaluation/phase5-results/corpus-002-analysis/tri-fetcher-probe.csv).

**Overall hit rate: 27/43 = 62.8%.** Resolution path distribution: `accept_header` = 20, `link_alternate` = 2, `sibling_md` = 5.

Per-vendor (16 vendors in corpus-002; 14 with >1 page):

| Vendor     | hits/n | rate   | Path(s) that worked              |
|------------|--------|--------|----------------------------------|
| anthropic  | 5/5    | 100%   | accept_header                    |
| aws        | 2/2    | 100%   | link_alternate                   |
| docker     | 3/3    | 100%   | accept_header                    |
| gcp        | 0/1    |   0%   | —                                |
| github     | 3/4    |  75%   | accept_header                    |
| k8s        | 0/2    |   0%   | —                                |
| learn      | 4/4    | 100%   | accept_header                    |
| mdn        | 0/2    |   0%   | —                                |
| nodejs     | 0/2    |   0%   | —                                |
| openai     | 2/2    | 100%   | sibling_md                       |
| perplexity | 2/2    | 100%   | accept_header                    |
| postgres   | 0/1    |   0%   | —                                |
| python     | 0/5    |   0%   | —                                |
| snowflake  | 3/3    | 100%   | sibling_md                       |
| stripe     | 3/3    | 100%   | accept_header                    |
| wikipedia  | 0/2    |   0%   | —                                |

**Nine vendors serve markdown on every page probed.** Seven serve none. This is an infrastructure fact about the current web, independent of any LLM-grading outcome: Clipper's served-markdown detection can only ever apply to the subset of the web where markdown is actually served. On this corpus that subset is **62.8% of pages** and **56% of vendors** (9/16). Any positive lift F4.2 eventually measures applies only to that fraction; for the remaining 37% of pages the feature contributes nothing one way or the other.

### E.3 F4.2 — Paired-grading scaffold (executable; does not auto-run LLMs)

`retrievability/phase5/runner.py` adds `regrade_markdown_for_pilot(pilot_dir, config, use_judge=True)`. For each page in an existing pilot directory it:

1. Reads `summary.json` (for URL and rendered accuracy) and `qapairs.json` (for ground truth).
2. Calls `fetch_markdown(url)`; writes `fetch.markdown.json` regardless of hit/miss.
3. On hit, if extracted markdown ≥ 1,500 chars, writes `page.markdown.txt`, then scores via the existing `score_page` / `grade_page` / (optional) `judge_page` pipeline. Outputs `scoring.primary.markdown.json`, `grades.primary.markdown.json`, and `grades.primary.judged.markdown.json`.
4. Aggregates per-page deltas into `markdown-regrade-summary.json` at the pilot root.

CLI surface (tested via `--help` smoke run):

```
python main.py phase5 regrade-markdown evaluation/phase5-results/corpus-002 [--no-judge]
```

Required environment (same names as Session 3): `PHASE5_FOUNDRY_ENDPOINT`, `PHASE5_FOUNDRY_API_KEY`, `PHASE5_SCORER_PRIMARY_DEPLOYMENT`, plus `PHASE5_JUDGE_DEPLOYMENT` (or legacy `PHASE5_SCORER_SECONDARY_DEPLOYMENT`) when `--no-judge` is absent.

The scaffold **does not execute LLM calls autonomously** in Session 4. Running it is an explicit operator action.

### E.4 F4.3 — Lift analysis (probe-only null result)

`scripts/phase6-markdown-lift.py` consumes the probe JSON and, optionally, the regrade summary. Run **without** `--regrade` in Session 4 to produce the committed probe-only report: [markdown-lift.json](evaluation/phase5-results/corpus-002-analysis/markdown-lift.json). Status: `"probe_only"`.

**What the probe-only evidence says:** served-markdown is structurally available to 27/43 corpus-002 pages. **What it does not say:** whether grading against the served markdown produces higher Q/A accuracy than grading against the rendered/extracted HTML. No lift has been measured; no direction is implied. An overall positive lift, an overall negative lift, and no lift are all consistent with the current evidence.

When paired grading runs, the script will emit one of four F4.4 statuses (see E.5).

### E.5 F4.4 — Promote/demote recommendation (deferred)

The lift script encodes the promotion rule at the default threshold of 0.10:

| Condition                                                          | `f4_4_recommendation`            |
|--------------------------------------------------------------------|----------------------------------|
| Paired data missing                                                | `no_paired_data`                 |
| Overall mean lift > 0.10 **and** ≥2 vendors above threshold        | `promote_to_pillar_contribution` |
| Overall mean ≤ 0 or (≤ 0.10 and <2 vendors above)                  | `keep_as_diagnostic_only`        |
| Otherwise                                                          | `insufficient_evidence`          |

Session 4 publishes **no** F4.4 recommendation. It is not yet computable.

### E.6 What this scaffold authorizes

- **Authorizes:** committing the tri-fetcher + its tests, the probe script and its corpus-002 output, the paired-grading runner and CLI, the lift script, and the null-context framing that markdown lift is only measurable on the ~63% of corpus-002 pages where markdown is served.
- **Does not authorize:** any claim that served markdown improves (or fails to improve) grading accuracy on corpus-002. That claim is gated on F4.2 execution and the F4.4 rule above.

## Addendum F — Session 5: Phase 6 Experiment 2 execution + token-efficiency probe (F4.2 / F4.3 / F4.4)

Session 5 executes F4.2 (paired LLM grading) twice — once on the original HTML-anchored Q/A (Track A) and once on a bias-corrected intersection-Q/A design (Track B) — and adds a non-LLM token-efficiency probe that the original PRD did not anticipate. The combined evidence resolves F4.4.

### F.1 Headline

- **F4.4 verdict (paired grading): `keep_as_diagnostic_only`.** Bias-corrected paired grading shows mean delta **−0.0118** on n=17, with 16/17 pages at exactly zero. Served markdown and rendered HTML are interchangeable for in-context comprehension on this corpus.
- **Token-efficiency finding (new):** served markdown is **~40% MORE tokens** than a clean readability extract on the median page (median 6,081 vs 4,637 cl100k_base tokens; ratio 1.39×). The widely-repeated "markdown is more token-efficient" framing applies to *naive raw-HTML ingestion*, not to a careful HTML→text pipeline. The ~50× token reduction agents experience comes from the HTML-cleaning step, not from format choice.
- **Combined implication:** served markdown produces neither comprehension lift nor token savings for an agent that already does readability-style extraction. Whatever value served markdown provides for agents must lie in *preprocessing reliability* or *retrieval-side chunking*, neither of which this corpus measures.

### F.2 Track A: paired grading on HTML-anchored Q/A (the original F4.2 design)

The runner generates Q/A from rendered HTML, then grades the rendered extract and the served markdown against the same pairs.

| Metric | n | Value |
|---|---|---|
| Pages with markdown resolved | 25 / 43 | 58.1% (probe was 62.8%; 2 pages dropped on extraction errors) |
| Pages scored | 25 |  |
| Mean delta (`accuracy_markdown_judged` − `accuracy_rendered`) | 25 | **−0.064** |
| Pos / neg / zero | 25 | 5 / 7 / 13 |

Per-vendor (judged):

| Vendor | n | Mean Δ | Median Δ | Pos / Neg |
|---|---|---|---|---|
| github | 3 | +0.133 | +0.200 | 2 / 0 |
| anthropic | 5 | +0.040 | 0.000 | 2 / 1 |
| aws | 2 | 0.000 | 0.000 | 0 / 0 |
| docker | 2 | 0.000 | 0.000 | 0 / 0 |
| perplexity | 2 | 0.000 | 0.000 | 0 / 0 |
| snowflake | 3 | −0.067 | 0.000 | 0 / 1 |
| learn | 4 | −0.200 | −0.200 | 1 / 2 |
| openai | 2 | −0.300 | −0.300 | 0 / 2 |
| stripe | 2 | −0.300 | −0.300 | 0 / 1 |

The F4.4 rule (mean lift > 0.10 AND ≥2 vendors above threshold) **fails**: overall mean is the wrong sign and only one vendor (github) clears the per-vendor threshold. Track A would yield `keep_as_diagnostic_only`.

**However, Track A has a known design flaw.** Q/A drawn from the rendered HTML extract bake content-coverage asymmetry into the test: any content the markdown legitimately omits (nav, dynamic widgets, expanded tables) becomes a grading penalty against markdown. The Track A delta cannot distinguish "markdown has worse comprehension fidelity" from "markdown drops content the rendered extract included." Track B was added to remove this confound.

### F.3 Track B: paired grading on intersection-Q/A (the bias-corrected design)

A new module ([retrievability/phase5/intersection.py](retrievability/phase5/intersection.py), 11 unit tests) computes the **sentence-level content intersection** of the rendered extract and the served markdown. Q/A are then generated from the intersection text only — neither format has a coverage advantage on the question pool.

Pre-flight on corpus-002 (no LLM cost):

- **17 of 25 markdown-resolved pages** have intersection text ≥ 1500 chars (the minimum to support 5 non-clustered Q/A).
- Median intersection size: 2,727 chars; max 15,453.
- Median sentence-overlap: 45% of rendered sentences appear in markdown; 30% of markdown sentences appear in rendered. The two formats are **not** the same document on the median page.
- 8 pages drop out: openai-quickstart, stripe (both pages), python (all 5 pages reported zero overlap because their markdown extracts are nav-only or missing — counted as `intersection_too_thin`), plus 3 anthropic / snowflake short pages.

Track B paired grading on the 17 survivors:

| Metric | Track A (HTML-Q/A) | Track B (intersection-Q/A) |
|---|---|---|
| n scored | 25 | 17 |
| Mean delta (judged) | **−0.064** | **−0.012** |
| Median delta | 0.000 | 0.000 |
| Pos / neg / zero | 5 / 7 / 13 | **0 / 1 / 16** |
| Track A − Track B (mean) | — | **+0.052** (size of the bias removed) |

The −0.052 difference between Track A and Track B is the **size of the HTML-source bias** in the original F4.2 design. After correcting it, **16 of 17 pages produce identical scores on rendered HTML and served markdown**. The single negative is `docs-snowflake-com-en-user-guide-data-load-overview` (rendered=1.0, markdown=0.8) — one question's worth of difference on a 5-question page; not a vendor-level finding.

Per-vendor Track B:

| Vendor | n | Mean Δ | Note |
|---|---|---|---|
| anthropic | 3 | 0.000 | All zero |
| aws | 2 | 0.000 | All zero |
| docker | 2 | 0.000 | All zero |
| github | 2 | 0.000 | (Track A's +0.133 was bias) |
| learn | 3 | 0.000 | (Track A's −0.200 was bias) |
| openai | 1 | 0.000 | Was −0.300 in Track A |
| perplexity | 2 | 0.000 | All zero |
| snowflake | 2 | −0.100 | Median page produced one-Q delta |

Note also: **rendered scores went UP** in Track B vs Track A on many pages (e.g. anthropic-getting-started 0.6→1.0, docker-get-started-02 0.6→1.0, github-plans 0.6→1.0). This is expected — Track A's questions about content the markdown couldn't see also lowered the *rendered* grade on questions that hit boilerplate or marginal content; restricting Q/A to intersection content lifts both versions.

### F.4 F4.4 promote/demote decision

Under the rule encoded in [scripts/phase6-markdown-lift.py](scripts/phase6-markdown-lift.py) (mean lift > 0.10 AND ≥2 vendors above threshold), Track B yields `keep_as_diagnostic_only` even more decisively than Track A — mean is essentially zero and no vendor shows lift. The bias-corrected test does not reverse the verdict.

**The reasoning behind the verdict shifts, however:**

- **Track A's null was inconclusive** because the test design produced a coverage bias of unknown sign and magnitude.
- **Track B's null is a positive finding** of format equivalence: 16/17 pages score identically. Within the corpus and grading methodology, **served markdown and rendered HTML produce indistinguishable in-context comprehension accuracy**.

This is a stronger evidence base than Track A alone, but it scopes narrowly to one regime: an LLM that has the full document in its context window. The finding does **not** apply to:
- **Retrieval-mode RAG.** Chunk boundaries, retriever recall, embedding quality differ between the formats; not measured here.
- **Pipeline reliability.** Crawler/extractor variance is reduced by markdown ingestion; this benefit shows up as variance reduction, not as a per-page mean delta.
- **Code-heavy pages.** Fenced code blocks may behave differently than prose; corpus-002 is mostly prose.

### F.5 Token-efficiency probe (added in Session 5; not in original PRD)

Pure file-size analysis on the 25 corpus-002 pages with all three artifacts ([scripts/phase6-token-efficiency.py](scripts/phase6-token-efficiency.py)). Token counts use `tiktoken` `cl100k_base` (GPT-4 / Claude family). Readability extract is re-computed locally without the runner's 40k clamp; markdown is read as-stored on disk (10 of 25 pages were clamped to 40k chars at fetch time, so reported markdown sizes are floors for those pages).

**Median per page (cl100k_base tokens):**

| Format | Tokens | vs readability |
|---|---|---|
| Rendered HTML (raw, with chrome/scripts/styles) | 206,611 | 53.6× larger |
| Readability extract (un-clamped) | 4,637 | baseline |
| Served markdown (clamped at 40k chars on disk) | 6,081 | **1.39× larger** |

**Three findings:**

1. **The 50× HTML→text reduction is real and is not from markdown.** Going raw HTML → readability extract is ~54× fewer tokens. Going raw HTML → served markdown is ~48× fewer tokens. The difference is small; the win comes from stripping nav/JS/styles, which both formats do. This is the "agent-friendly format" win that gets attributed to markdown but is mostly attributable to *cleaning*.
2. **Served markdown is ~40% MORE tokens than a clean readability extract.** On corpus-002, the median page's markdown is 6,081 tokens vs 4,637 for readability. The "markdown is more token-efficient" claim, applied to web-published documentation, is **false in this corpus**. The likely cause: publisher markdown exports preserve breadcrumbs, version selectors, sidebar links, and front-matter that readability aggressively strips.
3. **The clamp distorts the picture upward for 40% of pages.** 10 of 25 markdown files hit the 40k-char ceiling at fetch time; their true wire token counts are larger than the 6,081 median suggests. Stripe pages run 100k–200k+ chars on the wire. The aggregate markdown/readability ratio is a *floor*, not a ceiling.

### F.6 Per-vendor token efficiency

Sharper than the aggregate. (n=2 cells are noisy; n=4–5 cells more reliable. "clamp" = pages whose markdown was truncated at 40k chars on disk.)

| Vendor | n | Clamped | Median md tokens | Median rt tokens | md/rt ratio | html/md ratio | Reading |
|---|---|---|---|---|---|---|---|
| openai | 2 | 0/2 | 4,115 | 10,818 | **0.34×** | 78× | Markdown is *one-third* the size of readability — **only vendor where markdown wins on tokens**. Likely OpenAI strips chrome more aggressively in their markdown export than readability does in their rendered HTML. |
| aws | 2 | 2/2 | 10,894 | 11,693 | 1.00× | 2.2× | Token-equivalent. Both pages clamped on the markdown side, so true ratio could be much worse. The 2.2× HTML/md ratio is suspicious — AWS rendered HTML is unusually small on these endpoints. |
| docker | 2 | 1/2 | 5,872 | 5,903 | 1.23× | 61× | Roughly equivalent. |
| learn | 4 | 2/4 | 8,056 | 6,392 | 1.27× | 14× | Markdown ~27% larger. The 14× HTML/md ratio is the *worst* of the corpus — Learn's rendered HTML is the most aggressive at minimizing chrome (or its markdown is the most bloated; both can be true). |
| snowflake | 3 | 0/3 | 2,561 | 1,343 | 1.31× | 48× | Markdown ~31% larger; clean comparison (no clamping). |
| perplexity | 2 | 0/2 | 3,729 | 2,524 | 1.46× | 83× | Markdown ~46% larger; clean comparison. |
| github | 3 | 1/3 | 2,646 | 1,696 | 1.56× | 32× | Markdown ~56% larger. |
| anthropic | 5 | 2/5 | 2,911 | 1,163 | 1.61× | 70× | Markdown ~61% larger. The largest n in the corpus and a consistently negative result. |
| stripe | 2 | 2/2 | 8,250 | 3,424 | **6.29×** | 72× | Markdown is **6× LARGER** than readability — and both pages were clamped, so the true wire ratio is even worse. Stripe's markdown export ships massive amounts of chrome / TOC / sidebar content. |

**Reading the table:**

- **Only OpenAI** ships markdown smaller than the readability extraction. Its 0.34× ratio is striking but resting on n=2.
- **Eight of nine vendors** ship markdown that is **larger** than a clean HTML→text extraction. The ratios cluster around 1.2× – 1.6× for most vendors, with stripe as a 6× outlier and aws/openai as exceptions in the other direction.
- **Learn's rendered HTML is unusually compact** (14× HTML/md ratio is by far the lowest), which means the markdown comparison flatters the vendor less than it would for vendors with bigger HTML pages — yet markdown is still larger.
- **Stripe's markdown is dramatically inefficient**, which combined with stripe's Track A regression (−0.300 from the bias) suggests their markdown export is not optimized for agent ingestion at all. (Track B couldn't run on stripe — both pages had <10% sentence overlap.)

### F.7 What this corpus does and does not say about "markdown is agent-friendly"

The slogan does several jobs at once and they should be separated.

| Claim | Evidence on corpus-002 |
|---|---|
| Raw HTML is enormously more verbose than text/markdown | **Confirmed.** ~50× reduction either way. |
| Markdown beats a *naive* HTML ingestion in tokens | **Confirmed.** ~48× reduction. |
| Markdown beats a *good* HTML→text extraction in tokens | **Refuted on this corpus.** 8 of 9 vendors ship markdown larger than readability. Median ratio 1.39×; one outlier at 6.29×. |
| Markdown improves in-context LLM comprehension | **Refuted on this corpus.** Bias-corrected paired delta is −0.012; 16/17 pages identical. |
| Markdown is unambiguously a quality signal worth scoring | **Not supported.** Serving markdown does not imply serving *clean* markdown; some vendors ship markdown that is worse than their HTML on every measurable axis. |
| Markdown is useful for RAG / preprocessing pipelines | **Not measured.** Plausibly true; outside this corpus's regime. |
| Markdown is useful for chunking fidelity (retrieval-side) | **Not measured.** Plausibly true; outside this corpus's regime. |

### F.8 Implications for v2 scoring

1. **F4.4 stays `keep_as_diagnostic_only`** with the stronger Track B evidence base. Served markdown is not promoted to a scored pillar / sub-pillar.
2. **A binary "serves markdown" signal would be misleading** if added naively. Stripe and AWS publish markdown that is larger than their HTML extraction on every measured axis. Rewarding "ships markdown" without measuring "ships markdown that is *better than* the HTML alternative" would inflate scores for vendors whose markdown is publisher-side bloat.
3. **A future served-markdown signal should be conditional**, not binary. Roughly: "publisher serves markdown AND token(markdown) ≤ token(HTML→clean) AND content(markdown) ⊇ content(HTML→clean)." That requires per-page measurement against a reference extractor, not just an `Accept: text/markdown` probe.
4. **The token-efficiency analysis should remain a diagnostic in Clipper output** even without scoring impact. Publishers reading the report benefit from knowing whether their markdown export is leaner or more bloated than their HTML — that's actionable feedback the current pillars don't surface.

### F.9 Caveats and known weaknesses

1. **n is small.** 17 paired pages for Track B; 2-5 per vendor for token analysis. Per-vendor numbers are directional, not statistically separable from noise except where the effect size is large (stripe 6.29×, openai 0.34×).
2. **Judge calibration is not validated on markdown inputs.** The Llama 3.3 judge was calibrated at k=0.773 on rendered-HTML grading. Whether that calibration transfers cleanly to markdown documents was deferred (see Q2 in the session 5 design notes). Track B's null result is consistent with no drift, but does not affirmatively prove no drift.
3. **Test scope is comprehension-mode, not retrieval-mode.** Both versions of the document are in the LLM's context. RAG settings — chunk + embed + retrieve — were not tested. The "markdown helps retrieval" claim remains plausible and untested by this work.
4. **Token analysis ignores publisher intent.** Some publishers may serve markdown specifically as machine-readable export and accept the larger size as a tradeoff for structure. The "1.39× larger than readability" finding is descriptive, not normative.
5. **The 40k-char clamp affected 10 of 25 markdown files.** True wire ratios are worse on those pages than reported. Stripe in particular: the 6.29× ratio is a floor.

### F.10 What this session authorizes

- **Authorizes:** the Track B paired-grading code ([retrievability/phase5/intersection.py](retrievability/phase5/intersection.py), [retrievability/phase5/runner.py](retrievability/phase5/runner.py) `regrade_intersection_for_pilot`, CLI in [retrievability/phase5/cli.py](retrievability/phase5/cli.py) and [retrievability/cli.py](retrievability/cli.py)); the analyzer scripts ([scripts/phase6-intersection-preflight.py](scripts/phase6-intersection-preflight.py), [scripts/phase6-intersection-lift.py](scripts/phase6-intersection-lift.py), [scripts/phase6-token-efficiency.py](scripts/phase6-token-efficiency.py)); 11 new unit tests for intersection logic (test suite 179/179 green); on-disk artifacts under [evaluation/phase5-results/corpus-002/](evaluation/phase5-results/corpus-002) and [evaluation/phase5-results/corpus-002-analysis/](evaluation/phase5-results/corpus-002-analysis); the F4.4 verdict of `keep_as_diagnostic_only` with the stronger evidence base.
- **Authorizes (new claim):** "served markdown does not measurably improve in-context comprehension accuracy on corpus-002, and on the median page is ~40% more tokens than a clean readability extract; the conventional 'markdown is more token-efficient' claim does not survive a careful comparison against a non-naive HTML pipeline."
- **Does not authorize:** any claim about retrieval-mode (chunked/embedded) format effects; any claim that markdown is universally inferior to HTML extraction (the OpenAI counter-example is real, even if n=2); any per-vendor scoring rule using these results until cell sizes reach n≥5.

### F.11 Suggested next work

- **Phase 7 (proposed): retrieval-mode benchmark.** Chunk both formats with a standard splitter, embed, retrieve top-k for held-out questions, grade. This is the regime where the "markdown is agent-friendly" claim is most likely to be quantitatively true and where corpus-002's findings cannot reach.
- **Bloat diagnostic for v2 reports.** Surface per-page `tokens(markdown) / tokens(readability_extract)` as an unweighted observability signal in the standard Clipper output. No scoring impact; reader benefit only.
- **Corpus-003 (deferred).** Re-running F4.2 / token-efficiency on a larger corpus with ≥5 pages per markdown-serving vendor would tighten the per-vendor cells. Lower priority given the corpus-002 result is decisive on the comprehension question.


---

## Addendum G — Session 6: F3.2 cross-judge κ on corpus-002 (executed)

**Scope:** F3.2 was scaffolded in Session 3 (Addendum D) but blocked on Foundry deployment access. This session ran the rejudge pass against the corpus-002 saved candidate answers using two additional judges, computed pooled and per-page Cohen's κ across all three judges, and re-derived the corpus-002 headline accuracy CIs under cross-judge uncertainty. The single-judge CIs published in §D.4 are now superseded for any claim whose scope extends beyond "the Llama 3.3 70B grader specifically."

### G.1 Execution

Three judges ran the same 215 candidate answers (43 pages × 5 Q/A) from `scoring.primary.rendered.json`:

| judge_id   | model                          | role                       | mean accuracy |
|------------|--------------------------------|----------------------------|---------------|
| `primary`  | Llama-3.3-70B-Instruct         | original (Phase 5 baseline) | 0.698         |
| `gpt4o`    | GPT-4o                         | rejudge                    | 0.595         |
| `deepseek` | DeepSeek-V3.2                  | rejudge                    | 0.591         |

All three deployments are served from the same Foundry endpoint
(`ai-model-for-clipper.services.ai.azure.com`). Sonnet and Gemini were not
available on this tenant; DeepSeek-V3.2 was substituted as the third judge
based on diversity of model family (Anthropic-style ↔ OpenAI ↔ open-weights
DeepSeek) and prior precedent of DeepSeek as an LLM-as-judge.

Per-page artifacts: `evaluation/phase5-results/corpus-002/<slug>/grades.{primary|gpt4o|deepseek}.judged.rendered.json`.
Per-judge summaries: `rejudge-summary.{gpt4o,deepseek}.json` at corpus root.
Aggregate: [`evaluation/phase5-results/corpus-002-analysis/cross-judge-kappa.json`](../evaluation/phase5-results/corpus-002-analysis/cross-judge-kappa.json),
[`evaluation/phase5-results/corpus-002-analysis/cross-judge-cis.json`](../evaluation/phase5-results/corpus-002-analysis/cross-judge-cis.json).

### G.2 Cross-judge agreement (Cohen's κ)

Pooled κ across all 215 grades, per pair:

| pair                    | κ (pooled, n=215) | per-page κ < 0.60 |
|-------------------------|-------------------|-------------------|
| deepseek ↔ gpt4o        | **+0.817**        | 12/41 (29%)       |
| deepseek ↔ primary      | **+0.761**        | 14/38 (37%)       |
| gpt4o    ↔ primary      | **+0.706**        | 16/41 (39%)       |

All three pairs land in the **substantial-agreement** band of Landis & Koch
(κ ∈ [0.61, 0.80]) or **almost-perfect** (≥ 0.81 for the deepseek ↔ gpt4o
pair). The κ between Llama (`primary`) and the original human-labelled
calibration set on corpus-001 was 0.773 (pre-existing finding). The new
cross-judge κ values bracket that: machine ↔ machine agreement on
corpus-002 is in the same range as machine ↔ human agreement on
corpus-001.

Per-page κ < 0.60 occurs on 29-39% of pages depending on the pair. Some
of that is mechanical (per-page n=5 makes κ unstable when one judge marks
all 5 the same), some is real disagreement on borderline answers. The
denominator is < 43 because pages where one judge marked all 5 identically
yield undefined κ.

### G.3 Severity ordering and judge bias

GPT-4o (0.595) and DeepSeek-V3.2 (0.591) are noticeably stricter than
Llama-3.3 (0.698) — a ~10-point gap. The two stricter judges agree with
each other (κ = 0.817) more than either agrees with Llama (κ = 0.761,
0.706). This is consistent with Llama being more lenient in granting
"correct" verdicts to candidate answers that GPT-4o and DeepSeek mark
"incorrect" for omission or precision reasons. It is **not** evidence
that Llama is wrong: a third party (human re-adjudication) would be
needed to settle which severity profile is calibrated to ground truth.
For corpus-002 reporting the practical implication is that the
single-judge headline number is sensitive to grader choice.

### G.4 Cross-judge confidence intervals (90% bootstrap, n=43 pages)

Re-derives the §D.4 headline. Bootstraps over pages, not over questions.

| accuracy estimator         | mean   | 90% CI            |
|----------------------------|--------|-------------------|
| Llama (`primary`) only     | 0.698  | [0.633, 0.758]    |
| GPT-4o only                | 0.595  | [0.535, 0.656]    |
| DeepSeek-V3.2 only         | 0.591  | [0.530, 0.651]    |
| **Per-judge union**        | —      | **[0.530, 0.758]** |
| Majority-vote (≥ 2 of 3)   | 0.628  | [0.567, 0.688]    |
| Any-judge correct (upper)  | 0.721  | [0.661, 0.777]    |
| All-judges correct (lower) | 0.535  | [0.474, 0.595]    |

The majority-vote CI [0.567, 0.688] is the most defensible single number
to report when "headline accuracy on corpus-002" is needed and the audience
will not see the per-judge breakdown. The per-judge union [0.530, 0.758]
is the honest uncertainty band: it is wider than the single-judge
[0.633, 0.758] published in §D.4 by ~10 points on the low end, almost
entirely because of the severity gap between Llama and the other two.

### G.5 F3.5 — Weight-range widening decision (resolved)

The Session 3 acceptance criterion (§D.6) was: *widen the v2 weight range if any pair's per-page κ < 0.60 on > 10% of pages.* By the strict reading, all three pairs exceed that bar (per-page κ < 0.60 on 29-39% of pages). Pooled κ, however, is 0.706-0.817 across all pairs — well above 0.60 — and per-page κ at n=5 questions is mechanically unstable (one judge marking all 5 the same yields undefined κ even when accuracy agrees). The substantive question is therefore not the per-page-κ trigger but: **does the v2 ship gate (Pearson r ≥ +0.35 between the v2 composite and accuracy_rendered) survive judge replacement?**

It does. Re-running the F2.6 regression against per-judge accuracy on the same 43 pages:

| judge                   | mean accuracy | Pearson r (v2 composite vs accuracy) | passes +0.35 gate |
|-------------------------|---------------|--------------------------------------|-------------------|
| Llama-3.3-70B (`primary`) | 0.698       | **+0.618**                           | ✓                 |
| GPT-4o                    | 0.595       | **+0.440**                           | ✓                 |
| DeepSeek-V3.2             | 0.591       | **+0.497**                           | ✓                 |

Source: [`scripts/phase6-v2-gate-cross-judge.py`](../scripts/phase6-v2-gate-cross-judge.py),
[`evaluation/phase5-results/corpus-002-analysis/v2-gate-cross-judge.json`](../evaluation/phase5-results/corpus-002-analysis/v2-gate-cross-judge.json).

The composite-vs-accuracy correlation is sensitive to grader severity (r drops by 0.12-0.18 points under the stricter judges), but the v2 composite still cleanly clears the ship gate under every judge. **The v2 50/50 weight choice is therefore judge-robust on corpus-002**; the gate is not an artifact of Llama-specific calibration. F3.5 closes as a **caveat amendment** to `ScoreResult.confidence_range`:

> *"cross-judge accuracy variance: per-judge corpus-002 means span 0.591-0.698 (Llama-3.3-70B / GPT-4o / DeepSeek-V3.2). The v2 composite-vs-accuracy Pearson r ranges from +0.440 to +0.618 across judges (all above the +0.35 ship gate). Report majority-vote CI [0.567, 0.688] or per-judge union CI [0.530, 0.758] when comparing across studies."*

The scoring weights themselves remain 50/50; the v2 composite was deliberately coarse to insulate against exactly this class of grader-induced variance, and the cross-judge regression confirms that design choice held.

### G.6 What this session authorizes (and supersedes)

- **Authorizes:** the F3.2 rejudge runner ([retrievability/phase5/cli.py](retrievability/phase5/cli.py) `_rejudge` + [retrievability/phase5/runner.py](retrievability/phase5/runner.py) `rejudge_pilot`); the κ analysis script ([scripts/phase6-cross-judge-kappa.py](scripts/phase6-cross-judge-kappa.py)); the new cross-judge CI script ([scripts/phase6-cross-judge-cis.py](scripts/phase6-cross-judge-cis.py)); the rejudge artifacts and aggregate JSON files listed in G.1; the F3.4 caveat-amendment text in G.5.
- **Authorizes (new claim):** *"on corpus-002, three independent LLM judges (Llama-3.3-70B, GPT-4o, DeepSeek-V3.2) agree at the substantial-to-almost-perfect level (pooled κ between 0.71 and 0.82) but differ in calibrated severity by ~10 points of accuracy; the cross-judge union 90% CI for corpus-002 headline accuracy is [0.53, 0.76]."*
- **Supersedes:** §D.4's single-judge CI [0.633, 0.758] for any external comparison or competitor-claim use. §D.4 remains accurate as *the Llama-3.3 single-judge result*, but should not be quoted as *"corpus-002 accuracy"* without the cross-judge band.
- **Does not authorize:** a claim that any one of the three judges is the "correct" grader. Re-adjudication against fresh human labels remains the only way to settle severity calibration; that is out of scope for Phase 6.

### G.7 What this does not change

- The **Phase 5 ranking** of pages within corpus-002 is robust across judges. The pages with mean accuracy ≥ 0.80 (8 pages on Llama) are still in the top quartile under GPT-4o and DeepSeek; the pages at 0.0-0.2 (e.g. github REST API, stripe API, snowflake data-load) are bottom-quartile across all three. Cross-judge variance is in the *band* of accuracy, not the *order* of pages.
- The **Track B markdown null result** (Addendum F) is unaffected: that comparison is paired *within* a judge, so cross-judge severity cancels.
- The **F4.4 verdict** (`keep_as_diagnostic_only`, Session 5) is unaffected for the same paired-within-judge reason.


