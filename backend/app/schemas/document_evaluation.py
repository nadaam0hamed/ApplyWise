"""Structured output schema for professional document quality evaluation."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class DocumentCompletenessLevel(str, Enum):
    """Canonical three-level completeness classification for document evaluations."""

    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    MISSING = "MISSING"


class DocumentEvaluation(BaseModel):
    """Canonical professional document evaluation schema.

    Reusable by all document evaluators. Maps to the readiness report via
    ``DocumentAssessmentEntry`` while preserving legacy field names there.
    """

    document_name: str
    document_type: str
    uploaded: bool = True
    quality_score: int = Field(..., ge=0, le=100)
    completeness: DocumentCompletenessLevel
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    extracted_information: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class DocumentEvaluationLLMOutput(BaseModel):
    """LLM-parsed evaluation payload before attaching document metadata."""

    quality_score: int = Field(..., ge=0, le=100)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    confidence: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Evaluator confidence in this assessment (0-1).",
    )


class SubjectiveWritingLLMOutput(BaseModel):
    """LLM output for subjective writing quality only — never used for objective checks."""

    writing_quality_score: int = Field(..., ge=0, le=100)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)


class DocumentEvaluationResult(BaseModel):
    """Full evaluation result returned by every document evaluator.

    Extends the canonical ``DocumentEvaluation`` fields with pipeline metadata
    and legacy report labels for backward compatibility.
    """

    document_id: str
    file_name: str
    document_name: str
    document_type: str
    uploaded: bool = True
    quality_score: int = Field(..., ge=0, le=100)
    completeness_level: DocumentCompletenessLevel
    completeness: str = Field(
        ...,
        description="Legacy report label: Complete, Mostly Complete, Partial, Incomplete, or Missing",
    )
    quality_rating: str = Field(
        ...,
        description="Excellent, Good, Fair, Poor, or Not Assessed",
    )
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    extracted_information: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evaluation_status: str = Field(
        default="success",
        description="success, skipped, or error",
    )
    error_message: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _apply_legacy_defaults(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        payload = dict(data)
        if not payload.get("document_name") and payload.get("file_name"):
            payload["document_name"] = payload["file_name"]

        if not payload.get("completeness_level"):
            completeness_label = payload.get("completeness")
            quality_score = payload.get("quality_score", 0)
            evaluation_status = payload.get("evaluation_status", "success")
            uploaded = payload.get("uploaded", True)
            if isinstance(completeness_label, str):
                normalized = completeness_label.strip().lower()
                if normalized in {"complete", "mostly complete"}:
                    payload["completeness_level"] = DocumentCompletenessLevel.COMPLETE
                elif normalized == "partial":
                    payload["completeness_level"] = DocumentCompletenessLevel.PARTIAL
                else:
                    payload["completeness_level"] = score_to_completeness_level(
                        int(quality_score),
                        uploaded=bool(uploaded),
                        evaluation_status=str(evaluation_status),
                    )
            else:
                payload["completeness_level"] = score_to_completeness_level(
                    int(quality_score),
                    uploaded=bool(uploaded),
                    evaluation_status=str(evaluation_status),
                )

        if not payload.get("completeness") and payload.get("completeness_level"):
            level = payload["completeness_level"]
            if isinstance(level, DocumentCompletenessLevel):
                level_value = level.value
            else:
                level_value = str(level)
            payload["completeness"] = {
                DocumentCompletenessLevel.COMPLETE.value: "Complete",
                DocumentCompletenessLevel.PARTIAL.value: "Partial",
                DocumentCompletenessLevel.MISSING.value: "Missing",
            }.get(level_value, score_to_completeness_label(int(payload.get("quality_score", 0))))

        weaknesses = payload.get("weaknesses") or []
        missing_information = payload.get("missing_information")
        if missing_information is None:
            payload["missing_information"] = list(weaknesses)
        elif isinstance(missing_information, list):
            payload["missing_information"] = merge_missing_information(
                list(weaknesses),
                missing_information,
            )

        return payload

    def to_document_evaluation(self) -> DocumentEvaluation:
        """Return the canonical evaluation shape without pipeline metadata."""
        return DocumentEvaluation(
            document_name=self.document_name,
            document_type=self.document_type,
            uploaded=self.uploaded,
            quality_score=self.quality_score,
            completeness=self.completeness_level,
            strengths=self.strengths,
            weaknesses=self.weaknesses,
            missing_information=self.missing_information,
            suggestions=self.suggestions,
            extracted_information=self.extracted_information,
            confidence=self.confidence,
        )


def score_to_completeness_label(score: int) -> str:
    """Map a quality score to the legacy five-level completeness label."""
    if score >= 85:
        return "Complete"
    if score >= 70:
        return "Mostly Complete"
    if score >= 45:
        return "Partial"
    if score > 0:
        return "Incomplete"
    return "Missing"


def score_to_completeness_level(
    score: int,
    *,
    uploaded: bool = True,
    evaluation_status: str = "success",
) -> DocumentCompletenessLevel:
    """Map a quality score and upload status to the canonical completeness level."""
    if not uploaded or evaluation_status in {"skipped", "error"}:
        return DocumentCompletenessLevel.MISSING
    if score >= 70:
        return DocumentCompletenessLevel.COMPLETE
    if score >= 30:
        return DocumentCompletenessLevel.PARTIAL
    return DocumentCompletenessLevel.MISSING


def score_to_quality_rating(score: int) -> str:
    """Map a quality score to a human-readable quality rating."""
    if score >= 90:
        return "Excellent"
    if score >= 75:
        return "Good"
    if score >= 55:
        return "Fair"
    if score > 0:
        return "Poor"
    return "Not Assessed"


def merge_missing_information(
    weaknesses: list[str],
    missing_information: list[str],
) -> list[str]:
    """Combine explicit missing-information items with weakness-derived gaps."""
    merged: list[str] = []
    seen: set[str] = set()
    for item in [*missing_information, *weaknesses]:
        normalized = item.strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        merged.append(normalized)
    return merged
