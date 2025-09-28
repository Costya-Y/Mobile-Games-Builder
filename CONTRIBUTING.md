# Contributing

Thanks for your interest in improving the Game Builder Agent!

## Getting Started

1. Install [uv](https://github.com/astral-sh/uv) or use a Python virtual environment.
2. Install dependencies:
   ```bash
   uv pip install --system --no-cache-dir .[dev]
   ```
3. Run the test suite before committing:
   ```bash
   uv tool run ruff check src tests
   uv tool run pytest
   ```

## Development Workflow

- Create feature branches from `main`.
- Ensure linting and tests pass before opening a pull request.
- Use the provided PR template. At least one review is required.

## Releases

- Increment the version in `pyproject.toml` and `src/game_builder_agent/version.py`.
- Tag the commit (`vMAJOR.MINOR.PATCH`); the release workflow will build artifacts automatically.

## Communication

- Bug reports: open a GitHub issue.
- Security concerns: follow the instructions in `SECURITY.md`.
