"""Base class and shared helpers for document quality evaluators."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate

from app.chains.extraction_parser import ApplicantProfile, ExtractedDocument
from app.models import Document, Requirement
from app.schemas.document_evaluation import (
    DocumentEvaluationLLMOutput,
    DocumentEvaluationResult,
    SubjectiveWritingLLMOutput,
    merge_missing_information,
    score_to_completeness_label,
    score_to_completeness_level,
    score_to_quality_rating,
)
from app.services.document_evaluation.rule_based import merge_evaluations

SUBJECTIVE_WRITING_PROMPT = PromptTemplate(
    input_variables=[
        "document_type_label",
        "file_name",
        "document_text",
        "subjective_criteria",
        "format_instructions",
    ],
    template="""You are a senior admissions consultant assessing ONLY the subjective writing quality of an application document.

Do NOT evaluate factual completeness, contact details, scores, dates, or structured fields — those are scored separately by deterministic rules.

Focus exclusively on:
{subjective_criteria}

## Document type
{document_type_label}

## File name
{file_name}

## Document text
{document_text}

Provide writing quality feedback only. Score writing_quality_score from 0-100.

{format_instructions}
""",
)


def build_requirements_context(requirements: list[Requirement]) -> str:
    if not requirements:
        return "No specific program requirements available."
    lines = []
    for requirement in requirements[:12]:
        label = requirement.title or requirement.category
        required = "required" if requirement.is_required else "optional"
        lines.append(f"- {label} ({required})")
    return "\n".join(lines)


def find_extracted_document(
    profile: ApplicantProfile | None,
    document: Document,
) -> ExtractedDocument | None:
    if not profile:
        return None

    for extracted in profile.documents:
        if extracted.document_id == document.id:
            return extracted

    document_type = document.document_type or ""
    for extracted in profile.documents:
        if extracted.document_type == document_type:
            return extracted

    return None


class BaseDocumentEvaluator(ABC):
    """Template for type-specific document quality evaluation.

    Evaluation is always deterministic (rule-based) for objective checks.
    LLM is invoked only when ``uses_subjective_llm`` is True and only for
    subjective writing quality — never for factual/objective criteria.
    """

    supported_types: tuple[str, ...] = ()

    @abstractmethod
    def evaluation_criteria(self) -> str:
        """Return document-type-specific evaluation rubric (for documentation / subjective prompt)."""

    @abstractmethod
    def evaluate_rule_based(
        self,
        *,
        document: Document,
        extracted: ExtractedDocument | None,
        applicant_profile: ApplicantProfile | None,
        requirements: list[Requirement],
        document_text: str | None,
    ) -> DocumentEvaluationLLMOutput:
        """Deterministic evaluation for all objective checks."""

    def uses_subjective_llm(self) -> bool:
        """Whether this document type benefits from LLM subjective writing assessment."""
        return False

    def subjective_criteria(self) -> str:
        """Criteria passed to the LLM for subjective writing quality only."""
        return (
            "- Clarity, coherence, and flow of prose\n"
            "- Professional and authentic tone\n"
            "- Persuasiveness and narrative quality\n"
            "- Avoidance of generic or vague language"
        )

    def supports(self, document_type: str) -> bool:
        return document_type in self.supported_types

    def evaluate(
        self,
        *,
        document: Document,
        applicant_profile: ApplicantProfile | None,
        requirements: list[Requirement],
        document_text: str | None,
        llm: BaseChatModel | None = None,
        document_type_label: str = "",
    ) -> DocumentEvaluationResult:
        document_type = document.document_type or "other"
        extracted = find_extracted_document(applicant_profile, document)
        extracted_information = _build_extracted_information(extracted)
        base_kwargs = {
            "document_id": document.id,
            "file_name": document.file_name,
            "document_name": document.file_name,
            "document_type": document_type,
            "uploaded": True,
            "extracted_information": extracted_information,
        }

        if extracted and extracted.extraction_status == "skipped":
            return DocumentEvaluationResult(
                **base_kwargs,
                quality_score=0,
                completeness_level=score_to_completeness_level(
                    0,
                    uploaded=True,
                    evaluation_status="skipped",
                ),
                completeness=score_to_completeness_label(0),
                quality_rating=score_to_quality_rating(0),
                weaknesses=["Content could not be extracted for evaluation"],
                missing_information=["Content could not be extracted for evaluation"],
                suggestions=["Re-upload a readable PDF or DOCX version of this document"],
                confidence=0.0,
                evaluation_status="skipped",
                error_message=extracted.error_message,
            )

        # Step 1: Always run deterministic rule-based evaluation
        objective_output = self.evaluate_rule_based(
            document=document,
            extracted=extracted,
            applicant_profile=applicant_profile,
            requirements=requirements,
            document_text=document_text,
        )

        # Step 2: Optionally supplement with LLM for subjective writing quality only
        subjective_output: DocumentEvaluationLLMOutput | None = None
        used_llm = False
        if self.uses_subjective_llm() and llm and document_text:
            try:
                subjective_raw = self._evaluate_subjective_with_llm(
                    llm=llm,
                    document=document,
                    document_text=document_text,
                    document_type_label=document_type_label or document_type,
                )
                subjective_output = DocumentEvaluationLLMOutput(
                    quality_score=subjective_raw.writing_quality_score,
                    strengths=subjective_raw.strengths,
                    weaknesses=subjective_raw.weaknesses,
                    suggestions=subjective_raw.suggestions,
                    confidence=subjective_raw.confidence,
                )
                used_llm = True
            except Exception:
                subjective_output = None

        llm_output = merge_evaluations(objective_output, subjective_output)

        score = max(0, min(100, llm_output.quality_score))
        missing_information = merge_missing_information(
            llm_output.weaknesses,
            llm_output.missing_information,
        )
        confidence = llm_output.confidence if used_llm else min(0.95, llm_output.confidence)
        return DocumentEvaluationResult(
            **base_kwargs,
            quality_score=score,
            completeness_level=score_to_completeness_level(score),
            completeness=score_to_completeness_label(score),
            quality_rating=score_to_quality_rating(score),
            strengths=llm_output.strengths,
            weaknesses=llm_output.weaknesses,
            missing_information=missing_information,
            suggestions=llm_output.suggestions,
            confidence=confidence,
            evaluation_status="success",
        )

    def _evaluate_subjective_with_llm(
        self,
        *,
        llm: BaseChatModel,
        document: Document,
        document_text: str,
        document_type_label: str,
    ) -> SubjectiveWritingLLMOutput:
        parser = PydanticOutputParser(pydantic_object=SubjectiveWritingLLMOutput)
        chain = SUBJECTIVE_WRITING_PROMPT | llm | parser
        return chain.invoke(
            {
                "document_type_label": document_type_label,
                "file_name": document.file_name,
                "document_text": document_text,
                "subjective_criteria": self.subjective_criteria(),
                "format_instructions": parser.get_format_instructions(),
            }
        )


def _build_extracted_information(extracted: ExtractedDocument | None) -> dict[str, Any]:
    if not extracted or extracted.extraction_status != "success":
        return {}
    payload = extracted.model_dump(
        exclude={
            "document_id",
            "file_name",
            "document_type",
            "extraction_status",
            "error_message",
        },
        exclude_none=True,
    )
    return {key: value for key, value in payload.items() if value not in ({}, [], "")}


def clamp_score(value: int, *, minimum: int = 0, maximum: int = 100) -> int:
    return max(minimum, min(maximum, value))


def has_quantified_achievement(text: str) -> bool:
    from app.services.document_evaluation.rule_based import has_quantified_achievement as _has
    return _has(text)
