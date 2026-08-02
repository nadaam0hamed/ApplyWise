from pathlib import Path
from typing import Any

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document

from app.rag.types import DocumentSourceType, KnowledgeSource


def _base_metadata(
    *,
    source_type: DocumentSourceType,
    knowledge_source: KnowledgeSource,
    source_name: str,
    application_id: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "source_type": source_type.value,
        "knowledge_source": knowledge_source.value,
        "source_name": source_name,
    }
    if application_id:
        metadata["application_id"] = application_id
    if extra:
        metadata.update(extra)
    return metadata


def load_pdf_file(
    file_path: Path,
    *,
    knowledge_source: KnowledgeSource,
    application_id: str | None = None,
) -> list[Document]:
    """Load a PDF file from disk."""
    loader = PyPDFLoader(str(file_path))
    documents = loader.load()
    for document in documents:
        document.metadata.update(
            _base_metadata(
                source_type=DocumentSourceType.PDF,
                knowledge_source=knowledge_source,
                source_name=file_path.name,
                application_id=application_id,
                extra={"source_path": str(file_path.resolve())},
            )
        )
    return documents


def load_pdf_directory(
    directory: Path,
    *,
    knowledge_source: KnowledgeSource = KnowledgeSource.STATIC,
    application_id: str | None = None,
    recursive: bool = False,
) -> list[Document]:
    """Load every PDF file from a directory."""
    if not directory.exists():
        return []

    pattern = "**/*.pdf" if recursive else "*.pdf"
    documents: list[Document] = []
    for pdf_path in sorted(directory.glob(pattern)):
        documents.extend(
            load_pdf_file(
                pdf_path,
                knowledge_source=knowledge_source,
                application_id=application_id,
            )
        )
    return documents


def load_text_content(
    text: str,
    *,
    source_name: str,
    knowledge_source: KnowledgeSource,
    application_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> list[Document]:
    """Load extracted text from scholarship documents or other sources."""
    document = Document(
        page_content=text,
        metadata=_base_metadata(
            source_type=DocumentSourceType.TEXT,
            knowledge_source=knowledge_source,
            source_name=source_name,
            application_id=application_id,
            extra=metadata,
        ),
    )
    return [document]


def load_text_file(
    file_path: Path,
    *,
    knowledge_source: KnowledgeSource,
    application_id: str | None = None,
) -> list[Document]:
    """Load a plain-text file from disk."""
    loader = TextLoader(str(file_path), encoding="utf-8")
    documents = loader.load()
    for document in documents:
        document.metadata.update(
            _base_metadata(
                source_type=DocumentSourceType.TEXT,
                knowledge_source=knowledge_source,
                source_name=file_path.name,
                application_id=application_id,
                extra={"source_path": str(file_path.resolve())},
            )
        )
    return documents


def load_from_url(
    url: str,
    *,
    knowledge_source: KnowledgeSource,
    application_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> list[Document]:
    """
    Placeholder for future URL ingestion.

    Will support scholarship pages, university requirements, and other web sources.
    """
    raise NotImplementedError(
        "URL ingestion is not implemented yet. "
        f"Planned source: {url!r} ({knowledge_source.value})."
    )
