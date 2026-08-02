"""Professional document quality evaluation orchestrator."""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel

from app.chains.extraction_parser import ApplicantProfile
from app.models import Document, Requirement
from app.models.constants import DOCUMENT_TYPE_LABELS
from app.schemas.document_evaluation import DocumentEvaluationResult
from app.services.document_content_service import DocumentContentError, load_document_text
from app.services.document_evaluation.evaluators import (
    BaseDocumentEvaluator,
    CVEvaluator,
    FinancialDocumentsEvaluator,
    GenericDocumentEvaluator,
    GraduationCertificateEvaluator,
    LanguageCertificateEvaluator,
    MotivationLetterEvaluator,
    PassportEvaluator,
    RecommendationLetterEvaluator,
    ResearchProposalEvaluator,
    SOPEvaluator,
    TranscriptEvaluator,
)

_FILENAME_TYPE_HINTS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("research", "proposal"), "research_proposal"),
    (("bank", "financial", "sponsor", "statement"), "financial_documents"),
    (("graduation", "degree", "diploma"), "diploma"),
    (("cv", "resume", "curriculum"), "cv"),
    (("motivation",), "motivation_letter"),
    (("sop", "statement"), "statement_of_purpose"),
    (("recommend", "reference"), "letter_of_recommendation"),
    (("transcript",), "academic_transcript"),
    (("passport",), "passport"),
    (("ielts",), "ielts_score"),
    (("toefl",), "toefl_score"),
)


class DocumentEvaluationService:
    """Routes each uploaded document to the appropriate quality evaluator."""

    def __init__(self, *, llm: BaseChatModel | None = None) -> None:
        self.llm = llm
        self._evaluators: list[BaseDocumentEvaluator] = [
            CVEvaluator(),
            MotivationLetterEvaluator(),
            SOPEvaluator(),
            RecommendationLetterEvaluator(),
            TranscriptEvaluator(),
            PassportEvaluator(),
            LanguageCertificateEvaluator(),
            GraduationCertificateEvaluator(),
            ResearchProposalEvaluator(),
            FinancialDocumentsEvaluator(),
            GenericDocumentEvaluator(),
        ]
        self._evaluator_by_type = self._index_evaluators()

    def evaluate_all(
        self,
        documents: list[Document],
        *,
        applicant_profile: ApplicantProfile | None,
        requirements: list[Requirement],
    ) -> list[DocumentEvaluationResult]:
        results: list[DocumentEvaluationResult] = []
        for document in documents:
            results.append(
                self.evaluate_document(
                    document,
                    applicant_profile=applicant_profile,
                    requirements=requirements,
                )
            )
        return results

    def evaluate_document(
        self,
        document: Document,
        *,
        applicant_profile: ApplicantProfile | None,
        requirements: list[Requirement],
    ) -> DocumentEvaluationResult:
        document_type = _resolve_document_type(document)
        evaluator = self._evaluator_by_type.get(document_type, self._evaluator_by_type["other"])
        label = DOCUMENT_TYPE_LABELS.get(document_type, document.file_name)

        document_text: str | None = None
        try:
            document_text = load_document_text(document)
        except DocumentContentError:
            document_text = None

        return evaluator.evaluate(
            document=document.model_copy(update={"document_type": document_type}),
            applicant_profile=applicant_profile,
            requirements=requirements,
            document_text=document_text,
            llm=self.llm,
            document_type_label=label,
        )

    def _index_evaluators(self) -> dict[str, BaseDocumentEvaluator]:
        mapping: dict[str, BaseDocumentEvaluator] = {}
        for evaluator in self._evaluators:
            for document_type in evaluator.supported_types:
                mapping[document_type] = evaluator
        mapping.setdefault("other", GenericDocumentEvaluator())
        return mapping


def _resolve_document_type(document: Document) -> str:
    document_type = document.document_type or "other"
    if document_type != "other":
        return document_type

    file_name = (document.file_name or "").lower()
    for keywords, resolved_type in _FILENAME_TYPE_HINTS:
        if any(keyword in file_name for keyword in keywords):
            return resolved_type
    return document_type
