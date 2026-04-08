# YARA - Yet Another Retrieval Analyzer

A CLI-first tool for evaluating documentation page retrievability and readiness for AI agent consumption. **Now with actionable reports featuring code examples and priority scoring!**

## Table of Contents

- [Overview](#overview)
- [Quick Demo Results](#quick-demo-results)
- [Installation](#installation)
- [CLI Usage](#cli-usage)
  - [Content Negotiation Testing](#-5-test-content-negotiation)
- [Example: Enhanced Actionable Reports](#example-enhanced-actionable-reports)
- [🎯 YARA's Actionable Report Features](#-yaras-actionable-report-features)
- [🚀 Quick Start Demo](#-quick-start-demo)
- [GitHub Integration](#github-integration)
- [Demo & Presentation](#demo--presentation)
- [Scoring System](#scoring-system)
- [File Structure](#file-structure)
- [Non-Goals](#non-goals)
- [Real-World Use Cases for YARA](#real-world-use-cases-for-yara)
- [Contributing](#contributing)
- [License](#license)

## Overview

YARA measures whether documentation pages are:
- **Crawlable & accessible** as HTML
- **Parsable / extractable** into primary content (low chrome, clean structure)
- **Structurally ready** for retrieval systems (inputs to later retrieval evaluation)
- **🆕 Agent-optimized** with content negotiation (markdown, JSON, plain text alternatives)

**🚀 What makes YARA special:**
- **Actionable insights**: Get specific HTML fixes with before/after code examples
- **Priority scoring**: Know which fixes give the biggest score improvements
- **🆕 Content negotiation testing**: Detect markdown, JSON, and plain text alternatives
- **Agent optimization detection**: Identify sites optimized for AI consumption
- **Multi-cloud ready**: Evaluate Microsoft, AWS, Google, and other major documentation sites
- **Demo-proven**: Wikipedia (88/100) outperforms AWS Docs (63/100) and Google Cloud (51/100)

## Quick Demo Results

- [Non-Goals](#non-goals)
- [Real-World Use Cases for YARA](#real-world-use-cases-for-yara)
- [Quick Demo Results](#quick-demo-results)
- [Installation](#installation)
- [CLI Usage](#cli-usage)
  - [Content Negotiation Testing](#-5-test-content-negotiation)
- [Example: Enhanced Actionable Reports](#example-enhanced-actionable-reports)
- [🎯 YARA's Actionable Report Features](#-yaras-actionable-report-features)
- [🚀 Quick Start Demo](#-quick-start-demo)
- [GitHub Integration](#github-integration)
- [Demo & Presentation](#demo--presentation)
- [Scoring System](#scoring-system)
- [File Structure](#file-structure)
- [Contributing](#contributing)
- [License](#license)

## Quick Demo Results

Real evaluation of major documentation sites (as of 2026-04-08):

| Site | Score | Status | Key Insight |
|------|-------|--------|-------------|
| **GitHub Docs** | **98/100** | **🤖 Agent-Ready** | **Serves clean markdown on demand** |
| **Microsoft Learn** | **92/100** | **🤖 Agent-Ready** | **Advanced content negotiation** |
| Wikipedia | 88/100 | ✅ Clean | Content structure beats brand names |
| Microsoft Learn | 84/100 | ✅ Clean | Enterprise documentation standard |
| Google Developer | 77/100 | ⚠️ Noisy | Good content, extraction challenges |
| AWS Docs | 63/100 | ❌ Structure | Missing semantic HTML |
| Google Cloud | 51/100 | ❌ Structure | Major structure gaps |
| Stack Overflow | 42/100 | ❌ Structure | Heavy boilerplate contamination |

*Submit your own URLs to YARA for evaluation: `python -m retrievability.cli negotiate demo-urls.txt --out results/`*

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

### 3. Score Results
YARA scores parse results and classifies failure modes:
```bash
python -m retrievability.cli score reports/parse.json --out reports/report.json
```

### 4. Generate Report
YARA creates human-readable markdown reports with actionable fixes:
```bash
python -m retrievability.cli report reports/report.json --md reports/report.md
```

### 🆕 5. Test Content Negotiation
YARA tests for agent-friendly alternatives (markdown, JSON, plain text):
```bash
python -m retrievability.cli negotiate samples/urls.txt --out reports/negotiation/
```

### 🆕 Express Mode (All-in-One)
Run the complete YARA pipeline in a single command:
```bash
python -m retrievability.cli express urls.txt --out results/
```

**📚 Documentation:**
- **New users**: See [USER-INSTRUCTIONS.md](USER-INSTRUCTIONS.md) for step-by-step guide
- **Product managers**: See [docs/advanced-workflows.md](docs/advanced-workflows.md) for enterprise workflows
- **Developers**: See [docs/automation.md](docs/automation.md) for scripting and integration
- **Scoring details**: See [docs/scoring.md](docs/scoring.md) for technical details

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