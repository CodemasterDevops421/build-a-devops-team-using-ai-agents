"""Agent that produces Dockerfile content from configuration."""
from __future__ import annotations

from textwrap import dedent
from typing import Optional

from pydantic import BaseModel, Field


class DockerfileConfig(BaseModel):
    """Settings controlling Dockerfile generation."""

    base_image: str = Field(default="nginx:alpine")
    expose_port: int = Field(default=80)
    copy_source: str = Field(default="./html")
    work_dir: str = Field(default="/usr/share/nginx/html")
    groq_api_endpoint: Optional[str] = Field(default=None)
    groq_api_key: Optional[str] = Field(default=None)


class DockerfileAgent:
    """Create Dockerfiles for simple static-site deployments."""

    def __init__(self, config: DockerfileConfig):
        self.config = config

    def generate_dockerfile(self) -> str:
        """Return a Dockerfile string tailored to :class:`DockerfileConfig`."""

        dockerfile = dedent(
            f"""
            FROM {self.config.base_image}

            WORKDIR {self.config.work_dir}

            COPY {self.config.copy_source} .

            EXPOSE {self.config.expose_port}

            CMD [\"nginx\", \"-g\", \"daemon off;\"]
            """
        ).strip()

        return f"{dockerfile}\n"
