# Clipper-next — Design Sketch (Session 11 Input)

**Status:** Draft for Session 11 decision-making. Not yet committed direction.
**Author:** Session 9.5, April 28, 2026
**Depends on:** [findings/post-v2-roadmap.md](post-v2-roadmap.md) §10 (load-bearing literature anchors), Session 9 / 9.5 corpus-003 result.
**Companion to:** [findings/v2.1-release-scope.md](v2.1-release-scope.md) (the honest-re-labeling release that ships v2 as-is while Clipper-next is designed).

---

## 0. What this document is — and isn't

This is a **design sketch**, not a spec. Its purpose is to convert Section 10.3's six "implications to evaluate" from prose into a structured set of decisions Session 11 can take, reject, or amend. Every numbered decision below is a fork in the road; each fork has a **default recommendation**, the **alternatives** considered, and the **evidence** that pushes one way or the other.

It is explicitly **not**:
- A commitment to ship anything.
- A promise about timelines.
- A claim that Clipper-next solves Clipper v2's generalization failure — that's the hypothesis to test, not the result.

If, at the end of Session 11, the conclusion is "Clipper-next isn't the right shape and we need a different rewrite," this document has done its job.

---

## 1. Premise

v2's headline composite (`parseability_score`, `universal_score`) does not generalize from corpus-002 to corpus-003 — Pearson r vs. judged QA accuracy ≈ +0.10 on corpus-003 (n=172) against a ship gate of r ≥ +0.35. The per-pillar measurements (semantic HTML, Schema.org, axe-core a11y, Readability, RFC 7231, metadata) remain real signals against published standards, but the weighted combination of them does not predict the outcome it was tuned to predict on the held-out set.

Three diagnoses are consistent with this result:

