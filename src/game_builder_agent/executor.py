"""Repository execution layer that turns plans into concrete files."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable, List

from rich.console import Console
from rich.table import Table

from .config import Settings
from .llm_client import ChatClient, OllamaClient
from .prompts import BLUEPRINT_SYSTEM_PROMPT
from .schemas import FileArtifact, GamePlan, RepoBlueprint

console = Console()


class ExecutionError(RuntimeError):
    pass


class BlueprintBuilder:
    def __init__(self, client: ChatClient) -> None:
        self._client = client

    def create_blueprint(self, plan: GamePlan, additional_context: Iterable[str]) -> RepoBlueprint:
        context_text = "\n".join(additional_context)
        messages = [
            {"role": "system", "content": BLUEPRINT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps(plan.model_dump(mode="json"), indent=2),
            },
            {
                "role": "user",
                "content": (
                    "Incorporate the following operator notes as authoritative overrides"
                    " if provided.\n"
                    f"Notes:\n{context_text or 'None'}"
                ),
            },
        ]

        raw = self._client.chat(messages)
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ExecutionError("LLM blueprint response was not valid JSON") from exc

        return RepoBlueprint.model_validate(payload)


class FileSystemWriter:
    """Materializes file artifacts onto disk."""

    def __init__(self, root: Path) -> None:
        self._root = root

    def write(self, files: Iterable[FileArtifact]) -> None:
        for artifact in files:
            destination = self._root / artifact.path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(artifact.content, encoding="utf-8")
            if artifact.executable:
                current_mode = destination.stat().st_mode
                destination.chmod(current_mode | 0o111)


def display_blueprint(blueprint: RepoBlueprint) -> None:
    table = Table(title="Repository Blueprint Preview")
    table.add_column("Path", overflow="fold")
    table.add_column("Executable", justify="center")
    table.add_column("Preview", overflow="fold")

    for artifact in blueprint.files[:12]:
        preview = artifact.content[:240] + ("…" if len(artifact.content) > 240 else "")
        table.add_row(artifact.path, "✅" if artifact.executable else "", preview)

    console.print(table)

    if len(blueprint.files) > 12:
        console.print(f"…and {len(blueprint.files) - 12} more files")


class PlanExecutor:
    """Coordinates blueprint generation and filesystem writes."""

    def __init__(self, settings: Settings, client: OllamaClient) -> None:
        self._settings = settings
        self._client = client
        self._blueprint_builder = BlueprintBuilder(client)

    def execute(self, plan: GamePlan, *, reviewer_notes: Iterable[str]) -> Path:
        blueprint = self._blueprint_builder.create_blueprint(plan, reviewer_notes)
        display_blueprint(blueprint)

        project_root = self._settings.output_root / blueprint.project_slug
        project_root.mkdir(parents=True, exist_ok=True)

        writer = FileSystemWriter(project_root)
        writer.write(_merge_with_scaffolding(blueprint))

        _write_supporting_files(project_root, plan)

        return project_root


def _merge_with_scaffolding(blueprint: RepoBlueprint) -> List[FileArtifact]:
    """Inject essential governance files if the blueprint omitted them."""

    required: dict[str, FileArtifact] = {
        ".github/workflows/ci.yml": FileArtifact(
            path=".github/workflows/ci.yml",
            content=_ci_workflow_contents(),
        ),
        ".github/workflows/release.yml": FileArtifact(
            path=".github/workflows/release.yml",
            content=_release_workflow_contents(),
        ),
        ".github/pull_request_template.md": FileArtifact(
            path=".github/pull_request_template.md",
            content=_pull_request_template(),
        ),
        "CODEOWNERS": FileArtifact(
            path="CODEOWNERS",
            content="# Default code owners\n*       @game-core-team\n",
        ),
        "CONTRIBUTING.md": FileArtifact(
            path="CONTRIBUTING.md",
            content=_contributing_md(),
        ),
    }

    existing_paths = {artifact.path for artifact in blueprint.files}
    merged = list(blueprint.files)

    for path, artifact in required.items():
        if path not in existing_paths:
            merged.append(artifact)

    return merged


def _write_supporting_files(project_root: Path, plan: GamePlan) -> None:
    readme_path = project_root / "README.md"
    if not readme_path.exists():
        readme_path.write_text(_generate_readme(plan), encoding="utf-8")

    license_path = project_root / "LICENSE"
    if not license_path.exists():
        license_path.write_text(_mit_license_text(), encoding="utf-8")

    security_path = project_root / "SECURITY.md"
    if not security_path.exists():
        security_path.write_text(_security_md(), encoding="utf-8")


def _ci_workflow_contents() -> str:
    return """name: CI

