from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class TaskSpec(BaseModel):
    title: str
    objective: str
    constraints: list[str] = Field(default_factory=list)
    target_stack: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)


class PlanStep(BaseModel):
    id: str
    goal: str
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    risk: str


class ArchitectureSpec(BaseModel):
    summary: str
    modules: list[str] = Field(default_factory=list)
    data_flow: list[str] = Field(default_factory=list)
    file_structure: list[str] = Field(default_factory=list)
    plan: list[PlanStep] = Field(default_factory=list)


class AgentOutput(BaseModel):
    role: str
    summary: str
    decisions: list[str] = Field(default_factory=list)
    artifacts_to_create: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    prompt: str = ""
    raw_response: str = ""


class GeneratedFile(BaseModel):
    path: str
    content: str
    purpose: str


class ValidationResult(BaseModel):
    command: str
    success: bool
    stdout: str = ""
    stderr: str = ""
    artifacts_found: list[str] = Field(default_factory=list)


class JudgeReport(BaseModel):
    pass_status: bool
    missing_requirements: list[str] = Field(default_factory=list)
    suggested_fixes: list[str] = Field(default_factory=list)
    final_summary: str
    prompt: str = ""
    raw_response: str = ""


class RunMetadata(BaseModel):
    schema_version: int = 2
    mode: Literal["api", "mock_test"]
    started_at: str
    finished_at: str
    provider: dict[str, str] | None = None

