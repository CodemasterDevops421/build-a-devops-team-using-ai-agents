# app/routers/devops.py
from fastapi import APIRouter, HTTPException
from typing import Any, Dict

from app.schemas import (
    CIConfig,
    DockerfileConfig,
    BuildPredictRequest,
    StatusRequest,
)
from agents.github_actions_agent import GitHubActionsAgent, GitHubActionsConfig
from agents.dockerfile_agent import DockerfileAgent, DockerfileConfig as DFConfig
from agents.build_predictor_agent import BuildPredictorAgent, BuildPredictorConfig
from agents.build_status_agent import BuildStatusAgent, BuildStatusConfig
from app.database import supabase

router = APIRouter(prefix="/devops", tags=["DevOps AI Agents"])

@router.post("/generate-ci")
async def generate_ci(config: CIConfig) -> Dict[str, Any]:
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
        "groq_api_key": config.groq_api_key,
        "pipeline_yaml": pipeline_yaml,
    }
    result = supabase.table("ci_pipelines").insert(record).execute()
    if result.error:
        raise HTTPException(status_code=500, detail="Failed to save CI pipeline to DB")

    return {"pipeline_yaml": pipeline_yaml, "db_id": result.data[0]["id"]}

@router.post("/generate-dockerfile")
async def generate_dockerfile(config: DockerfileConfig) -> Dict[str, Any]:
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
        "groq_api_key": config.groq_api_key,
        "dockerfile_content": dockerfile_content,
    }
    result = supabase.table("dockerfiles").insert(record).execute()
    if result.error:
        raise HTTPException(status_code=500, detail="Failed to save Dockerfile to DB")

    return {"dockerfile_content": dockerfile_content, "db_id": result.data[0]["id"]}

@router.post("/predict-build")
async def predict_build(req: BuildPredictRequest) -> Dict[str, Any]:
    bp_cfg = BuildPredictorConfig(model=req.model, groq_api_key=req.groq_api_key)
    agent = BuildPredictorAgent(bp_cfg)

    build_data_dict = req.build_data.dict()
    prediction: Dict[str, Any] = agent.predict_build_failure(build_data_dict)

    record = {
        "model": req.model,
        "groq_api_key": req.groq_api_key,
        "build_id": req.build_data.build_id,
        "commit_hash": req.build_data.commit_hash,
        "files_changed": req.build_data.files_changed,
        "tests_failed": req.build_data.tests_failed,
        "coverage": req.build_data.coverage,
        "prediction": prediction,
    }
    result = supabase.table("build_predictions").insert(record).execute()
    if result.error:
        raise HTTPException(status_code=500, detail="Failed to save build prediction to DB")

    return {"prediction": prediction, "db_id": result.data[0]["id"]}

@router.post("/check-build-status")
async def check_build_status(req: StatusRequest) -> Dict[str, Any]:
    bs_cfg = BuildStatusConfig(image_tag=req.image_tag)
    agent = BuildStatusAgent(bs_cfg)
    status: str = agent.check_build_status()

    record = {"image_tag": req.image_tag, "status": status}
    result = supabase.table("build_status").insert(record).execute()
    if result.error:
        raise HTTPException(status_code=500, detail="Failed to save build status to DB")

    return {"status": status, "db_id": result.data[0]["id"]}
