"""Middleware and metrics for observability."""
from __future__ import annotations

import time
import uuid
from typing import Callable, Optional

from fastapi import Request, Response
from fastapi.routing import APIRoute
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware

from .config import get_settings


REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    labelnames=("method", "path", "status_code"),
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Request latency",
    labelnames=("method", "path"),
    buckets=(0.05, 0.1, 0.2, 0.5, 1, 2, 5),
)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        settings = get_settings()
        if not settings.metrics_enabled:
            return await call_next(request)

        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start

        path_template = getattr(request.scope.get("route"), "path", request.url.path)
        REQUEST_COUNT.labels(request.method, path_template, str(response.status_code)).inc()
        REQUEST_LATENCY.labels(request.method, path_template).observe(duration)
        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        settings = get_settings()
        header = settings.request_id_header
        request_id = request.headers.get(header) or uuid.uuid4().hex
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers[header] = request_id
        return response


async def metrics_endpoint() -> Response:
    settings = get_settings()
    if not settings.metrics_enabled:
        return Response(status_code=404)
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


class TimedRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original = super().get_route_handler()

        async def handler(request: Request) -> Response:
            start = time.perf_counter()
            response: Response = await original(request)
            elapsed = time.perf_counter() - start
            request.state.endpoint_latency = elapsed
            return response

        return handler


def get_request_id(request: Request | None) -> Optional[str]:
    if request is None:
        return None
    return getattr(request.state, "request_id", None)


__all__ = [
    "MetricsMiddleware",
    "RequestIDMiddleware",
    "metrics_endpoint",
    "TimedRoute",
    "REQUEST_COUNT",
    "REQUEST_LATENCY",
    "get_request_id",
]
