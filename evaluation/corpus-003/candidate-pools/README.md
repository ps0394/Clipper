# corpus-003 Candidate Pools

One file per vendor. Each line is either:

- A URL (sampler classifies it via URL-path heuristics matching `retrievability/profiles.py`)
- A URL followed by a TAB and a profile override (one of: `article`, `landing`, `reference`, `sample`, `faq`, `tutorial`)
- A `#`-prefixed comment
- A blank line

**These pools are the pre-registration artifact for corpus-003.** Once committed and the sampler has been run, no edits without a documented amendment per [spec.md](../spec.md) §4.

Pools are hand-curated from public vendor documentation indexes. The *sampling* within each pool is deterministic (`seed = 20260427`); see [scripts/phase7-corpus003-sample.py](../../../scripts/phase7-corpus003-sample.py).
