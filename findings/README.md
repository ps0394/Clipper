# Clipper Corpus Findings

Evidence-based findings from Clipper's corpus-level retrievability experiments. Each document in this directory reports a single corpus, its methodology, its results, and the specific scoring decisions the evidence supports or refutes.

## Contents

- [post-v2-roadmap.md](post-v2-roadmap.md) — Roadmap defining the v2-evidence-partial scoring model, the corpus-003 ship gate, and Section 10 external literature anchors. **Authoritative source for the corpus-003 generalization result.**
- [clipper-next-design.md](clipper-next-design.md) — Design sketch for the post-v3 ("Clipper-next") rewrite. Translates `post-v2-roadmap.md` §10.3 into three measurement tracks (citation-share DV, groundedness diagnostic, confound controls), eight open decisions, and four ship gates. **Input document for Session 11 decision-making.**
- [v2.1-release-scope.md](v2.1-release-scope.md) — Scope for the v2.1 honest-re-labeling release: `--diagnostic-mode` flag, per-result `methodology` block, README/docs updates anchored to the corpus-003 numbers.
- [phase-5-corpus-002-findings.md](phase-5-corpus-002-findings.md) — Harder-Q/A corpus designed to break the corpus-001 ceiling effect. 43 URLs, 14 vendors, dual-fetcher + LLM-judge pipeline.
- [v2-scoring-phase6-roadmap-prd.md](v2-scoring-phase6-roadmap-prd.md) — Product requirements document for the v2 scoring update and Phase 6 experimental program. Grounded in corpus-002 findings.
## Conventions

- **Direction before magnitude.** Findings state which scoring weights should move up or down; they do not assert precise target values unless a held-out corpus supports them.
- **Refusal to score what cannot be defended.** Signals with no measured retrieval-impact evidence are reported as diagnostics, not included in headline scores.
- **Each finding is traceable.** Every recommendation links to a specific pillar correlation, per-page observation, or structural argument. Recommendations without evidence are labeled as such.
