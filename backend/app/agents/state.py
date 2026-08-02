"""Shared LangGraph state for the analysis workflow."""

from __future__ import annotations

from typing import Any, TypedDict

from app.services.pipeline_context import AnalysisPipelineContext


class AnalysisGraphState(TypedDict):
    """State passed between analysis workflow nodes."""

    ctx: AnalysisPipelineContext
    llm: Any
