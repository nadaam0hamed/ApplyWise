"""Research proposal quality evaluator."""

from __future__ import annotations

from app.chains.extraction_parser import ApplicantProfile, ExtractedDocument
from app.models import Document, Requirement
from app.schemas.document_evaluation import DocumentEvaluationLLMOutput
from app.services.document_evaluation.evaluators.base import BaseDocumentEvaluator
from app.services.document_evaluation.rule_based import (
    RuleBasedScorer,
    has_closing_paragraph,
    has_opening_paragraph,
    merge_grammar_feedback,
    word_count,
)


class ResearchProposalEvaluator(BaseDocumentEvaluator):
    supported_types = ("research_proposal",)

    def evaluation_criteria(self) -> str:
        return (
            "- Clear research question or hypothesis\n"
            "- Literature context and gap identification\n"
            "- Methodology and feasible timeline\n"
            "- Alignment with target program or supervisor expertise\n"
            "- Expected contributions to the field"
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
        text = document_text or ""
        lowered = text.lower()
        scorer = RuleBasedScorer()

        sections = {
            "research_question": ("research question", "objective", "aim", "hypothesis"),
            "methodology": ("methodology", "methods", "approach", "data collection"),
            "literature": ("literature", "background", "related work", "prior research"),
            "timeline": ("timeline", "schedule", "milestones", "phases"),
            "contribution": ("contribution", "significance", "impact", "novel"),
        }

        for name, keywords in sections.items():
            label = name.replace("_", " ").title()
            scorer.add_if(
                name,
                any(keyword in lowered for keyword in keywords),
                weight=15,
                strength=f"{label} section addressed",
                weakness=f"{label} not clearly present",
                suggestion=f"Add a dedicated {label.lower()} section",
            )

        scorer.add_if(
            "opening",
            has_opening_paragraph(text),
            weight=8,
            strength="Clear introduction present",
            weakness="Introduction missing or too brief",
            suggestion="Open with the research problem and its significance",
        )

        scorer.add_if(
            "length",
            word_count(text) >= 500,
            weight=10,
            strength="Adequate depth for a research proposal",
            weakness="Proposal may be too brief",
            suggestion="Expand with methodology details and expected outcomes",
        )

        scorer.add_if(
            "closing",
            has_closing_paragraph(text),
            weight=7,
            strength="Conclusion or closing section present",
            weakness="Conclusion missing",
            suggestion="Summarize expected contributions and next steps",
        )

        output = scorer.build()
        return merge_grammar_feedback(output, text)
