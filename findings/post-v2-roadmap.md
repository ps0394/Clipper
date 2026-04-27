# Clipper Post-v2 Roadmap

**Status:** Draft, April 27, 2026
**Author:** Phase 6 Session 6 close-out
**Supersedes:** the Block 5/6/7 sections of [v2-scoring-phase6-roadmap-prd.md](v2-scoring-phase6-roadmap-prd.md), which were written before cross-judge κ landed and before the served-markdown null finding.

---

## 1. Problem Statement

Clipper's v2 scoring model ships under the tag `v2-evidence-partial` because the evidence base is a single corpus (corpus-002, n=43, curated). As of Phase 6 Session 6, four of the five validation axes that gate the `-evidence-partial` qualifier have been settled:

| Validation axis | Status | Evidence |
|---|---|---|
| 1. Single-corpus correlation | ✅ Settled | r = +0.618 (Llama-3.3-70B, corpus-002, F2.6) |
| 2. Cross-judge robustness | ✅ Settled | r = +0.44 to +0.62 across Llama / GPT-4o / DeepSeek-V3.2 (F3.2-F3.5, Addendum G) |
| 3. Format robustness (served markdown) | ✅ Settled | Null on comprehension; F4.4 verdict `keep_as_diagnostic_only` |
| 4. Temporal robustness | ⏸ Optional hygiene | Re-fetch + hash-compare; pipeline is offline-deterministic by design |
| 5. **Generalization beyond corpus-002** | ❌ **Open and blocking** | Untested |
| 6. Retrieval-mode validity (vs comprehension) | ❌ **Open, blocking for v3** | F4.4 explicitly deferred to "Phase 7" |

The two open axes (5 and 6) are external-validity questions that corpus-002 cannot answer architecturally — corpus-002 is curated, comprehension-mode-only, and capped at 43 pages. **No additional corpus-002 work will move them.**

The risk if we ship v2 unqualified now without closing axes 5 and 6:

- **Selection-bias risk.** The +0.618 correlation might be a property of corpus-002's curation (14 vendors × 5 profiles, hand-picked for diversity) rather than a property of the v2 model. A reviewer with access to a fresh URL set could disprove the headline.
- **Regime-validity risk.** v2 is validated on comprehension-mode QA — the LLM has the full page in its context. Real agent retrieval is RAG: chunk + embed + retrieve. v2 has no evidence in that regime; F4.4's null finding on served markdown does not generalize.

The risk if we keep grinding on corpus-002 polish (more judges, more temporal replications, more weight tuning):

- **Diminishing returns.** v2 ships 50/50 weights; there is no fractional-weight knob left to turn. Four of six pillars already carry 0% headline weight. Cross-judge robustness is settled across three model families. The remaining corpus-002 work surfaces second-order effects, not first-order ones.

This document defines the work that closes axes 5 and 6 and moves Clipper from `v2-evidence-partial` to a `v2` baseline plus a v3 design path.

---

## 2. Objective

Move the v2 scoring model from internally-validated to externally-validated by:

1. **Generalizing v2 beyond corpus-002** — a fresh corpus (corpus-003) with non-overlapping URLs and a methodologically pre-registered selection process.
2. **Establishing retrieval-mode validity** — a Phase 7 RAG benchmark on top of corpus-003 to test whether v2 predicts retrieval performance, not just comprehension.
3. **Designing v3 from those two new evidence bases** — pillar selection, weight tuning, and confidence ranges all calibrated against corpus-002 ∪ corpus-003 evidence in both retrieval and comprehension modes.

The end state is:

- v2 ships without the `-evidence-partial` suffix once corpus-003 generalization is confirmed.
- v3 ships once Phase 7 retrieval-mode evidence is in hand and the pillar architecture has been updated against it.
- The `keep_as_diagnostic_only` verdict on served markdown either survives the retrieval-mode test or gets explicitly reopened.

---

## 3. Acceptance Criteria

### Block A — Corpus-003 Generalization

