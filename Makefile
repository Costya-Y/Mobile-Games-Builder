PYTHON ?= python
UV ?= uv

.PHONY: install lint test format run

install:
	$(UV) pip install --system --no-cache-dir .[dev]

lint:
	$(UV) tool run ruff check src tests

format:
	$(UV) tool run ruff format src tests

test:
	$(UV) tool run pytest

run:
	$(PYTHON) -m game_builder_agent.cli run
