"""Requirement retrieval agent — indexes documents and retrieves from both knowledge bases."""

from __future__ import annotations

from app.agents.pipeline_helpers import index_application_documents
from app.agents.state import AnalysisGraphState


def requirement_retrieval_agent(state: AnalysisGraphState) -> AnalysisGraphState:
    """Index uploaded documents and retrieve requirements from static and dynamic KBs."""
    ctx = state["ctx"]

    ctx.retriever = index_application_documents(ctx.application_id, ctx.documents)
    ctx.retrieved_documents = ctx.retriever.retrieve(ctx.retrieval_query)

    return state
