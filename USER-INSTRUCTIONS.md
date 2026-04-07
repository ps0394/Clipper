# User Instructions: Retrievability Evaluation System

This guide walks you through using the retrievability evaluation system to assess documentation pages for agent and retrieval system readiness.

## Prerequisites

- **Python 3.7+** installed on your system
- **Internet connection** for crawling URLs
- **Command line access** (PowerShell, Terminal, or Command Prompt)

## Installation

### 1. Clone or Download the System
```bash
git clone https://github.com/ps0394/Retrieval.git
cd Retrieval
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Verify Installation
```bash
python -m retrievability.cli --help
```
You should see the command help menu with 4 available commands: `crawl`, `parse`, `score`, `report`.

## Basic Usage

### Step-by-Step Evaluation

#### 1. Prepare Your URL List
Create a text file with URLs to evaluate (one per line):

```bash
# Create urls.txt
echo "https://learn.microsoft.com/en-us/azure/functions/functions-overview" > urls.txt
echo "https://docs.python.org/3/tutorial/introduction.html" >> urls.txt
echo "https://kubernetes.io/docs/concepts/overview/" >> urls.txt
```

#### 2. Crawl Documentation Pages
```bash
python -m retrievability.cli crawl urls.txt --out snapshots/
```
**What this does:**
- Fetches each URL and saves the HTML content
- Creates `snapshots/crawl_results.json` with metadata
- Saves individual HTML files with unique names

#### 3. Extract Parseability Signals
```bash
python -m retrievability.cli parse snapshots/ --out results/parse.json
```
**What this does:**
- Analyzes HTML structure for semantic elements (`<main>`, `<article>`)
- Checks heading hierarchy (H1→H2→H3 progression)
- Measures content density and boilerplate leakage
- Generates raw signals for scoring

#### 4. Score and Classify Results
```bash
python -m retrievability.cli score results/parse.json --out results/scores.json
```
**What this does:**
- Converts signals to 0-100 parseability scores
- Classifies failure modes: `clean`, `structure-missing`, `extraction-noisy`
- Provides component subscores for detailed analysis

#### 5. Generate Human Report
```bash
python -m retrievability.cli report results/scores.json --md results/report.md
```
**What this does:**
- Creates executive summary with statistics
- Lists individual page results with actionable insights
- Identifies who should fix issues (Frontend Developer vs Content Author)

## Advanced Usage

### Custom URL Lists

Create focused evaluations for specific documentation sets:

```bash
# Microsoft Learn pages
echo "https://learn.microsoft.com/en-us/dotnet/core/introduction" > ms-learn.txt
echo "https://learn.microsoft.com/en-us/azure/app-service/overview" >> ms-learn.txt

# API documentation
echo "https://docs.github.com/en/rest/overview" > api-docs.txt
echo "https://stripe.com/docs/api" >> api-docs.txt

# Run separate evaluations
python -m retrievability.cli crawl ms-learn.txt --out ms-snapshots/
python -m retrievability.cli crawl api-docs.txt --out api-snapshots/
```

### Batch Processing Multiple Projects

```bash
# Evaluate multiple documentation sets
for project in project-a project-b project-c; do
    python -m retrievability.cli crawl ${project}-urls.txt --out ${project}-snapshots/
    python -m retrievability.cli parse ${project}-snapshots/ --out results/${project}-parse.json
    python -m retrievability.cli score results/${project}-parse.json --out results/${project}-scores.json
    python -m retrievability.cli report results/${project}-scores.json --md results/${project}-report.md
done
```

### Working with Existing HTML Files

If you already have HTML files, create the expected directory structure:

```bash
mkdir my-snapshots
# Copy your HTML files to my-snapshots/
# Create crawl_results.json manually or use existing snapshots as template

python -m retrievability.cli parse my-snapshots/ --out my-parse.json
```

## Understanding Results

### Reading the Markdown Report

The generated report (`report.md`) contains:

#### Executive Summary
```markdown
- **Average Parseability Score**: 82.5/100
- **Clean Pages**: 5 (62.5%)
- **Structure Issues**: 0 (0.0%)  
- **Extraction Issues**: 3 (37.5%)
```

#### Individual Page Analysis
Each page shows:
- **Overall Score** (0-100)
- **Failure Mode** (`clean` | `structure-missing` | `extraction-noisy`)
- **What Failed** - Specific issues identified
- **Why It Failed** - Root causes from evidence
- **Fix Owner** - Who should address the issues
- **Component Scores** - Breakdown by evaluation criteria

### Using JSON Data for Automation

The JSON outputs are designed for programmatic consumption:

```python
import json

