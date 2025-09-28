"""Tests for the execution layer."""

from pathlib import Path

from game_builder_agent.executor import FileArtifact, FileSystemWriter, _merge_with_scaffolding
from game_builder_agent.schemas import RepoBlueprint


def test_merge_with_scaffolding_adds_governance_files() -> None:
    blueprint = RepoBlueprint(
        project_slug="sample-game",
        primary_engine="Kivy",
        summary="Sample",
        files=[FileArtifact(path="src/main.py", content="# Main game")],
    )

    merged = _merge_with_scaffolding(blueprint)
    paths = {artifact.path for artifact in merged}

    assert ".github/workflows/ci.yml" in paths
    assert "CONTRIBUTING.md" in paths
    assert any(artifact.path == "src/main.py" for artifact in merged)


def test_file_system_writer_creates_files(tmp_path: Path) -> None:
    artifacts = [
        FileArtifact(path="src/app.py", content="print('hello')"),
        FileArtifact(path="README.md", content="Hello"),
    ]

    writer = FileSystemWriter(tmp_path)
    writer.write(artifacts)

    assert (tmp_path / "src" / "app.py").read_text(encoding="utf-8") == "print('hello')"
    assert (tmp_path / "README.md").exists()
