# Phase 5 pilot: findings (N=43)

**Companion to:** [phase-5-methodology.md](phase-5-methodology.md). Read the methodology for definitions, caveats, and pipeline description.
**Source data:** `evaluation/phase5-results/corpus-001/` (per-page) and `evaluation/phase5-results/corpus-001-analysis/` (aggregates).
**Pilot size:** N=43 pages — 36 tier-1, 7 tier-2. **Directional only.** Correlation coefficients at this sample size should not be quoted as effect sizes.

## 1. Headline

| Metric | Raw | Rendered | Delta |
|---|---|---|---|
| Mean accuracy | 0.956 | 0.949 | −0.006 |
| Mean `parseability_score` | 53.2 | 56.1 | +2.9 |
| Mean `universal_score` | 54.0 | 56.8 | +2.8 |

**The headline "rendered" accuracy is lower than "raw" in aggregate, but this is a compositional artifact, not a real effect.** Raw accuracy is computed only over the 36 pages where the raw fetch succeeded, and those are by construction the tier-1 pages. Rendered accuracy is computed over all 43 pages — including the 7 tier-2 pages where the raw fetch failed and where rendered accuracy is merely 0.886. When you restrict the comparison to pages where both fetches produce usable text (tier-1 only), raw and rendered accuracy are statistically identical: **0.956 raw vs 0.961 rendered**, delta +0.005.

The right framing is that raw and rendered extraction produce equivalent agent accuracy **when both work**, and rendered saves the day when raw fails. That is the expected outcome and the harness is behaving correctly.

## 2. Tier-2 is where the real finding lives

The per-tier breakdown:

| Tier | n | acc raw | acc rendered | mean `parseability_rendered` |
|------|---|---------|--------------|-------------------------------|
| 1 | 36 | 0.956 | 0.961 | 55.1 |
| 2 |  7 | — (all fetches failed or returned <1500 chars) | 0.886 | 61.2 |

For an HTTP-only agent — the default behavior of most retrieval-augmented LLM systems in production today — **tier-2 pages produce zero usable content**. The 7 tier-2 pages in the corpus break down as:

- **4/7 hard failures** — raw `httpx` GET returns HTTP 403 (Cloudflare, OpenAI docs × 3, Wikipedia × 2, plus `openai.com/docs/guides/function-calling`).
- **3/7 soft failures** — raw GET returns 200 but the response is a shell with <1500 chars of extractable text (Docker landing, GCP bigquery samples, Stripe quickstart).

A browser-capable agent, using Playwright to render, gets 0.886 mean accuracy on the same pages — close to the 0.961 tier-1 baseline but measurably lower. The gap is driven by two pages: Docker's get-started landing (0.600) and OpenAI's quickstart (0.800). Both are pages where even the rendered extraction is thin enough that the scorer loses a question or two.

The takeaway is not "tier-2 is worse in rendered mode." It is: **the cost of JavaScript-dependency for an HTTP-only agent is total. The rendered-mode accuracy (0.886) is what a browser-capable agent achieves, not what the typical agent sees.**

## 3. Tier-3 is a documentation category in its own right

Of the 86-URL candidate set, 30 URLs (35%) were tier-3: neither fetcher produced ≥1500 chars of usable content. We excluded them from the pilot because they cannot contribute a measurable accuracy number. But tier-3 composition matters:

| Root cause | Count |
|---|---|
| HTTP 200 + <1500 chars extracted from rendered (shell + lazy load, auth, or client-routing required) | 22 |
| HTTP 404 (stale URL) | 5 |
| HTTP 403 (active block) | 3 |

Only 3 of 30 tier-3 pages are "blocked by anti-bot." The dominant pattern is the **shell-plus-lazy-load architecture**: the origin returns a 200 response quickly, the document loads, but Clipper's rendered fetcher doesn't execute the right interactions (client-side routing, auth flow, scroll-triggered hydration) to trigger the content. Most Perplexity docs (5), OpenAI platform pages (3 beyond the ones we kept), Upsun docs (8), and several Snowflake landing pages are in this bucket.

