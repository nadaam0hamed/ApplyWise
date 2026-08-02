"""Fallback evaluator for unsupported or generic document types."""

from __future__ import annotations

from app.chains.extraction_parser import ApplicantProfile, ExtractedDocument
from app.models import Document, Requirement
from app.schemas.document_evaluation import DocumentEvaluationLLMOutput
from app.services.document_evaluation.evaluators.base import BaseDocumentEvaluator
from app.services.document_evaluation.rule_based import RuleBasedScorer, word_count


class GenericDocumentEvaluator(BaseDocumentEvaluator):
    supported_types = ("other", "application_form")

    def evaluation_criteria(self) -> str:
        return (
            "- Document is readable and complete\n"
            "- Content appears relevant to the application\n"
            "- Professional presentation\n"
            "- Key identifying information present\n"
            "- No obvious corruption or missing pages"
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
        if not document_text:
            return DocumentEvaluationLLMOutput(
                quality_score=0,
                weaknesses=["Document content could not be read"],
                suggestions=["Upload a readable PDF or DOCX version"],
            )

        scorer = RuleBasedScorer()
        wc = word_count(document_text)

        scorer.add(
            "readable",
            True,
            weight=30,
            strength="Document uploaded and readable",
        )
        scorer.add_if(
            "substantive_content",
            wc >= 100,
            weight=40,
            strength="Substantive content detected",
            weakness="Document appears very brief",
            suggestion="Confirm this is the complete document",
        )
        scorer.add_if(
            "reasonable_length",
            wc >= 20,
            weight=30,
            strength="Minimum content threshold met",
            weakness="Document has very little extractable text",
            suggestion="Verify the upload is not corrupted or blank",
        )

        output = scorer.build()
        output.suggestions.append("Verify this document type is required for your application")
        return output
