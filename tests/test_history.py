"""Tests for the scoped-down Phase 4.2 history command.

These tests construct their own tiny on-disk corpus of score files under
``tmp_path`` so they are fully hermetic and don't depend on the committed
``evaluation/`` output.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

from retrievability.history import collect_history, format_table, run_history


def _write_score_file(path: Path, rows: list[dict], mtime_epoch: float | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows), encoding="utf-8")
    if mtime_epoch is not None:
        os.utime(path, (mtime_epoch, mtime_epoch))


def _score_row(url: str, parse: float, universal: float, profile: str = "article", render: str = "rendered") -> dict:
    return {
        "url": url,
        "parseability_score": parse,
        "universal_score": universal,
        "content_type": profile,
        "render_mode": render,
    }


def test_collect_history_finds_only_matching_urls(tmp_path: Path):
    corpus = tmp_path / "corpus-a"
    _write_score_file(
        corpus / "a_scores.json",
        [
            _score_row("https://example.com/page-a", 60.0, 55.0),
            _score_row("https://example.com/page-b", 70.0, 65.0),
        ],
    )
    rows = collect_history("https://example.com/page-a", tmp_path)
    assert len(rows) == 1
    assert rows[0].parseability_score == 60.0
    assert rows[0].corpus == "corpus-a"


def test_collect_history_is_sorted_oldest_first(tmp_path: Path):
    older = tmp_path / "old-corpus" / "o_scores.json"
    newer = tmp_path / "new-corpus" / "n_scores.json"
    _write_score_file(
        older,
        [_score_row("https://example.com/page", 50.0, 45.0)],
        mtime_epoch=time.time() - 3600,
    )
    _write_score_file(
        newer,
        [_score_row("https://example.com/page", 65.0, 60.0)],
        mtime_epoch=time.time(),
    )
    rows = collect_history("https://example.com/page", tmp_path)
    assert [r.corpus for r in rows] == ["old-corpus", "new-corpus"]


def test_collect_history_tolerates_url_normalization(tmp_path: Path):
    _write_score_file(
        tmp_path / "c" / "c_scores.json",
        [_score_row("https://example.com/page", 60.0, 55.0)],
    )
    # Trailing slash and fragment should match the stored URL.
    rows = collect_history("https://example.com/page/#section", tmp_path)
    assert len(rows) == 1


def test_collect_history_skips_malformed_files(tmp_path: Path):
    bad = tmp_path / "bad" / "bad_scores.json"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_text("{not json", encoding="utf-8")
    good = tmp_path / "good" / "good_scores.json"
    _write_score_file(good, [_score_row("https://example.com/page", 60.0, 55.0)])
    rows = collect_history("https://example.com/page", tmp_path)
    assert len(rows) == 1
    assert rows[0].corpus == "good"


def test_format_table_handles_empty_and_nonempty(tmp_path: Path):
    assert format_table([]) == "No prior evaluations found."
    _write_score_file(
        tmp_path / "c" / "c_scores.json",
        [_score_row("https://example.com/page", 60.0, 55.0, profile="tutorial")],
    )
    rows = collect_history("https://example.com/page", tmp_path)
    table = format_table(rows)
    assert "tutorial" in table
    assert "60.00" in table
    # First row has no delta to compute against
    assert table.rstrip().endswith("-")


def test_run_history_returns_nonzero_when_no_rows(tmp_path: Path, capsys: pytest.CaptureFixture):
    rc = run_history("https://example.com/missing", root=str(tmp_path))
    assert rc == 1
    out = capsys.readouterr().out
    assert "Evaluations found: 0" in out


def test_run_history_json_mode_emits_valid_json(tmp_path: Path, capsys: pytest.CaptureFixture):
    _write_score_file(
        tmp_path / "c" / "c_scores.json",
        [_score_row("https://example.com/page", 60.0, 55.0)],
    )
    rc = run_history("https://example.com/page", root=str(tmp_path), as_json=True)
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert isinstance(payload, list)
    assert payload[0]["parseability_score"] == 60.0
    assert payload[0]["universal_score"] == 55.0
    assert payload[0]["corpus"] == "c"
