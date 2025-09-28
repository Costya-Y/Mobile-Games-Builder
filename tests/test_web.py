"""Integration smoke tests for the FastAPI web layer."""

from fastapi.testclient import TestClient

from game_builder_agent.schemas import (
    ArchitecturePlan,
    CICDPlan,
    DeploymentPlan,
    GamePlan,
    ImplementationMilestone,
    RepositoryPlan,
)
from game_builder_agent.schemas import (
    TestPlan as SchemaTestPlan,
)
from game_builder_agent.web import server


def sample_plan() -> GamePlan:
    return GamePlan(
        project_name="stellar-sprint",
        summary="A fast-paced endless runner.",
        goals=["Deliver MVP"],
        architecture=ArchitecturePlan(
            engine="Kivy",
            modules=["core", "ui"],
            scalability="Modular scenes",
        ),
        implementation_plan=[
            ImplementationMilestone(
                milestone="Foundations",
                description="Implement runner controls",
                deliverables=["Player controller"],
                risks=["Physics tuning"],
                mitigations=["Prototype quickly"],
            )
        ],
        test_plan=SchemaTestPlan(
            levels=["unit"],
            automations=["CI"],
            tooling=["pytest"],
            device_matrix=["Pixel 6"],
        ),
        deployment_plan=DeploymentPlan(
            tools=["BeeWare"],
            stages=["beta"],
            store_readiness="Prep listings",
        ),
        ci_cd=CICDPlan(
            pipelines=["lint"],
            quality_gates=["ruff"],
            release_process="Tag releases",
        ),
        repository=RepositoryPlan(
            root_structure=["src", "tests"],
            environments=["dev"],
            documentation=["README.md"],
        ),
    )


def test_web_flow(monkeypatch) -> None:
    clarifications = ["What is the art style?", "Preferred monetization?"]
    plan = sample_plan()

    monkeypatch.setattr(server, "_generate_clarifications", lambda settings, prompt: clarifications)
    monkeypatch.setattr(server, "_generate_plan", lambda settings, prompt, c, a, n: plan)
    monkeypatch.setattr(server, "_summarize_feedback", lambda settings, notes: "Noted adjustments.")
    monkeypatch.setattr(server, "_execute_plan", lambda settings, plan, reviewer_notes: "/tmp/repo")

    client = TestClient(server.app)

    create_resp = client.post("/api/sessions", json={"prompt": "Runner"})
    assert create_resp.status_code == 200
    payload = create_resp.json()
    session_id = payload["session_id"]
    assert payload["clarifications"] == clarifications

    answers_resp = client.post(
        f"/api/sessions/{session_id}/answers",
        json={"answers": ["Low-poly", "Season pass"]},
    )
    assert answers_resp.status_code == 200
    plan_payload = answers_resp.json()
    assert plan_payload["plan"]["project_name"] == "stellar-sprint"

    revise_resp = client.post(
        f"/api/sessions/{session_id}/revise",
        json={"notes": ["Add split-screen"]},
    )
    assert revise_resp.status_code == 200
    assert revise_resp.json()["last_acknowledgement"] == "Noted adjustments."

    approve_resp = client.post(f"/api/sessions/{session_id}/approve")
    assert approve_resp.status_code == 200
    assert approve_resp.json()["session"]["repo_path"] == "/tmp/repo"
