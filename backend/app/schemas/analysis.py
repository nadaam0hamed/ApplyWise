"""API request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.chains.output_parser import ApplicationAnalysisResult
from app.schemas.readiness_report import ReadinessReport


class AnalyzeResponse(ApplicationAnalysisResult):
    """Structured analysis returned by POST /api/analyze/{application_id}."""

    application_id: str
    analysis_id: str
    created_at: datetime
    report: ReadinessReport | None = Field(
        default=None,
        description="Full AI Readiness Report (optional extension; flat fields remain for backward compatibility).",
    )
