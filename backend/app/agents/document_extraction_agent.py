"""Document extraction agent — loads documents and builds the applicant profile."""

from __future__ import annotations

from app.agents.pipeline_helpers import build_retrieval_query, format_application_information
from app.agents.state import AnalysisGraphState
from app.chains import DocumentExtractionChain
from app.chains.extraction_parser import ApplicantProfile
from app.services.document_service import DocumentService
from app.services.requirement_service import RequirementService


def document_extraction_agent(state: AnalysisGraphState) -> AnalysisGraphState:
    """Load uploaded documents, extract structured content, and merge the profile."""
    ctx = state["ctx"]
    llm = state["llm"]

    ctx.documents = DocumentService.list_by_application(ctx.application_id)
    ctx.requirements = RequirementService.sync_status_from_documents(
        ctx.application_id,
        ctx.documents,
    )
    ctx.retrieval_query = build_retrieval_query(ctx.application, ctx.requirements)
    ctx.application_information = format_application_information(ctx.application, ctx.requirements)

    extraction_chain = DocumentExtractionChain(llm=llm)
    ctx.applicant_profile = extraction_chain.extract(ctx.documents)

    if ctx.applicant_profile is None:
        ctx.applicant_profile = ApplicantProfile()

    return state
