# GitHub URL Evaluation Agent

Instead of manually entering URLs into the GitHub workflow UI, you can now use these agent scripts to evaluate URLs programmatically and get results back automatically.

## Available Agents

### 1. PowerShell Agent (Windows) - `url-agent.ps1`

**Quick usage:**
```powershell
# Evaluate single URL
.\scripts\url-agent.ps1 -Urls "https://docs.microsoft.com/azure"

# Evaluate multiple URLs  
.\scripts\url-agent.ps1 -Urls "https://docs.microsoft.com/azure", "https://github.com/docs"

# Evaluate URLs from file
.\scripts\url-agent.ps1 -File "my-urls.txt"

# Named evaluation
.\scripts\url-agent.ps1 -File "urls.txt" -Name "weekly-audit"
```

### 2. Python Agent (Cross-platform) - `url-agent.py`

**Quick usage:**
```bash
# Evaluate URLs directly
python scripts/url-agent.py "https://docs.microsoft.com/azure" "https://github.com/docs"

# Evaluate URLs from file
python scripts/url-agent.py --file my-urls.txt

# Named evaluation  
python scripts/url-agent.py --file urls.txt --name "weekly-audit"
```

### 3. GitHub CLI Direct (Fastest)

**One-liner for quick evaluations:**
```bash
# Trigger and monitor
gh workflow run quick-evaluate.yml --repo ps0394/Retrieval \
  -f urls="https://docs.microsoft.com/azure
https://github.com/docs" \
  -f output_name="quick-test"

# Check status
gh run list --repo ps0394/Retrieval --workflow quick-evaluate.yml --limit 1

# View results (get run number from above)
gh run view <RUN_NUMBER> --repo ps0394/Retrieval
```

## Prerequisites

### Install GitHub CLI
- **Windows:** `winget install GitHub.cli` or download from https://cli.github.com/
- **Mac:** `brew install gh`  
- **Linux:** See https://github.com/cli/cli#installation

### Authenticate
```bash
gh auth login
```

## Usage Examples

### Simple URL Check
```powershell
.\scripts\url-agent.ps1 -Urls "https://learn.microsoft.com/azure"
```

**Output:**
```
🤖 Agent evaluating 1 URLs...
🚀 Triggering evaluation workflow...
✅ Workflow triggered successfully
⏳ Waiting for evaluation to complete...
✅ Evaluation completed successfully!

==================================================
📊 EVALUATION COMPLETED  
==================================================
🔗 View results: https://github.com/ps0394/Retrieval/actions/runs/12345
💡 Check the 'Summary' tab for detailed results
```

### Bulk URL Evaluation
Create `audit-urls.txt`:
```
https://docs.microsoft.com/azure/storage/
https://docs.microsoft.com/azure/functions/
https://github.com/docs
https://stackoverflow.com/questions/tagged/azure
https://learn.microsoft.com/dotnet/
```

Run:
```powershell
.\scripts\url-agent.ps1 -File "audit-urls.txt" -Name "monthly-audit"
```

### Integration with Other Tools

**PowerShell pipeline:**
```powershell
# Get URLs from somewhere and evaluate them
$urls = Get-Content "websites.txt" | Where-Object { $_ -like "https://docs.*" }
$urls | ForEach-Object { .\scripts\url-agent.ps1 -Urls $_ -Name "doc-check-$(Get-Date -f 'yyyyMMdd')" }
```

**Python automation:**
```python
import subprocess

urls_to_check = [
    "https://docs.microsoft.com/azure/",
    "https://github.com/docs",
    "https://learn.microsoft.com/dotnet/"
]

# Convert to newline-separated string
urls_text = "\n".join(urls_to_check)

# Run agent
result = subprocess.run([
    "python", "scripts/url-agent.py", 
    "--name", "automated-check"
] + urls_to_check, capture_output=True, text=True)

print(result.stdout)
```

## Agent Features

