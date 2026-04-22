# User Instructions: Clipper Content Evaluation

This guide walks you through using **Clipper** (Command-Line Interface Progressive Performance Evaluation & Reporting) to evaluate content for agent accessibility using standards-based evaluation methodology.

## What is Clipper

**Standards-Based Evaluation Engine**: Combines W3C Semantic HTML (25%) + Content Extractability (20%) + Schema.org (20%) + DOM Navigability (15%) + Metadata Completeness (10%) + HTTP Compliance (10%)
**Enterprise Defensible**: Built on established industry standards with complete audit trails
**API-Free Operation**: No external API dependencies - completely local evaluation

## Prerequisites

- **Python 3.7+** installed on your system
- **Internet connection** for crawling URLs
- **Command line access** (PowerShell, Terminal, or Command Prompt)
- **No API keys required** - Clipper operates completely offline

## Installation

### 1. Clone or Download the System
```bash
git clone https://github.com/your-org/clipper-content-evaluation.git
cd clipper-content-evaluation
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Test Installation
```bash
python main.py express --help
```

You should see **Clipper** in the help output with commands: `crawl`, `parse`, `score`, `report`, `negotiate`, and `express`.

## Optional Configuration

For enhanced logging and debugging:

```bash
# Enable verbose logging
export CLIPPER_LOG_LEVEL=DEBUG
```

## Documentation Reference

- **[README.md](README.md)** - Complete Clipper documentation
- **[docs/scoring.md](docs/scoring.md)** - Clipper standards-based scoring methodology

## Usage Examples

### Express Mode - Complete Clipper Evaluation

**Performance Mode (Default - 2.2x Faster):**
```bash
# Full Clipper standards-based scoring (performance optimized)
python main.py express --urls https://learn.microsoft.com/azure --out results/

# Multiple URLs evaluation (batch optimized)
python main.py express samples/urls.txt --out results/ --name comprehensive

# Clipper evaluation with minimal output (maximum speed)
python main.py express samples/urls.txt --out results/ --quiet
```

**Standard Mode (For Debugging):**
```bash
# Detailed analysis mode (slower, sequential processing)
python main.py express samples/urls.txt --out results/ --standard

# Performance comparison
python main.py express samples/urls.txt --out results/ --benchmark
```

**What Express Mode Does (2.2x Faster by Default):**
1. 📄 Crawls URLs and captures HTML content (concurrent operations)
2. 🔍 Parses content for structural signals (optimized parsing)
3. 📊 Scores using Clipper standards-based methodology (WebDriver pooling)
4. 📋 Generates comprehensive reports with audit trails (async I/O)

**Performance Benefits:**
- **Default Speed**: ~4 seconds per URL (performance mode)
- **Standard Mode**: ~9 seconds per URL (use --standard flag)
- **Batch Processing**: Concurrent evaluation for multiple URLs
- **CI/CD Optimized**: Faster quality gates and automated testing

**Output Files:**
- `results/report.md`: Human-readable report with recommendations
- `results/report_scores.json`: Clipper scores with component breakdown
- `results/report_parse.json`: Raw parsing results and structured data

### How the score is chosen for a page

Every evaluated page reports two 0–100 numbers:

- **`parseability_score`** — the *primary* number. Clipper detects the page's content type (article, landing, reference, sample, faq, or tutorial) and weighs the six pillars accordingly. Use this when asking "is this page good *for what it is*?"
- **`universal_score`** — the same pillar scores with the default *article* weights. Use this to compare pages of different types side by side, or to track a single page over time without profile changes biasing the trend.

Content type detection consults, in order:
1. `ms.topic` meta tag (authoritative on Microsoft Learn)
2. JSON-LD `@type`
3. URL path (`/samples/`, `/api/`, `/reference/`, `/quickstart/`, ...)
4. DOM heuristics
5. Default: `article`

The winning signal and matched value are recorded in `audit_trail._content_type.detection`. You can see them in `report_scores.json`:

```json
"content_type": "sample",
"parseability_score": 53.6,
"universal_score": 48.7,
"audit_trail": {
  "_content_type": {
    "profile": "sample",
    "detection": { "source": "url", "matched_value": "/samples/" },
    "weights": { "structured_data": 0.30, "content_extractability": 0.10, ... }
  }
}
```

See [docs/scoring.md#content-type-profiles](docs/scoring.md#content-type-profiles) for the complete weight table.

### Step-by-Step Pipeline

For detailed analysis, run individual components:

#### 1. Crawl URLs
```bash
# Download and snapshot content
python main.py crawl samples/urls.txt --out snapshots/
```

#### 2. Parse Content  
```bash
# Extract structural signals
python main.py parse snapshots/ --out parse-results.json
```
- Generates raw signals for Clipper standards-based scoring

#### 3. Score with Clipper Standards Engine
```bash
# Clipper standards-based scoring (recommended)
python main.py score parse-results.json --out scores.json

# Clipper with detailed component analysis
python main.py score parse-results.json --out scores.json --detailed
```

**What Clipper Standards Scoring Does:**
- **W3C Semantic HTML** (25%): HTML5 semantic elements and ARIA compliance
- **Content Extractability** (20%): Mozilla Readability signal-to-noise analysis
- **Schema.org Structured Data** (20%): JSON-LD quality, type validation, field completeness
- **DOM Navigability** (15%): WCAG 2.1 / Deque axe-core DOM evaluation
- **Metadata Completeness** (10%): Dublin Core, Schema.org, OpenGraph field coverage
- **HTTP Compliance** (10%): Reachability, redirects, robots.txt, cache headers, agent content hints

#### 4. Generate Reports
```bash
# Create comprehensive markdown report
python main.py report scores.json --md executive-summary.md
```
- Creates executive summary with Clipper scoring statistics
- Includes component-level recommendations
- Provides standards authority references

### Content Negotiation Testing
```bash
# Test HTTP content negotiation for agent compatibility
python main.py negotiate samples/urls.txt --out negotiation-results/
```

## Output Structure

### Comprehensive Results Directory
```
results/
├── report.md                 # Human-readable evaluation report  
├── report_scores.json        # Clipper component scores
├── report_parse.json         # Raw content analysis
└── snapshots/                # HTML content snapshots
    ├── site1_snapshot.html
    └── site2_snapshot.html
