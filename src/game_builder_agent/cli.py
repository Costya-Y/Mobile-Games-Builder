"""Command-line entrypoint for the Game Builder Agent."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from .config import load_settings
from .orchestrator import Orchestrator

console = Console()
app = typer.Typer(help="Plan and scaffold Python-based mobile game projects with Ollama.")


@app.command()
def run(
    prompt: Optional[str] = typer.Option(
        None,
        "--prompt",
        help="Initial vision brief for the game. If omitted, you'll be prompted interactively.",
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        help="Override the base directory where generated repositories will be created.",
    ),
    dry_run: bool = typer.Option(False, help="Plan only; skip repository scaffolding."),
) -> None:
    """Execute the agent end-to-end."""

    settings = load_settings()
    if output_dir is not None:
        settings = settings.model_copy(update={"output_root": output_dir})
    if dry_run:
        settings = settings.model_copy(update={"dry_run": True})

    console.print("[bold green]Python Mobile Game Builder[/bold green]")

    if prompt is None:
        prompt_text = typer.prompt("Describe the mobile game you want to create").strip()
    else:
        prompt_text = prompt.strip()

    orchestrator = Orchestrator(settings)
    try:
        orchestrator.run(prompt_text)
    except Exception as exc:  # pragma: no cover - top-level guard
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc


if __name__ == "__main__":  # pragma: no cover
    app()
