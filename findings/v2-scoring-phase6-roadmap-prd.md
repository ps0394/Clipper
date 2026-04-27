# Clipper v2 Scoring & Phase 6 Evidence Roadmap — PRD

**Status:** Draft, pending Session 1 completion
**Owner:** Clipper maintainers
**Scope:** v2 scoring update + Phase 6 experimental program
**Source evidence:** [findings/phase-5-corpus-002-findings.md](phase-5-corpus-002-findings.md)

---

## 1. Executive Summary

Clipper is a corpus-level measurement instrument for whether web pages are retrievable by AI agents. Its founding scoring model assigned pillar weights by standards-compliance intuition — giving equal standing to `semantic_html`, `structured_data`, `content_extractability`, and `dom_navigability`, among others — without a corpus-level test that those weights predicted measured agent retrieval accuracy.

Corpus-002 (43 URLs, 14 vendors, harder-Q/A pipeline) is the first Clipper experiment with enough dynamic range to test that assumption. It found that the composite `universal_score` carries essentially no linear predictive signal for measured LLM retrieval accuracy on synthesis-task Q/A (Pearson r = −0.007, n = 43). Individual pillars do carry signal, but in directions and magnitudes that contradict the current weighting scheme.

This document specifies the work required to convert corpus-002 evidence into a shipped v2 scoring model, establish confidence bounds through Phase 6 experiments, and lay the groundwork for a v3 redesign on corpus-003 evidence. Every requirement in this document traces to a specific corpus-002 finding, a structural scalability argument, or a named known gap. Claims without evidence are labeled as such and deferred.

**The work is being done because Clipper's credibility depends on measuring what it claims to measure.** A retrievability score that does not correlate with retrieval is not a retrievability score; it is a standards-compliance score with marketing on top. Corpus-002 produced the evidence to correct course, and this document is the plan for doing so without overclaiming in the other direction.

## 2. Problem Statement

Three data-backed problems motivate this work:

**Problem 1 — The current composite score does not predict agent retrieval accuracy.**

| Score | n | Pearson r vs accuracy |
|---|---:|---:|
| `parseability_score_rendered` vs `accuracy_rendered` | 43 | −0.009 |
| `universal_score_rendered` vs `accuracy_rendered` | 43 | −0.007 |
| `parseability_score_raw` vs `accuracy_raw` | 36 | +0.089 |
| `universal_score_raw` vs `accuracy_raw` | 36 | +0.095 |

The headline number a Clipper user sees has no measurable relationship with the outcome the number is supposed to represent. This is the central problem.

**Problem 2 — Individual pillar weights contradict the evidence of their signal.**

| Pillar | Current weight (article) | Pearson r vs accuracy |
|---|---:|---:|
| `semantic_html` | 25% (highest) | **−0.301** |
| `structured_data` | 20% | +0.036 |
| `content_extractability` | 20% | **+0.484** |
| `dom_navigability` | 15% | −0.189 |
| `metadata_completeness` | 10% | +0.224 |
| `http_compliance` | 10% | +0.242 |

The heaviest-weighted pillar (`semantic_html`, 25%) correlates *negatively* with retrieval accuracy. The pillar that should be heaviest (`content_extractability`, r = +0.484) is weighted at 20%. The next-heaviest (`structured_data`, 20%) carries no corpus-002 signal at all.

**Problem 3 — Scoring rewards declarations without measuring consumption.**

