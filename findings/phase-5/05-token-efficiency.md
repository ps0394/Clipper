# 05 — Token efficiency: a contrarian finding

> **Key point.** The popular claim "markdown is more token-efficient than HTML" is true vs naïve raw-HTML ingestion, but **false vs a careful HTML→text pipeline** on this corpus. Served markdown is **1.39× LARGER** than a Readability extract on the median page. The ~50× token reduction agents experience comes from the cleaning step, not from the format.

This is the most counterintuitive corpus-002 finding, and it materially changes how the "markdown is agent-friendly" slogan should be used in Clipper reports.

---

## Method

[scripts/phase6-token-efficiency.py](../../scripts/phase6-token-efficiency.py) runs a pure file-size analysis on the 25 corpus-002 pages with all three artifacts:

- **Rendered HTML** — raw on-disk capture from the dual-fetcher (with full chrome / scripts / styles).
- **Readability extract** — re-computed locally via `Document(html).summary` + BeautifulSoup, **without** the runner's 40k-char clamp.
- **Served markdown** — read as-stored from `fetch.markdown.json`. **10 of 25 pages were clamped to 40k chars at fetch time**; for those pages the reported markdown size is a *floor*, not the true wire size.

Token counts use `tiktoken` `cl100k_base` (GPT-4 / Claude family BPE).

---

## Headline numbers (median per page)

| Format | Tokens | vs readability |
|---|---:|---:|
| Rendered HTML (raw, with chrome/scripts/styles) | 206,611 | **53.6× larger** |
| Readability extract (un-clamped) | 4,637 | baseline |
| Served markdown (clamped at 40k chars on disk) | 6,081 | **1.39× larger** |

**Three findings, in order of importance:**

1. **The 50× HTML→text reduction is real and is not from markdown.** Going raw HTML → readability extract is ~54× fewer tokens. Going raw HTML → served markdown is ~48× fewer. The win comes from stripping nav, JS, and styles — which both formats do. This is the "agent-friendly format" effect that gets attributed to markdown but is mostly attributable to *cleaning*.
2. **Served markdown is ~40% MORE tokens than a clean readability extract.** Median 6,081 vs 4,637. The "markdown is more token-efficient" claim, applied to web-published documentation and compared against a careful HTML pipeline, is **false on this corpus**. Likely cause: publisher markdown exports preserve breadcrumbs, version selectors, sidebar links, and front-matter that Readability aggressively strips.
3. **The 40k-char clamp distorts the picture upward for 40% of pages.** 10 of 25 markdown files hit the ceiling at fetch time; their true wire token counts are larger than the 6,081 median suggests. Stripe pages run 100k–200k+ chars on the wire. The aggregate markdown/readability ratio is a **floor**, not a ceiling.

---

## Per-vendor breakdown

n=2 cells are noisy; n=4–5 cells more reliable. "clamp" = pages whose markdown was truncated at 40k chars on disk.

| Vendor | n | Clamped | Median md tokens | Median rt tokens | md/rt ratio | html/md ratio | Reading |
|---|---|---|---|---|---|---|---|
| **openai** | 2 | 0/2 | 4,115 | 10,818 | **0.34×** | 78× | The **only vendor** where markdown wins on tokens. Markdown is *one-third* the size of the Readability extract. OpenAI strips chrome more aggressively in their markdown export than Readability does in their rendered HTML. |
| aws | 2 | 2/2 | 10,894 | 11,693 | 1.00× | 2.2× | Token-equivalent. Both pages clamped on the markdown side, so true ratio could be much worse. The 2.2× HTML/md ratio is suspicious — AWS rendered HTML is unusually small on these endpoints. |
| docker | 2 | 1/2 | 5,872 | 5,903 | 1.23× | 61× | Roughly equivalent. |
| learn | 4 | 2/4 | 8,056 | 6,392 | 1.27× | **14×** | Markdown ~27% larger. The 14× HTML/md ratio is the lowest in the corpus — Learn's rendered HTML is the most aggressive at minimizing chrome (or its markdown is the most bloated; both can be true). |
| snowflake | 3 | 0/3 | 2,561 | 1,343 | 1.31× | 48× | Markdown ~31% larger; clean comparison (no clamping). |
| perplexity | 2 | 0/2 | 3,729 | 2,524 | 1.46× | 83× | Markdown ~46% larger; clean comparison. |
| github | 3 | 1/3 | 2,646 | 1,696 | 1.56× | 32× | Markdown ~56% larger. |
| anthropic | 5 | 2/5 | 2,911 | 1,163 | 1.61× | 70× | Markdown ~61% larger. **Largest n in the corpus and a consistently negative result.** |
| **stripe** | 2 | 2/2 | 8,250 | 3,424 | **6.29×** | 72× | Markdown is **6× LARGER** than Readability — and both pages were clamped, so the true wire ratio is even worse. Stripe's markdown export ships massive chrome / TOC / sidebar content. |

