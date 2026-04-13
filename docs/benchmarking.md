# YARA Benchmarking & Validation Guide

## 🎯 Validation Strategy Overview

YARA evaluates 5 weighted components:
- **Semantic structure** (25%) - main/article elements
- **Heading hierarchy** (20%) - proper H1→H6 structure
- **Content density** (25%) - text vs noise ratio
- **Rich content** (10%) - code blocks, tables
- **Boilerplate resistance** (20%) - navigation/ads contamination

**Failure modes:** `clean` (80+), `structure-missing`, `extraction-noisy`

## 🔬 Benchmarking Methods

### 1. Ground Truth Validation

Create **manually curated test sets** with known "correct" scores:

```bash
# Create benchmark URL sets
mkdir benchmark-sets
```

**Champion Sites** (Should score 85-100):
- GitHub documentation with perfect semantic markup
- Microsoft Learn with structured headings
- MDN Web Docs with code examples

**Problem Sites** (Should score 20-50):
- Heavy marketing sites with poor structure
- News sites with excessive boilerplate
- Old forums without semantic markup

**Edge Cases** (Validate specific scenarios):
- Single-page apps with dynamic content
- PDF-like dense text documents
- Code repositories with README files

### 2. Cross-Tool Comparison

Compare YARA against other evaluators:

```bash
# Manual readability assessment
# Mozilla Readability API
# Boilerpipe extraction quality
# Custom human evaluation
```

### 3. Consistency Testing

**Repeatability Check:**
```bash
# Run same URLs multiple times
python -m retrievability.cli express samples/urls.txt --out consistency-test1
python -m retrievability.cli express samples/urls.txt --out consistency-test2
# Compare score variance
```

**Temporal Stability:**
```bash
# Test same sites over time (sites change!)
python scripts/temporal-validation.py --baseline results-jan2026.json
```

## 🧪 Specific Validation Tests

### Test 1: Semantic Structure Accuracy

**Hypothesis:** Sites with proper `<main>` and `<article>` elements should score higher

**Test Sites:**
- ✅ **Good:** Modern documentation sites (GitHub, Microsoft Learn)
- ❌ **Bad:** Legacy sites without HTML5 semantics
- 🤔 **Ambiguous:** Sites with multiple main elements

**Validation:** Manual inspection of semantic markup vs YARA semantic scores

### Test 2: Heading Hierarchy Logic

**Hypothesis:** Sites with proper H1→H2→H3 flow should score higher than sites with H1→H3 gaps

**Test Cases:**
```html
<!-- Should score HIGH -->
<h1>Main Title</h1>
<h2>Section</h2>
<h3>Subsection</h3>

<!-- Should score LOW -->
<h1>Title</h1>
<h4>Random Header</h4>  <!-- Missing H2, H3 -->
<h2>Out of order</h2>
```

### Test 3: Content Density Validation

**Hypothesis:** Documentation should score higher than marketing pages

**Test Pairs:**
- Technical docs vs product landing pages (same company)
- Wikipedia articles vs news sites
- API documentation vs blog posts

### Test 4: Boilerplate Detection

**Hypothesis:** Sites with heavy navigation/ads should score lower on boilerplate resistance

**Test Method:** Compare same content on:
- Clean documentation site
- Same content on ad-heavy blog
- Mobile vs desktop versions

## 📊 Benchmarking Scripts

### Create Benchmark Dataset

```python
# benchmark-dataset.py
"""Generate curated benchmark data with expected ranges."""

BENCHMARK_URLS = {
    "champions": {
        "https://docs.github.com/en": {"expected_range": (85, 100), "rationale": "Perfect semantic HTML5"},
        "https://developer.mozilla.org/en-US/docs/Web/HTML": {"expected_range": (80, 95), "rationale": "Excellent structure + code examples"},
    },
    "problematic": {
        "https://old-forum-example.com": {"expected_range": (20, 40), "rationale": "No semantic markup, high noise"},
        "https://marketing-heavy-site.com": {"expected_range": (30, 50), "rationale": "Poor content density"},
    },
    "edge_cases": {
        "https://single-page-app.com": {"expected_range": (40, 70), "rationale": "Dynamic content challenges"},
    }
}
```

### Validation Dashboard

```python
# validation-report.py
def validate_benchmark_results(benchmark_file: str, results_file: str):
    """Compare actual YARA scores against expected ranges."""
    
    mismatches = []
    for url, actual_score in results:
        expected = benchmark_data[url]["expected_range"]
        if not (expected[0] <= actual_score <= expected[1]):
            mismatches.append({
                "url": url,
                "expected": expected,
                "actual": actual_score,
                "deviation": actual_score - expected[1] if actual_score > expected[1] else expected[0] - actual_score
            })
    
    return generate_validation_report(mismatches)
```

## 🔍 Manual Spot-Check Protocol

For **10% of evaluated URLs**, manually verify:

1. **Open URL in browser**
2. **Inspect HTML source** for semantic elements
3. **Check heading structure** (browser dev tools)
4. **Assess visual content density** (text vs ads/nav)
5. **Compare manual assessment** vs YARA subscores

**Quick Manual Scoring:**
- Semantic: Does it use `<main>`, `<article>`, `<section>`?
- Headings: Proper H1→H6 hierarchy?
- Density: Easy to find main content?
- Rich: Code blocks, tables present?
- Clean: Minimal boilerplate contamination?

## 🚨 Red Flags to Investigate

**Score Anomalies:**
- High score (80+) but visually cluttered site
- Low score (30-) but clean documentation site
- Identical content with vastly different scores

**Component Mismatches:**
- High semantic score but no visible `<main>` element
- Perfect heading score but broken visual hierarchy
- High density score but ad-heavy layout

## 📈 Continuous Validation

**Monthly validation routine:**
1. Re-evaluate benchmark dataset
2. Check for score drift over time  
3. Add new edge cases discovered
4. Update expected ranges based on evidence

**Integration testing:**
```bash
# Add to CI/CD pipeline
python scripts/benchmark-validation.py --fail-on-deviation 15
```

## 🎓 Learning from Mismatches

When YARA disagrees with human assessment:

1. **Investigate the HTML source** - YARA might be right!
2. **Check scoring weights** - Maybe density is overweighted?
3. **Refine failure mode thresholds** - 80+ for "clean" too high?
4. **Update extraction logic** - Missing important signals?

**Document findings:**
```markdown
## Validation Finding: GitHub Issues Pages

- **YARA Score:** 65/100 (extraction-noisy)
- **Human Assessment:** Should be 80+ (clean docs)
- **Root Cause:** Dynamic loading, YARA sees skeleton HTML
- **Action:** Add JavaScript rendering or update scoring for SPA patterns
```

This benchmarking approach will help you build confidence in YARA's accuracy and improve it systematically! 🎯