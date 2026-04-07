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