from dataclasses import dataclass, field
from pathlib import Path
import shutil
from typing import Any

from langchain_core.documents import Document

from app.rag.document_loader import load_pdf_directory, load_pdf_file, load_text_content
from app.rag.retriever import ApplicationRetriever, HybridRetriever, StaticRetriever
from app.rag.text_splitter import split_documents
from app.rag.types import DocumentSourceType, KnowledgeSource
from app.rag.vector_store import VectorStoreManager, application_collection_name
from app.utils.config import Settings, get_settings


@dataclass
class IngestionResult:
    source_name: str
    documents_loaded: int = 0
    chunks_created: int = 0
    chunks_stored: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class StaticKnowledgeIngester:
    """Ingest PDFs from backend/knowledge/static/ into the static collection."""

    def __init__(
        self,
        vector_store: VectorStoreManager | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.vector_store = vector_store or VectorStoreManager(self.settings)

    def ingest(self, *, force_rebuild: bool = False) -> IngestionResult:
        static_dir = self.settings.static_knowledge_dir
        static_dir.mkdir(parents=True, exist_ok=True)

        if force_rebuild:
            self.vector_store.reset_static_collection()

        documents = load_pdf_directory(
            static_dir,
            knowledge_source=KnowledgeSource.STATIC,
            recursive=True,
        )
        chunks = split_documents(documents, self.settings)
        stored = self.vector_store.add_documents_to_static(chunks)

        return IngestionResult(
            source_name=self.settings.static_collection_name,
            documents_loaded=len(documents),
            chunks_created=len(chunks),
            chunks_stored=stored,
            metadata={"directory": str(static_dir.resolve())},
        )


class ApplicationKnowledgeIngester:
    """Ingest scholarship documents into an application-specific collection."""

    def __init__(
        self,
        vector_store: VectorStoreManager | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.vector_store = vector_store or VectorStoreManager(self.settings)

    def ingest_pdf(
        self,
        application_id: str,
        pdf_path: Path,
        *,
        persist_copy: bool = True,
    ) -> IngestionResult:
        source_path = Path(pdf_path)
        if not source_path.exists():
            raise FileNotFoundError(f"PDF not found: {source_path}")

        if persist_copy:
            storage_dir = self.vector_store.application_storage_dir(application_id)
            destination = storage_dir / source_path.name
            if source_path.resolve() != destination.resolve():
                shutil.copy2(source_path, destination)
            source_path = destination

        documents = load_pdf_file(
            source_path,
            knowledge_source=KnowledgeSource.APPLICATION,
            application_id=application_id,
        )
        return self._ingest_documents(application_id, documents, source_name=source_path.name)

    def ingest_text(
        self,
        application_id: str,
        text: str,
        *,
        source_name: str = "extracted_text",
        metadata: dict[str, Any] | None = None,
    ) -> IngestionResult:
        documents = load_text_content(
            text,
            source_name=source_name,
            knowledge_source=KnowledgeSource.APPLICATION,
            application_id=application_id,
            metadata=metadata,
        )
        return self._ingest_documents(application_id, documents, source_name=source_name)

    def ingest_documents(
        self,
        application_id: str,
        documents: list[Document],
    ) -> IngestionResult:
        source_name = documents[0].metadata.get("source_name", "documents") if documents else "documents"
        return self._ingest_documents(application_id, documents, source_name=source_name)

    def reset_application(self, application_id: str) -> None:
        self.vector_store.reset_application_collection(application_id)

    def _ingest_documents(
        self,
        application_id: str,
        documents: list[Document],
        *,
        source_name: str,
    ) -> IngestionResult:
        chunks = split_documents(documents, self.settings)
        stored = self.vector_store.add_documents_to_application(application_id, chunks)

        return IngestionResult(
            source_name=source_name,
            documents_loaded=len(documents),
            chunks_created=len(chunks),
            chunks_stored=stored,
            metadata={
                "application_id": application_id,
                "collection": application_collection_name(application_id),
            },
        )


class HybridRAGPipeline:
    """
    High-level facade for ingestion and retrieval.

    Designed to be consumed by future LangChain chains and agents.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.vector_store = VectorStoreManager(self.settings)
        self.static_ingester = StaticKnowledgeIngester(self.vector_store, self.settings)
        self.application_ingester = ApplicationKnowledgeIngester(self.vector_store, self.settings)

    def ingest_static_knowledge(self, *, force_rebuild: bool = False) -> IngestionResult:
        return self.static_ingester.ingest(force_rebuild=force_rebuild)

    def ingest_application_pdf(
        self,
        application_id: str,
        pdf_path: Path,
        *,
        persist_copy: bool = True,
    ) -> IngestionResult:
        return self.application_ingester.ingest_pdf(
            application_id,
            pdf_path,
            persist_copy=persist_copy,
        )

    def ingest_application_text(
        self,
        application_id: str,
        text: str,
        *,
        source_name: str = "extracted_text",
        metadata: dict[str, Any] | None = None,
    ) -> IngestionResult:
        return self.application_ingester.ingest_text(
            application_id,
            text,
            source_name=source_name,
            metadata=metadata,
        )

    def get_static_retriever(self) -> StaticRetriever:
        return StaticRetriever(self.vector_store, self.settings)

    def get_application_retriever(self, application_id: str) -> ApplicationRetriever:
        return ApplicationRetriever(application_id, self.vector_store, self.settings)

    def get_hybrid_retriever(self, application_id: str | None = None) -> HybridRetriever:
        return HybridRetriever(application_id, self.vector_store, self.settings)
