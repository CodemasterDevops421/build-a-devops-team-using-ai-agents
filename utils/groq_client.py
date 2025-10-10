"""Lightweight HTTP client for interacting with Groq endpoints."""
from __future__ import annotations

from typing import Any, Dict

import requests
from pydantic import ValidationError

from models.groq_models import (
    InferenceResponse,
    CodeReviewRequest,
    CodeReviewFeedback,
    ChatCreateRequest,
    ChatCreateResponse,
)


class GROQClient:
    """Minimal wrapper around the Groq REST API."""

    def __init__(self, api_endpoint: str, api_key: str):
        self.api_endpoint = api_endpoint.rstrip("/")
        self.api_key = api_key

    @property
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def send_inference_request(self, model_id: str, input_data: Dict[str, Any]) -> InferenceResponse:
        payload = {"model": model_id, "messages": input_data.get("messages", [])}
        response = requests.post(self.api_endpoint, json=payload, headers=self._headers, timeout=30)
        response.raise_for_status()
        try:
            return InferenceResponse.model_validate(response.json())
        except ValidationError as exc:
            raise ValueError(f"Failed to parse inference response: {exc}") from exc

    def send_code_review_request(self, model_id: str, code_review_request: CodeReviewRequest) -> CodeReviewFeedback:
        payload = {"model_id": model_id, "input_data": code_review_request.model_dump()}
        url = f"{self.api_endpoint}/code-review"
        response = requests.post(url, json=payload, headers=self._headers, timeout=30)
        response.raise_for_status()
        try:
            return CodeReviewFeedback.model_validate(response.json())
        except ValidationError as exc:
            raise ValueError(f"Failed to parse code review response: {exc}") from exc

    def send_chat_create_request(self, chat_create_request: ChatCreateRequest) -> ChatCreateResponse:
        payload = chat_create_request.model_dump()
        response = requests.post(self.api_endpoint, json=payload, headers=self._headers, timeout=30)
        response.raise_for_status()
        try:
            return ChatCreateResponse.model_validate(response.json())
        except ValidationError as exc:
            raise ValueError(f"Failed to parse chat response: {exc}") from exc
