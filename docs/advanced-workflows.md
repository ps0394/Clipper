# Advanced Workflows for Product Managers - YARA 2.0

This guide covers enterprise-grade workflows for documentation quality assessment using **YARA 2.0** (Yet Another Retrieval Analyzer), designed for product managers working on agentic retrieval, grounding, and task success.

## Overview: PM Use Cases with YARA 2.0

YARA 2.0 enables product managers to:
- **Benchmark documentation** against major cloud providers using proven hybrid scoring methodology
- **Generate stakeholder presentations** with scientifically accurate data (90% correlation with agent success)
- **Run large-scale evaluations** on hundreds of URLs with Lighthouse integration and progress tracking
- **Make data-driven decisions** based on accessibility, SEO, performance, and agent readiness metrics
- **Track improvement ROI** with before/after hybrid scores that predict real agent performance
- **Set up automated quality gates** with YARA 2.0 scoring thresholds in CI/CD pipelines

---

## 🚀 YARA 2.0 Evaluation Workflow

### 1. Standard YARA 2.0 Hybrid Evaluation
```bash
# Full YARA 2.0 with Lighthouse integration
python -m retrievability.cli express your-urls.txt --out evaluation-results/ --api-key YOUR_PAGESPEED_KEY

# YARA 2.0 without API key (content analysis + agent simulation)
python -m retrievability.cli express your-urls.txt --out evaluation-results/

# Legacy YARA for comparison
python -m retrievability.cli express your-urls.txt --out legacy-results/ --legacy
```

**YARA 2.0 Outputs:**
- Terminal summary with **hybrid scores** and component breakdowns
- `evaluation-results/report.md` - Enhanced report with Lighthouse metrics and agent predictions
- `evaluation-results/report_scores.json` - Hybrid scoring data with subscores
- `evaluation-results/*.html` - Captured HTML for evidence and debugging

### 2. Hybrid Score Analysis
```bash
# Analyze YARA 2.0 hybrid components
cat evaluation-results/report_scores.json | jq '.[0].subscores | {lighthouse_foundation, content_analysis, agent_performance}'

# Compare hybrid vs legacy scores
python -c "
import json
with open('evaluation-results/report_scores.json') as f:
    scores = json.load(f)
    for i, score in enumerate(scores):
        hybrid = score['parseability_score']
        lighthouse = score['subscores']['lighthouse_foundation']
        agent = score['subscores']['agent_performance']
        print(f'Page {i+1}: Hybrid {hybrid:.1f} | Lighthouse {lighthouse:.1f} | Agent {agent:.1f}')
"
```

### 3. HTML Evidence Extraction
```bash
# Generate presentation-ready HTML examples
python scripts/extract-html-evidence.py evaluation-results/ --examples 6
```

**Output:**
- ✅ **High scoring examples** (positive patterns to follow)
- ❌ **Low scoring examples** (issues to fix with specific recommendations)
- Concrete HTML code snippets for development teams

---

## 🤖 M365 Copilot Integration

### PowerShell Wrapper
The `scripts/Invoke-YaraEvaluation.ps1` script enables M365 Copilot integration:

```powershell
# Basic evaluation
.\scripts\Invoke-YaraEvaluation.ps1 -Urls @("https://docs.example.com/api","https://docs.example.com/guide")

# JSON-only output for programmatic use
.\scripts\Invoke-YaraEvaluation.ps1 -Urls @("url1","url2") -JsonOnly

# Summary-only for quick checks
.\scripts\Invoke-YaraEvaluation.ps1 -Urls @("url1","url2") -SummaryOnly
```

### In M365 Copilot
**User prompt**: "Run YARA evaluation on these documentation URLs: [paste URLs] and show me the raw scores"

**Copilot executes**: 
```powershell
.\scripts\Invoke-YaraEvaluation.ps1 -Urls @("https://url1.com","https://url2.com") -JsonOnly
```

**Returns**: Structured JSON with individual scores and failure modes for immediate analysis.

---

## 📊 Large-Scale Evaluation (100s of URLs)

### Bulk Processing
Use `scripts/bulk-evaluate.py` for enterprise-scale evaluation:

```bash
# Process 500 URLs in batches of 50
python scripts/bulk-evaluate.py large-url-set.txt --batch-size 50 --out bulk-results/
```

**Features:**
- **Progress tracking**: Real-time URL processing rate and ETA
- **Batch management**: Processes in chunks to handle large datasets
- **Executive summary**: High-level statistics and score distribution
- **Failure resilience**: Individual batch failures don't stop entire evaluation

**Output Structure:**
```
bulk-results/
├── batch_1_results/          # Individual batch results
├── batch_2_results/
├── ...
├── bulk_summary.json         # Executive dashboard data
└── evaluation_data.csv       # Structured data for analysis
```

### Executive Summary Format
```json
{
  "evaluation_stats": {
    "total_urls_processed": 487,
    "average_score": 72.3,
    "processing_time_minutes": 45.2
  },
  "score_distribution": {
    "agent_ready_80plus": {"count": 156, "percentage": 32.0},
    "needs_work_60_79": {"count": 203, "percentage": 41.7},
    "major_issues_below_60": {"count": 128, "percentage": 26.3}
  }
}
```

---

## 📈 Presentation Materials Generation

### Automated Report Generation
Use `scripts/generate-presentation-data.py` to create stakeholder-ready materials:

```bash
# Generate PowerPoint-ready JSON
python scripts/generate-presentation-data.py results/ --format powerpoint

# Generate executive summary markdown
python scripts/generate-presentation-data.py results/ --format summary

# Generate CSV for charts and analysis
python scripts/generate-presentation-data.py results/ --format csv
```

