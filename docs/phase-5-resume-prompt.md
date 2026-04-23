# Phase 5 Resume Prompt

Paste this into a new Copilot chat to resume.

---

Resume Phase 5 dual-fetcher pilot. Read `/memories/session/phase5-state.md` first for full context.

**Where we left off:** The N=43 pilot run (`evaluation/phase5-results/corpus-001/`) crashed on page 11 with `'list' object has no attribute 'strip'`. First 10 pages completed successfully. Fixes are staged but UNCOMMITTED:

1. `retrievability/phase5/clients.py` — added `_coerce_content_to_text()` helper, applied at both `FoundryGeneratorClient.generate()` and `FoundryScoringClient.answer()` return sites. Handles the case where `response.choices[0].message.content` comes back as a list of content-part dicts/objects instead of a plain string.

2. `retrievability/phase5/runner.py` — added resume-from-cache logic at the top of the per-page loop. If `<page_dir>/summary.json` already exists, load the cached `PilotPageSummary` and skip the page. Lets us restart the crashed run without re-burning tokens or re-fetching.

**Do next:**

1. Verify both files look correct:
   - `retrievability/phase5/clients.py` — check `_coerce_content_to_text` handles str, list-of-dicts, list-of-SDK-objects, and falls back to `str()` for unknowns
   - `retrievability/phase5/runner.py` — check the resume block is at the top of the per-page loop body, before the fetch block, and uses `PilotPageSummary(**cached)` constructor
2. Count completed pages:
   ```powershell
   (Get-ChildItem evaluation/phase5-results/corpus-001 -Directory | Where-Object { Test-Path (Join-Path $_.FullName "summary.json") }).Count
   ```
   Expected: 10. If different, investigate before resuming.
3. Run a quick sanity test of the content-coercion helper (import it, call with a string, with `[{"type":"text","text":"hi"}]`, with a list of mock objects that have `.text` attr) — takes 30 seconds and prevents another mid-run crash.
4. Commit the two fixes:
   ```
   git add retrievability/phase5/clients.py retrievability/phase5/runner.py
   git commit -m "Phase 5: tolerate list-shaped message.content + resume-from-cache in runner"
   git push origin paulsanders/fix-ci-workflows
   ```
5. Resume the pilot:
   ```powershell
   python main.py phase5 pilot urls/phase5-corpus-urls.txt --out evaluation/phase5-results/corpus-001 --secondary-scorer 2>&1 | Tee-Object -FilePath evaluation/phase5-results/corpus-001-resumed.log
   ```
   Expected: runner prints `[RESUME — cached summary]` for pages 1-10, then runs pages 11-43 (~1h20m). If user wants it to survive logoff, re-launch as detached (see options below).

**Option for survive-logoff:**
Wrap the command in `Start-Process powershell -ArgumentList '-NoProfile','-Command','python main.py phase5 pilot urls/phase5-corpus-urls.txt --out evaluation/phase5-results/corpus-001 --secondary-scorer *> evaluation/phase5-results/corpus-001-resumed.log' -WindowStyle Hidden` — but confirm with the user before doing this since it detaches the process from your terminal visibility too.

**After corpus-001 completes:**
- Analyze the raw-vs-rendered accuracy delta across all 43 pages, split by tier (1 vs 2) and profile
- Expected headline finding: tier-2 pages show large negative `accuracy_raw - accuracy_rendered` delta (agent sees nothing useful in raw mode on JS-required sites)
- Produce the methodology note (not yet written) covering dual-fetcher rationale + the tier-3 "actively blocked" finding (30/86 candidates blocked even with Playwright, mostly OpenAI/Upsun/Mintlify)

**Do not re-litigate these approved decisions:**
- κ=0.773 calibration accepted at N=20
- LLM judge is the default grader
- Generate Q/A from rendered text only
- Score the LLM against both raw and rendered extractions (the delta is the finding)
- Profile-balanced corpus at N=43 (option 1+2 hybrid), tier-1:tier-2 = 36:7

**Files to keep in mind:**
- `retrievability/phase5/fetcher.py` — dual-fetcher module
- `retrievability/phase5/runner.py` — needs inspection for resume logic
- `retrievability/phase5/clients.py` — needs inspection for content-coercion helper
- `urls/phase5-corpus-urls.txt` — N=43 corpus (locked)
- `evaluation/phase5-corpus/probe-results.json` — 86-URL probe evidence
- `docs/phase-5-dual-fetcher-plan.md` — approved plan
- `evaluation/phase5-results/corpus-001/` — in-flight run directory