on:
  push:
    branches: [ main ]
  pull_request:

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install uv
        uses: astral-sh/setup-uv@v1
      - name: Install dependencies
        run: |
          uv pip install --system --no-cache-dir .[dev]
      - name: Lint
        run: |
          uv tool run ruff check src tests
      - name: Test
        run: |
          uv tool run pytest
"""


def _release_workflow_contents() -> str:
    return """name: Release

on:
  workflow_dispatch:
  push:
    tags:
      - 'v*.*.*'

jobs:
  build-and-publish:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install uv
        uses: astral-sh/setup-uv@v1
      - name: Build package
        run: |
          uv pip install --system --no-cache-dir build
          python -m build
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/
"""


def _pull_request_template() -> str:
    return """## Summary
- [ ] Feature complete
- [ ] Tests updated/added
- [ ] Docs updated (README, ADRs, etc.)

## Testing
```
# paste the exact commands you ran and their output
```

## Risk & Rollout
- Impact radius:
- Rollback plan:
- Monitoring/alerts:
"""


def _contributing_md() -> str:
    return """# Contributing Guide

## Development Environment

We recommend [uv](https://github.com/astral-sh/uv) for environment management. Once installed,
run:

```
uv pip install --system --no-cache-dir .[dev]
```

## Branching and Pull Requests
- Create feature branches from `main`.
- Ensure `ruff` and `pytest` pass locally.
- Submit PRs with the provided template. Reviews require at least one approval.

## Release Management
- Bump the version in `pyproject.toml` and `src/game_builder_agent/version.py`.
- Tag releases using `vMAJOR.MINOR.PATCH`.
- The release workflow will publish build artifacts automatically.
"""


def _generate_readme(plan: GamePlan) -> str:
    implementation_rows = "\n".join(
        f"- **{milestone.milestone}**: {milestone.description}"
        for milestone in plan.implementation_plan
    )
    goals = "\n".join(f"- {goal}" for goal in plan.goals) or "- TBD"

    return f"""# {plan.project_name}

{plan.summary}

## Goals
{goals}

## Architecture Overview
- Engine: {plan.architecture.engine}
- Key Modules:
{os.linesep.join(f'  - {module}' for module in plan.architecture.modules) or '  - TBD'}
- Scalability: {plan.architecture.scalability}

## Delivery Phases
{implementation_rows or 'Plan pending update.'}

## Test Strategy
- Levels: {', '.join(plan.test_plan.levels)}
- Automation: {', '.join(plan.test_plan.automations)}
- Tooling: {', '.join(plan.test_plan.tooling)}
- Device Matrix: {', '.join(plan.test_plan.device_matrix)}

## Deployment & Release
- Tools: {', '.join(plan.deployment_plan.tools)}
- Stages: {', '.join(plan.deployment_plan.stages)}
- Store Readiness: {plan.deployment_plan.store_readiness}

## CI/CD
- Pipelines: {', '.join(plan.ci_cd.pipelines)}
- Quality Gates: {', '.join(plan.ci_cd.quality_gates)}
- Release Process: {plan.ci_cd.release_process}

## Post-Generation Tasks
- Install dependencies using `uv pip install --system --no-cache-dir .[dev]`.
- Run `pytest` and `ruff check` to validate the project.
- Configure store credentials and analytics keys before first release.
"""


def _mit_license_text() -> str:
    return """MIT License

Copyright (c) 2025 Game Builder

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
associated documentation files (the "Software"), to deal in the Software without restriction,
including without limitation the rights to use, copy, modify, merge, publish, distribute,
sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial
portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT
OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""


def _security_md() -> str:
    return """# Security Policy

## Reporting a Vulnerability

Please email security@example.com with details and reproduction steps. We aim to respond within 2
business days.

## Supported Versions

We support the latest released version. Patch releases will be provided as needed.
"""
