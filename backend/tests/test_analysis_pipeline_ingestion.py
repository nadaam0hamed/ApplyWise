"""Tests for RAG document ingestion during the analysis pipeline."""

from datetime import datetime
from unittest.mock import MagicMock, patch

from app.agents.requirement_retrieval_agent import requirement_retrieval_agent
from app.agents.state import AnalysisGraphState
from app.models import Application, Document
from app.services.pipeline_context import AnalysisPipelineContext


def _application() -> Application:
    return Application(
        id="app-ingest",
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
        application_id="app-ingest",
        file_name="cv.pdf",
        document_type="cv",
        storage_path="/cv.pdf",
        uploaded_at=datetime(2026, 1, 10),
        file_size=512,
        mime_type="application/pdf",
    )


def test_requirement_retrieval_indexes_uploaded_documents():
    ctx = AnalysisPipelineContext(
        application_id="app-ingest",
        application=_application(),
        documents=[_document()],
        retrieval_query="scholarship requirements",
    )

    mock_ingester = MagicMock()

    with (
        patch("app.agents.pipeline_helpers.ApplicationKnowledgeIngester", return_value=mock_ingester),
        patch("app.agents.pipeline_helpers.load_document_text", return_value="CV content"),
        patch("app.agents.pipeline_helpers.HybridRetriever") as mock_retriever_cls,
    ):
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = []
        mock_retriever_cls.return_value = mock_retriever

        requirement_retrieval_agent({"ctx": ctx, "llm": MagicMock()})

    mock_ingester.reset_application.assert_called_once_with("app-ingest")
    mock_ingester.ingest_text.assert_called_once_with(
        "app-ingest",
        "CV content",
        source_name="cv.pdf",
        metadata={"document_id": "doc-1", "document_type": "cv"},
    )
    mock_retriever_cls.assert_called_once_with(application_id="app-ingest")
    mock_retriever.retrieve.assert_called_once_with("scholarship requirements")
    assert ctx.retriever is mock_retriever
    assert ctx.retrieved_documents == []
