"""Azure AI Foundry client adapters for Phase 5.

Single Foundry resource, three deployments. The Azure AI Inference SDK
addresses all three via the same base URL; only the deployment name
varies per call.

Auth: API key from .env. Entra-ID auth is a later swap; deliberately
keeping the pilot simple.

This module wires concrete implementations of the `GeneratorClient`
and `ScoringClient` Protocols defined in generator.py and scorer.py.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dep
    def load_dotenv(*args, **kwargs):  # type: ignore[misc]
        return False

try:
    from azure.ai.inference import ChatCompletionsClient
    from azure.ai.inference.models import SystemMessage, UserMessage
    from azure.core.credentials import AzureKeyCredential
    _SDK_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dep
    _SDK_AVAILABLE = False


_REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class FoundryConfig:
    """Config loaded from .env. `check()` raises a clear error if incomplete."""
    endpoint: str
    api_key: str
    generator_deployment: str
    scorer_primary_deployment: str
    scorer_secondary_deployment: str

    @classmethod
    def from_env(cls, *, env_file: Optional[Path] = None) -> "FoundryConfig":
        load_dotenv(env_file or (_REPO_ROOT / ".env"))
        return cls(
            endpoint=os.environ.get("PHASE5_FOUNDRY_ENDPOINT", ""),
            api_key=os.environ.get("PHASE5_FOUNDRY_API_KEY", ""),
            generator_deployment=os.environ.get("PHASE5_GENERATOR_DEPLOYMENT", ""),
            scorer_primary_deployment=os.environ.get("PHASE5_SCORER_PRIMARY_DEPLOYMENT", ""),
            scorer_secondary_deployment=os.environ.get("PHASE5_SCORER_SECONDARY_DEPLOYMENT", ""),
        )

    def check(self) -> list[str]:
        """Return list of missing-required-field errors. Empty list = OK."""
        missing: list[str] = []
        if not self.endpoint:
            missing.append("PHASE5_FOUNDRY_ENDPOINT")
        if not self.api_key:
            missing.append("PHASE5_FOUNDRY_API_KEY")
        if not self.generator_deployment:
            missing.append("PHASE5_GENERATOR_DEPLOYMENT")
        if not self.scorer_primary_deployment:
            missing.append("PHASE5_SCORER_PRIMARY_DEPLOYMENT")
        # Secondary scorer is permitted to be blank during pilot.
        return missing


def _inference_endpoint(project_endpoint: str) -> str:
    """Normalize a Foundry project endpoint to the inference-route URL.

    The Foundry Overview page shows a project endpoint like
    `https://<resource>.services.ai.azure.com/api/projects/<project>`.
    The Azure AI Inference SDK wants the `/models` route on the same
    host. This accepts either form and returns the canonical one.
    """
    base = project_endpoint.rstrip("/")
    if base.endswith("/models"):
        return base
    # Strip /api/projects/<name> if present.
    if "/api/projects/" in base:
        base = base.split("/api/projects/")[0]
    return base + "/models"


def _require_sdk() -> None:
    if not _SDK_AVAILABLE:
        raise RuntimeError(
            "azure-ai-inference is not installed. Run: "
            "pip install -r requirements-phase5.txt"
        )


class FoundryGeneratorClient:
    """Generator client (Mistral by default). Conforms to GeneratorClient Protocol."""

    def __init__(self, config: FoundryConfig, *, deployment: Optional[str] = None, temperature: float = 0.2) -> None:
        _require_sdk()
        self._deployment = deployment or config.generator_deployment
        self._temperature = temperature
        self._client = ChatCompletionsClient(
            endpoint=_inference_endpoint(config.endpoint),
            credential=AzureKeyCredential(config.api_key),
        )

    def complete(self, prompt: str) -> str:
        response = self._client.complete(
            messages=[UserMessage(content=prompt)],
            model=self._deployment,
            temperature=self._temperature,
            max_tokens=4096,
        )
        return response.choices[0].message.content or ""


class FoundryScoringClient:
    """Scoring client (GPT-4.1 primary or Llama secondary). Conforms to ScoringClient Protocol."""

    def __init__(
        self,
        config: FoundryConfig,
        *,
        deployment: str,
        temperature: float = 0.0,
        seed: Optional[int] = 0xC11_99_3,
    ) -> None:
        _require_sdk()
        self.model_id = deployment
        self._deployment = deployment
        self._temperature = temperature
        self._seed = seed
        self._client = ChatCompletionsClient(
            endpoint=_inference_endpoint(config.endpoint),
            credential=AzureKeyCredential(config.api_key),
        )

    def answer(self, prompt: str) -> tuple[str, int, int]:
        kwargs = {
            "messages": [UserMessage(content=prompt)],
            "model": self._deployment,
            "temperature": self._temperature,
            "max_tokens": 512,
        }
        if self._seed is not None:
            kwargs["seed"] = self._seed
        response = self._client.complete(**kwargs)
        text = response.choices[0].message.content or ""
        usage = getattr(response, "usage", None)
        tokens_in = getattr(usage, "prompt_tokens", 0) if usage else 0
        tokens_out = getattr(usage, "completion_tokens", 0) if usage else 0
        return text, tokens_in, tokens_out


def smoke_test(config: FoundryConfig) -> dict[str, object]:
    """Ping each configured deployment with a trivial prompt.

    Returns {deployment_role: {"deployment": name, "ok": bool, "error": str|None, "reply": str|None}}.
    Used by `python main.py phase5 status --check` to verify wiring.
    """
    out: dict[str, object] = {}

    def _probe(role: str, deployment: str, kind: str) -> dict[str, object]:
        if not deployment:
            return {"deployment": None, "ok": False, "error": "not configured", "reply": None}
        try:
            if kind == "generator":
                client = FoundryGeneratorClient(config, deployment=deployment)
                reply = client.complete("Reply with exactly the word OK.")
            else:
                client = FoundryScoringClient(config, deployment=deployment)
                reply, _, _ = client.answer("Reply with exactly the word OK.")
            return {"deployment": deployment, "ok": True, "error": None, "reply": reply.strip()[:40]}
        except Exception as exc:  # pragma: no cover - exercised only with live creds
            return {"deployment": deployment, "ok": False, "error": f"{type(exc).__name__}: {exc}", "reply": None}

    out["generator"] = _probe("generator", config.generator_deployment, "generator")
    out["scorer_primary"] = _probe("scorer_primary", config.scorer_primary_deployment, "scorer")
    out["scorer_secondary"] = _probe("scorer_secondary", config.scorer_secondary_deployment, "scorer")
    return out
