"""Training + orchestration simulation routes for DevOps learner workflows."""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, status

from app.schemas import (
    ApprovalRequest,
    LifecycleStage,
    PlanCreateRequest,
    PlanCreateResponse,
    TrainingModule,
    WorkflowRunResponse,
)
from app.services.workflow_service import workflow_service

router = APIRouter(prefix="/training", tags=["Training"])

LIFECYCLE_STAGES: List[LifecycleStage] = [
    LifecycleStage(id="intake", label="Intake", description="Collect goals, constraints, and context", order=1),
    LifecycleStage(id="plan", label="Plan", description="Build validated execution graph", order=2),
    LifecycleStage(id="develop", label="Develop", description="Implement and review code changes", order=3),
    LifecycleStage(id="cicd", label="CI/CD", description="Validate, package, and release safely", order=4),
    LifecycleStage(id="observe", label="Observe", description="Monitor SLOs, logs, metrics, traces", order=5),
    LifecycleStage(id="improve", label="Improve", description="Run postmortems and iterate", order=6),
]

TRAINING_MODULES: List[TrainingModule] = [
    TrainingModule(
        id="m1",
        title="From Requirement to Release Plan",
        phase="Plan",
        duration_minutes=25,
        objective="Transform ambiguous requirements into risk-aware executable tasks.",
    ),
    TrainingModule(
        id="m2",
        title="CI Pipeline Reliability Fundamentals",
        phase="CI/CD",
        duration_minutes=30,
        objective="Build deterministic lint/test/build/scan gates with rollback-aware releases.",
    ),
    TrainingModule(
        id="m3",
        title="Incident Triage and Fast Recovery",
        phase="Observe",
        duration_minutes=20,
        objective="Practice response flow: detect, diagnose, mitigate, and document RCA.",
    ),
]


def _serialize_run(run: Any) -> Dict[str, Any]:
    return {
        "run_id": run.id,
        "plan_id": run.plan_id,
        "status": run.status,
        "tasks": [
            {
                "id": task.id,
                "title": task.title,
                "phase": task.phase,
                "risk_level": task.risk_level,
                "status": task.status,
                "rationale": task.rationale,
            }
            for task in run.tasks
        ],
        "audit_events": run.audit_events,
    }


@router.get("/lifecycle", response_model=List[LifecycleStage])
async def get_lifecycle() -> List[LifecycleStage]:
    return LIFECYCLE_STAGES


@router.get("/modules", response_model=List[TrainingModule])
async def list_modules() -> List[TrainingModule]:
    return TRAINING_MODULES


@router.post("/plans", response_model=PlanCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(payload: PlanCreateRequest) -> PlanCreateResponse:
    plan = workflow_service.create_plan(
        workspace_id=payload.workspace_id,
        title=payload.title,
        objective=payload.objective,
        tasks=[task.model_dump() for task in payload.tasks],
    )
    return PlanCreateResponse(plan_id=plan.id, status="draft")


@router.post("/plans/{plan_id}/execute", response_model=WorkflowRunResponse)
async def execute_plan(plan_id: str) -> WorkflowRunResponse:
    try:
        run = workflow_service.execute_plan(plan_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found") from exc

    return WorkflowRunResponse(**_serialize_run(run))


@router.get("/runs/{run_id}", response_model=WorkflowRunResponse)
async def get_run(run_id: str) -> WorkflowRunResponse:
    try:
        run = workflow_service.get_run(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found") from exc

    return WorkflowRunResponse(**_serialize_run(run))


@router.post("/runs/{run_id}/approval", response_model=WorkflowRunResponse)
async def resolve_approval(run_id: str, payload: ApprovalRequest) -> WorkflowRunResponse:
    try:
        run = workflow_service.submit_approval(
            run_id=run_id,
            task_id=payload.task_id,
            decision=payload.decision,
            reason=payload.reason,
        )
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run or task not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Task not awaiting approval") from exc

    return WorkflowRunResponse(**_serialize_run(run))
