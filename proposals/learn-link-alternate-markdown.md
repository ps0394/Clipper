# Proposal: Add `<link rel="alternate">` for Markdown Format on Learn Pages

## Status
**Proposed** — Ready for implementation in Clipper/AIRE repo

## Summary

Learn pages now serve a `<meta name="markdown_url">` tag (shipped via Feature 1122297 — Native Markdown Support), but do **not** include the industry-standard `<link rel="alternate" type="text/markdown">` tag. This means AIRE detects `has_markdown_url_meta` (+4 pts) but not `has_markdown_alternate` (+6 pts), leaving 6 points on the table for every Learn page.

## Evidence

Running AIRE against `https://learn.microsoft.com/en-us/azure/storage/blobs/storage-blobs-introduction`:

| Signal | Detected | Points |
|---|---|---|
| `has_markdown_url_meta` | ✅ Yes | 4/4 |
| `has_markdown_alternate` | ❌ No | 0/6 |
| `has_llms_txt_ref` | ❌ No | 0/4 |
| `has_non_html_alternate` | ❌ No | 0/3 |
| **Total Agent Content Hints** | | **4/20** |

The markdown URL is already present in the HTML:

```html
<meta name="markdown_url" content="https://learn.microsoft.com/en-us/azure/storage/blobs/storage-blobs-introduction?accept=text/markdown">
```

## Recommended Fix (Learn template change)

Add to the `<head>` of all Learn pages:

```html
<link rel="alternate" type="text/markdown" href="https://learn.microsoft.com/en-us/azure/storage/blobs/storage-blobs-introduction?accept=text/markdown">
```

This is a **one-line template change** that would immediately add +6 points to every Learn page's HTTP compliance pillar.

## Additional Opportunities

- **llms.txt**: Adding a reference would gain +4 pts (pending Discovery feature ADO 1124031)
- **Non-HTML alternate links**: Any additional `<link rel="alternate">` for non-HTML formats (e.g., JSON, plain text) would gain +3 pts

## Impact

- Affects all ~100K+ Learn pages
- Projected improvement: +6 pts on HTTP pillar per page (currently 84/100 → 90/100)
- No functional change required — the markdown endpoint already exists and works

## Related

- ADO Feature 1122297: Native Markdown Support For Learn Site (Closed/Shipped)
- ADO Feature 1124031: Learn Dual-Head Content Delivery (Discovery)
- AIRE scoring: `access_gate_evaluator.py` lines 944–965 (Agent Content Hints sub-signal)
- AIRE detection: `parse.py` function `_detect_agent_content_hints()` lines 265–320
