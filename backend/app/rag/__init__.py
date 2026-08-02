"""Hybrid RAG pipeline for static and application-specific knowledge."""

from app.rag.document_loader import (
    load_from_url,
    load_pdf_directory,
    load_pdf_file,
    load_text_content,
    load_text_file,
)
from app.rag.embeddings import get_embeddings, resolve_embeddings
from app.rag.ingestion import (
    ApplicationKnowledgeIngester,
    HybridRAGPipeline,
    IngestionResult,
    StaticKnowledgeIngester,
)
from app.rag.retriever import ApplicationRetriever, HybridRetriever, StaticRetriever
from app.rag.text_splitter import get_text_splitter, split_documents
from app.rag.types import DocumentSourceType, KnowledgeSource
from app.rag.vector_store import VectorStoreManager, application_collection_name

__all__ = [
    "ApplicationKnowledgeIngester",
    "ApplicationRetriever",
    "DocumentSourceType",
    "HybridRAGPipeline",
    "HybridRetriever",
    "IngestionResult",
    "KnowledgeSource",
    "StaticKnowledgeIngester",
    "StaticRetriever",
    "VectorStoreManager",
    "application_collection_name",
    "get_embeddings",
    "resolve_embeddings",
    "get_text_splitter",
    "load_from_url",
    "load_pdf_directory",
    "load_pdf_file",
    "load_text_content",
    "load_text_file",
    "split_documents",
]
