"""Requirement data access and fulfillment evaluation."""

from app.db.schema import REQUIREMENT_COLUMNS, REQUIREMENT_STATUS_COLUMNS
from app.db.supabase import get_supabase_client
from app.models import Document, Requirement
from app.models.constants import (
    REQUIREMENT_CATEGORY_LABELS,
    REQUIRED_CATEGORIES,
    RequirementCategory,
)
from app.services.application_service import ApplicationService


def _has_document_for_types(documents: list[Document], types: list[str]) -> bool:
    return any(document.document_type in types for document in documents)


def evaluate_requirement_fulfillment(category: str, documents: list[Document]) -> bool:
    """Mirrors frontend RequirementService.evaluateRequirementFulfillment."""
    match category:
        case RequirementCategory.DOCUMENTS:
            return len(documents) > 0
        case RequirementCategory.LANGUAGE:
            return _has_document_for_types(documents, ["ielts_score", "toefl_score"])
        case RequirementCategory.ACADEMIC:
            return _has_document_for_types(documents, ["academic_transcript"])
        case RequirementCategory.RECOMMENDATION:
            return _has_document_for_types(documents, ["letter_of_recommendation"])
        case RequirementCategory.IDENTITY:
            return _has_document_for_types(documents, ["passport"])
        case RequirementCategory.ELIGIBILITY:
            return _has_document_for_types(documents, ["cv", "academic_transcript"])
        case RequirementCategory.FINANCIAL:
            return _has_document_for_types(documents, ["other"])
        case RequirementCategory.DEADLINE:
            return True
        case _:
            return False


def _enrich_requirement(row: dict, status: str | None) -> Requirement:
    category = row["category"]
    return Requirement(
        id=row["id"],
        application_id=row["application_id"],
        category=category,
        created_at=row["created_at"],
        title=REQUIREMENT_CATEGORY_LABELS.get(category, category),
        is_required=category in REQUIRED_CATEGORIES,
        is_fulfilled=status == "fulfilled",
    )


class RequirementService:
    @staticmethod
    def _load_statuses(requirement_ids: list[str]) -> dict[str, str]:
        if not requirement_ids:
            return {}

        response = (
            get_supabase_client()
            .table("requirement_status")
            .select(REQUIREMENT_STATUS_COLUMNS)
            .in_("requirement_id", requirement_ids)
            .execute()
        )

        return {
            row["requirement_id"]: row["status"]
            for row in (response.data or [])
        }

    @staticmethod
    def list_by_application(application_id: str) -> list[Requirement]:
        ApplicationService.get_by_id(application_id)

        response = (
            get_supabase_client()
            .table("requirements")
            .select(REQUIREMENT_COLUMNS)
            .eq("application_id", application_id)
            .order("created_at")
            .execute()
        )

        rows = response.data or []
        status_map = RequirementService._load_statuses([row["id"] for row in rows])
        return [_enrich_requirement(row, status_map.get(row["id"])) for row in rows]

    @staticmethod
    def sync_status_from_documents(
        application_id: str,
        documents: list[Document],
    ) -> list[Requirement]:
        """Mirrors frontend RequirementService.syncStatusFromDocuments."""
        requirements = RequirementService.list_by_application(application_id)
        if not requirements:
            return requirements

        client = get_supabase_client()
        requirement_ids = [requirement.id for requirement in requirements]
        response = (
            client.table("requirement_status")
            .select(REQUIREMENT_STATUS_COLUMNS)
            .in_("requirement_id", requirement_ids)
            .execute()
        )
        existing_by_requirement = {
            row["requirement_id"]: row for row in (response.data or [])
        }

        for requirement in requirements:
            fulfilled = evaluate_requirement_fulfillment(requirement.category, documents)
            status = "fulfilled" if fulfilled else "missing"
            existing = existing_by_requirement.get(requirement.id)

            if existing:
                if existing["status"] != status:
                    (
                        client.table("requirement_status")
                        .update({"status": status})
                        .eq("id", existing["id"])
                        .execute()
                    )
            else:
                (
                    client.table("requirement_status")
                    .insert({"requirement_id": requirement.id, "status": status})
                    .execute()
                )

        return RequirementService.list_by_application(application_id)

    @staticmethod
    def format_for_prompt(requirements: list[Requirement]) -> str:
        if not requirements:
            return "No structured requirements recorded for this application."

        lines: list[str] = []
        for requirement in requirements:
            fulfillment = "fulfilled" if requirement.is_fulfilled else "missing"
            required = "required" if requirement.is_required else "optional"
            lines.append(
                f"- {requirement.title} ({requirement.category}): "
                f"{fulfillment}, {required}"
            )
        return "\n".join(lines)
