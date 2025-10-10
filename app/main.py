"""FastAPI application entrypoint."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .logging_config import configure_logging
from .observability import MetricsMiddleware, RequestIDMiddleware, metrics_endpoint
from .routers.devops import router as devops_router

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging(settings)
    logger.info("application_start", extra={"environment": settings.environment})
    yield
    logger.info("application_stop")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    logger.warning(
        "validation_error",
        extra={
            "path": request.url.path,
            "errors": exc.errors(),
            "request_id": getattr(request.state, "request_id", None),
        },
    )
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.get("/")
async def root() -> Dict[str, Any]:
    return {"message": "DevOps AI Team FastAPI is running!"}


@app.get("/healthz")
async def healthz() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
async def readyz() -> Dict[str, str]:
    return {"status": "ready"}


app.include_router(devops_router)
app.add_api_route("/metrics", metrics_endpoint, methods=["GET"], include_in_schema=False)


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
