# Phase 5 pilot analysis — N=270

## Headline: raw vs rendered accuracy

| Metric | Raw | Rendered | Delta |
|---|---|---|---|
| Mean accuracy | 0.953 | 0.952 | -0.001 |
| Mean parseability_score | 72.4 | 72.6 | — |
| Mean universal_score | 72.4 | 72.6 | — |

## By tier

| tier | n | acc raw | acc rend | delta | parse raw | parse rend |
|---|---|---|---|---|---|---|
| challenged=cf_challenge | 8 | 0.960 | 0.960 | 0.000 | 71.3 | 71.5 |
| challenged=robots_blocked | 6 | 1.000 | 1.000 | 0.000 | 76.4 | 75.6 |
| challenged=ua_variant | 6 | 0.933 | 0.933 | 0.000 | 70.8 | 71.8 |
| unknown | 250 | 0.952 | 0.951 | -0.001 | 72.3 | 72.6 |

## By profile

| profile | n | acc raw | acc rend | delta | parse raw | parse rend |
|---|---|---|---|---|---|---|
| article | 56 | 0.961 | 0.962 | 0.005 | 74.3 | 74.2 |
| faq | 27 | 0.971 | 0.973 | 0.000 | 72.4 | 73.2 |
| landing | 47 | 0.904 | 0.892 | -0.008 | 70.6 | 71.4 |
| reference | 63 | 0.966 | 0.956 | -0.010 | 73.1 | 72.9 |
| sample | 24 | 0.975 | 0.978 | 0.000 | 68.3 | 69.9 |
| tutorial | 53 | 0.951 | 0.960 | 0.005 | 71.6 | 71.9 |

## By vendor

| vendor | n | acc raw | acc rend | delta | parse raw | parse rend |
|---|---|---|---|---|---|---|
| aws | 26 | 0.973 | 0.980 | 0.000 | 79.6 | 80.0 |
| clickhouse | 27 | 0.923 | 0.938 | 0.015 | 73.2 | 73.1 |
| cloudflare | 29 | 0.958 | 0.958 | 0.000 | 69.5 | 69.6 |
| databricks | 27 | 0.938 | 0.923 | -0.015 | 80.0 | 80.0 |
| huggingface | 27 | 0.950 | 0.920 | 0.000 | 72.1 | 74.6 |
| learn | 27 | 0.953 | 0.965 | 0.012 | 78.8 | 75.6 |
| mongodb | 28 | 0.947 | 0.926 | -0.021 | 64.6 | 64.6 |
| python | 26 | 0.975 | 0.974 | 0.000 | 72.0 | 72.8 |
| terraform | 25 | 0.960 | 0.960 | 0.000 | 73.7 | 73.8 |
| unknown | 1 | 1.000 | 1.000 | 0.000 | 72.7 | 72.8 |
| vercel | 27 | 0.933 | 0.933 | 0.000 | 65.8 | 66.6 |

## Fetch outcomes

| Mode | Statuses |
|---|---|
| raw | ok: 166, short: 67, failed: 37 |
| rendered | ok: 171, short: 63, failed: 36 |

## Correlation: Clipper score vs measured accuracy

| Score field | Accuracy field | n | Pearson r | mean score | mean accuracy |
|---|---|---|---|---|---|
| parseability_score_raw | accuracy_raw | 166 | 0.091 | 72.4 | 0.953 |
| parseability_score_rendered | accuracy_rendered | 171 | 0.102 | 72.6 | 0.952 |
| universal_score_raw | accuracy_raw | 166 | 0.091 | 72.4 | 0.953 |
| universal_score_rendered | accuracy_rendered | 171 | 0.102 | 72.6 | 0.952 |

## Per-pillar correlation with rendered accuracy

| Pillar | n | Pearson r | mean pillar score |
|---|---|---|---|
| semantic_html | 171 | -0.115 | 58.9 |
| content_extractability | 171 | 0.069 | 72.8 |
| structured_data | 171 | -0.067 | 62.2 |
| dom_navigability | 171 | 0.045 | 27.1 |
| metadata_completeness | 171 | -0.017 | 71.6 |
| http_compliance | 171 | 0.102 | 72.5 |

## Per-page detail

