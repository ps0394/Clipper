# Clipper Engineering Audit

**Audit date:** April 2026
**Auditor perspective:** Senior software engineer
**Scope:** Full repository and code review, plus cloud migration assessment
**Current branch:** `paulsanders/fix-ci-workflows`

---

## 1. Executive Summary

Clipper is a standards-based CLI that scores how well web pages support AI-agent retrieval across six pillars (semantic HTML, content extractability, structured data, DOM navigability, metadata completeness, HTTP compliance). The core evaluation engine is **well-conceived** and has recently been meaningfully improved — the 6-pillar rebalance, the agent-content-hints sub-signal, the robots.txt parser correction, and the performance-evaluator thread-pool fix are all solid pieces of work.

However, the **repository has accumulated significant drift** around that core engine: duplicated docs, dead scripts, and 14 archived test directories checked into source control. The **code quality is mid-grade** — functional, but with a thousand-line evaluator class, no test suite, hardcoded file-search paths, and silent `except:` clauses that hide real failures. Most critically, the architecture is tightly coupled to a local Selenium/Chrome stack, which **caps throughput at roughly one URL every 7–10 seconds** and makes the tool unsuitable for large catalog evaluations.

Moving Clipper to Azure is not just a deployment change — it is the architectural step that unlocks the product's actual use case (continuous evaluation of documentation at org scale) and fixes the operational problems that block productization today. The recommended path is an Azure Container Apps + Service Bus + Blob Storage + Cosmos DB topology that preserves the existing Python code but turns the CLI into a horizontally-scalable worker.

---

## 2. Repository Audit

### 2.1 Repository hygiene — Needs cleanup

| Signal | Count / Status | Assessment |
|---|---|---|
| Markdown files in repo | 55 | Excessive. README + USER-INSTRUCTIONS duplicate roughly 60% of each other's content. |
| Root-level `.md` files | 10 | Demo scripts, cleanup summaries, performance plans — all should live in `docs/` or be deleted. |
| Root-level URL lists | 5 (`clipper-demo-urls.txt`, `clipper-test-urls.txt`, `competitive-analysis-urls.txt`, `learn-analysis-urls.txt`) | Duplicates of files already in `urls/`. Legacy from before the `urls/` move. |
| `archived-tests/` subdirectories | 14 | Test artifacts from development iterations, with JSON and HTML snapshots, all committed. |
| `evaluation/` subdirectories | 6 | Mix of historical evaluation output (v1, v2, v2-fix, v2-fix3) and active PRD material. |
| GitHub Actions workflows | 12 | Many are marketing/demo workflows (`clipper-instant-demo`, `clipper-interactive-demo`, `clipper-comprehensive-demo`) that overlap heavily. |
| `scripts/` Python files | 15 | Several appear to be one-off experiments (`boilerpipe-comparison`, `hybrid-framework*.py`, `lighthouse-comparison`). |
| Test suite | **None** | No `tests/`, no `test_*.py`, no `pytest` configuration. The `dev` extras declare `pytest` but nothing uses it. |

**Recommendations:**

1. Delete `archived-tests/` and add it to `.gitignore`. Move any genuinely useful snapshots to a documented fixtures directory.
2. Remove the five duplicate URL files from the repo root; `urls/` is canonical.
3. Consolidate `CLIPPER-DEMO-PACKAGE.md`, `CLIPPER-DEMO-SCRIPT.md`, `CLIPPER-QUICK-DEMO.md`, `PERFORMANCE-OPTIMIZATION-COMPLETE.md`, `PERFORMANCE-OPTIMIZATION-PLAN.md`, and `WORKSPACE-CLEANUP-SUMMARY.md` — either into a single `docs/history.md` or delete. These read as progress reports, not reference material.
4. Prune GitHub workflows to three: a real CI (lint + tests + one smoke evaluation), the weekly audit, and the quality gate. Demo workflows do not belong in the primary repo.
5. Remove `run_clipper_demo.py` and the `scripts/hybrid-framework*.py` experiments if they are no longer referenced.
6. Fold `USER-INSTRUCTIONS.md` into `README.md` or `docs/getting-started.md`. Today they drift apart — the recent scoring change required edits to both.

