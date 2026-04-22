# Phase 5 scoring results

Per-run scoring-LLM outputs and graded results. See
[docs/phase-5-design.md](../../docs/phase-5-design.md) §7.

## Layout

Each **published** run lives in a subdirectory tagged by date + scoring
model + corpus id:

```
<run-id>/                          # e.g. 2026-05-01-gpt4o-pilot
  manifest.json                    # run config: model, seed, temperature, corpus ref
  scores/
    <slug>.json                    # raw scoring-LLM output per page
  grades/
    <slug>.json                    # binary correct/incorrect per question
  correlations.json                # per-pillar Spearman rho + bootstrap CI
  phase5-findings.md               # human-readable report
```

## Commit policy

Only runs that back a published finding land here. Scratch experiments
and pilot iterations go in `../phase5-scratch/` (gitignored).

A run is **published** once:

1. All pages in the corpus have scores + grades.
2. `correlations.json` addresses H0-strong, H0-weight, H0-profile.
3. Second-reviewer κ has been computed and is reported in findings.
4. A second person has reviewed the findings draft.
