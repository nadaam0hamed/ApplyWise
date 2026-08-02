"""Structured AI Readiness Report stored inside ai_analysis.recommendations JSONB."""

from __future__ import annotations

from pydantic import BaseModel, Field


class OverallReadiness(BaseModel):
    readiness_score: int = Field(..., ge=0, le=100)
    status: str


class PersonalInformation(BaseModel):
    full_name: str | None = None
    nationality: str | None = None
    passport_number: str | None = None
    passport_expiry: str | None = None


class AcademicInformation(BaseModel):
    university: str | None = None
    degree: str | None = None
    major: str | None = None
    gpa: str | None = None
    graduation_year: str | None = None


class LanguageScores(BaseModel):
    test_type: str | None = None
    overall_score: str | None = None
    reading: str | None = None
    listening: str | None = None
    writing: str | None = None
    speaking: str | None = None


class ApplicantProfileSummary(BaseModel):
    personal_information: PersonalInformation = Field(default_factory=PersonalInformation)
    academic_information: AcademicInformation = Field(default_factory=AcademicInformation)
    language_scores: LanguageScores = Field(default_factory=LanguageScores)
    skills: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)
    leadership: list[str] = Field(default_factory=list)


class EligibilityComparisonRow(BaseModel):
    requirement_name: str
    required_value: str | None = None
    applicant_value: str | None = None
    status: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    explanation: str
    suggested_action: str | None = None
    # Legacy aliases for stored payloads that used the older column names.
    requirement: str | None = None
    requirement_value: str | None = None
    reason: str | None = None


class DocumentAssessmentEntry(BaseModel):
    name: str
    document_type: str | None = None
    uploaded: bool = False
    completeness: str
    quality: str
    missing_information: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    # Extended professional evaluation fields (optional for backward compatibility).
    document_name: str | None = None
    quality_score: int | None = Field(default=None, ge=0, le=100)
    completeness_level: str | None = Field(
        default=None,
        description="Canonical completeness level: COMPLETE, PARTIAL, or MISSING",
    )
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    extracted_information: dict = Field(default_factory=dict)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class TimelineEntry(BaseModel):
    date: str
    event: str
    priority: str = "medium"


class FinalVerdict(BaseModel):
    summary: str
    recommendation: str
    confidence: str


class ReadinessReport(BaseModel):
    """Full professional AI Readiness Report."""

    overall_readiness: OverallReadiness
    executive_summary: str = ""
    applicant_profile_summary: ApplicantProfileSummary
    eligibility_comparison: list[EligibilityComparisonRow] = Field(default_factory=list)
    missing_requirements: list[dict] = Field(default_factory=list)
    document_assessment: list[DocumentAssessmentEntry] = Field(default_factory=list)
    missing_documents: list[dict] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    timeline: list[TimelineEntry] = Field(default_factory=list)
    final_verdict: FinalVerdict
