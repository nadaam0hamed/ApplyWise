"""Document data access."""

from app.db.schema import DOCUMENT_COLUMNS
from app.db.supabase import get_supabase_client
from app.models import Document
from app.models.constants import DOCUMENT_TYPE_LABELS
from app.services.application_service import ApplicationService
from app.services.exceptions import ApplicationNotFoundError


class DocumentService:
    @staticmethod
    def list_by_application(application_id: str) -> list[Document]:
        ApplicationService.get_by_id(application_id)

        response = (
            get_supabase_client()
            .table("documents")
            .select(DOCUMENT_COLUMNS)
            .eq("application_id", application_id)
            .order("uploaded_at", desc=True)
            .execute()
        )

        rows = response.data or []
        return [Document.model_validate(row) for row in rows]

    @staticmethod
    def build_summaries(documents: list[Document]) -> list[str]:
        if not documents:
            return []

        summaries: list[str] = []
        for document in documents:
            label = DOCUMENT_TYPE_LABELS.get(document.document_type or "", document.file_name)
            uploaded_at = document.uploaded_at.isoformat()
            summaries.append(
                f"{label} ({document.file_name}): uploaded {uploaded_at}, "
                f"mime_type={document.mime_type}, size={document.file_size} bytes"
            )
        return summaries
