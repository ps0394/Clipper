# Phase 5 Resume Prompt

Paste this into a new Copilot chat to resume.

---

Resume Phase 5 dual-fetcher pilot. Read `/memories/session/phase5-state.md` first for full context.

## Where we left off

The N=43 pilot run in `evaluation/phase5-results/corpus-001/` is **in flight** (or finished, depending on when this is read). As of the last status check, ~22/43 pages had completed, all cleanly, with no outstanding crashes. All fixes from earlier crashes are **committed and pushed** on `paulsanders/fix-ci-workflows`.

**Crash history (all fixed):**

| Crash | Cause | Fix |
|---|---|---|
| Page 11 (1st run) | `'list' object has no attribute 'strip'` in grader | Two causes were conflated. |
| Page 11 (2nd run) | Same error, same page | `retrievability/phase5/schemas.py` — `QAPair.from_dict` now coerces non-string `question`/`answer`/`supporting_sentences`. Mistral Large 3 emits list-shaped answers for multi-step questions (e.g. `["step 1","step 2",...]`); lists are now joined with `"; "`. Commit `dbdab57`. |
| Page 19 (3rd run) | `json.JSONDecodeError: Extra data: line 73 column 1` | `retrievability/phase5/generator.py` — `parse_generator_output` now walks every ```` ```json ... ``` ```` fence and returns the **last** valid JSON array. Mistral occasionally emits a first attempt, then a "Correction: to ensure exactly N pairs" paragraph, then a corrected array. Commit `91d5cb0`. |

Also previously fixed (earlier in the session):
- `retrievability/phase5/clients.py` — `_coerce_content_to_text()` defensively coerces Azure AI Inference `message.content` (handles str / list-of-dicts / list-of-SDK-objs). Commit `bddc9d2`.
- `retrievability/phase5/runner.py` — resume-from-cache at the top of the per-page loop. If `<page_dir>/summary.json` exists, load via `PilotPageSummary(**cached)` and skip. Commit `bddc9d2`.
- `retrievability/cli.py` — top-level exception handler prints a traceback (was silent before, which made the page-11 crash hard to diagnose the second time). Commit `dbdab57`.

## Do next

### If the pilot is still running

1. Check progress:
   ```powershell
   (Get-ChildItem evaluation/phase5-results/corpus-001 -Directory | Where-Object { Test-Path (Join-Path $_.FullName "summary.json") }).Count
   ```
2. If a new crash has occurred, read the traceback from the run log (`evaluation/phase5-results/corpus-001-run*.log`), fix, commit, re-launch. Resume-from-cache means zero token waste on restart.

### If the pilot has finished

1. Run the analysis script:
   ```powershell
   python scripts/phase5-analyze.py
   ```
   Writes `evaluation/phase5-results/corpus-001-analysis/{analysis.md, per-page.csv, stats.json}`. Defaults read from `corpus-001/` and `urls/phase5-corpus-urls.txt`.
2. Read `analysis.md`. Pay attention to:
   - Tier-1 vs tier-2 mean accuracy for both raw and rendered modes — the headline finding.
   - Pearson r of `parseability_score` and each pillar vs measured accuracy — the validity check for Clipper's methodology.
   - Fetch-status counts per mode — confirms the runner did what it should.
   - Ceiling effect: if rendered accuracy is ~0.95+ across the board, correlation will be noisy. Note it and proceed.
3. Write the methodology note at `docs/phase-5-methodology.md`:
   - Dual-fetcher rationale (what raw-vs-rendered is actually measuring).
   - Three-tier framing from the 86-URL probe (`evaluation/phase5-corpus/probe-results.json`): tier-1 (44) raw passes, tier-2 (12) rendered-only, tier-3 (30) blocked even with Playwright — mostly OpenAI / Upsun / Mintlify. Include the tier-3 finding explicitly; agents cannot retrieve these pages.
   - Grader choice (LLM judge, κ=0.773 at N=20).
   - Q/A generation from rendered text only; scoring against both extractions (delta is the finding).
   - Known caveats: ceiling effect at N=43 with easy factual Q/A; primary scorer is the model under test while judge + secondary scorer are a different model family (Llama) so judge-scorer contamination is bounded but not zero.
4. Optionally: run a second pilot with harder / more synthesis-style Q/A to break the accuracy ceiling. Not required for the first writeup — the tier-2 and tier-3 findings stand regardless.

### Survive-logoff option (if needed)

```powershell
Start-Process powershell -ArgumentList '-NoProfile','-Command','python main.py phase5 pilot urls/phase5-corpus-urls.txt --out evaluation/phase5-results/corpus-001 --secondary-scorer *> evaluation/phase5-results/corpus-001-detached.log' -WindowStyle Hidden
```

Confirm with user first — detaches from VS Code terminal visibility.

## Do not re-litigate these approved decisions

- κ=0.773 calibration accepted at N=20.
- LLM judge is the default grader.
- Q/A generated from rendered text only.
- LLM scored against both raw and rendered extractions; delta is the finding.
- Profile-balanced corpus at N=43 (option 2, 36 tier-1 + 7 tier-2).

## Files to keep in mind

**Phase 5 code:**
- `retrievability/phase5/fetcher.py` — dual-fetcher (httpx + Playwright).
- `retrievability/phase5/runner.py` — pilot runner, dual-fetch + dual-score + resume-from-cache.
- `retrievability/phase5/clients.py` — Foundry generator + scoring + judge clients, with `_coerce_content_to_text()` defense.
- `retrievability/phase5/generator.py` — Q/A generator, with multi-block fence parsing.
- `retrievability/phase5/schemas.py` — `QAPair`, `ReviewRecord`, with list-coercion defense.
- `retrievability/phase5/grader.py` — LLM judge + legacy substring grader.

**Inputs:**
- `urls/phase5-corpus-urls.txt` — N=43 corpus (locked; 36:7 tier split).
- `evaluation/phase5-corpus/probe-results.json` — 86-URL probe evidence for tier classification.

**Analysis + docs:**
- `scripts/phase5-analyze.py` — post-run analysis (reads per-page `summary.json` + corpus file).
- `docs/phase-5-dual-fetcher-plan.md` — approved plan.
- `evaluation/phase5-results/corpus-001/` — run directory.
- `evaluation/phase5-results/corpus-001-analysis/` — analysis output (after running the analyze script).
