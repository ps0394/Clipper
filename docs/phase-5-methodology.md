# Phase 5 methodology: calibrating Clipper against measured agent accuracy

**Status:** Methodology locked. Findings report (`phase-5-findings.md`) depends on this document for its definitions.
**Scope:** The N=43 dual-fetcher pilot (`evaluation/phase5-results/corpus-001/`).

## 1. The question Phase 5 answers

Clipper (see [docs/scoring.md](scoring.md)) produces a six-pillar standards-based score for how well a web page is structured for machine retrieval. Every pillar is a **proxy**: semantic HTML, Schema.org, accessibility, metadata, HTTP compliance, and content extractability each plausibly correlate with agent success, but Clipper had never directly measured the outcome those proxies are proxies for.

Phase 5 closes that gap by asking, for a given URL:

> When a frontier LLM is given nothing but the text a typical HTTP agent could extract from this page, how accurately does it answer factual questions grounded in that page's content?

Clipper's scores are then correlated against that empirical accuracy. Strong correlation is evidence for the methodology; weak correlation is evidence to retune it.

This is a **validation harness**, not a product feature. The LLMs are instrumentation.

## 2. The dual-fetcher

Clipper already emits a rendered-vs-raw score delta for every page. That delta was previously ambiguous: it could indicate real JavaScript-dependency of the content, or simply that axe-core runs only in rendered mode (making the WCAG sub-pillar stricter when rendered). The improvement plan flags this as a known caveat.

Phase 5 separates the two effects. For every URL the pilot performs **two independent fetches**:

| Mode | Fetcher | What it simulates |
|------|---------|---------------------|
| Raw | `httpx` GET with realistic user-agent, 30s timeout | Agents that fetch HTML over HTTP without executing JavaScript (most retrieval-augmented agents in production). |
| Rendered | Playwright headless Chromium, navigate + race `wait_for_function('document.body.innerText.length > 1500')` against `networkidle` | Agents (or humans) that run a full browser to hydrate dynamic content. |

Both snapshots are passed independently through Clipper's standard scorer, so each page emits `parseability_score_raw`, `parseability_score_rendered`, and matching component scores. The delta, measured this way, is isolated to **fetcher-visible differences in page content** — not WCAG strictness.

For the agent-accuracy side of the pilot, the LLM under test is scored against **both** the raw and rendered extractions. The accuracy delta is the direct measurement of JavaScript-dependency cost.

## 3. The 86-URL probe and the three-tier taxonomy

Before running the full pilot, an 86-URL candidate set spanning 16 documentation vendors and six content-type profiles was probed with both fetchers. Each URL was classified by which fetchers produced usable text (≥1500 chars of extractable content):

| Tier | Raw | Rendered | Count | Meaning |
|------|-----|----------|-------|---------|
| 1 | ✅ | ✅ | 44 | Server-rendered; HTTP-only agents see the same content as browsers. |
| 2 | ❌ | ✅ | 12 | JavaScript-required; HTTP-only agents see nothing useful, browsers succeed. |
| 3 | ❌ | ❌ | 30 | Unretrievable within our budget — see breakdown below. |

The taxonomy was **measured, not assumed**. It emerged from the probe's output.

### Tier-3 is not primarily "actively bot-blocked"

A useful finding in its own right. Looking at tier-3 more carefully:

- **22 of 30 tier-3 URLs returned HTTP 200 on the raw fetch** and loaded successfully in headless Chromium — but extracted less than 1500 chars of usable text from either mode. Examples include Perplexity docs, several OpenAI pages, Snowflake landing pages, Mintlify docs. These pages serve a shell (≤300 chars in most cases) that relies on client-side routing or lazy loading the probe didn't trigger.
- **5 of 30** returned HTTP 404 — stale URLs in the candidate list, mostly deprecated platform paths.
- **3 of 30** returned HTTP 403 — the only "actively bot-blocked" cases in the candidate set.

So the more precise framing is: **tier-3 pages are pages that do not reliably deliver their content to any HTTP client the probe could simulate, regardless of whether JavaScript is executed.** That includes outright blocking, stale URLs, and — most commonly — shell-plus-lazy-load architectures that need interaction or authentication beyond a simple load-and-wait.

### Tier-2 distribution

The 12 tier-2 URLs cluster on three vendors: Wikipedia (4), OpenAI docs (5), with singletons from Stripe, Docker, and GCP. These are well-known SPA-style sites where the server response is a shell and the content is populated by client-side JavaScript.

## 4. Corpus selection (N=43)

The pilot corpus was selected from tier-1 and tier-2 pages, with deliberate over-representation of tier-2 relative to its natural prevalence:

