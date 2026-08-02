"""Report generation agent — RAG-backed LLM analysis and readiness report assembly."""

from __future__ import annotations

from app.agents.state import AnalysisGraphState
from app.chains import ApplicationAnalysisChain
from app.services.exceptions import AnalysisServiceError
from app.services.readiness_report_builder import build_readiness_report
from app.utils.readiness_score import normalize_readiness_score


def report_generation_agent(state: AnalysisGraphState) -> AnalysisGraphState:
    """Run ApplicationAnalysisChain and assemble the professional readiness report."""
    ctx = state["ctx"]
    llm = state["llm"]

    if ctx.retriever is None:
        raise AnalysisServiceError("HybridRetriever must be initialised before building the report.")

    chain = ApplicationAnalysisChain(llm=llm, retriever=ctx.retriever)
    document_summaries = (
        ctx.applicant_profile.to_summary_lines()
        if ctx.applicant_profile
        else ["No uploaded documents with extractable content."]
    )
    ctx.analysis_result = chain.analyze(
        application_information=ctx.application_information,
        document_summaries=document_summaries,
        retrieval_query=ctx.retrieval_query,
    )

    readiness_score = normalize_readiness_score(ctx.analysis_result.readiness_score)
    ctx.report = build_readiness_report(
        ctx.analysis_result,
        readiness_score=readiness_score,
        application=ctx.application,
        documents=ctx.documents,
        requirements=ctx.requirements,
        applicant_profile=ctx.applicant_profile,
        requirement_matching=ctx.requirement_matching,
        document_evaluations=ctx.document_evaluations,
    )

    return state