✅ **No Manual UI Interaction** - Just provide URLs and get results  
✅ **Programmatic Interface** - Easy to integrate with scripts and automation  
✅ **Real-time Status** - Shows progress and completion status  
✅ **Automatic Results Fetching** - Gets summary and detailed reports  
✅ **Multiple Input Methods** - Direct URLs or file input  
✅ **Named Evaluations** - Organize your evaluation runs  

## API-Only Approach (Advanced)

For full API control without GitHub CLI:

```python
import requests

# Trigger workflow via REST API
response = requests.post(
    f"https://api.github.com/repos/ps0394/Retrieval/actions/workflows/quick-evaluate.yml/dispatches",
    headers={
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json"
    },
    json={
        "ref": "main",
        "inputs": {
            "urls": "https://docs.microsoft.com/azure\nhttps://github.com/docs",
            "output_name": "api-test"
        }
    }
)
```

## Troubleshooting

**"gh command not found"**  
→ Install GitHub CLI: https://cli.github.com/

**"Authentication required"**  
→ Run: `gh auth login`

**"Permission denied"**  
→ Make sure you have access to the ps0394/Retrieval repository

**"Workflow failed"**  
→ Check the workflow run URL provided in the output for detailed error logs

## Next Steps

The agent approach gives you exactly what you wanted - a simple interface where you provide URLs and get evaluation results back without manual UI interaction. You can integrate these scripts into larger automation workflows, CI/CD pipelines, or use them for regular audits.

---

# 🎯 YARA Benchmarking & Validation Scripts

These scripts help validate YARA's accuracy and ensure consistent evaluation results.

## Available Benchmarking Tools

### 1. Benchmark Validation - `benchmark-validation.py`

Validates YARA results against curated expectations:

```bash
# Validate evaluation results
python scripts/benchmark-validation.py results/scores.json

# Strict validation for CI/CD
python scripts/benchmark-validation.py results/scores.json --fail-threshold 10.0 --accuracy-threshold 0.8

# Save detailed report
python scripts/benchmark-validation.py results/scores.json --output validation-report.md
```

### 2. Create Benchmark Sets - `create-benchmark.py`

Creates curated URL sets for testing:

```bash
# List available benchmark sets
python scripts/create-benchmark.py list

# Create champion sites (should score 80-100)
python scripts/create-benchmark.py create champions --output benchmark-urls/champions.txt

# Create problematic sites (should score 20-50)  
python scripts/create-benchmark.py create problematic --output benchmark-urls/problematic.txt

# Validate URLs are accessible
python scripts/create-benchmark.py validate
```

### 3. Consistency Testing - `consistency-test.py`

Tests if YARA gives consistent results across multiple runs:

```bash
# Test consistency (3 runs)
python scripts/consistency-test.py samples/urls.txt --runs 3

# Extensive testing (5 runs with report)
python scripts/consistency-test.py samples/urls.txt --runs 5 --output consistency-report.md --verbose
```

## Quick Benchmarking Workflow

```bash
# 1. Create benchmark dataset
python scripts/create-benchmark.py create mixed --output benchmark-urls/mixed.txt

# 2. Run YARA evaluation  
python -m retrievability.cli express benchmark-urls/mixed.txt --out benchmark-results --name benchmark

# 3. Validate results
python scripts/benchmark-validation.py benchmark-results/benchmark_scores.json

# 4. Test consistency
python scripts/consistency-test.py benchmark-urls/mixed.txt --runs 3
```

## Expected Results

**✅ Good Validation:** 80%+ pass rate, <10 point deviations  
**⚠️ Needs Review:** 60-80% pass rate, 10-20 point deviations  
**❌ Poor Accuracy:** <60% pass rate, >20 point deviations  

**✅ Consistent:** Standard deviation <2.0 points  
**⚠️ Acceptable:** Standard deviation 2.0-5.0 points  
**❌ Unreliable:** Standard deviation >5.0 points  

See [docs/benchmarking-quickstart.md](../docs/benchmarking-quickstart.md) for comprehensive benchmarking guide.