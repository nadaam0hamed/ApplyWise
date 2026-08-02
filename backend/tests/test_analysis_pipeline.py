"""Integration tests for AnalysisService pipeline orchestration."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.agents.state import AnalysisGraphState
from app.chains.extraction_parser import ApplicantProfile, PassportFields
from app.chains.output_parser import ApplicationAnalysisResult
from app.models import Application, Document
from app.schemas.requirement_matching import RequirementMatchingResult
from app.schemas.readiness_report import (
    ApplicantProfileSummary,
    FinalVerdict,
    OverallReadiness,
    ReadinessReport,
)
from app.services.pipeline_context import AnalysisPipelineContext
from app.services.analysis_service import AnalysisService
from app.services.exceptions import AnalysisServiceError


def _application() -> Application:
    return Application(
        id="app-pipeline",
        user_id="user-1",
        application_type="scholarship",
        status="analyzing",
        title="Test Scholarship",
        country="UK",
        source_url=None,
        readiness_score=None,
        created_at=datetime(2026, 1, 1),
    )


def _document() -> Document:
    return Document(
        id="doc-1",
        application_id="app-pipeline",
        file_name="cv.pdf",
        document_type="cv",
        storage_path="/cv.pdf",
        uploaded_at=datetime(2026, 1, 10),
        file_size=512,
        mime_type="application/pdf",
    )


def _analysis_result() -> ApplicationAnalysisResult:
    return ApplicationAnalysisResult(
        readiness_score=75,
        strengths=["Good profile"],
        weaknesses=["Missing SOP"],
        missing_documents=["Statement of Purpose"],
        recommendations=["Upload SOP"],
        next_steps=["Draft SOP"],
    )


def _minimal_report() -> ReadinessReport:
    return ReadinessReport(
        overall_readiness=OverallReadiness(readiness_score=75, status="Moderate Readiness"),
        applicant_profile_summary=ApplicantProfileSummary(),
        final_verdict=FinalVerdict(
            summary="Moderate readiness.",
            recommendation="Proceed with Improvements",
            confidence="Moderate",
        ),
    )


def _graph_state(ctx: AnalysisPipelineContext, llm: MagicMock | None = None) -> AnalysisGraphState:
    return {"ctx": ctx, "llm": llm or MagicMock()}


@pytest.fixture
def pipeline_context() -> AnalysisPipelineContext:
    return AnalysisPipelineContext(
        application_id="app-pipeline",
        application=_application(),
    )


def test_pipeline_stage_order_load_extract_retriever_match_report_save(
    pipeline_context: AnalysisPipelineContext,
):
    """Verify pipeline stages execute in the required order."""
    stage_log: list[str] = []

    def document_extraction(state: AnalysisGraphState) -> AnalysisGraphState:
        stage_log.extend(["load", "extract", "profile"])
        ctx = state["ctx"]
        ctx.documents = [_document()]
        ctx.requirements = []
        ctx.retrieval_query = "query"
        ctx.application_information = "info"
        ctx.applicant_profile = ApplicantProfile(passport=PassportFields(full_name="Test User"))
        return state

    def requirement_retrieval(state: AnalysisGraphState) -> AnalysisGraphState:
        stage_log.append("retriever")
        state["ctx"].retriever = MagicMock()
        return state

    def requirement_matching(state: AnalysisGraphState) -> AnalysisGraphState:
        stage_log.append("match")
        state["ctx"].requirement_matching = RequirementMatchingResult()
        return state

    def document_evaluation(state: AnalysisGraphState) -> AnalysisGraphState:
        stage_log.append("evaluate")
        return state

    def report_generation(state: AnalysisGraphState) -> AnalysisGraphState:
        stage_log.append("report")
        ctx = state["ctx"]
        ctx.analysis_result = _analysis_result()
        ctx.report = _minimal_report()
        return state

    def timeline(state: AnalysisGraphState) -> AnalysisGraphState:
        return state

    with (
        patch("app.agents.workflow.document_extraction_agent", document_extraction),
        patch("app.agents.workflow.requirement_retrieval_agent", requirement_retrieval),
        patch("app.agents.workflow.requirement_matching_agent", requirement_matching),
        patch("app.agents.workflow.professional_document_evaluation_agent", document_evaluation),
        patch("app.agents.workflow.report_generation_agent", report_generation),
        patch("app.agents.workflow.timeline_agent", timeline),
        patch("app.agents.workflow._COMPILED_WORKFLOW", None),
        patch.object(AnalysisService, "_pipeline_save_report", side_effect=lambda ctx: (stage_log.append("save"), setattr(ctx, "saved_record", MagicMock(id="analysis-1", created_at=datetime(2026, 1, 20))))),
        patch.object(AnalysisService, "_create_llm", return_value=MagicMock()),
        patch("app.services.analysis_service.ApplicationService.get_by_id", return_value=_application()),
        patch("app.services.analysis_service.ApplicationService.update_status"),
        patch("app.services.analysis_service.ApplicationService.update_after_analysis"),
    ):
        response = AnalysisService.run_analysis("app-pipeline")

    assert stage_log == [
        "load",
        "extract",
        "profile",
        "retriever",
        "match",
        "evaluate",
        "report",
        "save",
    ]
    assert response.application_id == "app-pipeline"
    assert response.analysis_id == "analysis-1"
    assert response.readiness_score == 75


def test_requirement_retrieval_before_requirement_matching(pipeline_context: AnalysisPipelineContext):
    """HybridRetriever must exist before requirement matching runs."""
    with patch("app.agents.requirement_retrieval_agent.index_application_documents") as mock_index:
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = []
        mock_index.return_value = mock_retriever

        with patch("app.agents.requirement_matching_agent.RequirementMatchingEngine") as mock_engine_cls:
            mock_engine = MagicMock()
            mock_engine.match.return_value = RequirementMatchingResult()
            mock_engine_cls.return_value = mock_engine

            pipeline_context.documents = [_document()]
            pipeline_context.retrieval_query = "scholarship requirements"
            pipeline_context.applicant_profile = ApplicantProfile()

            from app.agents.requirement_retrieval_agent import requirement_retrieval_agent
            from app.agents.requirement_matching_agent import requirement_matching_agent

            requirement_retrieval_agent(_graph_state(pipeline_context))
            requirement_matching_agent(_graph_state(pipeline_context))

            mock_engine_cls.assert_called_once_with(
                application_id="app-pipeline",
                retriever=mock_retriever,
            )


def test_report_generation_uses_shared_retriever(pipeline_context: AnalysisPipelineContext):
    """Report generation reuses the shared HybridRetriever for LLM analysis."""
    mock_retriever = MagicMock()
    pipeline_context.retriever = mock_retriever
    pipeline_context.application_information = "info"
    pipeline_context.applicant_profile = ApplicantProfile()
    pipeline_context.retrieval_query = "query"

    mock_llm = MagicMock()

    with patch("app.agents.report_generation_agent.ApplicationAnalysisChain") as mock_chain_cls:
        mock_chain = MagicMock()
        mock_chain.analyze.return_value = _analysis_result()
        mock_chain_cls.return_value = mock_chain

        with patch(
            "app.agents.report_generation_agent.build_readiness_report",
            return_value=_minimal_report(),
        ):
            from app.agents.report_generation_agent import report_generation_agent

            report_generation_agent(_graph_state(pipeline_context, mock_llm))

        mock_chain_cls.assert_called_once_with(llm=mock_llm, retriever=mock_retriever)
        mock_chain.analyze.assert_called_once()


def test_report_generation_requires_retriever(pipeline_context: AnalysisPipelineContext):
    pipeline_context.retriever = None

    from app.agents.report_generation_agent import report_generation_agent

    with pytest.raises(AnalysisServiceError, match="HybridRetriever must be initialised"):
        report_generation_agent(_graph_state(pipeline_context, MagicMock()))


def test_requirement_matching_requires_retriever(pipeline_context: AnalysisPipelineContext):
    pipeline_context.retriever = None

    from app.agents.requirement_matching_agent import requirement_matching_agent

    with pytest.raises(AnalysisServiceError, match="HybridRetriever must be initialised"):
        requirement_matching_agent(_graph_state(pipeline_context))
