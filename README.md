# Clipper - **C**ommand-**L**ine **I**nterface **P**rogressive **P**erformance **E**valuation & **R**eporting

**Standards-Based Access Gate Evaluation for Agent-Ready Content**

HTTP crawlers build search indexes. Copilot training pipelines ingest documentation. Retrieval-augmented agents pull content on demand to ground responses. Before any of them can succeed — before agents can sequence deployment steps, mediate task completion, or reason about architecture — the content itself must be accessible, extractable, and machine-readable.

Clipper measures that foundational layer. It evaluates live URLs against six industry-standard pillars (W3C Semantic HTML, Mozilla Readability, Schema.org, WCAG/axe-core, Dublin Core/OpenGraph, RFC 7231) and returns a score with a complete audit trail — no APIs, no credentials, no external dependencies.

## Table of Contents

- [Overview](#overview)
- [Clipper Standards Framework](#clipper-standards-framework)
- [Quick Demo Results](#quick-demo-results)
- [Installation](#installation) 
- [CLI Usage](#cli-usage)
- [Enterprise Features](#enterprise-features)
- [Quick Start Demo](#quick-start-demo)
- [Standards Authority Mapping](#standards-authority-mapping)
- [Example: Audit Trail Reports](#example-audit-trail-reports)
- [Scoring System](#scoring-system)
- [GitHub Integration](#github-integration) 
- [File Structure](#file-structure)
- [Real-World Use Cases](#real-world-use-cases)
- [Contributing](#contributing)

## Overview

Clipper provides standards-based content evaluation with:

- **Industry Standards**: Every score traceable to recognized authorities (W3C, Schema.org, Mozilla Readability, WCAG)
- **Zero API Dependencies**: Local evaluation using established standards frameworks
- **Immediate Usability**: Runs directly from command line without external dependencies
- **Enterprise Defensible**: Comprehensive audit trails and standards authority documentation
- **Agent-focused**: Evaluates whether agents can access, extract, and use page content for grounding

**Core Question:** *Can agents reliably access this content?*

## Clipper Standards Framework

### **Industry-Standard Evaluation Stack (API-Free)**
```python
# Standards-based dependencies - no APIs required
axe-selenium-python    # WCAG 2.1 DOM navigability (Deque Systems)
selenium              # W3C WebDriver standard  
extruct               # Schema.org structured data (W3C)
readability-lxml      # Mozilla Readability content extraction
httpx                 # Modern HTTP standard (RFC compliance)
beautifulsoup4        # HTML parsing standard
```

### **6-Pillar Evaluation Framework**
1. **🏗️ W3C Semantic HTML (25%)** - HTML5 semantic elements, ARIA roles
2. **📄 Content Extractability (20%)** - Mozilla Readability signal-to-noise analysis
3. **📊 Schema.org Structured Data (20%)** - JSON-LD quality, type validation, field completeness
4. **🛡️ DOM Navigability (15%)** - WCAG 2.1 / Deque axe-core DOM evaluation
5. **🏷️ Metadata Completeness (10%)** - Dublin Core, Schema.org, OpenGraph field coverage
6. **🌐 HTTP Compliance (10%)** - Reachability, redirects, robots.txt, cache headers, agent content hints

### **Standards Authority Mapping**
```python
STANDARDS_AUTHORITY = {
    'semantic_html': 'HTML5 Semantic Elements (W3C)',
    'content_extractability': 'Mozilla Readability (Firefox Reader View algorithm)',
    'structured_data': 'Schema.org (Google/Microsoft/Yahoo)',
    'dom_navigability': 'WCAG 2.1 AA (W3C) + axe-core (Deque Systems)',
    'metadata_completeness': 'Dublin Core + Schema.org + OpenGraph',
    'http_compliance': 'RFC 7231 + robots.txt + Cache headers'
}
```

### **Enterprise Defensibility**
- **✅ Every Score Traceable** - No black box algorithms
- **✅ Audit Trail Generated** - Complete evaluation methodology documented
- **✅ Standards Compliance** - Built on recognized industry authorities
- **✅ Reproducible Results** - Same evaluation across different environments

## Quick Demo Results

**Clipper standards-based evaluation** of major documentation sites:

| Site | Clipper Score | Primary Strengths | Improvement Areas |
|------|---------------|-------------------|-------------------|
| **Microsoft Learn** | **50-60 Range** | **Full metadata, good extractability, strong HTML** | **Structured data quality, DOM navigability** |
| **Wikipedia** | **62.2/100** | **Rich structured data (85), good extraction** | **DOM navigability, metadata gaps** |
| **GitHub Docs** | **54.9/100** | **Strong DOM navigability (85), good HTML** | **Structured data, metadata** |
| **MDN Web Docs** | **55.3/100** | **Excellent semantic HTML (84), good HTTP** | **Structured data quality** |

**Try Clipper immediately: No API keys, no setup required.**

```bash
# Works from any Copilot conversation (performance mode default)
python main.py express --urls https://your-docs.com --out results/
```

## Installation

### **Instant Setup (API-Free)**
```bash
# 1. Clone repository
git clone https://github.com/your-org/clipper-content-evaluation.git
cd clipper-content-evaluation

# 2. Install standards-based dependencies  
pip install -r requirements.txt

# 3. Ready to evaluate immediately!
python main.py express --help
```

### **Prerequisites**
- Python 3.7+
- No API keys required ✅
- No external services needed ✅
- Works completely offline ✅

### **Copilot Integration**
Clipper is designed for immediate use from GitHub Copilot conversations:

```bash
# Just run it - no configuration needed
python main.py express urls/clipper-test-urls.txt --out evaluation-results
```

## CLI Usage

Clipper provides a complete **standards-based evaluation pipeline**:

### **🚀 Express Mode (Recommended)**
Run complete Access Gate evaluation in one command:
```bash
# Single URL evaluation
python main.py express --urls https://developer.upsun.com/api/sdk/php --out results/

# Multiple URLs from file (batch optimized)  
python main.py express samples/urls.txt --out comprehensive-results/ --name evaluation

# Copilot-friendly (minimal output, maximum speed)
python main.py express urls.txt --out results/ --quiet

# Debug mode (slower, detailed analysis)
python main.py express urls.txt --out results/ --standard

# Performance benchmarking
python main.py express urls.txt --out results/ --benchmark
```

### **Step-by-Step Pipeline**
For detailed analysis, run individual components:

```bash
# 1. Crawl URLs (capture HTML snapshots)
python main.py crawl samples/urls.txt --out snapshots/

# 2. Parse Content (extract structural signals)  
python main.py parse snapshots/ --out parse-results.json

# 3. Standards Evaluation (Clipper methodology)
python main.py score parse-results.json --out scores.json

# 4. Generate Report (actionable insights)
python main.py report scores.json --md comprehensive-report.md
```

### **Content Negotiation Testing**
Test for agent-friendly content formats:
```bash
# HTTP content negotiation analysis
python main.py negotiate urls.txt --out negotiation-results/
```

## 🎯 Enterprise Features

### **Audit Trail Generation**
Every evaluation generates comprehensive documentation:

```json
{
  "standards_authority": {
    "semantic_html": "HTML5 Semantic Elements (W3C)",
    "content_extractability": "Mozilla Readability (Firefox Reader View algorithm)",
    "structured_data": "Schema.org (Google/Microsoft/Yahoo)",
    "dom_navigability": "WCAG 2.1 AA (W3C) + axe-core (Deque Systems)",
    "metadata_completeness": "Dublin Core + Schema.org + OpenGraph",
    "http_compliance": "RFC 7231 + robots.txt + Cache headers"
  },
  "audit_trail": {
    "dom_navigability": {
      "standard": "WCAG 2.1 AA (W3C) + axe-core (Deque Systems)",
      "method": "Automated DOM navigability evaluation",
      "violations_count": 3,
      "passes_count": 47
    },
    "content_extractability": {
      "standard": "Mozilla Readability",
      "extraction_ratio": 0.45,
      "extracted_text_length": 12340,
      "structure_preservation": 28
    }
  },
  "evaluation_methodology": "Clipper Standards-Based Access Gate"
}
```

### **Compliance Documentation**
- **Standards mapping** for each component
- **Evaluation methodology** documentation  
- **Score calculation** transparency
- **Industry authority** references

### **Enterprise Workflows**
```bash
# Quality gate integration
python main.py express staging-urls.txt --out quality-gate/ --quiet
if jq '.parseability_score >= 70' quality-gate/report_scores.json; then
  echo "✅ Quality gate passed"
else 
  echo "❌ Quality gate failed - see audit trail"
fi

# Batch evaluation (optimized performance)
python main.py express production-urls.txt --out batch-audit/ --name prod-audit

# Debug mode for detailed analysis  
python main.py express problem-urls.txt --out debug-analysis/ --standard
```

## 🚀 Quick Start Demo

**5-Minute Clipper Validation:**

```bash
# 1. Test with a documentation URL
echo "https://learn.microsoft.com/en-us/azure/azure-functions/functions-overview" > test-url.txt
python main.py express test-url.txt --out demo-results --name validation

# 2. Review standards-based results  
cat demo-results/validation.md

# 3. Examine audit trail
jq '.audit_trail' demo-results/validation_scores.json
```

**Expected Output:**
```
Clipper Evaluation Results:
├─ Total URLs: 1
├─ Average Score: 60.7/100  
└─ Agent-Ready: 0/1 (0.0%)

Component Breakdown:
  semantic_html: 72.7/100 (HTML5 Semantic Elements)
  content_extractability: 74.5/100 (Mozilla Readability)
  structured_data: 12.0/100 (Schema.org)
  dom_navigability: 35.0/100 (WCAG 2.1 / axe-core)
  metadata_completeness: 100.0/100 (Dublin Core / OpenGraph)
  http_compliance: 100.0/100 (RFC 7231 / robots / cache)
```

## Standards Authority Mapping

Clipper builds on established industry standards:

| Pillar | Authority | Implementation | Weight |
|--------|-----------|----------------|--------|
| **Semantic HTML** | W3C HTML5 Specification | BeautifulSoup + html5lib | 25% |
| **Content Extractability** | Mozilla Readability | readability-lxml | 20% |
| **Structured Data** | Schema.org Consortium | extruct library | 20% |
| **DOM Navigability** | W3C + Deque Systems | axe-selenium-python | 15% |
| **Metadata Completeness** | Dublin Core / Schema.org / OpenGraph | BeautifulSoup | 10% |
| **HTTP Compliance** | IETF RFC 7231 + robots.txt | httpx | 10% |

**🏛️ No Custom Algorithms:** Every score component is traceable to recognized industry standards.

## Example: Audit Trail Reports

Clipper generates comprehensive audit documentation:

### **Standards Compliance Summary**
```markdown
## Clipper Access Gate Evaluation

**Final Score:** 60.7/100 (moderate_issues)
**Evaluation Methodology:** Standards-Based Access Gate
**Standards Compliance:** 6/6 frameworks evaluated

### Pillar Analysis
- **Semantic HTML**: 72.7/100 (Good semantic coverage, ARIA roles present)
- **Content Extractability**: 74.5/100 (Clean extraction via Readability, structure preserved)
- **Structured Data**: 12.0/100 (Limited JSON-LD quality, missing key fields)
- **DOM Navigability**: 35.0/100 (Accessibility violations detected, capped per-rule)
- **Metadata Completeness**: 100.0/100 (All metadata fields present)
- **HTTP Compliance**: 100.0/100 (Reachable, no robots blocks, cache headers present)
```

### **Actionable Recommendations**
```markdown
### Priority Fixes (Standards-Based)

🔥 **Critical - Structured Data Quality**
- Add complete JSON-LD with @type, name, author, dateModified, description
- Validate Schema.org required properties for declared types
- Include OpenGraph and microdata alongside JSON-LD

⚠️ **Important - DOM Navigability**
- Add `aria-label` attributes to navigation elements
- Ensure color contrast ratios meet WCAG AA standards
- Fix heading hierarchy violations

📋 **Recommended - Semantic HTML**
- Add `<main>` element wrapper (HTML5 semantic requirement)
- Implement proper heading hierarchy (h1 → h2 → h3)
- Use `<article>` elements for content sections
```

## Scoring System

### **Access Gate Classification**
- **90-100**: `clean` - Fully agent-ready
- **75-89**: `minor_issues` - Nearly agent-ready  
- **60-74**: `moderate_issues` - Improvements needed
- **40-59**: `significant_issues` - Major optimization required
- **0-39**: `severe_issues` - Substantial restructuring needed

### **Pillar Weight Distribution**
Based on agent retrievability impact:
- **Semantic HTML (25%)** - Essential for content structure and agent parsing
- **Content Extractability (20%)** - Can agents cleanly extract the content?
- **Structured Data (20%)** - Machine-readable metadata for agent understanding
- **DOM Navigability (15%)** - Accessible DOM structure for crawlers
- **Metadata Completeness (10%)** - Identity, authorship, and currency signals
- **HTTP Compliance (10%)** - Reachability, crawl permissions, cacheability, agent content hints

### **Content Extractability Sub-Signals**
The Content Extractability score (20% of overall) uses Mozilla Readability to measure extraction quality:

| Sub-signal | Max Points | What it measures |
|---|---|---|
| **Signal-to-Noise Ratio** | 40 | Ratio of extracted meaningful text to total page text. Optimal range: 0.3-0.8. |
| **Structure Preservation** | 30 | Do headings, lists, and code blocks survive extraction? (10 pts each category) |
| **Boundary Detection** | 30 | Did Readability find a clear article boundary? Checks title extraction, content length, and `<main>`/`<article>` overlap. |

### **Structured Data Sub-Signals**
The Structured Data score (20% of overall) evaluates schema quality, not just presence:

| Sub-signal | Max Points | What it measures |
|---|---|---|
| **Type Appropriateness** | 20 | Does the `@type` match recognized content types (Article, WebPage, HowTo, etc.)? |
| **Field Completeness** | 30 | Does JSON-LD include key fields: `name`, `dateModified`, `author`, `description`, etc.? |
| **Multiple Formats** | 20 | Are JSON-LD, OpenGraph, and microdata all present? |
| **Schema Validation** | 30 | Are required properties present for the declared Schema.org type? |

### **HTTP Compliance Sub-Signals**
The HTTP Compliance score (10% of overall) is split into five sub-signals:

| Sub-signal | Max Points | What it measures |
|---|---|---|
| **HTML Reachability** | 15 | Does the URL serve a 200 response to `Accept: text/html`? |
| **Redirect Efficiency** | 25 | Chain length (0 hops optimal, >4 penalized), proper status codes, performance impact. |
| **Crawl Permissions** | 20 | `robots.txt` allows access + no `<meta name="robots" content="noindex">` blocking. |
| **Cache Headers** | 20 | Presence of `ETag`, `Last-Modified`, and `Cache-Control` headers. |
| **Agent Content Hints** | 20 | Signals that the page offers machine-readable alternate formats or LLM-specific endpoints. |

**Agent Content Hints** detects:
- `<link rel="alternate" type="text/markdown">` (6 pts) — markdown alternate link
- `<meta name="markdown_url">` (4 pts) — markdown URL metadata (e.g. Microsoft Learn)
- `data-llm-hint` attributes (4 pts) — explicit LLM guidance in HTML
- `llms.txt` references (3 pts) — site-level LLM endpoint declaration
- Non-HTML `<link rel="alternate">` (3 pts) — any non-HTML alternate format (JSON, XML, etc.)

### **Metadata Completeness Fields**
The Metadata Completeness score (10% of overall) checks for 7 key fields across Dublin Core, Schema.org, and OpenGraph:

| Field | Max Points | Sources checked |
|---|---|---|
| **Title** | 15 | `<title>`, `og:title`, Schema.org `name`/`headline` |
| **Description** | 15 | `<meta name="description">`, `og:description`, Schema.org `description` |
| **Author/Publisher** | 15 | `<meta name="author">`, Schema.org `author`/`publisher` |
| **Date** | 15 | `<meta>` date tags, Schema.org `dateModified`/`datePublished`, `<time>` elements |
| **Topic/Category** | 15 | `<meta name="ms.topic">`, Schema.org `articleSection`, `<meta name="keywords">` |
| **Language** | 10 | `<html lang="">`, `<meta http-equiv="content-language">` |
| **Canonical URL** | 15 | `<link rel="canonical">` |

## GitHub Integration

Clipper integrates seamlessly with CI/CD workflows:

```yaml
# .github/workflows/clipper-quality-gate.yml
name: Clipper Quality Gate
on: [pull_request]
jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Clipper Standards Evaluation
        run: |
          python main.py express docs-urls.txt --out pr-evaluation/ --quiet
          score=$(jq '.parseability_score' pr-evaluation/report_scores.json)
          if [ "$score" -lt 70 ]; then exit 1; fi
```

**No API keys required** - works immediately in any CI environment!

## File Structure

```
clipper/
├─ README.md                           # This comprehensive guide
├─ main.py                            # CLI entry point
├─ requirements.txt                   # Standards-based dependencies
├─ retrievability/
│  ├─ cli.py                         # Clipper CLI interface
│  ├─ access_gate_evaluator.py       # Standards-based evaluation engine
│  ├─ score.py                       # Clipper scoring orchestration
│  ├─ crawl.py                       # URL acquisition
│  ├─ parse.py                       # Content signal extraction
│  ├─ report.py                      # Audit trail generation
│  └─ schemas.py                     # Clipper data structures
├─ samples/
│  ├─ urls.txt                       # Sample Microsoft Learn URLs
│  └─ snapshots/                     # HTML snapshot storage
├─ clipper-test-results/              # Validation test outputs
├─ scripts/                         # Automation utilities
└─ docs/                           # Technical documentation
```

## Real-World Use Cases

### **📚 Documentation Teams**
```bash
# Pre-publication quality gates
python main.py express staging-docs-urls.txt --out quality-check/
# Get standards-based compliance report immediately
```

### **🏢 Enterprise Compliance**
```bash
# Quarterly accessibility audits
python main.py express corporate-docs.txt --out compliance-audit/
jq '.audit_trail.dom_navigability' compliance-audit/report_scores.json
```

### **🤖 Agent Integration Teams** 
```bash
# Validate agent-ready content
python main.py express api-documentation.txt --out agent-readiness/
# Verify content extractability, structured data, and metadata coverage
```

### **🔍 Quality Assurance**
```bash
# Regression testing for content changes
python main.py express --urls https://docs.updated-site.com --out regression-test/
# Compare against baseline standards compliance
```

## Why Clipper?

### **🚫 Problems with Previous Approaches**
- ❌ Required PageSpeed Insights API (rate limits, costs)
- ❌ Dependent on Google Lighthouse availability  
- ❌ Custom scoring algorithms (not defensible)
- ❌ Setup friction for Copilot integration

### **✅ Clipper Solutions**
- ✅ **API-Free Operation** - Works immediately, anywhere
- ✅ **Industry Standards** - Every score traceable to authorities
- ✅ **Enterprise Defensible** - Comprehensive audit trails
- ✅ **Immediate Copilot Usability** - No setup required
- ✅ **Standards Authority** - Built on W3C, IETF, Schema.org

**🎯 Result:** The definitive, enterprise-ready tool for agent-accessible content evaluation using trusted industry standards.

## Contributing

Clipper welcomes contributions that enhance standards-based evaluation:

1. **Standards Integration** - Add support for additional industry standards
2. **Evaluation Enhancement** - Improve component-specific analysis  
3. **Enterprise Features** - Expand audit trail and compliance documentation
4. **Agent Optimization** - Enhance agent-focused content quality metrics

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines and standards compliance requirements.

## License

Clipper - Standards-Based Access Gate Evaluator
Licensed under MIT License - see [LICENSE](LICENSE) for details.

---

**🚀 Clipper: Where industry standards meet agent-ready content evaluation.**



