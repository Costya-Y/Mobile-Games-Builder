"""Tests for the clarification workflow."""

from typing import Iterable, Mapping

from game_builder_agent.clarifier import Clarifier


class FakeClient:
    def chat(self, messages: Iterable[Mapping[str, str]], *, temperature=None):
        recorded = list(messages)
        assert recorded[0]["role"] == "system"
        return {"questions": ["What genre?", "Preferred art style?"]}


def test_clarifier_parses_questions() -> None:
    clarifier = Clarifier(FakeClient())
    questions = clarifier.ask("Create a sci-fi adventure")
    assert questions == ["What genre?", "Preferred art style?"]
