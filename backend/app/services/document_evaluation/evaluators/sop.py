"""Statement of Purpose quality evaluator."""

from __future__ import annotations

from app.chains.extraction_parser import ApplicantProfile, ExtractedDocument
from app.models import Document, Requirement
from app.schemas.document_evaluation import DocumentEvaluationLLMOutput
from app.services.document_evaluation.evaluators.base import BaseDocumentEvaluator
from app.services.document_evaluation.rule_based import (
    RuleBasedScorer,
    has_closing_paragraph,
    has_opening_paragraph,
    has_personal_story_markers,
    merge_grammar_feedback,
    word_count,
)


class SOPEvaluator(BaseDocumentEvaluator):
    supported_types = ("statement_of_purpose",)

    def evaluation_criteria(self) -> str:
        return (
            "- Clear academic and research goals\n"
            "- Connection between past experience and proposed study\n"
            "- Fit with faculty, department, or research area\n"
            "- Career trajectory linked to the program\n"
            "- Coherent narrative structure\n"
            "- Grammar and professional writing"
        )

    def uses_subjective_llm(self) -> bool:
        return True

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

        scorer.add_if(
            "opening",
            has_opening_paragraph(text),
            weight=8,
            strength="Clear opening paragraph present",
            weakness="Opening paragraph missing or too brief",
            suggestion="Open with your academic focus and program intent",
        )

        scorer.add_field(
            "study_goals",
            sop.study_goals if sop else None,
            weight=15,
            strength="Study goals clearly defined",
            weakness="Study goals not clearly articulated",
            suggestion="State specific research or academic objectives",
        )

        scorer.add_field(
            "motivation",
            sop.motivation if sop else None,
            weight=12,
            strength="Motivation for the program is present",
            weakness="Motivation for the program is unclear",
            suggestion="Explain why this specific program is the right fit",
        )

        scorer.add_field(
            "career_goals",
            sop.career_goals if sop else None,
            weight=12,
            strength="Career trajectory linked to the program",
            weakness="Career goals not clearly stated",
            suggestion="Connect the program to your long-term career plans",
        )

        research_terms = ("research", "thesis", "methodology", "hypothesis", "publication", "faculty")
        scorer.add_if(
            "research_orientation",
            any(term in lowered for term in research_terms),
            weight=12,
            strength="Research orientation demonstrated",
            weakness="Research focus not clearly demonstrated",
            suggestion="Reference relevant research experience or faculty interests",
        )

        scorer.add_if(
            "personal_narrative",
            has_personal_story_markers(text),
            weight=10,
            strength="Personal narrative with specific examples",
            weakness="Narrative lacks specific personal examples",
            suggestion="Include concrete experiences that led to your academic goals",
        )

        scorer.add_if(
            "length",
            word_count(text) >= 400,
            weight=10,
            strength="Adequate depth for an SOP",
            weakness="SOP may lack sufficient depth",
            suggestion="Develop key paragraphs with concrete examples",
        )

        scorer.add_if(
            "closing",
            has_closing_paragraph(text),
            weight=8,
            strength="Professional closing present",
            weakness="Closing paragraph missing",
            suggestion="End with a concise summary of your fit and intent",
        )

        if sop and sop.leadership:
            scorer.add(
                "leadership",
                True,
                weight=8,
                strength="Leadership or initiative examples included",
            )

        output = scorer.build()
        return merge_grammar_feedback(output, text)
