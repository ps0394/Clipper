# Phase 5 — Corpus-002 Findings (Index)

This directory packages the corpus-002 findings as focused topical documents, each reinforcing one or two key points with the evidence behind them. The canonical, full-length source — including raw addenda and per-page tables — is [phase-5-corpus-002-findings.md](../phase-5-corpus-002-findings.md).

**Read the source for full evidence and audit trail. Read this directory to understand what corpus-002 actually decided.**

---

## TL;DR — six things corpus-002 settled

1. **Clipper's v1 composite did not predict agent retrieval accuracy.** Pearson r ≈ 0 against measured accuracy at n=43 on a harder-Q/A task. The headline number was not measuring what it claimed to measure.
2. **The pillars are not uniformly broken; the weights were.** `content_extractability` correlates strongly positive (r=+0.484); `semantic_html` correlates *negatively* (r=−0.301); `structured_data` is signal-free (r=+0.036).
3. **v2 is a structural change, not a re-weighting.** The shipping v2 composite uses two pillars (`content_extractability` + `http_compliance`, equally weighted) and demotes the other four to diagnostic-only. Live regression on corpus-002: r = **+0.618**.
4. **Served markdown does not improve in-context comprehension on this corpus.** A bias-corrected paired grading test (Track B, n=17) returned a mean delta of **−0.012**, with 16 of 17 pages producing identical scores. Format-equivalence under fair test.
5. **The "markdown is more token-efficient" claim is false against a clean readability extraction.** Median served markdown is **1.39× larger** than a Readability extract on corpus-002. The ~50× HTML→text reduction comes from cleaning, not from format choice.
6. **Confidence intervals matter.** Overall accuracy is 0.698 with a 90% CI of [0.633, 0.758]. Per-vendor intervals are wide enough that almost no two vendors separate at 90% confidence. Cross-vendor claims without published intervals are a methodology error.

---

## Documents in this directory

| # | File | Reinforces |
|---|---|---|
| 01 | [01-headline-results.md](01-headline-results.md) | The ceiling broke; composite r ≈ 0; pillar-level correlations show *which* pillars carry signal. |
| 02 | [02-v2-scoring-decision.md](02-v2-scoring-decision.md) | The path from "re-weighting fails" → "two-pillar subset ships at r=+0.618"; why v2 is structural, not cosmetic. |
| 03 | [03-judge-confidence-intervals.md](03-judge-confidence-intervals.md) | What the corpus-002 numbers can and cannot separate; the cross-vendor comparison hygiene rules. |
| 04 | [04-served-markdown-experiment.md](04-served-markdown-experiment.md) | Track A vs Track B, the HTML-source bias, the bias-corrected null result, the F4.4 verdict. |
| 05 | [05-token-efficiency.md](05-token-efficiency.md) | The contrarian token-efficiency finding broken out for emphasis: markdown ≠ token-efficient against a careful pipeline. |
| 06 | [06-what-this-does-not-support.md](06-what-this-does-not-support.md) | Overclaim guard. The list of things corpus-002 cannot prove. |
| 07 | [07-recommendations-and-next-steps.md](07-recommendations-and-next-steps.md) | Concrete v2 / Phase 6 / Phase 7 actions distilled from the findings. |

---

## How to use these documents

- **Quoting in a Clipper report or a vendor-facing comparison:** cite the topical doc that reinforces the specific point, then cite the source document for the full audit trail.
- **Onboarding a new contributor:** read the README, then 01, 02, 04 in order. 03/05 are deep-dives. 06 is the methodology guardrail. 07 is the action list.
- **Methodology challenge:** open the source document; topical docs are summaries, not the audit trail.

---

## Provenance

| | |
|---|---|
| Corpus | corpus-002, n=43, 14 vendors, English documentation |
| Pipeline | dual-fetcher (raw HTTP + Playwright) → Readability → Mistral-Large-3 harder-Q/A generator → GPT-4.1 primary scorer + Llama-3.3-70B judge (κ=0.773 vs human) |
| Phase 6 additions (Session 4–5) | tri-fetcher (raw / link-alternate / sibling-md), intersection-Q/A bias correction, token-efficiency probe |
| Source document | [findings/phase-5-corpus-002-findings.md](../phase-5-corpus-002-findings.md) |
| Roadmap PRD | [findings/v2-scoring-phase6-roadmap-prd.md](../v2-scoring-phase6-roadmap-prd.md) |
| Raw artifacts | [evaluation/phase5-results/corpus-002/](../../evaluation/phase5-results/corpus-002/), [evaluation/phase5-results/corpus-002-analysis/](../../evaluation/phase5-results/corpus-002-analysis/) |