```

### Clipper Score Format
```json
{
  "parseability_score": 60.7,
  "failure_mode": "moderate_issues",
  "component_scores": {
    "semantic_html": 72.7,
    "content_extractability": 74.5,
    "structured_data": 12.0,
    "dom_navigability": 35.0,
    "metadata_completeness": 100.0,
    "http_compliance": 71.5
  },
  "audit_trail": {
    "http_compliance": {
      "score_breakdown": {
        "html_reachability": 15,
        "redirect_efficiency": 12.5,
        "crawl_permissions": 20,
        "cache_headers": 20,
        "agent_content_hints": 4
      }
    }
  },
  "standards_authority": {
    "semantic_html": "HTML5 Semantic Elements (W3C)",
    "content_extractability": "Mozilla Readability (Firefox Reader View algorithm)",
    "structured_data": "Schema.org (Google/Microsoft/Yahoo)",
    "dom_navigability": "WCAG 2.1 AA (W3C) + axe-core (Deque Systems)",
    "metadata_completeness": "Dublin Core + Schema.org + OpenGraph",
    "http_compliance": "RFC 7231 + robots.txt + Cache headers"
  }
}
```

## HTTP Compliance Scoring

Clipper evaluates HTTP compliance across **five sub-signals** (10% of total score):

### **Sub-Signal Breakdown**
| Sub-signal | Max Points | What it measures |
|---|---|---|
| **HTML Reachability** | 15 | Does the URL serve a 200 response to `Accept: text/html`? |
| **Redirect Efficiency** | 25 | Chain length, proper status codes, performance impact |
| **Crawl Permissions** | 20 | `robots.txt` allows access + no `noindex` meta |
| **Cache Headers** | 20 | Presence of `ETag`, `Last-Modified`, `Cache-Control` |
| **Agent Content Hints** | 20 | Machine-readable alternate formats and LLM-specific endpoints |

### **Agent Content Hints (New)**
Detects whether pages declare machine-readable content formats:
- `<link rel="alternate" type="text/markdown">` (6 pts)
- `<meta name="markdown_url">` (4 pts) — e.g. Microsoft Learn
- `data-llm-hint` attributes (4 pts)
- `llms.txt` references (3 pts)
- Non-HTML `<link rel="alternate">` (3 pts)

### **Redirect Efficiency**
- 0 redirects: Full points (optimal)
- 1-2 redirects: Minor deduction
- 3-4 redirects: Moderate penalty
- 5+ redirects: Significant penalty

## Quick Command Reference

```bash
# Single URL quick evaluation (performance mode default)
python main.py express --urls https://example.com --out quick/

# Batch evaluation with URLs from file (2.2x faster)
python main.py express urls.txt --out batch-results/

# Quiet mode for CI/CD integration (maximum speed)
python main.py express urls.txt --out results/ --quiet

# Debug mode for detailed analysis
python main.py express urls.txt --out results/ --standard

# Performance benchmarking
python main.py express urls.txt --out results/ --benchmark

# Content negotiation analysis
python main.py negotiate urls.txt --out negotiate/

# Help for any command
python main.py [command] --help
```

## Troubleshooting

### Common Issues

**Issue**: Import errors during installation
**Solution**: Ensure Python 3.7+ and run `pip install --upgrade pip` before installing requirements

**Issue**: Selenium WebDriver errors
**Solution**: Chrome/Chromium browser required for automated accessibility testing

**Issue**: Network connectivity errors
**Solution**: Check internet connection and firewall settings for HTTPS access

### Getting Help

1. **Check command help**: `python main.py [command] --help`
2. **Enable verbose logging**: Set `CLIPPER_LOG_LEVEL=DEBUG`
3. **Review parsing results**: Check `report_parse.json` for content extraction issues
4. **Validate URLs**: Ensure URLs are accessible and return valid HTML content

## Enterprise Integration

### Quality Gate Integration  
```bash
# CI/CD pipeline example (2.2x faster evaluation)
python main.py express staging-urls.txt --out ci-results/ --quiet
if [ $(jq -r '.parseability_score >= 70' ci-results/report_scores.json) == "true" ]; then
  echo "✅ Quality gate passed - deploying"
  deploy_application
else
  echo "❌ Quality gate failed - blocking deployment"
  exit 1
fi

# Performance comparison in CI
python main.py express urls.txt --out perf-test/ --benchmark

# Legacy CI/CD pipeline example
python main.py express staging-urls.txt --out quality-gate/ --quiet
SCORE=$(jq '.overall_score' quality-gate/report_scores.json)
if (( $(echo "$SCORE >= 70.0" | bc -l) )); then
  echo "✅ Quality gate passed: $SCORE"
else
  echo "❌ Quality gate failed: $SCORE - see audit trail"
  exit 1
fi
```

### Audit Trail Access
Clipper generates complete audit trails for compliance:
- Standards authority mapping for each component
- Evaluation methodology documentation
- Score calculation transparency
- Industry framework references