| slug | tier | profile | vendor | acc raw | acc rend | parse raw | parse rend | raw fetch | rend fetch |
|---|---|---|---|---|---|---|---|---|---|
| developers-cloudflare-com-bots-concepts-bot | challenged=cf_challenge | article | cloudflare | 1.000 | 1.000 | 71.2 | 71.2 | ok | ok |
| docs-databricks-com-aws-en-security-network | challenged=cf_challenge | article | databricks | — | — | — | — | short | short |
| developers-cloudflare-com-ddos-protection | challenged=cf_challenge | landing | cloudflare | — | — | — | — | short | short |
| developers-cloudflare-com-waf | challenged=cf_challenge | landing | cloudflare | 0.800 | 0.800 | 67.9 | 67.9 | ok | ok |
| huggingface-co-docs-hub-spaces | challenged=cf_challenge | landing | huggingface | — | — | — | — | failed | short |
| clickhouse-com-docs-cloud-manage-api-api-overview | challenged=cf_challenge | reference | clickhouse | 1.000 | 1.000 | 79.5 | 79.5 | ok | ok |
| vercel-com-docs-edge-network-regions | challenged=cf_challenge | reference | vercel | 1.000 | 1.000 | 69.1 | 69.7 | ok | ok |
| developers-cloudflare-com-turnstile-get-started | challenged=cf_challenge | tutorial | cloudflare | 1.000 | 1.000 | 69.0 | 68.9 | ok | ok |
| developer-hashicorp-com-terraform-language-provide | challenged=robots_blocked | article | terraform | 1.000 | 1.000 | 76.1 | 76.2 | ok | ok |
| docs-aws-amazon-com-AmazonS3-latest-userguide-Usin | challenged=robots_blocked | article | aws | 1.000 | 1.000 | 79.7 | 79.7 | ok | ok |
| www-mongodb-com-docs-manual-core-authentication | challenged=robots_blocked | article | mongodb | 1.000 | 1.000 | 68.8 | 68.8 | ok | ok |
| docs-databricks-com-aws-en-sql-language-manual-sql | challenged=robots_blocked | reference | databricks | — | — | — | — | failed | failed |
| docs-python-org-3-library-typing-html | challenged=robots_blocked | reference | python | 1.000 | 1.000 | 76.0 | 76.0 | ok | ok |
| learn-microsoft-com-en-us-dotnet-api-system-thread | challenged=robots_blocked | reference | learn | 1.000 | 1.000 | 81.5 | 77.3 | ok | ok |
| clickhouse-com-docs-cloud-manage-billing | challenged=ua_variant | article | clickhouse | — | — | — | — | short | short |
| learn-microsoft-com-en-us-azure-openai-concepts-mo | challenged=ua_variant | article | learn | — | — | — | — | failed | failed |
| vercel-com-docs-edge-network-caching | challenged=ua_variant | article | vercel | 1.000 | 1.000 | 67.8 | 70.7 | ok | ok |
| huggingface-co-docs-text-generation-inference-inde | challenged=ua_variant | landing | huggingface | — | — | — | — | short | short |
| www-mongodb-com-docs-atlas-atlas-search | challenged=ua_variant | landing | mongodb | 0.800 | 0.800 | 68.2 | 68.2 | ok | ok |
| developer-hashicorp-com-terraform-cloud-docs-api-d | challenged=ua_variant | reference | terraform | 1.000 | 1.000 | 76.6 | 76.6 | ok | ok |
| clickhouse-com-docs-best-practices | unknown | article | clickhouse | — | — | — | — | short | short |
| clickhouse-com-docs-concepts | unknown | article | clickhouse | — | — | — | — | short | short |
| clickhouse-com-docs-engines-table-engines | unknown | article | clickhouse | 1.000 | 1.000 | 78.1 | 78.1 | ok | ok |
| clickhouse-com-docs-engines-table-engines-mergetre | unknown | article | clickhouse | 0.800 | 1.000 | 80.0 | 80.0 | ok | ok |
| clickhouse-com-docs-optimize-skipping-indexes | unknown | article | clickhouse | 1.000 | 1.000 | 81.3 | 81.3 | ok | ok |
| developer-hashicorp-com-terraform-language-express | unknown | article | terraform | 1.000 | 1.000 | 74.2 | 74.2 | ok | ok |
| developer-hashicorp-com-terraform-language-modules | unknown | article | terraform | 1.000 | 1.000 | 74.2 | 74.2 | ok | ok |
| developer-hashicorp-com-terraform-language-provide | unknown | article | terraform | 1.000 | 1.000 | 74.7 | 74.7 | ok | ok |
| developer-hashicorp-com-terraform-language-syntax- | unknown | article | terraform | 1.000 | 1.000 | 75.0 | 75.3 | ok | ok |
| developer-hashicorp-com-terraform-language-values- | unknown | article | terraform | 1.000 | 1.000 | 74.7 | 75.0 | ok | ok |
| developers-cloudflare-com-cache-about-default-cach | unknown | article | cloudflare | 1.000 | 1.000 | 71.6 | 71.6 | ok | ok |
| developers-cloudflare-com-ddos-protection-about | unknown | article | cloudflare | — | — | — | — | short | short |
| developers-cloudflare-com-workers-observability-lo | unknown | article | cloudflare | 1.000 | 1.000 | 69.3 | 69.3 | ok | ok |
| developers-cloudflare-com-workers-platform-pricing | unknown | article | cloudflare | 1.000 | 1.000 | 71.5 | 72.3 | ok | ok |
| developers-cloudflare-com-zero-trust-identity | unknown | article | cloudflare | — | — | — | — | failed | failed |
| docs-aws-amazon-com-AmazonRDS-latest-UserGuide-CHA | unknown | article | aws | 1.000 | 1.000 | 81.1 | 81.1 | ok | ok |
| docs-aws-amazon-com-AmazonS3-latest-userguide-secu | unknown | article | aws | 1.000 | 1.000 | 74.9 | 74.9 | ok | ok |
| docs-aws-amazon-com-AmazonS3-latest-userguide-stor | unknown | article | aws | 1.000 | 1.000 | 81.1 | 81.1 | ok | ok |
| docs-aws-amazon-com-lambda-latest-dg-lambda-runtim | unknown | article | aws | 1.000 | 1.000 | 80.2 | 80.2 | ok | ok |
| docs-aws-amazon-com-whitepapers-latest-aws-overvie | unknown | article | aws | 1.000 | 1.000 | 81.1 | 81.1 | ok | ok |
| docs-databricks-com-aws-en-delta-index | unknown | article | databricks | 1.000 | 1.000 | 79.8 | 79.8 | ok | ok |
| docs-databricks-com-aws-en-dlt | unknown | article | databricks | — | — | — | — | short | short |
| docs-databricks-com-aws-en-lakehouse-medallion | unknown | article | databricks | 0.600 | 0.600 | 83.2 | 83.2 | ok | ok |
| docs-databricks-com-aws-en-security-auth-access-co | unknown | article | databricks | 1.000 | 1.000 | 82.0 | 82.0 | ok | ok |
| docs-databricks-com-aws-en-structured-streaming | unknown | article | databricks | 1.000 | 1.000 | 81.6 | 81.7 | ok | ok |
| docs-python-org-3-whatsnew-3-12-html | unknown | article | python | 1.000 | 1.000 | 63.8 | 63.7 | ok | ok |
| docs-python-org-3-whatsnew-3-13-html | unknown | article | python | 1.000 | 1.000 | 62.3 | 62.2 | ok | ok |
| huggingface-co-docs-transformers-chat-templating | unknown | article | huggingface | 1.000 | 1.000 | 68.5 | 76.0 | ok | ok |
| huggingface-co-docs-transformers-generation-strate | unknown | article | huggingface | — | 0.800 | — | 77.2 | failed | ok |
| huggingface-co-docs-transformers-glossary | unknown | article | huggingface | 1.000 | 1.000 | 65.5 | 65.5 | ok | ok |
| huggingface-co-docs-transformers-performance | unknown | article | huggingface | — | — | — | — | short | short |
| huggingface-co-docs-transformers-philosophy | unknown | article | huggingface | — | — | — | — | short | failed |
| huggingface-co-docs-transformers-training | unknown | article | huggingface | 0.800 | 0.800 | 77.6 | 77.6 | ok | ok |
| learn-microsoft-com-en-us-azure-aks-concepts-clust | unknown | article | learn | 1.000 | 1.000 | 81.4 | 75.5 | ok | ok |
| learn-microsoft-com-en-us-azure-aks-learn-quick-ku | unknown | article | learn | 1.000 | 1.000 | 81.8 | 78.9 | ok | ok |
| learn-microsoft-com-en-us-azure-architecture-guide | unknown | article | learn | 0.800 | 0.800 | 81.5 | 77.0 | ok | ok |
| learn-microsoft-com-en-us-azure-well-architected | unknown | article | learn | — | — | — | — | short | short |
| learn-microsoft-com-en-us-dotnet-csharp-programmin | unknown | article | learn | 1.000 | 1.000 | 84.0 | 77.4 | ok | ok |
| vercel-com-docs-concepts-edge-network-overview | unknown | article | vercel | 0.600 | 0.600 | 65.7 | 66.2 | ok | ok |
| vercel-com-docs-concepts-limits-overview | unknown | article | vercel | 1.000 | 1.000 | 66.3 | 66.4 | ok | ok |
| vercel-com-docs-security-overview | unknown | article | vercel | 1.000 | 1.000 | 64.3 | 64.8 | ok | ok |
| vercel-com-docs-storage-vercel-kv | unknown | article | vercel | — | — | — | — | short | short |
| vercel-com-docs-storage-vercel-postgres | unknown | article | vercel | — | — | — | — | short | short |
| www-mongodb-com-docs-manual-administration-product | unknown | article | mongodb | 1.000 | 1.000 | 75.8 | 75.8 | ok | ok |
| www-mongodb-com-docs-manual-core-aggregation-pipel | unknown | article | mongodb | 0.800 | 0.800 | 69.9 | 69.9 | ok | ok |
| www-mongodb-com-docs-manual-core-index-single | unknown | article | mongodb | — | — | — | — | short | short |
| www-mongodb-com-docs-manual-core-replica-set-archi | unknown | article | mongodb | 1.000 | 1.000 | 74.1 | 74.1 | ok | ok |
| www-mongodb-com-docs-manual-core-transactions | unknown | article | mongodb | 1.000 | 1.000 | 49.8 | 49.8 | ok | ok |
| clickhouse-com-docs-faq | unknown | faq | clickhouse | — | — | — | — | short | short |
| clickhouse-com-docs-faq-general | unknown | faq | clickhouse | — | — | — | — | short | short |
| clickhouse-com-docs-faq-operations | unknown | faq | clickhouse | — | — | — | — | short | short |
| developer-hashicorp-com-terraform-intro | unknown | faq | terraform | 1.000 | 1.000 | 72.2 | 72.1 | ok | ok |
| developer-hashicorp-com-terraform-intro-vs | unknown | faq | terraform | — | — | — | — | short | short |
| developers-cloudflare-com-r2-reference-limits | unknown | faq | cloudflare | 1.000 | 1.000 | 69.6 | 70.2 | ok | ok |
| developers-cloudflare-com-workers-platform-limits | unknown | faq | cloudflare | 1.000 | 1.000 | 69.2 | 69.2 | ok | ok |
| docs-aws-amazon-com-AmazonS3-latest-userguide-trou | unknown | faq | aws | — | 1.000 | — | 81.8 | short | ok |
| docs-aws-amazon-com-lambda-latest-dg-lambda-troubl | unknown | faq | aws | — | — | — | — | short | short |
| docs-databricks-com-aws-en-release-notes | unknown | faq | databricks | 1.000 | 1.000 | 76.4 | 76.4 | ok | ok |
| docs-databricks-com-aws-en-resources-limits | unknown | faq | databricks | — | — | — | — | short | short |
| docs-python-org-3-faq-design-html | unknown | faq | python | 0.800 | 0.800 | 74.8 | 74.8 | ok | ok |
| docs-python-org-3-faq-extending-html | unknown | faq | python | 1.000 | 1.000 | 71.4 | 71.1 | ok | ok |
| docs-python-org-3-faq-installed-html | unknown | faq | python | — | — | — | — | short | short |
| docs-python-org-3-faq-library-html | unknown | faq | python | 1.000 | 1.000 | 74.1 | 74.2 | ok | ok |
| docs-python-org-3-faq-windows-html | unknown | faq | python | 1.000 | 1.000 | 74.2 | 74.3 | ok | ok |
| huggingface-co-docs-hub-repositories-getting-start | unknown | faq | huggingface | 1.000 | 1.000 | 76.6 | 76.5 | ok | ok |
| huggingface-co-docs-hub-security | unknown | faq | huggingface | — | — | — | — | short | short |
| learn-microsoft-com-en-us-azure-cosmos-db-faq | unknown | faq | learn | 1.000 | 1.000 | 81.1 | 81.9 | ok | ok |
| learn-microsoft-com-en-us-azure-openai-faq | unknown | faq | learn | — | — | — | — | failed | failed |
| learn-microsoft-com-en-us-azure-storage-common-sto | unknown | faq | learn | — | — | — | — | failed | failed |
| vercel-com-docs-concepts-limits | unknown | faq | vercel | 1.000 | 1.000 | 66.3 | 66.4 | ok | ok |
| vercel-com-docs-errors | unknown | faq | vercel | — | — | — | — | short | short |
| www-mongodb-com-docs-manual-faq | unknown | faq | mongodb | — | — | — | — | short | short |
| www-mongodb-com-docs-manual-faq-concurrency | unknown | faq | mongodb | 1.000 | 1.000 | 71.2 | 71.2 | ok | ok |
| www-mongodb-com-docs-manual-faq-fundamentals | unknown | faq | mongodb | 0.800 | 0.800 | 70.1 | 70.1 | ok | ok |
| www-mongodb-com-docs-manual-faq-storage | unknown | faq | mongodb | 1.000 | 1.000 | 67.2 | 67.2 | ok | ok |
| clickhouse-com-docs | unknown | landing | clickhouse | — | — | — | — | short | short |
| clickhouse-com-docs-cloud | unknown | landing | clickhouse | — | — | — | — | failed | failed |
| clickhouse-com-docs-integrations | unknown | landing | clickhouse | — | — | — | — | short | short |
| clickhouse-com-docs-operations | unknown | landing | clickhouse | 0.800 | 0.800 | 44.1 | 44.1 | ok | ok |
| developer-hashicorp-com-terraform | unknown | landing | terraform | — | — | — | — | short | short |
| developer-hashicorp-com-terraform-cli | unknown | landing | terraform | — | — | — | — | short | short |
| developer-hashicorp-com-terraform-cloud-docs | unknown | landing | terraform | 1.000 | 1.000 | 71.5 | 71.4 | ok | ok |
| developer-hashicorp-com-terraform-enterprise | unknown | landing | terraform | 0.600 | 0.600 | 71.1 | 71.1 | ok | ok |
| developer-hashicorp-com-terraform-language | unknown | landing | terraform | 0.800 | 0.800 | 74.8 | 75.3 | ok | ok |
| developers-cloudflare-com-d1 | unknown | landing | cloudflare | 1.000 | 1.000 | 67.1 | 67.0 | ok | ok |
| developers-cloudflare-com-pages | unknown | landing | cloudflare | — | — | — | — | short | short |
| developers-cloudflare-com-r2 | unknown | landing | cloudflare | 0.800 | 0.800 | 69.2 | 69.2 | ok | ok |
| developers-cloudflare-com-workers | unknown | landing | cloudflare | 1.000 | 1.000 | 64.7 | 64.7 | ok | ok |
| docs-aws-amazon-com-AWSEC2-latest-UserGuide-concep | unknown | landing | aws | 1.000 | 1.000 | 80.4 | 80.4 | ok | ok |
| docs-aws-amazon-com-AmazonRDS-latest-UserGuide-Wel | unknown | landing | aws | 1.000 | 1.000 | 80.6 | 80.6 | ok | ok |
| docs-aws-amazon-com-AmazonS3-latest-userguide-Usin | unknown | landing | aws | 1.000 | 1.000 | 79.8 | 79.8 | ok | ok |
| docs-aws-amazon-com-lambda-latest-dg-welcome-html | unknown | landing | aws | 1.000 | 1.000 | 81.5 | 81.5 | ok | ok |
| docs-databricks-com | unknown | landing | databricks | — | — | — | — | short | short |
| docs-databricks-com-aws-en | unknown | landing | databricks | — | — | — | — | short | short |
| docs-databricks-com-aws-en-delta | unknown | landing | databricks | 1.000 | 1.000 | 79.8 | 79.8 | ok | ok |
| docs-databricks-com-aws-en-lakehouse | unknown | landing | databricks | 1.000 | 0.800 | 79.3 | 79.3 | ok | ok |
| docs-databricks-com-aws-en-machine-learning | unknown | landing | databricks | 1.000 | 1.000 | 84.0 | 84.0 | ok | ok |
| docs-python-org-3-contents-html | unknown | landing | python | 1.000 | — | 51.9 | — | ok | short |
| docs-python-org-3-library-index-html | unknown | landing | python | 1.000 | 1.000 | 67.1 | 67.0 | ok | ok |
| huggingface-co-docs-accelerate-index | unknown | landing | huggingface | — | — | — | — | failed | failed |
| huggingface-co-docs-datasets-index | unknown | landing | huggingface | — | — | — | — | failed | failed |
| huggingface-co-docs-diffusers-index | unknown | landing | huggingface | — | — | — | — | failed | failed |
| huggingface-co-docs-peft-index | unknown | landing | huggingface | — | — | — | — | failed | failed |
| huggingface-co-docs-transformers-index | unknown | landing | huggingface | — | — | — | — | failed | failed |
| learn-microsoft-com-en-us-azure-aks | unknown | landing | learn | — | — | — | — | short | short |
| learn-microsoft-com-en-us-azure-cosmos-db | unknown | landing | learn | — | — | — | — | short | short |
| learn-microsoft-com-en-us-azure-security-fundament | unknown | landing | learn | 1.000 | 1.000 | 81.8 | 76.0 | ok | ok |
| learn-microsoft-com-en-us-dotnet | unknown | landing | learn | — | — | — | — | short | short |
| vercel-com-docs | unknown | landing | vercel | 1.000 | 1.000 | 67.0 | 67.6 | ok | ok |
| vercel-com-docs-deployments | unknown | landing | vercel | 0.800 | 0.800 | 63.3 | 64.0 | ok | ok |
| vercel-com-docs-edge-network | unknown | landing | vercel | 0.800 | 0.800 | 65.7 | 66.2 | ok | ok |
| vercel-com-docs-functions | unknown | landing | vercel | 0.600 | 0.600 | 63.8 | 67.9 | ok | ok |
| vercel-com-docs-observability | unknown | landing | vercel | 0.800 | 0.800 | 65.3 | 65.8 | ok | ok |
| www-mongodb-com-docs-atlas | unknown | landing | mongodb | — | — | — | — | short | short |
| www-mongodb-com-docs-atlas-security-overview | unknown | landing | mongodb | — | — | — | — | failed | failed |
| www-mongodb-com-docs-drivers | unknown | landing | mongodb | — | — | — | — | short | short |
| www-mongodb-com-docs-manual | unknown | landing | mongodb | 1.000 | 1.000 | 73.8 | 73.8 | ok | ok |
| clickhouse-com-docs-interfaces-cli | unknown | reference | clickhouse | 1.000 | 1.000 | 80.0 | 80.0 | ok | ok |
| clickhouse-com-docs-operations-settings | unknown | reference | clickhouse | — | — | — | — | short | short |
| clickhouse-com-docs-operations-system-tables | unknown | reference | clickhouse | 1.000 | 1.000 | 75.8 | 75.8 | ok | ok |
| clickhouse-com-docs-sql-reference | unknown | reference | clickhouse | — | — | — | — | short | short |
| clickhouse-com-docs-sql-reference-statements-inser | unknown | reference | clickhouse | 1.000 | 1.000 | 81.0 | 81.0 | ok | ok |
| clickhouse-com-docs-sql-reference-statements-selec | unknown | reference | clickhouse | 0.600 | 0.600 | 80.3 | 78.3 | ok | ok |
| developer-hashicorp-com-terraform-cli-commands | unknown | reference | terraform | 1.000 | 1.000 | 75.8 | 75.8 | ok | ok |
| developer-hashicorp-com-terraform-cli-commands-pla | unknown | reference | terraform | 1.000 | 1.000 | 74.7 | 74.7 | ok | ok |
| developer-hashicorp-com-terraform-language-express | unknown | reference | terraform | 1.000 | 1.000 | 75.8 | 75.8 | ok | ok |
| developer-hashicorp-com-terraform-language-functio | unknown | reference | terraform | 1.000 | 1.000 | 63.6 | 63.5 | ok | ok |
| developer-hashicorp-com-terraform-language-functio | unknown | reference | terraform | — | — | — | — | short | short |
| developers-cloudflare-com-api | unknown | reference | cloudflare | — | — | — | — | short | short |
| developers-cloudflare-com-r2-api | unknown | reference | cloudflare | — | — | — | — | short | short |
| developers-cloudflare-com-workers-runtime-apis-fet | unknown | reference | cloudflare | 1.000 | 1.000 | 65.5 | 65.4 | ok | ok |
| developers-cloudflare-com-workers-runtime-apis-kv | unknown | reference | cloudflare | — | — | — | — | short | short |
| developers-cloudflare-com-workers-wrangler-command | unknown | reference | cloudflare | — | — | — | — | short | short |
| docs-aws-amazon-com-AWSEC2-latest-APIReference-Wel | unknown | reference | aws | — | — | — | — | short | short |
| docs-aws-amazon-com-AmazonS3-latest-API-API-GetObj | unknown | reference | aws | 1.000 | 1.000 | 80.4 | 80.4 | ok | ok |
| docs-aws-amazon-com-AmazonS3-latest-API-Welcome-ht | unknown | reference | aws | 1.000 | 1.000 | 81.1 | 81.1 | ok | ok |
| docs-aws-amazon-com-cli-latest-reference-dynamodb- | unknown | reference | aws | — | — | — | — | short | short |
| docs-aws-amazon-com-cli-latest-reference-ec2-index | unknown | reference | aws | — | — | — | — | short | short |
| docs-aws-amazon-com-cli-latest-reference-s3-index- | unknown | reference | aws | 1.000 | 1.000 | 75.7 | 75.7 | ok | ok |
| docs-aws-amazon-com-lambda-latest-api-welcome-html | unknown | reference | aws | 0.800 | 0.800 | 81.5 | 81.5 | ok | ok |
| docs-databricks-com-aws-en-dev-tools-api-jobs | unknown | reference | databricks | — | — | — | — | failed | failed |
| docs-databricks-com-aws-en-dev-tools-api-latest-in | unknown | reference | databricks | 1.000 | 1.000 | 77.4 | 77.4 | ok | ok |
| docs-databricks-com-aws-en-dev-tools-cli-commands | unknown | reference | databricks | — | — | — | — | short | short |
| docs-databricks-com-aws-en-sql-language-manual | unknown | reference | databricks | 0.800 | 0.800 | 67.8 | 67.8 | ok | ok |
| docs-databricks-com-aws-en-sql-language-manual-sql | unknown | reference | databricks | — | — | — | — | short | short |
| docs-python-org-3-library-asyncio-html | unknown | reference | python | — | — | — | — | short | short |
| docs-python-org-3-library-datetime-html | unknown | reference | python | 1.000 | 1.000 | 77.1 | 77.1 | ok | ok |
| docs-python-org-3-library-exceptions-html | unknown | reference | python | 1.000 | 1.000 | 74.2 | 74.2 | ok | ok |
| docs-python-org-3-library-itertools-html | unknown | reference | python | 1.000 | 1.000 | 66.8 | 66.7 | ok | ok |
| docs-python-org-3-library-re-html | unknown | reference | python | 1.000 | 1.000 | 77.5 | 77.5 | ok | ok |
| docs-python-org-3-library-string-html | unknown | reference | python | 1.000 | 0.800 | 75.8 | 75.8 | ok | ok |
| docs-python-org-3-reference-expressions-html | unknown | reference | python | 1.000 | 1.000 | 76.7 | 76.7 | ok | ok |
| docs-python-org-3-reference-lexical-analysis-html | unknown | reference | python | 1.000 | 1.000 | 77.8 | 77.8 | ok | ok |
| docs-python-org-3-reference-simple-stmts-html | unknown | reference | python | 1.000 | 1.000 | 76.3 | 76.3 | ok | ok |
| huggingface-co-docs-transformers-main-classes-mode | unknown | reference | huggingface | — | — | — | — | failed | failed |
| huggingface-co-docs-transformers-main-classes-pipe | unknown | reference | huggingface | — | — | — | — | failed | failed |
| huggingface-co-docs-transformers-main-classes-toke | unknown | reference | huggingface | — | — | — | — | failed | failed |
| huggingface-co-docs-transformers-main-classes-trai | unknown | reference | huggingface | — | — | — | — | failed | failed |
| huggingface-co-docs-transformers-model-doc-llama | unknown | reference | huggingface | — | — | — | — | failed | failed |
| learn-microsoft-com-en-us-azure-templates-microsof | unknown | reference | learn | 0.800 | 0.800 | 67.3 | 67.3 | ok | ok |
| learn-microsoft-com-en-us-dotnet-api-system-collec | unknown | reference | learn | 0.800 | 1.000 | 70.3 | 70.0 | ok | ok |
| learn-microsoft-com-en-us-dotnet-api-system-collec | unknown | reference | learn | 1.000 | 1.000 | 71.7 | 71.3 | ok | ok |
| learn-microsoft-com-en-us-dotnet-api-system-thread | unknown | reference | learn | 1.000 | 1.000 | 71.9 | 70.9 | ok | ok |
| learn-microsoft-com-en-us-powershell-module-micros | unknown | reference | learn | 1.000 | 1.000 | 82.7 | 80.8 | ok | ok |
| vercel-com-docs-cli | unknown | reference | vercel | 1.000 | 1.000 | 64.9 | 65.5 | ok | ok |
| vercel-com-docs-cli-dev | unknown | reference | vercel | — | — | — | — | short | short |
| vercel-com-docs-edge-network-headers | unknown | reference | vercel | 1.000 | 1.000 | 66.5 | 67.0 | ok | ok |
| vercel-com-docs-projects-project-configuration | unknown | reference | vercel | 1.000 | 1.000 | 67.6 | 68.1 | ok | ok |
| vercel-com-docs-rest-api | unknown | reference | vercel | — | — | — | — | short | short |
| www-mongodb-com-docs-manual-reference-configuratio | unknown | reference | mongodb | 1.000 | 1.000 | 51.0 | 51.0 | ok | ok |
| www-mongodb-com-docs-manual-reference-method-db-co | unknown | reference | mongodb | 0.800 | 0.800 | 71.1 | 71.1 | ok | ok |
| www-mongodb-com-docs-manual-reference-method-db-co | unknown | reference | mongodb | 1.000 | 1.000 | 67.8 | 67.8 | ok | ok |
| www-mongodb-com-docs-manual-reference-operator-agg | unknown | reference | mongodb | 1.000 | 0.600 | 69.4 | 69.4 | ok | ok |
| www-mongodb-com-docs-manual-reference-program-mong | unknown | reference | mongodb | 1.000 | 1.000 | 52.9 | 52.9 | ok | ok |
| clickhouse-com-docs-getting-started-example-datase | unknown | sample | clickhouse | 1.000 | 1.000 | 69.4 | 69.4 | ok | ok |
| clickhouse-com-docs-getting-started-example-datase | unknown | sample | clickhouse | 1.000 | 1.000 | 66.2 | 66.2 | ok | ok |
| developer-hashicorp-com-terraform-tutorials-aws-ge | unknown | sample | unknown | 1.000 | 1.000 | 72.7 | 72.8 | ok | ok |
| developers-cloudflare-com-pages-framework-guides | unknown | sample | cloudflare | — | — | — | — | short | short |
| developers-cloudflare-com-workers-examples | unknown | sample | cloudflare | 1.000 | 1.000 | 69.5 | 69.5 | ok | ok |
| developers-cloudflare-com-workers-examples-extract | unknown | sample | cloudflare | 0.800 | 0.800 | 66.9 | 66.9 | ok | ok |
| developers-cloudflare-com-workers-examples-redirec | unknown | sample | cloudflare | 1.000 | 1.000 | 69.1 | 69.1 | ok | ok |
| docs-aws-amazon-com-AmazonS3-latest-userguide-exam | unknown | sample | aws | — | 1.000 | — | 81.8 | short | ok |
| docs-aws-amazon-com-code-samples-latest-catalog-py | unknown | sample | aws | — | — | — | — | short | short |
| docs-aws-amazon-com-sdk-for-python-latest-develope | unknown | sample | aws | — | — | — | — | failed | failed |
| docs-databricks-com-aws-en-getting-started-sample- | unknown | sample | databricks | — | — | — | — | failed | failed |
| docs-databricks-com-aws-en-notebooks-sample-notebo | unknown | sample | databricks | — | — | — | — | failed | failed |
| github-com-hashicorp-terraform-provider-aws-tree-m | unknown | sample | terraform | — | — | — | — | short | short |
| huggingface-co-docs-diffusers-using-diffusers-load | unknown | sample | huggingface | — | — | — | — | failed | failed |
| huggingface-co-docs-transformers-notebooks | unknown | sample | huggingface | — | — | — | — | failed | failed |
| learn-microsoft-com-en-us-azure-azure-functions-fu | unknown | sample | learn | — | — | — | — | failed | failed |
| learn-microsoft-com-en-us-samples-azure-samples-az | unknown | sample | learn | — | — | — | — | failed | failed |
| learn-microsoft-com-en-us-samples-dotnet-samples | unknown | sample | learn | — | — | — | — | failed | failed |
| vercel-com-docs-functions-runtimes-node-js-node-js | unknown | sample | vercel | — | — | — | — | failed | failed |
| vercel-com-docs-functions-streaming | unknown | sample | vercel | 1.000 | 1.000 | 70.5 | 70.5 | ok | ok |
| vercel-com-templates | unknown | sample | vercel | 1.000 | 1.000 | 62.4 | 63.1 | ok | ok |
| www-mongodb-com-docs-atlas-sample-data | unknown | sample | mongodb | — | — | — | — | short | short |
| www-mongodb-com-docs-drivers-node-current-usage-ex | unknown | sample | mongodb | — | — | — | — | failed | failed |
| www-mongodb-com-docs-manual-core-sample-aggregatio | unknown | sample | mongodb | — | — | — | — | failed | failed |
| clickhouse-com-docs-getting-started-example-datase | unknown | tutorial | clickhouse | — | — | — | — | short | short |
| clickhouse-com-docs-getting-started-install | unknown | tutorial | clickhouse | — | — | — | — | short | short |
| clickhouse-com-docs-getting-started-quick-start | unknown | tutorial | clickhouse | — | — | — | — | short | short |
| clickhouse-com-docs-operations-server-configuratio | unknown | tutorial | clickhouse | 1.000 | 1.000 | 80.6 | 80.6 | ok | ok |
| clickhouse-com-docs-tutorial | unknown | tutorial | clickhouse | 0.800 | 0.800 | 55.9 | 55.9 | ok | ok |
| developer-hashicorp-com-terraform-tutorials-aws-ge | unknown | tutorial | terraform | 1.000 | 1.000 | 72.7 | 72.8 | ok | ok |
| developer-hashicorp-com-terraform-tutorials-aws-ge | unknown | tutorial | terraform | 1.000 | 1.000 | 74.4 | 74.4 | ok | ok |
| developer-hashicorp-com-terraform-tutorials-aws-ge | unknown | tutorial | terraform | 1.000 | 1.000 | 74.8 | 75.7 | ok | ok |
| developer-hashicorp-com-terraform-tutorials-config | unknown | tutorial | terraform | 0.800 | 0.800 | 73.8 | 73.9 | ok | ok |
| developer-hashicorp-com-terraform-tutorials-state- | unknown | tutorial | terraform | 1.000 | 1.000 | 72.7 | 72.8 | ok | ok |
| developers-cloudflare-com-cache-how-to-configure-c | unknown | tutorial | cloudflare | 1.000 | 1.000 | 72.5 | 72.4 | ok | ok |
| developers-cloudflare-com-pages-tutorials-build-a- | unknown | tutorial | cloudflare | 1.000 | 1.000 | 71.7 | 71.7 | ok | ok |
| developers-cloudflare-com-r2-tutorials-upload-via- | unknown | tutorial | cloudflare | — | — | — | — | failed | failed |
| developers-cloudflare-com-workers-configuration-en | unknown | tutorial | cloudflare | 1.000 | 1.000 | 72.2 | 72.2 | ok | ok |
| developers-cloudflare-com-workers-get-started-quic | unknown | tutorial | cloudflare | 0.800 | 0.800 | 72.8 | 72.8 | ok | ok |
| docs-aws-amazon-com-AWSEC2-latest-UserGuide-tutori | unknown | tutorial | aws | — | 1.000 | — | 80.4 | short | ok |
| docs-aws-amazon-com-AmazonRDS-latest-UserGuide-CHA | unknown | tutorial | aws | 0.800 | 0.800 | 74.5 | 74.5 | ok | ok |
| docs-aws-amazon-com-AmazonS3-latest-userguide-tuto | unknown | tutorial | aws | — | 1.000 | — | 81.8 | short | ok |
| docs-aws-amazon-com-lambda-latest-dg-tutorial-cont | unknown | tutorial | aws | — | 1.000 | — | 81.5 | short | ok |
| docs-databricks-com-aws-en-clusters-configure | unknown | tutorial | databricks | 1.000 | 1.000 | 83.0 | 83.0 | ok | ok |
| docs-databricks-com-aws-en-dev-tools-cli-install | unknown | tutorial | databricks | 0.800 | 0.800 | 82.7 | 82.7 | ok | ok |
| docs-databricks-com-aws-en-getting-started | unknown | tutorial | databricks | — | — | — | — | short | short |
| docs-databricks-com-aws-en-getting-started-quick-s | unknown | tutorial | databricks | — | — | — | — | short | short |
| docs-databricks-com-aws-en-jobs-scheduled | unknown | tutorial | databricks | — | — | — | — | short | short |
| docs-databricks-com-aws-en-notebooks-notebooks-use | unknown | tutorial | databricks | 1.000 | 1.000 | 83.1 | 83.1 | ok | ok |
| docs-python-org-3-howto-functional-html | unknown | tutorial | python | 1.000 | 1.000 | 76.4 | 76.4 | ok | ok |
| docs-python-org-3-howto-logging-html | unknown | tutorial | python | 1.000 | 1.000 | 77.1 | 77.1 | ok | ok |
| docs-python-org-3-howto-sockets-html | unknown | tutorial | python | 0.800 | 0.800 | 74.5 | 74.5 | ok | ok |
| docs-python-org-3-tutorial-classes-html | unknown | tutorial | python | 1.000 | 1.000 | 75.7 | 75.7 | ok | ok |
| docs-python-org-3-tutorial-inputoutput-html | unknown | tutorial | python | 1.000 | 1.000 | 74.4 | 74.4 | ok | ok |
| docs-python-org-3-tutorial-interpreter-html | unknown | tutorial | python | 0.800 | 1.000 | 73.9 | 73.4 | ok | ok |
| docs-python-org-3-tutorial-modules-html | unknown | tutorial | python | 1.000 | 1.000 | 57.4 | 57.1 | ok | ok |
| huggingface-co-docs-datasets-quickstart | unknown | tutorial | huggingface | — | — | — | — | failed | failed |
| huggingface-co-docs-diffusers-quicktour | unknown | tutorial | huggingface | — | — | — | — | failed | failed |
| huggingface-co-docs-transformers-llm-tutorial | unknown | tutorial | huggingface | — | — | — | — | failed | failed |
| huggingface-co-docs-transformers-quicktour | unknown | tutorial | huggingface | — | — | — | — | failed | failed |
| huggingface-co-docs-transformers-tutorials | unknown | tutorial | huggingface | — | — | — | — | failed | failed |
| learn-microsoft-com-en-us-azure-aks-tutorial-kuber | unknown | tutorial | learn | 1.000 | 1.000 | 83.7 | 78.2 | ok | ok |
| learn-microsoft-com-en-us-azure-aks-tutorial-kuber | unknown | tutorial | learn | 0.800 | 0.800 | 80.7 | 78.6 | ok | ok |
| learn-microsoft-com-en-us-azure-app-service-quicks | unknown | tutorial | learn | 1.000 | 1.000 | 82.6 | 80.0 | ok | ok |
| learn-microsoft-com-en-us-azure-storage-blobs-stor | unknown | tutorial | learn | 1.000 | 1.000 | 82.0 | 74.0 | ok | ok |
| learn-microsoft-com-en-us-dotnet-csharp-how-to | unknown | tutorial | learn | 1.000 | 1.000 | 73.5 | 70.0 | ok | ok |
| vercel-com-docs-deployments-environments | unknown | tutorial | vercel | 1.000 | 1.000 | 64.7 | 65.4 | ok | ok |
| vercel-com-docs-getting-started-with-vercel | unknown | tutorial | vercel | 1.000 | 1.000 | 64.6 | 65.3 | ok | ok |
| vercel-com-docs-getting-started-with-vercel-import | unknown | tutorial | vercel | 1.000 | 1.000 | 64.6 | 65.3 | ok | ok |
| vercel-com-docs-getting-started-with-vercel-projec | unknown | tutorial | vercel | 1.000 | 1.000 | 64.6 | 65.3 | ok | ok |
| vercel-com-docs-projects-environment-variables | unknown | tutorial | vercel | 1.000 | 1.000 | 67.5 | 68.0 | ok | ok |
| www-mongodb-com-docs-atlas-getting-started | unknown | tutorial | mongodb | 1.000 | 1.000 | 76.3 | 76.3 | ok | ok |
| www-mongodb-com-docs-manual-tutorial-insert-docume | unknown | tutorial | mongodb | 1.000 | 1.000 | 50.1 | 50.1 | ok | ok |
| www-mongodb-com-docs-manual-tutorial-query-documen | unknown | tutorial | mongodb | 1.000 | 1.000 | 49.1 | 49.1 | ok | ok |
| www-mongodb-com-docs-manual-tutorial-remove-docume | unknown | tutorial | mongodb | — | — | — | — | short | short |
| www-mongodb-com-docs-manual-tutorial-update-docume | unknown | tutorial | mongodb | 0.800 | 0.800 | 51.3 | 51.3 | ok | ok |
