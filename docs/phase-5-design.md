# Phase 5 Design — LLM Ground-Truth Validation

**Status:** Draft for review. Nothing has been implemented.
**Owner:** tbd
**Date:** 2026-04-22

---

## 1. Purpose

Every pillar in Clipper's scoring model is a **proxy** for agent
retrievability: we measure structural properties (semantic HTML,
JSON-LD, HTTP compliance, etc.) that we believe correlate with how well
an AI agent can read and use a page. Phase 5 is the only item in the
improvement plan that measures retrievability **directly** and asks
whether that correlation actually holds.

The deliverable is a **correlation analysis**, not a new score. If the
structural-to-LLM correlation is strong, the pillar weights are
defensible and the framework stands. If it's weak, the scoring model is
on shakier ground than we currently claim, and later calibration work
gets a clear target.

**Hard rule:** LLM scoring is an instrument, not a verdict. It does not
replace `parseability_score` or `universal_score`. It is reported as a
third, separate axis alongside them.

---

## 2. Honest-null framing

Before any data collection, we commit to the null hypotheses that would
disprove the model:

**H0-strong:** Across the calibration corpus, no pillar's score
correlates with LLM task performance at Spearman ρ ≥ 0.3 (p < 0.05).

> If H0-strong is not rejected, the structural scoring model is not
> measuring agent retrievability in any observable way. The response
> would be to either abandon the composite score and report pillars
> individually, or redesign the measurement from scratch.

**H0-weight:** The pillar-weight ordering implied by correlation
strength does not match the ordering currently encoded in the `article`
profile weights (Semantic HTML 25%, Content Extract 20%, Structured
Data 20%, DOM Nav 15%, Metadata 10%, HTTP 10%).

> If H0-weight is not rejected, the default weights are arbitrary rather
> than empirically grounded. The response would be to recalibrate
> profile weights using the observed correlations, with a documented
> methodology.

**H0-profile:** For any content-type profile (landing / reference /
sample / faq / tutorial), the LLM-performance delta between pages scored
under that profile and pages scored under `article` is not statistically
significant.

> If H0-profile is not rejected for every profile, content-type
> awareness does not change measurement quality, and the profile system
> is over-engineered.

A Phase 5 report that does not address each of these explicitly is
incomplete.

---

## 3. LLM selection

Decision required before build.

### Candidates

| Candidate | Reproducibility | Access | Cost (rough) | Notes |
|---|---|---|---|---|
| Azure OpenAI GPT-4o | High (fixed model + seed) | GitHub Enterprise provides access | $ per-token, bounded | Matches Learn's primary agent surface. Preferred. |
| Azure OpenAI GPT-5 | Unknown stability at draft time | Same | $$ | Worth testing if available, but output drift may confound Phase 5's reproducibility story. |
| Anthropic Claude (via API) | High | Requires separate billing | $$ | Diversifies the instrument. Useful as a second-LLM check but not the primary. |
| Open-weight (Llama 3.x via Azure AI Studio / local) | Highest (deterministic) | Requires inference infrastructure | Infra cost | Cheapest marginal; no API quota limits. |

### Recommendation

**Primary:** Azure OpenAI GPT-4o via GitHub Enterprise access.
**Secondary (robustness check):** one open-weight model (Llama 3.x or
similar) run on the same corpus. If correlations agree within ±0.1
Spearman ρ across the two instruments, we can claim the finding is about
the pages rather than about the primary LLM.

**Explicitly not:** no ensembling, no "average the LLMs." Each model
produces its own correlation table. Agreement between them is evidence;
averaging them hides the signal we care about.

---

## 4. Task design

The LLM's observable behavior is the measurement. Four candidates,
ordered by how directly they model agent retrievability:

### 4.1 Question-answering accuracy (PRIMARY)

For each page:

1. Hand-author 5 fact-based questions whose answers are unambiguously
   present in the page content (not inferred, not "general knowledge").
2. Feed the page's **raw extracted text** (not HTML, not rendered) to
   the LLM with a prompt of the form: *"Using only the document below,
   answer the following questions. If the answer is not in the
   document, say 'not in document.' Answer: <Q>."*