### 2.2 Branch and release hygiene

- Active work is being done directly on the `paulsanders/fix-ci-workflows` branch with a mix of fixes, features, docs, and scoring changes in the same history. In a multi-contributor context this is unsustainable; PRs should be scoped (one change per branch) and land via review.
- There is no `CHANGELOG.md` and no git tags. `setup.py` claims `version="3.0.0"` but nothing is released or tagged.
- The repo has no `LICENSE` file despite the README claiming MIT.
- There is no `CONTRIBUTING.md` despite the README linking to it.

### 2.3 Dependency hygiene

`requirements.txt` declares loose lower bounds (`>=`) with no upper pins and no lockfile. For a tool that depends on Selenium, axe, and Chrome — all of which have had breaking changes across minor versions — this is a reliability risk. `advertools` is declared but I could not find a single import of it in `retrievability/`; it pulls in pandas transitively and should be removed if unused. Similarly, `pyquery` and `charset-normalizer` appear in dependencies but are imported only once each with trivial usage that could be replaced by BeautifulSoup.

**Recommendations:**

1. Generate and commit `requirements.lock` (or switch to `uv`/`poetry`).
2. Drop unused dependencies: `advertools`, `pyquery` (used once, replaceable), `charset-normalizer` (used once for encoding detection — `requests` already handles this).
3. Pin `selenium`, `axe-selenium-python`, and `readability-lxml` to known-good ranges; these are the libraries most likely to break silently.

---

## 3. Code Audit

### 3.1 Architecture

The pipeline is a classic four-stage batch processor: `crawl → parse → score → report`. Each stage persists JSON to disk and the next stage reads it. This is a sound, debuggable design for a CLI tool and should be preserved.

The scoring engine has **two parallel implementations**:

- [`AccessGateEvaluator`](../retrievability/access_gate_evaluator.py) — synchronous, 1,291 lines, the source of truth for all pillar logic.
- [`PerformanceOptimizedEvaluator`](../retrievability/performance_evaluator.py) — async subclass with WebDriver pooling and `run_in_executor` fan-out, 561 lines.

This dual-path arrangement is justified historically (the perf version was added to parallelize a slow Selenium step) but has become a maintenance tax:

- Every new sub-signal risks being added to one class but not the other.
- The `--standard` flag exists to toggle between them, ostensibly "for debugging," but in practice the two paths now drift.
- `performance_score.py` exists as a thin orchestration layer that duplicates `score.py`.

The cleaner design is a single evaluator with pluggable execution strategies (or simpler: delete the sync path, default to async, and let `--concurrency=1` provide debug-style sequential behavior).

### 3.2 Code quality — Specific findings

#### Evaluator class is too large

[`access_gate_evaluator.py`](../retrievability/access_gate_evaluator.py) is 1,291 lines in a single class with ~40 methods. The six pillar evaluators should be separate modules (`evaluators/semantic_html.py`, `evaluators/structured_data.py`, etc.) each implementing a shared `PillarEvaluator` protocol. This unlocks:

- Unit tests per pillar with fixture HTML
- Independent iteration on scoring logic without merge conflicts
- Clean dependency injection for HTTP client, BeautifulSoup, etc.

#### Redundant HTML parsing

Each of the six pillars re-parses the same HTML string into its own BeautifulSoup tree (confirmed: 6 `BeautifulSoup(html_content, ...)` calls per URL in the evaluator, plus another in `parse.py`). For a typical 100 KB page this is ~20 ms × 6 wasted per URL; across a batch of 1,000 URLs that is a real cost. Parse once, pass the tree.

#### Silent `except:` blocks hide real errors

Seven bare `except:` clauses in `retrievability/`, all of them swallowing exceptions without logging. Examples:

- [`cli.py` L39, L49, L76, L83](../retrievability/cli.py) — cleanup, crawl-result loading, summary rendering
- [`access_gate_evaluator.py` L330, L1193](../retrievability/access_gate_evaluator.py) — inside `_is_valid_url` and elsewhere
- [`performance_evaluator.py` L162](../retrievability/performance_evaluator.py) — WebDriver cleanup

These should catch specific exception classes and at minimum log at debug level. Right now a malformed file, a permission error, and a `KeyboardInterrupt` are all indistinguishable.

#### Hardcoded file-discovery logic

[`_load_html_content` in `access_gate_evaluator.py`](../retrievability/access_gate_evaluator.py) walks up to five different candidate paths to find the HTML snapshot, including a loop over every directory in the current working directory. This is fragile search logic that exists because the pipeline does not pass absolute paths between stages. The fix is: when `crawl.py` writes `crawl_results.json`, store the absolute snapshot path; downstream stages read it directly.

#### Print-based output is hostile to integration

The entire pipeline emits human-formatted text via `print()` to stdout. There is no structured logging, no `--json` output flag for the summary, and no way to run the CLI programmatically without screen-scraping. Windows charmap issues (fixed this session for emoji but still present in `cli.py` L264 `🔄`, L268 `1️⃣`, etc.) are a symptom of this.

**Fix:** route user messages through `logging` with a `StreamHandler`, keep `print()` only for the final quiet-mode summary line, and add `--json-summary` for machine consumption.

#### Data contracts are weak

`ScoreResult.audit_trail` is typed as `Dict[str, Any]` — anything can go in. The nested structure (per-pillar trails with different shapes) is stable in practice but undocumented and unvalidated. Agents and consumers parsing these JSON outputs have no schema to rely on. A `pydantic` model or `jsonschema` definition in `schemas.py` would catch drift early.

#### Security: input validation on URL files

