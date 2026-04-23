# Microsoft Learn AI Retrievability Analysis
## Competitive Baseline & Improvement Roadmap

**Date:** April 22, 2026 (Updated)  
**Author:** Porkchop Squad (Clipper Automated Evaluation)  
**Audience:** Leadership  
**Tool:** Clipper v4.0 — Standards-based AI retrievability scoring  
**Scoring changes since v3:** Vendor-neutrality applied (ms.topic removed from metadata pillar), per-type JSON-LD field validation (Phase 4.1), classifier lockdown (Phase 4.3)

---

## Executive Summary

Microsoft Learn scores **57.8/100** on AI retrievability — **6 points ahead of the competitive average** (51.6/100). Learn leads in metadata (+24 pts), semantic HTML (+17 pts), content extractability (+16 pts), and HTTP compliance (+9 pts). However, Learn trails badly on **structured data** (18.2 vs 42.7) — a gap that costs ~12 points per page.

**Scoring update (v3→v4):** Clipper's vendor-neutrality pass removed `ms.topic` from the metadata pillar (it now influences only content-type classification, not scoring), dropping Learn's metadata average from 98.1 to 85.0. Per-type JSON-LD field validation (Phase 4.1) now properly credits the FAQ page's structured data (12→97). These are fairer scores — they measure what any documentation platform could implement, not Microsoft-specific signals.

No pages across any platform — Learn or competitor — qualify as "agent-ready" (90+). **Two template-level fixes could lift Learn to ~74/100**, opening a 22-point competitive lead.

### Scorecard

| Platform | Rendered | Raw (no-JS) | Pages | Best Pillar | Worst Pillar |
|----------|----------|-------------|-------|-------------|--------------|
| **Microsoft Learn** | **57.8** | **67.3** | 16 | Metadata (85.0) | Structured Data (18.2) |
| AWS | 61.7 | 61.4 | 4 | Structured Data (83.0) | Semantic HTML (29.1) |
| Google Cloud | 57.9 | 58.1 | 4 | Structured Data (75.8) | DOM Nav (13.8) |
| MDN Web Docs | 52.8 | 55.4 | 4 | HTTP Compliance (78.4) | Structured Data (0) |
| Mintlify | 33.8 | 37.2 | 4 | HTTP Compliance (61.1) | DOM Nav (11.2) |
| **Competitor Average** | **51.6** | **61.1** | 16 | HTTP Compliance (71.8) | DOM Nav (34.4) |

---

## Scoring Methodology

Clipper evaluates six pillars of AI retrievability — how well content can be discovered, parsed, and used by AI agents, RAG systems, and answer engines:

| Pillar | Weight | What It Measures |
|--------|--------|-----------------|
| Semantic HTML | 25% | Heading hierarchy, landmark roles, content structure |
| Content Extractability | 20% | Clean text extraction via Readability algorithm |
| Structured Data | 20% | Schema.org/JSON-LD richness and correctness |
| DOM Navigability | 15% | WCAG 2.1 accessibility (axe-core), skip links, ARIA |
| Metadata Completeness | 10% | Dublin Core, OpenGraph, description, canonical |
| HTTP Compliance | 10% | RFC 7231, robots.txt, caching, content negotiation |

Each URL was evaluated in **rendered** (full browser + axe-core) and **raw** (no JavaScript) modes to measure JS dependency. Sample: **16 Learn URLs** (10 content types) vs **16 competitor/exemplar URLs** (4 sites × 4 content types).

---

## Pillar-by-Pillar Comparison

| Pillar | Learn | Google Cloud | AWS | MDN | Mintlify | Comp Avg | Learn Delta |
|--------|-------|-------------|-----|-----|----------|----------|-------------|
| **Metadata** | **85.0** | 51.2 | 70.0 | 70.0 | 55.0 | 61.6 | **+23.4** ✅ |
| **Semantic HTML** | **69.9** | 64.4 | 29.1 | 66.9 | 50.1 | 52.6 | **+17.3** ✅ |
| **Extractability** | **75.0** | 64.3 | 68.5 | 67.2 | 35.6 | 58.9 | **+16.1** ✅ |
| **HTTP Compliance** | **80.8** | 66.2 | 81.5 | 78.4 | 61.1 | 71.8 | **+9.0** ✅ |
| **DOM Nav** | **32.2** | 13.8 | 61.2 | 51.2 | 11.2 | 34.4 | **-2.2** ➖ |
| **Structured Data** | 18.2 | 75.8 | **83.0** | 0 | 12.0 | 42.7 | **-24.5** ❌ |

