"""In-memory session tracking for the web experience."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from game_builder_agent.schemas import GamePlan


@dataclass(slots=True)
class SessionState:
    session_id: str
    prompt: str
    clarifications: List[str] = field(default_factory=list)
    answered: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    last_acknowledgement: Optional[str] = None
    plan: Optional[GamePlan] = None
    repo_path: Optional[str] = None
    status: str = "awaiting_clarifications"
    selected_model: Optional[str] = None
    output_path: Optional[Path] = None


class SessionStore:
    """In-memory store. Replace with persistent storage in production."""

    def __init__(self) -> None:
        self._sessions: Dict[str, SessionState] = {}

    def create(
        self,
        prompt: str,
        clarifications: List[str],
        *,
        model: Optional[str] = None,
        output_path: Optional[Path] = None,
    ) -> SessionState:
        session_id = uuid.uuid4().hex
        state = SessionState(
            session_id=session_id,
            prompt=prompt,
            clarifications=clarifications,
            selected_model=model,
            output_path=output_path,
        )
        self._sessions[session_id] = state
        return state

    def get(self, session_id: str) -> SessionState:
        if session_id not in self._sessions:
            raise KeyError(session_id)
        return self._sessions[session_id]

    def update(self, session: SessionState) -> None:
        self._sessions[session.session_id] = session

    def clear(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)