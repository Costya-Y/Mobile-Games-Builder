# Game Builder Agent

An automated assistant that uses [Ollama](https://ollama.com) to plan and scaffold end-to-end Python
mobile game projects. Provide a high-level pitch and the agent will clarify requirements, craft an
architecture-aware delivery plan, and materialize a ready-to-commit GitHub repository complete with
CI/CD pipelines, pull-request governance, and release automation.

## Features

- Clarifies ambiguous requirements with up to three targeted questions.
- Produces detailed delivery plans covering architecture, testing, deployment, and operations.
- Generates repository structures tailored for scalable teams, including docs and workflows.
- Creates GitHub-ready CI/CD (lint/test), release automation, PR templates, and CODEOWNERS files.
- Supports iterative feedback loops—adjust the plan before code generation, or re-run with new
  guidance at any time.
- Outputs production-ready Python projects leveraging mobile-friendly frameworks such as Kivy or
  BeeWare (model dependent).

## Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com) running locally with a suitable model (e.g., `llama3`).
- Recommended: [uv](https://github.com/astral-sh/uv) for fast dependency management.

## Installation

```bash
uv pip install --system --no-cache-dir .[dev]
```

If you prefer `pip`, run `pip install -e '.[dev]'` inside a virtual environment.

## Usage

```bash
game-builder-agent run --prompt "Create a cozy farming sim with seasonal events"
```

You can omit `--prompt` to enter the idea interactively. The agent will:

1. Ask follow-up questions.
2. Present an execution plan and repository blueprint.
3. Request approval or further edits.
4. Generate a fully structured repository under `generated_projects/` (or `--output-dir`).

Set `AGENT_DRY_RUN=1` to skip file generation while reviewing plans.

## Configuration

| Environment Variable   | Description                                      | Default                 |
| ---------------------- | ------------------------------------------------ | ----------------------- |
| `OLLAMA_BASE_URL`      | Ollama API endpoint                              | `http://localhost:11434`|
| `OLLAMA_MODEL`         | Model name used for all prompts                  | `llama3`                |
| `OLLAMA_TEMPERATURE`   | Sampling temperature for completions             | `0.2`                   |
| `AGENT_OUTPUT_ROOT`    | Root directory for generated repositories        | `generated_projects/`   |
| `AGENT_DRY_RUN`        | If truthy, skip repository creation              | `false`                 |

## Project Structure

```
src/game_builder_agent/
├── clarifier.py      # Clarification question workflow
├── executor.py       # Blueprint execution and scaffolding
├── feedback.py       # Feedback acknowledgment helpers
├── llm_client.py     # Ollama chat client
├── orchestrator.py   # End-to-end coordination
├── planner.py        # Delivery plan generation
├── presenter.py      # Rich console presenters
├── prompts.py        # Prompt templates shared by the agent
└── schemas.py        # Pydantic data models
```

## Development

- Lint: `ruff check src tests`
- Format: `ruff format src tests`
- Test: `pytest`

A GitHub Actions workflow (`.github/workflows/ci.yml`) runs lint and tests on pull requests. A
separate release workflow packages the project when tags are pushed.

## Security

Report vulnerabilities to `security@example.com`. See `SECURITY.md` for details.

## License

Released under the MIT License. See `LICENSE`.
