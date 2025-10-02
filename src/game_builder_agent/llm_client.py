"""Client wrapper around the Ollama chat API using the official SDK."""

from __future__ import annotations

import json
from typing import Any, Iterable, Mapping, Optional, Protocol

import ollama

from .config import Settings

Message = Mapping[str, str]


class ChatClient(Protocol):
    def chat(self, messages: Iterable[Message], *, temperature: Optional[float] = None) -> Any:
        ...


class OllamaClient(ChatClient):
    """Lightweight synchronous client powered by :mod:`ollama`."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = ollama.Client(host=str(settings.ollama_base_url))

    def chat(self, messages: Iterable[Message], *, temperature: Optional[float] = None) -> Any:
        temp = temperature if temperature is not None else self._settings.temperature
        response = self._client.chat(
            model=self._settings.ollama_model,
            messages=list(messages),
            options={"temperature": temp},
        )

        # Ollama may respond with either a "message" dict (chat format) or a simple "response".
        data_content = response.message.content
        content: Any = data_content or ""
        try:
            if data_content:
                data_content = data_content[data_content.index("{") : data_content.rindex("}") + 1]
                content = json.loads(data_content or "")
        except (json.JSONDecodeError, ValueError):
            pass

        return content

    def close(self) -> None:
        """Align with previous interface; :mod:`ollama` does not require closing."""
        return None

    def __enter__(self) -> "OllamaClient":  # pragma: no cover - context manager sugar
        return self

    def __exit__(self, *_exc_info: object) -> None:  # pragma: no cover - context manager sugar
        self.close()
