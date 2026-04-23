# Phase 5 — Dual-Fetcher Corpus Plan (for review)

**Status:** Draft. Nothing in this plan is implemented yet. Written 2026-04-23 after the corpus probe revealed ~46% of candidate URLs return either 403s (OpenAI) or sub-1500-char `<noscript>` shells (Perplexity, Upsun, Snowflake landing, Stripe quickstart, etc.) under plain httpx fetching.

---

## 1. What happened and what it means

When we probed 65 candidate URLs spanning the vendors you named (OpenAI, Anthropic, Perplexity, Snowflake, Upsun) plus the existing baseline (Learn, MDN, AWS, GCP, Stripe, Python, Wikipedia), only **30 of 65 passed** the current pilot's 1500-char extraction floor. Failures broke into two clean categories:

1. **Bot blocking.** OpenAI's `platform.openai.com/docs/*` returns 403 to non-JS fetchers (Cloudflare bot-check). Wikipedia similarly 403s programmatic access. Not fixable with UA tweaks.
2. **Client-side rendered SPAs.** Upsun, Perplexity, most of Snowflake, Stripe's quickstart, and modern Mintlify/Nextra/Fumadocs-based docs return a 500KB–1MB JS bundle whose body is `<div id="__next"></div>`. The docs don't *exist* in the raw HTML; they are assembled by JavaScript at runtime.

This is not a pilot bug. **It is the finding Phase 5 is designed to surface.** A large fraction of the AI-infrastructure vendors selling "build AI agents with our API" publish their docs in a way that prevents AI agents (other than browser-using ones) from reading them. Dropping these vendors from the corpus because they are hard to fetch would sanitize away the single most consequential observation the phase can make.

---

## 2. What we'll do instead

We add a **second fetcher** to the Phase 5 pilot that uses a real browser (Playwright + Chromium). Every page is fetched twice — once with httpx (raw), once with Playwright (rendered) — and the full pipeline runs on each snapshot independently. The pilot now produces two accuracy numbers per page, and their delta becomes a first-class dependent variable.

### What this models

| Fetcher | Represents | Agent population |
|---|---|---|
| **httpx (raw)** | HTML-only retrieval | RAG crawlers, API-based agents, search indexers, LLM training scrapers |
| **Playwright (rendered)** | Post-JS-hydration DOM | Browser-using agents: ChatGPT web tool, Claude computer use, Perplexity's own crawler, human-in-the-loop workflows |

### Why this isn't scope creep

Clipper's scoring layer already has a `render_mode: 'raw' | 'rendered' | 'both'` dimension at the *pillar-evaluation* level (DOM-navigability pillar runs axe-core in a browser in rendered mode, falls back to static analysis in raw mode). What it lacks is the equivalent at the *fetch* level. Today a Clipper run will score a 58-char `<noscript>` shell as a legitimate page and report "content_extractability: 5" — the scoring is honest, the fetcher lies about the input. The dual-fetcher is the fetch-level counterpart to a dimension Clipper already expresses at the scoring level.

### Where the new code lives

**In Phase 5 only, not Clipper core.** New file `retrievability/phase5/fetcher.py`:

```python
def fetch_raw(url: str) -> tuple[str, dict]:  # httpx — moved from runner.py
def fetch_rendered(url: str) -> tuple[str, dict]:  # new, Playwright
```

Both return `(html, metadata)`. Metadata records fetcher type, status, timing, final URL after redirects, Playwright-specific fields (load-state reached, console errors) where relevant.

Clipper core (`retrievability/crawl.py`, `main.py express`) is **not modified** in this phase. If the raw-vs-rendered delta turns out to be a large, vendor-characteristic signal — which is the expected outcome — we promote the fetcher into Clipper core in a later phase. If the delta is small or noisy, pulling it into core would have been premature. Phase-5-only avoids that bet.

### Pipeline changes

Per URL, the runner does:

