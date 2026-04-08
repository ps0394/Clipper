# Automation & Integration Guide

This guide covers automated YARA evaluations, scripting integrations, and CI/CD pipeline setups for continuous documentation quality monitoring.

## Overview

YARA supports automated workflows through:
- **PowerShell scripts** for M365 Copilot integration
- **Python automation scripts** for bulk processing
- **CI/CD pipeline integration** for quality gates
- **API-style usage** for programmatic access
- **Scheduled evaluations** for ongoing monitoring

---

## 🔧 Available Automation Scripts

### 1. M365 Copilot Integration (`scripts/Invoke-YaraEvaluation.ps1`)

**Purpose**: Enable natural language evaluation requests through M365 Copilot

**Usage:**
```powershell
# Interactive evaluation
.\scripts\Invoke-YaraEvaluation.ps1 -Urls @("https://docs.example.com") 

# JSON output for programmatic use
.\scripts\Invoke-YaraEvaluation.ps1 -Urls @("url1","url2") -JsonOnly

# Custom output directory
.\scripts\Invoke-YaraEvaluation.ps1 -Urls @("url1") -OutputPath "custom-results"

# Summary only (for quick checks)
.\scripts\Invoke-YaraEvaluation.ps1 -Urls @("url1") -SummaryOnly
```

**Returns:**
- Full evaluation results with recommendations
- Raw JSON scores for analysis
- HTML snapshots for evidence
- Custom output paths for organization

### 2. Bulk Evaluation (`scripts/bulk-evaluate.py`)

**Purpose**: Process hundreds of URLs with progress tracking and executive summaries

**Usage:**
```bash
# Standard bulk processing
python scripts/bulk-evaluate.py urls.txt --out bulk-results/ --batch-size 50

# Smaller batches for limited resources
python scripts/bulk-evaluate.py urls.txt --batch-size 25

# Large datasets with custom output
python scripts/bulk-evaluate.py large-sitemap.txt --out enterprise-audit/ --batch-size 100
```

**Features:**
- Progress tracking with ETA calculations
- Batch failure resilience 
- Executive summary generation
- CSV export for analysis tools

### 3. HTML Evidence Extraction (`scripts/extract-html-evidence.py`)

**Purpose**: Generate concrete code examples for development teams

**Usage:**
```bash
# Standard evidence extraction
python scripts/extract-html-evidence.py results/ --examples 6

# Focus on specific issues
python scripts/extract-html-evidence.py results/ --examples 10

# Custom analysis
python scripts/extract-html-evidence.py results/
```

**Output:** 
- Before/after HTML examples
- Positive pattern identification  
- Issue categorization with fix recommendations

### 4. Presentation Data Generator (`scripts/generate-presentation-data.py`)

**Purpose**: Create stakeholder-ready materials from YARA results

**Usage:**
```bash
# PowerPoint slide data
python scripts/generate-presentation-data.py results/ --format powerpoint

# Executive summary
python scripts/generate-presentation-data.py results/ --format summary  

# CSV for charts/analysis
python scripts/generate-presentation-data.py results/ --format csv
```

---

## 🔄 CI/CD Pipeline Integration

### GitHub Actions Workflow

Create `.github/workflows/documentation-quality.yml`:

```yaml
name: Documentation Quality Assessment

on:
  pull_request:
    paths:
      - 'docs/**'
      - '*.md'
  push:
    branches: [main]

jobs:
  documentation-quality:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install YARA
      run: |
        pip install -r requirements.txt
    
    - name: Extract URLs from documentation
      run: |
        # Extract URLs from your docs (customize as needed)
        find docs/ -name "*.md" -exec grep -ho 'https://[^)]*' {} \; > pr-urls.txt || true
        echo "https://yoursite.com/docs" >> pr-urls.txt  # Add your live docs
    
    - name: Run YARA evaluation
      run: |
        python -m retrievability.cli express pr-urls.txt --out pr-evaluation/ --quiet
    
    - name: Generate quality report
      run: |
        python scripts/generate-presentation-data.py pr-evaluation/ --format summary
    
    - name: Check quality threshold
      run: |
        python scripts/quality-gate-check.py pr-evaluation/ --min-score 70 --min-percentage 80
    
    - name: Comment PR with results
      if: github.event_name == 'pull_request'
      uses: actions/github-script@v6
      with:
        script: |
          const fs = require('fs');
          const summary = fs.readFileSync('pr-evaluation/executive_summary.md', 'utf8');
          github.rest.issues.createComment({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            body: `## 📊 Documentation Quality Assessment\n\n${summary}`
          });
```

### Quality Gate Script

Create `scripts/quality-gate-check.py`:

```python
#!/usr/bin/env python3
"""
Quality gate check for CI/CD pipelines
Usage: python quality-gate-check.py results/ --min-score 70 --min-percentage 80
"""

