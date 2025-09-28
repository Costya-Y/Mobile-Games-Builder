"""Utilities for capturing and reflecting user feedback into the planning loop."""

from __future__ import annotations

import json
from typing import Iterable

from .llm_client import ChatClient
from .prompts import FEEDBACK_AFFIRMATION_PROMPT
from .schemas import FeedbackSummary


class FeedbackSynthesizer:
    """Uses the LLM to concisely acknowledge requested updates."""

    def __init__(self, client: ChatClient) -> None:
        self._client = client

    def summarize(self, notes: Iterable[str]) -> FeedbackSummary:
        joined = "\n".join(f"- {note}" for note in notes)
        messages = [
            {"role": "system", "content": FEEDBACK_AFFIRMATION_PROMPT},
            {"role": "user", "content": f"Adjustments requested:\n{joined}"},
        ]

        raw = self._client.chat(messages)
        payload = {"acknowledgement": raw.strip()}
        return FeedbackSummary.model_validate(payload)