1. `fetch_raw(url)` → `page.raw.html`, `page.raw.txt` (readability), `fetch.raw.json` (metadata)
2. `fetch_rendered(url)` → `page.rendered.html`, `page.rendered.txt`, `fetch.rendered.json`
3. Skip the URL (with a recorded reason) only if **both** fetches fail or **both** extract below 1500 chars. If one succeeds and the other doesn't, that asymmetry is the data — record it, continue.
4. Run the existing generator (Mistral) on the *rendered* text. The rendered DOM is what the page "means." Questions derived from raw text would be biased toward pages that happen to server-render.
5. Score the LLM against both extractions: `scoring.raw.json`, `scoring.rendered.json`. Judge both. Produce `accuracy_raw`, `accuracy_rendered`, `accuracy_delta`.
6. Run Clipper's pillar scoring on each snapshot: `clipper-scores.raw.json`, `clipper-scores.rendered.json`. Clipper's own `render_mode` flag handles the DOM-navigability pillar correctly for each.
7. Per-page summary gains `accuracy_raw`, `accuracy_rendered`, `parseability_raw`, `parseability_rendered`, and their deltas.

### What Phase 5's headline result becomes

Instead of a single "LLM QA accuracy" number per page, we get a **2×2 matrix** per vendor:

| | Raw HTML | Rendered |
|---|---|---|
| Learn, MDN, AWS, Python, GCP | should be ~equal | should be ~equal |
| OpenAI, Anthropic, Perplexity, Upsun, Snowflake | expected low / N/A | expected normal |

A large raw→rendered accuracy lift for a vendor means: "Your docs require JavaScript execution to be readable. RAG systems, search indexes, and most LLM training corpora will see empty pages or broken fragments." That is a *specific, actionable, vendor-attributable* finding of the kind Clipper's mission statement exists to produce.

---

## 3. Cost and risk

**Plumbing cost:** ~1 hour of implementation.

- Install Playwright + Chromium into the venv (`pip install playwright; playwright install chromium`). Adds ~200 MB on disk.
- New `fetcher.py` module with the two functions and their metadata schemas.
- Runner changes: two fetches per URL, the matrix of downstream outputs, schema updates to `PilotPageSummary` and `pilot-summary.json`.
- Probe-script update: probe both raw and rendered, report both in the probe results so corpus culling sees both dimensions.
- One smoke test, one full pilot re-run.

**Runtime cost per page:** adds ~5–8 s of Playwright time (launch Chromium, navigate, wait for network-idle, dump DOM, close). Pilot goes from ~125 s/page to ~135 s/page. **N=60 pilot estimated wall-clock: ~2h15m → ~2h25m.** Not a meaningful change.

**Token cost:** *doubles* because we run the scorer on both raw and rendered text. At pilot-005 rates this was ~32k prompt tokens per page. At N=60 that's ~60×2×32k = 3.8M prompt tokens on GPT-4.1 plus ~60×2×32k on Llama judge. Order-of-magnitude ~$10 total across both models.

**Technical risks:**

1. *Playwright flakiness.* Some pages will still fail (aggressive bot-check, navigation timeouts). Mitigation: record the failure in `fetch.rendered.json` and keep going; the runner is already defensive. A page that fails in rendered mode but succeeds in raw mode is *still useful data*.
2. *SPA pages that need interaction.* Some docs sites require you to click a cookie banner, dismiss a "what's new" modal, or scroll to trigger lazy-loading. We do *not* attempt to handle these generically; a bounded `wait_for_load_state("networkidle")` plus a 5-second hard timeout will cover the majority. Pages that still fail get recorded and skipped. Don't over-engineer this for the pilot.
3. *"What about `llms.txt` / AI-specific endpoints?"* Out of scope for this phase. Some vendors (Anthropic, Stripe) ship canonical plain-text alternatives at known paths. Testing whether agents route to them *would* be a good Phase 6 question, but it's a different question from "how does raw HTML retrieval compare to rendered retrieval."

---

## 4. What's in the corpus

Target: **N=60, 10 URLs per profile × 6 profiles**, spread across vendors. I will **not** try to hit vendor quotas exactly — profile balance matters more for the statistics than vendor balance, and forcing vendor symmetry when some vendors have few pages in a given profile would make the corpus artificial.

Expected distribution after re-probing with both fetchers:

