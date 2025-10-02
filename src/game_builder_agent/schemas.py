"""Pydantic data structures describing the agent's domain objects."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class ClarificationResponse(BaseModel):
    questions: List[str] = Field(default_factory=list, max_length=3)


class ArchitecturePlan(BaseModel):
    engine: str
    modules: List[str] = Field(default_factory=list)
    scalability: str


class ImplementationMilestone(BaseModel):
    milestone: str
    description: str
    deliverables: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    mitigations: List[str] = Field(default_factory=list)


class TestPlan(BaseModel):
    levels: List[str] = Field(default_factory=list)
    automations: List[str] = Field(default_factory=list)
    tooling: List[str] = Field(default_factory=list)
    device_matrix: List[str] = Field(default_factory=list)


class DeploymentPlan(BaseModel):
    tools: List[str] = Field(default_factory=list)
    stages: List[str] = Field(default_factory=list)
    store_readiness: str


class CICDPlan(BaseModel):
    pipelines: List[str] = Field(default_factory=list)
    quality_gates: List[str] = Field(default_factory=list)
    release_process: str


class RepositoryPlan(BaseModel):
    root_structure: List[str] = Field(default_factory=list)
    environments: List[str] = Field(default_factory=list)
    documentation: List[str] = Field(default_factory=list)


class GamePlan(BaseModel):
    project_name: str
    summary: str
    goals: List[str] = Field(default_factory=list)
    architecture: ArchitecturePlan
    implementation_plan: List[ImplementationMilestone] = Field(default_factory=list)
    test_plan: TestPlan
    deployment_plan: DeploymentPlan
    ci_cd: CICDPlan
    repository: RepositoryPlan


class FileArtifact(BaseModel):
    path: str
    content: str
    executable: bool = False


class RepoBlueprint(BaseModel):
    project_slug: str
    primary_engine: str
    summary: str
    files: List[FileArtifact] = Field(default_factory=list)
    post_generation: List[str] = Field(default_factory=list)


class FeedbackSummary(BaseModel):
    acknowledgement: str
    next_steps: Optional[str] = None


class TestSuite(BaseModel):
    summary: str
    unit_tests: List[str] = Field(default_factory=list)
    end_to_end_tests: List[str] = Field(default_factory=list)
    performance_tests: List[str] = Field(default_factory=list)
    files: List[FileArtifact] = Field(default_factory=list)


class PerformanceReport(BaseModel):
    summary: str
    metrics: List[str] = Field(default_factory=list)
    bottlenecks: List[str] = Field(default_factory=list)
    remediation_steps: List[str] = Field(default_factory=list)
    patches: List[FileArtifact] = Field(default_factory=list)