URLs are read from a user-provided file and passed to `requests.get(url, ...)`. There is no validation that URLs use `http`/`https`, no protection against SSRF to internal addresses (file://, http://169.254.169.254), and no maximum response size limit. For a tool that may run in CI or be wrapped as a service, these are standard hardening targets.

#### Concurrency correctness

The performance evaluator ThreadPoolExecutor sizing was recently fixed (24 workers), but the sizing logic is still coupled to `max_workers * 6` — an implicit assumption that each URL generates 6 executor tasks. If a seventh pillar is added, throughput silently degrades. Prefer an explicitly-sized pool with a documented rationale, or an `asyncio.Semaphore` around URL-level work rather than worker-count math.

#### No retry logic on transient HTTP failures

The HTTP reachability check does one `httpx.get` with no retry. A single transient timeout (as seen with Stripe and Google redirect chains in the competitive eval) scores the URL at 0 for that sub-signal. For network-bound evaluation, one retry with backoff is standard.

#### Schema backward-compat hack

[`ScoreResult.to_dict`](../retrievability/schemas.py) copies `component_scores` into `subscores` for "backward compatibility" with an unnamed consumer. If that consumer is internal, remove the duplication; if it is external, document it.

### 3.3 Testing — Critical gap

**There is no test suite.** This is the single largest code-quality issue in the repo. The scoring engine has:

- Six complex pillar evaluators with point allocations that drift as features are added
- A sub-signal (agent content hints) that was just added with no regression coverage
- Two parallel evaluator implementations that can drift
- An async orchestration path with race conditions that already burned the team once

The first tests to write are fixture-based: commit small HTML files representing each pillar's success/failure modes (a page with good schema, a page with no `main`, a page with an `noindex` meta, a page with `<link rel="alternate" type="text/markdown">`). Then assert per-pillar scores against those fixtures. That single test file would have caught the thread-pool bug and the robots.txt-parser bug before they shipped.

### 3.4 What works well

Credit where due:

- **Clear separation of concerns** between crawl, parse, score, report.
- **Explicit standards mapping** (`STANDARDS_AUTHORITY` dict). This is unusually good — most scoring tools are black boxes, and Clipper's audit trails are genuinely defensible.
- **Weighted-component model** is the right abstraction for a "score made of standards" and makes it easy to reason about results.
- **Recent fixes are correct.** The robots.txt User-agent parsing, the 5-sub-signal HTTP compliance rebalance, and the performance-evaluator thread-pool sizing are all real, well-reasoned improvements.
- **The CLI ergonomics are good** — `express` mode with one-shot URL evaluation is the right default.

---

## 4. Operational Gaps

These are neither pure code nor pure repo issues, but block real-world usage:

| Gap | Current state | Impact |
|---|---|---|
| Throughput | ~7–10s per URL, limited by Selenium | Evaluating 10,000 docs takes 20+ hours sequentially |
| Parallelism across hosts | None — single process, single machine | Cannot scale horizontally |
| Result storage | Local JSON files | No historical query, no trending, no dashboards |
| Scheduling | Manual CLI invocation or weekly cron workflow | No event-driven re-evaluation (e.g. on doc publish) |
| Authentication | None | Cannot evaluate private/staged docs |
| Rate limiting | None | Can hammer a host with unbounded concurrent requests |
| Observability | `print()` output | No metrics, no traces, no alerting on drift |
| Reproducibility | Chrome version floats | Score changes between runs when Chrome auto-updates |

---

## 5. Azure Migration — Why and How

### 5.1 Why Azure specifically

Clipper evaluates Microsoft Learn, Microsoft 365 docs, and Azure docs as its primary real-world corpus. Running it in Azure puts it in the same trust/compliance boundary as the content it measures, gives it low-latency access to private previews of that content, and lines it up with the Docs team's existing pipeline for CI/CD quality gates.

Azure is also the natural home because Clipper's workload shape maps cleanly onto Azure-native primitives:

- **Bursty, embarrassingly-parallel work** → Container Apps auto-scaling from 0 to N replicas
- **Queue-driven batch** → Service Bus or Storage Queue
- **Large result sets** → Blob Storage for raw snapshots, Cosmos DB for queryable scores
- **Headless Chrome** → Playwright on Linux containers, fully supported
- **Scheduled runs** → Azure Functions timer triggers or Logic Apps
- **Dashboards** → Azure Monitor + Log Analytics + Power BI

### 5.2 Benefits

**Scale and throughput.** A Container Apps deployment with 20 replicas, each running a 4-worker asyncio pool, evaluates ~80 URLs concurrently. The current single-machine throughput ceiling of ~8 URLs/minute becomes ~600 URLs/minute. A 10,000-URL catalog finishes in under 20 minutes instead of overnight.

**Elastic cost.** Container Apps scales to zero when the queue is empty. A daily 10,000-URL audit costs only the compute minutes consumed — on the order of a few dollars per run.

**Historical data and trending.** Writing scores to Cosmos DB turns Clipper from a point-in-time tool into a continuous-monitoring product. "Was this page better two sprints ago?" becomes queryable. Regression detection on the Learn corpus becomes an automation, not a weekly review.

**Integration surface.** A stable Azure endpoint (API Management in front of a Container Apps HTTP ingress, or an Azure Function) lets docs authors trigger evaluations on PR merge, lets Copilot surface scores inline, and lets the Learn pipeline gate publishes on score thresholds.

**Security and identity.** Managed identity for Cosmos/Blob access, Key Vault for any future secrets, VNet integration for evaluating internal staging URLs — all available without writing auth code.

**Observability.** Application Insights captures distributed traces across queue → worker → storage, with per-URL and per-pillar metrics, without code changes beyond adding the OpenTelemetry SDK.

### 5.3 Target architecture

```
┌────────────────┐    ┌────────────────────┐    ┌──────────────────────┐
│  Trigger       │    │  Orchestrator      │    │  Evaluation Workers  │
│  ────────      │    │  ────────────      │    │  ──────────────────  │
│  HTTP (APIM)   │──▶│  Azure Function     │──▶│  Container Apps      │
│  Scheduled     │    │  (HTTP + Timer)    │    │  (Python + Playwright│
│  GitHub webhook│    │  Enqueue URL jobs  │    │   + axe-core)        │
└────────────────┘    └────────────────────┘    └──────────┬───────────┘
                              │                            │
                              ▼                            │
                     ┌────────────────────┐                │
                     │  Service Bus Queue │◀──────────────┘
                     │  (jobs + DLQ)      │
                     └────────────────────┘
                              │
                 ┌────────────┴──────────────┐
                 ▼                           ▼
       ┌─────────────────┐        ┌─────────────────────┐
       │  Blob Storage   │        │  Cosmos DB          │
       │  HTML snapshots │        │  Scores + trails    │
       │  (lifecycle mgd)│        │  (indexed by URL,   │
       │                 │        │   site, timestamp)  │
       └─────────────────┘        └─────────┬───────────┘
                                            │
                                            ▼
                                  ┌─────────────────────┐
                                  │  Power BI / Grafana │
                                  │  + App Insights     │
                                  └─────────────────────┘
```

**Component mapping from current code:**

| Today | Azure target |
|---|---|
| `crawl.py` | Worker stage 1, writes snapshot to Blob |
| `parse.py` + `access_gate_evaluator.py` | Same worker, pillar evaluators run in-process |
| `report.py` | Optional HTTP-triggered function |
| `samples/snapshots/` | Blob container `snapshots/{date}/{url-hash}.html` |
| `results/*.json` | Cosmos DB container `scores`, one doc per (url, run_id) |
| `print()` output | `logging` → Application Insights via OpenTelemetry |
| `ThreadPoolExecutor(24)` | Per-replica async concurrency; horizontal scale via replica count |

### 5.4 Migration plan

The migration is sequenced to keep the CLI working at every step. No big-bang rewrite.

**Phase 0 — Preparation (prerequisite)**

- Land the repo cleanup from Section 2.1 so the containerized build is not 300 MB of archived tests.
- Write the pillar-fixture test suite from Section 3.3. Without tests, a containerized worker is untestable.
- Replace Selenium with Playwright (1–2 days). Playwright's async API integrates cleanly with the existing asyncio code, has better Linux-headless stability, and removes the `axe-selenium-python` dependency. Axe-core can be injected directly via `page.add_script_tag`.

**Phase 1 — Containerize**

- Add a `Dockerfile` based on `mcr.microsoft.com/playwright/python:v1.47.0-jammy`.
- Add a thin HTTP wrapper (`retrievability/service.py`) using FastAPI that exposes `POST /evaluate` accepting a URL and returning a `ScoreResult`. The existing CLI remains for local development.
- Push to Azure Container Registry. At this point a single container can already serve HTTP evaluations — a useful intermediate deliverable.

**Phase 2 — Storage**

- Introduce a `StorageBackend` protocol with two implementations: `LocalStorage` (current JSON-on-disk) and `AzureStorage` (Blob + Cosmos). Select via env var.
- `AzureStorage` writes HTML snapshots to Blob with 30-day lifecycle, scores to Cosmos DB partitioned by URL host.
- CLI continues to work with `LocalStorage`; cloud deployment uses `AzureStorage`.

**Phase 3 — Queue-driven workers**

- Deploy the container to Azure Container Apps with a Service Bus scaler (KEDA-native).
- Add an Azure Function `EnqueueEvaluation` that accepts a batch of URLs and writes one message per URL to the queue.
- Each worker replica pulls one message, runs the full evaluation, persists to storage, acks. Dead-letter queue handles repeated failures.
- Scale rules: min 0 replicas, max 20, target 5 messages per replica.

**Phase 4 — Triggers and observability**

- Timer-triggered function for nightly audit of the Learn corpus.
- HTTP-triggered function behind APIM for on-demand evaluation from CI/CD.
- GitHub webhook endpoint for PR-time evaluation of changed docs.
- OpenTelemetry auto-instrumentation for Application Insights. Custom metrics: `evaluation.duration`, `evaluation.score`, `pillar.{name}.score`, `evaluation.failures`.

**Phase 5 — Dashboards and alerts**

- Power BI report over Cosmos DB: score trends by site, pillar breakdowns, regression flags.
- App Insights alerts: p99 duration > 30s, failure rate > 5%, average score drop > 3 points week-over-week.

**Phase 6 — Security hardening**

- Managed identity between Container Apps, Service Bus, Blob, and Cosmos. No connection strings.
- Private endpoints for Blob and Cosmos.
- VNet integration so workers can reach staged (non-public) documentation URLs.
- APIM rate limiting and subscription keys for external HTTP clients.

### 5.5 Estimated scope

Rough sizing, one senior engineer:

| Phase | Scope |
|---|---|
| 0 — Repo cleanup + tests + Playwright swap | Small |
| 1 — Containerize + FastAPI wrapper | Small |
| 2 — StorageBackend abstraction + Azure impl | Medium |
| 3 — Queue workers + Container Apps deploy | Medium |
| 4 — Triggers + observability | Medium |
| 5 — Dashboards + alerts | Small |
| 6 — Security hardening | Small |

The critical path is Phases 0–3; Phases 4–6 can run in parallel with early production traffic.

### 5.6 Cost shape (order of magnitude)

For a workload of 10,000 URLs/day:

- **Container Apps**: ~5 vCPU-hours/day @ ~$0.10/vCPU-hr = ~$0.50/day
- **Service Bus Standard**: flat ~$10/month
- **Cosmos DB serverless**: ~10k writes/day = ~$1/day
- **Blob Storage** (hot, 30-day lifecycle): ~10 GB = ~$0.20/month
- **App Insights**: ~1 GB ingest/day = ~$2.50/day

Total: **~$100–150/month for a continuous 10k-URL/day evaluation pipeline.** Orders of magnitude cheaper than a dedicated VM, and scales linearly with load.

---

## 6. Prioritized Recommendations

### Immediate (before any further feature work)

1. **Write the pillar-fixture test suite.** Six small HTML files, one test per pillar asserting expected scores. This is the highest-leverage change in this audit.
2. **Delete `archived-tests/`, the root-level duplicate URL files, and the root-level progress-report markdown files.** Commit the deletions in one PR.
3. **Replace the seven bare `except:` blocks** with specific exception classes and at-debug logging.
4. **Fix the snapshot-path fragility** by persisting absolute paths in `crawl_results.json`.

### Near-term (next 2–3 PRs)

5. **Split `access_gate_evaluator.py`** into per-pillar modules with a shared `PillarEvaluator` interface.
6. **Collapse the dual evaluator paths.** Delete `AccessGateEvaluator` as a standalone class; keep the async evaluator as the only path and expose a `--sequential` flag if debug sequencing is needed.
7. **Pin dependencies** and drop the unused ones (`advertools`, likely `pyquery` and `charset-normalizer`).
8. **Migrate print-based output to `logging`** and add a `--json-summary` flag for programmatic consumers.
9. **Replace Selenium with Playwright** — prerequisite for container deployment and an independent quality win.

### Medium-term (the Azure migration)

10. Execute Phases 1–3 of the migration plan in Section 5.4. Deliverable: an Azure endpoint that accepts a URL and returns a score, fed by a queue-driven worker pool.

### Longer-term

11. Historical data, dashboards, and PR-time evaluation integration (Phases 4–5).
12. Hardening, private endpoints, rate limiting (Phase 6).

---

## 7. Closing Assessment

Clipper has **strong product bones**: the standards-based scoring model is genuinely defensible, the audit trails are a real differentiator, and the recent round of scoring improvements (6-pillar rebalance, agent content hints, robots.txt parser) show the evaluation logic is being taken seriously. That foundation is worth building on.

The code needs **structural cleanup but not a rewrite.** The 1,300-line evaluator, the print-based output, and the missing test suite are all fixable in a few focused PRs without touching the scoring logic.

The repo needs **aggressive pruning.** The current file tree implies a much messier project than the code underneath actually is, which will hurt onboarding and outside contributions.

And the tool is **ready to leave the laptop.** An Azure-native deployment is not a nice-to-have — it is the step that matches Clipper's architecture to its actual use case (continuous, corpus-scale documentation evaluation), and every operational limitation in Section 4 disappears with it.
