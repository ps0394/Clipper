# Wire content negotiation signals into Access Gate scoring

## Problem

Clipper's `crawl.py` has a complete content negotiation framework — it sends `Accept: text/markdown`, `text/plain`, `application/json`, `application/xml` requests and calculates `format_availability_score`, `content_consistency_score`, and `agent_optimization_detected`. There's even a CLI subcommand (`negotiate`).

**None of this is wired into the 6-pillar evaluator.** The signals that most directly indicate "this site wants agents to succeed" contribute 0% to the final Access Gate score.

## Evidence from Live Sites

Fetching raw HTML from three major documentation sites reveals the gap:

| Site | Agent-Friendly Signal | Clipper Detects? |
|---|---|---|
| **GitHub Docs** | `<link rel="alternate" type="text/markdown">` with `data-llm-hint` attributes pointing to clean markdown and JSON API endpoints | :x: No |
| **Microsoft Learn** | `<meta name="markdown_url">` exposing a `?accept=text/markdown` endpoint | :x: No |
| **MDN Web Docs** | `<link rel="alternate" type="application/rss+xml">` (feed, not markdown) | N/A |

GitHub Docs even includes LLM-specific hints:

```html
<link rel="alternate" type="text/markdown"
  href="https://docs.github.com/api/article/body?pathname=..."
  data-llm-hint="Hey agent! You are burning tokens scraping HTML like it is 2005. Use this instead." />

<link rel="index" type="text/markdown"
  href="https://docs.github.com/llms.txt"
  data-llm-hint="The directory of everything. We even followed the llmstxt.org spec because we are nice like that." />
```

These are arguably the strongest possible signals that a site is agent-ready, yet Clipper ignores them.

## What Exists Today (Built but Disconnected)

**In `crawl.py`:**
- `crawl_with_content_negotiation()` — sends 5 different `Accept` headers
- `_calculate_format_availability_score()` — scores format variety
- `_calculate_content_consistency_score()` — checks if formats return different content
- `_detect_agent_optimization()` — boolean agent-optimization detection
- Full schema support: `FormatResponse`, `ContentNegotiationResult`

**In `access_gate_evaluator.py` — no content negotiation:**
- `_evaluate_http_compliance_enhanced()` checks only: HTML reachability (20 pts), redirect efficiency (30 pts), robots/crawl permissions (25 pts), cache headers (25 pts)
- Zero references to markdown alternatives, `<link rel="alternate">`, or content negotiation

**In `parse.py` — no agent-hint detection:**
- Does not scan for `<link rel="alternate" type="text/markdown">`, `<meta name="markdown_url">`, `llms.txt` references, or `data-llm-hint` attributes

## Proposed Solution: New 7th Pillar — Agent Content Negotiation

Add a dedicated pillar that measures whether the site explicitly supports machine-readable content formats.

**Proposed weight redistribution:**

| Pillar | Current | Proposed |
|---|---|---|
| Semantic HTML | 25% | 22% |
| Content Extractability | 20% | 18% |
| Structured Data | 20% | 18% |
| DOM Navigability | 15% | 14% |
| Metadata Completeness | 10% | 8% |
| HTTP Compliance | 10% | 10% |
| **Agent Content Negotiation** | **—** | **10%** |

**Sub-signals (100 pts → weighted to 10%):**

| Sub-signal | Max Points | What it measures |
|---|---|---|
| **HTML Agent Hints** | 30 | `<link rel="alternate" type="text/markdown">`, `<meta name="markdown_url">`, `data-llm-hint`, `llms.txt` refs |
| **Format Availability** | 30 | Live probes: does `Accept: text/markdown` or `Accept: application/json` return 200 with correct content-type? |
| **Content Differentiation** | 25 | Is the alternative format actually different from HTML? |
| **Agent Optimization Detected** | 15 | Composite: multiple working formats + differentiated content + explicit LLM hints |

## Implementation Scope

1. **`parse.py`** — Add agent-hint extraction: scan for `<link rel="alternate">`, `<meta name="markdown_url">`, `data-llm-hint`, `llms.txt` references
2. **`schemas.py`** — Extend `ParseSignals` with `agent_alternate_formats`, `has_markdown_url`, `has_llm_hints`, `llms_txt_referenced`
3. **`access_gate_evaluator.py`** — Add `_evaluate_agent_content_negotiation()` method, update `WEIGHTS` and `STANDARDS_AUTHORITY`, wire in existing `crawl.py` functions
4. **`report.py`** — Include content negotiation in audit trail
5. **`README.md`** — Update scoring docs, pillar tables, example output
6. **Tests** — Cases for sites with and without agent hints

**~80% of the crawl-time infrastructure already exists in `crawl.py`.** The main work is HTML-level hint detection in `parse.py` and wiring into the evaluator.

## Standards Authority

| Signal | Authority |
|---|---|
| `<link rel="alternate">` | HTML5 spec (W3C) |
| Content negotiation via `Accept` header | RFC 7231 §5.3.2 (IETF) |
| `llms.txt` | llmstxt.org specification |
| Schema.org `encodingFormat` | Schema.org Consortium |

## Why This Matters

- **Alignment:** Clipper's core question is "Can agents reliably access this content?" A site serving markdown on request is the most direct answer.
- **Differentiation:** No other evaluation tool measures this signal.
- **Industry direction:** GitHub Docs, Microsoft Learn, and others are investing in agent-friendly endpoints. This trend will accelerate.
- **Score impact:** Max 10 points. Sites without support drop 0–3 pts from redistribution. Sites with strong agent support gain 7–10 pts net.

## Alternative: Fold into HTTP Compliance (conservative)

If adding a 7th pillar is too disruptive, an alternative is to expand the HTTP Compliance pillar with a 5th sub-signal for content negotiation (20 pts), rebalancing the existing 4 sub-signals. This limits max score impact to ~2 points but buries an important signal.
