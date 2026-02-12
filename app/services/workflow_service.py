"""In-memory orchestration/training workflow service for MVP simulation."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Literal
from uuid import uuid4

TaskStatus = Literal["pending", "running", "pending_approval", "succeeded", "failed"]
RunStatus = Literal["draft", "running", "pending_approval", "succeeded", "failed"]
Decision = Literal["approve", "reject"]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class TaskRecord:
    id: str
    title: str
    phase: str
    risk_level: str
    status: TaskStatus = "pending"
    rationale: str = ""


@dataclass
class PlanRecord:
    id: str
    workspace_id: str
    title: str
    objective: str
    tasks: List[TaskRecord]
    created_at: str = field(default_factory=_utc_now)


@dataclass
class RunRecord:
    id: str
    plan_id: str
    status: RunStatus
    tasks: List[TaskRecord]
    audit_events: List[Dict[str, Any]]
    created_at: str = field(default_factory=_utc_now)
    updated_at: str = field(default_factory=_utc_now)


class WorkflowService:
    def __init__(self) -> None:
        self._lock = Lock()
        self._plans: Dict[str, PlanRecord] = {}
        self._runs: Dict[str, RunRecord] = {}

    def create_plan(self, workspace_id: str, title: str, objective: str, tasks: List[Dict[str, str]]) -> PlanRecord:
        plan_id = str(uuid4())
        normalized_tasks = [
            TaskRecord(
                id=str(uuid4()),
                title=item["title"],
                phase=item["phase"],
                risk_level=item["risk_level"],
                rationale=item["rationale"],
            )
            for item in tasks
        ]
        plan = PlanRecord(
            id=plan_id,
            workspace_id=workspace_id,
            title=title,
            objective=objective,
            tasks=normalized_tasks,
        )
        with self._lock:
            self._plans[plan_id] = plan
        return plan

    def execute_plan(self, plan_id: str) -> RunRecord:
        with self._lock:
            plan = self._plans.get(plan_id)
            if not plan:
                raise KeyError("plan_not_found")

            run_id = str(uuid4())
            tasks = [
                TaskRecord(
                    id=t.id,
                    title=t.title,
                    phase=t.phase,
                    risk_level=t.risk_level,
                    status="pending",
                    rationale=t.rationale,
                )
                for t in plan.tasks
            ]
            run = RunRecord(id=run_id, plan_id=plan_id, status="running", tasks=tasks, audit_events=[])
            self._runs[run_id] = run
            self._append_event(run, "run_created", {"plan_id": plan_id})
            self._progress_run_locked(run)
            return run

    def get_run(self, run_id: str) -> RunRecord:
        with self._lock:
            run = self._runs.get(run_id)
            if not run:
                raise KeyError("run_not_found")
            return run

    def submit_approval(self, run_id: str, task_id: str, decision: Decision, reason: str) -> RunRecord:
        with self._lock:
            run = self._runs.get(run_id)
            if not run:
                raise KeyError("run_not_found")

            target = next((task for task in run.tasks if task.id == task_id), None)
            if not target:
                raise KeyError("task_not_found")
            if target.status != "pending_approval":
                raise ValueError("task_not_waiting_approval")

            self._append_event(
                run,
                "approval_decision",
                {"task_id": task_id, "decision": decision, "reason": reason},
            )
            if decision == "reject":
                target.status = "failed"
                run.status = "failed"
                run.updated_at = _utc_now()
                self._append_event(run, "run_failed", {"task_id": task_id, "reason": reason})
                return run

            target.status = "succeeded"
            run.status = "running"
            run.updated_at = _utc_now()
            self._append_event(run, "task_resumed", {"task_id": task_id})
            self._progress_run_locked(run)
            return run

    def _progress_run_locked(self, run: RunRecord) -> None:
        for task in run.tasks:
            if task.status in {"succeeded", "failed"}:
                continue

            task.status = "running"
            self._append_event(run, "task_started", {"task_id": task.id, "title": task.title})
            if task.risk_level == "high":
                task.status = "pending_approval"
                run.status = "pending_approval"
                run.updated_at = _utc_now()
                self._append_event(run, "approval_required", {"task_id": task.id, "phase": task.phase})
                return

            task.status = "succeeded"
            self._append_event(run, "task_succeeded", {"task_id": task.id, "phase": task.phase})

        run.status = "succeeded"
        run.updated_at = _utc_now()
        self._append_event(run, "run_succeeded", {"run_id": run.id})

    def _append_event(self, run: RunRecord, event_type: str, payload: Dict[str, Any]) -> None:
        run.audit_events.append(
            {
                "event_id": str(uuid4()),
                "event_type": event_type,
                "timestamp": _utc_now(),
                "payload": payload,
            }
        )


workflow_service = WorkflowService()
