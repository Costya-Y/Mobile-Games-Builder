"""Clarification workflow that queries the LLM."""

from __future__ import annotations

import json
from typing import List

from .llm_client import ChatClient
from .prompts import CLARIFICATION_SYSTEM_PROMPT
from .schemas import ClarificationResponse


class Clarifier:
    """Generates targeted clarification questions for the product vision."""

    def __init__(self, client: ChatClient) -> None:
        self._client = client

    def ask(self, user_prompt: str) -> List[str]:
        messages = [
            {"role": "system", "content": CLARIFICATION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "The initial product pitch is as follows. Return JSON only.\n\n"
                    f"Pitch: {user_prompt.strip()}"
                ),
            },
        ]

        raw = self._client.chat(messages)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("Failed to parse clarification questions from LLM response") from exc

        result = ClarificationResponse.model_validate(data)
        return [q.strip() for q in result.questions if q.strip()]