- [ ] **A1.** Corpus-003 spec doc published with URL list under `evaluation/corpus-003/` *before* fetching, so selection is auditable.
- [ ] **A2.** Corpus-003 fetched (Tier 1 raw + Tier 2 rendered) and scored through the v2 pipeline. Tri-fetcher records served-markdown availability per page as diagnostic-only.
- [ ] **A3.** Cross-judge regression check: pooled per-judge mean **r ≥ +0.35** between v2 composite and `accuracy_rendered`, computed under at least 2 judges (Llama + one other). 3 judges if Foundry budget permits.
- [ ] **A4.** Cross-corpus stability table published: per-pillar r on corpus-002 vs corpus-003. Identifies any pillar whose correlation flips sign or drops > 0.20 between corpora.
- [ ] **A5.** If A3 passes, drop `-evidence-partial` from the release tag. If A3 fails, do not ship v3; diagnose first (which pillar, which vendor distribution, which profile).

### Block B — Temporal Hygiene (Parallel, Lower Priority)

- [ ] **B1.** corpus-002 re-fetched at T+4 (Apr 27), T+14 (May 7), and T+30 (May 23) without any code changes. HTML hash compared per page.
- [ ] **B2.** Drift report published: per-vendor and per-page page-content stability over each window. Identifies pages with content drift vs pages where the score moved without content change.
- [ ] **B3.** If > 20% of pages show |Δuniversal_score| > 10 points without content changes, investigate before any v3 announcement.

### Block C — Phase 7 Retrieval-Mode Benchmark

- [ ] **C1.** Phase 7 design doc published: chunker config, embedder, retriever, top-k, grading protocol. Pre-registered before any runs.
- [ ] **C2.** `retrievability/phase7/` module mirrors the `phase5/` shape: generator, scorer, judge.
- [ ] **C3.** Phase 7 run against corpus-003 with the same Q/A pairs used in Block A, so paired comprehension ↔ retrieval comparison is possible.
- [ ] **C4.** Format question revisited: does served markdown lift accuracy in retrieval mode? If lift > +0.10 on ≥ 2 vendors → F4.4 reopens; markdown becomes a candidate v3 signal. If not → `keep_as_diagnostic_only` is now defended in both regimes.

### Block D — v3 Design

- [ ] **D1.** Pillar-selection note: which pillars carry retrieval-relevance evidence in *both* corpus-003 comprehension *and* Phase 7 retrieval, above an explicit threshold (proposal: r ≥ +0.20 in both regimes).
- [ ] **D2.** v3 weight table with weight ranges (not point values) calibrated against corpus-002 ∪ corpus-003 ∪ Phase 7. Profile-specific reweighting if and only if per-profile correlations differ by > 0.15.
- [ ] **D3.** v3 confidence ranges replace the coarse 50/50 v2 composite. Bootstrap CIs over corpora *and* judges *and* regimes — not just pages.
- [ ] **D4.** `docs/scoring.md` rewritten for v3. Migration guide from v2.
- [ ] **D5.** Optional: a Fetch Integrity pillar if challenged-fetch corpus-003 pages produce a separable signal.

---

## 4. Session-Level Breakdown

Sessions are dependency-ordered, not time-boxed. Entry and exit criteria below; do not start a session before its entry criteria pass.

### Session 7 — Corpus-003 Spec (F6.1)

- **Entry:** Phase 6 Session 6 closed (current state).
- **Work:**
  - Define corpus composition: 5 vendors × 5 profiles × 5 pages floor (n=125); 6 × 5 × 20 (n=600) stretch.
  - Vendor selection rule: ≤ 5 overlap with corpus-002. Document why each vendor is in.
  - Profile balance: equal cells if possible; otherwise per-profile floor of 5 pages.
  - Include challenged-fetch pages per F6.2 (Cloudflare-challenged, robots-blocked, UA-allowlisted) — these are what allow a Fetch Integrity pillar to be evaluated in v3.
  - Pre-register URL list in `evaluation/corpus-003/urls.txt` and the spec in `evaluation/corpus-003/spec.md` *before* fetching.
- **Exit:** spec doc and URL list committed; methodology reviewed.
- **Risk:** if URL list changes after fetching, all generalization claims become post-hoc and must be re-run.

### Session 8 — Corpus-003 Fetch & Score

- **Entry:** Session 7 spec + URL list locked.
- **Work:**
  - Run `python main.py phase5 run` against corpus-003 URLs.
  - Tri-fetcher logs served-markdown availability (diagnostic-only).
  - Generator produces 5 Q/A per page using the same prompt as corpus-002 for parity.
  - Primary judge (Llama-3.3-70B) grades all pages.
  - Run cross-judge rejudge on at least one additional judge (GPT-4o or DeepSeek-V3.2). 3-judge panel if Foundry budget permits.
