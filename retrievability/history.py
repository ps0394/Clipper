"""Phase 4.2 (scoped down): `clipper history <url>` — trend view across
prior evaluations.

Walks ``<root>/**/*_scores.json`` looking for entries that match a URL and
prints a sorted table of how that page scored over time. Uses the score
file's mtime as the evaluation timestamp; score-file format does not
record its own timestamp today.

Deliberately a plain function, not a storage abstraction. If/when a
second backend is actually needed (e.g. Azure Cosmos), extract the
interface then.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional


@dataclass(frozen=True)
class HistoryRow:
    """One historical evaluation of a URL."""

    score_file: Path
    corpus: str
    mtime: datetime
    parseability_score: Optional[float]
    universal_score: Optional[float]
    content_type: Optional[str]
    render_mode: Optional[str]

    def as_dict(self) -> dict:
        return {
            "score_file": str(self.score_file),
            "corpus": self.corpus,
            "evaluated_at": self.mtime.isoformat(timespec="seconds"),
            "parseability_score": self.parseability_score,
            "universal_score": self.universal_score,
            "content_type": self.content_type,
            "render_mode": self.render_mode,
        }


def _iter_score_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return []
    return sorted(root.rglob("*_scores.json"))


def _normalize(url: str) -> str:
    """Normalize URLs just enough for trend matching.

    Trailing slash and trailing ``#fragment`` are dropped; query strings
    are kept because they often identify a view (e.g. ``?view=net-10.0``).
    Host and path are case-preserving because Learn paths are case-sensitive.
    """
    u = url.strip()
    if "#" in u:
        u = u.split("#", 1)[0]
    if u.endswith("/") and u.count("/") > 2:
        u = u[:-1]
    return u


def collect_history(url: str, root: Path) -> List[HistoryRow]:
    """Return every scored row for ``url`` under ``root``, sorted oldest
    first by score-file mtime.
    """
    target = _normalize(url)
    rows: List[HistoryRow] = []
    for score_file in _iter_score_files(root):
        try:
            data = json.loads(score_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(data, list):
            continue
        for entry in data:
            if not isinstance(entry, dict):
                continue
            if _normalize(entry.get("url", "")) != target:
                continue
            mtime = datetime.fromtimestamp(
                score_file.stat().st_mtime, tz=timezone.utc
            )
            rows.append(
                HistoryRow(
                    score_file=score_file,
                    corpus=score_file.parent.name,
                    mtime=mtime,
                    parseability_score=entry.get("parseability_score"),
                    universal_score=entry.get("universal_score"),
                    content_type=entry.get("content_type"),
                    render_mode=entry.get("render_mode"),
                )
            )
    rows.sort(key=lambda r: r.mtime)
    return rows


def format_table(rows: List[HistoryRow]) -> str:
    """Render the history as a plain-text table suitable for terminal output."""
    if not rows:
        return "No prior evaluations found."
    header = (
        f"{'evaluated_at':<20} {'corpus':<32} {'profile':<12} "
        f"{'render':<9} {'parse':>7} {'univ':>7} {'Δparse':>8}"
    )
    lines = [header, "-" * len(header)]
    prev_parse: Optional[float] = None
    for row in rows:
        ts = row.mtime.strftime("%Y-%m-%d %H:%M:%S")
        profile = (row.content_type or "-")[:12]
        render = (row.render_mode or "-")[:9]
        parse = (
            f"{row.parseability_score:7.2f}"
            if row.parseability_score is not None
            else "      -"
        )
        univ = (
            f"{row.universal_score:7.2f}"
            if row.universal_score is not None
            else "      -"
        )
        if (
            prev_parse is not None
            and row.parseability_score is not None
        ):
            delta = f"{row.parseability_score - prev_parse:+8.2f}"
        else:
            delta = "       -"
        lines.append(
            f"{ts:<20} {row.corpus[:32]:<32} {profile:<12} "
            f"{render:<9} {parse} {univ} {delta}"
        )
        if row.parseability_score is not None:
            prev_parse = row.parseability_score
    return "\n".join(lines)


def run_history(url: str, root: str = "evaluation", as_json: bool = False) -> int:
    """CLI entry point for ``clipper history``. Returns process exit code."""
    rows = collect_history(url, Path(root))
    if as_json:
        print(json.dumps([r.as_dict() for r in rows], indent=2))
    else:
        print(f"URL: {url}")
        print(f"Root: {root}")
        print(f"Evaluations found: {len(rows)}")
        print()
        print(format_table(rows))
    return 0 if rows else 1
