"""Shared constants mirroring frontend enums and labels."""

from enum import StrEnum


class ApplicationStatus(StrEnum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    ANALYZING = "analyzing"
    READY = "ready"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class RequirementCategory(StrEnum):
    ELIGIBILITY = "eligibility"
    DOCUMENTS = "documents"
    LANGUAGE = "language"
    ACADEMIC = "academic"
    FINANCIAL = "financial"
    RECOMMENDATION = "recommendation"
    IDENTITY = "identity"
    DEADLINE = "deadline"
    OTHER = "other"


REQUIREMENT_CATEGORY_LABELS: dict[str, str] = {
    RequirementCategory.ELIGIBILITY: "Eligibility",
    RequirementCategory.DOCUMENTS: "Required Documents",
    RequirementCategory.LANGUAGE: "Language Requirements",
    RequirementCategory.ACADEMIC: "Academic Requirements",
    RequirementCategory.FINANCIAL: "Financial Requirements",
    RequirementCategory.RECOMMENDATION: "Recommendation Letters",
    RequirementCategory.IDENTITY: "Identity & Passport",
    RequirementCategory.DEADLINE: "Deadlines",
    RequirementCategory.OTHER: "Other",
}

REQUIRED_CATEGORIES = {
    RequirementCategory.ELIGIBILITY,
    RequirementCategory.DOCUMENTS,
    RequirementCategory.LANGUAGE,
    RequirementCategory.ACADEMIC,
    RequirementCategory.RECOMMENDATION,
    RequirementCategory.IDENTITY,
}

DOCUMENT_TYPE_LABELS: dict[str, str] = {
    "passport": "Passport",
    "cv": "CV / Resume",
    "academic_transcript": "Academic Transcript",
    "motivation_letter": "Motivation Letter",
    "statement_of_purpose": "Statement of Purpose",
    "letter_of_recommendation": "Letter of Recommendation",
    "ielts_score": "IELTS Score",
    "toefl_score": "TOEFL Score",
    "gre_score": "GRE Score",
    "diploma": "Diploma / Degree Certificate",
    "application_form": "Application Form",
    "other": "Other",
}
