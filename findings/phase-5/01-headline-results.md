# 01 — Headline results

> **Key point.** Clipper's v1 composite score did not predict agent retrieval accuracy on corpus-002. Pearson r ≈ 0 at n=43. Individual pillars carry signal; the v1 weights combined them in a way that cancels out.

## The ceiling broke (and that mattered)

Corpus-001 hit a 0.949 mean rendered accuracy — too high a ceiling to discriminate documentation quality. Corpus-002 used a harder-Q/A generator prompt requiring synthesis, quantitative reasoning, and constraint/edge-case questions. The result was a usable distribution.

| Metric | Corpus-001 | Corpus-002 | Change |
|---|---:|---:|---:|
| Rendered accuracy (mean) | 0.949 | 0.698 | −0.251 |
| Raw accuracy (mean) | 0.938 | 0.739 | −0.199 |
| Variance across pages | very compressed | broad — 0.0 to 1.0 | dramatically expanded |

The ~0.70 rendered accuracy is a defensible measurement of synthesis-task retrievability on curated documentation. **Without the harder-Q/A prompt, the headline finding below could not have been discovered** — the v1 composite would have correlated with the ceiling, not with retrieval.

## The headline negative finding

| Score | n | Pearson r vs accuracy |
|---|---:|---:|
| `parseability_score_raw` vs `accuracy_raw` | 36 | +0.089 |
| `parseability_score_rendered` vs `accuracy_rendered` | 43 | **−0.009** |
| `universal_score_raw` vs `accuracy_raw` | 36 | +0.095 |
| `universal_score_rendered` vs `accuracy_rendered` | 43 | **−0.007** |

Both `parseability_score` (profile-weighted) and `universal_score` (article-weighted) carry essentially zero linear predictive signal. The v1 composite is uncorrelated with the outcome it claims to measure.

## Pillar-level correlations explain why

Correlations against `accuracy_rendered` (n=43):

| Pillar | Pearson r | Mean pillar score | Current weight (article) |
|---|---:|---:|---:|
| `content_extractability` | **+0.484** | 74.2 | 20% |
| `http_compliance` | +0.242 | 71.2 | 10% |
| `metadata_completeness` | +0.224 | 57.4 | 10% |
| `structured_data` | +0.036 | 31.2 | 20% |
| `dom_navigability` | −0.189 | 36.3 | 15% |
| `semantic_html` | **−0.301** | 63.3 | 25% |

**Three pillars carry positive signal. Two carry negative signal. One carries no signal.** The v1 weight scheme spends 25% on the worst-correlating pillar (`semantic_html`) and 20% on the no-signal pillar (`structured_data`). When you weight a positive signal at 20% and an equal-magnitude negative signal at 25%, you get a composite that looks well-engineered and predicts nothing.

### What each correlation means

- **`content_extractability` (+0.484)** — measures whether Readability extracts a coherent body from the DOM. The single dominant signal. Pages that defeat this step score near zero on retrieval regardless of any other pillar.
- **`semantic_html` (−0.301)** — heavily-templated sites (Stripe API reference, GitHub REST reference) are simultaneously *high* on semantic markup and *low* on extractability. Semantic structure does not equal agent-readable structure.
- **`structured_data` (+0.036)** — schema.org / JSON-LD presence on corpus-002 does not predict retrieval accuracy. Not "negative", not "weak positive": noise.
- **`dom_navigability` (−0.189)** — axe-core WCAG proxy. Same templating mechanism as `semantic_html`.
- **`http_compliance` (+0.242)** and **`metadata_completeness` (+0.224)** — directionally positive, below p<0.05 at n=43.

## Per-profile observations (deferred for weighting)

| Profile | n | Mean accuracy (rendered) |
|---|---:|---:|
| FAQ | 3 | 0.933 |
| article | 12 | 0.733 |
| sample | 2 | 0.700 |
| reference | 12 | 0.683 |
| landing | 4 | 0.650 |
| tutorial | 10 | 0.620 |

Content-type matters, but n is too small per profile for weight-fitting. Profile-specific weights are deferred to corpus-003.

## Per-vendor outliers worth naming

- **Stripe API** (`docs-stripe-com-api-charges`): `accuracy_rendered = 0.0`, `content_extractability = 41.6`. Interactive shell defeats Readability.
- **GitHub REST** (`docs-github-com-en-rest-repos-repos`): `accuracy_rendered = 0.0`, `content_extractability = 40.9`. Same failure mode on auto-generated API-reference DOM.
- **Wikipedia LLM article**: `accuracy_rendered = 0.3` despite a reasonable composite. Substantial non-body chrome the grader picked up as distractors.
- **AWS**: highest vendor rendered accuracy at 1.000 (n=2). Small sample but the only 100% under harder-Q/A.

## Implications (carried forward to other docs)

- **The composite needs a structural change, not a re-weight.** See [02-v2-scoring-decision.md](02-v2-scoring-decision.md) for how that decision was made.
- **Per-vendor differences need confidence intervals before they are publishable.** See [03-judge-confidence-intervals.md](03-judge-confidence-intervals.md) for the rule.
- **Extraction failures are not random.** Pages that fail `content_extractability` are systematically the API-reference / interactive-template pages that served-markdown was invented to rescue. See [04-served-markdown-experiment.md](04-served-markdown-experiment.md) for what the served-markdown test actually measures.
