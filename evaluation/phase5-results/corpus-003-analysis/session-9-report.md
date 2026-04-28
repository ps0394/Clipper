# Session 9 — corpus-003 Regression & Stability

- pilot dir: `evaluation\phase5-results\corpus-003`
- pages with at least one judge accuracy: **171**
- gate threshold: r ≥ +0.35

## F2.6 / F3.5 — composite vs accuracy, per judge

| Judge | n | mean acc | mean v2 | r (v1 vs acc) | r (v2 vs acc) | gate |
|---|---:|---:|---:|---:|---:|:--:|
| Llama-3.3-70B | 171 | 0.952 | 72.63 | +0.1020 | +0.1020 | **FAIL** |
| GPT-4o | 171 | 0.904 | 72.63 | -0.0253 | -0.0253 | **FAIL** |
| DeepSeek-V3.2 | 171 | 0.917 | 72.63 | +0.0616 | +0.0616 | **FAIL** |

## A4 — Per-pillar correlation, cross-corpus

Per-pillar Pearson r (pillar score vs judged accuracy_rendered).
`Δ` = corpus-003 minus corpus-002. Flags: `*` = |Δ| > 0.20, `!` = sign flip.

| Pillar | corpus-002 | 003 / Llama-3.3-70B | Δ | 003 / GPT-4o | Δ | 003 / DeepSeek-V3.2 | Δ |
|---|---:|---:|---:|---:|---:|---:|---:|
| semantic_html | -0.3006 | -0.1153 | +0.1853 | -0.1006 | +0.2000 | -0.0755* | +0.2251 |
| content_extractability | +0.4839 | +0.0694* | -0.4145 | -0.0370* | -0.5209 | +0.0059* | -0.4780 |
| structured_data | +0.0359 | -0.0671 | -0.1030 | +0.0165 | -0.0194 | -0.1087 | -0.1446 |
| dom_navigability | -0.1889 | +0.0455* | +0.2344 | -0.0645 | +0.1244 | -0.0060 | +0.1829 |
| metadata_completeness | +0.2236 | -0.0168* | -0.2404 | +0.0249 | -0.1987 | -0.0525*! | -0.2761 |
| http_compliance | +0.2418 | +0.1018 | -0.1400 | +0.0185* | -0.2233 | +0.1416 | -0.1002 |

## Block A acceptance

- **A3 (3 of 3 judges clear gate):** FAIL
- **A3 minimum (2 of 3 judges clear gate):** FAIL
- **A4 flags (|Δ|>0.20 or sign flip):** 8

## Notes

- **Selection bias / range restriction (HEADLINE):** corpus-003 accuracy is bunched near the ceiling (Llama std 0.10, GPT-4o std 0.15, DeepSeek std 0.14) vs corpus-002 (std 0.25). The v2 composite spread is essentially unchanged (std ~7.4 vs 7.8). Pearson r against a near-constant target collapses mechanically — this is a **textbook range-restriction artifact, not evidence that v2 fails to generalize**. corpus-003 neither confirms nor refutes the v2 ship gate.
- **Dropped pages:** 99 of 271 pages had both raw and rendered extracts under MIN_DOCUMENT_CHARS and produced no Q/A pairs. Those are exactly the pages where v2 → accuracy correlation would be most informative (sparse content → bad answers); their exclusion is the primary driver of the ceiling effect.
- **Llama judge inversion:** mean Llama accuracy on the evaluable subset (0.952) is *higher* than GPT-4o (0.904) and DeepSeek (0.917) — a reversal from corpus-002. Three-way unanimous agreement is 91.6% (783/855 pairs). The earlier 'Llama vs frontier' framing was an artifact of mixing page-level (with fetch failures = 0%) and Q/A-level statistics. Judge fitness is not the issue.
- **A5 diagnosis pointer:** Block A cannot be closed as-passed under this corpus. The remediation is not v3 weight redesign; it is a harder generalization corpus that produces wider accuracy variance (weaker generator, sparser content, multi-hop synthesis, or all three).