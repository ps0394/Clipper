# Clipper Improvement Issues

Create these as issues on [ps0394/Clipper](https://github.com/ps0394/Clipper).

---

## Issue 1: Add agent-perspective validation layer (no-JS fetch scoring)

**Labels:** enhancement, high-priority

### Summary
Add an automated validation layer that fetches each URL **without JavaScript rendering** (raw HTTP GET) and compares the extraction result against the full rendered Clipper score.

### Motivation
Many AI agents (RAG pipelines, search crawlers, LLM tool-use) fetch pages with simple HTTP requests — no Puppeteer, no JS rendering. The gap between "rendered Clipper score" and "raw fetch score" is itself a valuable metric that Clipper doesn't currently capture.

During manual validation, landing pages like Well-Architected Security returned almost nothing via raw fetch despite Clipper scoring them 52.6. The real-world agent experience is worse than Clipper suggests.

### Proposed Approach
- After the existing Puppeteer-based evaluation, do a parallel `fetch()` or `requests.get()` for each URL
- Run the same extractability analysis on the raw HTML
- Report both scores and the delta
- Flag pages where the delta exceeds a threshold (e.g., >15 points)

### Impact
High — addresses the most fundamental gap in Clipper's current model: assuming agents render JavaScript.

---

## Issue 2: Dual scoring profiles — "agent with browser" vs "agent with fetch"

**Labels:** enhancement, high-priority

### Summary
Produce two score profiles per URL: one for agents that render JavaScript (current behavior), and one for agents that do raw HTTP fetches.

### Motivation
A page that scores 60/100 with Puppeteer might score 25/100 to a RAG pipeline doing `requests.get()`. This distinction matters more than any single pillar score. The two profiles serve different audiences:
- **Browser profile:** Copilot, ChatGPT with browsing, Perplexity
- **Fetch profile:** RAG pipelines, search indexers, API-based agents

### Proposed Approach
- Run current evaluation pipeline → "Browser Score"
- Run no-JS evaluation pipeline (Issue #1) → "Fetch Score"
- Report both in the markdown output with a comparison table
- Overall score could be a weighted average (configurable)

### Impact
High — makes Clipper useful for a much broader range of agent architectures.

---

## Issue 3: Content-type-aware scoring profiles

**Labels:** enhancement, high-priority

### Summary
Score pages against expectations for their content type (e.g., `ms.topic` value) rather than a universal rubric.

### Motivation
Clipper currently penalizes landing pages and API references the same way it penalizes tutorials. But Storage Samples (52.5) *should* be a link catalog — its low extractability is by design, not a defect. Similarly, API reference pages like System.String have dense tables that are structurally correct but score poorly on prose-oriented extractability metrics.

### Proposed Approach
- Detect content type from metadata (`ms.topic`, Schema.org `@type`, or heuristics)
- Define scoring profiles per type:
  - **article/tutorial/how-to:** Full rubric (current behavior)
  - **landing-page:** De-weight extractability, emphasize navigation structure and structured data
  - **reference:** De-weight prose extractability, add table/API structure metrics
  - **sample:** Emphasize code block detection and extractability
  - **faq:** Emphasize Q&A structure and FAQ schema
- Report both the type-adjusted score and the raw universal score

### Impact
High — eliminates false negatives on non-prose content types and makes recommendations more actionable.

---

## Issue 4: Test actual extraction, not just signals

**Labels:** enhancement, medium-priority

### Summary
Run Mozilla Readability extraction and report *what was actually extracted* alongside the extractability score.

### Motivation
The current extractability score is based on signals (content ratio, structure preservation, boundary detection) but doesn't show the actual extracted text. During validation, seeing the extracted output made score interpretation much easier — a 33/100 on Storage Samples makes immediate sense when you see the 3 sentences that were extracted.

### Proposed Approach
- Run Readability on each page and save the extracted text to a file (e.g., `{hash}_extracted.txt`)
- In the markdown report, include a "Content Preview" section showing the first 200-300 characters of extracted text per URL
- Optionally include a diff view between full page text and extracted text
- Report extraction ratio: `extracted_chars / total_chars`

### Impact
Medium — dramatically improves report actionability without changing the scoring model.

---

## Issue 5: JSON-LD completeness validation

**Labels:** enhancement, medium-priority

### Summary
When JSON-LD is detected, validate field completeness against Schema.org requirements for the declared `@type`.

### Motivation
Clipper currently detects JSON-LD presence and awards points for having it, but doesn't validate whether the structured data is complete or useful. The AKS FAQ gets 67/100 for having `FAQPage` JSON-LD, but is the `mainEntity` array complete? Does it have all Q&A pairs? AWS's `BreadcrumbList` gets credit, but it's missing `Article` type entirely.

### Proposed Approach
- For each detected `@type`, define required and recommended fields:
  - `Article`: `headline`, `author`, `datePublished`, `dateModified`, `description`, `publisher`
  - `FAQPage`: `mainEntity` with `Question`/`acceptedAnswer` pairs, count vs actual FAQ count
  - `HowTo`: `step` array, `name`, `description`
  - `BreadcrumbList`: `itemListElement` with valid URLs
- Score completeness as a percentage of required+recommended fields present
- Flag invalid or empty fields

### Impact
Medium — makes the Structured Data pillar more granular and actionable.

---

## Issue 6: Cross-page template consistency analysis

**Labels:** enhancement, medium-priority

### Summary
When evaluating a set of pages from the same site/template, detect and report template-level issues separately from page-level issues.

### Motivation
In the Learn evaluation, 15 of 16 pages scored identically (35/100) on DOM Navigability due to shared template ARIA violations. Clipper reports this as 15 individual findings, but it's really one template fix. Separating template issues from content issues would make recommendations much more actionable.

### Proposed Approach
- When evaluating multiple URLs from the same domain, cluster identical sub-scores
- If >50% of pages share the same score on a pillar, flag it as a "template-level" issue
- In the report, separate "Template Recommendations" from "Page-Specific Recommendations"
- Include estimated impact: "Fixing this template issue lifts N pages by X points"

### Impact
Medium — transforms a wall of per-page findings into actionable template vs. content buckets.

---

## Issue 7: Competitive auto-discovery

**Labels:** enhancement, nice-to-have

### Summary
Given a set of URLs to evaluate, automatically suggest competitive/comparable pages covering the same topics.

### Motivation
Currently, competitive URLs must be manually curated in a separate file. This is time-consuming and may miss relevant comparisons. An auto-discovery feature would make competitive benchmarking more accessible and comprehensive.

### Proposed Approach
- Extract the topic/title from each input URL
- Use a search API (Bing, Google Custom Search, or DuckDuckGo) to find comparable pages from known documentation platforms
- Present discovered URLs for user approval before including in evaluation
- Maintain a configurable list of "competitor domains" to prioritize (e.g., docs.aws.amazon.com, cloud.google.com, developer.mozilla.org)

### Impact
Nice-to-have — reduces manual effort in setting up competitive analyses.

---

## Issue 8: Score trend tracking over time

**Labels:** enhancement, nice-to-have

### Summary
Store evaluation scores in a time-series format so teams can track whether template or content changes improve or degrade agent retrievability.

### Motivation
Clipper already snapshots pages and generates scores, but there's no way to compare today's scores against last month's. Teams deploying template fixes (e.g., adding JSON-LD) need to measure the impact.

### Proposed Approach
- Store scores in a lightweight format (JSON or SQLite) with timestamp, URL, and per-pillar scores
- Add a `clipper trend <url-or-dir>` command that shows score history
- Generate a trend chart (ASCII or markdown table) showing score changes over time
- Optionally integrate with CI to track scores per PR/commit

### Impact
Nice-to-have — enables data-driven iteration on agent retrievability improvements.

---

## Issue 9: LLM extraction quality test

**Labels:** enhancement, nice-to-have

### Summary
Add an optional evaluation mode that sends page content to an LLM and grades the quality of the LLM's response as a real-world proxy for agent retrievability.

### Motivation
Clipper's 6-pillar scoring measures structural signals that *should* correlate with agent retrievability, but doesn't directly test whether an agent can actually use the content. An LLM extraction test would close this loop.

### Motivation (example)
Send the page to an LLM with a prompt like "Summarize this page in 3 sentences" or "Extract the key steps from this tutorial." Grade the response on:
- Factual accuracy (does it match the page content?)
- Completeness (did it capture the main points?)
- Hallucination rate (did it invent information not on the page?)

### Proposed Approach
- Add an `--llm-test` flag to the CLI
- Support configurable LLM backends (Azure OpenAI, OpenAI, local models)
- Define 2-3 standard extraction prompts per content type
- Score LLM responses against page content using automated metrics (ROUGE, factual overlap)
- Report "LLM Retrievability Score" alongside the structural score
- Keep this optional — not everyone has LLM API access

### Impact
Nice-to-have — provides ground-truth validation that structural scores actually predict agent success. Could become the most important metric long-term.
