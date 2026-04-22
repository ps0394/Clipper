# Phase 5: Next Session Plan

**Status at end of 2026-04-22:** Pilot runner works end-to-end. N=5 run committed at [evaluation/phase5-results/pilot-001/](../evaluation/phase5-results/pilot-001/). Three Foundry deployments (Mistral Large 3, GPT-4.1, Llama 3.3 70B) verified live. Grader is the choke point.

## Observed problem

Pilot mean accuracy came out at 20% — not because GPT-4.1 is answering wrong, but because the substring grader rejects semantically-equivalent rephrasings.

Concrete case from [stripe-com-docs-api-charges-create/grades.primary.json](../evaluation/phase5-results/pilot-001/stripe-com-docs-api-charges-create/grades.primary.json):

| # | Ground truth (Mistral-generated) | GPT-4.1 answer | Substring grader | Reality |
|---|---|---|---|---|
| 0 | `charge` | `charge` | correct | correct |
| 1 | `1099 in USD` | `1099, usd` | **incorrect** | correct |
| 2 | `visa` | `visa` | correct | correct |
| 3 | `normal` | `normal` | correct | correct |
| 4 | `Expiration month is 3 and year is 2024` | `3, 2024` | **incorrect** | correct |

Actual accuracy on that page: 5/5. Reported: 3/5. The grader is the measurement instrument; calibrating it is a prerequisite for every correlation claim downstream.

## Priority-ordered work for tomorrow

### 1. LLM-as-judge grader (BIGGEST UNLOCK)

**What.** Replace the substring heuristic in [retrievability/phase5/grader.py](../retrievability/phase5/grader.py) with a scoring-LLM call that receives `(question, ground_truth_answer, candidate_answer)` and returns one of `correct / incorrect / not_in_document` plus a short rationale.

**Design sketch:**

- New module `retrievability/phase5/judge.py` with a `JudgeClient` Protocol and a `judge_answer(question, ground_truth, candidate) -> (label, rationale, tokens_in, tokens_out)` function.
- New prompt file `retrievability/phase5/prompts/judge.txt`. Keep it short and strict: "Reply with exactly one of: CORRECT / INCORRECT / NOT_IN_DOCUMENT, followed by one line of justification."
- Extend `Grade` schema (or add sibling `JudgedGrade`) with `rationale: str` and `judge_model: str`. Keep the old substring grader around as `grade_answer_substring()` for comparison and for cheap CI checks.
- Wire a new flag `--grader {substring,llm}` into `phase5 pilot`. Default `llm` once the calibration below is passed.

**Judge-model choice.** Use GPT-4.1 (the primary scorer) as the judge. It's already deployed, and using the same family for scoring + judging is a known research pattern as long as the generator is cross-family (Mistral is). Document the choice in the design doc §5.

**Calibration gate.** Before declaring the grader trustworthy:

