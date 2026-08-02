"""Motivation letter quality evaluator."""

from __future__ import annotations

from app.chains.extraction_parser import ApplicantProfile, ExtractedDocument
from app.models import Document, Requirement
from app.schemas.document_evaluation import DocumentEvaluationLLMOutput
from app.services.document_evaluation.evaluators.base import BaseDocumentEvaluator
from app.services.document_evaluation.rule_based import (
    GENERIC_PHRASES,
    RuleBasedScorer,
    has_closing_paragraph,
    has_opening_paragraph,
    has_personal_story_markers,
    merge_grammar_feedback,
    word_count,
)


class MotivationLetterEvaluator(BaseDocumentEvaluator):
    supported_types = ("motivation_letter",)

    def evaluation_criteria(self) -> str:
        return (
            "- Opening paragraph with clear intent\n"
            "- Motivation for applying to this specific program\n"
            "- Scholarship or program fit\n"
            "- Career goals alignment\n"
            "- Personal story with specific examples\n"
            "- Grammar and professional structure\n"
            "- Closing paragraph"
        )

    def uses_subjective_llm(self) -> bool:
        return True

    def subjective_criteria(self) -> str:
        return (
            "- Authenticity and persuasiveness of the narrative\n"
            "- Emotional engagement without generic phrasing\n"
            "- Flow between motivation, fit, and career goals"
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
        sop = extracted.sop if extracted else (applicant_profile.sop if applicant_profile else None)
        text = document_text or ""
        lowered = text.lower()

        scorer = RuleBasedScorer()

        # Opening
        scorer.add_if(
            "opening",
            has_opening_paragraph(text),
            weight=10,
            strength="Clear opening paragraph present",
            weakness="Opening paragraph missing or too brief",
            suggestion="Open with a specific reason for choosing this program",
        )

        # Motivation
        motivation_present = bool(sop and sop.motivation) or any(
            kw in lowered for kw in ("motivat", "reason for applying", "why i want", "drawn to")
        )
        scorer.add_if(
            "motivation",
            motivation_present,
            weight=15,
            strength="Clear motivation statement present",
            weakness="Motivation for applying is unclear or missing",
            suggestion="Explain why this program aligns with your goals",
        )

        # Scholarship / program fit
        fit_present = any(
            kw in lowered for kw in ("scholarship", "program", "university", "fit", "align")
        )
        scorer.add_if(
            "scholarship_fit",
            fit_present,
            weight=12,
            strength="Program or scholarship fit addressed",
            weakness="Program or scholarship fit not clearly explained",
            suggestion="Explain how you meet the scholarship criteria and program goals",
        )

        # Career goals
        career_present = bool(sop and sop.career_goals) or any(
            kw in lowered for kw in ("career", "future", "long-term", "aspir")
        )
        scorer.add_if(
            "career_goals",
            career_present,
            weight=12,
            strength="Career goals articulated",
            weakness="Career goals not clearly stated",
            suggestion="Explain how this program fits your short- and long-term goals",
        )

        # Personal story
        scorer.add_if(
            "personal_story",
            has_personal_story_markers(text),
            weight=10,
            strength="Personal story with specific examples",
            weakness="Personal narrative lacks specific examples",
            suggestion="Include concrete experiences that shaped your motivation",
        )

        # Length / depth
        wc = word_count(text)
        scorer.add_if(
            "length",
            wc >= 250,
            weight=8,
            strength="Sufficient depth and detail",
            weakness="Letter may be too brief",
            suggestion="Expand with specific examples from your background",
        )

        # Generic phrasing (inverse check)
        has_generic = any(phrase in lowered for phrase in GENERIC_PHRASES)
        scorer.add_if(
            "avoid_generic",
            not has_generic,
            weight=8,
            strength="Avoids common generic phrasing",
            weakness="Contains generic phrasing",
            suggestion="Replace generic statements with program-specific reasons",
        )

        # Closing
        scorer.add_if(
            "closing",
            has_closing_paragraph(text),
            weight=10,
            strength="Professional closing paragraph present",
            weakness="Closing paragraph or sign-off missing",
            suggestion="End with a clear closing and professional sign-off",
        )

        output = scorer.build()
        return merge_grammar_feedback(output, text)
