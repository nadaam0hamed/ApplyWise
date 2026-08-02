"""Requirement matching agent — deterministic requirement comparison via RAG."""

from __future__ import annotations

from app.agents.state import AnalysisGraphState
from app.chains.extraction_parser import ApplicantProfile
from app.services.exceptions import AnalysisServiceError
from app.services.requirement_matching_engine import RequirementMatchingEngine


def requirement_matching_agent(state: AnalysisGraphState) -> AnalysisGraphState:
    """Match applicant profile and documents against scholarship requirements."""
    ctx = state["ctx"]

    if ctx.retriever is None:
        raise AnalysisServiceError("HybridRetriever must be initialised before requirement matching.")

    matching_engine = RequirementMatchingEngine(
        application_id=ctx.application_id,
        retriever=ctx.retriever,
    )
    ctx.requirement_matching = matching_engine.match(
        ctx.applicant_profile or ApplicantProfile(),
        ctx.documents,
        retrieval_query=ctx.retrieval_query,
        application_requirements=ctx.requirements,
    )

    return state
