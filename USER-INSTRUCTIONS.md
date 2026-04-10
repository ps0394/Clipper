# User Instructions: Clipper Content Evaluation

This guide walks you through using **Clipper** (Command-Line Interface Progressive Performance Evaluation & Reporting) to evaluate content for agent accessibility using standards-based evaluation methodology.

## What is Clipper

**Standards-Based Evaluation Engine**: Combines WCAG 2.1 (25%) + W3C Semantic HTML (25%) + Schema.org (20%) + HTTP Standards (15%) + Content Quality (15%)
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

```bash
# Full Clipper standards-based scoring
python main.py express --urls https://learn.microsoft.com/azure --out results/

# Multiple URLs evaluation
python main.py express samples/urls.txt --out results/ --name comprehensive

# Clipper evaluation with minimal output
python main.py express samples/urls.txt --out results/ --quiet
```

**What Express Mode Does:**
1. 📄 Crawls URLs and captures HTML content
2. 🔍 Parses content for structural signals
3. 📊 Scores using Clipper standards-based methodology
4. 📋 Generates comprehensive reports with audit trails

**Output Files:**
- `results/report.md`: Human-readable report with recommendations
- `results/report_scores.json`: Clipper scores with component breakdown
- `results/report_parse.json`: Raw parsing results and structured data

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
- **WCAG 2.1 Accessibility** (25%): Automated accessibility analysis using axe-core
- **W3C Semantic HTML** (25%): HTML5 semantic elements and ARIA compliance
- **Schema.org Structured Data** (20%): JSON-LD, microdata analysis
- **HTTP Standards** (15%): Content negotiation and RFC compliance
- **Content Quality** (15%): Agent-optimized content metrics

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
  "overall_score": 75.2,
  "component_scores": {
    "wcag_accessibility": 85.0,
    "semantic_html": 72.5,
    "structured_data": 68.0,
    "http_compliance": 90.0,
    "content_quality": 80.5
  },
  "standards_authority": {
    "accessibility": "WCAG 2.1 AA (W3C) + axe-core (Deque Systems)",
    "semantics": "HTML5 Semantic Elements (W3C)"
  }
}
```

## Quick Command Reference

```bash
# Single URL quick evaluation
python main.py express --urls https://example.com --out quick/

# Batch evaluation with URLs from file
python main.py express urls.txt --out batch-results/

# Quiet mode for CI/CD integration
python main.py express urls.txt --out results/ --quiet

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
# CI/CD pipeline example
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