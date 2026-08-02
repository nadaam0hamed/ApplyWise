import re
from pathlib import Path

import chromadb
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from app.rag.embeddings import resolve_embeddings
from app.utils.config import Settings, get_settings

APPLICATION_COLLECTION_PREFIX = "application_"
COLLECTION_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9._-]{3,512}$")


def sanitize_application_id(application_id: str) -> str:
    """Normalize application IDs for safe Chroma collection names."""
    sanitized = re.sub(r"[^a-zA-Z0-9_-]", "_", application_id.strip())
    sanitized = re.sub(r"_+", "_", sanitized).strip("_")
    if not sanitized:
        raise ValueError("application_id must contain at least one alphanumeric character")
    return sanitized


def application_collection_name(application_id: str) -> str:
    """Build the Chroma collection name for an application."""
    safe_id = sanitize_application_id(application_id)
    name = f"{APPLICATION_COLLECTION_PREFIX}{safe_id}"
    if len(name) > 63:
        name = name[:63].rstrip("_-")
    if not COLLECTION_NAME_PATTERN.match(name):
        raise ValueError(f"Invalid collection name generated: {name!r}")
    return name


class VectorStoreManager:
    """Manage persistent Chroma collections for static and application knowledge."""

    def __init__(
        self,
        settings: Settings | None = None,
        embeddings: Embeddings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.embeddings = embeddings or resolve_embeddings(self.settings)
        self.persist_directory = self.settings.chroma_persist_path
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(self.persist_directory))

    @property
    def client(self) -> chromadb.PersistentClient:
        return self._client

    def get_static_store(self) -> Chroma:
        return Chroma(
            client=self._client,
            collection_name=self.settings.static_collection_name,
            embedding_function=self.embeddings,
            persist_directory=str(self.persist_directory),
        )

    def get_application_store(self, application_id: str) -> Chroma:
        return Chroma(
            client=self._client,
            collection_name=application_collection_name(application_id),
            embedding_function=self.embeddings,
            persist_directory=str(self.persist_directory),
        )

    def static_collection_exists(self) -> bool:
        return self.settings.static_collection_name in {
            collection.name for collection in self._client.list_collections()
        }

    def application_collection_exists(self, application_id: str) -> bool:
        collection_name = application_collection_name(application_id)
        return collection_name in {collection.name for collection in self._client.list_collections()}

    def reset_static_collection(self) -> None:
        if self.static_collection_exists():
            self._client.delete_collection(self.settings.static_collection_name)

    def reset_application_collection(self, application_id: str) -> None:
        collection_name = application_collection_name(application_id)
        if collection_name in {collection.name for collection in self._client.list_collections()}:
            self._client.delete_collection(collection_name)

    def add_documents_to_static(self, documents: list[Document]) -> int:
        if not documents:
            return 0

        store = self.get_static_store()
        ids = store.add_documents(documents)
        return len(ids)

    def add_documents_to_application(self, application_id: str, documents: list[Document]) -> int:
        if not documents:
            return 0

        store = self.get_application_store(application_id)
        ids = store.add_documents(documents)
        return len(ids)

    def similarity_search_static(self, query: str, k: int) -> list[tuple[Document, float]]:
        store = self.get_static_store()
        if not self.static_collection_exists():
            return []
        return store.similarity_search_with_score(query, k=k)

    def similarity_search_application(
        self,
        application_id: str,
        query: str,
        k: int,
    ) -> list[tuple[Document, float]]:
        if not self.application_collection_exists(application_id):
            return []

        store = self.get_application_store(application_id)
        return store.similarity_search_with_score(query, k=k)

    def application_storage_dir(self, application_id: str) -> Path:
        safe_id = sanitize_application_id(application_id)
        path = self.settings.dynamic_knowledge_dir / safe_id
        path.mkdir(parents=True, exist_ok=True)
        return path
