# Phase 5 pilot analysis — N=43

## Headline: raw vs rendered accuracy

| Metric | Raw | Rendered | Delta |
|---|---|---|---|
| Mean accuracy | 0.739 | 0.698 | -0.022 |
| Mean parseability_score | 52.9 | 54.6 | — |
| Mean universal_score | 53.7 | 55.2 | — |

## By tier

| tier | n | acc raw | acc rend | delta | parse raw | parse rend |
|---|---|---|---|---|---|---|
| tier1 | 36 | 0.739 | 0.717 | -0.022 | 52.9 | 53.9 |
| tier2 | 7 | — | 0.600 | — | — | 58.1 |

## By profile

| profile | n | acc raw | acc rend | delta | parse raw | parse rend |
|---|---|---|---|---|---|---|
| article | 12 | 0.800 | 0.733 | 0.000 | 50.9 | 52.6 |
| faq | 3 | 1.000 | 0.933 | -0.067 | 56.7 | 57.0 |
| landing | 4 | 0.600 | 0.650 | 0.000 | 51.3 | 55.6 |
| reference | 12 | 0.683 | 0.683 | -0.000 | 51.5 | 53.2 |
| sample | 2 | 0.800 | 0.700 | 0.000 | 44.9 | 58.2 |
| tutorial | 10 | 0.700 | 0.620 | -0.075 | 57.5 | 56.8 |

## By vendor

| vendor | n | acc raw | acc rend | delta | parse raw | parse rend |
|---|---|---|---|---|---|---|
| anthropic | 5 | 0.760 | 0.720 | -0.040 | 44.5 | 44.9 |
| aws | 2 | 0.900 | 1.000 | 0.100 | 62.4 | 62.4 |
| docker | 3 | 0.700 | 0.733 | 0.000 | 65.9 | 67.6 |
| gcp | 1 | — | 0.600 | — | — | 71.6 |
| github | 4 | 0.450 | 0.450 | 0.000 | 54.5 | 54.5 |
| k8s | 2 | 0.800 | 0.800 | 0.000 | 69.8 | 69.8 |
| learn | 4 | 0.900 | 0.800 | -0.100 | 64.1 | 72.6 |
| mdn | 2 | 0.700 | 0.700 | 0.000 | 58.7 | 56.6 |
| nodejs | 2 | 0.700 | 0.700 | 0.000 | 52.6 | 52.6 |
| openai | 2 | — | 0.700 | — | — | 52.8 |
| perplexity | 2 | 0.800 | 0.800 | 0.000 | 44.3 | 44.3 |
| postgres | 1 | 1.000 | 1.000 | 0.000 | 38.6 | 38.6 |
| python | 5 | 0.880 | 0.800 | -0.080 | 48.1 | 48.1 |
| snowflake | 3 | 0.733 | 0.733 | 0.000 | 44.0 | 44.1 |
| stripe | 3 | 0.300 | 0.467 | 0.000 | 44.6 | 42.9 |
| wikipedia | 2 | — | 0.300 | — | — | 61.3 |

## Fetch outcomes

| Mode | Statuses |
|---|---|
| raw | ok: 36, failed: 4, short: 3 |
| rendered | ok: 43 |

## Correlation: Clipper score vs measured accuracy

| Score field | Accuracy field | n | Pearson r | mean score | mean accuracy |
|---|---|---|---|---|---|
| parseability_score_raw | accuracy_raw | 36 | 0.089 | 52.9 | 0.739 |
| parseability_score_rendered | accuracy_rendered | 43 | -0.009 | 54.6 | 0.698 |
| universal_score_raw | accuracy_raw | 36 | 0.095 | 53.7 | 0.739 |
| universal_score_rendered | accuracy_rendered | 43 | -0.007 | 55.2 | 0.698 |

## Per-pillar correlation with rendered accuracy

| Pillar | n | Pearson r | mean pillar score |
|---|---|---|---|
| semantic_html | 43 | -0.301 | 63.3 |
| content_extractability | 43 | 0.484 | 74.2 |
| structured_data | 43 | 0.036 | 31.2 |
| dom_navigability | 43 | -0.189 | 36.3 |
| metadata_completeness | 43 | 0.224 | 57.4 |
| http_compliance | 43 | 0.242 | 71.2 |

## Per-page detail

