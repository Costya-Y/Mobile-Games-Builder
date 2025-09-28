"""Abstractions over interactive input/output."""

from __future__ import annotations

from typing import Protocol

import typer
from rich.console import Console


class InteractionPort(Protocol):
    def prompt(self, message: str) -> str: ...

    def confirm(self, message: str, *, default: bool = False) -> bool: ...

    def notify(self, message: str) -> None: ...


class ConsoleInteraction(InteractionPort):
    def __init__(self, console: Console | None = None) -> None:
        self._console = console or Console()

    def prompt(self, message: str) -> str:
        return typer.prompt(message).strip()

    def confirm(self, message: str, *, default: bool = False) -> bool:
        return typer.confirm(message, default=default)

    def notify(self, message: str) -> None:
        self._console.print(message)
