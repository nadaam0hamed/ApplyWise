"""Schemas for deterministic requirement-vs-profile matching."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class MatchStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"


class StructuredRequirement(BaseModel):
    """Normalized requirement payload extracted from knowledge-base text."""

    type: str = Field(description="Requirement category, e.g. gpa, ielts, degree.")
    operator: str | None = Field(
        default=None,
        description="Comparison operator when applicable, e.g. >= for minimum thresholds.",
    )
    value: str | float | int | bool | list[str] | None = Field(
        default=None,
        description="Normalized requirement value.",
    )


class RetrievedRequirement(BaseModel):
    """A single requirement value extracted from knowledge-base text."""

    field: str
    value: str
    source: str = Field(description="static or application knowledge base")
    excerpt: str = Field(default="", description="Source text snippet supporting the extraction.")
    structured: StructuredRequirement | None = Field(
        default=None,
        description="Normalized structured representation of the requirement.",
    )


class FieldComparison(BaseModel):
    """Comparison of one requirement against one applicant field."""

    field: str
    requirement: str | None = None
    applicant: str | None = None
    status: MatchStatus
    reason: str
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence in this evaluation (0–1).",
    )
    suggested_action: str | None = Field(
        default=None,
        description="Concrete next step when status is FAIL or PARTIAL.",
    )
    knowledge_source: str | None = None


class RequirementMatchingResult(BaseModel):
    """Full output of the requirement matching engine."""

    comparisons: list[FieldComparison] = Field(default_factory=list)
    retrieved_requirements: list[RetrievedRequirement] = Field(default_factory=list)


def normalized_numeric_value(requirement: RetrievedRequirement) -> float | None:
    """Return a numeric threshold from structured data or the legacy value string."""
    if requirement.structured and requirement.structured.value is not None:
        raw = requirement.structured.value
        if isinstance(raw, (int, float)):
            return float(raw)
        if isinstance(raw, str):
            import re

            match = re.search(r"(\d+\.?\d*)", raw.replace(",", "."))
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    return None
    import re

    match = re.search(r"(\d+\.?\d*)", requirement.value.replace(",", "."))
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None
