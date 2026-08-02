"""Timeline agent — builds the application action timeline from analysis outputs."""

from __future__ import annotations

from app.agents.state import AnalysisGraphState
from app.services.readiness_report_builder import _build_missing_documents, _build_timeline


def timeline_agent(state: AnalysisGraphState) -> AnalysisGraphState:
    """Return the report timeline when already present, otherwise build it."""
    ctx = state["ctx"]

    if ctx.report is None:
        return state

    if ctx.report.timeline:
        return state

    if ctx.analysis_result is not None:
        missing_docs = _build_missing_documents(ctx.analysis_result)
        ctx.report.timeline = _build_timeline(
            ctx.analysis_result,
            missing_docs,
            ctx.application,
        )

    return state