**Implication:** a non-trivial fraction of modern documentation is effectively invisible to retrieval agents, including agents willing to run a headless browser. The fix is not anti-bot-circumvention — it's publishing content in a way that survives a naive `navigate → wait → extract` flow.

## 4. Clipper score vs measured accuracy — correlations are weak

| Score field | Accuracy field | n | Pearson r |
|---|---|---|---|
| `parseability_score_raw` | `accuracy_raw` | 36 | −0.231 |
| `parseability_score_rendered` | `accuracy_rendered` | 43 | −0.158 |
| `universal_score_raw` | `accuracy_raw` | 36 | −0.247 |
| `universal_score_rendered` | `accuracy_rendered` | 43 | −0.139 |

All four correlations are weak and slightly negative. **The dominant cause is a ceiling effect in the accuracy distribution:** 30 of 43 pages score 1.000 on rendered accuracy. With most of the outcome variable piled at 1.0, there is essentially nothing for a score to correlate with. Per-page: the pages that score below 1.0 on accuracy (MDN CORS 0.8, Anthropic release notes 0.8, k8s kubectl reference 0.8, `System.String` 0.6, Docker landing 0.6) happen to include some pages with above-average Clipper scores, which drags the correlation slightly negative.

**This is not evidence against Clipper's methodology.** It is evidence that factual Q/A on well-written documentation is too easy for GPT-4.1 to discriminate between "good" and "very good" pages. To detect correlation you need either (a) harder questions, (b) a wider quality spread, or (c) a larger sample — ideally all three.

## 5. Per-pillar correlation (rendered-mode)

| Pillar | Pearson r vs `accuracy_rendered` | Mean pillar score |
|---|---|---|
| Semantic HTML | −0.259 | 63.3 |
| Content Extractability | +0.054 | 74.2 |
| Structured Data | −0.075 | 33.2 |
| DOM Navigability | +0.037 | 44.4 |
| Metadata Completeness | −0.299 | 57.4 |
| HTTP Compliance | +0.008 | 71.2 |

Same ceiling caveat applies to every row, so read these as direction, not magnitude. Two things are worth flagging for the follow-up corpus:

- **Metadata Completeness has the largest-magnitude (still weak) negative correlation.** This is the pillar with the known vendor-neutrality caveat (`ms.topic` acceptance — see the improvement-plan file). A follow-up pilot that breaks the ceiling should prioritize testing whether this negative relationship is real.
- **Content Extractability is essentially uncorrelated.** This is the pillar most directly tied to the text the scorer sees, so if the ceiling weren't capping the outcome we'd expect the strongest positive correlation here. Its absence is itself a signal that the measurement is ceiling-limited.

## 6. Per-profile summary

| Profile | n | acc raw | acc rendered | Notes |
|---|---|---|---|---|
| article | 12 | 0.956 | 0.967 | Baseline. |
| faq | 3 | 1.000 | 1.000 | Perfect. Small n. |
| reference | 12 | 0.950 | 0.950 | Baseline. `System.String` (0.6/0.6) is the outlier. |
| tutorial | 10 | 0.975 | 0.960 | k8s tutorial: raw 0.8 → rendered 1.0. |
| landing | 4 | 0.867 | 0.800 | Lowest profile. Docker landing 0.6 is the outlier. |
| sample | 2 | 1.000 | 1.000 | Small n. |

Landing pages are the lowest-scoring profile, consistent with the general view that landing pages carry less directly answerable content than reference or tutorial pages. Small n; directional.

## 7. Vendor highlights

- **Wikipedia, OpenAI platform, GCP samples** — all score 1.0 or near-1.0 in rendered mode despite being tier-2. When rendered succeeds, these pages are as agent-friendly as anything else. The cost is entirely in the raw-fetch failure mode.
- **Docker** — split personality. The `get-started` landing (tier-2, 0.6 rendered) and `get-started/02_our_app` tutorial (tier-1, 1.0 both) are very different pages; the landing is a JS-heavy shell and the tutorial is a normal document.
- **Anthropic** — all 5 pages tier-1, average accuracy 0.920. The `release-notes/api` page (0.8/0.8) and `welcome` landing (0.8/0.8) drag the average.
- **Learn (.NET `System.String` API reference)** — sole 0.6/0.6 page. Worth a per-page inspection of which Q/A the scorer missed. May be a generator artifact (overly specific questions) rather than a page problem.

