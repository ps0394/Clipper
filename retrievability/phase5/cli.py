"""Phase 5 CLI dispatcher.

Current state: scaffolding only. The only implemented subcommand is
`status`, which reports which pieces are wired and which still need
credentials or additional code. The pilot runner itself is not wired
yet — it needs an Anthropic client and an Azure OpenAI client, which
require credentials.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def dispatch(args: argparse.Namespace) -> int:
    if getattr(args, "phase5_command", None) in (None, "status"):
        return _status()
    print(f"Unknown phase5 subcommand: {args.phase5_command}")
    return 2


def _status() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    corpus_dir = repo_root / "evaluation" / "phase5-corpus"
    results_dir = repo_root / "evaluation" / "phase5-results"
    scratch_dir = repo_root / "evaluation" / "phase5-scratch"

    print("Phase 5 scaffolding status")
    print("-" * 40)
    print(f"Design doc:     docs/phase-5-design.md (approved 2026-04-22)")
    print(f"Corpus dir:     {_state(corpus_dir)}")
    print(f"Results dir:    {_state(results_dir)}")
    print(f"Scratch dir:    {_state(scratch_dir)}  (gitignored)")
    print()
    print("Modules:")
    print("  schemas    OK")
    print("  templates  OK (generator + scorer prompts on disk)")
    print("  generator  OK (prompt builder + output parser; needs Claude client)")
    print("  reviewer   OK (CLI loop; no pilot runner yet)")
    print("  scorer     OK (prompt builder + driver; needs Azure OpenAI client)")
    print("  grader     OK (pilot-grade heuristic, calibrate before full run)")
    print("  analyzer   OK (Spearman rho + bootstrap CI, pure Python)")
    print()
    print("Still to wire:")
    print("  - Anthropic client adapter (generator)")
    print("  - Azure OpenAI client adapter (scorer primary)")
    print("  - Local Llama client adapter (scorer secondary)")
    print("  - Pilot runner that stitches corpus -> generator -> reviewer -> scorer -> grader -> analyzer")
    print("  - Credentials discovery (env vars)")
    return 0


def _state(p: Path) -> str:
    return "present" if p.is_dir() else "MISSING"
