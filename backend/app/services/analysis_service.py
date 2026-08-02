"""AI analysis orchestration and persistence.

Pipeline execution flow::

    Upload Documents
         ↓
    Document Extraction
         ↓
    Applicant Profile
         ↓
    HybridRetriever
         ↓
    Requirement Matching
         ↓
    Professional Document Evaluation
         ↓
    Report Generation
         ↓
    Save Report
         ↓
    Return Response
"""

from __future__ import annotations

import traceback

from langchain_core.exceptions import OutputParserException

from app.agents.workflow import run_analysis_workflow
from app.chains import HuggingFaceAnalysisLLMProvider
from app.chains.extraction_parser import ApplicantProfile
from app.chains.huggingface_provider import HuggingFaceInferenceConfigurationError
from app.chains.output_parser import ApplicationAnalysisResult
from app.db.queries import MultipleRowsError, fetch_single_row
from app.db.schema import AI_ANALYSIS_COLUMNS
from app.db.supabase import SupabaseConfigurationError, get_supabase_client
from app.models import Application, Document, MissingDocumentEntry, Requirement, StoredAnalysisRecord
from app.models.constants import ApplicationStatus, DOCUMENT_TYPE_LABELS
from app.schemas.analysis import AnalyzeResponse
from app.schemas.readiness_report import ReadinessReport
from app.schemas.requirement_matching import RequirementMatchingResult
from app.services.application_service import ApplicationService
from app.services.exceptions import AnalysisServiceError
from app.services.readiness_report_builder import (
    document_assessment_to_evaluations,
    timeline_to_legacy,
)
from app.services.pipeline_context import AnalysisPipelineContext


def _derive_profile_strength(score: int) -> str:
    if score >= 80:
        return "Strong"
    if score >= 50:
        return "Moderate"
    return "Needs Improvement"


def _to_missing_document_entries(items: list[str]) -> list[dict]:
    return [
        MissingDocumentEntry(name=item, priority="medium").model_dump()
        for item in items
        if item.strip()
    ]


def _build_applicant_info(
    application: Application,
    applicant_profile: ApplicantProfile | None,
) -> dict:
    name = "Applicant"
    if applicant_profile and applicant_profile.passport and applicant_profile.passport.full_name:
        name = applicant_profile.passport.full_name

    return {
        "name": name,
        "email": "",
        "phone": "",
        "target_program": application.title or "",
        "target_university": application.country or "",
    }


def _build_stored_recommendations(
    result: ApplicationAnalysisResult,
    *,
    report: ReadinessReport,
    application: Application,
    documents: list[Document],
    requirements: list[Requirement],
    applicant_profile: ApplicantProfile | None = None,
    requirement_matching: RequirementMatchingResult | None = None,
) -> dict:
    readiness_score = report.overall_readiness.readiness_score
    missing_requirements = [
        {
            "name": requirement.title or requirement.category,
            "category": requirement.category,
            "priority": "high" if requirement.is_required else "medium",
        }
        for requirement in requirements
        if not requirement.is_fulfilled
    ]

    uploaded_documents = [
        {
            "name": DOCUMENT_TYPE_LABELS.get(document.document_type or "", document.file_name),
            "status": "complete",
            "date": document.uploaded_at.date().isoformat(),
        }
        for document in documents
    ]

    checklist = [
        {
            "item": requirement.title or requirement.category,
            "completed": requirement.is_fulfilled,
        }
        for requirement in requirements
    ]

    return {
        "summary": result.recommendations,
        "improvement_suggestions": result.recommendations,
        "recommended_next_steps": result.next_steps,
        "missing_requirements": missing_requirements,
        "document_evaluations": document_assessment_to_evaluations(report.document_assessment),
        "uploaded_documents": uploaded_documents,
        "checklist": checklist,
        "timeline": timeline_to_legacy(report.timeline),
        "applicant_info": _build_applicant_info(application, applicant_profile),
        "applicant_profile": applicant_profile.model_dump() if applicant_profile else None,
        "requirement_comparisons": (
            [comparison.model_dump() for comparison in requirement_matching.comparisons]
            if requirement_matching
            else []
        ),
        "retrieved_requirements": (
            [item.model_dump() for item in requirement_matching.retrieved_requirements]
            if requirement_matching
            else []
        ),
        "profile_strength": _derive_profile_strength(readiness_score),
        "scholarship_name": application.title,
        "eligibility_score": readiness_score,
        "readiness_status": report.overall_readiness.status,
        "readiness_report": report.model_dump(),
        "final_verdict": report.final_verdict.model_dump(),
    }