1. **Wrong outcome variable.** Reader-comprehension QA accuracy may simply not correlate with HTML structural quality at any defensible scale. This is the harshest interpretation but the one most consistent with [Section 10 / L3](post-v2-roadmap.md#10-external-literature-anchors) (verifiability) — generative-search engines themselves only support ~50% of their claims, so the upstream signal is noisy regardless of page structure.
2. **Wrong unit of analysis.** Even if the outcome is right, scoring whole pages obscures the part of the page that retrieval actually uses. [L1 (Lost in the Middle)](post-v2-roadmap.md#10-external-literature-anchors) argues that LM attention is non-uniform; first-N tokens dominate. A page-level structural score averages over a unit that doesn't matter.
3. **Wrong absence of confound controls.** [L4 (Webis)](post-v2-roadmap.md#10-external-literature-anchors) shows SEO-optimized content is over-represented in retrieval baselines; structural quality covaries with SEO investment, which covaries with retrieval visibility, regardless of structure causing visibility. A real signal can be invisible behind an SEO-driven confound — or a fake one can hide there masquerading as real.

Clipper-next does not try to relitigate v2's failure. It treats the failure as a finding, accepts the three diagnoses above as orthogonal, and structures the rewrite to address each one separately so we can tell which (if any) was the binding constraint.

---

## 2. Three tracks (mapped from roadmap §10.3)

Clipper-next is structured as three measurement tracks, each producing its own report and metrics. They are **deliberately not combined into a single composite**; per [L8 (HELM)](post-v2-roadmap.md#10-external-literature-anchors), a multi-metric harness is the defensible state for an evaluation tool that does not have validated weights.

### Track A — Citation-share DV
**Maps to roadmap §10.3 #1 (outcome reframe), #2 (sub-page unit), #6 (GEO ceiling).**

The primary outcome variable is **whether (and where in) a page is cited when an AI search system answers a relevant prompt**. This replaces reader-comprehension QA accuracy as the headline DV. Rationale: it's the outcome both [L2 (GEO)](post-v2-roadmap.md#10-external-literature-anchors) and [P1 (Semrush)](post-v2-roadmap.md#10-external-literature-anchors) measure at scale, and it's commercially actionable in a way comprehension is not.

### Track B — Groundedness diagnostic
**Maps to roadmap §10.3 #3 (groundedness as a separate axis).**

Independent of citation-share, measure how well a page **supports** the claim it gets cited for. [L3 (verifiability)](post-v2-roadmap.md#10-external-literature-anchors) shows production AI search engines fail at attribution roughly half the time; the question is whether structural properties of the *cited page* (not the citing engine) predict attribution success. [L7 (KILT)](post-v2-roadmap.md#10-external-literature-anchors) provides the methodological template: provenance evaluation against a labeled span.

A page can be highly cited but poorly grounding (Track A high, Track B low) or rarely cited but well-grounding when it is (Track A low, Track B high). These are different desiderata; they should not be combined.

### Track C — Confound controls (methodology, not a track per se)
**Maps to roadmap §10.3 #5 (SEO confound).**

Every Track A or B finding must be reported with at least one SEO-investment proxy controlled or stratified. This isn't a separate measurement Clipper-next produces; it's a methodological requirement that gates how Track A/B results are reported.

### What's NOT a track
**The six v2 pillars survive as diagnostic features, not as report sections.** Semantic HTML, Schema.org, axe-core a11y, Readability extractability, metadata completeness, HTTP compliance — these continue to be measured (the code already exists; it works) and they're available as independent variables in any Track A/B regression. They just aren't a standalone "structural quality" report anymore. Section 5 below states this explicitly.

---

## 3. Track A — open decisions

### A.1 Where do we get cited-URL data?

| Option | Pros | Cons | Recommendation |
|---|---|---|---|
| **A.1.a — GEO-bench (L2 dataset, public)** | Already published, peer-reviewed, replicable. | Domain-specific (the L2 paper notes this). May not generalize past the queries it was built for. ~10k prompts; small for our purposes. | **Default starting point.** Replicates L2's results before extending. |
| A.1.b — Build our own corpus | Full control over query distribution, page mix, vendor balance. | Months of data engineering. Vendor TOS questions for Perplexity/Bing/etc. Per-query cost scales linearly. | Defer until A.1.a is exhausted. |
| A.1.c — License from Semrush | Largest sample (P1: 11,882 prompts × 304k cited URLs). | Practitioner study, not peer-reviewed. License negotiation. Vendor lock-in. | Decline. P1 is a citation in our roadmap, not an input to our methodology. |
| A.1.d — Hybrid | Use GEO-bench for replication; build a minimal extension corpus for any Microsoft-relevant slice. | More work than A.1.a alone. | Reasonable Session 12+ extension. |

**Decision needed at Session 11:** A.1.a or A.1.d?

### A.2 Which "AI search system" produces the citations?

This is the highest-leverage and highest-risk decision in Track A. Different systems will surface different URLs for the same prompt; the choice changes everything downstream.

| Option | Pros | Cons |
|---|---|---|
| **A.2.a — Perplexity API** | Public API, citation metadata in response. Most comparable to L2/P1's setup. | TOS scrutiny for systematic measurement. Single-vendor signal. |
| A.2.b — Bing Copilot / Microsoft Copilot | Largest user base in our institutional context. Aligns with Microsoft Learn use cases. | API access for systematic citation measurement is unclear. Possible asymmetric advantage to Microsoft properties (confound). |
| A.2.c — Self-hosted RAG harness | Full reproducibility. No vendor TOS. We control everything. | Builds a model of "AI search," not "AI search as users experience it." Findings may not generalize past our harness. |
| A.2.d — Multi-vendor (n ≥ 3) | Findings that hold across vendors are far more defensible. Aligns with L4's methodology (Google/Bing/DDG comparison). | 3× the data engineering, 3× the cost. |

**Recommendation:** A.2.d as the eventual target, A.2.a as the bootstrapping default. Single-vendor results published only as "Perplexity-specific findings, multi-vendor replication pending."

**Decision needed at Session 11:** Bootstrap with A.2.a, or wait until A.2.d is feasible?

### A.3 Sub-page unit

Per [L1](post-v2-roadmap.md#10-external-literature-anchors) and [L6 (MS MARCO)](post-v2-roadmap.md#10-external-literature-anchors), the unit of analysis should be sub-page. Two candidates:

| Option | Definition | Notes |
|---|---|---|
| **A.3.a — First-N tokens** | The first 512 / 1024 / 2048 tokens of cleaned, extracted page text. | Aligns most directly with L1. Simplest to implement; v2's `parse.py` already produces this signal. |
| A.3.b — Per-section / per-passage | Page broken into sections by `<h2>` boundaries (or similar); each section scored independently. | Aligns with L6 / KILT-style evaluation. Better matches how RAG actually retrieves. More implementation surface. |
| A.3.c — Both | Report both unit definitions; let consumers pick. | HELM-style. Most honest. Most reporting surface. |

**Recommendation:** A.3.c. We have the data either way; emitting both is cheap and lets the eventual user (or analysis) pick the right unit per question.

**Decision needed at Session 11:** Confirm A.3.c or constrain to A.3.a / A.3.b?

### A.4 Track A's reportable outputs

Per page (or per sub-page unit), Track A produces:

- **Citation count** — how many of the N relevant prompts caused this URL to be cited.
- **Citation rank** — when cited, what position in the citation list (proxy for engine confidence).
- **Sub-page citation locality** — when L1's hypothesis is in scope, where in the page the cited content lives (first 512 tokens? last 25%? scattered?).

These are descriptive statistics, not a score. There is no Track A composite. Combining them is up to whoever consumes the data.

---

## 4. Track B — open decisions

### B.1 What does "groundedness" mean concretely?

[L3](post-v2-roadmap.md#10-external-literature-anchors) defines two failure modes for AI-search citations:

1. **Citation-precision failure** — the citation does not support the sentence it's attached to (~25% of citations in L3's evaluation).
2. **Sentence-recall failure** — the sentence is not supported by *any* citation in the response (~50% of sentences in L3's evaluation).

Track B's question is whether **structural properties of the cited page** predict either rate. Specifically:

- **B.1.a — Span-level support.** Given a cited page and a citing sentence, is there a span on the page that entails the sentence? (Adapted from L7's provenance task.)
- **B.1.b — Self-containment.** Can the cited span stand alone, or does it depend on context elsewhere in the document? (Adapts the corpus-002 "self-contained" notion that became Phase 6 work.)

**Recommendation:** B.1.a is the binding question. B.1.b is a feature derived from the page's structure, not an outcome — keep it as a Track A independent variable.

### B.2 What's the corpus?

Track B's corpus is a **subset of Track A's**: prompt → response → cited URLs. We need the *citing sentences* not just the citation list. Most AI search systems return that.

The bottleneck is labeled spans for ground-truth evaluation. Three approaches:

- **B.2.a — Auto-grade with an LLM-judge** (Phase 5 pattern). Cheap, scales. Judge bias is a real risk, but the approach is well-tested in Clipper.
- **B.2.b — Human label a small subset** (n=100–500 spans). Defensible, slow, expensive.
- **B.2.c — KILT's published gold spans** for any Wikipedia subset of Track A's URLs. Free, peer-reviewed, but limited coverage.

**Recommendation:** Hybrid. C.2.c where Wikipedia URLs are in the corpus (rare for production AI search, but happens). B.2.a for everything else, validated against a B.2.b subsample to bound judge bias.

**Decision needed at Session 11:** Confirm hybrid, or commit to B.2.a only as a Phase-1 simplification?

---

## 5. Disposition of v2's pillars

| Pillar | v2 weight | Clipper-next disposition | Rationale |
|---|---|---|---|
| Semantic HTML | 0% (diagnostic) | Diagnostic feature; candidate IV in Track A regression. | Already 0% in v2 headline. Preserve as feature for Track A, drop the standalone "score." |
| Content Extractability | 50% | Diagnostic feature; **strong candidate IV** for Track A and B. | Highest single-pillar correlation in corpus-002 (+0.484); collapses to +0.07 on corpus-003. Keep as feature, not as a standalone signal. |
| Structured Data | 0% (diagnostic) | Diagnostic feature; candidate IV. | corpus-003 r = -0.07; weak signal but cheap to compute, keep as feature. |
| DOM Navigability (axe-core) | 0% (diagnostic) | **Separate accessibility report**, not a Clipper-next feature. | WCAG accessibility is a worthy signal *for accessibility*; pretending it predicts AI-citation behavior was always speculative. Spin out as `clipper a11y` subcommand or similar. |
| Metadata Completeness | 0% (diagnostic) | Diagnostic feature; candidate IV. | Phase 4.4's `ms.topic` neutrality fix preserved. Keep feature, drop the score. |
| HTTP Compliance | 50% | Diagnostic feature; **rename pillar**. | "RFC 7231 compliance" is overstated for what we measure (mostly: status codes, redirects, cache headers, robots.txt, agent content hints). Rename to "agent-content-hints" or similar; keep as feature. |

**Universal score retires.** The default-article-weight composite was designed to enable cross-vendor comparison; that need is replaced by Track A's citation-share, which is naturally cross-vendor by construction.

**`parseability_score` is retired in Clipper-next** but kept available for back-compat under a v2-compat flag during the deprecation window. Recommend a 6-month deprecation aligned with semver `2.x → 3.0` boundary.

---

## 6. Output schema (HELM-style, no composite)

Clipper-next emits a per-URL JSON like:

```json
{
  "url": "https://example.com/docs/page",
  "scoring_version": "v3-tracks",

  "track_a": {
    "citation_count": 7,
    "citation_rank_mean": 2.3,
    "citation_locality": {
      "tokens_0_512": 4,
      "tokens_512_2048": 2,
      "tokens_2048_plus": 1
    }
  },

  "track_b": {
    "spans_evaluated": 7,
    "span_support_rate": 0.71,
    "judge": "deepseek-v3.2"
  },

  "diagnostic_features": {
    "semantic_html_score": 72.7,
    "content_extractability_score": 92.7,
    "structured_data_score": 12.0,
    "metadata_completeness_score": 100.0,
    "agent_content_hints_score": 77.8,
    "v2_compat": {
      "parseability_score_for_back_compat_only": 65.6
    }
  },

  "confound_proxies": {
    "domain_age_years": 9.2,
    "estimated_backlink_density": null,
    "ms_topic_present": true
  },

  "methodology": {
    "scoring_version": "v3-tracks",
    "no_composite": true,
    "see": "findings/clipper-next-design.md"
  }
}
```

Three properties of this schema are load-bearing:

1. **No top-level score.** Even Track A and Track B don't roll up to a "Clipper-next score." [HELM](post-v2-roadmap.md#10-external-literature-anchors) is the precedent: they explicitly argue against composite metrics for multi-objective evaluation.
2. **`v2_compat` is a leaf, not a peer.** It's there only for the deprecation window.
3. **`confound_proxies` is mandatory.** Track C's discipline shows up in every output, not just in published reports.

---

## 7. What Clipper-next is NOT

To prevent scope creep at Session 11:

- ❌ It is **not** a redesign of v2's pillars. The pillar measurements continue working; what changes is what we report from them and how we frame their relationship to the headline.
- ❌ It is **not** a model-graded scoring system. Track B uses LLM judges (Phase 5 pattern); Track A uses citation counts from real AI search systems. Neither is "ask GPT-4 if this page is good."
- ❌ It is **not** a citation-driven SEO tool. The L4 confound controls are non-negotiable; we don't ship "raise this number to be cited more" as a recommendation without controlled evidence.
- ❌ It is **not** a competitor benchmark / leaderboard. The rendered-vs-raw misunderstandings around v2 (see roadmap §1) are warning enough.

---

## 8. Ship gates for Clipper-next

Borrowing v2's discipline: a Clipper-next "v3" can ship only when:

- **G1 — Track A non-degeneracy.** At least one structural diagnostic feature predicts Track A citation count with Pearson r ≥ +0.20 on a held-out corpus, controlled for at least one Track C confound proxy.
- **G2 — Track B non-degeneracy.** Track B span-support evaluation produces > 0 measurable variance across pages (i.e., not every page scores 0.50, the L3 baseline).
- **G3 — Cross-vendor stability.** Track A results computed under at least two different "AI search system" choices (per A.2) agree on rankings at Spearman ρ ≥ +0.50.
- **G4 — Track C published.** Every shipped finding includes at least one confound proxy stratification or control.

These are deliberately stricter than v2's gates — v2 shipped on G1-equivalent (corpus-002 r = +0.62) without G3 or G4. The corpus-003 result is the cost of having shipped without those.

---

## 9. Sequencing — possible Session 11+ phase plan

Numbered for reference; **no time estimates**, since the dataset / vendor decisions in §3 are size-of-effort gates.

- **Phase A0 — Decide §3 / §4 forks at Session 11.** Output: this doc, amended with selected paths.
- **Phase A1 — Bootstrap Track A on GEO-bench / Perplexity** (per A.1.a + A.2.a). Produce first cross-section of citation-share data; validate against L2's published numbers.
- **Phase A2 — Sub-page unit Track A.** Re-run A1 with first-N-tokens / per-section units; check L1's hypothesis.
- **Phase B1 — Track B span-support** on a subset of A1's cited URLs (B.2.a hybrid).
- **Phase A3 — Cross-vendor extension** (A.2.d). G3 ship gate.
- **Phase C — Confound proxies operationalized.** SEO-investment proxy candidates evaluated, picked, integrated. G4 ship gate.
- **Phase v3.0 — Ship.** All four gates passed.

Phases A1, A2, and B1 can run partially in parallel.

---

## 10. Open questions for Session 11

1. **§3.A.1** — GEO-bench only, or hybrid with our own extension corpus?
2. **§3.A.2** — Bootstrap on Perplexity API, or wait for multi-vendor?
3. **§3.A.3** — First-N tokens, per-section, or both?
4. **§4.B.1** — Both span-precision and span-recall, or just one?
5. **§4.B.2** — Pure LLM-judge, hybrid with human, or hybrid with KILT?
6. **§5** — Spin out the WCAG / axe-core work as a separate `clipper a11y` tool, or fold it into Clipper-next as a non-Track diagnostic?
7. **§7** — Is "no composite" tenable for non-research users? Or do we need a single number for executive consumption with all the caveats Clipper v2.1 already publishes?
8. **§8** — Are these gates the right ones, or are we still missing something v2's failure has taught us?

These eight questions are the agenda for Session 11. Answering all of them produces a Clipper-next PRD; answering some of them and deferring others is also a legitimate outcome.

---

## 11. What this design does NOT solve

Honesty about limits, before Session 11 raises them:

- **Vendor TOS for systematic citation measurement is unsolved.** A1's bootstrap depends on whether Perplexity's API permits the volume of queries Track A needs. If it doesn't, A.2.c (self-hosted RAG) becomes the default and the findings get a much bigger asterisk.
- **Track A data is non-stationary.** AI search systems update their retrieval behavior continuously. Any Track A result is a snapshot; longitudinal stability is itself a separate measurement we haven't scoped.
- **The confound space is large.** SEO investment is one confound; domain trust, recency, backlink graph, topical authority — each of these covaries with "structural quality" in ways we cannot fully control. Track C is a discipline, not a solution.
- **Reader-comprehension is not abandoned, just demoted.** v2's QA-accuracy DV is still computable on any Clipper-next corpus; it becomes a secondary outcome alongside Track A. If Track A and reader-accuracy diverge sharply on a page, that's interesting, not a methodology failure.

---

## 12. Cross-references

- [findings/post-v2-roadmap.md](post-v2-roadmap.md) §10 — verified literature anchors.
- [findings/v2.1-release-scope.md](v2.1-release-scope.md) — what ships in the meantime.
- [findings/phase-5-corpus-002-findings.md](phase-5-corpus-002-findings.md) — the corpus that v2 was tuned on.
- [evaluation/phase5-results/corpus-003-analysis/session-9-report.md](../evaluation/phase5-results/corpus-003-analysis/session-9-report.md) — the corpus-003 generalization failure.
- [docs/scoring.md](../docs/scoring.md) — v2 scoring documentation; Clipper-next will need a parallel doc.
