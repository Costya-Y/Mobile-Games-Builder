"""Configuration helpers for the Game Builder Agent."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Tuple, cast

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, ValidationError


class Settings(BaseModel):
    """Runtime configuration loaded from environment variables."""

    ollama_base_url: HttpUrl = Field(
        default=cast(HttpUrl, "http://localhost:11434"),
        description="Base URL where the Ollama HTTP API lives.",
    )
    ollama_model: str = Field(
        default="gpt-oss:latest",
        description="The Ollama model identifier to use for planning and generation steps.",
    )
    output_root: Path = Field(
        default=Path("generated_projects"),
        description="Where generated repositories will be written.",
    )
    max_clarification_questions: Tuple[int, int] = Field(
        default=(1, 3),
        description=(
            "Inclusive range (min, max) for clarification questions to solicit from the LLM."
        ),
    )
    temperature: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Temperature passed to the Ollama chat endpoint.",
    )
    dry_run: bool = Field(
        default=False,
        description="If true, the agent will produce plans but skip repository materialization.",
    )
    available_models: Tuple[str, ...] = Field(
        default=("gpt-oss:latest", "llama-3", "mixtral"),
        description="LLM model identifiers exposed to the web UI for selection.",
    )

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)


def parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    lowered = value.lower()
    if lowered in {"1", "true", "yes", "on"}:
        return True
    if lowered in {"0", "false", "no", "off"}:
        return False
    return default


def load_settings() -> Settings:
    """Construct :class:`Settings` from the process environment."""

    env = os.environ
    overrides = {}

    if base_url := env.get("OLLAMA_BASE_URL"):
        overrides["ollama_base_url"] = base_url
    if model := env.get("OLLAMA_MODEL"):
        overrides["ollama_model"] = model
    if output_root := env.get("AGENT_OUTPUT_ROOT"):
        overrides["output_root"] = Path(output_root).expanduser()
    if temp := env.get("OLLAMA_TEMPERATURE"):
        try:
            overrides["temperature"] = float(temp)
        except ValueError:
            pass
    dry_run = parse_bool(env.get("AGENT_DRY_RUN"), default=False)
    overrides["dry_run"] = dry_run
    if models := env.get("AGENT_AVAILABLE_MODELS"):
        overrides["available_models"] = tuple(m.strip() for m in models.split(",") if m.strip())

    try:
        return Settings(**overrides)
    except ValidationError as exc:  # pragma: no cover - defensive guard
        raise RuntimeError(f"Invalid configuration: {exc}") from exc