class AnalysisService:
    """Orchestrates the document-to-report analysis pipeline via LangGraph."""

    @staticmethod
    def _create_llm():
        return HuggingFaceAnalysisLLMProvider().create_chat_model()

    @staticmethod
    def _pipeline_save_report(ctx: AnalysisPipelineContext) -> None:
        """Persist report and analysis snapshot to ai_analysis."""
        if ctx.analysis_result is None or ctx.report is None:
            raise AnalysisServiceError("Report must be built before saving.")

        result = ctx.analysis_result
        readiness_score = ctx.report.overall_readiness.readiness_score
        payload = {
            "application_id": ctx.application_id,
            "readiness_score": readiness_score,
            "missing_documents": _to_missing_document_entries(result.missing_documents),
            "strengths": result.strengths,
            "weaknesses": result.weaknesses,
            "recommendations": _build_stored_recommendations(
                result,
                report=ctx.report,
                application=ctx.application,
                documents=ctx.documents,
                requirements=ctx.requirements,
                applicant_profile=ctx.applicant_profile,
                requirement_matching=ctx.requirement_matching,
            ),
        }

        try:
            row = fetch_single_row(
                get_supabase_client()
                .table("ai_analysis")
                .insert(payload)
                .select(AI_ANALYSIS_COLUMNS),
                not_found_message="Failed to persist analysis result to ai_analysis.",
            )
        except (LookupError, MultipleRowsError) as exc:
            raise AnalysisServiceError(str(exc)) from exc

        ctx.saved_record = StoredAnalysisRecord.model_validate(row)

    @staticmethod
    def _pipeline_build_response(ctx: AnalysisPipelineContext) -> AnalyzeResponse:
        """Return backward-compatible API response with optional report."""
        if ctx.analysis_result is None or ctx.saved_record is None or ctx.report is None:
            raise AnalysisServiceError("Pipeline incomplete — cannot build response.")

        return AnalyzeResponse(
            application_id=ctx.application_id,
            analysis_id=ctx.saved_record.id,
            created_at=ctx.saved_record.created_at,
            report=ctx.report,
            **ctx.analysis_result.model_dump(),
        )

    @staticmethod
    def run_analysis(application_id: str) -> AnalyzeResponse:
        application = ApplicationService.get_by_id(application_id)
        ApplicationService.update_status(application_id, status=ApplicationStatus.ANALYZING)

        ctx = AnalysisPipelineContext(
            application_id=application_id,
            application=application,
        )

        try:
            llm = AnalysisService._create_llm()

            ctx = run_analysis_workflow(ctx, llm)
            AnalysisService._pipeline_save_report(ctx)

            ApplicationService.update_after_analysis(
                application_id,
                readiness_score=ctx.report.overall_readiness.readiness_score if ctx.report else 0,
                status=ApplicationStatus.READY,
            )

            return AnalysisService._pipeline_build_response(ctx)
        except (
            ApplicationNotFoundError,
            SupabaseConfigurationError,
            HuggingFaceInferenceConfigurationError,
            OutputParserException,
        ) as exc:
            ApplicationService.update_status(
                application_id,
                status=ApplicationStatus.IN_PROGRESS,
            )
            raise AnalysisServiceError(str(exc)) from exc
        except Exception as exc:
            traceback.print_exc()

            ApplicationService.update_status(
                application_id,
                status=ApplicationStatus.IN_PROGRESS,
            )

            raise


# Avoid circular import for type used in except clause
from app.services.exceptions import ApplicationNotFoundError  # noqa: E402
