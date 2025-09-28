"""HTTP client wrapper around the Ollama chat API."""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, Mapping, Optional, Protocol

import httpx

from .config import Settings

Message = Mapping[str, str]


class ChatClient(Protocol):
    def chat(self, messages: Iterable[Message], *, temperature: Optional[float] = None) -> str:
        ...


class OllamaClient(ChatClient):
    """Lightweight synchronous client for Ollama's /api/chat endpoint."""

    def __init__(self, settings: Settings, *, timeout: float = 120.0) -> None:
        self._settings = settings
        self._client = httpx.Client(base_url=str(settings.ollama_base_url), timeout=timeout)

    def chat(self, messages: Iterable[Message], *, temperature: Optional[float] = None) -> str:
        payload: Dict[str, Any] = {
            "model": self._settings.ollama_model,
            "messages": list(messages),
        }
        temp = temperature if temperature is not None else self._settings.temperature
        payload["options"] = {"temperature": temp}

        response = self._client.post("/api/chat", json=payload)
        response.raise_for_status()
        data = response.json()

        # Ollama supports both streaming and non-streaming responses. For our use case we expect
        # the aggregated response payload to include a "message" key.
        if message := data.get("message"):
            content = message.get("content", "")
        else:
            content = data.get("response", "")

        if not isinstance(content, str):
            raise ValueError(f"Unexpected Ollama response payload: {json.dumps(data)[:250]}")
        return content

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "OllamaClient":  # pragma: no cover - context manager sugar
        return self

    def __exit__(self, *_exc_info: object) -> None:  # pragma: no cover - context manager sugar
        self.close()
