"""Document evaluation agent — professional quality assessment for uploaded documents."""

from __future__ import annotations

from app.agents.state import AnalysisGraphState
from app.services.document_evaluation import DocumentEvaluationService


def document_evaluation_agent(state: AnalysisGraphState) -> AnalysisGraphState:
    """Evaluate the quality of every uploaded document using type-specific evaluators."""
    ctx = state["ctx"]
    llm = state["llm"]

    service = DocumentEvaluationService(llm=llm)
    ctx.document_evaluations = service.evaluate_all(
        ctx.documents,
        applicant_profile=ctx.applicant_profile,
        requirements=ctx.requirements,
    )

    return state