import json
import argparse
import sys
from pathlib import Path

def check_quality_gate(results_dir, min_score=70, min_percentage=80):
    """Check if documentation meets quality thresholds"""
    
    scores_file = Path(results_dir) / 'report_scores.json'
    
    if not scores_file.exists():
        print("❌ No evaluation results found")
        sys.exit(1)
    
    with open(scores_file) as f:
        scores = json.load(f)
    
    if not scores:
        print("❌ No scores to evaluate")
        sys.exit(1)
    
    # Calculate metrics
    total_urls = len(scores)
    avg_score = sum(s['parseability_score'] for s in scores) / total_urls
    passing_urls = len([s for s in scores if s['parseability_score'] >= min_score])
    passing_percentage = (passing_urls / total_urls) * 100
    
    print(f"📊 Quality Gate Results:")
    print(f"   Total URLs: {total_urls}")
    print(f"   Average Score: {avg_score:.1f}/100 (threshold: {min_score})")
    print(f"   Passing URLs: {passing_urls}/{total_urls} ({passing_percentage:.1f}%)")
    print(f"   Required: {min_percentage}% above {min_score} points")
    
    # Check thresholds
    avg_pass = avg_score >= min_score
    percentage_pass = passing_percentage >= min_percentage
    
    if avg_pass and percentage_pass:
        print("✅ Quality gate PASSED")
        sys.exit(0)
    else:
        if not avg_pass:
            print(f"❌ Average score {avg_score:.1f} below threshold {min_score}")
        if not percentage_pass:
            print(f"❌ Only {passing_percentage:.1f}% pass, need {min_percentage}%")
        
        print("❌ Quality gate FAILED")
        
        # Show failing pages
        failing_pages = [s for s in scores if s['parseability_score'] < min_score]
        if failing_pages:
            print(f"\n📋 Pages needing improvement:")
            for i, page in enumerate(failing_pages[:5], 1):  # Show first 5
                print(f"   {i}. Score: {page['parseability_score']:.1f} - {page['failure_mode']}")
        
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Check documentation quality gate')
    parser.add_argument('results_dir', help='YARA evaluation results directory')
    parser.add_argument('--min-score', type=float, default=70, help='Minimum average score')
    parser.add_argument('--min-percentage', type=float, default=80, help='Minimum percentage above min-score')
    
    args = parser.parse_args()
    check_quality_gate(args.results_dir, args.min_score, args.min_percentage)
```

---

## 📅 Scheduled Monitoring

### Weekly Quality Report (Cron/Task Scheduler)

**Linux/Mac Cron:**
```bash
# Add to crontab (crontab -e)
# Run every Monday at 9 AM
0 9 * * 1 cd /path/to/yara && python scripts/weekly-quality-report.py

# Run bulk evaluation every Sunday at 2 AM  
0 2 * * 0 cd /path/to/yara && python scripts/bulk-evaluate.py production-urls.txt --out weekly-reports/$(date +\%Y-\%m-\%d)/
```

**Windows Task Scheduler:**
```powershell
# Create scheduled task
$action = New-ScheduledTaskAction -Execute "python" -Argument "scripts/weekly-quality-report.py" -WorkingDirectory "C:\path\to\yara"
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 9am
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "YARA Weekly Report"
```

### Weekly Report Script

Create `scripts/weekly-quality-report.py`:

```python
#!/usr/bin/env python3
"""
Weekly documentation quality report generator
Runs automated evaluation and sends summary email/slack
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

def generate_weekly_report():
    """Generate and distribute weekly quality report"""
    
    # Create timestamped output directory
    timestamp = datetime.now().strftime('%Y-%m-%d')
    output_dir = f"weekly-reports/{timestamp}"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    print(f"📊 Generating weekly report for {timestamp}")
    
    # Run evaluation on production URLs
    cmd = [
        sys.executable, "-m", "retrievability.cli", "express",
        "production-urls.txt", "--out", output_dir, "--quiet"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Evaluation failed: {result.stderr}")
        return
    
    # Generate executive summary
    summary_cmd = [
        sys.executable, "scripts/generate-presentation-data.py",
        output_dir, "--format", "summary"
    ]
    
    subprocess.run(summary_cmd)
    
    # Load results for email/Slack
    with open(f"{output_dir}/report_scores.json") as f:
        scores = json.load(f)
    
    avg_score = sum(s['parseability_score'] for s in scores) / len(scores)
    agent_ready = len([s for s in scores if s['parseability_score'] >= 80])
    
    # Create summary message
    summary = f"""📊 **Weekly Documentation Quality Report - {timestamp}**
    
📈 **Key Metrics:**
- Average Score: {avg_score:.1f}/100
- Agent-Ready Pages: {agent_ready}/{len(scores)} ({agent_ready/len(scores)*100:.1f}%)
- Total Pages Evaluated: {len(scores)}

