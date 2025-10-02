"""Tests for the planning workflow."""

from typing import Any, Iterable, Mapping

from game_builder_agent.planner import Planner


class FakeClient:
    def __init__(self, payload: Mapping[str, Any]) -> None:
        self._payload = payload

    def chat(self, messages: Iterable[Mapping[str, str]], *, temperature=None):
        return self._payload


def test_planner_parses_game_plan() -> None:
    payload = {
        "project_name": "stellar-sprint",
        "summary": "A fast-paced endless runner set in orbit.",
        "goals": ["Deliver MVG in 8 weeks"],
        "architecture": {
            "engine": "Kivy",
            "modules": ["core", "ui", "analytics"],
            "scalability": "Modular screens and service locator pattern",
        },
        "implementation_plan": [
            {
                "milestone": "Foundations",
                "description": "Core runner mechanics and physics tuning",
                "deliverables": ["Player controller", "Obstacle spawner"],
                "risks": ["Performance on low-end devices"],
                "mitigations": ["Profile with cProfile"],
            }
        ],
        "test_plan": {
            "levels": ["unit", "integration"],
            "automations": ["GitHub Actions"],
            "tooling": ["pytest", "pytest-benchmark"],
            "device_matrix": ["iPhone 12", "Pixel 6"],
        },
        "deployment_plan": {
            "tools": ["BeeWare"],
            "stages": ["internal", "beta", "store"],
            "store_readiness": "Prepare Play Store and App Store listings",
        },
        "ci_cd": {
            "pipelines": ["lint", "tests"],
            "quality_gates": ["ruff", "pytest"],
            "release_process": "Tag-driven release workflow",
        },
        "repository": {
            "root_structure": ["src", "tests", "assets"],
            "environments": ["dev", "ci"],
            "documentation": ["README.md", "CONTRIBUTING.md"],
        },
    }

    planner = Planner(FakeClient(payload))
    plan = planner.create_plan("runner", [], [])

    assert plan.project_name == "stellar-sprint"
    assert plan.architecture.engine == "Kivy"
    assert plan.implementation_plan[0].milestone == "Foundations"
