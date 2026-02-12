"""Pydantic models for API payloads."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


def _blank_to_none(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    return value or None


class CIConfig(BaseModel):
    workflow_name: str = Field(..., min_length=1, max_length=100)
    python_version: str = Field(..., pattern=r"^3\.[0-9]+$")
    run_tests: bool
    groq_api_endpoint: Optional[str] = None
    groq_api_key: Optional[str] = None

    _normalise_endpoint = field_validator("groq_api_endpoint", mode="before")(_blank_to_none)
    _normalise_key = field_validator("groq_api_key", mode="before")(_blank_to_none)


class DockerfileConfig(BaseModel):
    base_image: str = Field(..., min_length=3)
    expose_port: int = Field(..., ge=1, le=65535)
    copy_source: str = Field(..., min_length=1)
    work_dir: str = Field(..., min_length=1)
    groq_api_endpoint: Optional[str] = None
    groq_api_key: Optional[str] = None

    _normalise_endpoint = field_validator("groq_api_endpoint", mode="before")(_blank_to_none)
    _normalise_key = field_validator("groq_api_key", mode="before")(_blank_to_none)


class BuildData(BaseModel):
    build_id: str = Field(..., min_length=1)
    commit_hash: str = Field(..., min_length=1)
    files_changed: List[str] = Field(default_factory=list)
    tests_failed: bool
    coverage: float = Field(..., ge=0.0, le=100.0)


class BuildPredictRequest(BaseModel):
    model: Optional[str] = Field(default="llama3-8b-8192", min_length=1)
    groq_api_key: Optional[str] = None
    build_data: BuildData

    _normalise_key = field_validator("groq_api_key", mode="before")(_blank_to_none)


class StatusRequest(BaseModel):
    image_tag: str = Field(..., min_length=1)


class TrainingModule(BaseModel):
    id: str
    title: str
    phase: str
    duration_minutes: int
    objective: str


class LifecycleStage(BaseModel):
    id: str
    label: str
    description: str
    order: int


class PlanTaskInput(BaseModel):
    title: str = Field(..., min_length=3, max_length=120)
    phase: str = Field(..., min_length=2, max_length=60)
    risk_level: str = Field(..., pattern=r"^(low|medium|high)$")
    rationale: str = Field(..., min_length=10, max_length=500)


class PlanCreateRequest(BaseModel):
    workspace_id: str = Field(..., min_length=3, max_length=80)
    title: str = Field(..., min_length=3, max_length=120)
    objective: str = Field(..., min_length=10, max_length=500)
    tasks: List[PlanTaskInput] = Field(..., min_length=1, max_length=25)


class PlanCreateResponse(BaseModel):
    plan_id: str
    status: str


class RunTask(BaseModel):
    id: str
    title: str
    phase: str
    risk_level: str
    status: str
    rationale: str


class WorkflowRunResponse(BaseModel):
    run_id: str
    plan_id: str
    status: str
    tasks: List[RunTask]
    audit_events: List[dict]


class ApprovalRequest(BaseModel):
    task_id: str = Field(..., min_length=3)
    decision: str = Field(..., pattern=r"^(approve|reject)$")
    reason: str = Field(..., min_length=5, max_length=400)