### PowerPoint Slide Data
The PowerPoint format generates structured JSON with ready-to-use slide content:

```json
{
  "slide_type": "executive_summary",
  "data": {
    "total_sites_evaluated": 9,
    "average_score": "68.1/100", 
    "agent_ready_percentage": "33.3%"
  }
}
```

```json
{
  "slide_type": "benchmark_comparison",
  "data": {
    "benchmarks": [
      {"name": "Wikipedia", "score": 88, "status": "✅"},
      {"name": "Microsoft Learn", "score": 84, "status": "✅"},
      {"name": "Your Docs", "score": 68.1, "status": "⚠️ Needs Work"},
      {"name": "AWS Docs", "score": 63, "status": "⚠️"},
      {"name": "Google Cloud", "score": 51, "status": "❌"}
    ]
  }
}
```

### Site-Specific Recommendations
Each site gets a detailed scorecard:

```json
{
  "slide_type": "site_evaluation",
  "data": {
    "site_name": "Microsoft Learn",
    "score": "78.1/100",
    "status": "⚠️ Needs Work", 
    "primary_issue": "Boilerplate Resistance",
    "fix": "Reduce boilerplate, improve content/chrome separation",
    "component_scores": {
      "Semantic Structure": "60/100",
      "Heading Hierarchy": "100/100",
      "Content Density": "85/100",
      "Boilerplate Resistance": "85/100"
    }
  }
}
```

---

## 🎯 PM Success Metrics & Benchmarks

### Industry Benchmarks (2026 Data)
| Documentation Site | Score | Agent-Ready Status |
|-------------------|-------|-------------------|
| Wikipedia | 88/100 | ✅ Gold Standard |
| Microsoft Learn | 84/100 | ✅ Enterprise Standard |
| **Your Target** | **75+/100** | **🎯 Goal** |
| AWS Docs | 63/100 | ⚠️ Needs Work |
| Google Cloud | 51/100 | ❌ Major Issues |
| Stack Overflow | 42/100 | ❌ Heavy Rework Needed |

### Success Criteria by Role

**📊 Executive Dashboard Metrics:**
- **Agent-Ready Percentage**: % of docs scoring 80+ points
- **Average Score Trend**: Month-over-month improvement
- **Benchmark Position**: Ranking vs. major cloud providers

**🛠️ Development Team KPIs:**
- **Critical Fixes**: Pages needing semantic HTML (15+ point gains)
- **Quick Wins**: Heading hierarchy fixes (12+ point gains)  
- **Technical Debt**: Boilerplate reduction efforts (18+ point gains)

**📝 Content Team Targets:**
- **Content Quality Score**: Content density + heading structure
- **Structural Consistency**: Heading hierarchy compliance rate
- **Update Priorities**: Lowest-scoring pages first

---

## ⚡ Complete PM Workflow Example

### Week 1: Assessment & Baseline
```bash
# 1. Evaluate current documentation
python -m retrievability.cli express docs-inventory.txt --out baseline/

# 2. Generate executive summary
python scripts/generate-presentation-data.py baseline/ --format summary

# 3. Extract HTML evidence for dev teams
python scripts/extract-html-evidence.py baseline/ --examples 10

# 4. Create presentation materials
python scripts/generate-presentation-data.py baseline/ --format powerpoint
```

### Week 2: Development Sprint Planning
- **Share baseline results** with engineering teams
- **Prioritize fixes** by score impact (Critical: +15pts, Important: +10pts)
- **Set sprint goals**: Target 3-5 highest-impact pages

### Week 3-4: Implementation & Validation  
```bash
# Re-evaluate after fixes
python -m retrievability.cli express docs-inventory.txt --out sprint-1-results/

# Compare improvement
python -c "
import json
# Load baseline and current scores
# Calculate improvements per page
# Generate improvement report
"
```

### Ongoing: Automated Monitoring
- **Set up CI/CD integration** (see [docs/automation.md](docs/automation.md))
- **Weekly score tracking** with `bulk-evaluate.py`
- **Quarterly benchmark reviews** against industry leaders

---

## 🚀 Quick Start Checklist for PMs

**Day 1: Setup & First Evaluation**
- [ ] Install YARA: `pip install -r requirements.txt`
- [ ] Prepare URL list of your documentation 
- [ ] Run first evaluation: `python -m retrievability.cli express urls.txt --out results/`
- [ ] Generate executive summary: `python scripts/generate-presentation-data.py results/ --format summary`

**Week 1: Stakeholder Presentation**
- [ ] Create benchmark comparison slide
- [ ] Extract HTML evidence for development teams  
- [ ] Set team score targets (recommend 75+ average)
- [ ] Identify quick wins (semantic HTML additions)

**Month 1: Process Integration**
- [ ] Set up M365 Copilot integration for ad-hoc evaluations
- [ ] Establish monthly bulk evaluation process
- [ ] Create development team scorecards
- [ ] Set up progress tracking dashboard

**Ongoing: Continuous Improvement**
- [ ] Monthly benchmark reviews
- [ ] Quarterly industry comparison updates  
- [ ] Feature request tracking for YARA enhancements
- [ ] Documentation quality KPI reporting

---

## 📞 Support & Advanced Use Cases

**Need help with:**
- Custom scoring criteria for your domain
- Integration with specific CI/CD pipelines  
- Large-scale evaluation optimization (1000+ URLs)
- Custom presentation templates
- Historical trend analysis setup

**See also:**
- [docs/automation.md](docs/automation.md) - CI/CD and scripting integration
- [docs/presentation-materials.md](docs/presentation-materials.md) - Creating executive dashboards
- [USER-INSTRUCTIONS.md](USER-INSTRUCTIONS.md) - Basic usage guide