# Phase 5 calibration corpus

This directory holds the Phase 5 LLM ground-truth validation corpus. See
[docs/phase-5-design.md](../../docs/phase-5-design.md) for the full design.

## Layout

Each page gets a subdirectory keyed by a slug derived from the URL:

```
<slug>/
  source.json          # URL, profile, vendor, fetch timestamp
  snapshot.html        # captured rendered HTML
  snapshot.txt         # extracted text fed to scoring LLMs
  generator.prompt.txt # exact prompt sent to Claude
  generator.raw.json   # Claude's raw generator output (5+ Q/A pairs)
  review.json          # accept/edit/reject audit trail per pair
  ground_truth.json    # final 5 reviewer-approved Q/A pairs
```

## Commit policy

Everything in this directory is permanent corpus data and is committed
to git. Do not delete or rewrite `generator.raw.json` or `review.json`
after review — they are the audit trail.

## Pilot vs. full corpus

The pilot runs against `_pilot/` (5 URLs, 1 Q/A per page). The full
N=60 corpus lives in flat subdirs at this level once the pilot is
approved.
