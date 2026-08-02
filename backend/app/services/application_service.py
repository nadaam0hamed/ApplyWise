"""Application data access."""

from app.db.queries import fetch_maybe_single
from app.db.schema import APPLICATION_COLUMNS
from app.db.supabase import get_supabase_client
from app.models import Application
from app.services.exceptions import ApplicationNotFoundError
from app.utils.readiness_score import normalize_readiness_score


class ApplicationService:
    @staticmethod
    def get_by_id(application_id: str) -> Application:
        row = fetch_maybe_single(
            get_supabase_client()
            .table("applications")
            .select(APPLICATION_COLUMNS)
            .eq("id", application_id)
        )

        if row is None:
            raise ApplicationNotFoundError(f"Application `{application_id}` was not found.")

        return Application.model_validate(row)

    @staticmethod
    def update_status(application_id: str, *, status: str) -> None:
        (
            get_supabase_client()
            .table("applications")
            .update({"status": status})
            .eq("id", application_id)
            .execute()
        )

    @staticmethod
    def update_after_analysis(
        application_id: str,
        *,
        readiness_score: int | float | str,
        status: str,
    ) -> None:
        score = normalize_readiness_score(readiness_score)
        (
            get_supabase_client()
            .table("applications")
            .update({"readiness_score": score, "status": status})
            .eq("id", application_id)
            .execute()
        )