| Vendor | Expected count | Role |
|---|---|---|
| Learn | 5–6 | baseline: server-rendered, well-templated |
| Anthropic | 6–8 | strong signal: well-structured docs, mostly passes raw |
| Python | 4–5 | baseline: plain server-rendered reference and tutorial |
| MDN | 3–4 | baseline: server-rendered article / reference / tutorial |
| AWS, GCP, Stripe/API | 4–6 combined | mix of server-rendered reference and article |
| **OpenAI** | 4–6 | raw=N/A, rendered=normal — cloudflare + SPA |
| **Perplexity** | 3–5 | raw=N/A, rendered=normal — SPA |
| **Upsun** | 3–5 | raw=N/A, rendered=normal — SPA |
| **Snowflake** | 4–6 | mix: some server-rendered reference, SPA landing |
| Wikipedia | 0 | dropped: 403 even with Playwright's default UA on this host |
| Mintlify | 0–1 | edge: demo site, deprioritize |

This is a **draft**. The final distribution emerges from the re-probe, not a pre-assigned quota.

### URL assembly process

1. Expand candidate list from 65 → ~85 (add 3–5 more URLs per vendor where probing suggests page availability; this is cheap).
2. Re-probe with the dual-fetcher script. Output: `evaluation/phase5-corpus/probe-results.json` with `passed_raw`, `passed_rendered` flags per URL.
3. Human pass: you review the probe results, cull URLs that are clearly off-topic or duplicative, flag any where the profile hint is wrong.
4. Lock `urls/phase5-corpus-urls.txt` at 60 URLs. Commit.
5. Run the pilot. Commit results under `evaluation/phase5-results/corpus-001/`.

---

## 5. Open questions for you before I start

1. **Playwright vs. alternatives.** I'm recommending Playwright because it's the current best-in-class for browser automation in Python (2026), has async support, handles networkidle detection cleanly, and is a single dependency. Selenium is what Clipper already uses for axe — reusing it would avoid a second browser stack but Selenium's rendered-HTML capture is clunkier and historically flakier for SPAs. **I'd prefer Playwright.** Objections?

2. **Questions generated from rendered text only, or both?** My recommendation above is: generate questions from the *rendered* text (the page's actual content), and grade the scorer's answers against it when tested on each extraction. The alternative — generating two sets of questions, one per extraction — produces a harder-to-interpret result because differences in accuracy could be attributed to either retrieval or question choice. **Generate from rendered, grade both.**

3. **Corpus vendor balance.** I'm recommending "profile-balanced, vendor-asymmetric." If you'd rather enforce a rough vendor cap (e.g. no single vendor contributes more than 12 URLs = 20%) that's defensible but reduces usable URLs per profile. **Profile-balanced as-is.**

4. **Scope discipline.** I want to commit to *not* adding the following in Phase 5 even though they'll be tempting:
   - Vendor-specific extraction tweaks (e.g. "click the cookie banner on Perplexity")
   - Raw-vs-rendered-at-pillar-level hybrid scoring (we'd need to decide which raw pillars combine with which rendered pillars)
   - `llms.txt` / well-known agent-endpoint probing
   - Productionizing the rendered fetcher into Clipper core
   - Any UI / reporting beyond JSON outputs
   
   All of these are good ideas and none of them belong in this phase.

---

## 6. If you approve, next concrete steps

1. `pip install playwright`, `playwright install chromium`. Add to `requirements-phase5.txt`.
2. Write `retrievability/phase5/fetcher.py` with `fetch_raw` and `fetch_rendered`.
3. Update `runner.py`: two fetches per URL, matrix of outputs, schema updates. Extend `PilotPageSummary`.
4. Update `scripts/phase5-probe-urls.py`: probe both modes, report both.
5. Re-probe the candidate list. Commit probe results.
6. Draft `urls/phase5-corpus-urls.txt` (60 URLs). Wait for your review.
7. Run `phase5 pilot` against the locked corpus. Commit results.
8. Separately: write a short methodology note for the eventual writeup covering the dual-fetcher rationale and the raw-vs-rendered delta as a primary finding.

Total to reach step 7 (first N=60 run): **roughly half a day of implementation + ~2.5 h of pilot runtime + a corpus-review pause on you.**

---

## 7. What I want from you in the review

- Approve or reject each of the four open questions in §5.
- Flag anything in the scope-discipline list (§5.4) you'd actually want to include.
- Sanity-check the expected vendor distribution in §4. If there's a vendor you particularly want over-represented for the writeup ("I want Upsun to be comparable to Learn's count because the framing is 'CMS quality matters more than vendor'"), say so now.
- Confirm budget tolerance (~$10 token spend, ~2.5 h runtime, ~½ day implementation).
