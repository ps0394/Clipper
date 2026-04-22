"""Load Phase 5 prompt templates from disk.

Templates use `{{TOKEN}}` placeholders (double braces) so single-brace
content in the template text (JSON examples, Python f-string examples)
doesn't collide with the substitution syntax.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict

_PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_template(name: str) -> str:
    """Load a prompt template by stem (e.g. 'generator', 'scorer')."""
    path = _PROMPTS_DIR / f"{name}.txt"
    if not path.is_file():
        raise FileNotFoundError(f"Prompt template not found: {path}")
    return path.read_text(encoding="utf-8")


def render(template: str, values: Dict[str, str]) -> str:
    """Substitute `{{KEY}}` tokens in `template` with values.

    Missing keys raise KeyError. Unknown tokens in the template (not in
    `values`) are left as-is so they surface during manual prompt
    inspection rather than being silently dropped.
    """
    result = template
    for key, value in values.items():
        token = "{{" + key + "}}"
        if token not in result:
            raise KeyError(f"Template does not contain token {token}")
        result = result.replace(token, value)
    return result
