"""Domain models for the ApplyWise backend."""

from datetime import datetime

from pydantic import BaseModel, Field


class Application(BaseModel):
    id: str
    user_id: str
    application_type: str
    status: str
    title: str | None = None
    country: str | None = None
    source_url: str | None = None
    readiness_score: float | None = None
    created_at: datetime


class Document(BaseModel):
    id: str
    application_id: str
    file_name: str
    document_type: str | None = None
    storage_path: str
    uploaded_at: datetime
    file_size: int
    mime_type: str


class Requirement(BaseModel):
    id: str
    application_id: str
    category: str
    created_at: datetime
    title: str | None = None
    is_required: bool = False
    is_fulfilled: bool = False


class StoredAnalysisRecord(BaseModel):
    id: str
    application_id: str
    readiness_score: float | None = None
    missing_documents: list[dict] | None = None
    recommendations: dict | list | None = None
    strengths: list[str] | None = None
    weaknesses: list[str] | None = None
    created_at: datetime


class MissingDocumentEntry(BaseModel):
    name: str
    priority: str = Field(default="medium", pattern="^(high|medium|low)$")
