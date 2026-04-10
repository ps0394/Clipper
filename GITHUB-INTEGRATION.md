# YARA GitHub Integration Quick Start

This guide shows how to use YARA (Yet Another Retrieval Analyzer) in your GitHub workflows.

## 🚀 One-Click Setup for Any Repository

### 1. Add the Reusable Action to Your Workflow

Create `.github/workflows/docs-quality.yml` in your repository:

```yaml
name: Documentation Quality Check

on:
  pull_request:
    paths: ['docs/**', '*.md']

jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    # Use the reusable evaluation action
    - name: Evaluate documentation quality
      uses: ps0394/YARA/.github/actions/docs-eval@main
      with:
        urls-file: 'docs/urls.txt'  # Your documentation URLs
        min-score: '75'
        min-clean-percentage: '65'
```

### 2. Create Your URLs File

Add `docs/urls.txt` to your repository:
```
https://yourdocs.example.com/getting-started
https://yourdocs.example.com/api-reference  
https://yourdocs.example.com/tutorials
```

That's it! Your PRs will now get automatic documentation quality reports.

## 🔧 Advanced Configurations

### Quality Gates for Different Environments

```yaml
- name: Production-ready check
  uses: ps0394/YARA/.github/actions/docs-eval@main
  with:
    urls-file: 'production-urls.txt'
    min-score: '85'              # Strict production standards
    min-clean-percentage: '80'   
    fail-on-quality-gate: 'true' # Fail deployment if not met

- name: Development monitoring  
  uses: ps0394/YARA/.github/actions/docs-eval@main
  with:
    urls-file: 'dev-urls.txt'
    min-score: '60'              # Lower bar for development
    fail-on-quality-gate: 'false' # Just monitor, don't fail
```

### Scheduled Quality Monitoring

```yaml
name: Weekly Docs Audit
on:
  schedule:
    - cron: '0 9 * * 1'  # Monday 9 AM

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: ps0394/YARA/.github/actions/docs-eval@main
      with:
        urls-file: 'all-docs-urls.txt'
        min-score: '70'
    
    # Create GitHub issue if quality degrades
    - name: Create issue on regression
      if: failure()
      uses: actions/github-script@v6
      with:
        script: |
          github.rest.issues.create({
            owner: context.repo.owner,
            repo: context.repo.repo,
            title: 'Documentation Quality Regression',
            body: 'Weekly audit failed. Check workflow for details.',
            labels: ['documentation', 'quality']
          });
```

## 📊 Working with Results

### Access Evaluation Data in Workflows

```yaml
- name: Evaluate docs
  id: eval
  uses: ps0394/YARA/.github/actions/docs-eval@main
  with:
    urls-file: 'docs-urls.txt'

- name: Use results
  run: |
    echo "Average score: ${{ steps.eval.outputs.average-score }}"
    echo "Clean pages: ${{ steps.eval.outputs.clean-count }}"
    echo "Quality passed: ${{ steps.eval.outputs.quality-passed }}"

- name: Custom logic based on scores
  if: steps.eval.outputs.average-score < 70
  run: echo "Docs need improvement before release"
```

### Generate Quality Badges

```yaml
- name: Update README badge
  run: |
    score="${{ steps.eval.outputs.average-score }}"
    color="red"
    if (( $(echo "$score >= 80" | bc -l) )); then color="green"
    elif (( $(echo "$score >= 70" | bc -l) )); then color="yellow"
    fi
    
    badge_url="https://img.shields.io/badge/docs%20quality-${score}%2F100-${color}"
    echo "Badge URL: $badge_url"
```

## 🏗️ Development Environments

### GitHub Codespaces Support

The evaluation system includes `.devcontainer/devcontainer.json` for instant development environments:

1. **Open in Codespaces**: Click "Code" → "Create codespace" 
2. **Pre-configured environment** with Python, dependencies, and VS Code extensions
3. **Ready to use**: `python -m retrievability.cli --help`

### Local Development Integration

