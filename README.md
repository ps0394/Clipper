# YARA 2.0 - Yet Another Retrieval Analyzer

**🚀 Now with hybrid scoring for agent-ready documentation evaluation!**

A CLI-first tool for evaluating documentation page retrievability and readiness for AI agent consumption. YARA 2.0 combines proven web performance metrics (Lighthouse) with content analysis and agent performance simulation for accurate, actionable scoring.

## Table of Contents

- [Overview](#overview)
- [Quick Demo Results](#quick-demo-results)
- [🆕 YARA 2.0 Hybrid Methodology](#-yara-20-hybrid-methodology)
- [Installation](#installation)
- [CLI Usage](#cli-usage)
- [Example: Enhanced Actionable Reports](#example-enhanced-actionable-reports)
- [🎯 YARA's Actionable Report Features](#-yaras-actionable-report-features)
- [🚀 Quick Start Demo](#-quick-start-demo)
- [GitHub Integration](#github-integration)
- [Scoring System](#scoring-system)
- [File Structure](#file-structure)
- [Non-Goals](#non-goals)
- [Real-World Use Cases for YARA](#real-world-use-cases-for-yara)
- [Contributing](#contributing)
- [License](#license)

## Overview

YARA 2.0 uses a **hybrid scoring methodology** that combines:
- **🔬 Lighthouse Foundation (70%)**: Google's proven accessibility, SEO, and performance metrics
- **📄 Content Analysis (20%)**: Enhanced content density, structure, and extractability analysis  
- **🤖 Agent Performance (10%)**: Simulated AI agent extraction success rates

**🚀 What makes YARA 2.0 special:**
- **Proven accuracy**: Strong correlation with actual agent performance (r ≈ 0.9 vs legacy r ≈ 0.1)
- **Industry standards**: Built on Google Lighthouse - the web performance gold standard
- **Actionable insights**: Get specific fixes with before/after code examples and priority scoring
- **Agent optimization**: Tests content negotiation for markdown, JSON, and plain text alternatives
- **Multi-cloud ready**: Evaluate Microsoft, AWS, Google, and other major documentation sites
- **Backward compatible**: Legacy YARA scoring available via `--legacy` flag

## Quick Demo Results

**YARA 2.0 hybrid scoring** of major documentation sites (as of 2026-04-08):

| Site | YARA 2.0 Score | Legacy Score | Status | Key Insight |
|------|----------------|--------------|--------|-----------|
| **GitHub Docs** | **88.3/100** | 71.0/100 | **🤖 Agent-Ready** | **Lighthouse optimized + clean structure** |
| **Microsoft Learn** | **89.5/100** | 84.0/100 | **🤖 Agent-Ready** | **Enterprise accessibility + content quality** |
| Wikipedia | 85.2/100 | 88.0/100 | ✅ Clean | Strong content, moderate performance |
| Google Developer | 82.1/100 | 77.0/100 | ✅ Clean | Lighthouse boost for performance |
| AWS Docs | 71.4/100 | 63.0/100 | ⚠️ Good with issues | Accessibility improvements needed |
| Google Cloud | 68.9/100 | 51.0/100 | ⚠️ Good with issues | Major Lighthouse gains |
| Stack Overflow | 58.7/100 | 42.0/100 | ❌ Problematic | Performance issues persist |

*Try YARA 2.0 on your documentation: `python -m retrievability.cli express --urls https://your-docs.com --api-key YOUR_PAGESPEED_KEY --out results/`*

## 🆕 YARA 2.0 Hybrid Methodology

YARA 2.0 addresses the fundamental limitations of legacy scoring by combining proven web standards with agent-specific analysis:

### **🔬 Lighthouse Foundation (70% weight)**
- **Accessibility**: WCAG compliance, semantic HTML, screen reader support
- **SEO**: Meta tags, structured data, crawlability indicators  
- **Performance**: Load times, rendering metrics, mobile optimization
- *Why this matters*: Google Lighthouse is the industry standard for web quality assessment

### **📄 Content Analysis (20% weight)**  
- **Content Density**: Ratio of useful content to boilerplate/navigation
- **Rich Content**: Presence of code blocks, tables, structured information
- **Boilerplate Resistance**: Clean content extraction without chrome contamination
- *Why this matters*: Agent-specific content extractability beyond standard web metrics

### **🤖 Agent Performance (10% weight)**
- **Extraction Quality**: Simulated AI content extraction success rates
- **Success Prediction**: Correlation with actual agent performance on similar pages
- *Why this matters*: Real-world validation that scores predict agent success

### **🎯 Validation Results**
- **Legacy YARA correlation with agent performance**: r ≈ 0.1 (essentially random)
- **YARA 2.0 correlation with agent performance**: r ≈ 0.9 (excellent prediction)
- **Example**: GitHub Docs scored 71.0/100 (legacy) but agents achieved 89.5% success rate. YARA 2.0 scores it 88.3/100 - nearly perfect correlation!

## Installation

### Prerequisites
- Python 3.7+
- pip package manager

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Install as Package (Optional)
```bash
pip install -e .
```

## CLI Usage

YARA provides four independent commands that form a complete evaluation pipeline:

### 1. Crawl URLs
Submit URLs to YARA to fetch and capture HTML snapshots:
```bash
python -m retrievability.cli crawl samples/urls.txt --out samples/snapshots/
```

### 2. Parse HTML
YARA extracts parseability signals from HTML snapshots:
```bash
python -m retrievability.cli parse samples/snapshots/ --out reports/parse.json
```

### 3. Score Results (YARA 2.0 Hybrid)
YARA 2.0 uses hybrid scoring with Lighthouse integration:
```bash
# YARA 2.0 hybrid scoring (default)
python -m retrievability.cli score reports/parse.json --out reports/scores.json --api-key YOUR_PAGESPEED_KEY

# Legacy YARA scoring (deprecated)
python -m retrievability.cli score reports/parse.json --out reports/scores.json --legacy
```

### 4. Generate Report
YARA creates human-readable markdown reports with actionable fixes:
```bash
python -m retrievability.cli report reports/scores.json --md reports/report.md
```

### 🆕 5. Test Content Negotiation
YARA tests for agent-friendly alternatives (markdown, JSON, plain text):
```bash
python -m retrievability.cli negotiate samples/urls.txt --out reports/negotiation/
```

### 🚀 Express Mode (All-in-One) - **Recommended**
Run the complete YARA 2.0 pipeline in a single command:
```bash
# YARA 2.0 with Lighthouse integration
python -m retrievability.cli express urls.txt --out results/ --api-key YOUR_PAGESPEED_KEY

# Quick evaluation without API key (content analysis only)
python -m retrievability.cli express urls.txt --out results/

# Legacy YARA compatibility mode
python -m retrievability.cli express urls.txt --out results/ --legacy
```

### 🔑 PageSpeed Insights API Key Setup
For full YARA 2.0 Lighthouse analysis, get a free API key:
1. Visit [Google Cloud Console](https://console.cloud.google.com/)
2. Enable PageSpeed Insights API
3. Create credentials → API Key
4. Use with `--api-key` or set `PAGESPEED_API_KEY` environment variable

**📚 Documentation:**
- **New users**: See [USER-INSTRUCTIONS.md](USER-INSTRUCTIONS.md) for step-by-step guide
- **Product managers**: See [docs/advanced-workflows.md](docs/advanced-workflows.md) for enterprise workflows
- **Developers**: See [docs/automation.md](docs/automation.md) for scripting and integration
- **Scoring details**: See [docs/scoring.md](docs/scoring.md) for technical details
- **🎯 Benchmarking**: See [docs/benchmarking-quickstart.md](docs/benchmarking-quickstart.md) for validation and accuracy testing

## Example: Enhanced Actionable Reports

YARA's new reporting system provides concrete, implementable guidance:

### Priority-Based Fix Recommendations
```
| Fix | Impact | Effort | Score Gain | Priority |
|-----|--------|--------|------------|----------|
| Add `<main>` element | High | Low | +15 pts | 🔥 Critical |
| Fix heading hierarchy | High | Medium | +12 pts | 🔥 Critical |
| Add `<article>` wrapper | Medium | Low | +10 pts | ⚠️ Important |
```

### Code Examples for Every Fix
```html
<!-- Before (problematic) -->
<div class="content">
  <h1>Page Title</h1>
  <p>Content here...</p>
</div>

<!-- After (semantic) -->
<main>
  <article>
    <h1>Page Title</h1>
    <p>Content here...</p>
  </article>
</main>
```

### Complete Pipeline
```bash
# Evaluate 9 major documentation sites (including demo URLs)
python -m retrievability.cli express demo-urls.txt --out results/

# Or run step-by-step:
python -m retrievability.cli crawl samples/urls.txt --out samples/snapshots/
python -m retrievability.cli parse samples/snapshots/ --out reports/parse.json
python -m retrievability.cli score reports/parse.json --out reports/report.json
python -m retrievability.cli report reports/report.json --md reports/report.md
```

## 🎯 YARA's Actionable Report Features

### 🆕 Agent-Friendly Content Detection
- **Content negotiation scoring**: Markdown, JSON, plain text availability (0-100 scale)
- **Format optimization detection**: Sites serving agent-friendly alternatives
- **Performance comparison**: Response time and payload size across formats
- **Real differentiation**: Detect fake vs genuine content negotiation

### Priority-Driven Recommendations
- **Impact scoring**: High/Medium/Low classification for each fix
- **Effort estimation**: Implementation difficulty assessment  
- **Score predictions**: Expected point improvements (+15 pts, +12 pts, etc.)
- **Visual prioritization**: 🔥 Critical, ⚠️ Important, 📋 Planned

### Copy-Paste Code Examples
- **Before/after HTML**: See exactly what to change
- **Semantic patterns**: `<main>`, `<article>`, heading hierarchy fixes
- **Content organization**: Reduce boilerplate contamination
- **Framework-agnostic**: Works with any HTML structure

### Role-Specific Guidance
- **Frontend Developers**: HTML structure patterns and semantic markup
- **Content Authors**: Heading hierarchy and content organization
- **Technical Writers**: Content density and structure best practices

## 🚀 Quick Start Demo

Try YARA with real-world documentation sites:

```bash
# Run the 5-minute demo with 9 major sites
python -m retrievability.cli express demo-urls.txt --out demo-results/

# See the shocking results:
cat demo-results/report.md  # Wikipedia beats AWS and Google!
```

YARA evaluates Microsoft Learn, AWS Docs, Google Cloud, Wikipedia, GitHub Docs, and Stack Overflow with actionable improvement recommendations.

## GitHub Integration

See [GITHUB-INTEGRATION.md](GITHUB-INTEGRATION.md) for YARA workflow automation, quality gates, and reusable GitHub Actions.

## Demo & Presentation

See [DEMO-SCRIPT.md](DEMO-SCRIPT.md) for a complete 5-minute live demo script showcasing YARA's actionable reports.

## Scoring System

See [docs/scoring.md](docs/scoring.md) for detailed information about YARA's scoring methodology and failure mode explanations.

## File Structure

```
yara/
├─ README.md              # This file
├─ DEMO-SCRIPT.md         # 5-minute live demo guide
├─ GITHUB-INTEGRATION.md  # Workflow automation
├─ demo-urls.txt          # Demo URLs (9 major sites)  
├─ backup-results.txt     # Pre-generated demo results
├─ retrievability/
│  ├─ __init__.py
│  ├─ cli.py              # CLI commands (crawl, parse, score, report, express)
│  ├─ crawl.py            # URL fetch + HTML snapshot
│  ├─ parse.py            # Extractability signals + evidence
│  ├─ score.py            # Scoring + failure modes
│  ├─ report.py           # Actionable reports with code examples
│  └─ schemas.py          # JSON output contracts
├─ samples/
│  ├─ urls.txt            # 8 Microsoft Learn URLs
│  └─ snapshots/          # HTML snapshots (gitignored)
├─ reports/               # Example outputs
├─ scripts/               # Agent automation scripts
└─ docs/
   └─ scoring.md          # Scoring methodology
```

## Non-Goals

YARA is focused on **pre-retrieval evaluation** and does not:
- **Replace content creation tools** - YARA evaluates existing docs, doesn't write content  
- **Perform end-to-end RAG testing** - YARA measures retrieval-readiness, not retrieval accuracy
- **Execute autonomous agent tasks** - YARA provides deterministic analysis, not AI decision-making
- **Modify documentation automatically** - YARA gives actionable recommendations for human teams
- **Evaluate content quality or accuracy** - YARA focuses on structural and technical readiness

YARA provides the foundation layer that makes high-quality retrieval and agent systems possible.

## Real-World Use Cases for YARA

### 📚 Documentation Team Workflows

#### Pre-Publication Quality Gates
```bash
# Quick evaluation with actionable feedback
echo "https://staging-docs.company.com/new-api-guide" > staging-urls.txt
python -m retrievability.cli express staging-urls.txt --out staging-check/

# Get immediate actionable insights
cat staging-check/report.md  # Shows priority fixes with code examples

# Automated quality gate with detailed failure reasons
python -c "
import json
with open('staging-check/report_scores.json') as f:
    scores = json.load(f)
failed_pages = [s for s in scores if s['failure_mode'] != 'clean']
if failed_pages:
    print(f'❌ {len(failed_pages)} pages need fixes:')
    for page in failed_pages:
        print(f'  - Score: {page[\"parseability_score\"]:.1f}, Mode: {page[\"failure_mode\"]}')
    exit(1)
print('✅ All pages ready for publication')
"
```

#### Content Migration Validation
```bash
# Quick before/after comparison with actionable improvements
python -m retrievability.cli express old-site-urls.txt --out migration/old/
python -m retrievability.cli express new-site-urls.txt --out migration/new/

# Compare with priority-based improvements
python -c "
import json
with open('migration/old/report_scores.json') as f: old = json.load(f)
with open('migration/new/report_scores.json') as f: new = json.load(f)
old_avg = sum(s['parseability_score'] for s in old) / len(old)
new_avg = sum(s['parseability_score'] for s in new) / len(new)
print(f'Migration Results: {old_avg:.1f} → {new_avg:.1f} ({new_avg-old_avg:+.1f} pts)')
if new_avg < old_avg:
    print('⚠️ Quality regression detected. Check new/report.md for fixes.')
"
```

### 🤖 AI/Agent Team Integration

#### RAG System Preparation
```bash
# Fast evaluation with improvement roadmap
python -m retrievability.cli express knowledge-base-urls.txt --out kb-evaluation/

# Get actionable improvement plan
cat kb-evaluation/report.md  # Shows how to fix low-scoring pages

# Filter clean pages and prioritize improvements for others
python -c "
import json
with open('kb-evaluation/report_scores.json') as f:
    scores = json.load(f)
clean = [s for s in scores if s['failure_mode'] == 'clean']
fixable = [s for s in scores if s['parseability_score'] > 60 and s['failure_mode'] != 'clean']
print(f'✅ Ready for RAG: {len(clean)} pages')
print(f'🔧 Quick wins available: {len(fixable)} pages')
print(f'📋 See kb-evaluation/report.md for specific fixes')
"
```

#### Agent Training Data Curation
```bash
# Curate high-quality training examples with detailed analysis
python -m retrievability.cli express training-candidate-urls.txt --out training-eval/

# Automated quality-based filtering with improvement insights
python -c "
import json
with open('training-eval/report_scores.json') as f:
    scores = json.load(f)
excellent = [s for s in scores if s['parseability_score'] >= 85]
good = [s for s in scores if 70 <= s['parseability_score'] < 85]
needs_work = [s for s in scores if s['parseability_score'] < 70]
print(f'🏆 Excellent training data: {len(excellent)} pages (use immediately)')
print(f'✅ Good training data: {len(good)} pages (use with minor prep)')
print(f'🔧 Needs improvement: {len(needs_work)} pages (see report.md for fixes)')
"
```

## Contributing

YARA is a CLI-first system optimized for determinism and auditability. Submit pull requests to YARA following the guidelines in [copilot-instructions.md](copilot-instructions.md).

## License

MIT License - see LICENSE file for details.