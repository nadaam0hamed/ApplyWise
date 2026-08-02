"""Financial documents quality evaluator."""

from __future__ import annotations

from app.chains.extraction_parser import ApplicantProfile, ExtractedDocument
from app.models import Document, Requirement
from app.schemas.document_evaluation import DocumentEvaluationLLMOutput
from app.services.document_evaluation.evaluators.base import BaseDocumentEvaluator
from app.services.document_evaluation.rule_based import RuleBasedScorer, has_section, parse_date, word_count


class FinancialDocumentsEvaluator(BaseDocumentEvaluator):
    supported_types = ("financial_documents", "financial_proof")

    def evaluation_criteria(self) -> str:
        return (
            "- Official bank statements or sponsorship letters\n"
            "- Account holder name matches applicant\n"
            "- Clear balance or funding amount\n"
            "- Recent issue date within required window\n"
            "- Bank letterhead or official stamps"
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
        text = document_text or ""
        lowered = text.lower()

        if not text:
            return DocumentEvaluationLLMOutput(
                quality_score=0,
                weaknesses=["Financial document content unavailable"],
                suggestions=["Upload official bank statements or sponsorship letters"],
            )

        scorer = RuleBasedScorer()

        scorer.add_if(
            "bank_documentation",
            has_section(lowered, "bank", "account", "financial institution", "statement"),
            weight=20,
            strength="Bank or financial institution information detected",
            weakness="No clear bank documentation detected",
            suggestion="Upload an official bank statement on letterhead",
        )
        scorer.add_if(
            "sponsor_documentation",
            has_section(lowered, "sponsor", "sponsorship", "affidavit of support", "guarantor"),
            weight=15,
            strength="Sponsorship information detected",
            weakness="No sponsorship documentation detected",
            suggestion="Include a formal sponsorship or affidavit of support letter if applicable",
        )
        scorer.add_if(
            "amount",
            has_section(lowered, "balance", "amount", "usd", "eur", "gbp", "$", "funds"),
            weight=25,
            strength="Funding amount or balance detected",
            weakness="No clear funding amount detected",
            suggestion="Ensure the document shows sufficient funds for the program duration",
        )
        scorer.add_if(
            "date",
            parse_date(text) is not None or has_section(lowered, "date", "issued", "period", "statement date"),
            weight=20,
            strength="Issue date or statement period detected",
            weakness="No issue date detected",
            suggestion="Ensure documents are recent (typically within 3-6 months)",
        )
        scorer.add_if(
            "readability",
            word_count(text) >= 30,
            weight=20,
            strength="Financial document content is readable",
            weakness="Document may be incomplete or unreadable",
            suggestion="Upload a complete, legible financial document",
        )

        output = scorer.build()
        output.suggestions.append(
            "Ensure documents are recent and show sufficient funds for the program duration"
        )
        return output
