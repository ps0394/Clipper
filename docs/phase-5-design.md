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


1. **Generate 5 fact-based question/answer pairs** whose answers are
   unambiguously present in the page content (not inferred, not
   "general knowledge"). Generation uses a **different model family**
   than the scoring LLMs (see §4.1.1). A human reviewer edits/accepts
   /rejects each pair (~2 min/page); rejected pairs are regenerated
   until 5 per page pass review.
2. Feed the page's **raw extracted text** (not HTML, not rendered) to
   the scoring LLM with a prompt of the form: *"Using only the
   document below, answer the following questions. If the answer is
   not in the document, say 'not in document.' Answer: <Q>."*
3. Grade each answer against the reviewer-approved ground-truth answer.
   Binary correct/incorrect, plus a "not in document" false-negative
   category.

**Signal:** per-page correct-answer rate ∈ [0, 1].

**Why this task is right:** it directly tests whether the extracted
content is comprehensible and complete. It's also the closest proxy to
what a RAG agent does — fetch content, answer the user's question.

### 4.1.1 Question generation: cross-family guardrail

Fully hand-authoring 5 questions × 30 pages is ~12 hours and is the
dominant cost of Phase 5. Fully automating it collapses the measurement
into LLM-LLM agreement. We adopt a middle path:

- **Generator**: **Anthropic Claude** (specific model — Sonnet or
  Opus — chosen at pilot time based on API access). Cross-family
  separation from the scoring LLMs (OpenAI GPT-4o primary, Meta Llama
  3.x secondary) breaks the shared-training-data loop that would
  otherwise let the scoring LLM "recognize" its own style of question.
- **Generator prompt**: *"From the document below, write 5 fact-based
  questions whose answers are unambiguously stated in the document.
  For each question, provide the exact answer (quoted or paraphrased
  from the document) and the sentence(s) that support it. Questions
  must not require outside knowledge."*
- **Human review**: a single reviewer spends ~2 min/page editing,
  accepting, or rejecting each Q/A pair. Rejected pairs are regenerated.
  The reviewer's job is **not** to author questions — it is to enforce
  the "unambiguously in the document" rule and to catch leakage of
  outside knowledge. Review cost: ~1 hour at N=30, ~2 hours at N=60.
- **Disclosure**: the final Phase 5 report must state that questions
  were LLM-generated and human-reviewed, name the generator model, and
  report the reject rate from review. A high reject rate (say, >30%)
  is itself a finding about the page — pages where the generator
  cannot produce clean questions may be pages where structural quality
  is genuinely low.

**Why this is still valid measurement:** the generator cannot help the
scoring LLM answer; it only chooses *which* facts the scoring LLM is
tested on. A weakly-structured page will still produce questions whose
answers the scoring LLM fails to locate. What the guardrail prevents
is a stylistic handshake ("GPT-4o writes questions GPT-4o finds easy")
that would otherwise inflate scores uniformly.

**Weakness:** the generator may systematically skip content the
scoring LLM *can't* find (selection bias toward findable facts). We
partly mitigate this by requiring the generator to cite supporting
sentences; the reviewer checks that the 5 questions span different
sections of the page rather than clustering in one easy region.

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

**N = 60 pages** for the primary QA task (6 profiles × 10 pages),
stratified by:

- Content type: 10 pages per profile across landing, reference, sample,
  FAQ, tutorial, article. 10 pages per profile is the minimum for
  per-profile Spearman ρ to have meaningful 95% CI width.
- Vendor (Microsoft Learn, AWS Docs, Google Cloud Docs, Wikipedia, MDN,
  Stripe, and additional vendors as needed to fill profile × vendor
  cells): vendor diversity matters so findings don't reflect Learn
  alone.

N=60 is chosen over N=30 because the honest-null framing in §2
includes H0-profile ("per-profile LLM delta is not significant"). At
N=30 (5 pages per profile) we cannot reject H0-profile with any power,
so shipping N=30 would force us either to drop H0-profile from the
null list or to publish a finding we can't falsify. N=60 keeps the
hypothesis reachable. Cost implications are modest (see §8).

### Source and artifact layout

The 22-URL `tests/fixtures/classifier_corpus_golden.json` is the base.
Extend to 60 with hand-selected URLs that fill the profile × vendor
cells not yet covered.

Phase 5 artifacts live in two committed directories plus one ignored:

- **`evaluation/phase5-corpus/`** (committed, permanent) — the inputs
  and ground truth: URLs, captured HTML snapshots (for
  reproducibility), generator prompts and raw generator output,
  reviewer-approved questions and ground-truth answers, and the review
  audit trail (accept/edit/reject per pair).
- **`evaluation/phase5-results/`** (committed, per published run) —
  scoring-LLM outputs and graded results, one subdirectory per run
  tagged by date and LLM version, e.g.
  `results-2026-05-01-gpt4o/` and `results-2026-05-01-llama3/`. Only
  runs that back a published finding are committed.
- **`evaluation/phase5-scratch/`** (gitignored) — pilot runs, prompt
  iterations, and scratch experiments that do not back a finding.

Total estimated footprint at N=60: ~3 MB across corpus + one published
results pair. Small enough that Git LFS, separate branches, or external
storage would add more friction than they save. A `.gitattributes`
entry `evaluation/phase5-results/**/*.json text eol=lf` keeps diffs
readable across platforms.

**Licensing note.** Outputs from Anthropic Claude (generator) and
OpenAI GPT-4o and Meta Llama (scorers) are currently permitted by
their respective terms for use and redistribution. If Clipper ever
publishes this repo outside the current hosting, verify the model
providers' current TOS at publication time and include a one-line
model/date attribution in the findings doc.

