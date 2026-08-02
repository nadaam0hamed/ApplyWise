from functools import lru_cache

from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings

from app.utils.config import Settings, get_settings


@lru_cache
def get_embeddings(embedding_model: str) -> Embeddings:
    """
    Return a local embedding model.

    Uses HuggingFace sentence-transformers by default so the pipeline works
    without OpenAI. Swap this provider later when OpenAI embeddings are enabled.
    """
    return HuggingFaceEmbeddings(
        model_name=embedding_model,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def resolve_embeddings(settings: Settings | None = None) -> Embeddings:
    config = settings or get_settings()
    return get_embeddings(config.embedding_model)
