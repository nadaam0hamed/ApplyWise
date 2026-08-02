"""Shared helpers for LangGraph analysis agents."""

from __future__ import annotations

from app.models import Application, Document, Requirement
from app.rag.ingestion import ApplicationKnowledgeIngester
from app.rag.retriever import HybridRetriever
from app.services.document_content_service import DocumentContentError, load_document_text
from app.services.requirement_service import RequirementService


def format_application_information(
    application: Application,
    requirements: list[Requirement],
) -> str:
    requirement_block = RequirementService.format_for_prompt(requirements)
    return (
        f"Application ID: {application.id}\n"
        f"Type: {application.application_type}\n"
        f"Title/Program: {application.title or 'N/A'}\n"
        f"Country: {application.country or 'N/A'}\n"
        f"Source URL: {application.source_url or 'N/A'}\n"
        f"Current status: {application.status}\n\n"
        f"Requirements:\n{requirement_block}"
    )


def build_retrieval_query(application: Application, requirements: list[Requirement]) -> str:
    requirement_titles = ", ".join(
        requirement.title or requirement.category for requirement in requirements
    )
    return (
        f"{application.title or 'scholarship application'} "
        f"{application.country or ''} requirements documents {requirement_titles}"
    ).strip()


def index_application_documents(application_id: str, documents: list[Document]) -> HybridRetriever:
    """Index uploaded documents into the dynamic KB and return a HybridRetriever."""
    ingester = ApplicationKnowledgeIngester()
    ingester.reset_application(application_id)

    for document in documents:
        try:
            text = load_document_text(document)
        except DocumentContentError:
            continue

        ingester.ingest_text(
            application_id,
            text,
            source_name=document.file_name,
            metadata={
                "document_id": document.id,
                "document_type": document.document_type or "other",
            },
        )

    return HybridRetriever(application_id=application_id)
