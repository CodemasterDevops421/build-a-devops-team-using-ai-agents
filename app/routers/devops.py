"""FastAPI routes exposing the DevOps helper agents."""
from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status

from agents.build_predictor_agent import BuildPredictorAgent, BuildPredictorConfig
from agents.build_status_agent import BuildStatusAgent, BuildStatusConfig
from agents.dockerfile_agent import DockerfileAgent, DockerfileConfig as DFConfig
from agents.github_actions_agent import GitHubActionsAgent, GitHubActionsConfig
from app.database import supabase
from app.schemas import BuildPredictRequest, CIConfig, DockerfileConfig, StatusRequest

from ..observability import TimedRoute, get_request_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/devops", tags=["DevOps AI Agents"], route_class=TimedRoute)


def get_supabase_client() -> Any:
    return supabase


def _persist(record: Dict[str, Any], table: str, db: Any) -> int:
    try:
        result = db.table(table).insert(record).execute()
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("database_write_failed", extra={"table": table})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database write failed") from exc

    if getattr(result, "error", None):
        logger.error("database_error", extra={"table": table, "error": result.error})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database write failed")

    return int(result.data[0]["id"])


@router.post("/generate-ci")
async def generate_ci(config: CIConfig, request: Request, db: Any = Depends(get_supabase_client)) -> Dict[str, Any]:
    agent_cfg = GitHubActionsConfig(
        workflow_name=config.workflow_name,
        python_version=config.python_version,
        run_tests=config.run_tests,
        groq_api_endpoint=config.groq_api_endpoint,
        groq_api_key=config.groq_api_key,
    )
    agent = GitHubActionsAgent(agent_cfg)
    pipeline_yaml: str = agent.generate_pipeline()

    record = {
        "workflow_name": config.workflow_name,
        "python_version": config.python_version,
        "run_tests": config.run_tests,
        "groq_api_endpoint": config.groq_api_endpoint,
        "pipeline_yaml": pipeline_yaml,
    }
    db_id = _persist(record, "ci_pipelines", db)
    logger.info(
        "ci_generated",
        extra={"workflow_name": config.workflow_name, "request_id": get_request_id(request)},
    )
    return {"pipeline_yaml": pipeline_yaml, "db_id": db_id}


@router.post("/generate-dockerfile")
async def generate_dockerfile(
    config: DockerfileConfig, request: Request, db: Any = Depends(get_supabase_client)
) -> Dict[str, Any]:
    agent_cfg = DFConfig(
        base_image=config.base_image,
        expose_port=config.expose_port,
        copy_source=config.copy_source,
        work_dir=config.work_dir,
        groq_api_endpoint=config.groq_api_endpoint,
        groq_api_key=config.groq_api_key,
    )
    agent = DockerfileAgent(agent_cfg)
    dockerfile_content: str = agent.generate_dockerfile()

    record = {
        "base_image": config.base_image,
        "expose_port": config.expose_port,
        "copy_source": config.copy_source,
        "work_dir": config.work_dir,
        "groq_api_endpoint": config.groq_api_endpoint,
        "dockerfile_content": dockerfile_content,
    }
    db_id = _persist(record, "dockerfiles", db)
    logger.info(
        "dockerfile_generated",
        extra={"base_image": config.base_image, "request_id": get_request_id(request)},
    )
    return {"dockerfile_content": dockerfile_content, "db_id": db_id}


@router.post("/predict-build")
async def predict_build(
    req: BuildPredictRequest, request: Request, db: Any = Depends(get_supabase_client)
) -> Dict[str, Any]:
    bp_cfg = BuildPredictorConfig(model=req.model or "heuristic", groq_api_key=req.groq_api_key)
    agent = BuildPredictorAgent(bp_cfg)

    build_data_dict = req.build_data.model_dump()
    prediction: Dict[str, Any] = agent.predict_build_failure(build_data_dict)

    record = {
        "model": req.model,
        "build_id": req.build_data.build_id,
        "commit_hash": req.build_data.commit_hash,
        "files_changed": req.build_data.files_changed,
        "tests_failed": req.build_data.tests_failed,
        "coverage": req.build_data.coverage,
        "prediction": prediction,
    }
    db_id = _persist(record, "build_predictions", db)
    logger.info(
        "build_prediction_completed",
        extra={"build_id": req.build_data.build_id, "request_id": get_request_id(request)},
    )
    return {"prediction": prediction, "db_id": db_id}


@router.post("/check-build-status")
async def check_build_status(
    req: StatusRequest, request: Request, db: Any = Depends(get_supabase_client)
) -> Dict[str, Any]:
    bs_cfg = BuildStatusConfig(image_tag=req.image_tag)
    agent = BuildStatusAgent(bs_cfg)
    status_message: str = agent.check_build_status()

    record = {"image_tag": req.image_tag, "status": status_message}
    db_id = _persist(record, "build_status", db)
    logger.info(
        "build_status_checked",
        extra={"image_tag": req.image_tag, "request_id": get_request_id(request)},
    )
    return {"status": status_message, "db_id": db_id}
