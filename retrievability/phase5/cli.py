"""Phase 5 CLI dispatcher.

Current state: scaffolding + Foundry client adapters in place. The
pilot runner (corpus -> generator -> reviewer -> scorer -> grader ->
analyzer) is not yet wired end-to-end; `status` reports what is ready.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def dispatch(args: argparse.Namespace) -> int:
    if getattr(args, "phase5_command", None) in (None, "status"):
        return _status(check=getattr(args, "check", False))
    print(f"Unknown phase5 subcommand: {args.phase5_command}")
    return 2


def _status(*, check: bool = False) -> int:
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
    print("  generator  OK (prompt builder + output parser)")
    print("  reviewer   OK (CLI loop)")
    print("  scorer     OK (prompt builder + driver)")
    print("  grader     OK (pilot-grade heuristic, calibrate before full run)")
    print("  analyzer   OK (Spearman rho + bootstrap CI, pure Python)")
    print("  clients    OK (Foundry GPT-4.1 / Mistral / Llama adapters)")
    print()

    from .clients import FoundryConfig
    config = FoundryConfig.from_env()
    missing = config.check()
    print("Foundry config (.env):")
    print(f"  endpoint:            {'SET' if config.endpoint else 'MISSING'}")
    print(f"  api_key:             {'SET' if config.api_key else 'MISSING'}")
    print(f"  generator:           {config.generator_deployment or 'MISSING'}")
    print(f"  scorer_primary:      {config.scorer_primary_deployment or 'MISSING'}")
    print(f"  scorer_secondary:    {config.scorer_secondary_deployment or 'MISSING'}")
    if missing:
        print(f"  [!] missing required env vars: {', '.join(missing)}")
        print(f"  Copy .env.example to .env and fill in values.")
        return 0 if not check else 1

    if not check:
        print()
        print("Pass --check to ping each deployment.")
        return 0

    print()
    print("Pinging deployments (temperature=0 'Reply OK')...")
    from .clients import smoke_test
    results = smoke_test(config)
    all_ok = True
    for role, info in results.items():
        info_dict = info  # type: ignore[assignment]
        ok = info_dict.get("ok")
        deployment = info_dict.get("deployment")
        if ok:
            reply = info_dict.get("reply") or ""
            print(f"  [OK]   {role:<18} {deployment}  -> {reply!r}")
        else:
            err = info_dict.get("error") or "not configured"
            print(f"  [FAIL] {role:<18} {deployment}  -> {err}")
            if role != "scorer_secondary":
                all_ok = False
    return 0 if all_ok else 1


def _state(p: Path) -> str:
    return "present" if p.is_dir() else "MISSING"