- **36 tier-1 pages** chosen for profile balance across `article`, `reference`, `tutorial`, `landing`, `faq`, `sample`.
- **7 tier-2 pages** chosen to represent the SPA cluster (Wikipedia, OpenAI, Stripe, Docker, GCP).

Tier-3 was excluded: if neither fetcher produces usable content, there is no meaningful accuracy to measure. The existence of tier-3, and its composition, is reported separately.

## 5. The scoring pipeline

Per page, three LLMs play distinct roles:

1. **Generator — Mistral Large 3** — is given the **rendered** extraction (always the full picture) and produces 5 factual Q/A pairs with supporting sentences. Rendered is used because it is the ground-truth view of what the page actually says.
2. **Primary scorer — GPT-4.1** — receives one of the extractions (raw or rendered) as its only context, is asked each of the 5 questions with a neutral system prompt, and produces an answer. It is scored against both extractions independently.
3. **Judge — Llama-3.3-70B-Instruct** — for each Q/A pair, reads the generator's ground-truth answer and the scorer's answer, and issues a binary correct/incorrect judgment.

A **secondary scorer — also Llama-3.3-70B-Instruct** — repeats step 2 against the rendered extraction only. Its accuracy provides an inter-model cross-check: if the headline accuracy is a property of the page rather than of GPT-4.1 specifically, both models should rank pages similarly.

Three families of model are deliberately chosen to reduce (not eliminate) self-grading contamination. The generator is Mistral, the scorer-under-test is OpenAI, the judge is Llama. Judge-and-secondary-scorer share a family; that's a known caveat, bounded but not zero.

## 6. Why an LLM judge, not substring matching

An earlier calibration pass ran the substring grader and the LLM judge against 20 manually adjudicated Q/A pairs. Cohen's κ between the LLM judge and human adjudication was **0.773** at N=20, substantially better than substring matching, which systematically penalized semantically-correct answers that differed in format — for example, "Expiration month is 3 and year is 2024" was marked wrong against a ground-truth "3, 2024."

The κ value carries a well-known caveat: it is sensitive to class imbalance ("kappa paradox"). At N=20 the imbalance was modest; the judge was accepted on that basis. Scaling to production would benefit from a larger calibration set.

## 7. Not an agent test

What Phase 5 measures is the **reading-comprehension step** of an agent, not the full agent. Specifically:

- There is no tool use, no planning, no multi-turn retrieval.
- The primary scorer is given one page's text and asked questions. A real agent would also choose which pages to fetch, when to re-query, and how to synthesize across sources.
- The dual-fetcher approximates variation in agents' HTTP clients. It does not approximate variation in agents' reasoning scaffolds.

This is deliberate. Adding agent-planning to the harness would inject variance that has nothing to do with page quality — which is what Clipper is scoring. Isolating the reading step lets the pilot's findings attribute cleanly to the page, not to the harness.

## 8. Known caveats

- **Ceiling effect.** Factual Q/A on well-written documentation is easy for GPT-4.1. Most tier-1 pages score at or near 1.0 on accuracy, leaving little variance for correlation. A follow-up corpus with harder (synthesis or multi-step) questions would break the ceiling but was out of scope for the first pilot.
- **Judge-scorer family overlap.** Judge and secondary scorer both use Llama 3.3-70B. They play different roles (judge compares to ground truth; scorer produces the answer) and are grounded in different prompts, but full family independence would be stronger.
- **N=43 is a pilot, not a study.** Correlation coefficients reported at this sample size are directional only.
- **Tier-3 URLs dropped from the corpus** means the pilot cannot measure the agent-accuracy cost of tier-3 pages. Tier-3 composition (especially "shell plus lazy load") is reported as its own finding, not as an accuracy number.
- **Single run.** One pilot run, one random seed in the generator. Variance across re-runs is not characterized.
- **Q/A pairs are generated from the page itself.** A well-formed page that simply omits the information needed to answer an external question will score perfectly here. This harness measures "can an agent answer questions grounded in this page," not "does this page contain the information an agent needs."

## 9. Artifact inventory

- Code: [retrievability/phase5/](../retrievability/phase5/) (fetcher, runner, clients, generator, grader, schemas).
- Corpus: [urls/phase5-corpus-urls.txt](../urls/phase5-corpus-urls.txt) (N=43, locked).
- Probe evidence: [evaluation/phase5-corpus/probe-results.json](../evaluation/phase5-corpus/probe-results.json) (N=86).
- Per-page outputs: `evaluation/phase5-results/corpus-001/<slug>/summary.json` + dual-mode HTML/text/scoring/grading artifacts.
- Manifest: `evaluation/phase5-results/corpus-001/manifest.json`.
- Analysis script: [scripts/phase5-analyze.py](../scripts/phase5-analyze.py) — consumes the per-page summaries and emits the correlation tables used in the findings report.
