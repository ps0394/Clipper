
Purpose: This file provides authoritative instructions for GitHub Copilot (VS Code) when working in this repository. Copilot should treat this document as a system-level constraint and design contract for all code generation, reasoning, and suggestions.


This repository implements Clipper (Command-Line Interface Progressive Performance Evaluation & Reporting), a CLI-first retrievability evaluation system with agent-ready content negotiation testing. Copilot must optimize for determinism, auditability, and repeatability, not autonomous behavior.

**GitHub Integration Available**: This repository includes GitHub Copilot Chat integration and agent automation scripts while preserving CLI-first principles. Copilot can guide users to these interfaces but must not suggest bypassing the underlying CLI architecture.


1. Authoritative Scope (Must Not Be Violated)
Copilot is assisting with a pre-agent evaluation system that measures whether a documentation page is:

Crawlable & accessible as HTML
Parsable / extractable into primary content (low chrome, clean structure)
Structurally ready for retrieval systems (inputs to later retrieval evaluation)
Explicit Non-Goals
Copilot must not:

Rewrite content automatically
Perform agent task-completion benchmarks (ACE / SCOPE)

Act autonomously on repositories
Introduce non-deterministic logic or heuristic “judgment”
Copilot may:

Help write deterministic code
Explain HTML / DOM parsing techniques
Suggest explicitly implementable heuristics
Review JSON outputs for correctness and completeness


2. Working Model (Conceptual Contract)
Copilot must preserve the following mental model:

VS Code = workbench only
The CLI = the actual product
Agents (if any) come later, wrapping the CLI
Copilot must never collapse these roles or suggest skipping the CLI layer.


3. Repository Shape (Canonical)
Copilot should assume and preserve this structure:
retrievability-eval/
├─ README.md              # Product definition and non-goals
├─ retrievability/
│  ├─ __init__.py
│  ├─ cli.py              # argparse entrypoint (5 commands: crawl, parse, score, report, negotiate)
│  ├─ crawl.py            # URL fetch + HTML snapshot + content negotiation testing
│  ├─ parse.py            # extractability signals
│  ├─ score.py            # scoring + failure modes
│  └─ schemas.py          # JSON output contracts
├─ samples/
│  ├─ urls.txt            # 5–10 Learn URLs
│  └─ snapshots/
├─ reports/
│  ├─ report.json
│  └─ report.md
└─ docs/
   └─ scoring.md          # One-page scoring explanation


Python is the default language unless explicitly overridden.


4. CLI Contract (Hard Requirement)
Copilot must respect and help implement this CLI interface exactly:
```
retrievability crawl urls.txt --out snapshots/
retrievability parse snapshots/ --out parse.json
retrievability score parse.json --out report.json
retrievability report report.json --md report.md
retrievability negotiate urls.txt --out negotiation/ 
retrievability express urls.txt --out results/
```


Rules:

Each command must be runnable independently
Outputs must be reusable without re-running prior stages
No hidden or implicit state


5. Crawl Stage — crawl.py
Responsibilities:

Fetch each URL
Capture and persist:

HTTP status
Response headers
Final resolved URL
Raw HTML (as returned)
Expected per-URL output shape:
{
  "url": "…",
  "timestamp": "…",
  "status": 200,
  "headers": { "content-type": "text/html" },
  "html_path": "snapshots/abc123.html"
}

Copilot must not introduce parsing or scoring logic here.


6. Parseability Stage — parse.py
Copilot should help implement deterministic, evidence-based signals only. Initial signals include:

Presence of <main> or <article>
Heading hierarchy validity (H1 → H2 → H3)
Text density (primary content vs total DOM)
Detection of code blocks / tables
Boilerplate leakage estimate (nav / footer dominance)
Copilot must emit raw signals and evidence, never subjective judgments.


7. Scoring Stage — score.py
Copilot may help map signals to normalized scores (0–100):

Parseability score
Failure-mode label:extraction-noisy
structure-missing
clean
Any composite score must be explicit, documented, and reproducible.


8. Reporting Requirements
JSON (Authoritative Output)
Must contain:

Raw signals
Subscores
Failure mode classification
Evidence references
Markdown (Human-Facing Output)
Must clearly answer:

What failed?
Why did it fail?
Who likely owns the fix?
Marketing language is prohibited.


9. Copilot Usage Guidance
Good Copilot Prompts

“Write a deterministic heuristic to estimate boilerplate leakage from HTML.”
“Given this DOM, identify heading hierarchy violations.”
“Review this JSON output for missing evidence fields.”
Prohibited Copilot Prompts

“Decide whether this page is good for agents.”
“Rewrite this content automatically.”
When unsure, Copilot should apply this test:


Would this produce the same result if rerun tomorrow?


If not, the suggestion is invalid.


10. Definition of Success (Prototype)
Copilot should guide development until:

The CLI runs end-to-end on 5–10 pages
Outputs are stable across repeated runs
A human can read report.md and immeunderstandtely see what to fix
It is obvious how an agent could consume report.json later


11. Explicit Non-Goals (Do Not Suggest Yet)
Copilot must not suggest:

VS Code extensions
Web dashboards
Autonomous remediation
Multi-agent orchestration
These come after the CLI is trusted.


12. Final System Constraint


Build the system agents will trust — not the agent itself.

If Copilot is unsure how to proceed, it should implement the smallest missing deterministic piece that moves the CLI toward completeness.
