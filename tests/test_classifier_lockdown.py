"""Phase 4.3 — content-type classifier lockdown.

Converts a silent dependency (profile weights are shaped by a
zero-coverage classifier) into an asserted contract. Every URL in
``tests/fixtures/classifier_corpus_golden.json`` is re-classified
offline against its committed HTML snapshot; drift is rejected with the
URL and the changed signal named in the failure.

Regenerate the golden after a deliberate classifier change:

    python scripts/generate-classifier-golden.py

Then hand-review the diff before committing.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import pytest
from bs4 import BeautifulSoup

from retrievability.profiles import PROFILE_NAMES, detect_content_type


REPO_ROOT = Path(__file__).resolve().parent.parent
GOLDEN_PATH = REPO_ROOT / "tests" / "fixtures" / "classifier_corpus_golden.json"


def _load_golden() -> List[Dict]:
    assert GOLDEN_PATH.exists(), (
        f"classifier golden missing: {GOLDEN_PATH}. "
        "Run: python scripts/generate-classifier-golden.py"
    )
    with GOLDEN_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


GOLDEN = _load_golden()


def test_golden_is_nonempty():
    """Sanity: the lockdown is meaningless if the golden is empty."""
    assert len(GOLDEN) >= 20, (
        f"classifier golden has only {len(GOLDEN)} entries; "
        "extend CORPORA in scripts/generate-classifier-golden.py"
    )


def test_golden_covers_every_profile():
    """The lockdown loses value if a whole profile drops out of the
    corpus. Fail fast if that happens so the corpus is extended rather
    than silently under-sampled."""
    seen = {entry["profile"] for entry in GOLDEN}
    missing = set(PROFILE_NAMES) - seen
    assert not missing, (
        f"classifier golden missing profiles: {sorted(missing)}. "
        "Add snapshots that exercise them."
    )


@pytest.mark.parametrize(
    "entry",
    GOLDEN,
    ids=[entry["url"] for entry in GOLDEN],
)
def test_classifier_matches_golden(entry: Dict):
    """Each URL must still produce its locked (profile, source) tuple."""
    snapshot_path = REPO_ROOT / entry["snapshot"]
    assert snapshot_path.exists(), (
        f"snapshot missing for {entry['url']}: {snapshot_path}"
    )

    html = snapshot_path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(html, "html5lib")
    profile, trace = detect_content_type(soup, url=entry["url"])

    expected = (entry["profile"], entry["source"], entry.get("matched_value"))
    actual = (profile, trace.get("source", "default"), trace.get("matched_value"))

    assert actual == expected, (
        f"classifier drift on {entry['url']}:\n"
        f"  expected: profile={expected[0]} source={expected[1]} "
        f"matched_value={expected[2]!r}\n"
        f"  actual:   profile={actual[0]} source={actual[1]} "
        f"matched_value={actual[2]!r}\n"
        "If this change is intentional, regenerate the golden with "
        "`python scripts/generate-classifier-golden.py` and review the diff."
    )
