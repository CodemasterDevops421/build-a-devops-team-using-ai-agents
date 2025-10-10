"""Utilities for querying Docker build status."""
from __future__ import annotations

import shutil
import subprocess

from pydantic import BaseModel, Field


class BuildStatusConfig(BaseModel):
    """Configuration for :class:`BuildStatusAgent`."""

    image_tag: str = Field(..., description="Docker image tag to inspect.")


class BuildStatusAgent:
    """Check Docker image status with graceful fallbacks when Docker is absent."""

    def __init__(self, config: BuildStatusConfig):
        self.config = config

    def check_build_status(self) -> str:
        """Return a human readable status message for ``config.image_tag``."""

        if not shutil.which("docker"):
            return "Docker CLI not available on PATH; skipping inspection."

        try:
            result = subprocess.run(
                ["docker", "inspect", self.config.image_tag],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                timeout=30,
            )
        except FileNotFoundError:
            return "Docker CLI not available on PATH; skipping inspection."
        except subprocess.SubprocessError as exc:  # pragma: no cover - defensive.
            return f"Error checking build status: {exc}"

        if result.returncode == 0:
            return f"Docker image '{self.config.image_tag}' exists."

        detail = result.stderr.strip() or "unknown error"
        return f"Docker image '{self.config.image_tag}' does not exist ({detail})."