1. Hand-label all 25 pilot Q/A pairs (5 pages × 5 questions) against the primary scorer's answers. Store in `evaluation/phase5-results/pilot-001/_calibration/hand-labels.json`.
2. Run the LLM judge against the same 25 pairs.
3. Report agreement (accuracy, Cohen's κ). Gate: κ ≥ 0.8. If lower, revise the judge prompt and rerun. If still lower, escalate to a second judge model (Llama) and compare.
4. Only then rerun the pilot under `--grader llm` and commit the new accuracy numbers.

**Estimated effort:** 1 session including calibration.

### 2. Corpus-hygiene fixes

Both fail-to-skip reasons in pilot-001 are corpus-selection issues, not pipeline bugs. Fix before the N=60 run.

- **Wikipedia 403.** httpx default User-Agent is blocked. Switch the runner's `User-Agent` from `Clipper-Phase5-Pilot/0.1` to a realistic browser UA (match what `crawl.py` uses in the main pipeline for consistency). File: [retrievability/phase5/runner.py](../retrievability/phase5/runner.py) constant `USER_AGENT`.
- **Min-document-length guard.** The MDN 429 page extracted to 645 chars. That's too short to yield 5 non-clustered questions. Add a threshold — skip + log if `len(text) < 1500` after readability. Corpus build should flag these pages during selection, not discover them at runtime.
- **Regenerate the pilot list.** Current [urls/phase5-pilot-urls.txt](../urls/phase5-pilot-urls.txt) has a Wikipedia URL that doesn't fetch and an MDN URL that's too short. Replace with 5 pages that will actually exercise all downstream steps.

**Estimated effort:** 30 min.

### 3. Wire Clipper pillar scores into the analyzer

The math is already in [retrievability/phase5/analyzer.py](../retrievability/phase5/analyzer.py) (Spearman ρ + 10 000-resample bootstrap CI, pure Python). Not yet wired end-to-end.

- Add `phase5 analyze <pilot-dir>` subcommand.
- For each page in `pilot-summary.json`, read the corresponding `*_scores.json` produced by `python main.py express` against the same URL. Decision needed: **run express inline from the pilot runner**, or require it as a separate preceding step?
  - **Recommended:** inline. The pilot runner already fetches each URL; piggybacking a Clipper scoring pass keeps the corpus consistent and avoids URL-drift between the two runs. Adds ~8 s/page.
- Emit a per-pillar `correlations.json` + markdown table.

N=5 produces meaningless ρ values — but we need the plumbing working before N=60 so the full-run report is a one-command build.

**Estimated effort:** 1 session.

### 4. Secondary-reviewer κ infrastructure

Blocking dependency called out in the plan. Not needed for the pilot-grade grader calibration, but needed before any full-run publication.

- Reviewer B reviews a random 20% slice of accepted Q/A pairs.
- Compute Cohen's κ on accept/reject agreement.
- Report κ alongside per-pillar ρ in the findings table.
- Design spike only next session — actual reviewer B time slots later.

**Estimated effort:** 30 min of scaffolding, then a real person-hour when the N=60 corpus is ready.

### 5. Token and cost telemetry

The per-page `summary.json` already records tokens-in / tokens-out for the primary scorer. Missing: aggregate per run, and generator costs.

- Extend `pilot-summary.json` with totals across all pages broken out by model role (generator, scorer_primary, scorer_secondary, judge once (1) ships).
- Convert to approximate USD using the current Foundry pricing table (hard-code; revisit if pricing changes).
- This confirms the <$50 budget before the N=60 run is launched.

**Estimated effort:** 30 min.

## What to do first when next session starts

1. Read the summary at the top of this doc, skim the [stripe grades file](../evaluation/phase5-results/pilot-001/stripe-com-docs-api-charges-create/grades.primary.json) to re-ground.
2. Start on task (1). Build the `judge.py` module and prompt, run it against the 25 existing pilot pairs, spot-check the labels.
3. Hand-label the same 25 pairs on paper or in a scratch JSON; compute κ.
4. If κ ≥ 0.8, flip the default grader to `llm`, rerun pilot-001 with `--grader llm`, commit the new numbers.
5. Only then move to (2).

## What NOT to do next session

- Do not run the full N=60 corpus. Grader must pass calibration first.
- Do not touch the correlation analyzer until the grader is calibrated — running Spearman on bad grades would produce precisely the false-confident numbers the design doc's "honest null" framing is meant to prevent.
- Do not add new LLMs or new deployments. The three we have are sufficient for everything above.

## Open decisions to confirm

- **Judge-model choice.** GPT-4.1 (reuse) vs Llama 3.3 (different family from primary scorer). Default recommendation: GPT-4.1, with Llama as a disagreement-diagnostic if κ ≤ 0.8.
- **Single-judge vs two-judge-agreement.** Design doc currently assumes one judge. Two-judge-agreement is cleaner but doubles judge cost. Decide at calibration time based on the κ number.
- **Inline Clipper scoring in the pilot runner vs separate step.** See (3). Recommending inline.

## References

- Design doc: [docs/phase-5-design.md](./phase-5-design.md) §5 (grading methodology), §6 (correlation analysis), §10 (open questions).
- Improvement plan: [docs/improvement-plan.md](./improvement-plan.md).
- Pilot results to read back: [evaluation/phase5-results/pilot-001/pilot-summary.json](../evaluation/phase5-results/pilot-001/pilot-summary.json).
- Pilot runner: [retrievability/phase5/runner.py](../retrievability/phase5/runner.py).
- Current grader (to be replaced): [retrievability/phase5/grader.py](../retrievability/phase5/grader.py).
