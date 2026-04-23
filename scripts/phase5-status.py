"""Print Phase 5 pilot progress from on-disk summary.json files.

Usage:
    python scripts/phase5-status.py
    python scripts/phase5-status.py --results evaluation/phase5-results/corpus-001
    python scripts/phase5-status.py --tail 10
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--results",
        type=Path,
        default=Path("evaluation/phase5-results/corpus-001"),
    )
    ap.add_argument("--total", type=int, default=43)
    ap.add_argument("--tail", type=int, default=5, help="Show N most recent pages.")
    args = ap.parse_args()

    root: Path = args.results
    if not root.is_dir():
        print(f"error: {root} not found", file=sys.stderr)
        return 2

    completed = sorted(
        (p for p in root.iterdir() if p.is_dir() and (p / "summary.json").is_file()),
        key=lambda p: (p / "summary.json").stat().st_mtime,
    )
    n = len(completed)
    print(f"{n}/{args.total} pages complete")

    if not completed:
        return 0

    now = datetime.datetime.now()
    for p in completed[-args.tail :]:
        sj = p / "summary.json"
        ts = datetime.datetime.fromtimestamp(sj.stat().st_mtime)
        try:
            s = json.loads(sj.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"  {ts:%H:%M:%S}  {p.name[:60]:60s}  [unreadable: {exc}]")
            continue
        ar = s.get("accuracy_raw")
        aR = s.get("accuracy_rendered")
        rs = s.get("raw_fetch_status", "?")
        rR = s.get("rendered_fetch_status", "?")
        print(
            f"  {ts:%H:%M:%S}  {p.name[:55]:55s}  raw={ar}  rend={aR}  [{rs}/{rR}]"
        )

    last_ts = datetime.datetime.fromtimestamp(
        (completed[-1] / "summary.json").stat().st_mtime
    )
    age = int((now - last_ts).total_seconds())
    print(f"\nLast completion: {age}s ago")
    return 0


if __name__ == "__main__":
    sys.exit(main())