### Key Findings

1. **Metadata is Learn's strongest pillar** — 85.0 vs competitors' 61.6. Under v4 vendor-neutral scoring (which no longer credits `ms.topic` as a metadata field), Learn still leads by 23 points — the advantage is built entirely on standard signals. Learn's CMS template automatically injects:

   ```html
   <!-- OpenGraph (present on every Learn page) -->
   <meta property="og:title" content="Introduction to Blob (object) Storage - Azure Storage">
   <meta property="og:description" content="Use Azure Blob Storage to store massive amounts...">
   <meta property="og:url" content="https://learn.microsoft.com/en-us/azure/storage/blobs/...">
   
   <!-- Dublin Core / standard meta -->
   <meta name="description" content="...">
   <link rel="canonical" href="...">
   <html lang="en-us">
   ```

   Competitors miss key fields: Google Cloud pages lack `og:description` on reference pages (metadata score: 25/100), Mintlify omits canonical URLs on some pages, and Wikipedia lacks `description` in its JSON-LD (field completeness: 83.3%).

2. **Structured data is Learn's biggest gap** — 14 of 16 Learn pages score exactly 12/100. These pages have **no JSON-LD at all** — only bare `schema.org/Organization` microdata and OpenGraph. Clipper finds 2 formats (microdata + OG) but zero validated schema types, zero field completeness, and zero schema validation:

   ```
   Learn storage-blobs score breakdown:
     type_appropriateness:  0/20  (no recognized @type)
     field_completeness:    0/30  (no Article/HowTo/FAQ fields)
     multiple_formats:     12/20  (microdata + OpenGraph only)
     schema_validation:     0/30  (no schema to validate)
     TOTAL:               12/100
   ```

   **What competitors embed that Learn doesn't:**

   AWS injects a `BreadcrumbList` JSON-LD block on every page with full navigation hierarchy, scoring 85/100:
   ```json
   {"@type": "BreadcrumbList", "itemListElement": [
     {"@type": "ListItem", "position": 1, "name": "AWS", "item": "https://aws.amazon.com"},
     {"@type": "ListItem", "position": 2, "name": "Amazon S3", "item": "..."},
     {"@type": "ListItem", "position": 3, "name": "User Guide", "item": "..."},
     {"@type": "ListItem", "position": 4, "name": "What is Amazon S3?", "item": "..."}
   ]}
   ```

   Wikipedia embeds a full `Article` JSON-LD with `headline`, `datePublished`, `dateModified`, `author`, `publisher` — scoring 92/100:
   ```json
   {"@type": "Article", "name": "Microsoft Azure",
    "headline": "cloud computing platform operated by Microsoft",
    "datePublished": "2008-10-27T18:36:15Z",
    "dateModified": "2026-03-10T16:10:43Z",
    "author": {"@type": "Organization", "name": "Contributors to Wikimedia projects"},
    "publisher": {"@type": "Organization", "name": "Wikimedia Foundation, Inc."}}
   ```

   **The proof that Learn can excel here:** Learn's FAQ page (`/azure/aks/faq`) already has `FAQPage` JSON-LD and scores **97/100** on structured data — the highest structured data score in the entire evaluation:
   ```json
   {"@type": "FAQPage", "mainEntity": [
     {"@type": "Question", "name": "Does AKS offer a service-level agreement?",
      "acceptedAnswer": {"@type": "Answer", "text": "<p>AKS provides SLA guarantees..."}}
   ]}
   ```
   ```
   FAQ score breakdown:
     type_appropriateness:  20/20  (FAQPage recognized)
     field_completeness:    30/30  (mainEntity with Question/Answer pairs)
     multiple_formats:      17/20  (JSON-LD + microdata + OpenGraph)
     schema_validation:     30/30  (all required fields present)
     TOTAL:                97/100
   ```

3. **AWS has weak semantic HTML** (29.1) — their pages are built on `<div>` soup with good metadata bolted on. AWS S3 overview pages use `<div class="awsdocs-container">` instead of `<main>`, `<article>`, or `<section>`. Learn's 69.9 is a meaningful advantage because its CMS template uses proper HTML5 landmarks (`<main>`, `<nav>`, `<header>`, `<footer>`, `<article>`).

