from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from agents.build_predictor_agent import BuildPredictorAgent, BuildPredictorConfig
from agents.build_status_agent import BuildStatusAgent, BuildStatusConfig
from agents.dockerfile_agent import DockerfileAgent, DockerfileConfig
from agents.github_actions_agent import GitHubActionsAgent, GitHubActionsConfig
from app import database
from app.main import app
from app.routers import devops


def test_github_actions_pipeline_includes_python_version_and_tests():
    agent = GitHubActionsAgent(
        GitHubActionsConfig(workflow_name="Test", python_version="3.12", run_tests=True)
    )
    pipeline = agent.generate_pipeline()
    assert "python-version: 3.12" in pipeline
    assert "pytest --maxfail=1" in pipeline


def test_dockerfile_agent_outputs_expected_commands():
    agent = DockerfileAgent(DockerfileConfig())
    dockerfile = agent.generate_dockerfile()
    assert "FROM nginx:alpine" in dockerfile
    assert "CMD [\"nginx\", \"-g\", \"daemon off;\"]" in dockerfile


def test_build_predictor_agent_risk_levels():
    agent = BuildPredictorAgent(BuildPredictorConfig())
    data = {
        "commit_hash": "abc123",
        "files_changed": ["a.py", "b.py"],
        "tests_failed": True,
        "coverage": 65.0,
        "last_build_status": "failed",
        "dependencies_updated": False,
        "dockerfile_exists": True,
        "ci_pipeline_exists": True,
    }
    result = agent.predict_build_failure(data)
    assert result["status"] == "success"
    assert result["prediction"]["risk_level"] == "high"


def test_build_status_agent_handles_missing_docker(monkeypatch):
    monkeypatch.setattr("agents.build_status_agent.shutil.which", lambda _: None)
    agent = BuildStatusAgent(BuildStatusConfig(image_tag="demo:latest"))
    assert "Docker CLI not available" in agent.check_build_status()


@pytest.fixture
def client(monkeypatch):
    memory_db = database.InMemorySupabaseClient()
    monkeypatch.setattr(devops, "supabase", memory_db, raising=False)
    return TestClient(app)


def test_generate_ci_endpoint(client):
    payload = {
        "workflow_name": "CI",
        "python_version": "3.12",
        "run_tests": True,
        "groq_api_endpoint": "https://api.example.com",
        "groq_api_key": "dummy",
    }
    response = client.post("/devops/generate-ci", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "pipeline_yaml" in data
    assert data["pipeline_yaml"].startswith("name: CI")


def test_predict_build_endpoint(client):
    payload = {
        "model": "heuristic",
        "groq_api_key": "",
        "build_data": {
            "build_id": "build-1",
            "commit_hash": "abc",
            "files_changed": ["main.py"],
            "tests_failed": False,
            "coverage": 95.0,
        },
    }
    response = client.post("/devops/predict-build", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["prediction"]["status"] in {"success", "degraded"}


def test_invalid_python_version_rejected(client):
    payload = {"workflow_name": "CI", "python_version": "2.7", "run_tests": True}
    response = client.post("/devops/generate-ci", json=payload)
    assert response.status_code == 422


def test_check_build_status_endpoint(client, monkeypatch):
    monkeypatch.setattr("agents.build_status_agent.shutil.which", lambda _: None)
    response = client.post("/devops/check-build-status", json={"image_tag": "demo:latest"})
    assert response.status_code == 200
    assert "Docker CLI not available" in response.json()["status"]


def test_health_endpoints(client):
    health = client.get("/healthz")
    ready = client.get("/readyz")

    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
    assert ready.status_code == 200
    assert ready.json() == {"status": "ready"}


def test_metrics_endpoint(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text


def test_request_id_header_present(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
