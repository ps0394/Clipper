# 06 — What this data does NOT support

> **Key point.** Corpus-002 is one corpus, one grader architecture, one timepoint. The findings authorize specific structural decisions but do not authorize a long list of plausible-sounding adjacent claims. This document is the overclaim guard.

If a claim is on this list, it is **not** corpus-002 evidence. Some are plausible, some are likely true, some require Phase 6 / corpus-003 / Phase 7 work to settle. None should appear in a Clipper report or a vendor-facing analysis as "shown by corpus-002."

---

## Not supported by corpus-002

### Scoring

- **Precise pillar weight values.** The shipping v2 uses 0.50 / 0.50 deliberately, not because that is the optimum. A 0.67 / 0.33 split projects to higher r on this corpus but is overfit at n=43.
- **Profile-specific weight schemes.** Per-profile n is too small (FAQ n=3, sample n=2, landing n=4). Profile-weighted scoring is deferred to corpus-003.
- **"Permanent" demotion of the four diagnostic-only pillars.** They are demoted *until a corpus shows retrieval-relevance.* A future corpus could restore any of them.
- **Cross-vendor template-quality rankings.** Per-vendor 90% CIs overlap for almost every pair. See [03-judge-confidence-intervals.md](03-judge-confidence-intervals.md).

### Markdown / served-markdown

- **Retrieval-mode (RAG) format effects.** Track B measures in-context comprehension only. Chunked + embedded + retrieved differs structurally. Phase 7.
- **"Markdown is universally inferior to HTML extraction."** OpenAI's 0.34× ratio is real even at n=2. Universal claims in either direction are not authorized.
- **Universal "markdown is bloated" claim.** True on 8 of 9 corpus-002 vendors; one vendor refutes it. Generalize cautiously.
- **Pipeline-reliability lift from markdown.** Plausibly real (variance reduction across many runs). Not measured by single-run paired grading.
- **Chunking-fidelity lift from markdown.** Plausibly real. Not measured.

### Cross-agent / cross-corpus / cross-time

- **Cross-agent generalization.** Single grader architecture (GPT-4.1 scorer + Llama-3.3-70B judge). Other agent pipelines may produce different deltas.
- **Cross-corpus generalization.** Curated 43-page corpus across 14 vendors of developer documentation. Not a sample of "the web."
- **Non-English content.** Out of scope.
- **Non-developer-documentation content.** Out of scope.
- **Temporal stability.** One run, one timepoint. Re-running at T+30d is Session 5 work.
- **Standard-as-methodology publication.** Corpus-003 is the minimum bar.

### Cross-judge

- **"Validated cross-judge agreement" on corpus-002.** F3.2 has now landed (Addendum G): three judges (Llama-3.3-70B, GPT-4o, DeepSeek-V3.2) achieve substantial-to-almost-perfect pooled κ (0.706 / 0.761 / 0.817), but with a ~10-point severity gap. The cross-judge union 90% CI is [0.530, 0.758] — wider than the single-judge band by ~10 points on the low end. **The single-judge CIs published in §D.4 are now superseded for any external comparison; quote the union CI or the majority-vote CI [0.567, 0.688] instead.** What is *still* not authorized: a claim that any one of the three judges is the calibrated grader (re-adjudication against fresh human labels would be needed).

### Cross-vendor "competitive" framings

- **"Vendor X beats Vendor Y" without published intervals.** Methodology error.
- **"Learn's metadata pillar leads because of CMS template quality"** — to the extent it is supported at all, the supporting numbers must come from Phase 4.4-corrected scoring (commit `3c71ce2`, April 22 2026). Pre-fix Learn metadata scores included a 15-point `ms.topic` topic-field credit no other vendor could earn from a comparable internal signal; offline measurement on the v3 corpora showed 14 of 16 Learn pages lost that credit (mean metadata Δ −13.12), 0 of 6 competitor pages affected. Reports that cite Learn metadata numbers from before April 23 2026 must qualify the comparison.
- **"Agent-ready" / "needs improvement" bands** without stating which score (`parseability_score` vs `universal_score`) the band is applied to.
- **Vendor template fixes recommended from a single-run evaluation** without reporting variance or confidence.

---

## Specifically: things people will want to say but can't

### "Markdown helps agents"
- *True for naïve HTML ingestion.* See [05-token-efficiency.md](05-token-efficiency.md).
- *Not true for in-context comprehension on this corpus.* Track B null. See [04-served-markdown-experiment.md](04-served-markdown-experiment.md).
- *Not measured for retrieval-mode.* Phase 7.

### "Clipper's pillars measure agent retrievability"
- *Two pillars do, on this corpus* (`content_extractability`, `http_compliance`).
- *Four pillars do not, on this corpus* — they are diagnostic-only in v2.
- *Pillar performance on other corpora is not measured.*

### "Vendor X publishes high-quality documentation"
- Replace with a quantitative claim that includes:
  - Which score (`universal_score`, with the v2 weights, on this corpus).
  - Sample size and 90% CI.
  - The detected content-type profile and detection source for each page.
  - A comparison set with matched n and matched profiles.

### "v2 is more accurate than v1"
- More precisely: v2 correlates more strongly with measured agent retrieval accuracy on corpus-002 (r = +0.618 vs −0.0086).
- "More accurate" implies a single ground truth. Clipper measures alignment with one specific grader architecture's accuracy, on one corpus.

---

## How to use this list

When drafting a Clipper report:
1. **Write the claim.**
2. **Find the supporting corpus-002 finding.** If it is on this "not supported" list, weaken the claim or remove it.
3. **If the supporting finding is in this directory**, cite the topical doc and the source document.
4. **If the supporting evidence requires Phase 6 / corpus-003 / Phase 7**, label the claim as such or omit it.

The goal is not to be timid — it is to make every published claim survive a methodology audit.