4. **Mintlify scores poorly despite "AI-native" positioning** — 33.8 overall. Their `llms.txt` documentation page scores just 30.5/100 with extractability at 26.9 (Readability could only extract 133 characters of meaningful content). Their pages have zero DOM navigability (axe-core finds no ARIA landmarks, skip links, or focus management) and minimal structured data (12/100, same bare microdata as Learn).

5. **DOM navigability is weak across the board** — Learn averages 32.2, slightly below the competitive average (34.4). Axe-core flags specific WCAG 2.1 AA violations in Learn's CMS template:

   - **`[critical] aria-valid-attr-value`** — The collapsible TOC button uses `aria-controls` referencing a non-existent ID:
     ```html
     <button aria-expanded="true" aria-controls="ms--collapsible-toc-content-...">
     <!-- Target ID not found in DOM -->
     ```
   - **`[critical] label`** — Search combobox inputs lack associated `<label>` elements:
     ```html
     <input role="combobox" id="ax-2" aria-autocomplete="list">
     <!-- No <label for="ax-2"> or aria-label -->
     ```
   - **`[critical] duplicate-id-aria`** — On pages with tabbed content (like `quickstart-python`), duplicate ARIA IDs cause 4 violations, dropping DOM nav to 0/100.

   Wikipedia fares even worse (0/100 with 8 violations) — including `<input role="button">` misuse and color contrast failures.

---

## Learn Scores by Content Type

| Content Type | Pages | Avg Score | Top Page | Bottom Page |
|-------------|-------|-----------|----------|-------------|
| FAQ | 1 | **80.5** | aks/faq (80.5) | — |
| Tutorial | 4 | **61.8** | aks/tutorial (64.1) | quickstart-python (57.9) |
| Article | 5 | **56.8** | compute-decision-tree (59.0) | answers/qna (54.2) |
| Sample | 2 | **55.5** | functions-ref-python (61.0) | storage-samples (50.0) |
| Reference | 1 | **52.2** | system.string (52.2) | — |
| Landing | 3 | **50.2** | storage-blobs (52.8) | well-architected (46.4) |

**Key observation:** FAQ pages perform best because structured Q&A aligns naturally with semantic HTML and extractability. Landing pages perform worst — thin content plus low extractability.

---

## Site-by-Site Competitor Detail

### Google Cloud Docs (Avg: 57.9)

| URL | Type | Score | Strength | Weakness |
|-----|------|-------|----------|----------|
| storage/docs/introduction | overview | 63.7 | Extractability (80.8) | DOM Nav (35) |
| storage/docs/discover-object-storage-console | quickstart | 60.5 | Structured Data (67) | DOM Nav (0) |
| storage/docs/json_api/v1/objects | reference | 60.7 | Structured Data (92) | Metadata (25) |
| storage/docs/creating-buckets | how-to | 46.8 | Extractability (63.5) | DOM Nav (0) |

**Template pattern:** Strong structured data (75.8 avg), weak DOM navigability (13.8 avg). Google invests in JSON-LD but neglects accessibility.

### AWS Docs (Avg: 61.7)

| URL | Type | Score | Strength | Weakness |
|-----|------|-------|----------|----------|
| S3/userguide/Welcome | overview | 58.8 | Structured Data (85) | Semantic HTML (20) |
| S3/userguide/GetStarted | quickstart | 64.4 | Structured Data (85) | Semantic HTML (23.6) |
| S3/API/API_GetObject | reference | 60.7 | Structured Data (77) | Semantic HTML (23.6) |
| s3/faqs/ | faq | 63.0 | Structured Data (85) | Semantic HTML (49.1) |

**Template pattern:** Consistently strong structured data (83 avg) with rich JSON-LD, but very weak semantic HTML (29.1 avg) — they rely on `<div>` soup with good metadata bolted on.

### MDN Web Docs (Avg: 52.8)

| URL | Type | Score | Strength | Weakness |
|-----|------|-------|----------|----------|
| Fetch_API | overview | 47.8 | HTTP Compliance (80) | Structured Data (0) |
| Fetch_API/Using_Fetch | tutorial | 53.7 | Extractability (79.5) | Structured Data (0) |
| Response | reference | 55.1 | Semantic HTML (72.7) | Structured Data (0) |
| Fetch_API/Basic_concepts | how-to | 54.6 | Extractability (76.3) | Structured Data (0) |

