"""Phase 5 CLI dispatcher.

Current state: scaffolding + Foundry client adapters in place. The
pilot runner (corpus -> generator -> reviewer -> scorer -> grader ->
analyzer) is not yet wired end-to-end; `status` reports what is ready.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def dispatch(args: argparse.Namespace) -> int:
    cmd = getattr(args, "phase5_command", None)
    if cmd in (None, "status"):
        return _status(check=getattr(args, "check", False))
    if cmd == "pilot":
        return _pilot(args)
    if cmd == "rejudge":
        return _rejudge(args)
    if cmd == "kappa":
        return _kappa(args)
    print(f"Unknown phase5 subcommand: {args.phase5_command}")
    return 2


def _pilot(args: argparse.Namespace) -> int:
    from .clients import FoundryConfig
    from .runner import load_pilot_urls, run_pilot

    config = FoundryConfig.from_env()
    missing = config.check()
    if missing:
        print(f"[!] Cannot run pilot — missing env vars: {', '.join(missing)}")
        print(f"    Copy .env.example to .env and fill in values.")
        return 1

    urls_path = Path(args.urls_file)
    if not urls_path.is_file():
        print(f"URL file not found: {urls_path}")
        return 1
    urls = load_pilot_urls(urls_path)
    if not urls:
        print(f"No URLs found in {urls_path}")
        return 1
    print(f"Pilot: {len(urls)} URL(s) from {urls_path}")

    summaries = run_pilot(
        urls=urls,
        out_dir=Path(args.out),
        config=config,
        review=bool(args.review),
        reviewer_id=args.reviewer_id,
        use_secondary=bool(args.secondary_scorer),
        grader_mode=args.grader,
        generator_prompt=getattr(args, "generator_prompt", "generator"),
    )

    print()
    print("Pilot summary")
    print("-" * 40)
    for s in summaries:
        print(f"  {s.accuracy:>5.0%}  {s.num_pairs} pairs  {s.slug}")
    if summaries:
        mean = sum(s.accuracy for s in summaries) / len(summaries)
        print(f"  mean accuracy: {mean:.0%}")
    print(f"  results: {args.out}/pilot-summary.json")
    return 0


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


def _rejudge(args: argparse.Namespace) -> int:
    from .clients import FoundryConfig
    from .runner import rejudge_pilot

    config = FoundryConfig.from_env()
    missing = config.check()
    if missing:
        print(f"[!] Cannot rejudge — missing env vars: {', '.join(missing)}")
        return 1
    pilot_dir = Path(args.pilot_dir)
    if not pilot_dir.is_dir():
        print(f"Pilot dir not found: {pilot_dir}")
        return 1
    print(f"Rejudging {pilot_dir} with LLM judge ({config.scorer_secondary_deployment})")
    result = rejudge_pilot(pilot_dir=pilot_dir, config=config)
    print()
    print("Rejudge summary")
    print("-" * 40)
    for p in result["pages"]:
        print(f"  {p['judged_accuracy']:>5.0%}  {p['num_pairs']} pairs  {p['slug']}")
    print(f"  mean judged accuracy: {result['mean_judged_accuracy']:.0%}")
    print(f"  results: {pilot_dir / 'rejudge-summary.json'}")
    return 0


def _kappa(args: argparse.Namespace) -> int:
    """Compute Cohen's kappa between hand-labels and judge-labels.

    Expects:
      <pilot_dir>/_calibration/hand-labels.json   — array of {slug, pair_index, label}
      <pilot_dir>/<slug>/grades.primary.judged.json  — from rejudge or pilot --grader llm
    """
    import json as _json
    from .judge import cohens_kappa

    pilot_dir = Path(args.pilot_dir)
    hand_path = pilot_dir / "_calibration" / "hand-labels.json"
    if not hand_path.is_file():
        print(f"Hand-labels file not found: {hand_path}")
        print(f"Create it with entries: [{{\"slug\": \"...\", \"pair_index\": 0, \"label\": \"correct\"}}, ...]")
        return 1

    hand = _json.loads(hand_path.read_text(encoding="utf-8"))
    if not isinstance(hand, list) or not hand:
        print(f"Hand-labels file is empty or malformed: {hand_path}")
        return 1

    hand_labels = []
    judge_labels = []
    missing = 0
    for entry in hand:
        slug = entry["slug"]
        idx = entry["pair_index"]
        hand_label = entry["label"]
        judged_path = pilot_dir / slug / "grades.primary.judged.json"
        if not judged_path.is_file():
            missing += 1
            continue
        judged = _json.loads(judged_path.read_text(encoding="utf-8"))
        match = next((g for g in judged if g["pair_index"] == idx and g["run_index"] == 0), None)
        if match is None:
            missing += 1
            continue
        hand_labels.append(hand_label)
        judge_labels.append(match["label"])

    if missing:
        print(f"[!] {missing} hand-labeled entries had no matching judged grade; skipped.")
    if not hand_labels:
        print("No overlapping labels to compare.")
        return 1

    exact_agree = sum(1 for a, b in zip(hand_labels, judge_labels) if a == b)
    k = cohens_kappa(hand_labels, judge_labels)
    print("Calibration — hand vs judge")
    print("-" * 40)
    print(f"  n overlapping:   {len(hand_labels)}")
    print(f"  exact agreement: {exact_agree}/{len(hand_labels)} ({exact_agree/len(hand_labels):.0%})")
    print(f"  Cohen's kappa:   {k:.3f}")
    print()
    gate = 0.80
    if k >= gate:
        print(f"  [PASS] kappa >= {gate:.2f}. Judge is calibrated.")
        return 0
    print(f"  [FAIL] kappa < {gate:.2f}. Revise judge prompt or escalate to two-judge agreement.")

    # breakdown of disagreements
    print()
    print("Disagreements:")
    for entry, h, j in zip(hand, hand_labels, judge_labels):
        if h != j:
            print(f"  {entry['slug']} pair {entry['pair_index']}: hand={h}  judge={j}")
    return 2
