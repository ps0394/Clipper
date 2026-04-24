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
