"""Professional document evaluation agent — independent quality assessment per upload."""

from __future__ import annotations

from app.agents.state import AnalysisGraphState
from app.services.document_evaluation import DocumentEvaluationService


def professional_document_evaluation_agent(state: AnalysisGraphState) -> AnalysisGraphState:
    """Evaluate every uploaded document independently and store results on the pipeline context."""
    ctx = state["ctx"]
    llm = state["llm"]

    service = DocumentEvaluationService(llm=llm)
    ctx.document_evaluations = service.evaluate_all(
        ctx.documents,
        applicant_profile=ctx.applicant_profile,
        requirements=ctx.requirements,
    )

    return state
