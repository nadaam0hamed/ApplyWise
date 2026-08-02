"""LangGraph workflow for the ApplyWise analysis pipeline."""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agents.document_extraction_agent import document_extraction_agent
from app.agents.professional_document_evaluation_agent import professional_document_evaluation_agent
from app.agents.report_generation_agent import report_generation_agent
from app.agents.requirement_matching_agent import requirement_matching_agent
from app.agents.requirement_retrieval_agent import requirement_retrieval_agent
from app.agents.state import AnalysisGraphState
from app.agents.timeline_agent import timeline_agent
from app.services.pipeline_context import AnalysisPipelineContext

_COMPILED_WORKFLOW = None


def create_analysis_workflow():
    """Build the linear analysis StateGraph for multi-agent orchestration."""
    graph = StateGraph(AnalysisGraphState)

    graph.add_node("document_extraction", document_extraction_agent)
    graph.add_node("requirement_retrieval", requirement_retrieval_agent)
    graph.add_node("requirement_matching", requirement_matching_agent)
    graph.add_node("professional_document_evaluation", professional_document_evaluation_agent)
    graph.add_node("report_generation", report_generation_agent)
    # Skip timeline for faster analysis
    # graph.add_node("timeline", timeline_agent)

    graph.add_edge(START, "document_extraction")
    graph.add_edge("document_extraction", "requirement_retrieval")
    graph.add_edge("requirement_retrieval", "requirement_matching")
    graph.add_edge("requirement_matching", "professional_document_evaluation")
    graph.add_edge("professional_document_evaluation", "report_generation")
    # graph.add_edge("report_generation", "timeline")
    # graph.add_edge("timeline", END)
    graph.add_edge("report_generation", END)

    return graph.compile()


def get_analysis_workflow():
    """Return a cached compiled workflow instance."""
    global _COMPILED_WORKFLOW
    if _COMPILED_WORKFLOW is None:
        _COMPILED_WORKFLOW = create_analysis_workflow()
    return _COMPILED_WORKFLOW


def run_analysis_workflow(ctx: AnalysisPipelineContext, llm: Any) -> AnalysisPipelineContext:
    """Execute the LangGraph analysis workflow and return the updated pipeline context."""
    result = get_analysis_workflow().invoke({"ctx": ctx, "llm": llm})
    return result["ctx"]
