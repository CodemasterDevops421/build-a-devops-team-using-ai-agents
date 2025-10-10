"""Entry point orchestrating the DevOps AI helper agents."""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any

from dotenv import load_dotenv

from agents.github_actions_agent import GitHubActionsAgent, GitHubActionsConfig
from agents.dockerfile_agent import DockerfileAgent, DockerfileConfig
from agents.build_predictor_agent import BuildPredictorAgent, BuildPredictorConfig
from agents.build_status_agent import BuildStatusAgent, BuildStatusConfig


load_dotenv()


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _build_docker_image(image_tag: str) -> str:
    if not shutil.which("docker"):
        return "Docker CLI not available; build skipped."

    result = subprocess.run(
        ["docker", "build", "-t", image_tag, "."],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode == 0:
        return "Docker build succeeded."

    return f"Docker build failed: {result.stderr.strip() or 'unknown error'}."


def main() -> Dict[str, Any]:
    """Coordinate the helper agents and return a summary payload."""

    print("🤖 DevOps AI Team Starting Up...")

    gha_config = GitHubActionsConfig(
        workflow_name="CI Pipeline",
        python_version="3.12",
        run_tests=True,
        groq_api_endpoint=os.getenv("GROQ_API_ENDPOINT"),
        groq_api_key=os.getenv("GROQ_API_KEY"),
    )
    gha_agent = GitHubActionsAgent(config=gha_config)
    pipeline = gha_agent.generate_pipeline()
    _write_file(Path(".github/workflows/ci.yml"), pipeline)
    print("✅ CI/CD pipeline created at .github/workflows/ci.yml")

    docker_config = DockerfileConfig(
        base_image="nginx:alpine",
        expose_port=80,
        copy_source="./html",
        work_dir="/usr/share/nginx/html",
        groq_api_endpoint=os.getenv("GROQ_API_ENDPOINT"),
        groq_api_key=os.getenv("GROQ_API_KEY"),
    )
    docker_agent = DockerfileAgent(config=docker_config)
    dockerfile = docker_agent.generate_dockerfile()
    _write_file(Path("Dockerfile"), dockerfile)
    print("✅ Dockerfile created at Dockerfile")

    status_config = BuildStatusConfig(image_tag="myapp:latest")
    status_agent = BuildStatusAgent(config=status_config)

    build_message = _build_docker_image("myapp:latest")
    print(f"🔨 {build_message}")

    status_message = status_agent.check_build_status()
    print(f"📊 Build Status: {status_message}")

    predictor_config = BuildPredictorConfig(
        model="heuristic",
        groq_api_endpoint=os.getenv("GROQ_API_ENDPOINT"),
        groq_api_key=os.getenv("GROQ_API_KEY"),
    )
    predictor_agent = BuildPredictorAgent(config=predictor_config)
    build_data = {
        "commit_hash": os.getenv("GIT_COMMIT", "unknown"),
        "files_changed": [],
        "tests_failed": False,
        "coverage": 92.0,
        "last_build_status": status_message,
        "dependencies_updated": True,
        "dockerfile_exists": True,
        "ci_pipeline_exists": True,
    }
    prediction = predictor_agent.predict_build_failure(build_data)
    print(f"🔮 Build Prediction: {prediction}")

    print("✨ DevOps AI Team has completed their tasks!")

    return {
        "pipeline_path": ".github/workflows/ci.yml",
        "dockerfile_path": "Dockerfile",
        "docker_build_message": build_message,
        "status_message": status_message,
        "prediction": prediction,
    }


if __name__ == "__main__":
    main()
