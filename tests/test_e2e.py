"""End-to-end automation test powered by a live Ollama instance."""

from __future__ import annotations

from typing import List

import ollama
import pytest

from game_builder_agent.config import load_settings
from game_builder_agent.orchestrator import Orchestrator


def _ollama_available() -> bool:
    try:
        client = ollama.Client()
        client.list()
        return True
    except Exception:  # pragma: no cover - network check
        return False


class AutomatedInteraction:
    """Implements the ``InteractionPort`` protocol with canned answers."""

    def __init__(self) -> None:
        self.questions: List[str] = []
        self.notifications: List[str] = []
        self.confirmations: List[bool] = []

    def prompt(self, message: str) -> str:
        self.questions.append(message)
        return "Automated response for testing."

    def confirm(self, message: str, *, default: bool = False) -> bool:
        self.confirmations.append(True)
        return True

    def notify(self, message: str) -> None:
        self.notifications.append(message)


OLLAMA_SKIP_REASON = "Ollama service is not reachable at default host"


@pytest.mark.e2e
@pytest.mark.skipif(not _ollama_available(), reason=OLLAMA_SKIP_REASON)
def test_end_to_end_automation(tmp_path, monkeypatch) -> None:
    prompt = (
        "Automation smoke test. Respond with concise, valid JSON following the schemas. "
        "Focus on a minimal single-player mobile concept and keep outputs short."
    )

    monkeypatch.setenv("AGENT_OUTPUT_ROOT", str(tmp_path))
    monkeypatch.setenv("AGENT_DRY_RUN", "1")

    plans: List = []
    monkeypatch.setattr(
        "game_builder_agent.orchestrator.show_plan",
        lambda plan: plans.append(plan),
    )

    settings = load_settings()
    orchestrator = Orchestrator(settings, io=AutomatedInteraction())
    result = None

    result = orchestrator.run(prompt)


    assert result is None, "Dry-run mode should not materialize a repository"
    assert plans, "Planner should have produced at least one plan"
    final_plan = plans[-1]

    assert final_plan.project_name, "Plan must include a project name"
    assert final_plan.summary, "Plan must include a summary"
    assert final_plan.implementation_plan, "Plan must include implementation milestones"
    assert final_plan.ci_cd.pipelines, "Plan must specify CI/CD pipelines"
