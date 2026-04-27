# corpus-003 Specification

**Status:** Pre-registered, April 27, 2026
**Author:** Phase 6 Session 7 (F6.1)
**Roadmap reference:** [findings/post-v2-roadmap.md](../../findings/post-v2-roadmap.md) §5 Session 7 / Block A

This document specifies the methodology for corpus-003 **before** any URLs are fetched. The selection rule, vendor list, profile balance, and challenged-fetch inclusion are committed here as a methodology lock. Any post-hoc deviation invalidates the generalization claim and must be re-run.

---

## 1. Purpose

corpus-003 is the generalization-test corpus for the Clipper v2 scoring model. It exists to answer a single question:

> **Does the v2 composite-vs-accuracy correlation (r = +0.618 on corpus-002) survive on a fresh, methodologically pre-registered URL set?**

If yes, v2 sheds the `-evidence-partial` suffix and ships as `v2`. If no, v2 was selection-biased and a redesign sub-session opens before any v3 work begins.

corpus-003 also pre-positions evidence for two open v3 questions:

- **Fetch Integrity as a candidate pillar** — by deliberately including 20 challenged-fetch pages.
- **Per-profile weight reactivation** — by sizing per-profile cells (n ≈ 40) large enough to defend per-profile correlation analysis.

---

## 2. Composition (locked)

### 2.1 Size

**n = 250 pages** = 10 vendors × ~25 pages per vendor.

Rationale: 125 was too thin per-cell; 600 was 5× the cost for marginal returns. 250 produces per-vendor cells of ~25 (real CIs, separable from corpus-002), per-profile cells of ~40 (above the n=30 threshold for stable per-profile r), at ~2× corpus-002's grading cost.

### 2.2 Vendors

**10 vendors, 3 anchors + 7 fresh:**

| Vendor | Status | Pages target | Why |
|---|---|---|---|
| `python` | anchor (corpus-002) | 25 | Cross-corpus stability check; corpus-002 had 5 pages |
| `learn` (Microsoft) | anchor (corpus-002) | 25 | Cross-corpus stability check; corpus-002 had 4 pages; tests Phase 4.4 ms.topic neutrality on a fresh page set |
| `aws` | anchor (corpus-002) | 25 | Cross-corpus stability check; corpus-002 had 2 pages |
| `cloudflare` | fresh | 25 | Doc platform with aggressive bot-challenge; sources Fetch Integrity stress |
| `mongodb` | fresh | 25 | Independent SaaS; no GCP/AWS overlap |
| `terraform` (HashiCorp) | fresh | 25 | Sample-heavy; distinct ops domain from k8s |
| `huggingface` | fresh | 25 | ML docs; distinct from openai/anthropic |
| `databricks` | fresh | 25 | Heavy SPA; stresses Tier-2 rendering |
| `vercel` | fresh | 25 | Modern Next.js-rendered docs |
| `clickhouse` | fresh | 25 | Open-source DB docs; contrast against snowflake |

The 3 anchor vendors enable **per-vendor cross-corpus stability checks** in Block A's Session 9 analysis. The 7 fresh vendors carry the generalization claim.

Vendors not in this list — including all corpus-002 vendors except the three anchors — are **deliberately excluded**.

### 2.3 Profiles

Same 6 profiles as corpus-002 / v2: `article`, `landing`, `reference`, `sample`, `faq`, `tutorial`.

Per-profile target distribution:

| Profile | Floor | Target | Cap |
|---|---|---|---|
| article | 5 | 50 | — |
| reference | 5 | 60 | — |
| tutorial | 5 | 50 | — |
| landing | 5 | 30 | — |
| sample | 5 | 30 | — |
| faq | 5 | 30 | — |

Total target: 250 pages. Floors enforced per **(vendor × profile)** cell to prevent any vendor from concentrating in a single profile. Cells with no available pages may fall below floor — recorded as a deviation in the post-fetch report.

### 2.4 Challenged-fetch stratum

