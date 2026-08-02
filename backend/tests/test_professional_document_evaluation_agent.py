"""Unit tests for the ProfessionalDocumentEvaluationAgent LangGraph node."""

from datetime import datetime
from unittest.mock import MagicMock, patch

from app.agents.professional_document_evaluation_agent import professional_document_evaluation_agent
from app.agents.state import AnalysisGraphState
from app.chains.extraction_parser import ApplicantProfile
from app.models import Application, Document
from app.schemas.document_evaluation import DocumentEvaluationResult
from app.services.pipeline_context import AnalysisPipelineContext


def _application() -> Application:
    return Application(
        id="app-1",
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
        application_id="app-1",
        file_name="cv.pdf",
        document_type="cv",
        storage_path="/cv.pdf",
        uploaded_at=datetime(2026, 1, 10),
        file_size=512,
        mime_type="application/pdf",
    )


def _graph_state(ctx: AnalysisPipelineContext, llm: MagicMock | None = None) -> AnalysisGraphState:
    return {"ctx": ctx, "llm": llm or MagicMock()}


def test_professional_document_evaluation_agent_evaluates_each_document():
    ctx = AnalysisPipelineContext(application_id="app-1", application=_application())
    ctx.documents = [_document(), _document()]
    ctx.documents[1].id = "doc-2"
    ctx.documents[1].file_name = "passport.pdf"
    ctx.documents[1].document_type = "passport"
    ctx.applicant_profile = ApplicantProfile()
    ctx.requirements = []

    mock_results = [
        DocumentEvaluationResult(
            document_id="doc-1",
            file_name="cv.pdf",
            document_type="cv",
            quality_score=85,
            completeness="Complete",
            quality_rating="Good",
            strengths=["Clear structure"],
            weaknesses=[],
            suggestions=[],
        ),
        DocumentEvaluationResult(
            document_id="doc-2",
            file_name="passport.pdf",
            document_type="passport",
            quality_score=90,
            completeness="Complete",
            quality_rating="Excellent",
            strengths=["Valid expiry date"],
            weaknesses=[],
            suggestions=[],
        ),
    ]

    with patch(
        "app.agents.professional_document_evaluation_agent.DocumentEvaluationService"
    ) as mock_service_cls:
        mock_service = MagicMock()
        mock_service.evaluate_all.return_value = mock_results
        mock_service_cls.return_value = mock_service

        result_state = professional_document_evaluation_agent(_graph_state(ctx))

    mock_service_cls.assert_called_once()
    mock_service.evaluate_all.assert_called_once_with(
        ctx.documents,
        applicant_profile=ctx.applicant_profile,
        requirements=ctx.requirements,
    )
    assert result_state["ctx"].document_evaluations == mock_results
    assert len(result_state["ctx"].document_evaluations) == 2


def test_professional_document_evaluation_agent_stores_empty_list_when_no_documents():
    ctx = AnalysisPipelineContext(application_id="app-1", application=_application())
    ctx.documents = []

    with patch(
        "app.agents.professional_document_evaluation_agent.DocumentEvaluationService"
    ) as mock_service_cls:
        mock_service = MagicMock()
        mock_service.evaluate_all.return_value = []
        mock_service_cls.return_value = mock_service

        result_state = professional_document_evaluation_agent(_graph_state(ctx))

    assert result_state["ctx"].document_evaluations == []