- **Exit:** all per-page artifacts on disk under `evaluation/phase5-results/corpus-003/`.
- **Cost note:** at corpus-003 floor (n=125), expect roughly 3× the LLM cost of corpus-002 per pass. Budget accordingly.

### Session 9 — Corpus-003 Regression & Stability Analysis

- **Entry:** Session 8 grading complete.
- **Work:**
  - Run F2.6 regression check: v2 composite vs accuracy_rendered on corpus-003.
  - Run F3.5 cross-judge gate check: composite-vs-accuracy r per judge, all clear +0.35 ship gate.
  - Cross-corpus per-pillar stability table: which pillar correlations move > 0.20 between corpus-002 and corpus-003.
  - Identify any pillar whose correlation flips sign — that's a v3 design signal, possibly a v2 demotion.
- **Exit:** Block A acceptance criteria A3 and A4 either pass or fail.
  - **A3 passes** → strip `-evidence-partial`; release v2 as `v2`.
  - **A3 fails** → do not strip the suffix; open a diagnosis sub-session before continuing to Block C.

### Session 10 — Temporal Replication Pass (B1, B2, B3)

- **Entry:** can run in parallel with Sessions 8-9; no dependency.
- **Work:**
  - Re-fetch corpus-002 at T+4 (Apr 27), T+14 (May 7), T+30 (May 23). No code changes between runs.
  - Per-page rendered-HTML hash comparison.
  - Per-page score deltas, separated into "content changed" vs "score moved without content change."
  - If the latter exceeds 20% of pages, investigate.
- **Exit:** Drift report published. If clean, append a temporal-stability section to corpus-002 findings doc. If dirty, open a sub-session to diagnose.
- **Note:** no new judging required; this is HTML/score stability, not accuracy stability. Cheap.

### Session 11 — Phase 7 Design Doc (C1)

- **Entry:** Session 9 closed (Block A passes).
- **Work:**
  - Pick chunker (proposal: `langchain.text_splitter.RecursiveCharacterTextSplitter`, chunk_size=1000, overlap=100).
  - Pick embedder (proposal: a single fixed embedding model, `text-embedding-3-small` or equivalent on Foundry).
  - Pick retriever: top-k=5, cosine similarity, no rerank in v1.
  - Pick grading protocol: same 3-judge panel as Block A, but on retrieved chunks instead of full pages.
  - Define metrics: answer accuracy given retrieved context; recall@k against ground-truth chunk.
  - Pre-register all hyperparameters in `findings/phase-7/00-design.md` *before* implementation.
- **Exit:** design doc committed and reviewed.

### Session 12 — Phase 7 Implementation (C2)

- **Entry:** Session 11 design committed.
- **Work:**
  - New module `retrievability/phase7/` mirrors the `phase5/` shape: generator, scorer, judge.
  - Reuses Foundry deployments from Phase 5/6.
  - New CLI subcommand `python main.py phase7 ...` with the same surface (run, rejudge, etc.).
  - Unit tests for chunker, retriever, and grading wiring.
- **Exit:** module passes 179+ tests; can run end-to-end on a 3-page smoke corpus.

### Session 13 — Phase 7 Run on Corpus-003 (C3, C4)

- **Entry:** Session 12 implementation green.
- **Work:**
  - Run Phase 7 against corpus-003 with the same Q/A pairs used in Block A.
  - Produce paired comprehension-mode and retrieval-mode accuracy per page.
  - Cross-format analysis: served-markdown lift in retrieval mode.
  - If lift > +0.10 on ≥ 2 vendors, F4.4 reopens; markdown becomes a v3 candidate signal. If not, the `keep_as_diagnostic_only` verdict is now defended in both regimes.
- **Exit:** Phase 7 findings doc published.

### Session 14 — v3 Pillar Architecture (D1, D2)

- **Entry:** Sessions 9 and 13 closed.
- **Work:**
  - Pillar selection rule: pillar carries weight in v3 if r ≥ +0.20 against accuracy in *both* corpus-003 comprehension and Phase 7 retrieval.
  - Build the v3 weight table with weight *ranges* (not point values), computed via bootstrap over corpora ∪ judges ∪ regimes.
  - If challenged-fetch pages in corpus-003 produce signal, propose a Fetch Integrity pillar.
  - Profile-specific reweighting only if per-profile correlations differ by > 0.15.
