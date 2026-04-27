# 07 — Recommendations & next steps

> **Key point.** Corpus-002 authorizes one structural scoring change (v2: two-pillar headline, four diagnostic), one detection-only addition (page-level markdown-alternate), one removal from headline scoring (site-level agent manifests), and a defined Phase 6 / Phase 7 / corpus-003 work plan.

This document distills the actionable list. Underlying evidence sits in [01-headline-results.md](01-headline-results.md) through [05-token-efficiency.md](05-token-efficiency.md); guardrails sit in [03-judge-confidence-intervals.md](03-judge-confidence-intervals.md) and [06-what-this-does-not-support.md](06-what-this-does-not-support.md).

---

## v2 — what corpus-002 authorizes shipping

### Headline composite

| Pillar | v2 weight | Rationale |
|---|---:|---|
| `content_extractability` | **0.50** | Single-pillar r = +0.484 (only strong positive signal). |
| `http_compliance` | **0.50** | Single-pillar r = +0.242 (positive, with `agent_content_hints` removed). |
| `semantic_html` | 0.00 (diagnostic) | Single-pillar r = −0.301 on corpus-002. |
| `structured_data` | 0.00 (diagnostic) | Single-pillar r = +0.036 (no signal). |
| `dom_navigability` | 0.00 (diagnostic) | Single-pillar r = −0.189. |
| `metadata_completeness` | 0.00 (diagnostic) | Single-pillar r = +0.224, not significant at n=43. |

Live regression on the shipping code: **r = +0.618** vs `accuracy_rendered`. Above the +0.35 ship gate.

### Surface and tagging

- Publish v2 weights as a **headline composite + diagnostic-only** structure. Diagnostic pillars continue to be measured and reported.
- Tag the release `v2-evidence-partial` with disclosure that the evidence base is one corpus, single-grader architecture.
- Document the four-pillar demotion as "evidence-driven, not permanent" — restoration requires a corpus that shows retrieval-relevance.
- In the report: surface the per-page `tokens(markdown) / tokens(readability)` ratio when markdown is served, as a non-scored diagnostic.

### Detection-only additions

- **Page-level markdown-alternate detection.** Detect `<link rel="alternate" type="text/markdown">` and presence of a sibling `.md` at a predictable path. Report in the audit trail. **No scoring contribution** until Phase 7 validates retrieval-mode lift.

### Removed from headline scoring

- **Site-level agent-discovery conventions** (`llms.txt` and similar manifests). Keep detection in the audit trail. Remove from `universal_score`. Rationale: no evidence of autonomous agent consumption; the structural scalability problem (e.g. Learn's ~20M pages across locales) makes awarding points a docs-team-size proxy, not a retrievability proxy.
- **`agent_content_hints` as a sub-component of `http_compliance`.** Demoted to diagnostic. This sub-demotion is what raises v2's regression from +0.548 (γ projection) to +0.618 (live).

---

## Phase 6 work that gates further changes

| ID | Work | Gates |
|---|---|---|
| F3.2 | ~~Cross-judge re-grading with 2 additional judges~~ **Landed Session 6 (Addendum G).** Three-judge panel: Llama-3.3-70B + GPT-4o + DeepSeek-V3.2. Pooled κ 0.706 / 0.761 / 0.817 (substantial-to-almost-perfect). Union 90% CI on corpus-002 widened from [0.633, 0.758] (single-judge) to [0.530, 0.758] (cross-judge union) / [0.567, 0.688] (majority-vote). | Done. |
| F3.5 | Weight-range widening based on cross-judge κ | Conditional on F3.2. Currently no fractional-weight claim to widen (50/50 is coarse). |
| F4.4 | Promote/demote decision for served-markdown lift | **Settled in Session 5: `keep_as_diagnostic_only`** (Track B null). |
| Session 5 (T+30d) | Temporal replication of corpus-002 | Page-level \|Δ\| > 0.10 without content changes widens v2 weight ranges. |

---

## Phase 7 (proposed)

### Retrieval-mode benchmark

The "markdown is agent-friendly" claim is most likely to be quantitatively true in a retrieval-mode setting. Corpus-002 cannot reach this regime. Phase 7 proposal:

- Chunk both formats with a standard splitter.
- Embed chunks, retrieve top-k for held-out questions.
- Grade with the same judge architecture.

This would produce the first direct evidence on whether served markdown improves retriever recall, chunk fidelity, or grade — none of which are visible to in-context paired grading.

### Token-efficiency diagnostic in standard reports

Surface `tokens(markdown) / tokens(readability_extract)` per page as an unweighted observability signal. No scoring impact. Reader benefit: publishers learn whether their markdown export is leaner or more bloated than their HTML, which is actionable feedback the current pillars don't surface.

---

## Corpus-003 design (deferred)

Required for v3 design. Corpus-002 cannot supply:

- **Profile-specific weight evidence.** Need ≥10 pages per profile.
- **Per-vendor template-quality claims.** Need n≥5 per vendor and matched profiles across vendors.
- **Robots-blocked / challenged page handling.** Add ≥5 pages per category.
- **Non-developer-documentation content.** Add a sample beyond the current 14-vendor doc-site corpus.

Target shape: 5 content-type profiles × 6 vendors × ≥3 pages each, plus a robots-blocked/challenged category. Total ~100–120 pages.

---

## Editorial / process recommendations

These are not scoring changes but they protect the scoring credibility:

- **Every Clipper report quoting corpus-002 numbers must include the 90% CI.** Means alone are not publishable.
- **Cross-vendor reports must follow the rules** in [03-judge-confidence-intervals.md](03-judge-confidence-intervals.md): use `universal_score`, disclose per-page profile + detection source, match sample sizes, do not mix exemplars into competitor averages, project symmetric fixes.
- **Findings in this directory are summaries.** Audit-trail evidence sits in [phase-5-corpus-002-findings.md](../phase-5-corpus-002-findings.md). Reviewers should land there, not here.
- **Phase 4.4 (metadata-pillar `ms.topic` neutrality) landed** in commit `3c71ce2` (April 22 2026). corpus-002 scores captured on or after April 23 2026 already reflect the fix; pre-fix Learn metadata numbers are not directly comparable. The corpus-002 `metadata_completeness` correlation (r=+0.224) was computed post-fix and stands.

---

## Concrete next-action checklist

- [ ] Update `findings/v2-scoring-phase6-roadmap-prd.md` F4.4 entry to `keep_as_diagnostic_only` with the Track B evidence.
- [ ] Commit Session 5 artifacts: intersection module + tests, runner + CLI changes, three new analyzer scripts, Addendum F, this directory, PRD update.
- [ ] When F3.2 deployments are approved, run cross-judge re-grading and tighten the published CIs.
- [ ] Schedule T+30d temporal replication.
- [ ] Open a Phase 7 design document for retrieval-mode benchmark.
- [ ] Open a corpus-003 design document with the shape above.
