"""Tests for retrievability.phase5.intersection."""
from __future__ import annotations

import pytest

from retrievability.phase5.intersection import (
    MIN_SENTENCE_CHARS,
    compute_intersection,
    to_dict,
)


def _long(s: str) -> str:
    """Pad a sentence so it passes MIN_SENTENCE_CHARS after normalization."""
    pad = "x" * max(0, MIN_SENTENCE_CHARS - len(s) + 5)
    return f"{s} {pad}."


def test_identical_inputs_full_overlap():
    text = (
        "Cloud computing delivers compute power on demand over the internet. "
        "It enables elastic scaling of resources for many workloads."
    )
    result = compute_intersection(text, text)
    assert result.n_shared == 2
    assert result.overlap_ratio_rendered == 1.0
    assert result.overlap_ratio_markdown == 1.0
    assert result.chars > 0


def test_disjoint_inputs_no_overlap():
    rendered = (
        "Cloud computing delivers compute power on demand over the internet. "
        "It enables elastic scaling of resources for many workloads."
    )
    markdown = (
        "Photosynthesis converts sunlight into chemical energy in plant cells. "
        "Mitochondria produce ATP through cellular respiration in eukaryotes."
    )
    result = compute_intersection(rendered, markdown)
    assert result.n_shared == 0
    assert result.text == ""
    assert result.overlap_ratio_rendered == 0.0


def test_partial_overlap_keeps_only_shared():
    shared = "Containers package an application together with its dependencies."
    rendered = (
        f"{shared} "
        "The host kernel is shared between containers, unlike virtual machines."
    )
    markdown = (
        f"{shared} "
        "Each container gets its own filesystem namespace at runtime."
    )
    result = compute_intersection(rendered, markdown)
    assert result.n_shared == 1
    assert "Containers package" in result.text
    assert "host kernel" not in result.text
    assert "filesystem namespace" not in result.text


def test_markdown_formatting_does_not_block_match():
    rendered = (
        "Containers package an application together with its dependencies."
    )
    markdown = (
        "## Heading\n\n"
        "**Containers** package an application together with its `dependencies`."
    )
    result = compute_intersection(rendered, markdown)
    assert result.n_shared == 1


def test_markdown_link_syntax_normalizes_to_text():
    rendered = (
        "See the official documentation for the complete API reference list."
    )
    markdown = (
        "See the [official documentation](https://example.com) for the complete API reference list."
    )
    result = compute_intersection(rendered, markdown)
    assert result.n_shared == 1


def test_case_and_whitespace_normalization():
    rendered = (
        "Containers package an application together with its dependencies."
    )
    markdown = (
        "containers   package an application\ttogether with   its dependencies."
    )
    result = compute_intersection(rendered, markdown)
    assert result.n_shared == 1


def test_short_sentences_excluded():
    # Each short sentence is below MIN_SENTENCE_CHARS even though it appears
    # in both inputs, so it must not contribute to the intersection.
    rendered = "Yes. No. Maybe. OK."
    markdown = "Yes. No. Maybe. OK."
    result = compute_intersection(rendered, markdown)
    assert result.n_shared == 0


def test_rendered_order_preserved():
    s1 = "Containers package an application together with its dependencies."
    s2 = "Virtual machines emulate an entire hardware stack including the kernel."
    s3 = "Orchestrators schedule containers across a cluster of host machines."
    rendered = f"{s1} {s2} {s3}"
    # Markdown has the shared sentences in a different order.
    markdown = f"{s3} {s1}"
    result = compute_intersection(rendered, markdown)
    assert result.n_shared == 2
    # s1 must appear before s3 in the output because rendered order wins.
    assert result.text.index(s1) < result.text.index(s3)


def test_duplicate_sentences_deduplicated():
    s = "Containers package an application together with its dependencies."
    rendered = f"{s} {s}"
    markdown = s
    result = compute_intersection(rendered, markdown)
    assert result.n_shared == 1


def test_empty_inputs():
    r = compute_intersection("", "")
    assert r.n_shared == 0
    assert r.text == ""
    assert r.overlap_ratio_rendered == 0.0
    assert r.overlap_ratio_markdown == 0.0


def test_to_dict_shape():
    s = "Containers package an application together with its dependencies."
    r = compute_intersection(s, s)
    d = to_dict(r)
    assert set(d.keys()) == {
        "n_sentences_rendered",
        "n_sentences_markdown",
        "n_sentences_eligible_rendered",
        "n_sentences_eligible_markdown",
        "n_shared",
        "overlap_ratio_rendered",
        "overlap_ratio_markdown",
        "chars",
        "min_sentence_chars",
    }
    assert d["min_sentence_chars"] == MIN_SENTENCE_CHARS