📋 **Full Report:** {output_dir}/executive_summary.md
📊 **Detailed Data:** {output_dir}/report_scores.json
"""
    
    print(summary)
    
    # Optional: Send to Slack/Teams/Email
    # send_to_slack(summary)
    # send_email_report(summary, f"{output_dir}/executive_summary.md")

if __name__ == '__main__':
    generate_weekly_report()
```

---

## 🔗 Programmatic API Usage

### Python Integration

```python
#!/usr/bin/env python3
"""Example: Programmatic YARA usage"""

import subprocess
import json
import sys
from pathlib import Path

def evaluate_urls_programmatically(urls, output_dir="api-results"):
    """Run YARA evaluation programmatically"""
    
    # Create temp URL file
    url_file = Path(output_dir) / "temp_urls.txt"
    url_file.parent.mkdir(exist_ok=True)
    
    with open(url_file, 'w') as f:
        for url in urls:
            f.write(f"{url}\n")
    
    # Run YARA
    cmd = [
        sys.executable, "-m", "retrievability.cli", "express",
        str(url_file), "--out", output_dir, "--quiet"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        # Load and return results
        with open(f"{output_dir}/report_scores.json") as f:
            return json.load(f)
    else:
        raise Exception(f"YARA evaluation failed: {result.stderr}")

# Usage example
if __name__ == '__main__':
    urls = [
        "https://learn.microsoft.com/en-us/azure/functions/functions-overview",
        "https://docs.aws.amazon.com/lambda/"
    ]
    
    try:
        results = evaluate_urls_programmatically(urls)
        for i, score in enumerate(results):
            print(f"URL {i+1}: {score['parseability_score']:.1f}/100")
    except Exception as e:
        print(f"Error: {e}")
```

### REST API Wrapper (Optional)

For integration with external systems, create a simple Flask API wrapper:

```python
#!/usr/bin/env python3
"""Optional REST API wrapper for YARA"""

from flask import Flask, request, jsonify
import tempfile
import subprocess
import json
import sys
from pathlib import Path

app = Flask(__name__)

@app.route('/evaluate', methods=['POST'])
def evaluate_urls():
    """API endpoint for URL evaluation"""
    
    data = request.json
    urls = data.get('urls', [])
    
    if not urls:
        return jsonify({'error': 'No URLs provided'}), 400
    
    # Create temporary workspace
    with tempfile.TemporaryDirectory() as temp_dir:
        url_file = Path(temp_dir) / "urls.txt"
        
        with open(url_file, 'w') as f:
            for url in urls:
                f.write(f"{url}\n")
        
        # Run YARA
        cmd = [
            sys.executable, "-m", "retrievability.cli", "express",
            str(url_file), "--out", temp_dir, "--quiet"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Return results
            with open(f"{temp_dir}/report_scores.json") as f:
                scores = json.load(f)
            
            return jsonify({
                'success': True,
                'results': scores,
                'summary': {
                    'average_score': sum(s['parseability_score'] for s in scores) / len(scores),
                    'total_urls': len(scores),
                    'agent_ready': len([s for s in scores if s['parseability_score'] >= 80])
                }
            })
        else:
            return jsonify({'error': result.stderr}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

---

## 🎯 Implementation Checklist

**CI/CD Integration:**
- [ ] Create GitHub Actions workflow file
- [ ] Add quality gate script with score thresholds  
- [ ] Configure PR comments with evaluation results
- [ ] Set up failure notifications

**Scheduled Monitoring:**
- [ ] Set up weekly/monthly bulk evaluations
- [ ] Create executive report automation
- [ ] Configure Slack/Teams/email notifications
- [ ] Set up trend tracking and historical data

**API Integration:**
- [ ] Implement programmatic evaluation functions
- [ ] Create REST API wrapper (if needed)
- [ ] Set up authentication and rate limiting
- [ ] Document API endpoints and response formats

**Production Setup:**
- [ ] Configure production URL lists
- [ ] Set appropriate score thresholds for your domain
- [ ] Create alerting for quality degradation  
- [ ] Set up backup and archival of evaluation results

---

## 📞 Advanced Integration Support

**Custom Integrations:**
- Azure DevOps pipelines
- Jenkins integration  
- GitLab CI/CD
- Custom webhook endpoints

**Enterprise Features:**
- Historical trend analysis
- Custom scoring criteria
- White-label reporting
- SSO integration

**See Also:**
- [docs/advanced-workflows.md](docs/advanced-workflows.md) - PM workflows and presentation materials
- [docs/presentation-materials.md](docs/presentation-materials.md) - Executive dashboard creation
- [USER-INSTRUCTIONS.md](USER-INSTRUCTIONS.md) - Basic usage guide