### Ground-truth grading

Ground truth is produced by the generator-plus-review pipeline in
§4.1.1. A single reviewer enforces the "unambiguously in the document"
rule across all pages for consistency. On 20% of pages a second
reviewer independently re-runs the accept/edit/reject pass on the same
generator output; we report the inter-reviewer agreement (Cohen's κ)
on the accept/reject decision. If κ < 0.7 the review rubric is too
loose and must be tightened before the findings are published.

Answer grading (scoring-LLM output vs. reviewer-approved ground truth)
is binary and largely mechanical; the reviewer spot-checks 20% of
graded answers for correctness.

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

At the committed N=60 corpus size:

- **Question generation (LLM):** 60 pages through Anthropic Claude.
  ~30 k input tokens × 60 pages ≈ under $10.
- **Human review of generated Q/A:** ~2 min/page × 60 pages ≈ 2 hours.
  Reviewer edits, accepts, or rejects each pair; regeneration handles
  rejections.
- **Secondary review:** 20% × 60 = 12 pages re-reviewed by a second
  person for inter-rater κ on the accept/reject decision.
- **Scoring-LLM costs (estimate):** 60 pages × 5 questions × 3 runs ×
  2 LLMs = 1 800 inferences. At ~2 k tokens per inference (page text +
  Q + A), that's ~3.6 M input tokens. GPT-4o input is currently <$0.01
  per 1 k input tokens → under $40 for scoring. Open-weight secondary
  adds infrastructure cost but no per-token cost if self-hosted.
- **URL curation:** hand-selecting ~38 additional URLs (beyond the
  22-URL golden corpus) to fill profile × vendor cells. ~1–2 hours.
- **Code scaffolding:** generator prompt + runner, review UI (CLI is
  fine), scoring runner, grader harness, correlation analyzer, report
  generator. ~3–4 sessions.
- **Calibration loop:** pilot run on N=5 pages — generate, review,
  score, grade — to shake out the rubric before scaling to N=60.

Total: ~4–5 sessions of Copilot-assisted code + roughly 3–4 hours of
human review and URL curation. The critical path shifts from hand-authoring to reviewer
capacity, which is much cheaper but still gates the phase.

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

1. **LLM choice:** ~~is Azure OpenAI GPT-4o the right primary? Is any
   open-weight secondary worth the infrastructure cost?~~ **Resolved:
   GPT-4o primary + open-weight secondary (Llama 3.x family).** Both
   LLMs score; findings require correlations to agree within ±0.1
   Spearman ρ across the two to claim a result is about the pages
   rather than the primary model. Specific Llama variant chosen at
   pilot time based on infrastructure availability.
2. **Corpus size:** ~~N=30 or N=60?~~ **Resolved: N=60** (6 profiles
   × 10 pages). Required to keep H0-profile reachable; see §5. Pilot
   at N=5 before scaling to N=60.
3. **Question generator:** ~~which non-OpenAI, non-Meta model is the
   generator?~~ **Resolved: Anthropic Claude.** Specific Claude model
   (Sonnet vs. Opus) and API access path still TBD at pilot time, but
   the family is locked.
4. **Secondary reviewer:** ~~do we have a second person to re-run
   accept/reject on 20% of pages for κ?~~ **Resolved: yes, required.**
   A second reviewer must run accept/reject independently on 12 of the
   60 pages (60 Q/A pairs) before findings are published. Cohen's κ is
   computed on the accept/reject decision and reported in the findings
   doc. This is a blocking dependency for publication; see the tracking
   entry in `docs/improvement-plan.md` so it doesn't get forgotten.
5. **Commit LLM outputs to git?** ~~Generator output, review audit
   trail, and scoring-LLM outputs are large but they're the data of
   record. Consider a separate artifact branch or LFS.~~ **Resolved:
   yes, committed directly to git.** ~3 MB at N=60 doesn't justify
   LFS or external storage. Layout: `evaluation/phase5-corpus/`
   (permanent), `evaluation/phase5-results/<run-id>/` (per published
   run), `evaluation/phase5-scratch/` (gitignored). See §5.
6. **Audience.** ~~Does this phase produce a deliverable for a specific
   audience, or is it internal-only?~~ **Resolved: internal research,
   shared with a small product team.** Findings doc is written for
   engineers and PMs who understand Clipper's architecture. Implications
   for the methodology:
   - κ, Spearman ρ, and bootstrap CIs are reported with brief inline
     explanations, not assumed as reader background.
   - No blinded replication protocol, no peer review gate beyond the
     second-person review in §11.
   - Forbidden framings (§7) still apply — no "Learn leads" headlines,
     no replacing `parseability_score` — because the audience includes
     stakeholders who will act on the finding.
   - If the audience ever expands (external publication, customer
     deliverable), re-open this doc and harden the methodology section
     before publishing.

---

## 11. Decision gate

**Design status (2026-04-22): APPROVED.** All six open questions in §10
are resolved. See the tracking entry in `docs/improvement-plan.md`
Phase 5.

**Before any code:** ~~this document is reviewed and the six open
questions in §10 are resolved.~~ Done. Implementation may begin with
the pilot.

**During implementation:** pilot run on N=5 pages, single LLM, one
question per page. Review the output before scaling to N=60. If the
pilot reveals the rubric or prompt structure isn't working, revise the
design doc rather than pushing through.

**Post-run, before publishing findings:** a second person reviews the
correlations.json and the findings draft, specifically checking that
the three null hypotheses are each addressed and that forbidden framings
aren't creeping in.