---

## What the per-vendor view tells you

- **Eight of nine vendors ship markdown that is larger than a clean HTML→text extraction.** The ratios cluster around 1.2× – 1.6× for most; Stripe is a 6× outlier; OpenAI is the lone exception in the other direction.
- **OpenAI** is the only vendor whose markdown is unambiguously token-efficient relative to a careful pipeline. The 0.34× ratio is striking but rests on n=2.
- **Stripe's markdown is dramatically inefficient.** Combined with Stripe's Track A regression in the served-markdown experiment ([04-served-markdown-experiment.md](04-served-markdown-experiment.md)) — and that Track B couldn't even run on Stripe because both pages had <10% sentence overlap with the rendered extract — the picture is consistent: **Stripe's markdown export is not optimized for agent ingestion.**
- **Learn's rendered HTML is unusually compact** (14× HTML/md ratio is by far the lowest). The markdown comparison flatters the vendor less than it would for vendors with bigger HTML pages — yet Learn markdown is still larger than its Readability extract.

---

## Decomposing the slogan "markdown is agent-friendly"

The slogan does several jobs at once and they should be separated. Corpus-002's evidence on each:

| Claim | Evidence on corpus-002 |
|---|---|
| Raw HTML is enormously more verbose than text/markdown | **Confirmed.** ~50× reduction either way. |
| Markdown beats a *naïve* HTML ingestion in tokens | **Confirmed.** ~48× reduction. |
| Markdown beats a *good* HTML→text extraction in tokens | **Refuted on this corpus.** 8 of 9 vendors ship markdown larger than Readability. Median ratio 1.39×; one outlier at 6.29×. |
| Markdown improves in-context LLM comprehension | **Refuted on this corpus.** Bias-corrected paired delta is −0.012; 16/17 pages identical. |
| Markdown is unambiguously a quality signal worth scoring | **Not supported.** Serving markdown does not imply serving *clean* markdown; some vendors ship markdown that is worse than their HTML on every measurable axis. |
| Markdown is useful for RAG / preprocessing pipelines | **Not measured.** Plausibly true; outside this corpus's regime. |
| Markdown is useful for chunking fidelity (retrieval-side) | **Not measured.** Plausibly true; outside this corpus's regime. |

---

## Implications for v2 scoring

1. **F4.4 stays `keep_as_diagnostic_only`.** No promotion to a scored pillar / sub-pillar.
2. **A binary "serves markdown" signal would be misleading** if added naïvely. Stripe and AWS publish markdown larger than their HTML extraction on every measured axis. Rewarding "ships markdown" without measuring "ships markdown that is better than the HTML alternative" would inflate scores for vendors whose markdown is publisher-side bloat.
3. **A future served-markdown signal should be conditional**, not binary. Roughly: "publisher serves markdown AND `tokens(markdown) ≤ tokens(HTML→clean)` AND `content(markdown) ⊇ content(HTML→clean)`." That requires per-page measurement against a reference extractor, not just an `Accept: text/markdown` probe.
4. **The token-efficiency analysis should remain a diagnostic in Clipper output** even without scoring impact. Publishers reading the report benefit from knowing whether their markdown export is leaner or more bloated than their HTML — that's actionable feedback the current pillars don't surface.

---

## Caveats

1. **n is small per vendor** (2–5). Per-vendor numbers are directional, not statistically separable except where the effect is large (Stripe 6.29×, OpenAI 0.34×).
2. **The 40k-char clamp** affected 10 of 25 markdown files. Reported ratios are floors for those pages.
3. **Code density not separated.** Pages with heavy fenced-code blocks may behave differently; not stratified here.
4. **Token analysis ignores publisher intent.** Some publishers may serve markdown specifically as machine-readable export and accept the larger size as a tradeoff for structure. The 1.39× finding is descriptive, not normative.
