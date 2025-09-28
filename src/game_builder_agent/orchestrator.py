"""End-to-end orchestration for the Game Builder Agent."""

from __future__ import annotations

from pathlib import Path
from typing import List

from rich.console import Console

from .clarifier import Clarifier
from .config import Settings
from .executor import PlanExecutor
from .feedback import FeedbackSynthesizer
from .io import ConsoleInteraction, InteractionPort
from .llm_client import OllamaClient
from .planner import Planner
from .presenter import show_plan


class Orchestrator:
    def __init__(self, settings: Settings, io: InteractionPort | None = None) -> None:
        self._settings = settings
        self._console = Console()
        self._io = io or ConsoleInteraction(self._console)
        self._client = OllamaClient(settings)
        self._clarifier = Clarifier(self._client)
        self._planner = Planner(self._client)
        self._feedback = FeedbackSynthesizer(self._client)
        self._executor = PlanExecutor(settings, self._client)

    def run(self, initial_prompt: str) -> Path | None:
        clarifications = self._clarifier.ask(initial_prompt)

        answered: List[str] = []
        for question in clarifications:
            answer = self._io.prompt(question)
            answered.append(f"Q: {question}\nA: {answer}")

        notes: List[str] = []
        plan = self._planner.create_plan(initial_prompt, clarifications, answered)

        while True:
            show_plan(plan)
            satisfied = self._io.confirm("Does this plan look complete?", default=True)
            if satisfied:
                break
            update = self._io.prompt(
                "Describe the adjustments needed (separate items with ';')."
            )
            revisions = [item.strip() for item in update.split(";") if item.strip()]
            if not revisions:
                self._io.notify("No actionable feedback captured; assuming approval.")
                break

            notes.extend(revisions)
            summary = self._feedback.summarize(revisions)
            self._io.notify(summary.acknowledgement)
            plan = self._planner.create_plan(initial_prompt, clarifications, answered + notes)

        if self._settings.dry_run:
            self._io.notify("Dry-run enabled; repository scaffolding skipped.")
            return None

        reviewer_notes = notes if notes else ["Plan approved without modifications."]
        project_path = self._executor.execute(plan, reviewer_notes=reviewer_notes)
        self._io.notify(f"Repository ready at: {project_path}")
        self._client.close()
        return project_path
