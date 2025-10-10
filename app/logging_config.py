"""Logging configuration for the FastAPI application."""
from __future__ import annotations

import json
import logging
import logging.config
from typing import Any, Dict

from .config import Settings, get_settings


class JsonFormatter(logging.Formatter):
    """Minimal JSON formatter for structured logs."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401 - see base class.
        payload: Dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        if hasattr(record, "request_id") and record.request_id:
            payload["request_id"] = getattr(record, "request_id")
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": JsonFormatter,
            }
        },
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "formatter": "json",
            }
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": settings.log_level, "propagate": False},
            "uvicorn.error": {"handlers": ["default"], "level": settings.log_level, "propagate": False},
            "uvicorn.access": {
                "handlers": ["default"],
                "level": settings.log_level,
                "propagate": False,
            },
        },
        "root": {"handlers": ["default"], "level": settings.log_level},
    }
    logging.config.dictConfig(logging_config)


__all__ = ["configure_logging", "JsonFormatter"]