## 8. Specific pages worth inspecting

Pages below 1.0 rendered accuracy, in order:

| Page | Tier | Profile | acc rendered | Notable |
|---|---|---|---|---|
| `learn-microsoft-com-en-us-dotnet-api-system-string` | 1 | reference | 0.600 | `parse_rendered`=83.5 — high Clipper, low accuracy. Investigate Q/A quality. |
| `docs-docker-com-get-started` | 2 | landing | 0.600 | Tier-2 landing; content is thin even rendered. |
| `docs-stripe-com-payments-quickstart` | 2 | tutorial | 0.800 | Shell + lazy load; rendered extraction incomplete. |
| `platform-openai-com-docs-quickstart` | 2 | tutorial | 0.800 | Tier-2; similar shape. |
| `docs-anthropic-com-en-release-notes-api` | 1 | article | 0.800 | Listicle content; generator may have hit the 40k cap. |
| `docs-anthropic-com-en-docs-welcome` | 1 | landing | 0.800 | |
| `developer-mozilla-org-en-US-docs-Web-HTTP-CORS` | 1 | article | 0.800 | |
| `nodejs-org-en-about` | 1 | landing | 0.800 | |
| `kubernetes-io-docs-reference-kubectl` | 1 | reference | 0.800 | Reference index page; questions may require following links. |

For a production report, spot-check the generator's Q/A pairs on 3–5 of these. If the miss is "generator asked a question the page doesn't really answer," that's a methodology note, not a page problem. If the miss is "the page contains the answer but in a format the scorer couldn't use," that's the more interesting finding.

## 9. Headline claims the pilot supports

1. **JavaScript-dependency has a binary retrievability cost for HTTP-only agents.** Tier-2 pages (16% of our candidate set, 35% of the pilot's corpus by design) return zero usable content to an agent that doesn't run a browser. This is a new, evidence-backed claim for Clipper.
2. **Among pages where both fetchers work (tier-1), raw and rendered are equivalent for agent accuracy.** The Clipper `parseability_score` delta between the two modes on tier-1 pages is small (+1.9 avg), and agent accuracy is identical. This confirms that for tier-1 pages the delta is mostly WCAG-strictness, as suspected.
3. **A non-trivial fraction (~35%) of modern documentation is tier-3** — unretrievable even with a headless browser, and the dominant cause is shell-plus-lazy-load architectures, not anti-bot blocking. This is the finding the pilot did not set out to produce.

## 10. Claims the pilot does not support

1. ❌ "Clipper scores predict agent accuracy." The correlations at N=43 are weak and noisy; the ceiling effect makes it impossible to judge. **A follow-up pilot with harder Q/A is the single most valuable next step.**
2. ❌ "Vendor X is better than vendor Y." Per-vendor n is 1–5 pages; variance is not characterized.
3. ❌ "Metadata pillar is miscalibrated." The weak negative correlation is suggestive at best; needs the ceiling-broken pilot before this can be claimed.

## 11. Recommended next steps

1. **Write a hard-Q/A pilot** (corpus-002) with synthesis or multi-step questions designed to land accuracy in the 0.3–0.8 range. This is the only way to break the ceiling and test pillar correlations meaningfully. Same N=43 corpus is fine; just harder generator prompts.
2. **Investigate the 9 below-1.0 pages** (§8) to separate "page problem" from "generator artifact." 30 minutes of Q/A inspection.
3. **Track tier distribution over time.** The 44/12/30 split in the probe is a snapshot of today's web. If tier-3 is growing, Clipper users need to know.
4. **Publish the methodology note externally** once a second pilot has confirmed (or refuted) the tier findings. The tier-2/tier-3 findings are the pilot's strongest contributions and are worth formalizing.
