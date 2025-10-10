"""Agents that generate GitHub Actions workflow YAML."""
from __future__ import annotations

from textwrap import dedent, indent
from typing import List, Optional

from pydantic import BaseModel, Field


class GitHubActionsConfig(BaseModel):
    """Configuration for the GitHub Actions workflow generator."""

    workflow_name: str = Field(default="CI Pipeline")
    python_version: str = Field(default="3.12")
    run_tests: bool = Field(default=True)
    groq_api_endpoint: Optional[str] = Field(default=None)
    groq_api_key: Optional[str] = Field(default=None)


class GitHubActionsAgent:
    """Generate reproducible GitHub Actions workflows."""

    def __init__(self, config: GitHubActionsConfig):
        self.config = config

    def generate_pipeline(self) -> str:
        """Render a CI pipeline YAML string based on :class:`GitHubActionsConfig`."""

        steps: List[str] = [
            "- name: Checkout code\n  uses: actions/checkout@v4",
            (
                f"- name: Set up Python {self.config.python_version}\n"
                "  uses: actions/setup-python@v5\n"
                "  with:\n"
                f"    python-version: {self.config.python_version}"
            ),
            dedent(
                """
                - name: Cache pip packages
                  uses: actions/cache@v4
                  with:
                    path: ~/.cache/pip
                    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
                    restore-keys: |
                      ${{ runner.os }}-pip-
                """
            ).strip(),
            dedent(
                """
                - name: Install dependencies
                  run: |
                    python -m pip install --upgrade pip
                    pip install -r requirements.txt
                """
            ).strip(),
            "- name: Run DevOps AI team orchestration\n  run: python main.py",
        ]

        if self.config.run_tests:
            steps.append(
                dedent(
                    """
                    - name: Run unit tests
                      run: |
                        pytest --maxfail=1 --disable-warnings -q
                    """
                ).strip()
            )

        steps_yaml = "\n".join(indent(step, "      ") for step in steps)

        pipeline = dedent(
            f"""
            name: {self.config.workflow_name}

            on:
              push:
                branches: [main]
              pull_request:
                branches: [main]

            permissions:
              contents: read
              pull-requests: write

            jobs:
              run-devops-ai:
                runs-on: ubuntu-latest

                env:
                  GROQ_API_ENDPOINT: ${{{{ secrets.GROQ_API_ENDPOINT }}}}
                  GROQ_API_KEY: ${{{{ secrets.GROQ_API_KEY }}}}
                  GITHUB_TOKEN: ${{{{ secrets.GH_TOKEN }}}}

                steps:
            """
        ).strip()

        return f"{pipeline}\n{steps_yaml}\n"
