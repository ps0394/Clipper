# Clipper — Copilot Cloud Agent Instructions

This repository is **Clipper** (CLI Progressive Performance Evaluation & Reporting), a standards-based tool for evaluating how well web pages are structured for AI agent retrieval.

## Running Clipper

### Single URL evaluation
```bash
python main.py express --urls https://example.com --out results --quiet
```

### Multiple URLs from a file
```bash
python main.py express urls/clipper-demo-urls.txt --out results --name evaluation-name --quiet
```

### Key flags
- `--urls <url>` — Evaluate a single URL directly
- `--out <dir>` — Output directory for results
- `--name <name>` — Prefix for output files
- `--quiet` — Suppress verbose output (recommended for agent use)

### URL file format
One URL per line. Lines starting with `#` are comments. Blank lines are ignored.

## Reading Results

After evaluation, read the structured JSON output for machine-parseable results:

- `<out>/<name>_scores.json` — Array of scored results per URL
- `<out>/<name>.md` — Human-readable markdown report

### Score JSON structure
Each entry in `*_scores.json` contains:
```json
{
  "url": "https://...",
  "parseability_score": 48.4,
  "failure_mode": "structured-data-deficit",
  "component_scores": {
    "wcag_accessibility": 0.0,
    "semantic_html": 72.7,
    "structured_data": 13.0,
    "http_compliance": 100.0,
    "content_quality": 84.1
  },
  "audit_trail": { ... }
}
```

### Scoring components (weights)
| Component | Weight | Standard |
|-----------|--------|----------|
| WCAG Accessibility | 25% | WCAG 2.1 AA via Deque axe-core |
| Semantic HTML | 25% | W3C HTML5 specification |
| Schema.org Structured Data | 20% | Schema.org vocabulary |
| HTTP Compliance | 15% | RFC 7231 content negotiation |
| Content Quality | 15% | Agent-focused readability metrics |

### Score interpretation
- **70+** — Agent-ready (good retrievability)
- **40–69** — Needs improvement
- **Below 40** — Critical issues for agent consumption

## When Asked to Evaluate URLs

1. Run `python main.py express` with the appropriate arguments
2. Read the `*_scores.json` file for structured results
3. Summarize findings: overall score, weakest components, actionable recommendations
4. Reference specific component scores and failure modes in your analysis

## Project Structure

- `main.py` — CLI entry point
- `retrievability/` — Core evaluation modules
  - `cli.py` — Argument parsing and express command
  - `crawl.py` — URL fetching and HTML snapshot capture
  - `parse.py` — Content extraction and signal detection
  - `score.py` — Standards-based scoring engine
  - `performance_evaluator.py` — Parallel execution engine
  - `access_gate_evaluator.py` — Component evaluators (WCAG, HTML, Schema.org, HTTP, Content)
  - `report.py` — Markdown report generation
  - `schemas.py` — JSON output contracts
- `urls/clipper-demo-urls.txt` — 11 demo URLs across 4 categories
- `samples/urls.txt` — Sample URL list

## Important Notes

- WCAG evaluation requires Chrome and ChromeDriver (installed via copilot-setup-steps.yml)
- Each URL makes 5 HTTP requests for RFC 7231 content negotiation testing — this is by design
- Evaluation takes ~7-10 seconds per URL in performance mode
- The `--quiet` flag is recommended to keep output clean for parsing
