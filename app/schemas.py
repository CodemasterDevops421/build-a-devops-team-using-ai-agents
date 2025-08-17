# app/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional, Any

class CIConfig(BaseModel):
    workflow_name: str
    python_version: str
    run_tests: bool
    groq_api_endpoint: str
    groq_api_key: str

class DockerfileConfig(BaseModel):
    base_image: str
    expose_port: int
    copy_source: str
    work_dir: str
    groq_api_endpoint: str
    groq_api_key: str

class BuildData(BaseModel):
    build_id: str
    commit_hash: str
    files_changed: List[str]
    tests_failed: bool
    coverage: float

class BuildPredictRequest(BaseModel):
    model: Optional[str] = Field(default="llama3-8b-8192")
    groq_api_key: str
    build_data: BuildData

class StatusRequest(BaseModel):
    image_tag: str
