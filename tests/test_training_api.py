from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def _make_plan(client: TestClient) -> str:
    payload = {
        "workspace_id": "ws-devops",
        "title": "Ship Inventory API Safely",
        "objective": "Plan and execute a safe release with approvals and observability.",
        "tasks": [
            {
                "title": "Design deployment strategy",
                "phase": "Plan",
                "risk_level": "low",
                "rationale": "Baseline deployment strategy aligns rollout and rollback constraints.",
            },
            {
                "title": "Production deploy",
                "phase": "CI/CD",
                "risk_level": "high",
                "rationale": "Production changes require approval to enforce least-risk release controls.",
            },
        ],
    }
    resp = client.post("/training/plans", json=payload)
    assert resp.status_code == 201
    return resp.json()["plan_id"]


def test_lifecycle_and_modules_endpoints() -> None:
    client = TestClient(app)

    lifecycle = client.get("/training/lifecycle")
    assert lifecycle.status_code == 200
    assert len(lifecycle.json()) >= 5

    modules = client.get("/training/modules")
    assert modules.status_code == 200
    assert len(modules.json()) >= 3


def test_plan_execution_requires_approval_then_completes() -> None:
    client = TestClient(app)
    plan_id = _make_plan(client)

    run_resp = client.post(f"/training/plans/{plan_id}/execute")
    assert run_resp.status_code == 200
    run_data = run_resp.json()
    assert run_data["status"] == "pending_approval"

    pending_task = next(task for task in run_data["tasks"] if task["status"] == "pending_approval")

    approve_resp = client.post(
        f"/training/runs/{run_data['run_id']}/approval",
        json={"task_id": pending_task["id"], "decision": "approve", "reason": "Validated canary checks"},
    )
    assert approve_resp.status_code == 200
    approved_data = approve_resp.json()
    assert approved_data["status"] == "succeeded"


def test_approval_reject_marks_run_failed() -> None:
    client = TestClient(app)
    plan_id = _make_plan(client)

    run_resp = client.post(f"/training/plans/{plan_id}/execute")
    run_data = run_resp.json()
    pending_task = next(task for task in run_data["tasks"] if task["status"] == "pending_approval")

    reject_resp = client.post(
        f"/training/runs/{run_data['run_id']}/approval",
        json={"task_id": pending_task["id"], "decision": "reject", "reason": "Failed pre-deploy checks"},
    )
    assert reject_resp.status_code == 200
    assert reject_resp.json()["status"] == "failed"