**20 pages (8% of corpus)** marked with the `#challenged` tag in `urls.txt`. These pages are counted toward their normal vendor/profile cell — they're not a separate stratum, they're a deliberate stress test inside the regular corpus.

| Sub-stratum | Pages | Definition |
|---|---|---|
| Cloudflare-challenged | 8 | Page renders behind Cloudflare's bot-challenge layer (`__cf_chl_*` cookies, JS challenge, or 403 to non-browser UAs) |
| robots-blocked | 6 | `robots.txt` `Disallow:` matches the page path; page is publicly visible and not behind auth |
| UA-allowlist-variant | 6 | Page returns materially different content (> 20% byte diff) for known agent UAs vs Chrome |

Sub-stratum balance allowed to skew (e.g., if cloudflare's own docs aggressively challenge, that vendor naturally over-contributes to the cloudflare-challenged sub-stratum — recorded but not corrected).

---

## 3. Selection Rule (deterministic)

For each (vendor, profile) cell, pages are selected by this rule:

1. **Candidate pool:** for each vendor, a hand-curated pool of 60-100 candidate URLs is committed in `scripts/phase7-corpus003-sample.py` under the `VENDOR_POOLS` constant. Pools are drawn from each vendor's published documentation index pages, manually compiled from public navigation. **The pool itself is the pre-registration artifact** — committing it before sampling locks the universe of candidates.
2. **Profile classifier:** each candidate URL is classified into a profile via the same URL-path heuristics the live classifier uses ([retrievability/profiles.py](../../retrievability/profiles.py) `URL_HEURISTICS`), with one extension: URLs whose path doesn't match any heuristic are classified `article` (matching the classifier's default), but a `pool_hint` field per pool entry can override (e.g., a known landing page that doesn't have `/overview` in the path).
3. **Stratified random sample** with `seed = 20260427` (today's date, locked here). For each vendor, sample 25 URLs targeting the profile distribution in §2.3, with a per-(vendor × profile) cell floor of 5 where the candidate pool supports it.
4. **Replacement:** none required at sampling time — the candidate pool is the canonical universe. Quality gates (HTTP 200, content-type `text/html`, ≥ 200 words after Readability extraction) are deferred to fetch time in Session 8. URLs that fail those gates at fetch time are **dropped, not replaced**, and the corpus shrinks accordingly. Recorded as deviations.
5. **Challenged-fetch URLs:** the 20 challenged-fetch URLs are *not* sampled — they're explicitly listed in the sampler script under `CHALLENGED_URLS` and added to the output deterministically. Each challenged URL is tagged with its sub-stratum (`cf_challenge` / `robots_blocked` / `ua_variant`).

Tooling: `scripts/phase7-corpus003-sample.py` (this session) implements the rule. The script is fully deterministic: re-running with no input changes produces a byte-identical `urls.txt` (acceptance gate G6).

**Why hand-curated pools instead of sitemap.xml:** sitemap availability and format vary by vendor (gzipped, indexed, paginated, missing entirely for some sites), and dependency on live sitemap fetches at sampling time would make the corpus selection step non-reproducible across machines and time. A committed candidate pool sidesteps that, at the explicit cost of acknowledging the pool itself is curated. The curation is documented in the script and reviewable. The *sampling* within the pool is deterministic.

---

## 4. Pre-registration

The following are committed and pushed to `paulsanders/fix-ci-workflows` **before any page is fetched**, by commit timestamp:

- This document (`evaluation/corpus-003/spec.md`)
- Sampler script (`scripts/phase7-corpus003-sample.py`)
- URL list (`evaluation/corpus-003/urls.txt`) — produced by running the sampler

The commit hash is the methodology lock. Any subsequent change to vendor list, profile balance, challenged-fetch inclusion, seed, or selection rule requires:

1. Documenting the change as a *named amendment* in this file (e.g., "Amendment A1, 2026-05-XX: replaced `clickhouse` with `duckdb` because clickhouse sitemap unreachable").
2. Re-running the sampler with the amendment applied.
3. Re-committing both spec and url list before fetching.

Amendments after fetching has begun invalidate any generalization claim; corpus-003 would have to be re-run from scratch.

---

## 5. Acceptance Criteria for the corpus

Before corpus-003 enters Block A scoring (Session 8), the URL list must pass these gates:

- [ ] **G1 — Vendor coverage.** All 10 vendors listed in §2.2 are represented.
- [ ] **G2 — Per-cell floor.** Every (vendor × profile) cell with available source pages has ≥ 5 entries.
- [ ] **G3 — Challenged-fetch count.** Exactly 20 pages tagged `#challenged`, distributed across the 3 sub-strata per §2.4.
- [ ] **G4 — Total size.** 230 ≤ n ≤ 290. (Wider than the 250 nominal because floor is sacred — see §2.3: floor allocation may push some vendor totals slightly above 25.)
- [ ] **G5 — No corpus-002 URL overlap.** Zero URLs from `evaluation/phase5-results/corpus-002/` appear in `corpus-003/urls.txt` (even for anchor vendors — anchor vendors keep their vendor identity but use *different pages*).
- [ ] **G6 — Reproducibility.** Re-running the sampler with the same seed produces a byte-identical `urls.txt`.

If any gate fails, fix the sampler or amend §2 before fetching. Don't paper over mismatches.

---

## 6. What corpus-003 does NOT do

- **Not a temporal replication of corpus-002.** That's Block B's optional T+30d work.
- **Not a retrieval-mode benchmark.** That's Block C / Phase 7. corpus-003 is graded in comprehension mode like corpus-002, so the v2 model can be re-tested apples-to-apples.
- **Not a multi-agent benchmark.** Single Llama-3.3-70B primary judge, with one cross-judge pass (GPT-4o) for Block A acceptance. DeepSeek-V3.2 is deferred unless the 2-judge pass produces a problematic split.
- **Not a vendor scorecard.** Per-vendor cells are diagnostic; the generalization claim is at the corpus level.
- **Not Markdown-format-validated.** Tri-fetcher will record served-markdown availability per page as diagnostic-only (same v2 treatment), but corpus-003 does not re-run F4.2 / F4.3 paired grading — that question is parked at `keep_as_diagnostic_only` until Phase 7.

---

## 7. Sequencing

| Step | Owner | Output | Status |
|---|---|---|---|
| 1. Spec doc (this file) | Session 7 | `evaluation/corpus-003/spec.md` | in progress |
| 2. Sampler script | Session 7 | `scripts/phase7-corpus003-sample.py` | pending |
| 3. Sampler run → URL list | Session 7 | `evaluation/corpus-003/urls.txt` | pending |
| 4. Acceptance gates G1-G6 | Session 7 | committed in this file | pending |
| 5. Methodology-lock commit | Session 7 | git push, hash recorded | pending |
| 6. Fetch + score corpus-003 | Session 8 | `evaluation/phase5-results/corpus-003/` | not started |
| 7. Cross-judge regrade | Session 8 | per-page `grades.<judge>.judged.rendered.json` | not started |
| 8. Block A regression analysis | Session 9 | `evaluation/phase5-results/corpus-003-analysis/` | not started |

Steps 1-5 are done before any pages are fetched. Steps 6-8 are downstream sessions and gated on the steps before them.

---

## 8. Cross-references

- Roadmap: [findings/post-v2-roadmap.md](../../findings/post-v2-roadmap.md)
- v2 calibration corpus: [evaluation/phase5-results/corpus-002/](../phase5-results/corpus-002/)
- v2 calibration evidence: [findings/phase-5-corpus-002-findings.md](../../findings/phase-5-corpus-002-findings.md)
- v2 cross-judge evidence: Addendum G of the same
- Classifier (profile detection): [retrievability/profiles.py](../../retrievability/profiles.py)
- Standards-based scorer: [retrievability/access_gate_evaluator.py](../../retrievability/access_gate_evaluator.py)