| slug | tier | profile | vendor | acc raw | acc rend | parse raw | parse rend | raw fetch | rend fetch |
|---|---|---|---|---|---|---|---|---|---|
| developer-mozilla-org-en-US-docs-Web-HTTP-CORS | tier1 | article | mdn | 0.800 | 0.800 | 59.4 | 55.3 | ok | ok |
| docs-anthropic-com-en-docs-build-with-claude-promp | tier1 | article | anthropic | 1.000 | 1.000 | 48.5 | 50.2 | ok | ok |
| docs-anthropic-com-en-release-notes-api | tier1 | article | anthropic | 0.800 | 0.800 | 40.9 | 40.5 | ok | ok |
| docs-aws-amazon-com-AmazonS3-latest-userguide-Welc | tier1 | article | aws | 1.000 | 1.000 | 58.8 | 58.8 | ok | ok |
| docs-perplexity-ai-guides-prompt-guide | tier1 | article | perplexity | 0.800 | 0.800 | 41.7 | 41.7 | ok | ok |
| docs-perplexity-ai-guides-search-domain-filter-gui | tier1 | article | perplexity | 0.800 | 0.800 | 46.8 | 46.8 | ok | ok |
| docs-snowflake-com-en-user-guide-data-load-overvie | tier1 | article | snowflake | 0.400 | 0.400 | 46.1 | 46.1 | ok | ok |
| help-github-com-en-github-site-policy-github-terms | tier1 | article | github | 0.600 | 0.600 | 56.8 | 56.8 | ok | ok |
| learn-microsoft-com-en-us-azure-ai-services-openai | tier1 | article | learn | 1.000 | 1.000 | 59.0 | 59.5 | ok | ok |
| docs-python-org-3-faq-general-html | tier1 | faq | python | 1.000 | 1.000 | 44.7 | 44.7 | ok | ok |
| docs-python-org-3-faq-programming-html | tier1 | faq | python | 1.000 | 0.800 | 44.9 | 44.9 | ok | ok |
| learn-microsoft-com-en-us-azure-aks-faq | tier1 | faq | learn | 1.000 | 1.000 | 80.5 | 81.4 | ok | ok |
| docs-anthropic-com-en-docs-welcome | tier1 | landing | anthropic | 0.600 | 0.600 | 45.4 | 47.1 | ok | ok |
| docs-github-com-en-get-started-learning-about-gith | tier1 | landing | github | 0.600 | 0.600 | 53.8 | 53.8 | ok | ok |
| nodejs-org-en-about | tier1 | landing | nodejs | 0.600 | 0.600 | 54.7 | 54.7 | ok | ok |
| docs-anthropic-com-en-docs-about-claude-models-ove | tier1 | reference | anthropic | 0.600 | 0.600 | 41.0 | 40.4 | ok | ok |
| docs-aws-amazon-com-AWSEC2-latest-APIReference-API | tier1 | reference | aws | 0.800 | 1.000 | 66.0 | 66.0 | ok | ok |
| docs-docker-com-engine-reference-commandline-run | tier1 | reference | docker | 0.800 | 0.800 | 65.1 | 66.4 | ok | ok |
| docs-github-com-en-rest-repos-repos | tier1 | reference | github | 0.000 | 0.000 | 48.8 | 48.7 | ok | ok |
| docs-python-org-3-library-functions-html | tier1 | reference | python | 0.800 | 0.800 | 38.9 | 38.8 | ok | ok |
| docs-python-org-3-library-os-html | tier1 | reference | python | 0.800 | 0.800 | 57.2 | 57.2 | ok | ok |
| docs-snowflake-com-en-sql-reference-functions-coun | tier1 | reference | snowflake | 1.000 | 1.000 | 41.1 | 41.2 | ok | ok |
| docs-stripe-com-api-charges | tier1 | reference | stripe | 0.000 | 0.000 | 49.4 | 48.9 | ok | ok |
| kubernetes-io-docs-reference-kubectl | tier1 | reference | k8s | 0.800 | 0.800 | 68.2 | 68.1 | ok | ok |
| learn-microsoft-com-en-us-dotnet-api-system-string | tier1 | reference | learn | 0.800 | 0.600 | 52.9 | 73.0 | ok | ok |
| nodejs-org-api-fs-html | tier1 | reference | nodejs | 0.800 | 0.800 | 50.5 | 50.5 | ok | ok |
| www-postgresql-org-docs-current-sql-select-html | tier1 | reference | postgres | 1.000 | 1.000 | 38.6 | 38.6 | ok | ok |
| docs-snowflake-com-en-user-guide-sample-data-using | tier1 | sample | snowflake | 0.800 | 0.800 | 44.9 | 44.9 | ok | ok |
| developer-mozilla-org-en-US-docs-Learn-Forms-Your- | tier1 | tutorial | mdn | 0.600 | 0.600 | 58.1 | 57.8 | ok | ok |
| docs-anthropic-com-en-api-getting-started | tier1 | tutorial | anthropic | 0.800 | 0.600 | 46.7 | 46.0 | ok | ok |
| docs-docker-com-get-started-02-our-app | tier1 | tutorial | docker | 0.600 | 0.600 | 66.6 | 69.4 | ok | ok |
| docs-github-com-en-get-started-start-your-journey- | tier1 | tutorial | github | 0.600 | 0.600 | 58.6 | 58.6 | ok | ok |
| docs-python-org-3-tutorial-introduction-html | tier1 | tutorial | python | 0.800 | 0.600 | 54.8 | 54.8 | ok | ok |
| docs-stripe-com-payments-accept-a-payment-platform | tier1 | tutorial | stripe | 0.600 | 0.600 | 39.9 | 39.9 | ok | ok |
| kubernetes-io-docs-tutorials-hello-minikube | tier1 | tutorial | k8s | 0.800 | 0.800 | 71.5 | 71.4 | ok | ok |
| learn-microsoft-com-en-us-azure-aks-tutorial-kuber | tier1 | tutorial | learn | 0.800 | 0.600 | 64.1 | 76.4 | ok | ok |
| en-wikipedia-org-wiki-Cloud-computing | tier2 | article | wikipedia | — | 0.000 | — | 62.2 | failed | ok |
| en-wikipedia-org-wiki-Large-language-model | tier2 | article | wikipedia | — | 0.600 | — | 60.5 | failed | ok |
| platform-openai-com-docs-guides-function-calling | tier2 | article | openai | — | 1.000 | — | 52.3 | failed | ok |
| docs-docker-com-get-started | tier2 | landing | docker | — | 0.800 | — | 67.0 | short | ok |
| cloud-google-com-bigquery-docs-samples | tier2 | sample | gcp | — | 0.600 | — | 71.6 | short | ok |
| docs-stripe-com-payments-quickstart | tier2 | tutorial | stripe | — | 0.800 | — | 40.0 | short | ok |
| platform-openai-com-docs-quickstart | tier2 | tutorial | openai | — | 0.400 | — | 53.2 | failed | ok |