```bash
# Install the integration helper
pip install -r requirements.txt

# Run evaluation with GitHub integration
python github_integration.py evaluate \
  --urls-file docs/urls.txt \
  --output-dir results/ \
  --min-score 75

# Check quality gates only
python github_integration.py check-gates \
  --output-dir results/ \
  --min-score 75
```

## 🔄 CI/CD Pipeline Integration

### Pre-deployment Quality Gates

```yaml
deploy:
  runs-on: ubuntu-latest
  needs: [build, test]
  steps:
  - name: Check documentation quality
    uses: ps0394/YARA/.github/actions/docs-eval@main
    with:
      urls-file: 'deployment-docs.txt'
      min-score: '80'
      fail-on-quality-gate: 'true'  # Block deployment if docs are poor
  
  - name: Deploy if quality passes
    run: ./deploy.sh
```

### Multi-stage Validation

```yaml
strategy:
  matrix:
    environment: [staging, production]
    
steps:
- name: Evaluate ${{ matrix.environment }} docs
  uses: ps0394/YARA/.github/actions/docs-eval@main
  with:
    urls-file: '${{ matrix.environment }}-urls.txt'
    min-score: ${{ matrix.environment == 'production' && '85' || '75' }}
```

## 🛠️ Custom Integrations

### Slack/Teams Notifications

```yaml
- name: Evaluate docs
  id: eval
  uses: ps0394/YARA/.github/actions/docs-eval@main
  with:
    urls-file: 'docs-urls.txt'

- name: Notify team on Slack
  if: steps.eval.outputs.quality-passed == 'false'
  uses: 8398a7/action-slack@v3
  with:
    status: failure
    text: |
      📉 Documentation quality check failed!
      Score: ${{ steps.eval.outputs.average-score }}/100
      Clean pages: ${{ steps.eval.outputs.clean-percentage }}%
```

### Database Integration

```python
# Example: Store results in database
import json
import psycopg2

def store_evaluation_results(scores_file, database_url):
    with open(scores_file) as f:
        results = json.load(f)
    
    conn = psycopg2.connect(database_url)
    cur = conn.cursor()
    
    for result in results:
        cur.execute("""
            INSERT INTO doc_quality_history 
            (url, score, failure_mode, timestamp)
            VALUES (%s, %s, %s, NOW())
        """, (
            result.get('url', 'unknown'),
            result['parseability_score'], 
            result['failure_mode']
        ))
    
    conn.commit()
```

## 📈 Quality Monitoring Dashboard

### GitHub Pages Integration

```yaml
- name: Generate quality dashboard
  run: |
    python -c "
    import json
    with open('results/scores.json') as f:
        scores = json.load(f)
    
    # Generate HTML dashboard
    html = '''
    <html><body>
    <h1>Documentation Quality Dashboard</h1>
    <div>Average Score: {avg}</div>
    <div>Last Updated: {date}</div>
    </body></html>
    '''.format(
        avg=sum(s['parseability_score'] for s in scores) / len(scores),
        date='$(date)'
    )
    
    with open('docs/quality-dashboard.html', 'w') as f:
        f.write(html)
    "

- name: Deploy to GitHub Pages
  uses: peaceiris/actions-gh-pages@v3
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    publish_dir: ./docs
```

## ⚙️ Action Outputs Reference

The reusable action provides these outputs for integration:

| Output | Description | Example |
|--------|-------------|---------|
| `average-score` | Overall score (0-100) | `82.5` |
| `clean-count` | Pages classified as clean | `5` |
| `clean-percentage` | Percentage of clean pages | `62.5` |
| `total-pages` | Total pages evaluated | `8` |
| `structure-missing` | Pages needing structure fixes | `0` |  
| `extraction-noisy` | Pages needing extraction fixes | `3` |
| `quality-passed` | Whether quality gates passed | `true` |
| `report-path` | Path to markdown report | `results/report.md` |
| `scores-path` | Path to JSON scores | `results/scores.json` |

Use these outputs to build sophisticated quality monitoring and automation workflows tailored to your team's needs!