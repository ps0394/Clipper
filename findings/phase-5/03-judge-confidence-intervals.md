# 03 — Confidence intervals & the cross-vendor comparison rule

> **Key point.** Corpus-002 accuracy numbers come with wide intervals. The overall mean is 0.698 with a **90% CI of [0.633, 0.758]**. Per-vendor intervals overlap for almost every pair. Cross-vendor "X beats Y" claims published without intervals are a methodology error.

These intervals are computed on a **single judge** (Llama-3.3-70B, κ = 0.773 vs human). They under-state true uncertainty: cross-grader variance is not yet captured. F3.2 (cross-judge κ with two additional judges) is the gating work to tighten these.

---

## Overall and tier intervals

Bootstrap (percentile) 90% CIs over pages, seed=42, n_bootstrap=10000.

| Stratum | n | Mean | 90% CI |
|---|---|---|---|
| **overall** | 43 | **0.698** | **[0.633, 0.758]** |
| tier1 (raw fetch succeeded) | 36 | 0.717 | [0.650, 0.778] |
| tier2 (raw fetch failed → rendered-only) | 7 | 0.600 | [0.400, 0.771] |

**Read this:** any comparison against a corpus-002 baseline must budget at least ±0.06 of single-judge sampling uncertainty before adding cross-judge or temporal uncertainty.

---

## Profile intervals — most are not separable

| Profile | n | Mean | 90% CI |
|---|---|---|---|
| faq | 3 | 0.933 | [0.867, 1.000] |
| article | 12 | 0.733 | [0.583, 0.867] |
| sample | 2 | 0.700 | [0.600, 0.800] |
| reference | 12 | 0.683 | [0.517, 0.833] |
| landing | 4 | 0.650 | [0.600, 0.750] |
| tutorial | 10 | 0.620 | [0.560, 0.680] |

Only `faq` (0.933) and `tutorial` (0.620) clearly separate. The middle four overlap heavily.

---

## Vendor intervals — almost nothing separates

| Vendor | n | Mean | 90% CI |
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

**The only clearly-separable pairs at 90% confidence on this corpus** are roughly: {python, learn, k8s, perplexity, aws} vs {github, wikipedia}. Every other comparison is inside the noise.

OpenAI's [0.400, 1.000] is the canonical example: one mean, but the interval spans nearly the whole accuracy axis. A vendor comparison that quotes "OpenAI = 0.700" without quoting the interval is hiding a 60-point uncertainty band.

---

## The cross-vendor rule (write it down)

For any Clipper report or analysis that compares vendors using corpus-002 numbers:

1. **Quote the 90% CI alongside the mean.** Means without intervals are not publishable.
2. **State n.** n=2 cells are diagnostic-only. n=1 has no interval and should be marked as such.
3. **Use `universal_score`, not `parseability_score`, for cross-vendor headline deltas.** Profile-weighted scores apply different weights to different pages and are not on a common scale.
4. **Disclose the per-page profile assignment and detection source** (`ms.topic` / `schema_type` / `url` / `dom` / `default`). Asymmetric detection signals are a known confound (Phase 4.4).
5. **Match sample sizes or disclose the asymmetry.** 16 vs 6 is not a comparable baseline.
6. **Do not mix exemplars into competitor averages.** A page is one or the other.
7. **Symmetric projections.** If projecting fixes on the primary subject, project equivalent fixes on the comparison set with the same assumptions.

These are the same rules in [.github/copilot-instructions.md](../../.github/copilot-instructions.md) — reinforced here because corpus-002 is the corpus most likely to be quoted in such reports.

---

## What these intervals are NOT

1. **Cross-judge variance is not captured.** A single judge produced these labels. The true uncertainty is the union of page-level sampling variance + cross-judge grader variance. F3.2 lands the second variance term.
2. **Temporal variance is not captured.** Corpus-002 was graded once, in one window. Pages drift. T+30d replication is Session 5 work.
3. **Population generalization is not supported.** These intervals assume the 43 pages are representative of "the population of interest." They are a *curated* Phase 5 corpus. Generalization to the open web is not authorized; generalization to "developer documentation pages from the 14 sampled vendors" is cautiously authorized.

---

## Practical guidance

- **Headline numbers should always carry their CI when published externally.** "v2 r = +0.618 on corpus-002" should be paired with the CI from the regression script when audited.
- **Per-vendor "winner" framings are usually wrong at n=43.** Prefer ranges, not rankings.
- **CI widths on small per-vendor samples are not meaningful as absolute scores.** Use them as guardrails against overclaim, not as evidence for vendor choice.
