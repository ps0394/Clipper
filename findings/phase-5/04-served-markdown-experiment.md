# 04 — Served-markdown experiment (F4.1–F4.4)

> **Key point.** Served markdown does not measurably improve in-context comprehension on corpus-002. A bias-corrected paired test (Track B, n=17) returned a mean delta of **−0.012**, with **16 of 17 pages producing identical scores** on rendered HTML and served markdown. F4.4 verdict: `keep_as_diagnostic_only`.

This is the strongest negative evidence the corpus produced, and it is methodologically harder than it looks. The first attempt (Track A) produced a misleading negative; the bias-corrected attempt (Track B) produced an informative null.

---

## The setup

The tri-fetcher (`retrievability/phase5/fetcher.py`) probes three paths in order to obtain a markdown body for any URL:

1. **Accept-header content negotiation** — `Accept: text/markdown` on the original URL.
2. **Link alternate** — `<link rel="alternate" type="text/markdown">` in the rendered HTML, fetched.
3. **Sibling `.md`** — predictable path mutation, e.g. `/page` → `/page.md`.

On corpus-002, **27 of 43 pages (62.8%)** had a markdown body resolvable via at least one tier. The lift experiment is only measurable on those pages.

---

## Track A — naïve paired grading (the failed first attempt)

The runner generates Q/A from rendered HTML, then grades both rendered extract and served markdown against the same Q/A pool.

| Metric | n | Value |
|---|---|---|
| Pages scored | 25 | (2 dropped on extraction errors) |
| Mean delta (`accuracy_markdown_judged` − `accuracy_rendered`) | 25 | **−0.064** |
| Pos / neg / zero | 25 | 5 / 7 / 13 |

Per-vendor:

| Vendor | n | Mean Δ | Pos / Neg |
|---|---|---|---|
| github | 3 | +0.133 | 2 / 0 |
| anthropic | 5 | +0.040 | 2 / 1 |
| aws | 2 | 0.000 | 0 / 0 |
| docker | 2 | 0.000 | 0 / 0 |
| perplexity | 2 | 0.000 | 0 / 0 |
| snowflake | 3 | −0.067 | 0 / 1 |
| learn | 4 | −0.200 | 1 / 2 |
| openai | 2 | −0.300 | 0 / 2 |
| stripe | 2 | −0.300 | 0 / 1 |

Track A would yield `keep_as_diagnostic_only` — but the result is **uninterpretable** because of a known design flaw.

### Why Track A is biased

Q/A drawn from the rendered HTML extract bake **content-coverage asymmetry** into the test. Any content the markdown legitimately omits (nav, dynamic widgets, expanded API tables) becomes a grading penalty against markdown — even if the markdown faithfully represents the article body.

The Track A delta cannot distinguish:
- "markdown has worse comprehension fidelity" (the question we want to answer), from
- "markdown drops content the rendered extract included" (a coverage choice, not a fidelity defect).

For Stripe and OpenAI especially, the markdown export drops large interactive sections that the rendered HTML retained — and the Q/A pool, drawn from rendered, asks about them. The resulting −0.300 is not a fidelity finding.

---

## Track B — intersection-Q/A (the bias-corrected design)

A new module ([retrievability/phase5/intersection.py](../../retrievability/phase5/intersection.py), 11 unit tests) computes the **sentence-level content intersection** of the rendered extract and the served markdown. Q/A are then generated from the intersection text only — neither format has a coverage advantage.

Pre-flight (no LLM cost):
- **17 of 25 markdown-resolved pages** have intersection text ≥ 1500 chars.
- Median intersection size: 2,727 chars; max 15,453.
- Median sentence-overlap: 45% rendered → markdown; 30% markdown → rendered. **The two formats are not the same document on the median page.**
- 8 pages drop out: openai-quickstart, both Stripe pages, all 5 Python pages (markdown extracts were nav-only or missing; counted as `intersection_too_thin`), plus 3 short anthropic / snowflake pages.

### Track A vs Track B on the same corpus

