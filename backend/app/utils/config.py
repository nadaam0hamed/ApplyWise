from functools import lru_cache
import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseModel):
    """Application settings loaded from environment variables."""

    app_name: str = Field(default="ApplyWise API")
    app_version: str = Field(default="0.1.0")
    app_env: Literal["development", "staging", "production"] = Field(default="development")
    debug: bool = Field(default=True)

    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)

    cors_origins: str = Field(default="http://localhost:3000")

    # OpenAI (future)
    openai_api_key: str | None = Field(default=None)
    openai_model: str = Field(default="gpt-4o-mini")

    # Supabase
    supabase_url: str | None = Field(default=None)
    supabase_service_role_key: str | None = Field(default=None)

    # ChromaDB / RAG
    chroma_persist_directory: str = Field(default="chroma_data")
    static_collection_name: str = Field(default="static_knowledge")
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    chunk_size: int = Field(default=1000)
    chunk_overlap: int = Field(default=200)
    retrieval_top_k: int = Field(default=5)

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def chroma_persist_path(self) -> Path:
        path = Path(self.chroma_persist_directory)
        if path.is_absolute():
            return path
        return BACKEND_ROOT / path

    @property
    def static_knowledge_dir(self) -> Path:
        return BACKEND_ROOT / "knowledge" / "static"

    @property
    def dynamic_knowledge_dir(self) -> Path:
        return BACKEND_ROOT / "knowledge" / "dynamic"


def _env_bool(key: str, default: bool) -> bool:
    value = os.getenv(key)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _load_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "ApplyWise API"),
        app_version=os.getenv("APP_VERSION", "0.1.0"),
        app_env=os.getenv("APP_ENV", "development"),  # type: ignore[arg-type]
        debug=_env_bool("DEBUG", True),
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        cors_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
        chroma_persist_directory=os.getenv("CHROMA_PERSIST_DIRECTORY", "chroma_data"),
        static_collection_name=os.getenv("STATIC_COLLECTION_NAME", "static_knowledge"),
        embedding_model=os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
        chunk_size=int(os.getenv("CHUNK_SIZE", "1000")),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "200")),
        retrieval_top_k=int(os.getenv("RETRIEVAL_TOP_K", "5")),
    )


@lru_cache
def get_settings() -> Settings:
    return _load_settings()
