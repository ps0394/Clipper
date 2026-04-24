# Clipper Corpus Findings

Evidence-based findings from Clipper's corpus-level retrievability experiments. Each document in this directory reports a single corpus, its methodology, its results, and the specific scoring decisions the evidence supports or refutes.

## Contents

- [phase-5-corpus-002-findings.md](phase-5-corpus-002-findings.md) — Harder-Q/A corpus designed to break the corpus-001 ceiling effect. 43 URLs, 14 vendors, dual-fetcher + LLM-judge pipeline.
- [v2-scoring-phase6-roadmap-prd.md](v2-scoring-phase6-roadmap-prd.md) — Product requirements document for the v2 scoring update and Phase 6 experimental program. Grounded in corpus-002 findings.

## Conventions

- **Direction before magnitude.** Findings state which scoring weights should move up or down; they do not assert precise target values unless a held-out corpus supports them.
- **Refusal to score what cannot be defended.** Signals with no measured retrieval-impact evidence are reported as diagnostics, not included in headline scores.
- **Each finding is traceable.** Every recommendation links to a specific pillar correlation, per-page observation, or structural argument. Recommendations without evidence are labeled as such.