3. Grade each answer against the hand-authored ground-truth answer.
   Binary correct/incorrect, plus a "not in document" false-negative
   category.

**Signal:** per-page correct-answer rate ∈ [0, 1].

**Why this task is right:** it directly tests whether the extracted
content is comprehensible and complete. It's also the closest proxy to
what a RAG agent does — fetch content, answer the user's question.

**Weakness:** 5 questions × N pages is a lot of hand authoring. Scaling
is the main cost.

### 4.2 Summarization faithfulness (SECONDARY)

Ask the LLM to summarize the extracted text. Grade the summary against
the source for factual fidelity (hallucination rate) and coverage
(what percent of the five-question gold set can be answered from the
summary alone).

**Signal:** hallucination rate + coverage. Two correlated sub-measures.

**Why it's secondary:** grading summaries for faithfulness is itself
subjective and needs its own rubric. Useful as a robustness check
against 4.1.

### 4.3 Citation extraction (TERTIARY)

Ask the LLM to identify the 3 most informative sentences from the page
for a given topic. Measure whether the cited sentences match what a
human annotator considers the key claims.

**Weakness:** heavily subjective grading. Not primary.

### 4.4 Structural comprehension probes (DISCARD)

"Does this page have an H1? What's in the JSON-LD?" — these test what
Clipper already measures. Tautological. Not useful.

### Recommendation

**Use 4.1 (QA accuracy) as the primary task.** Use 4.2
(summarization faithfulness) as a robustness check on a **subset** of
the corpus (say, 10 pages) rather than the whole thing, to keep
hand-grading cost bounded.

---

## 5. Calibration corpus

### Size

**Minimum N = 30 pages** for the primary QA task, stratified by:

- Content type (6 profiles × 5 pages = 30): one landing, one reference,
  one sample, one FAQ, one tutorial, one article per vendor bucket.
- Vendor (Microsoft Learn, AWS Docs, Google Cloud Docs, Wikipedia, MDN,
  Stripe): vendor diversity is important so findings don't reflect Learn
  alone.

**Ideal N = 60** (6 profiles × 10 pages). At N=30, per-profile power is
thin (5 pages per profile) and we should report per-profile findings as
"directional" rather than "significant."

### Source

The 22-URL `tests/fixtures/classifier_corpus_golden.json` is the base.
Extend to 30–60 with additional hand-selected URLs that hit the profile
× vendor cells that are currently empty. Commit a
`evaluation/phase5-corpus/` directory with: URLs, captured HTML
snapshots (for reproducibility), hand-authored questions, ground-truth
answers, and (eventually) LLM outputs.

### Ground-truth grading

