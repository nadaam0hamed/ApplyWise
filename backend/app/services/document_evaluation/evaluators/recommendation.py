"""Recommendation letter quality evaluator."""

from __future__ import annotations

from app.chains.extraction_parser import ApplicantProfile, ExtractedDocument
from app.models import Document, Requirement
from app.schemas.document_evaluation import DocumentEvaluationLLMOutput
from app.services.document_evaluation.evaluators.base import BaseDocumentEvaluator
from app.services.document_evaluation.rule_based import (
    RELATIONSHIP_KEYWORDS,
    SIGNATURE_KEYWORDS,
    RuleBasedScorer,
    has_email,
    has_opening_paragraph,
    has_phone,
    word_count,
)


class RecommendationLetterEvaluator(BaseDocumentEvaluator):
    supported_types = ("letter_of_recommendation",)

    def evaluation_criteria(self) -> str:
        return (
            "- Recommender identity and credentials\n"
            "- Position and organization affiliation\n"
            "- Relationship to the applicant\n"
            "- Specific examples of applicant achievements\n"
            "- Signature and professional closing\n"
            "- Referee contact information"
        )

    def uses_subjective_llm(self) -> bool:
        return True

    def subjective_criteria(self) -> str:
        return (
            "- Depth and specificity of endorsement language\n"
            "- Balance between praise and concrete evidence\n"
            "- Professional tone appropriate for admissions"
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
        letter = extracted.recommendation_letter if extracted else None
        if not letter and applicant_profile and applicant_profile.recommendation_letters:
            letter = applicant_profile.recommendation_letters[0]

        text = document_text or ""
        lowered = text.lower()
        scorer = RuleBasedScorer()

        # Recommender identity
        scorer.add_field(
            "referee_identity",
            letter.referee if letter else None,
            weight=12,
            strength="Referee identity identified",
            weakness="Referee name not clearly identified",
            suggestion="Ensure the letter includes the referee's full name and signature",
        )

        # Position
        scorer.add_field(
            "referee_position",
            letter.position if letter else None,
            weight=10,
            strength="Referee position or title present",
            weakness="Referee position or title missing",
            suggestion="Include the referee's job title on letterhead or in the signature block",
        )

        # Organization
        scorer.add_field(
            "referee_organization",
            letter.organization if letter else None,
            weight=10,
            strength="Referee organization or affiliation present",
            weakness="Referee organization missing",
            suggestion="Use official letterhead with institution details",
        )

        # Relationship
        relationship_found = any(kw in lowered for kw in RELATIONSHIP_KEYWORDS)
        scorer.add_if(
            "relationship",
            relationship_found,
            weight=12,
            strength="Relationship to applicant clearly described",
            weakness="Relationship between referee and applicant not stated",
            suggestion="Ask the referee to describe how they know you and in what capacity",
        )

        # Specific examples
        examples_present = bool(letter and letter.strengths_mentioned) or any(
            term in lowered
            for term in ("for example", "specifically", "during", "project", "demonstrated", "achieved")
        )
        scorer.add_if(
            "examples",
            examples_present,
            weight=15,
            strength="Specific applicant strengths and examples highlighted",
            weakness="No specific strengths or examples mentioned about the applicant",
            suggestion="Ask the referee to include concrete examples of your work",
        )

        # Signature / closing
        signature_found = any(kw in lowered for kw in SIGNATURE_KEYWORDS)
        scorer.add_if(
            "signature",
            signature_found,
            weight=8,
            strength="Professional signature or closing detected",
            weakness="Signature or professional closing missing",
            suggestion="Ensure the letter is signed with a professional closing",
        )

        # Contact information
        contact_found = has_email(text) or has_phone(text)
        scorer.add_if(
            "contact_information",
            contact_found,
            weight=8,
            strength="Referee contact information present",
            weakness="Referee contact information missing",
            suggestion="Include referee email, phone, or institutional address",
        )

        # Opening
        scorer.add_if(
            "opening",
            has_opening_paragraph(text),
            weight=6,
            strength="Formal opening present",
            weakness="Formal opening missing",
            suggestion="Use a standard opening (e.g., 'Dear Admissions Committee')",
        )

        # Endorsement strength
        endorsement_terms = ("highly recommend", "strongest recommendation", "top", "excellent", "without reservation")
        scorer.add_if(
            "endorsement",
            any(term in lowered for term in endorsement_terms),
            weight=8,
            strength="Strong endorsement language",
            weakness="Endorsement language could be stronger",
            suggestion="Request explicit recommendation language from the referee",
        )

        # Length
        scorer.add_if(
            "length",
            word_count(text) >= 200,
            weight=6,
            strength="Adequate letter length",
            weakness="Letter may be too brief for a strong recommendation",
            suggestion="Request a detailed letter with specific project examples",
        )

        return scorer.build()