| Metric | Track A (HTML-Q/A) | Track B (intersection-Q/A) |
|---|---|---|
| n scored | 25 | 17 |
| **Mean delta (judged)** | **−0.064** | **−0.012** |
| Median delta | 0.000 | 0.000 |
| Pos / neg / zero | 5 / 7 / 13 | **0 / 1 / 16** |
| Track A − Track B (mean) | — | **+0.052** |

The **+0.052 difference between Track A and Track B is the size of the HTML-source bias** in the original test. After correcting it, **16 of 17 pages produce identical scores on rendered HTML and served markdown.**

The single negative is `docs-snowflake-com-en-user-guide-data-load-overview` (rendered = 1.0, markdown = 0.8) — one question's worth of difference on a 5-question page. Not a vendor-level finding.

### Per-vendor Track B

| Vendor | n | Mean Δ |
|---|---|---|
| anthropic | 3 | 0.000 |
| aws | 2 | 0.000 |
| docker | 2 | 0.000 |
| github | 2 | 0.000 |
| learn | 3 | 0.000 |
| openai | 1 | 0.000 |
| perplexity | 2 | 0.000 |
| snowflake | 2 | −0.100 |

Note: Track A's apparent leads (github +0.133) and apparent gaps (learn −0.200, openai −0.300) **all collapse to 0.000** under fair test. Those Track A results were bias.

Note also: rendered scores went **up** in Track B vs Track A on many pages (anthropic-getting-started 0.6→1.0, docker-get-started-02 0.6→1.0, github-plans 0.6→1.0). Restricting Q/A to intersection content lifts both versions.

---

## F4.4 verdict

Under the rule encoded in [scripts/phase6-markdown-lift.py](../../scripts/phase6-markdown-lift.py) (mean lift > 0.10 AND ≥2 vendors above threshold), Track B yields **`keep_as_diagnostic_only`** even more decisively than Track A.

But the *reasoning* is now different:

- **Track A's null was inconclusive** because the test design produced a coverage bias of unknown sign and magnitude.
- **Track B's null is a positive finding** of format equivalence: 16/17 pages score identically. **Within this corpus and grading methodology, served markdown and rendered HTML produce indistinguishable in-context comprehension accuracy.**

---

## What this finding does NOT cover

1. **Retrieval-mode RAG.** Chunk + embed + retrieve + grade is a different regime. Format-driven differences in chunk boundaries, retriever recall, and embedding quality are not measured. Plausibly markdown wins here. Phase 7 work.
2. **Pipeline reliability.** Crawler/extractor variance is reduced by markdown ingestion; this benefit shows up as variance reduction across many runs, not as a per-page mean delta.
3. **Code-heavy pages.** Fenced code blocks may behave differently than prose. Corpus-002 is mostly prose.
4. **Judge calibration on markdown inputs.** The Llama-3.3 judge was calibrated at κ=0.773 on rendered-HTML grading. Whether that calibration transfers to markdown documents is deferred. Track B's null is consistent with no drift but does not affirmatively prove no drift.

---

## Token-efficiency footnote — broken out for emphasis

The companion token-efficiency analysis is a separate finding deserving its own document. Headline:

- HTML → readability extract: **53.6× token reduction** (median).
- HTML → served markdown: **48.1× token reduction** (median).
- **Served markdown is 1.39× LARGER than a clean readability extract.**

The "markdown is more token-efficient" claim is true vs naïve raw-HTML ingestion; **false vs a careful HTML→text pipeline** on this corpus.

Full breakdown: [05-token-efficiency.md](05-token-efficiency.md).

---

## What this work authorizes

- **Authorizes:** the `keep_as_diagnostic_only` verdict for served-markdown lift on corpus-002 with the bias-corrected evidence base; the claim that served markdown does not improve in-context LLM comprehension at this scale and methodology.
- **Does not authorize:** any retrieval-mode claim; any "markdown is universally inferior" framing (the OpenAI Track A signal is real even if the n is small); any per-vendor scoring rule from these numbers.
