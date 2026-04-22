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

Each entry in `*_scores.json` carries **two headline scores** and a full component breakdown. You must understand the difference between the two scores before reporting either.

```json
{
  "url": "https://...",
  "parseability_score": 65.6,
  "universal_score": 62.1,
  "content_type": {
    "profile": "tutorial",
    "detection": { "source": "ms_topic", "matched_value": "tutorial" }
  },
  "component_scores": {
    "semantic_html": 72.7,
    "content_extractability": 92.7,
    "structured_data": 12.0,
    "dom_navigability": 35.0,
    "metadata_completeness": 100.0,
    "http_compliance": 77.8
  },
  "audit_trail": { ... }
}
```

### The two scores — when to use which

- **`parseability_score`** — computed with **content-type-specific weights** chosen by the classifier. Use when comparing pages of the same content type, or when scoring a single page against itself over time.
- **`universal_score`** — computed with the default **`article`** profile weights applied to every page. Use whenever comparing pages across content types, across vendors, or across corpora.

**Cross-vendor and cross-corpus comparisons must use `universal_score`.** `parseability_score` applies different weights to different pages; averaging or deltaing it across a mixed set produces numbers that aren't on a common scale.

### Six-pillar structure and default (article) weights

| Pillar | Default weight | Standard |
|--------|----------------|----------|
| Semantic HTML | 25% | W3C HTML5 |
| Content Extractability | 20% | Readability algorithm |
| Structured Data | 20% | Schema.org / JSON-LD |
| DOM Navigability | 15% | WCAG 2.1 AA via axe-core |
| Metadata Completeness | 10% | Dublin Core + Schema.org + OpenGraph |
| HTTP Compliance | 10% | RFC 7231 |

Profile-specific weights (`landing`, `reference`, `sample`, `faq`, `tutorial`) reweight these same six pillars — they do not add or remove pillars. See [docs/scoring.md](../docs/scoring.md) for the profile weight table and [docs/improvement-plan.md](../docs/improvement-plan.md) for known methodology caveats still in flight.

### Score interpretation

- **90+** — Agent-ready (clean)
- **70–89** — Minor issues
- **40–69** — Needs improvement (moderate issues)
- **Below 40** — Critical issues

## When Asked to Evaluate URLs

1. Run `python main.py express` with the appropriate arguments.
2. Read `*_scores.json` for structured results.
3. Report `parseability_score` **and** `universal_score` side-by-side. Never report only one.
4. For each page, state the detected content-type profile and the detection source (`ms_topic` / `schema_type` / `url` / `dom` / `default`) — this is in `content_type.detection` or `audit_trail._content_type.detection`.
5. Summarize findings: weakest components, actionable recommendations. Reference component scores, failure modes, and profile assignments.

## When Asked to Write a Comparison or Analysis Report

Clipper reports that compare pages across vendors, corpora, or content types have specific hygiene requirements. Violating these produces reports that look quantitative but aren't defensible.

### Required disclosures

Every comparison report must disclose:

1. **Which headline score is used** (`parseability_score` vs `universal_score`) and **why**.
2. **Per-page profile assignment** — in the appendix table, add a column showing the profile each page was scored under. Different profiles mean different weights; readers cannot interpret deltas without this.
3. **Detection source** — whether each page's profile came from `ms.topic`, `schema_type`, URL heuristic, DOM heuristic, or default. Pages typed via `ms.topic` get a vendor-specific signal; pages typed via the other sources get universal signals. This asymmetry matters for cross-vendor comparisons.
4. **Methodology caveats section** — link to known biases and in-flight phases that affect the numbers (see `docs/improvement-plan.md`). Currently relevant: Phase 4.4 (metadata-pillar vendor-neutrality audit — `ms.topic` accepted in the metadata topic-field check in a way that may inflate Learn metadata scores). If a report's findings depend on a pillar with an in-flight neutrality fix, say so.

### Required rules for cross-vendor / cross-corpus comparisons

- **Use `universal_score` for headline deltas.** Not `parseability_score`. The advertised pillar-weight table in the report body must match the weights actually applied to the headline number. Mixing `parseability_score` in the body with `article` weights in the methodology section is a methodology error.
- **Match sample sizes** or disclose the asymmetry. 16 vs 6 is not a comparable baseline; compute per-page distributions, not just means, and acknowledge variance.
- **Do not mix "exemplars" into competitor averages.** Either a page is a competitor (included in the average) or an exemplar (excluded, shown for reference). Pick one per page and apply consistently.
- **Symmetric projections.** If projecting the effect of fixes on the primary subject, project equivalent fixes on the comparison set too. One-sided "Learn → 76.5, gap widens to +24.8" projections are not evidence unless the competitor projections are computed with the same assumptions.
- **Label accessibility-strictness deltas correctly.** Rendered-vs-raw score deltas driven by axe-core running only in rendered mode are WCAG-strictness effects, not JavaScript-dependency effects. Separate the two in reporting.

### Forbidden framings

- Presenting `parseability_score` deltas across different profiles as a like-for-like comparison.
- Attributing a metadata-pillar lead entirely to "CMS template quality" without acknowledging the `ms.topic` signal-acceptance asymmetry (until Phase 4.4 lands).
- Using "agent-ready" / "needs improvement" bands without stating which score (`parseability_score` or `universal_score`) the band is applied to.
- Recommending vendor template fixes based on a single-run evaluation without reporting variance or confidence.

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
