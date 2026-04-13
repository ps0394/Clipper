# Benchmarking YARA - Quick Start Guide

## 🚀 Quick Validation Workflow

### 1. Create Benchmark Dataset

```bash
# List available benchmark sets
python scripts/create-benchmark.py list

# Create a champion sites dataset (should score 80-100)
python scripts/create-benchmark.py create champions --output benchmark-urls/champions.txt

# Create mixed dataset for comprehensive testing
python scripts/create-benchmark.py create mixed --output benchmark-urls/mixed.txt
```

### 2. Run YARA Evaluation

```bash
# Evaluate champion sites
python -m retrievability.cli express benchmark-urls/champions.txt --out results/champions --name champions

# Evaluate mixed benchmark 
python -m retrievability.cli express benchmark-urls/mixed.txt --out results/mixed --name mixed
```

### 3. Validate Against Expectations

```bash
# Validate champion results (should mostly pass)
python scripts/benchmark-validation.py results/champions/champions_scores.json

# Validate mixed results  
python scripts/benchmark-validation.py results/mixed/mixed_scores.json --output validation-report.md
```

### 4. Test Consistency 

```bash
# Test if YARA gives consistent results across multiple runs
python scripts/consistency-test.py benchmark-urls/champions.txt --runs 3 --output consistency-report.md
```

## 📋 Example Output

**Validation Results:**
```
# YARA Benchmark Validation Report
**Results:** 7/8 passed (87.5%)

## ❌ Failed Validations

### https://stackoverflow.com/questions/tagged/azure
- **Expected:** 20-50
- **Actual:** 65.2
- **Deviation:** 15.2 points
- **Rationale:** Poor semantic structure, high boilerplate, complex layout

## ✅ Passed Validations
- **https://docs.github.com/en:** 89.3 (expected 80-100)
- **https://learn.microsoft.com/en-us/azure/:** 91.7 (expected 80-95)
```

**Consistency Results:**
```
# YARA Consistency Analysis Report  
**Runs:** 3
**URLs Tested:** 6

## 📊 Overall Consistency
- **Average Standard Deviation:** 1.24 points
- **Maximum Standard Deviation:** 2.87 points
- **Average Score Range:** 3.45 points

## ✅ All Results Consistent
No URLs showed high variance (stdev > 5.0 or range > 10.0)
```

## 🎯 Interpreting Results

### Validation Scores

**✅ Good validation (>80% pass rate):**
- YARA is correctly identifying good/bad sites
- Scoring is aligned with human expectations
- Ready for production use

**⚠️ Moderate validation (60-80% pass rate):**
- Some edge cases or calibration issues
- Review failed cases for patterns
- Consider adjusting thresholds

**❌ Poor validation (<60% pass rate):**
- Significant scoring problems
- May need algorithm improvements
- Investigate root causes systematically

### Consistency Metrics  

**✅ Excellent (stdev < 2.0):**
- Highly reliable, deterministic scoring
- Safe for automated decisions

**⚠️ Good (stdev 2.0-5.0):**
- Generally reliable with minor variance
- Acceptable for most use cases

**❌ Poor (stdev > 5.0):**
- High variance indicates problems
- Investigate non-deterministic factors
- May need algorithmic improvements

## 🔍 Common Issues & Solutions

### Issue: High Scores on Poor Sites

**Symptoms:** Marketing sites scoring 80+
**Causes:** 
- Overweighting semantic elements (some marketing sites use proper HTML5)
- Underweighting boilerplate contamination
**Solutions:**
- Adjust scoring weights in [score.py](retrievability/score.py#L120-L130)
- Improve boilerplate detection thresholds

### Issue: Low Scores on Good Sites  

**Symptoms:** Clean documentation scoring <60
**Causes:**
- Missing semantic markup on older sites
- Strict heading hierarchy requirements
**Solutions:**
- Lower clean threshold from 80 to 70
- Add partial credit for heading presence without perfect hierarchy

### Issue: High Consistency Variance

**Symptoms:** Same URL scoring 65, then 78, then 71
**Causes:**
- Network timeouts affecting content retrieval  
- Dynamic content loading differently
**Solutions:**
- Add retry logic for failed crawls
- Consider JavaScript rendering for SPAs

## 🛠️ Advanced Benchmarking

### Manual Spot-Checking

For any failed validations:

1. **Visit URL in browser** - Does it look agent-friendly?
2. **Inspect HTML source** - Check semantic markup
3. **Manual scoring** - Rate 1-10 on each criterion
4. **Compare with YARA** - Identify disconnect

### Custom Benchmark Sets

Add your own domain-specific URLs:

```python
# Edit scripts/create-benchmark.py
BENCHMARK_SETS["my_domain"] = [
    "https://my-company-docs.com/api", 
    "https://my-company-docs.com/tutorial",
    # ... add URLs with known good/bad characteristics
]
```

### Continuous Integration

Add to CI/CD pipeline:

```yaml
# .github/workflows/yara-validation.yml
- name: Validate YARA Benchmark
  run: |
    python scripts/benchmark-validation.py results/benchmark_scores.json --fail-threshold 15.0
```

This benchmarking approach will help you build confidence in YARA's accuracy systematically! 🎯