- **Exit:** v3 weight table + pillar selection note committed.

### Session 15 — v3 Confidence Ranges + Doc (D3, D4)

- **Entry:** Session 14 closed.
- **Work:**
  - Replace the coarse 50/50 v2 composite with calibrated v3 weights per Session 14.
  - `ScoreResult.confidence_range` populated from real bootstrap intervals.
  - Rewrite `docs/scoring.md` for v3. Migration guide from v2 included.
  - Tag release as `v3`.
- **Exit:** v3 ships.

---

## 5. Sequencing Diagram

```
Now ────► Session 7 (corpus-003 spec)
            │
            ├──► Session 10 (temporal, parallel)
            │
            ▼
         Session 8 (fetch + grade)
            │
            ▼
         Session 9 (regression + stability)
            │
            ▼  [A3 passes → strip -evidence-partial]
            │
            ▼
         Session 11 (Phase 7 design)
            │
            ▼
         Session 12 (Phase 7 impl)
            │
            ▼
         Session 13 (Phase 7 run on corpus-003)
            │
            ▼
         Session 14 (v3 pillar arch)
            │
            ▼
         Session 15 (v3 ship)
```

---

## 6. What This Roadmap Explicitly Does Not Do

- **No more corpus-002 polish.** Per-vendor cross-judge CIs, second-order κ analyses, additional judges beyond the existing 3 — all rounding error. Corpus-002 is closed evidence.
- **No 4th judge on corpus-002.** The Llama / GPT-4o / DeepSeek panel already represents three model families and three severity calibrations. A 4th would reduce the per-judge CI by ~0.02.
- **No new pillars on corpus-002 alone.** Any v3 pillar promotion must be evidenced in corpus-003 + Phase 7. corpus-002 is the existence case, not the generalization case.
- **No `parseability_score` revival in v3.** Profile-weighted scoring stays collapsed until per-profile corpora are large enough to defend per-profile weights — which corpus-003 alone may not achieve. That's a v4 question.
- **No agent-customization scoring (e.g. custom user-agent allowlist credit) until corpus-003 has challenged-fetch pages and Phase 7 measures their retrieval impact.**

---

## 7. Decision Points Worth Flagging Now

These are choices that should be made deliberately, not by default:

- **Corpus-003 size.** 125-floor vs 600-stretch is a 4-5× cost decision. Recommendation: 125 if Foundry budget is the constraint; 250 if it's not.
- **Vendor overlap with corpus-002.** ≤ 5 overlapping vendors keeps the generalization claim clean but limits per-vendor stability analysis. ≥ 8 lets us build per-vendor cross-corpus CIs at the cost of weakening "fresh" claims. Recommendation: 5.
- **Phase 7 chunker choice.** The chunker is the single biggest free parameter in the retrieval-mode benchmark. Pre-registering one config closes design freedom; running an A/B opens it back up. Recommendation: pre-register one config, document the assumption, defer A/B to v4.
- **3-judge panel on corpus-003.** Triples the LLM cost of grading. Recommendation: run only Llama on the first pass, add GPT-4o on the second pass once the regression has passed; defer DeepSeek unless cross-judge variance specifically becomes a story.

---

## 8. Cross-References

- v2 specification and weight table: [`docs/scoring.md`](../docs/scoring.md)
- v2 calibration evidence: [`findings/phase-5-corpus-002-findings.md`](phase-5-corpus-002-findings.md)
- v2 cross-judge evidence (latest): [`findings/phase-5-corpus-002-findings.md`](phase-5-corpus-002-findings.md) Addendum G
- v2 ship gate (cross-judge): [`evaluation/phase5-results/corpus-002-analysis/v2-gate-cross-judge.json`](../evaluation/phase5-results/corpus-002-analysis/v2-gate-cross-judge.json)
- Original PRD this roadmap supersedes (Blocks 5+): [`findings/v2-scoring-phase6-roadmap-prd.md`](v2-scoring-phase6-roadmap-prd.md)
- Phase 5 topical findings index: [`findings/phase-5/README.md`](phase-5/README.md)
