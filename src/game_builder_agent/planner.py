"""Plan-building capabilities for the agent."""

from __future__ import annotations

import json
from typing import List

from .llm_client import ChatClient
from .prompts import PLAN_SYSTEM_PROMPT
from .schemas import GamePlan


class Planner:
    """Transforms validated requirements into an actionable delivery plan."""

    def __init__(self, client: ChatClient) -> None:
        self._client = client

    def create_plan(self, user_prompt: str, clarifications: List[str], notes: List[str]) -> GamePlan:
        clarifications_text = "\n".join(f"- {q}" for q in clarifications) if clarifications else "None"
        notes_text = "\n".join(f"- {n}" for n in notes) if notes else "None"

        messages = [
            {"role": "system", "content": PLAN_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Create a JSON plan using the provided schema.\n\n"
                    f"Original prompt:\n{user_prompt.strip()}\n\n"
                    f"Clarifications answered:\n{clarifications_text}\n\n"
                    f"Additional notes:\n{notes_text}"
                ),
            },
        ]

        raw = self._client.chat(messages)
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("LLM response for plan was not valid JSON") from exc

        return GamePlan.model_validate(payload)