# Load scoring results
with open('results/scores.json', 'r') as f:
    scores = json.load(f)

# Filter pages by failure mode
clean_pages = [s for s in scores if s['failure_mode'] == 'clean']
problem_pages = [s for s in scores if s['parseability_score'] < 60]

# Extract specific signals for custom logic
for score in scores:
    density = score['subscores']['content_density']
    if density < 50:
        print(f"Low content density detected: {score.get('html_path', 'unknown')}")
```

### Score Interpretation

| Score Range | Meaning | Action Required |
|-------------|---------|-----------------|
| **90-100** | Excellent | Ready for production agents |
| **80-89** | Good | Minor optimizations recommended |
| **60-79** | Fair | Moderate improvements needed |
| **40-59** | Poor | Significant structural fixes required |
| **0-39** | Critical | Complete restructuring needed |

## Common Workflows

### 1. Documentation Audit
**Goal:** Assess existing documentation quality
```bash
# Collect all your docs URLs
python -m retrievability.cli crawl all-docs.txt --out audit-snapshots/
python -m retrievability.cli parse audit-snapshots/ --out audit-parse.json
python -m retrievability.cli score audit-parse.json --out audit-scores.json
python -m retrievability.cli report audit-scores.json --md audit-report.md

# Review audit-report.md for prioritized improvements
```

### 2. Pre-Agent Validation
**Goal:** Verify documentation is ready for AI agent consumption
```bash
# Test critical pages before agent deployment
python -m retrievability.cli crawl critical-pages.txt --out validation-snapshots/
# ... run full pipeline ...

# Only deploy agent if average score > 80
```

### 3. Continuous Quality Monitoring
**Goal:** Track documentation quality over time
```bash
# Run weekly evaluations
python -m retrievability.cli crawl docs-urls.txt --out weekly-$(date +%Y-%m-%d)/
# ... process results ...
# Compare scores week-over-week for regression detection
```

### 4. Developer Feedback Loop
**Goal:** Guide developers on fixing structure issues
```bash
# Generate targeted reports for specific teams
python -m retrievability.cli crawl frontend-docs.txt --out frontend-snapshots/
# ... generate report ...
# Share report.md with frontend team highlighting "Fix Owner" sections
```

## Troubleshooting

### Command Not Found
If `python -m retrievability.cli` doesn't work:
```bash
# Try explicit Python path
C:/Python313/python.exe -m retrievability.cli --help

# Or install as package
pip install -e .
retrievability --help
```

### Empty Results
If no pages are parsed:
- Check that URLs in your input file are accessible
- Verify `crawl_results.json` contains successful HTTP responses (status 200)
- Ensure HTML files exist in the snapshots directory

### Low Scores Across All Pages
If all pages score poorly:
- Review the [docs/scoring.md](docs/scoring.md) to understand criteria
- Check if pages use semantic HTML5 elements (`<main>`, `<article>`)
- Verify heading hierarchy follows H1→H2→H3 progression

### Network Issues
If crawling fails:
- Check internet connection
- Verify URLs are publicly accessible
- Some sites may block automated requests - try with different User-Agent

## Integration with CI/CD

Add quality gates to your documentation pipeline:

```bash
# In your CI script
python -m retrievability.cli crawl docs/urls.txt --out ci-snapshots/
python -m retrievability.cli parse ci-snapshots/ --out ci-parse.json
python -m retrievability.cli score ci-parse.json --out ci-scores.json

# Fail build if average score < 70
python -c "
import json
with open('ci-scores.json') as f:
    scores = json.load(f)
avg_score = sum(s['parseability_score'] for s in scores) / len(scores)
exit(0 if avg_score >= 70 else 1)
"
```

## Getting Help

- **Scoring Details:** See [docs/scoring.md](docs/scoring.md)
- **System Architecture:** See [README.md](README.md)  
- **CLI Reference:** Run `python -m retrievability.cli --help`
- **Issues:** Check GitHub issues or create new ones

## Next Steps

After evaluating your documentation:
1. **Prioritize fixes** based on failure modes and scores
2. **Address structure-missing pages first** (highest impact)
3. **Re-run evaluations** after implementing fixes
4. **Set up monitoring** for ongoing quality assurance
5. **Deploy agents** once average scores meet your thresholds