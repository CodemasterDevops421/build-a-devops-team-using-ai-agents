"""Build prediction agent built on deterministic heuristics."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional

from pydantic import BaseModel, Field, ValidationError

try:  # Optional dependency; only used when credentials are configured.
    from groq import Groq  # type: ignore
except Exception:  # pragma: no cover - we handle absence gracefully at runtime.
    Groq = None  # type: ignore


class BuildPredictorConfig(BaseModel):
    """Configuration for :class:`BuildPredictorAgent`."""

    model: str = Field(default="heuristic", description="LLM model identifier if Groq is used.")
    groq_api_key: Optional[str] = Field(default=None, description="Groq API key; optional.")
    groq_api_endpoint: Optional[str] = Field(default=None, description="Groq endpoint override.")


@dataclass
class PredictionResult:
    """Structured build prediction returned by the agent."""

    risk_score: float
    risk_level: str
    summary: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "summary": self.summary,
        }


class BuildPredictorAgent:
    """Predict build failures using lightweight heuristics with optional Groq fallback."""

    def __init__(self, config: BuildPredictorConfig):
        self.config = config
        self._client = None
        api_key = config.groq_api_key
        if api_key:
            if Groq is None:
                raise RuntimeError("groq package is not available but an API key was provided")
            endpoint_overrides = {}
            if config.groq_api_endpoint:
                endpoint_overrides["base_url"] = config.groq_api_endpoint
            self._client = Groq(api_key=api_key, **endpoint_overrides)  # type: ignore[arg-type]

    # ------------------------------ public API ------------------------------
    def predict_build_failure(self, build_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict the likelihood of a build failure.

        The agent validates *build_data*, computes a risk score using explainable
        heuristics, and returns a structured prediction payload. When Groq
        credentials are supplied we attempt to enrich the result with an LLM
        response; otherwise we fall back to a deterministic implementation so
        the tool works offline and in tests.
        """

        try:
            normalised = self._validate_build_data(build_data)
        except ValidationError as exc:
            return {"status": "error", "error": exc.errors()}

        heuristic_prediction = self._run_heuristics(normalised)

        if not self._client:
            return {"status": "success", "prediction": heuristic_prediction.as_dict()}

        try:
            llm_prediction = self._call_groq(normalised, heuristic_prediction)
        except Exception as exc:  # pragma: no cover - network paths are not tested.
            # Fall back to the deterministic prediction while surfacing the error.
            return {
                "status": "degraded",
                "prediction": heuristic_prediction.as_dict(),
                "warning": f"Groq enrichment failed: {exc}",
            }

        return {"status": "success", "prediction": llm_prediction}

    # ---------------------------- internal helpers ----------------------------
    class _BuildData(BaseModel):
        commit_hash: str
        files_changed: Iterable[str]
        tests_failed: bool
        coverage: float = Field(ge=0.0, le=100.0)
        last_build_status: Optional[str] = None
        dependencies_updated: Optional[bool] = True
        dockerfile_exists: Optional[bool] = True
        ci_pipeline_exists: Optional[bool] = True

    def _validate_build_data(self, build_data: Dict[str, Any]) -> "BuildPredictorAgent._BuildData":
        return self._BuildData.model_validate(build_data)

    def _run_heuristics(self, data: "BuildPredictorAgent._BuildData") -> PredictionResult:
        score = 0.0
        summary_bits = []

        if data.tests_failed:
            score += 0.45
            summary_bits.append("recent test failures detected")

        coverage_penalty = max(0.0, (90.0 - data.coverage) / 100.0)
        if coverage_penalty:
            score += coverage_penalty
            summary_bits.append(f"coverage at {data.coverage:.1f}%")

        change_penalty = min(len(list(data.files_changed)) * 0.05, 0.25)
        if change_penalty:
            score += change_penalty
            summary_bits.append("large change-set")

        if data.last_build_status and "success" not in data.last_build_status.lower():
            score += 0.15
            summary_bits.append("previous build not successful")

        if data.dependencies_updated is False:
            score += 0.05
            summary_bits.append("dependencies outdated")

        if data.dockerfile_exists is False or data.ci_pipeline_exists is False:
            score += 0.05
            summary_bits.append("missing automation artifacts")

        score = min(round(score, 2), 1.0)
        if score >= 0.7:
            level = "high"
        elif score >= 0.4:
            level = "medium"
        else:
            level = "low"

        if not summary_bits:
            summary_bits.append("no risk indicators detected")

        summary = ", ".join(summary_bits)
        return PredictionResult(risk_score=score, risk_level=level, summary=summary)

    def _call_groq(
        self,
        data: "BuildPredictorAgent._BuildData",
        heuristic: PredictionResult,
    ) -> Dict[str, Any]:  # pragma: no cover - requires network.
        assert self._client is not None
        response = self._client.chat.completions.create(  # type: ignore[union-attr]
            messages=[
                {
                    "role": "system",
                    "content": "You are a build reliability assistant. Provide concise risk assessments.",
                },
                {
                    "role": "user",
                    "content": (
                        "Predict the probability of a CI/CD build failure given the following telemetry: "
                        f"{data.model_dump()}\n"
                        f"A heuristic model produced this assessment: {heuristic.as_dict()}"
                    ),
                },
            ],
            model=self.config.model,
            temperature=0.2,
            max_tokens=256,
        )
        content = response.choices[0].message.content
        return {
            "risk_score": heuristic.risk_score,
            "risk_level": heuristic.risk_level,
            "summary": heuristic.summary,
            "llm_analysis": content,
        }
