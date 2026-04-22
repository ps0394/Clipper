"""Claude-based Q/A generator for Phase 5.

SCAFFOLDING — this module defines the interface and writes the prompt
to disk, but does not call the Claude API yet. Wire the API client in
the pilot runner once credentials are available.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Protocol

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
) -> str:
    """Render the generator prompt for a single page."""
    template = load_template("generator")
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

    Tolerates leading/trailing whitespace and a surrounding ```json ... ```
    fence. Mistral Large 3 wraps its output in a code block despite the
    prompt instruction to the contrary; stripping is cheaper than
    failing and re-prompting.
    """
    s = raw.strip()
    if s.startswith("```"):
        # drop opening fence (``` or ```json) and closing fence
        first_newline = s.find("\n")
        if first_newline != -1:
            s = s[first_newline + 1 :]
        if s.rstrip().endswith("```"):
            s = s.rstrip()[: -3].rstrip()
    data = json.loads(s)
    if not isinstance(data, list):
        raise ValueError("Generator output is not a JSON array")
    pairs: List[QAPair] = []
    for i, obj in enumerate(data):
        if not isinstance(obj, dict):
            raise ValueError(f"Generator output item {i} is not an object")
        pairs.append(QAPair.from_dict(obj))
    return pairs


def generate_for_page(
    *,
    client: GeneratorClient,
    title: str,
    url: str,
    profile: str,
    document_text: str,
    out_dir: Path,
) -> List[QAPair]:
    """Run the generator for one page and persist prompt + raw output.

    Writes `generator.prompt.txt` and `generator.raw.json` under
    `out_dir`. Returns the parsed QAPair list.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    prompt = build_generator_prompt(
        title=title, url=url, profile=profile, document_text=document_text
    )
    (out_dir / "generator.prompt.txt").write_text(prompt, encoding="utf-8")
    raw = client.complete(prompt)
    (out_dir / "generator.raw.json").write_text(raw, encoding="utf-8")
    return parse_generator_output(raw)
