"""Content-intersection extraction for paired markdown-vs-rendered tests.

Given two text extractions of the same page (the rendered-HTML readability
extract and the served-markdown extract), produce a third document that
contains only sentences that demonstrably exist in BOTH versions.

Why this exists
---------------
The original F4.2 paired test generated Q/A from the rendered-HTML extract
and graded both versions against them. That bakes a containment bias into
the test: any content the markdown legitimately omits (nav, dynamic
widgets, expanded tables) becomes a grading penalty against markdown even
though the markdown is doing its job. The HTML version wins by definition
on anything the markdown drops.

The intersection corrects that. By generating Q/A only from content that
appears in BOTH versions, neither format has a structural advantage on
the question pool. Any remaining accuracy delta is attributable to format
itself (ordering, density, formatting noise) rather than to coverage.

Method
------
1. Sentence-tokenize both inputs (period/question/exclamation boundaries
   plus newline boundaries; no NLTK dependency).
2. Normalize each sentence: lowercase, collapse whitespace, strip common
   markdown punctuation that does not exist in the rendered text
   (``*``, ``_``, ``` ` ```, leading list markers, heading hashes).
3. Keep sentences whose normalized form appears in both sets.
4. Reassemble the kept sentences in their original order in the
   rendered text (so the resulting document reads naturally).

Determinism
-----------
Pure function. No LLM calls, no randomness, no external state.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Tuple


# Sentence boundary: ., !, ? followed by whitespace+capital, OR a newline.
# We deliberately keep this simple — a perfect tokenizer is not needed
# because the same tokenizer runs on both sides, so any errors are
# symmetric.
_SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])|\n+")

# Markdown noise to strip when normalizing. The rendered text won't have
# these, so leaving them in would prevent matches.
_MD_NOISE_RE = re.compile(
    r"^\s*[#>\-\*\+]+\s+"          # leading heading/list/quote markers
    r"|`+"                           # backticks (inline code)
    r"|\*+"                          # bold/italic asterisks
    r"|_+"                           # underscores used for emphasis
    r"|\[([^\]]+)\]\([^)]+\)"        # markdown links: [text](url) -> text
)

# Whitespace collapse.
_WS_RE = re.compile(r"\s+")

# Minimum normalized sentence length (chars) to be eligible for matching.
# Very short fragments ("Yes.", "Note:") match too easily and inflate
# overlap without contributing useful Q/A material.
MIN_SENTENCE_CHARS = 30


@dataclass(frozen=True)
class IntersectionResult:
    """Output of :func:`compute_intersection`."""

    text: str                       # reassembled intersection document
    n_sentences_rendered: int       # sentences detected in rendered input
    n_sentences_markdown: int       # sentences detected in markdown input
    n_sentences_eligible_rendered: int   # passing MIN_SENTENCE_CHARS
    n_sentences_eligible_markdown: int
    n_shared: int                   # sentences kept in the intersection
    overlap_ratio_rendered: float   # n_shared / n_eligible_rendered
    overlap_ratio_markdown: float   # n_shared / n_eligible_markdown
    chars: int                      # len(text)


def _split_sentences(text: str) -> List[str]:
    """Split a block of text into sentence-ish units."""
    if not text:
        return []
    pieces = _SENT_SPLIT_RE.split(text)
    # Strip and drop empties.
    return [p.strip() for p in pieces if p.strip()]


def _normalize_for_matching(sentence: str) -> str:
    """Aggressively normalize a sentence for cross-format matching."""
    # Replace markdown link syntax with the link text first (capture group 1).
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", sentence)
    # Drop other markdown noise.
    s = re.sub(r"^\s*[#>\-\*\+]+\s+", "", s)
    s = s.replace("`", "").replace("*", "").replace("_", "")
    # Collapse whitespace, lowercase.
    s = _WS_RE.sub(" ", s).strip().lower()
    # Strip trailing punctuation noise that varies between formats.
    s = s.rstrip(".,;:!?")
    return s


def compute_intersection(
    rendered_text: str,
    markdown_text: str,
) -> IntersectionResult:
    """Compute the sentence-level content intersection.

    The reassembled ``text`` preserves the order in which shared sentences
    appear in ``rendered_text`` (not the markdown order), so the output
    reads as a coherent excerpt of the rendered page.
    """
    rendered_sents = _split_sentences(rendered_text)
    markdown_sents = _split_sentences(markdown_text)

    rendered_norm = [
        (i, s, _normalize_for_matching(s)) for i, s in enumerate(rendered_sents)
    ]
    markdown_norm = [
        (i, s, _normalize_for_matching(s)) for i, s in enumerate(markdown_sents)
    ]

    eligible_rendered = [t for t in rendered_norm if len(t[2]) >= MIN_SENTENCE_CHARS]
    eligible_markdown = [t for t in markdown_norm if len(t[2]) >= MIN_SENTENCE_CHARS]

    md_set = {t[2] for t in eligible_markdown}

    shared = [t for t in eligible_rendered if t[2] in md_set]
    # Preserve rendered order; deduplicate by normalized form so we don't
    # repeat the same sentence twice.
    seen: set[str] = set()
    kept: list[str] = []
    for _, original, norm in shared:
        if norm in seen:
            continue
        seen.add(norm)
        kept.append(original)

    text = "\n\n".join(kept)

    return IntersectionResult(
        text=text,
        n_sentences_rendered=len(rendered_sents),
        n_sentences_markdown=len(markdown_sents),
        n_sentences_eligible_rendered=len(eligible_rendered),
        n_sentences_eligible_markdown=len(eligible_markdown),
        n_shared=len(kept),
        overlap_ratio_rendered=(
            len(kept) / len(eligible_rendered) if eligible_rendered else 0.0
        ),
        overlap_ratio_markdown=(
            len(kept) / len(eligible_markdown) if eligible_markdown else 0.0
        ),
        chars=len(text),
    )


def to_dict(result: IntersectionResult) -> dict:
    """Serialize an :class:`IntersectionResult` for ``intersection.stats.json``."""
    return {
        "n_sentences_rendered": result.n_sentences_rendered,
        "n_sentences_markdown": result.n_sentences_markdown,
        "n_sentences_eligible_rendered": result.n_sentences_eligible_rendered,
        "n_sentences_eligible_markdown": result.n_sentences_eligible_markdown,
        "n_shared": result.n_shared,
        "overlap_ratio_rendered": round(result.overlap_ratio_rendered, 4),
        "overlap_ratio_markdown": round(result.overlap_ratio_markdown, 4),
        "chars": result.chars,
        "min_sentence_chars": MIN_SENTENCE_CHARS,
    }