**Template pattern:** Zero structured data across all pages — no JSON-LD at all. Strong semantic HTML and extractability, good HTTP compliance. A cautionary tale: even best-in-class HTML structure can't compensate for missing structured data.

### Mintlify (Avg: 33.8)

| URL | Type | Score | Strength | Weakness |
|-----|------|-------|----------|----------|
| docs/ai-native | overview | 32.3 | Semantic HTML (56.4) | DOM Nav (0) |
| docs/ai/llmstxt | how-to | 30.5 | HTTP Compliance (64) | DOM Nav (0) |
| docs/api-playground/openapi-setup | reference | 39.8 | Semantic HTML (72.7) | DOM Nav (0) |
| docs/quickstart | quickstart | 32.6 | HTTP Compliance (61.4) | DOM Nav (0) |

**Template pattern:** Consistently the weakest performer. Zero DOM navigability across all pages, low extractability (35.6 avg), minimal structured data (12 avg). Their "AI-native" branding does not translate to AI-retrievable content.

---

## JavaScript Dependency Risk

| Platform | Rendered Avg | Raw Avg | JS Delta | JS-Dependent Pages |
|----------|-------------|---------|----------|-------------------|
| Learn | 57.8 | 67.3 | **-9.5** | 1 of 16 |
| Google Cloud | 57.9 | 58.1 | -0.2 | 0 of 4 |
| AWS | 61.7 | 61.4 | +0.3 | 0 of 4 |
| MDN | 52.8 | 55.4 | -2.6 | 0 of 4 |
| Mintlify | 33.8 | 37.2 | -3.4 | 0 of 4 |

**Learn has the largest JS delta** (-9.5 pts). Most Learn pages lose ~10 points between raw and rendered, consistently across content types — this is a template-level effect. One page (`quickstart-python`) is flagged as JS-dependent (15pt delta). AWS and Google Cloud show near-zero JS dependency.

---

## Template-Level Fixes (Highest ROI)

Clipper detected **3 template clusters** — groups of Learn pages sharing the exact same weakness because it originates in the CMS template.

### Fix 1: Add JSON-LD Structured Data to Learn Templates

| Metric | Detail |
|--------|--------|
| **Affected pages** | 14 of 16 (score exactly 12/100 on structured data) |
| **Estimated uplift** | +11.6 points per page |
| **Competitive context** | AWS: 83, Google Cloud: 75.8, Learn: 18.2 |
| **Priority** | **P0** — largest single-fix impact |
| **Proof point** | Learn's FAQ page already has `FAQPage` JSON-LD and scores **97/100** on structured data — when Learn has JSON-LD, it excels |

**What competitors do right:**
- **AWS** embeds `BreadcrumbList` + `TechArticle` JSON-LD on every page, with `headline`, `datePublished`, `author`
- **Google Cloud** embeds `Article` with rich breadcrumb navigation and `dateModified`

