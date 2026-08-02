from dataclasses import dataclass
from hashlib import sha256
from typing import Protocol

from langchain_core.documents import Document

from app.rag.types import KnowledgeSource
from app.rag.vector_store import VectorStoreManager
from app.utils.config import Settings, get_settings


@dataclass(frozen=True)
class ScoredDocument:
    document: Document
    score: float
    knowledge_source: KnowledgeSource


class BaseRetriever(Protocol):
    def retrieve(self, query: str, k: int | None = None) -> list[Document]:
        ...


def _dedupe_scored_documents(results: list[ScoredDocument]) -> list[ScoredDocument]:
    seen: set[str] = set()
    unique: list[ScoredDocument] = []

    for result in results:
        content_key = sha256(result.document.page_content.encode("utf-8")).hexdigest()
        if content_key in seen:
            continue
        seen.add(content_key)
        unique.append(result)

    return unique


def _merge_scored_results(
    results: list[ScoredDocument],
    *,
    k: int,
) -> list[Document]:
    """
    Merge scored results from multiple collections.

    Chroma returns lower scores for closer vectors (distance). Sort ascending.
    """
    deduped = _dedupe_scored_documents(results)
    deduped.sort(key=lambda item: item.score)

    documents: list[Document] = []
    for item in deduped[:k]:
        enriched = Document(
            page_content=item.document.page_content,
            metadata={
                **item.document.metadata,
                "retrieval_score": item.score,
                "retrieved_from": item.knowledge_source.value,
            },
        )
        documents.append(enriched)

    return documents


class StaticRetriever:
    """Retrieve relevant chunks from the static knowledge collection."""

    def __init__(
        self,
        vector_store: VectorStoreManager | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.vector_store = vector_store or VectorStoreManager(self.settings)

    def retrieve(self, query: str, k: int | None = None) -> list[Document]:
        top_k = k or self.settings.retrieval_top_k
        results = self.vector_store.similarity_search_static(query, k=top_k)
        return _merge_scored_results(
            [
                ScoredDocument(
                    document=document,
                    score=score,
                    knowledge_source=KnowledgeSource.STATIC,
                )
                for document, score in results
            ],
            k=top_k,
        )

    def as_langchain_retriever(self, k: int | None = None):
        """Expose a LangChain-compatible retriever for chains and agents."""
        top_k = k or self.settings.retrieval_top_k
        return self.vector_store.get_static_store().as_retriever(search_kwargs={"k": top_k})


class ApplicationRetriever:
    """Retrieve relevant chunks from an application-specific collection."""

    def __init__(
        self,
        application_id: str,
        vector_store: VectorStoreManager | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.application_id = application_id
        self.settings = settings or get_settings()
        self.vector_store = vector_store or VectorStoreManager(self.settings)

    def retrieve(self, query: str, k: int | None = None) -> list[Document]:
        top_k = k or self.settings.retrieval_top_k
        results = self.vector_store.similarity_search_application(
            self.application_id,
            query,
            k=top_k,
        )
        return _merge_scored_results(
            [
                ScoredDocument(
                    document=document,
                    score=score,
                    knowledge_source=KnowledgeSource.APPLICATION,
                )
                for document, score in results
            ],
            k=top_k,
        )

    def as_langchain_retriever(self, k: int | None = None):
        """Expose a LangChain-compatible retriever for chains and agents."""
        top_k = k or self.settings.retrieval_top_k
        return self.vector_store.get_application_store(self.application_id).as_retriever(
            search_kwargs={"k": top_k}
        )


class HybridRetriever:
    """
    Search static and application collections, then merge the most relevant chunks.
    """

    def __init__(
        self,
        application_id: str | None = None,
        vector_store: VectorStoreManager | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.application_id = application_id
        self.settings = settings or get_settings()
        self.vector_store = vector_store or VectorStoreManager(self.settings)
        self.static_retriever = StaticRetriever(self.vector_store, self.settings)

        self.application_retriever: ApplicationRetriever | None = None
        if application_id:
            self.application_retriever = ApplicationRetriever(
                application_id,
                self.vector_store,
                self.settings,
            )

    def retrieve(self, query: str, k: int | None = None) -> list[Document]:
        top_k = k or self.settings.retrieval_top_k
        per_source_k = top_k

        scored_results: list[ScoredDocument] = []

        static_results = self.vector_store.similarity_search_static(query, k=per_source_k)
        scored_results.extend(
            ScoredDocument(
                document=document,
                score=score,
                knowledge_source=KnowledgeSource.STATIC,
            )
            for document, score in static_results
        )

        if self.application_retriever and self.application_id:
            application_results = self.vector_store.similarity_search_application(
                self.application_id,
                query,
                k=per_source_k,
            )
            scored_results.extend(
                ScoredDocument(
                    document=document,
                    score=score,
                    knowledge_source=KnowledgeSource.APPLICATION,
                )
                for document, score in application_results
            )

        return _merge_scored_results(scored_results, k=top_k)

    def get_static_retriever(self) -> StaticRetriever:
        return self.static_retriever

    def get_application_retriever(self) -> ApplicationRetriever | None:
        return self.application_retriever
