# User Instructions: Clipper Content Evaluation

This guide walks you through using **Clipper** (Command-Line Interface Progressive Performance Evaluation & Reporting) to evaluate content for agent accessibility using standards-based evaluation methodology.

## What is Clipper

**Standards-Based Evaluation Engine**: Combines WCAG 2.1 (25%) + W3C Semantic HTML (25%) + Schema.org (20%) + HTTP Standards + Redirects (15%) + Content Quality (15%)
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
- **HTTP Standards + Redirects** (15%): Content negotiation and redirect efficiency analysis
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
  "audit_trail": {
    "http_compliance": {
      "content_negotiation": {...},
      "redirect_efficiency": {
        "redirect_analysis": {
          "redirect_count": 1,
          "efficiency_classification": "good (standard redirects)",
          "performance_ratio": 0.15
        }
      }
    }
  },
  "standards_authority": {
    "accessibility": "WCAG 2.1 AA (W3C) + axe-core (Deque Systems)",
    "semantics": "HTML5 Semantic Elements (W3C)"
  }
}
```

## Enhanced HTTP Compliance Scoring

Clipper now includes **redirect efficiency analysis** as part of HTTP compliance evaluation:

### **HTTP Standards + Redirects Component (15% of total score)**
- **Content Negotiation (60%)** - Server's ability to provide different content formats
- **Redirect Efficiency (40%)** - Quality and performance of redirect chains **[NEW]**

### **What Redirect Efficiency Evaluates:**
1. **Chain Length** - Fewer redirects = better score
   - 0 redirects: 25/25 points (optimal)
   - 1-2 redirects: 20/25 points (good)  
   - 3-4 redirects: 10/25 points (moderate)
   - 5+ redirects: 0/25 points (poor)

2. **Redirect Types** - Proper HTTP status codes
   - 301, 302, 303, 307, 308: Good
   - Invalid or missing status codes: Penalty

3. **Performance Impact** - Redirect overhead analysis
   - Low redirect-to-content time ratio: Better score
   - High redirect overhead: Lower score

### **Real-World Impact:**
- **Direct URLs (no redirects)**: Get full HTTP compliance bonus
- **Standard redirects (http→https)**: Minor score impact
- **Excessive redirect chains**: Meaningful score penalty
- **Redirect loops**: Early detection prevents evaluation failures

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