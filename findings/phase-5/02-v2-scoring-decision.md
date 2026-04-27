# 02 — The v2 scoring decision

> **Key point.** v2 is a structural change to Clipper's headline composite, not a re-weighting. Two pillars carry the score; four are demoted to diagnostic-only. The shipping v2 composite correlates with measured agent retrieval at **r = +0.618** on corpus-002.

The decision arrived in three steps. Each step was a separate gate; none of the steps could have been skipped.

---

## Step 1 — Re-weighting alone fails

A projected-correlation gate (Session 1, F1.2) tested whether re-weighting the existing six pillars could move the composite from r ≈ 0 to a target of r ≥ +0.35.

| Candidate | sem | ext | struct | dom | meta | http | Pearson r | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| v1_baseline_article | 0.25 | 0.20 | 0.20 | 0.15 | 0.10 | 0.10 | −0.007 | fail |
| A_extractability_40 | 0.10 | 0.40 | 0.10 | 0.10 | 0.15 | 0.15 | +0.278 | fail |
| B_extractability_35 | 0.10 | 0.35 | 0.15 | 0.10 | 0.15 | 0.15 | +0.224 | fail |
| C_extractability_30 | 0.15 | 0.30 | 0.15 | 0.10 | 0.15 | 0.15 | +0.170 | fail |
| **D_drop_semantic_and_dom** | 0.05 | 0.40 | 0.15 | 0.05 | 0.20 | 0.15 | **+0.315** | fail |
| E_http_metadata_lift | 0.05 | 0.30 | 0.15 | 0.05 | 0.20 | 0.25 | +0.285 | fail |

**Best candidate: r = +0.315.** Below the +0.35 ship threshold.

The result is not "re-weighting moved nothing." It moved the composite from −0.007 to +0.315 — a swing of ~0.32. **It is "re-weighting alone cannot reach the threshold."** At least one of {pillar measurement quality, pillar selection, accuracy signal granularity} is also limiting the ceiling.

A pre-committed decision rule said: if best r is between 0.32 and 0.35, ship Candidate D as a fallback; if best r < 0.32, defer; if a structural reformulation passes, ship that. The next step tested the third option.

---

## Step 2 — Structural reformulations pass decisively

The γ-experiments script (Session 1, F1.3) tested four classes of reformulation, not just re-weightings:

| Experiment | Best variant | r | Gate |
|---|---|---:|:---:|
| Drop one pillar | drop `structured_data` | **+0.457** | ship |
| Drop one pillar | drop `semantic_html` | +0.341 | directional |
| **Top-2 corr-proportional** (`ext` + `http`) | 0.67 / 0.33 | **+0.570** | ship |
| Top-2 equal | 0.50 / 0.50 | **+0.548** | ship |
| Top-3 equal (`ext` + `http` + `meta`) | 0.33 each | +0.465 | ship |
| Top-4 equal (+ `struct`) | 0.25 each | +0.252 | fail |
| Z-score + Candidate D | — | +0.457 | ship |
| Rank-based + Candidate D | — | +0.396 | ship |
| Binary median-gate | — | +0.281 | fail |

**Four independent reformulations exceeded the ship gate.** Restricting to the top-2 positively-correlating pillars (equal weight) reached r = +0.548. Restricting with correlation-proportional weights reached +0.570.

### What the negative results add

- **Top-4 equal at r = +0.252.** Once `structured_data` is given weight equal to the positive pillars, the composite is dragged back down. `structured_data` contributes noise to corpus-002, not signal.
- **Binary median-gate at r = +0.281.** Agent-readiness is continuous, not pass/fail. Treating it as a threshold loses signal.

---

## Step 3 — The shipping v2 configuration

Per the PRD's ranges-not-points discipline, the overfit risk on `top2_corr_proportional` (an exact 0.67/0.33 split fit to a 43-page corpus) argues for the slightly less precise but more defensible variant:

| Pillar | v2 headline weight | Role |
|---|---:|---|
| `content_extractability` | **0.50** | headline |
| `http_compliance` | **0.50** | headline |
| `semantic_html` | 0.00 | diagnostic only |
| `structured_data` | 0.00 | diagnostic only |
| `dom_navigability` | 0.00 | diagnostic only |
| `metadata_completeness` | 0.00 | diagnostic only |

The four zero-weighted pillars **continue to be measured and reported** in the audit trail. They are not deleted. They are excluded from the headline number until a corpus shows they predict retrieval relevance.

### Live regression on the shipping code

The v2 scorer additionally demotes `agent_content_hints` (markdown-alt link, `markdown_url` meta, `llms.txt`, non-HTML alternates, `data-llm-hint`) inside `http_compliance` to diagnostic-only. The live regression replays this against the on-disk corpus-002 captures:

| metric | value |
|---|---|
| N | 43 |
| v1 parseability mean | 54.57 |
| v2 headline mean | 71.14 |
| Pearson r (v1 composite vs accuracy_rendered) | −0.0086 |
| **Pearson r (v2 composite vs accuracy_rendered)** | **+0.6181** |
| Ship gate | r ≥ +0.35 |
| Decision | **PASS** |

The v2 r is **higher** than the +0.548 γ-projection because removing `agent_content_hints` from `http_compliance` strengthens that pillar's correlation. Hint signals were *detractors* on corpus-002, not neutral additions.

---

## What v2 ships under, and what it does not claim

**Authorized claims (with the `v2-evidence-partial` tag):**
- v2 correlates moderately with measured agent retrieval accuracy on corpus-002 (r = +0.618, n = 43).
- The structural change — four pillars demoted to diagnostic-only — is supported by single-pillar correlations and four independent reformulation experiments.
- Diagnostic-only pillars are still measured and surfaced.

**Not authorized:**
- Precise weight values. 50/50 is deliberately coarse.
- Cross-vendor "template quality" rankings. See [03-judge-confidence-intervals.md](03-judge-confidence-intervals.md).
- "Permanent" demotion of the four diagnostic-only pillars. They are demoted *until a corpus shows retrieval-relevance.*
- Generalization to non-English / non-developer-documentation content.

---

## Why this matters in plain language

> *v2 scores what predicts agent retrieval accuracy on our corpus. Four of the six v1 pillars failed to predict it. v2 keeps those four as diagnostic findings and drops them from the headline.*

This is a much larger change than "tune the numbers." It is the first time Clipper's composite is anchored to a measured outcome rather than to standards-compliance intuition. The downside, faithfully labeled, is that the anchor is one corpus and one grader architecture. See [06-what-this-does-not-support.md](06-what-this-does-not-support.md).