Hand-authored by a single annotator for consistency; spot-checked by a
second annotator on 20% of pages to measure inter-rater agreement
(Cohen's κ). Report κ with the final results; if κ < 0.7 the grading
rubric is too loose and must be tightened.

### Variance control

- **Fixed seed** where the LLM supports it (Azure OpenAI does).
- **N=3 runs per page-question** with a fixed seed. Report mean ±
  stddev for the per-page correct-answer rate.
- If per-question stddev across runs exceeds 0.2 on any question,
  drop that question (too ambiguous).

---

## 6. Correlation methodology

### Primary analysis

For each pillar, compute **Spearman ρ** between the pillar's score
across the corpus and the per-page LLM QA accuracy. Report:

- ρ and 95% CI (bootstrap, 10 000 resamples)
- p-value against H0-strong (ρ = 0)
- Per-profile ρ (with the "directional at N=5" caveat)
- Correlation across the two LLMs (primary + secondary)

### Secondary analysis

- Multi-pillar regression: do any two pillars together explain more
  variance than their individual ρs imply? If yes, that's evidence for
  an interaction term the composite score is currently missing.
- Rendered-vs-raw comparison: does the rendered-mode score correlate
  more strongly with LLM accuracy than raw? If not, we're paying the
  browser cost for nothing.

### Not in scope

- ROC curves, F1 scores, or any "agent-ready threshold" tuning. Those
  are downstream products once we have a correlation to calibrate
  against.
- Retraining or fine-tuning any LLM. The instrument is an off-the-shelf
  model being prompted.

---

## 7. Reporting

Output artifacts, committed to `evaluation/phase5-results/`:

1. `correlations.json` — full per-pillar ρ, CI, p-value, per-profile
   breakdown, per-LLM breakdown.
2. `phase5-findings.md` — human-readable report structured around the
   three null hypotheses in §2. Either rejects each or does not, with
   data. No cross-vendor framing, no "Learn leads by X points"
   headlines — that's not what this phase produces.
3. `phase5-methodology.md` — the corpus construction, question
   authoring rubric, grading rubric, seed values, and LLM configuration
   needed to reproduce.

**Forbidden framings (same as in the Copilot comparison-report rules):**
Phase 5's findings must not be presented as "the LLM says Learn is
better" or as a new headline score. They are findings about whether the
structural scoring model tracks what an LLM can actually do with a page.

---

## 8. Cost and timeline

- **Hand authoring:** 5 questions × 30 pages = 150 questions. Single
  annotator at ~5 minutes per question = ~12 hours.
- **Secondary grading:** 20% × 30 = 6 pages × 5 questions × 2 runs = 60
  graded answers from a second annotator.
- **LLM costs (estimate):** 30 pages × 5 questions × 3 runs × 2 LLMs =
  900 inferences. At ~2k tokens per inference (page text + Q + A),
  that's ~1.8 M input tokens. GPT-4o input is currently <$0.01 per 1 k
  input tokens → under $20 for the primary run.
- **Code scaffolding:** prompt template, runner, grader harness,
  correlation analyzer, report generator. ~3 sessions.
- **Calibration loop:** one pilot run on 5 pages to shake out the
  rubric before scaling to 30.

Total: 4–5 sessions of Copilot-assisted code + roughly 2 working days
of human hand-authoring and grading. The hand-authoring is the critical
path, not the code.

---

## 9. Non-goals

- Running LLM evaluation in CI or as part of `python main.py express`.
  This is a research pipeline, not a scoring component.
- Replacing `parseability_score`. The LLM score is a third, separate
  axis and is reported alongside the structural scores, not instead of
  them.
- Scoring every page Clipper ever evaluates. The calibration corpus is
  finite and hand-curated. Running LLM evaluation on arbitrary URLs is
  out of scope.
- Using LLM output to tune pillar weights within this phase. If the
  correlations justify recalibration, that is a separate, deliberate
  follow-up with its own design doc and its own review.

---

## 10. Open questions for review

1. **LLM choice:** is Azure OpenAI GPT-4o the right primary? Is any
   open-weight secondary worth the infrastructure cost, or do we accept
   a single-LLM finding with that limitation disclosed?
2. **Corpus size:** N=30 or N=60? The marginal cost of 30 more pages
   is ~12 more hours of hand-authoring but roughly doubles per-profile
   power.
3. **Secondary annotator:** do we have one? Inter-rater agreement is
   hard to report if the answer is "the same person graded everything."
4. **Commit LLM outputs to git?** They're large but they're the data
   of record. Consider a separate artifact branch or LFS.
5. **Does this phase produce a deliverable for a specific audience,
   or is it internal-only?** Changes the tone and methodology rigor of
   the findings doc.

---

## 11. Decision gate

**Before any code:** this document is reviewed and the five open
questions in §10 are resolved. A `phase-5-design-approved` marker is
added to `docs/improvement-plan.md` referencing the decisions made.

**During implementation:** pilot run on N=5 pages, single LLM, one
question per page. Review the output before scaling to N=30. If the
pilot reveals the rubric or prompt structure isn't working, revise the
design doc rather than pushing through.

**Post-run, before publishing findings:** a second person reviews the
correlations.json and the findings draft, specifically checking that
the three null hypotheses are each addressed and that forbidden framings
aren't creeping in.