Clipper awards points in `metadata_completeness` for signals including site-level agent-discovery manifests (e.g. `llms.txt`-style files) that have no documented autonomous agent consumption and that do not scale to enterprise content corpora (e.g. Learn's ~20M pages across locales). A page author following Clipper's current guidance can add such signals without materially changing whether any agent actually retrieves the page. This makes Clipper's recommendations less trustworthy than they should be, and penalizes large documentation corpora for structural reasons unrelated to retrievability.

## 3. Clipper Goals & Objectives (Agentic Readiness)

**Primary goal:** Clipper should quantify agentic readiness — the probability that an AI agent, given a URL, retrieves content from that URL accurately enough to answer synthesis questions about it.

**Objectives that operationalize the goal:**

1. **Evidence-calibrated scoring.** Every pillar weight traces to a corpus-level correlation with measured retrieval accuracy, or to a structural argument (e.g. scalability) when evidence is not yet available.
2. **Multi-channel retrieval measurement.** Score accounts for the fact that an agent may retrieve a page via raw HTML, rendered HTML, content-negotiated markdown, or a served alternate. Differences between channels are surfaced, not hidden.
3. **Uncertainty transparency.** Scores are published with confidence ranges, not point values, whenever the underlying corpus does not support point precision. Known gaps are named explicitly in user-facing documentation.
4. **Content-type awareness.** Different content profiles (reference, tutorial, article, FAQ, landing, sample) have different retrievability constraints. Scoring acknowledges this via profile-specific weights once evidence supports them.
5. **Actionable recommendations.** For any page scored, Clipper should name the one or two interventions most likely to lift measured retrieval accuracy, not just the most-broken standards-compliance pillar.

**Non-objectives (stated positively here for clarity, restated as non-goals in §5):**

- Clipper is not a SEO tool.
- Clipper is not a WCAG auditor (even though WCAG pillars contribute signal).
- Clipper is not a schema.org validator.
- Clipper is not an opinionated style enforcer for markdown, heading structure, or link density.

## 4. Success Metrics

The v2 scoring update and Phase 6 experimental program succeed if, at the end of the roadmap:

### 4.1 Correlation metrics (primary)

| Metric | Current | v2 target | v3 target (post-corpus-003) |
|---|---:|---:|---:|
| Pearson r, composite score vs measured accuracy (n≥40) | −0.007 | **≥ +0.35** | ≥ +0.50 |
| Pearson r, top-signal pillar vs measured accuracy | +0.484 | ≥ +0.50 | ≥ +0.55 |
| Rendered-accuracy range across corpus (floor to ceiling) | 0.0–1.0 | preserve | preserve |

The v2 target is deliberately modest. The current composite is at r ≈ 0; even a correctly-weighted v2 model on the same 43-URL corpus should reach moderate correlation. r ≥ +0.50 is a post-held-out-corpus aspiration, not a v2 commitment.

### 4.2 Coverage metrics

- v2 detects page-level markdown alternates on ≥ 95% of pages that serve them, across the corpus-002 vendor set.
- v2 excludes from headline scoring every signal in the §3 known-gaps list.
- Documentation (`docs/scoring.md`) publishes every v2 pillar weight as a range with evidence citation, or explicitly marks the weight as a known gap.

### 4.3 Stability metrics

- Cross-judge κ ≥ 0.60 between the primary judge (Llama-3.3-70B) and each added judge in Phase 6 experiment 1, across ≥ 90% of pages.
- Temporal stability: re-running unchanged corpus-002 at T+30d produces per-page |Δaccuracy| ≤ 0.10 on ≥ 80% of pages, excluding pages with vendor-side content changes.

If any stability metric fails, v2 weight ranges must widen accordingly before external publication.

### 4.4 Qualitative

- Every recommendation Clipper surfaces to a page owner for a bottom-quartile page can be traced to a pillar with corpus-level evidence of retrieval impact.
- No recommendation reads like "add this standard because the standard says to" without a retrievability justification.

## 5. Non-Goals / Out of Scope

Explicitly **not** in scope for the v2 scoring update or Phase 6 program:

1. **Methodology publication as an external standard.** Deferred to post-corpus-003 minimum.
2. **Non-English or non-documentation content scoring.** Corpus-002 is English docs; v2 and Phase 6 stay in that scope. Broader generalization requires corpus-003.
3. **Real-time scoring for live agent traffic.** Clipper remains a batch corpus-level measurement tool, not an inline scorer.
4. **Agent-vendor behavioral telemetry.** Clipper cannot observe which agents actually fetch which URLs. Claims about specific agent behavior require external data sources that are not part of this roadmap.
5. **SEO scoring, ranking-factor scoring, or marketing-funnel optimization.** Out of scope in all phases.
6. **WCAG compliance as a headline goal.** WCAG signals remain as a pillar contribution where evidence supports their correlation with retrievability, but Clipper does not aspire to replace WCAG auditors.
7. **Schema.org or structured-data advocacy.** Structured data remains a pillar contribution where evidence supports it. Corpus-002 does not support a heavy weight.
8. **Site-level agent-discovery manifest scoring.** Detection retained as diagnostic; excluded from headline scoring per §2 Problem 3 and corpus-002 evidence.
9. **Point-value weight precision in v2.** v2 ships ranges, not point values. Point precision requires a held-out corpus.
10. **New pillar architecture (Fetch Integrity, Content Atomicity, Context Portability) in v2.** All new-pillar proposals defer to v3 pending Phase 6 evidence.

## 6. Jobs To Be Done / Scenarios

Five primary users, each with a JTBD the v2+Phase-6 work must serve:

### JTBD 1 — Documentation author auditing their own pages

**Scenario:** A technical writer at a SaaS company runs Clipper against their top 100 docs URLs. They receive per-page `universal_score`, a ranked list of weakest pillars, and a set of recommendations.

**Job:** "I need to know which of my pages are invisible to agents and what one intervention per page would most improve that, so I can prioritize my next sprint."

**v2 requirement implication:** Recommendations must be ranked by projected retrieval-lift, not by pillar-point-gap. A page with `semantic_html` at 40 and `content_extractability` at 85 should not be told to fix `semantic_html` first.

### JTBD 2 — Docs platform owner comparing vendor sites

**Scenario:** A platform team lead compares their documentation to three competitors' documentation across 50 URLs each. They want to know if their pages are more or less agent-retrievable and why.

**Job:** "I need a cross-vendor comparison that is not confounded by vendor size, template differences, or content-type mix."

**v2 requirement implication:** Reports must disclose per-page content profile, `universal_score` (not `parseability_score`) for cross-vendor headline deltas, and must acknowledge when competitor sets have asymmetric sizes. Built-in via existing `copilot-instructions.md` conventions.

### JTBD 3 — Clipper maintainer scoping v3

**Scenario:** A Clipper maintainer needs to decide which of three pillar-design proposals (Fetch Integrity, Content Atomicity, Context Portability) to prioritize for corpus-003.

**Job:** "I need Phase 6 evidence that tells me which proposed pillars carry signal, so corpus-003 design doesn't enshrine speculation."

**v2 requirement implication:** Phase 6 experiment outputs must be structured to feed directly into corpus-003 design decisions. Specifically, cross-judge κ and served-markdown A/B results must be published in a form usable for v3 pillar-design arguments.

### JTBD 4 — External reader evaluating Clipper's credibility

**Scenario:** A CTO or developer advocate encounters a Clipper report and wants to know whether to trust it.

**Job:** "I need to see evidence for every weight and every recommendation, in terms I can verify."

**v2 requirement implication:** `docs/scoring.md` must publish pillar weights with evidence citations and known-gaps disclosure. Findings documents must be linked from scoring docs.

### JTBD 5 — Agent-platform engineer integrating Clipper signals

**Scenario:** An engineer building an agent retrieval pipeline wants to use Clipper output to pre-rank URLs for their crawler.

**Job:** "I need structured scores I can consume programmatically, with uncertainty information attached."

**v2 requirement implication:** `universal_score` in `*_scores.json` must carry a confidence range, not just a point value, and the per-page JSON must expose which signals are diagnostics (unscored) vs. headline (scored).

## 7. Features and Requirements

Organized by roadmap session. Each requirement carries an evidence tier (E1 direct / E2 inferential / E3 structural / E4 speculative) and a confidence level.

### 7.1 Session 1 — Close Corpus-002

**F1.1 — Secret redaction in corpus-002 artifacts.** [E3, High]
Redact Stripe / AWS / GitHub / Slack secret patterns from `evaluation/phase5-results/corpus-002/` before any git commit. Apply the same regex-based rewrite used for corpus-001: `(sk_test|sk_live|pk_live|rk_live)_[A-Za-z0-9]+ → $1_REDACTED` across `*.html`, `*.txt`, `*.json`. Blocking for all downstream commits.

**F1.2 — Projected-correlation gate.** [E1, High]
Before v2 weight changes are implemented, re-weight existing corpus-002 pillar values with at least three candidate weight sets and compute Pearson r for each composite. Document the results in a short addendum. If no candidate set reaches r ≥ +0.35 against rendered accuracy, investigate before proceeding — the problem is deeper than weight choice.

**F1.3 — Commit findings + redacted artifacts.** [E3, High]
Two-commit sequence: (1) redacted corpus-002 artifacts; (2) `findings/phase-5-corpus-002-findings.md` + `findings/README.md`. Push.

### 7.2 Session 2 — v2 Scoring

**F2.1 — Pillar-subset headline composite in `retrievability/score.py`.** [E1, High]
*(Superseded during Session 1 γ experiments. Original scope: directional reweighting of all six pillars. New scope per findings Addendum B.)*

Headline `universal_score` is computed from **two pillars only**: `content_extractability` (weight 0.50) and `http_compliance` (weight 0.50). The remaining four pillars — `semantic_html`, `structured_data`, `dom_navigability`, `metadata_completeness` — are demoted to **diagnostic-only**: they continue to be evaluated, reported in the `component_scores` block, and surfaced in the author-facing report, but contribute **zero** weight to the headline score.

Rationale: corpus-002 γ experiments (`scripts/gamma-experiments.py`) show the 2-pillar equal-weighted composite reaches Pearson r = +0.548 against `accuracy_rendered`, versus r = −0.007 for v1 six-pillar weights and r = +0.315 for the best six-pillar reweighting (Addendum A Candidate D). Three of the six v1 pillars correlate negatively or near-zero on corpus-002; keeping them in the headline suppresses predictive value.

Profile-specific weights (`landing`, `reference`, `sample`, `faq`, `tutorial`) collapse to the same two-pillar composite for v2. Profile-aware reweighting is deferred to v3 (requires corpus-003 per-profile evidence).

The four demoted pillars remain first-class diagnostics. v2 headline claims only predict agent retrieval accuracy on the corpus-002 distribution; the diagnostic pillars still carry actionable findings for authors (accessibility, schema.org, semantic structure, metadata).

**F2.2 — Page-level markdown-alternate detection.** [E3, High]
Detect `<link rel="alternate" type="text/markdown">` in page `<head>`, presence of a `.md` sibling at predictable paths (`{url}.md`, `{url}/index.md`), and `text/markdown` availability via HEAD request with `Accept: text/markdown`. Record all three in the audit trail. **No scoring contribution in v2** — retrieval-lift evidence belongs to Phase 6.

**F2.3 — Remove site-level agent-discovery manifest points.** [E3, High]
Remove point contribution from `metadata_completeness` for site-level agent-manifest detection (e.g. `llms.txt`-style files). Keep detection as an audit-trail diagnostic. Document in `docs/scoring.md` with rationale referencing scalability asymmetry and absence of consumer evidence.

**F2.4 — Publish weights and demotions with evidence citations.** [E2, High]
`docs/scoring.md` must list each pillar with: current v2 weight (headline or `diagnostic-only`), evidence citation (corpus-002 single-pillar correlation from findings Addendum B §B.1, and γ experiment outcome), and confidence level. Note that `content_extractability` (r=+0.484) and `http_compliance` (r=+0.242) carry 0.50 each; the remaining four pillars are listed as diagnostic-only with their single-pillar correlations and the γ evidence for demotion.

**F2.5 — Add "Known Gaps" section to scoring docs.** [E3, High]
Enumerate in `docs/scoring.md`: served-markdown grading not yet measured, Fetch Integrity not yet a pillar, cross-agent variance not yet measured, four pillars demoted to diagnostic-only on corpus-002 evidence and pending re-evaluation in Phase 6 and corpus-003, profile-specific weights collapsed to the 2-pillar composite pending corpus-003.

**F2.6 — v2 regression check against corpus-002.** [E1, High]
Re-run corpus-002 through v2 scoring. Confirm `universal_score` Pearson r against `accuracy_rendered` reaches or exceeds +0.35. Expected value per findings Addendum B: r ≈ +0.548 for the `top2_equal` composite. If the re-run value drops below +0.35, investigate before shipping.

**F2.7 — Tag v2 release as `v2-evidence-partial`.** [E3, High]
Release tag must include the word "partial" to make explicit that the model ships on corpus-002 evidence alone without cross-judge, temporal, or held-out validation.

**F2.8 — Confidence range in `*_scores.json`.** [E3, Medium]
Add a `confidence_range` field to each per-page score object, populated from the v2 weight-range uncertainty. Format to be decided during implementation.

### 7.3 Session 3 — Phase 6 Experiment 1 (Cross-Judge Variance)

**F3.1 — Select 2 additional judges.** [E3, High]
Candidates: Claude-3.5-Sonnet, Gemini-1.5-Pro, GPT-4o, depending on Azure Foundry availability. Criteria: architectural diversity (avoid two OpenAI models), access availability, cost feasibility for 43-page re-grading.

**F3.2 — Re-grade corpus-002 through each added judge.** [E1, High] **— COMPLETE (Session 6)**
Reuse existing generated Q/A pairs. Do not regenerate. Three total judgment sets per page (primary + 2 added). Executed against Llama-3.3-70B (primary), GPT-4o, and DeepSeek-V3.2 — Sonnet/Gemini were unavailable on the deployment tenant; DeepSeek substituted for diversity. Mean accuracies: Llama 0.698, GPT-4o 0.595, DeepSeek 0.591. Per-page artifacts under `evaluation/phase5-results/corpus-002/<slug>/grades.{primary|gpt4o|deepseek}.judged.rendered.json`. See Addendum G of `findings/phase-5-corpus-002-findings.md`.

**F3.3 — Compute agreement statistics.** [E1, High] **— COMPLETE (Session 6)**
Produce per-page and overall κ for each judge pair. Also produce mean-accuracy differentials per judge and per vendor. Pooled κ: deepseek↔gpt4o = 0.817, deepseek↔primary = 0.761, gpt4o↔primary = 0.706 (all substantial-to-almost-perfect). See [`scripts/phase6-cross-judge-kappa.py`](../scripts/phase6-cross-judge-kappa.py) and `evaluation/phase5-results/corpus-002-analysis/cross-judge-kappa.json`.

**F3.4 — Publish CIs on corpus-002 accuracy.** [E1, High] **— COMPLETE (Session 6)**
Single-judge CIs published in Addendum D §D.4. Cross-judge CIs published in Addendum G §G.4: per-judge union [0.530, 0.758], majority-vote [0.567, 0.688]. See [`scripts/phase6-cross-judge-cis.py`](../scripts/phase6-cross-judge-cis.py).

**F3.5 — Adjust v2 weight ranges if κ < 0.60.** [E1, High] **— RESOLVED AS CAVEAT-AMENDMENT (Session 6)**
The “> 10% of pages with per-page κ < 0.60” trigger fired for all three pairs (29-39%). Because v2 ships as the coarse 50/50 composite (no fractional weights to widen), the trigger translates into a caveat amendment to `ScoreResult.confidence_range`: "cross-judge accuracy variance: per-judge corpus-002 means span 0.591-0.698; report majority-vote or per-judge union when comparing across studies." See Addendum G §G.5.

### 7.4 Session 4 — Phase 6 Experiment 2 (Tri-Fetcher Served-Markdown A/B)

**F4.1 — Extend dual-fetcher to tri-fetcher.** [E3, High]
In `retrievability/phase5/`, add a third fetcher path with resolution order: `Accept: text/markdown` content negotiation → `<link rel="alternate" type="text/markdown">` href → sibling `.md` path probe. Fall-through on each step. Record which path succeeded per page.

**F4.2 — Paired grading on vendors with markdown alternates.** [E3, High] **— COMPLETE (Session 4 + Session 5)**
For each page where the tri-fetcher succeeds on any markdown path, run the same harder-Q/A Q/A generation and grading pipeline against the markdown content. Produce paired `accuracy_html` and `accuracy_markdown` per page.

Execution notes:
- **Track A (Session 4):** Q/A generated from rendered HTML, graded against both rendered extract and served markdown. n=25, mean delta = −0.064. **Methodologically biased**: HTML-anchored Q/A penalizes markdown for content it legitimately omits.
- **Track B (Session 5, bias-corrected):** new module `retrievability/phase5/intersection.py` computes sentence-level content intersection of rendered extract and served markdown; Q/A generated from intersection text only. n=17 survivors of the 25 markdown-resolved pages (8 dropped on intersection < 1500 chars). **Mean delta = −0.012; 16/17 pages produced identical scores.**
- Track A − Track B = +0.052 = the size of the HTML-source bias removed.

**F4.3 — Publish served-markdown lift analysis.** [E1, High] **— COMPLETE (Session 5)**
Per-page delta, per-vendor delta, and overall delta. Include the null-result case explicitly if served-markdown does not provide lift — that is valuable evidence.

Published in:
- `findings/phase-5-corpus-002-findings.md` Addendum F (Sections F.2 / F.3 / F.6)
- `findings/phase-5/04-served-markdown-experiment.md` (focused topical doc)
- `findings/phase-5/05-token-efficiency.md` (companion non-LLM probe)
- Artifacts: `evaluation/phase5-results/corpus-002/<page>/intersection*.json`, `evaluation/phase5-results/corpus-002-analysis/intersection-lift.json`, `evaluation/phase5-results/corpus-002-analysis/token-efficiency.json`.

**F4.4 — v3 pillar-design input.** [E2, Medium] **— COMPLETE (Session 5): `keep_as_diagnostic_only`**
If the served-markdown lift is consistently > +0.10 on vendors that ship it, document a v3 recommendation to promote page-level markdown detection from a diagnostic to a pillar contribution.

Verdict: **`keep_as_diagnostic_only`**. Rule (mean lift > +0.10 AND ≥2 vendors above threshold) fails decisively under Track B (mean −0.012, no vendor positive). The bias-corrected null is a *positive finding of format equivalence* for in-context comprehension on this corpus, not a measurement failure. v3 is **not** authorized to promote served-markdown to a scored pillar on corpus-002 evidence.

A naïve binary "serves markdown" signal is also disauthorized: Stripe ships markdown 6.29× larger than its HTML→clean extract; AWS ships clamped markdown of unknown true size. Any future served-markdown signal must be *conditional* (`tokens(md) ≤ tokens(HTML→clean)` AND `content(md) ⊇ content(HTML→clean)`), not binary on presence.

The finding does not cover retrieval-mode (RAG); a Phase 7 retrieval-mode benchmark is the next gate for the served-markdown pillar question.

### 7.5 Session 5 — Temporal Replication

**F5.1 — T+30d re-run.** [E3, High]
Re-run corpus-002 unchanged 30 days after the original run. No code changes between runs. Publish page-level deltas.

**F5.2 — Flag content-changed pages.** [E3, High]
Before attributing score deltas to pipeline instability, detect vendor-side content changes (e.g. via rendered-HTML hash comparison) and exclude those pages from stability statistics.

**F5.3 — Update weight ranges if instability is significant.** [E1, High]
If > 20% of pages show |Δuniversal_score| > 10 points without content changes, v2 weight ranges widen before the next release.

### 7.6 Session 6 — Corpus-003 Design

**F6.1 — Balanced corpus composition.** [E2, High]
Target ~20 pages × 5 content-type profiles × 6 vendors (~600 URLs). Scope-down negotiable; 5 × 5 × 5 (~125 URLs) is an acceptable floor if 600 is infeasible.

**F6.2 — Include challenged-fetch pages.** [E3, High]
Include robots-blocked pages, Cloudflare-challenged pages, and pages with agent-specific user-agent allowlist variance. This is what lets a proposed Fetch Integrity pillar be evaluated.

**F6.3 — Run through v2 pipeline + tri-fetcher + multi-judge.** [E1, High]
All Session 3–4 infrastructure applies. Corpus-003 is graded with the full Phase 6 instrument, not the Phase 5 pilot.

### 7.7 Session 7 — v3 Scoring Design

Out of detailed scope for this PRD. Entry criterion: Session 6 complete. Exit criterion: a v3 pillar architecture with weights traceable to corpus-003 correlations, and a published methodology candidate-standard document.

## 8. Acceptance Criteria

Binary pass/fail criteria per session. Sessions do not ship until all their criteria are met.

### Session 1

- [ ] All corpus-002 artifacts free of unredacted secret patterns (grep returns zero matches for `(sk_test|sk_live|pk_live|rk_live)_[A-Za-z0-9]+`).
- [ ] F1.2 projected-correlation analysis produces at least one candidate weight set with Pearson r ≥ +0.35 on corpus-002 rendered accuracy.
- [ ] Two git commits pushed: redacted artifacts and findings doc.
- [ ] `findings/README.md` lists phase-5-corpus-002 findings and conventions.

### Session 2

- [ ] `retrievability/score.py` implements directional weight changes per F2.1.
- [ ] Detection logic for page-level markdown alternates lands in `retrievability/parse.py` (or equivalent) per F2.2, with audit-trail output but zero score contribution.
- [ ] Site-level agent-manifest point contribution is removed from `metadata_completeness` per F2.3.
- [ ] `docs/scoring.md` publishes all pillar weights as ranges with citations per F2.4.
- [ ] `docs/scoring.md` includes a "Known Gaps" section per F2.5.
- [ ] v2 regression on corpus-002 produces composite Pearson r ≥ +0.35 per F2.6.
- [ ] Release tagged with `v2-evidence-partial` (or similar) per F2.7.
- [ ] `*_scores.json` includes `confidence_range` field per F2.8.

### Session 3

- [x] At least 2 additional judges successfully grade 100% of corpus-002 pages. *(Session 6: GPT-4o + DeepSeek-V3.2, 43/43 pages each.)*
- [x] κ statistics computed and published per F3.3. *(Pooled κ 0.706 / 0.761 / 0.817; Addendum G §G.2.)*
- [x] 90% CIs added to vendor and overall accuracy numbers per F3.4. *(Single-judge: Addendum D §D.4. Cross-judge: Addendum G §G.4.)*
- [x] If κ < 0.60 on > 10% of pages, weight ranges widened per F3.5 before the next release. *(Trigger fired (29-39% of pages); resolved as caveat amendment to `ScoreResult.confidence_range` per Addendum G §G.5; no fractional v2 weights to widen.)*

### Session 4

- [ ] Tri-fetcher implemented with documented resolution order per F4.1.
- [x] ≥ 1 vendor from corpus-002 successfully produces paired `accuracy_html` and `accuracy_markdown` values per F4.2. *(Session 4: Track A on 25 pages × 9 vendors. Session 5: Track B intersection-Q/A on 17 pages × 8 vendors.)*
- [x] Lift analysis published per F4.3. *(Addendum F + `findings/phase-5/` directory.)*
- [x] v3 design input captured per F4.4, even if the result is a null finding. *(Verdict: `keep_as_diagnostic_only`; Phase 7 retrieval-mode benchmark is the next gate.)*

### Session 5

- [ ] T+30d re-run completes successfully per F5.1.
- [ ] Content-change detection applied per F5.2.
- [ ] Weight ranges updated if instability threshold is crossed per F5.3.

### Session 6

- [ ] Corpus-003 URL list finalized and published in `evaluation/`.
- [ ] Corpus-003 includes challenged-fetch pages per F6.2.
- [ ] Corpus-003 graded through v2 pipeline + tri-fetcher + multi-judge per F6.3.
- [ ] Corpus-003 findings doc published under `findings/`.

## 9. Order of Operations — Session Sequencing

Sessions are dependency-ordered, not time-boxed. A "session" is a working block with a clear entry and exit criterion.

### Block A: Close corpus-002 and ship v2

**Session 1 → Session 2 → Session 2 regression check.** Sequential, no parallelism. Session 1 unblocks everything. Session 2 cannot ship until F2.6 regression passes. If it fails, diagnose before proceeding — do not bypass.

### Block B: Phase 6 evidence experiments

**Session 3 and Session 4 are independent** and can run in parallel if capacity allows. If not, Session 3 (cross-judge) is prioritized because:
1. It retrospectively re-grades corpus-002 without new fetcher infrastructure.
2. Its output (CIs on accuracy) directly constrains v2 weight-range publication.
3. It is cheap: ~1 week of compute vs. ~2–3 weeks for Session 4.

Session 4 (tri-fetcher served-markdown A/B) follows. Its output informs v3 pillar architecture.

### Block C: Stability and generalization

**Session 5** triggers passively at T+30d from corpus-002 original run. It can overlap with Block B.

**Session 6 (corpus-003)** requires both Session 3 and Session 4 complete. It is the largest-effort session and is the gate for Session 7.

### Block D: v3 design

**Session 7** requires Session 6 complete. Not scoped in detail in this PRD; entry criteria are the exit criteria of Session 6.

### Visual summary

```
Session 1 (redact + findings)
    ↓
Session 2 (v2 scoring)
    ↓
Session 2 regression check
    ↓
    ├── Session 3 (cross-judge) ──┐
    │                              │
    ├── Session 4 (tri-fetcher) ───┤
    │                              │
    └── Session 5 (T+30d) ─────────┤
                                   ↓
                            Session 6 (corpus-003)
                                   ↓
                            Session 7 (v3 design)
```

### Immediate next action

Session 1, Step 1: secret redaction in `evaluation/phase5-results/corpus-002/`. Mechanical, unblocks all downstream commits, requires no pending decisions.

---

## Appendix A — Decisions Still Open

Listed here to force explicit closure rather than leaving them implicit in implementation:

- **D1** — v2 weight publication format: ranges vs. directional-only language? *Current recommendation: ranges with evidence citations.*
- **D2** — `structured_data` pillar: down-weight to 10% or remove entirely? *Current recommendation: down-weight; preserve for content types where it may still matter.*
- **D3** — Page-level markdown-alternate check placement: sub-signal inside `content_extractability`, own pillar, or diagnostic-only? *Current recommendation: diagnostic-only for v2; promote post-Session 4 if evidence supports.*
- **D4** — Phase 6 ordering: cross-judge first or tri-fetcher first? *Current recommendation: cross-judge first per §9 Block B reasoning.*
- **D5** — Phase 6 corpus: reuse corpus-002 for both experiments, or build corpus-003 first? *Current recommendation: reuse corpus-002; don't confound new instrument with new content.*
- **D6** — v2 ship-blocking: does Phase 6 block v2 or does v2 ship on corpus-002 alone? *Current recommendation: v2 ships on corpus-002 as partial; v3 waits.*
- **D7** — Six-pillar v3 architecture proposal (Fetch Integrity, Content Density, Content Atomicity, Information Fidelity, Context Portability, Factual Addressability): adopt, reject, or hold open? *Current recommendation: hold open; Phase 6 evidence confirms or refutes.*
- **D8** — Dual-score split (`parseability_score` + `universal_score`): keep or collapse? *Current recommendation: keep; corpus-002 reinforces profile-specific weights will exist.*
- **D9** — External methodology publication: publish v2 as a standard candidate, or wait? *Current recommendation: wait for corpus-003 minimum.*

Open decisions are decided during the session they block. Recording them here so they cannot be implicitly resolved by implementation choice.

## Appendix B — Evidence Tier and Confidence Glossary

**Evidence tiers:**
- **E1 — Direct**: corpus-002 statistical result supports the claim (correlation computed, significance computed where n permits).
- **E2 — Inferential**: corpus-002 shows a gap or ceiling the claim addresses, but the claim itself is not directly tested.
- **E3 — Structural**: argument from architecture, scalability, or known external facts; not from corpus-002.
- **E4 — Speculative**: plausible but untested. Not used to justify shipping changes.

**Confidence levels:**
- **High**: directionally certain; magnitude may vary.
- **Medium**: direction probable; magnitude unknown.
- **Low**: may or may not hold; needs a test before shipping.

## Appendix C — Traceability Matrix (Evidence → Feature)

| Feature | Evidence source | Section |
|---|---|---|
| F2.1 directional weight update | Corpus-002 pillar correlations | findings §6.3, §8.1 |
| F2.2 markdown-alternate detection | Structural (scalability) | findings §7.4, §8.2 |
| F2.3 remove site-manifest points | Structural (consumer evidence absent) | findings §8.3 |
| F2.4 ranges-with-citations | Composite r ≈ 0 | findings §6.2 |
| F2.5 known gaps | All of §11 findings doc | findings §11 |
| F2.6 v2 regression | Projected r ≥ +0.35 | §4.1 success metrics |
| F3.x cross-judge | Single-judge architecture limitation | findings §11 |
| F4.x tri-fetcher | Served-markdown gap | findings §7.4 |
| F5.x temporal | Single-timepoint limitation | findings §11 |
| F6.x corpus-003 | Profile n too small, vendor mix imbalanced | findings §6.4–6.5 |
