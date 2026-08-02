"""Academic transcript quality evaluator."""

from __future__ import annotations

from app.chains.extraction_parser import ApplicantProfile, ExtractedDocument
from app.models import Document, Requirement
from app.schemas.document_evaluation import DocumentEvaluationLLMOutput
from app.services.document_evaluation.evaluators.base import BaseDocumentEvaluator
from app.services.document_evaluation.rule_based import (
    GPA_PATTERN,
    RuleBasedScorer,
    count_courses,
    has_section,
)


class TranscriptEvaluator(BaseDocumentEvaluator):
    supported_types = ("academic_transcript",)

    def evaluation_criteria(self) -> str:
        return (
            "- University name present\n"
            "- Degree level identified\n"
            "- GPA or grade average extracted\n"
            "- Course listings readable\n"
            "- Official or certified format"
        )

    def evaluate_rule_based(
        self,
        *,
        document: Document,
        extracted: ExtractedDocument | None,
        applicant_profile: ApplicantProfile | None,
        requirements: list[Requirement],
        document_text: str | None,
    ) -> DocumentEvaluationLLMOutput:
        transcript = extracted.transcript if extracted else (
            applicant_profile.transcript if applicant_profile else None
        )
        text = document_text or ""
        lowered = text.lower()
        scorer = RuleBasedScorer()

        # University
        scorer.add_field(
            "university",
            transcript.university if transcript else None,
            weight=20,
            strength="University name present",
            weakness="University name missing",
            suggestion="Upload a transcript that clearly shows the institution name",
        )

        # Degree
        degree_value = transcript.degree if transcript else None
        degree_found = bool(degree_value) or has_section(
            text, "bachelor", "master", "doctor", "b.sc", "b.a", "m.sc", "ph.d"
        )
        scorer.add_if(
            "degree",
            degree_found,
            weight=20,
            strength="Degree level identified",
            weakness="Degree level not found",
            suggestion="Ensure the degree title is visible on the transcript",
        )

        # GPA
        gpa_value = transcript.gpa if transcript else None
        gpa_found = bool(gpa_value) or bool(GPA_PATTERN.search(text))
        scorer.add_if(
            "gpa",
            gpa_found,
            weight=20,
            strength="GPA or grade average included",
            weakness="GPA not detected",
            suggestion="Ensure GPA or cumulative grade average is visible",
        )

        # Courses
        course_count = count_courses(text)
        scorer.add_if(
            "courses",
            course_count >= 3,
            weight=20,
            strength=f"Course listings detected ({course_count} entries)",
            weakness="Course listings not clearly readable",
            suggestion="Upload a complete transcript with all course titles and grades",
        )

        # Official format
        scorer.add_if(
            "official_format",
            has_section(lowered, "official", "registrar", "certified", "seal"),
            weight=10,
            strength="Appears to be an official transcript",
            weakness="Official certification markers not detected",
            suggestion="Upload an official transcript from your registrar if available",
        )

        # Graduation year (supplementary)
        scorer.add_field(
            "graduation_year",
            transcript.graduation_year if transcript else None,
            weight=10,
            strength="Graduation year specified",
            weakness="Graduation year missing",
            suggestion="Ensure graduation or expected graduation year is visible",
        )

        if not transcript and not text:
            return DocumentEvaluationLLMOutput(
                quality_score=0,
                weaknesses=["Transcript content unavailable"],
                suggestions=["Upload a clear, official academic transcript"],
            )

        return scorer.build()
