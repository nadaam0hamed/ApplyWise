"""Graduation certificate / diploma quality evaluator."""

from __future__ import annotations

from app.chains.extraction_parser import ApplicantProfile, ExtractedDocument
from app.models import Document, Requirement
from app.schemas.document_evaluation import DocumentEvaluationLLMOutput
from app.services.document_evaluation.evaluators.base import BaseDocumentEvaluator
from app.services.document_evaluation.rule_based import RuleBasedScorer, has_section, word_count


class GraduationCertificateEvaluator(BaseDocumentEvaluator):
    supported_types = ("diploma", "graduation_certificate")

    def evaluation_criteria(self) -> str:
        return (
            "- Issuing institution name clearly visible\n"
            "- Degree title and field of study\n"
            "- Graduation or conferral date\n"
            "- Signatures, seals, or authentication marks\n"
            "- Consistency with transcript information"
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
        degree = extracted.degree_certificate if extracted else (
            applicant_profile.degree_certificate if applicant_profile else None
        )
        text = document_text or ""
        scorer = RuleBasedScorer()

        scorer.add_field(
            "university",
            degree.university if degree else None,
            weight=20,
            strength="Issuing institution identified",
            weakness="Issuing institution not detected",
            suggestion="Upload a clear scan showing the university name",
        )
        scorer.add_field(
            "degree",
            degree.degree if degree else None,
            weight=25,
            strength="Degree title present",
            weakness="Degree title not detected",
            suggestion="Ensure the degree name is clearly visible",
        )
        scorer.add_field(
            "major",
            degree.major if degree else None,
            weight=20,
            strength="Field of study listed",
            weakness="Field of study not detected",
            suggestion="Ensure major or specialization is visible on the certificate",
        )
        scorer.add_field(
            "graduation_year",
            degree.graduation_year if degree else None,
            weight=15,
            strength="Graduation year specified",
            weakness="Graduation year missing",
            suggestion="Ensure the conferral date or year is visible",
        )

        scorer.add_if(
            "authentication",
            has_section(text.lower(), "certified", "registrar", "seal", "signature", "signed"),
            weight=10,
            strength="Official certification markers detected",
            weakness="No official certification markers detected",
            suggestion="Upload an officially signed and sealed certificate",
        )

        scorer.add_if(
            "readability",
            word_count(text) >= 15 or bool(degree and degree.university),
            weight=10,
            strength="Certificate content is readable",
            weakness="Certificate scan may be blurry or incomplete",
            suggestion="Upload a clear scan of your official degree certificate",
        )

        if not degree and not text:
            return DocumentEvaluationLLMOutput(
                quality_score=0,
                weaknesses=["Certificate data could not be extracted"],
                suggestions=["Upload a clear scan of your official degree certificate"],
            )

        return scorer.build()
