"""Shared mutable state for the analysis pipeline and LangGraph workflow."""

from __future__ import annotations

from dataclasses import dataclass, field

from langchain_core.documents import Document as LangChainDocument

from app.chains.extraction_parser import ApplicantProfile
from app.chains.output_parser import ApplicationAnalysisResult
from app.models import Application, Document, Requirement, StoredAnalysisRecord
from app.rag.retriever import HybridRetriever
from app.schemas.document_evaluation import DocumentEvaluationResult
from app.schemas.readiness_report import ReadinessReport
from app.schemas.requirement_matching import RequirementMatchingResult


@dataclass
class AnalysisPipelineContext:
    """Mutable state passed through each pipeline stage."""

    application_id: str
    application: Application
    documents: list[Document] = field(default_factory=list)
    requirements: list[Requirement] = field(default_factory=list)
    retrieval_query: str = ""
    application_information: str = ""
    applicant_profile: ApplicantProfile | None = None
    retriever: HybridRetriever | None = None
    retrieved_documents: list[LangChainDocument] = field(default_factory=list)
    requirement_matching: RequirementMatchingResult | None = None
    document_evaluations: list[DocumentEvaluationResult] | None = None
    analysis_result: ApplicationAnalysisResult | None = None
    report: ReadinessReport | None = None
    saved_record: StoredAnalysisRecord | None = None
