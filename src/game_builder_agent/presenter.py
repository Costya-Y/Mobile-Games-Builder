"""Pretty-print helpers for plans and summaries."""

from __future__ import annotations

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from .schemas import GamePlan

console = Console()


def show_header(title: str, subtitle: str | None = None) -> None:
    text = f"# {title}\n\n{subtitle or ''}"
    console.print(Panel(Markdown(text), expand=False))


def show_plan(plan: GamePlan) -> None:
    header = f"# {plan.project_name}\n\n{plan.summary}"
    console.print(Markdown(header))

    goals = "\n".join(f"- {goal}" for goal in plan.goals)
    console.print(Markdown(f"## Goals\n\n{goals}"))

    architecture_lines = [
        f"- Engine: {plan.architecture.engine}",
        "- Modules:",
        *[f"  - {module}" for module in plan.architecture.modules],
        f"- Scalability: {plan.architecture.scalability}",
    ]
    console.print(Markdown("## Architecture\n\n" + "\n".join(architecture_lines)))

    sections: list[str] = []
    for milestone in plan.implementation_plan:
        deliverables = "\n".join(f"- {deliverable}" for deliverable in milestone.deliverables) or "- TBD"
        section = (
            f"### {milestone.milestone}\n\n{milestone.description}\n\n{deliverables}\n"
        )
        sections.append(section)
    impl_md = "\n\n".join(sections) if sections else "Implementation details pending."
    console.print(Markdown("## Delivery Plan\n\n" + impl_md))

    test_plan_md = "\n".join(
        [
            f"- Levels: {', '.join(plan.test_plan.levels)}",
            f"- Automation: {', '.join(plan.test_plan.automations)}",
            f"- Tooling: {', '.join(plan.test_plan.tooling)}",
            f"- Device Matrix: {', '.join(plan.test_plan.device_matrix)}",
        ]
    )
    console.print(Markdown("## Test Strategy\n\n" + test_plan_md))

    deployment_md = "\n".join(
        [
            f"- Tools: {', '.join(plan.deployment_plan.tools)}",
            f"- Stages: {', '.join(plan.deployment_plan.stages)}",
            f"- Store Readiness: {plan.deployment_plan.store_readiness}",
        ]
    )
    console.print(Markdown("## Deployment\n\n" + deployment_md))

    cicd_md = "\n".join(
        [
            f"- Pipelines: {', '.join(plan.ci_cd.pipelines)}",
            f"- Quality Gates: {', '.join(plan.ci_cd.quality_gates)}",
            f"- Release Process: {plan.ci_cd.release_process}",
        ]
    )
    console.print(Markdown("## CI/CD\n\n" + cicd_md))

    repo_md = "\n".join(
        [
            f"- Root Structure: {', '.join(plan.repository.root_structure)}",
            f"- Environments: {', '.join(plan.repository.environments)}",
            f"- Documentation: {', '.join(plan.repository.documentation)}",
        ]
    )
    console.print(Markdown("## Repository\n\n" + repo_md))
