"""Claude-based Q/A generator for Phase 5.

SCAFFOLDING — this module defines the interface and writes the prompt
to disk, but does not call the Claude API yet. Wire the API client in
the pilot runner once credentials are available.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Optional, Protocol

from .schemas import QAPair
from .templates import load_template, render


class GeneratorClient(Protocol):
    """Minimal interface for whichever Claude client the pilot wires up."""

    def complete(self, prompt: str) -> str:
        """Return the model's text completion for the given prompt."""
        ...


def build_generator_prompt(
    *,
    title: str,
    url: str,
    profile: str,
    document_text: str,
    prompt_name: str = "generator",
) -> str:
    """Render the generator prompt for a single page.

    ``prompt_name`` selects which template under ``phase5/prompts/`` to
    load (default: ``generator``). Use e.g. ``generator-hard`` to swap
    in a harder-Q/A prompt for a follow-up corpus without changing the
    baseline prompt.
    """
    template = load_template(prompt_name)
    return render(
        template,
        {
            "TITLE": title,
            "URL": url,
            "PROFILE": profile,
            "DOCUMENT_TEXT": document_text,
        },
    )


def parse_generator_output(raw: str) -> List[QAPair]:
    """Parse the JSON-array response from the generator into QAPair objects.

    Tolerates (a) leading/trailing whitespace, (b) a surrounding
    ```json ... ``` fence, and (c) multiple fenced code blocks — Mistral
    Large 3 sometimes emits a first attempt, realizes it missed the
    prompt constraint (e.g. "exactly 5 pairs"), and appends a
    "Correction: ..." block with a second JSON array. In that case we
    take the **last** valid JSON array, which is the model's corrected
    output.
    """
    # Collect every fenced code block. If none, fall back to the whole string.
    candidates = _extract_fenced_json_blocks(raw)
    if not candidates:
        candidates = [raw.strip()]

    last_err: Optional[Exception] = None
    # Iterate from last to first so a corrected second array wins over the
    # first attempt. Also use raw_decode as a fallback for trailing garbage.
    for snippet in reversed(candidates):
        try:
            data = json.loads(snippet)
        except json.JSONDecodeError as exc:
            # Tolerate trailing junk after the array ends.
            try:
                data, _ = json.JSONDecoder().raw_decode(snippet)
            except json.JSONDecodeError as exc2:
                last_err = exc2
                continue
        if not isinstance(data, list):
            last_err = ValueError("Generator output is not a JSON array")
            continue
        pairs: List[QAPair] = []
        ok = True
        for i, obj in enumerate(data):
            if not isinstance(obj, dict):
                ok = False
                last_err = ValueError(f"Generator output item {i} is not an object")
                break
            pairs.append(QAPair.from_dict(obj))
        if ok:
            return pairs

    raise last_err or ValueError("Generator produced no parseable JSON array")


_FENCE_RE = re.compile(r"```(?:json)?\s*\n?(.*?)\n?```", re.DOTALL | re.IGNORECASE)


def _extract_fenced_json_blocks(text: str) -> List[str]:
    """Return the contents of every ```json ... ``` fence in ``text``.

    If the text has no fences at all, returns []. If a single fence has no
    closing ``` (model ran out of tokens), returns the text after the
    opening fence with whitespace stripped.
    """
    matches = _FENCE_RE.findall(text)
    if matches:
        return [m.strip() for m in matches if m.strip()]
    # Unclosed fence fallback.
    stripped = text.strip()
    if stripped.startswith("```"):
        # Drop opening fence marker line.
        nl = stripped.find("\n")
        if nl >= 0:
            return [stripped[nl + 1 :].strip()]
    return []


def generate_for_page(
    *,
    client: GeneratorClient,
    title: str,
    url: str,
    profile: str,
    document_text: str,
    out_dir: Path,
    prompt_name: str = "generator",
) -> List[QAPair]:
    """Run the generator for one page and persist prompt + raw output.

    Writes `generator.prompt.txt` and `generator.raw.json` under
    `out_dir`. Returns the parsed QAPair list.

    ``prompt_name`` selects which template under ``phase5/prompts/`` to
    load.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    prompt = build_generator_prompt(
        title=title,
        url=url,
        profile=profile,
        document_text=document_text,
        prompt_name=prompt_name,
    )
    (out_dir / "generator.prompt.txt").write_text(prompt, encoding="utf-8")
    raw = client.complete(prompt)
    (out_dir / "generator.raw.json").write_text(raw, encoding="utf-8")
    return parse_generator_output(raw)