**Recommendation:** Add a `<script type="application/ld+json">` block to Learn CMS templates. Example for a typical article page:

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "TechArticle",
  "headline": "{{page.title}}",
  "description": "{{page.description}}",
  "datePublished": "{{page.ms.date}}",
  "dateModified": "{{page.updated_at}}",
  "author": {"@type": "Organization", "name": "Microsoft"},
  "publisher": {"@type": "Organization", "name": "Microsoft Learn"}
}
</script>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {"@type": "ListItem", "position": 1, "name": "Azure", "item": "https://learn.microsoft.com/azure"},
    {"@type": "ListItem", "position": 2, "name": "{{service}}", "item": "{{service_url}}"},
    {"@type": "ListItem", "position": 3, "name": "{{page.title}}", "item": "{{page.canonical_url}}"}
  ]
}
</script>
```

Map `ms.topic` values to `@type`: `overview` → `TechArticle`, `quickstart`/`tutorial` → `HowTo`, `reference` → `TechArticle`, `faq` → `FAQPage`, `sample` → `SoftwareSourceCode`.

### Fix 2: Improve DOM Navigability (WCAG/axe)

| Metric | Detail |
|--------|--------|
| **Affected pages** | 10 of 16 (score exactly 35/100) |
| **Estimated uplift** | +5.2 points per page |
| **Competitive context** | AWS: 61.2, MDN: 51.2, Learn: 32.2 |
| **Priority** | **P1** — moderate impact, also improves accessibility |

Axe-core identifies three recurring critical violations in the Learn template:

1. **`aria-valid-attr-value`** — The TOC toggle button references a non-existent `aria-controls` target:
   ```html
   <!-- Current (broken): target ID not in DOM -->
   <button aria-expanded="true" aria-controls="ms--collapsible-toc-content-undefined">
   
   <!-- Fix: ensure the controlled element exists or remove aria-controls -->
   <button aria-expanded="true" aria-controls="toc-content">
   <div id="toc-content">...</div>
   ```

2. **`label`** — Search combobox inputs lack accessible labels:
   ```html
   <!-- Current (missing label) -->
   <input role="combobox" id="ax-2" aria-autocomplete="list">
   
   <!-- Fix: add aria-label -->
   <input role="combobox" id="site-search" aria-label="Search documentation" aria-autocomplete="list">
   ```

3. **`duplicate-id-aria`** — Pages with tabbed code samples (quickstart, tutorial) generate duplicate ARIA IDs, causing DOM nav to drop to 0/100. On `quickstart-python`, 4 nodes share duplicate IDs, each incurring a 25-point critical penalty.

**Recommendation:** Fix these three patterns in the CMS template. Estimated impact: score lifts from 35 → ~70 on most pages (from `significant_issues` to `moderate_issues`).

### Fix 3: Add Missing Semantic HTML Elements

| Metric | Detail |
|--------|--------|
| **Affected pages** | 14 of 16 (score exactly 72.7/100 on semantic HTML) |
| **Estimated uplift** | +4 points per page |
| **Competitive context** | MDN: 66.9, Google Cloud: 64.4, Learn: 69.9 |
| **Priority** | **P1** — template-level, low effort, also improves extractability |

Learn's CMS template includes 6 of 11 checked semantic elements — the ARIA landmark coverage (20/20) and heading structure (20/20) are perfect, but 5 HTML5 elements are consistently missing, capping the semantic coverage sub-signal at 32.7/60:

**Present in template:** `<header>`, `<nav>`, `<main>`, `<section>`, `<aside>`, `<footer>` ✅
**Missing from template:** `<article>`, `<figure>`, `<figcaption>`, `<time>`, `<mark>` ❌

**Recommended changes:**

1. **`<article>`** — Wrap the content zone in `<article>`. Currently content sits in `<main>` → `<section>` without an article boundary. This also improves Readability extraction (it uses `<article>` as a primary boundary signal for content detection):
   ```html
   <!-- Current -->
   <main id="main">
     <section>
       <h1>Introduction to Blob Storage</h1>
       <p>Azure Blob Storage is...</p>
     </section>
   </main>

   <!-- Recommended -->
   <main id="main">
     <article>
       <h1>Introduction to Blob Storage</h1>
       <p>Azure Blob Storage is...</p>
     </article>
   </main>
   ```

2. **`<time datetime="">`** — Learn displays `ms.date` and updated dates as plain text. Wrapping in `<time>` gives agents machine-readable dates at zero visual cost:
   ```html
   <!-- Current -->
   <span>Article • 02/15/2026</span>

   <!-- Recommended -->
   <span>Article • <time datetime="2026-02-15">02/15/2026</time></span>
   ```

3. **`<figure>` / `<figcaption>`** — Code samples and diagrams are rendered as bare `<pre><code>` blocks. Wrapping them enables agents to associate captions with code:
   ```html
   <!-- Current -->
   <pre><code class="lang-python">from azure.storage.blob import BlobServiceClient</code></pre>

   <!-- Recommended -->
   <figure>
     <pre><code class="lang-python">from azure.storage.blob import BlobServiceClient</code></pre>
     <figcaption>Connect to Azure Blob Storage using the Python SDK</figcaption>
   </figure>
   ```

Adding `<article>`, `<time>`, and `<figure>`/`<figcaption>` lifts coverage from 6/11 → 9/11, raising semantic coverage from 32.7 → 49.1 out of 60. Combined with ARIA (20) and headings (20), semantic HTML scores would rise from **72.7 → ~89** on most pages.

### Combined Projected Impact

| Metric | Current | Projected (all 3 fixes) | Change |
|--------|---------|-------------------------|--------|
| Learn Average | 57.8 | **~78** | **+20** |
| vs Competitor Avg | +6.3 | **+26** | — |
| vs AWS (closest) | -3.9 | **+16** | — |
| Pages ≥ 75 ("minor issues") | 1 | ~12 | — |

---

## Wikipedia Exemplar Benchmark

Wikipedia is included as a **ceiling benchmark** for structured content — not as a documentation competitor. As an encyclopedia, Wikipedia has different content goals, but its template engineering is widely regarded as best-in-class for structured data and semantic markup.

### Wikipedia vs Learn (Rendered)

| Metric | Wikipedia (4 pages) | Learn (16 pages) | Delta |
|--------|-------------------|-------------------|-------|
| **Overall** | 61.2 | 57.8 | +3.4 |
| **Structured Data** | **89.5** | 18.2 | **+71.3** |
| Semantic HTML | 70.0 | 69.9 | +0.1 |
| Extractability | 69.8 | 75.0 | -5.2 |
| Metadata | 70.0 | **85.0** | -15.0 |
| HTTP Compliance | 48.0 | **80.8** | -32.8 |
| DOM Navigability | 0.0 | 32.2 | -32.2 |

### Key Takeaways

1. **Structured data is Wikipedia's superpower** — 89.5 vs Learn's 18.2. Every Wikipedia page embeds a complete `Article` JSON-LD block with `headline`, `datePublished`, `dateModified`, `author`, and `publisher`, plus OpenGraph and microformat markup (3 formats total). The only missing field is `description` (field completeness: 83.3%, 5 of 6 expected fields). This is the benchmark Learn should target with JSON-LD template fixes — Learn already matches this quality on its FAQ page (97/100).

2. **Learn beats Wikipedia on metadata and HTTP** — Learn's CMS template delivers better Dublin Core/OpenGraph coverage (85 vs 70) and far better HTTP compliance (80.8 vs 48). Wikipedia's aggressive bot-blocking (403 Forbidden on programmatic `Accept: text/html` requests) actually *hurts* its retrievability — agents that don't use a full browser get rejected entirely:

   ```
   Wikipedia HTTP breakdown:
     html_reachability:     0/15  (403 Forbidden — blocked)
     redirect_efficiency:  25/25  (no redirects)
     crawl_permissions:    20/20  (meta robots permissive)
     cache_headers:         0/20  (no ETag, Last-Modified, or Cache-Control)
     agent_content_hints:   3/20  (no markdown alternate, no llms.txt)
     TOTAL:                48/100
   ```

   Compare to Learn, which returns 200 OK, provides `ETag`, `Last-Modified`, `Cache-Control`, and even exposes a `markdown_url` meta tag:
   ```
   Learn HTTP breakdown:
     html_reachability:    15/15  (200 OK)
     redirect_efficiency:  25/25  (direct access)
     crawl_permissions:    20/20  (robots.txt open)
     cache_headers:        20/20  (ETag + Last-Modified + Cache-Control)
     agent_content_hints:   4/20  (markdown_url meta present)
     TOTAL:               ~84/100
   ```

3. **Wikipedia's DOM navigability is 0/100** — axe-core flags 8 violations including `<input role="button">` misuse on checkbox elements, color contrast failures, and missing form labels. Despite being one of the most-visited sites on the web, Wikipedia has significant WCAG 2.1 AA gaps.

4. **Despite leading on structured data by 71 points, Wikipedia only leads overall by 3.4** — demonstrating that Learn's advantages in metadata, HTTP, and extractability compensate significantly. Fixing structured data alone would flip this and put Learn well ahead.

### Wikipedia Page Detail

| URL | Score | SemHTML | Extract | StrData | DOMNav | Meta | HTTP |
|-----|-------|---------|---------|---------|--------|------|------|
| Microsoft_Azure | **62.2** | 72.7 | 69.1 | 92.0 | 0.0 | 70.0 | 48.0 |
| Object_storage | **61.4** | 72.7 | 70.0 | 87.0 | 0.0 | 70.0 | 48.0 |
| Virtual_machine | **61.4** | 72.7 | 69.9 | 87.0 | 0.0 | 70.0 | 48.0 |
| Azure_DevOps_Server | **59.7** | 61.8 | 70.2 | 92.0 | 0.0 | 70.0 | 48.0 |

---

## Recommended Actions

| Priority | Action | Owner | Impact | Competitive Context |
|----------|--------|-------|--------|-------------------|
| **P0** | Add JSON-LD structured data to CMS templates | Platform Engineering | +11.6 pts avg | Closes gap with AWS (83) and Google (76); FAQ page already proves Learn excels at 97/100 when JSON-LD is present |
| **P1** | Fix WCAG/axe violations in base template | Platform Engineering | +5.2 pts avg | Approaches AWS (61) from current 32; fix `aria-controls`, missing labels, duplicate IDs |
| **P1** | Add `<article>`, `<time>`, `<figure>` to CMS template | Platform Engineering | +4 pts avg | Lifts semantic HTML from 72.7 → ~89; adds 3 of 5 missing HTML5 elements |
| **P1** | Improve extractability for landing pages | Content Team | +5–10 pts for 3 pages | Landing pages score 50.2 vs tutorials at 61.8 |
| **P2** | Reduce JS dependency in template | Platform Engineering | -9 pt delta → ~0 | AWS/Google show near-zero JS dependency |
| **P2** | Add content negotiation signals | Platform Engineering | Future readiness | llms.txt, markdown alternates, `<link rel="alternate">` |

---

## Appendix A: Full Learn Scores (Rendered)

| URL | Type | Score | SemHTML | Extract | StrData | DOMNav | Meta | HTTP |
|-----|------|-------|---------|---------|---------|--------|------|------|
| aks/faq | faq | **80.5** | 78.2 | 88.3 | 97.0 | 35.0 | 100 | 84.0 |
| aks/tutorial-kubernetes-prepare-app | tutorial | **64.1** | 72.7 | 88.0 | 12.0 | 35.0 | 85.0 | 84.0 |
| virtual-machines/linux/quick-create-cli | tutorial | **62.8** | 72.7 | 82.5 | 12.0 | 35.0 | 85.0 | 84.0 |
| cosmos-db/nosql/how-to-dotnet-get-started | tutorial | **62.2** | 72.7 | 82.8 | 12.0 | 35.0 | 85.0 | 77.8 |
| azure-functions/functions-reference-python | sample | **61.0** | 72.7 | 87.5 | 12.0 | 10.0 | 85.0 | 84.0 |
| architecture/.../compute-decision-tree | article | **59.0** | 72.7 | 81.3 | 12.0 | 35.0 | 85.0 | 84.0 |
| azure-resource-manager/.../resource-providers | article | **58.0** | 72.7 | 76.5 | 12.0 | 35.0 | 85.0 | 84.0 |
| app-service/quickstart-python | tutorial | **57.9** | 72.7 | 84.0 | 12.0 | 0.0 | 85.0 | 84.0 |
| ai-services/openai/concepts/models | article | **57.8** | 72.7 | 85.3 | 12.0 | 30.0 | 85.0 | 71.5 |
| training/.../compute-networking-services | article | **54.8** | 49.8 | 70.4 | 12.0 | 60.0 | 85.0 | 84.0 |
| answers/.../azure-data-factory | article | **54.2** | 49.8 | 73.3 | 27.0 | 55.0 | 70.0 | 64.0 |
| storage/blobs/storage-blobs-introduction | landing | **52.8** | 72.7 | 88.7 | 12.0 | 35.0 | 85.0 | 84.0 |
| dotnet/api/system.string | reference | **52.2** | 72.7 | 59.9 | 12.0 | 10.0 | 85.0 | 77.8 |
| azure-functions/functions-overview | landing | **51.4** | 72.7 | 74.5 | 12.0 | 35.0 | 85.0 | 84.0 |
| storage/common/storage-samples | sample | **50.0** | 72.7 | 33.5 | 12.0 | 35.0 | 85.0 | 84.0 |
| well-architected/security/overview | landing | **46.4** | 67.3 | 44.4 | 12.0 | 35.0 | 85.0 | 77.8 |

## Appendix B: Full Competitive Scores (Rendered)

| URL | Site | Type | Score | SemHTML | Extract | StrData | DOMNav | Meta | HTTP |
|-----|------|------|-------|---------|---------|---------|--------|------|------|
| storage/docs/introduction | Google | overview | **63.7** | 67.3 | 80.8 | 67.0 | 35.0 | 55.0 | 66.1 |
| storage/docs/discover-object-storage-console | Google | quickstart | **60.5** | 67.3 | 51.7 | 67.0 | 0.0 | 55.0 | 64.0 |
| storage/docs/json_api/v1/objects | Google | reference | **60.7** | 56.4 | 60.9 | 92.0 | 20.0 | 25.0 | 70.5 |
| storage/docs/creating-buckets | Google | how-to | **46.8** | 67.3 | 63.5 | 77.0 | 0.0 | 70.0 | 64.0 |
| S3/userguide/Welcome | AWS | overview | **58.8** | 20.0 | 83.6 | 85.0 | 30.0 | 70.0 | 86.0 |
| S3/userguide/GetStarted | AWS | quickstart | **64.4** | 23.6 | 70.9 | 85.0 | 85.0 | 70.0 | 86.0 |
| S3/API/API_GetObject | AWS | reference | **60.7** | 23.6 | 47.7 | 77.0 | 85.0 | 70.0 | 68.0 |
| s3/faqs/ | AWS | faq | **63.0** | 49.1 | 71.6 | 85.0 | 45.0 | 70.0 | 86.0 |
| Fetch_API | MDN | overview | **47.8** | 63.2 | 66.3 | 0.0 | 25.0 | 70.0 | 80.0 |
| Fetch_API/Using_Fetch | MDN | tutorial | **53.7** | 67.3 | 79.5 | 0.0 | 55.0 | 70.0 | 80.0 |
| Response | MDN | reference | **55.1** | 72.7 | 46.8 | 0.0 | 70.0 | 70.0 | 73.4 |
| Fetch_API/Basic_concepts | MDN | how-to | **54.6** | 63.2 | 76.3 | 0.0 | 55.0 | 70.0 | 80.0 |
| docs/ai-native | Mintlify | overview | **32.3** | 56.4 | 43.3 | 12.0 | 0.0 | 55.0 | 57.8 |
| docs/ai/llmstxt | Mintlify | how-to | **30.5** | 44.2 | 26.9 | 12.0 | 0.0 | 55.0 | 64.0 |
| docs/api-playground/openapi-setup | Mintlify | reference | **39.8** | 72.7 | 52.3 | 12.0 | 0.0 | 55.0 | 61.4 |
| docs/quickstart | Mintlify | quickstart | **32.6** | 27.3 | 20.0 | 12.0 | 45.0 | 55.0 | 61.4 |

## Appendix C: Wikipedia Exemplar Scores (Rendered)

| URL | Type | Score | SemHTML | Extract | StrData | DOMNav | Meta | HTTP |
|-----|------|-------|---------|---------|---------|--------|------|------|
| wiki/Microsoft_Azure | article | **62.2** | 72.7 | 69.1 | 92.0 | 0.0 | 70.0 | 48.0 |
| wiki/Object_storage | article | **61.4** | 72.7 | 70.0 | 87.0 | 0.0 | 70.0 | 48.0 |
| wiki/Virtual_machine | article | **61.4** | 72.7 | 69.9 | 87.0 | 0.0 | 70.0 | 48.0 |
| wiki/Azure_DevOps_Server | article | **59.7** | 61.8 | 70.2 | 92.0 | 0.0 | 70.0 | 48.0 |

## Appendix D: Methodology Notes

- **Tool:** Clipper v4.0 with performance-optimized evaluator
- **Render modes:** Both raw (no-JS) and rendered (full browser + axe-core)
- **Content-type detection:** Automatic via ms.topic metadata, JSON-LD @type, URL heuristics
- **Scoring:** 6-pillar weighted framework with content-type-specific weight profiles
- **Vendor-neutrality (v4):** `ms.topic` no longer credited in metadata pillar — only influences content-type classification. Ensures scores are comparable across vendors.
- **Field validation (v4):** Per-type JSON-LD field completeness for Article, FAQPage, HowTo, BreadcrumbList — validates required and recommended fields.
- **Classifier lockdown (v4):** Content-type classifications locked against golden file to prevent score drift.
- **Date:** April 22, 2026
- **Sample:** 16 Learn URLs (10 distinct ms.topic types) + 16 competitor/exemplar URLs (4 sites × 4 content types, matched by type) + 4 Wikipedia exemplar URLs (ceiling benchmark)
- **Limitations:** Sample size reflects template behavior more than content quality. Structured data scoring is strict — partial JSON-LD scores low if required fields are missing.
