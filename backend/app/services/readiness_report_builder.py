"""Build the professional AI Readiness Report from analysis pipeline outputs."""

from __future__ import annotations

from datetime import date, timedelta

from app.chains.extraction_parser import ApplicantProfile, ExtractedDocument
from app.chains.output_parser import ApplicationAnalysisResult
from app.models import Application, Document, Requirement
from app.models.constants import DOCUMENT_TYPE_LABELS
from app.schemas.document_evaluation import DocumentEvaluationResult
from app.schemas.readiness_report import (
    AcademicInformation,
    ApplicantProfileSummary,
    DocumentAssessmentEntry,
    EligibilityComparisonRow,
    FinalVerdict,
    LanguageScores,
    OverallReadiness,
    PersonalInformation,
    ReadinessReport,
    TimelineEntry,
)
from app.schemas.requirement_matching import MatchStatus, RequirementMatchingResult

# Required document slots mirrored from frontend constants/documentTypes.ts
DOCUMENT_SLOTS: list[tuple[str, list[str]]] = [
    ("CV", ["cv"]),
    ("Passport", ["passport"]),
    ("Academic Transcript", ["academic_transcript"]),
    ("IELTS/TOEFL", ["ielts_score", "toefl_score"]),
    ("Recommendation Letter", ["letter_of_recommendation"]),
    ("Statement of Purpose", ["statement_of_purpose", "motivation_letter"]),
]

HIGH_PRIORITY_SLOTS = {"CV", "Academic Transcript", "IELTS/TOEFL"}


def _derive_readiness_status(score: int) -> str:
    if score >= 80:
        return "Ready"
    if score >= 60:
        return "Moderate Readiness"
    if score >= 40:
        return "Needs Improvement"
    return "Not Ready"


def _build_profile_summary(profile: ApplicantProfile | None) -> ApplicantProfileSummary:
    if not profile:
        return ApplicantProfileSummary()

    personal = PersonalInformation()
    if profile.passport:
        personal = PersonalInformation(
            full_name=profile.passport.full_name,
            nationality=profile.passport.nationality,
            passport_number=profile.passport.passport_number,
            passport_expiry=profile.passport.expiry_date,
        )

    academic = AcademicInformation()
    transcript = profile.transcript
    degree = profile.degree_certificate
    if transcript or degree:
        academic = AcademicInformation(
            university=(transcript.university if transcript else None) or (degree.university if degree else None),
            degree=(transcript.degree if transcript else None) or (degree.degree if degree else None),
            major=(transcript.major if transcript else None) or (degree.major if degree else None),
            gpa=transcript.gpa if transcript else None,
            graduation_year=(transcript.graduation_year if transcript else None)
            or (degree.graduation_year if degree else None),
        )

    language = LanguageScores()
    if profile.language_test:
        lt = profile.language_test
        language = LanguageScores(
            test_type=lt.test_type,
            overall_score=lt.overall_score,
            reading=lt.reading,
            listening=lt.listening,
            writing=lt.writing,
            speaking=lt.speaking,
        )

    skills: list[str] = list(profile.cv.skills) if profile.cv else []
    experience: list[str] = list(profile.cv.experience) if profile.cv else []
    leadership: list[str] = list(profile.cv.leadership) if profile.cv else []

    if profile.sop and profile.sop.leadership:
        leadership = leadership + [profile.sop.leadership]

    for letter in profile.recommendation_letters:
        leadership.extend(letter.strengths_mentioned)

    return ApplicantProfileSummary(
        personal_information=personal,
        academic_information=academic,
        language_scores=language,
        skills=skills,
        experience=experience,
        leadership=_dedupe(leadership),
    )


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        key = item.strip().lower()
        if key and key not in seen:
            seen.add(key)
            result.append(item.strip())
    return result


def _build_eligibility_comparison(
    matching: RequirementMatchingResult | None,
) -> list[EligibilityComparisonRow]:
    if not matching:
        return []

    rows: list[EligibilityComparisonRow] = []
    for comparison in matching.comparisons:
        status = (
            comparison.status.value
            if isinstance(comparison.status, MatchStatus)
            else str(comparison.status)
        )
        rows.append(
            EligibilityComparisonRow(
                requirement_name=comparison.field,
                required_value=comparison.requirement,
                applicant_value=comparison.applicant,
                status=status,
                confidence=comparison.confidence,
                explanation=comparison.reason,
                suggested_action=comparison.suggested_action,
                requirement=comparison.field,
                requirement_value=comparison.requirement,
                reason=comparison.reason,
            )
        )
    return rows


def _build_executive_summary(
    *,
    application: Application,
    readiness_score: int,
    matching: RequirementMatchingResult | None,
    result: ApplicationAnalysisResult,
) -> str:
    program = application.title or "this scholarship"
    if not matching or not matching.comparisons:
        return (
            f"Readiness score {readiness_score}/100 for {program}. "
            f"{len(result.missing_documents)} document gap(s) identified. "
            "Upload remaining materials and re-run analysis for requirement-level comparison."
        )

    comparisons = matching.comparisons
    pass_count = sum(1 for row in comparisons if row.status == MatchStatus.PASS)
    fail_count = sum(1 for row in comparisons if row.status == MatchStatus.FAIL)
    partial_count = sum(1 for row in comparisons if row.status == MatchStatus.PARTIAL)
    unknown_count = sum(1 for row in comparisons if row.status == MatchStatus.UNKNOWN)

    headline = (
        f"Readiness score {readiness_score}/100 for {program}. "
        f"Evaluated {len(comparisons)} requirement(s): "
        f"{pass_count} pass, {partial_count} partial, {fail_count} fail, {unknown_count} unknown."
    )
    if fail_count:
        failed_labels = ", ".join(row.field for row in comparisons if row.status == MatchStatus.FAIL)[:200]
        return f"{headline} Priority gaps: {failed_labels}."
    if partial_count:
        return f"{headline} Address partial matches before submission."
    return f"{headline} Core eligibility criteria appear satisfied."


def _build_missing_requirements(
    matching: RequirementMatchingResult | None,
    requirements: list[Requirement],
) -> list[dict]:
    entries: list[dict] = []

    if matching:
        for comparison in matching.comparisons:
            if comparison.status not in {MatchStatus.FAIL, MatchStatus.PARTIAL}:
                continue
            priority = "high" if comparison.status == MatchStatus.FAIL else "medium"
            entries.append(
                {
                    "name": comparison.field,
                    "status": comparison.status.value,
                    "required_value": comparison.requirement,
                    "applicant_value": comparison.applicant,
                    "priority": priority,
                    "suggested_action": comparison.suggested_action,
                }
            )

    seen_names = {entry["name"].lower() for entry in entries}
    for requirement in requirements:
        if requirement.is_fulfilled:
            continue
        name = (requirement.title or requirement.category or "Requirement").strip()
        if not name or name.lower() in seen_names:
            continue
        entries.append(
            {
                "name": name,
                "status": "FAIL" if requirement.is_required else "PARTIAL",
                "category": requirement.category,
                "priority": "high" if requirement.is_required else "medium",
                "suggested_action": "Complete this checklist requirement.",
            }
        )

    return entries


def _personalized_recommendations(
    result: ApplicationAnalysisResult,
    matching: RequirementMatchingResult | None,
) -> list[str]:
    action_items: list[str] = []
    if matching:
        for comparison in matching.comparisons:
            if comparison.status not in {MatchStatus.FAIL, MatchStatus.PARTIAL}:
                continue
            if comparison.suggested_action:
                action_items.append(comparison.suggested_action)
    return _dedupe(action_items + result.recommendations + result.next_steps)


def _count_populated_fields(model: object | None, field_names: list[str]) -> tuple[int, int]:
    if model is None:
        return 0, len(field_names)
    populated = sum(1 for name in field_names if getattr(model, name, None))
    return populated, len(field_names)


def _evaluation_to_assessment(evaluation: DocumentEvaluationResult) -> DocumentAssessmentEntry:
    """Map a professional document evaluation into the report entry shape."""
    label = DOCUMENT_TYPE_LABELS.get(evaluation.document_type, evaluation.file_name)
    completeness_level = (
        evaluation.completeness_level.value
        if hasattr(evaluation.completeness_level, "value")
        else str(evaluation.completeness_level)
    )
    return DocumentAssessmentEntry(
        name=label,
        document_type=evaluation.document_type,
        uploaded=evaluation.uploaded,
        completeness=evaluation.completeness,
        quality=f"{evaluation.quality_score}/100 ({evaluation.quality_rating})",
        missing_information=list(evaluation.missing_information),
        suggestions=list(evaluation.suggestions),
        document_name=evaluation.document_name or evaluation.file_name,
        quality_score=evaluation.quality_score,
        completeness_level=completeness_level,
        strengths=list(evaluation.strengths),
        weaknesses=list(evaluation.weaknesses),
        extracted_information=dict(evaluation.extracted_information),
        confidence=evaluation.confidence,
    )


def _missing_slot_assessment(slot_label: str, slot_type: str) -> DocumentAssessmentEntry:
    """Professional-style assessment entry for a required document slot that was not uploaded."""
    missing_message = f"{slot_label} has not been uploaded"
    return DocumentAssessmentEntry(
        name=slot_label,
        document_type=slot_type,
        uploaded=False,
        completeness="Missing",
        quality="N/A",
        missing_information=[missing_message],
        suggestions=[f"Upload your {slot_label} to complete your application package"],
        document_name=slot_label,
        quality_score=0,
        completeness_level="MISSING",
        strengths=[],
        weaknesses=[missing_message],
        confidence=0.0,
    )


def _unevaluated_upload_assessment(
    *,
    label: str,
    document_type: str | None,
    file_name: str,
    reason: str,
    suggestions: list[str],
) -> DocumentAssessmentEntry:
    """Professional-style fallback when a document was uploaded but not professionally evaluated."""
    return DocumentAssessmentEntry(
        name=label,
        document_type=document_type,
        uploaded=True,
        completeness="Uploaded",
        quality="Not Assessed",
        missing_information=[reason],
        suggestions=suggestions,
        document_name=file_name,
        quality_score=0,
        completeness_level="MISSING",
        strengths=[],
        weaknesses=[reason],
        confidence=0.0,
    )


def _assess_extracted_document(extracted: ExtractedDocument) -> DocumentAssessmentEntry:
    label = DOCUMENT_TYPE_LABELS.get(extracted.document_type, extracted.file_name)
    missing: list[str] = []
    suggestions: list[str] = []

    if extracted.extraction_status == "skipped":
        return DocumentAssessmentEntry(
            name=label,
            document_type=extracted.document_type,
            uploaded=True,
            completeness="Unknown",
            quality="Not Assessed",
            missing_information=["Content could not be extracted"],
            suggestions=["Re-upload a readable PDF or DOCX version of this document"],
        )

    if extracted.extraction_status == "error":
        return DocumentAssessmentEntry(
            name=label,
            document_type=extracted.document_type,
            uploaded=True,
            completeness="Incomplete",
            quality="Poor",
            missing_information=["Extraction failed"],
            suggestions=["Verify the document is not corrupted and try uploading again"],
        )

    completeness, quality, missing, suggestions = _assess_by_type(extracted)
    return DocumentAssessmentEntry(
        name=label,
        document_type=extracted.document_type,
        uploaded=True,
        completeness=completeness,
        quality=quality,
        missing_information=missing,
        suggestions=suggestions,
    )


def _assess_by_type(extracted: ExtractedDocument) -> tuple[str, str, list[str], list[str]]:
    missing: list[str] = []
    suggestions: list[str] = []

    if extracted.passport:
        populated, total = _count_populated_fields(
            extracted.passport,
            ["full_name", "nationality", "passport_number", "expiry_date"],
        )
        if not extracted.passport.full_name:
            missing.append("Full name")
        if not extracted.passport.nationality:
            missing.append("Nationality")
        if not extracted.passport.passport_number:
            missing.append("Passport number")
        if not extracted.passport.expiry_date:
            missing.append("Expiry date")
            suggestions.append("Ensure passport expiry date is clearly visible")
        return _score_assessment(populated, total, suggestions)

    if extracted.transcript:
        populated, total = _count_populated_fields(
            extracted.transcript,
            ["university", "degree", "major", "gpa", "graduation_year"],
        )
        for field, label in [
            ("university", "University name"),
            ("degree", "Degree level"),
            ("major", "Major/field of study"),
            ("gpa", "GPA"),
            ("graduation_year", "Graduation year"),
        ]:
            if not getattr(extracted.transcript, field):
                missing.append(label)
        if not extracted.transcript.gpa:
            suggestions.append("Request an official transcript showing GPA")
        return _score_assessment(populated, total, suggestions)

    if extracted.degree_certificate:
        populated, total = _count_populated_fields(
            extracted.degree_certificate,
            ["university", "degree", "major", "graduation_year"],
        )
        for field, label in [
            ("university", "University name"),
            ("degree", "Degree"),
            ("major", "Major"),
            ("graduation_year", "Graduation year"),
        ]:
            if not getattr(extracted.degree_certificate, field):
                missing.append(label)
        return _score_assessment(populated, total, suggestions)

    if extracted.language_test:
        populated, total = _count_populated_fields(
            extracted.language_test,
            ["test_type", "overall_score", "reading", "listening", "writing", "speaking"],
        )
        if not extracted.language_test.overall_score:
            missing.append("Overall score")
            suggestions.append("Upload a complete score report with all section scores")
        return _score_assessment(populated, total, suggestions)

    if extracted.cv:
        skills = len(extracted.cv.skills)
        experience = len(extracted.cv.experience)
        if skills == 0:
            missing.append("Skills section")
        if experience == 0:
            missing.append("Work experience")
            suggestions.append("Add relevant internships or work experience to strengthen your CV")
        populated = sum(1 for count in [skills, experience, len(extracted.cv.projects)] if count > 0)
        return _score_assessment(populated, 3, suggestions)

    if extracted.sop:
        populated, total = _count_populated_fields(
            extracted.sop,
            ["motivation", "career_goals", "leadership", "study_goals"],
        )
        for field, label in [
            ("motivation", "Motivation for applying"),
            ("career_goals", "Career goals"),
            ("study_goals", "Study goals"),
        ]:
            if not getattr(extracted.sop, field):
                missing.append(label)
        if not extracted.sop.motivation:
            suggestions.append("Expand on why you are applying to this specific program")
        return _score_assessment(populated, total, suggestions)

    if extracted.recommendation_letter:
        populated, total = _count_populated_fields(
            extracted.recommendation_letter,
            ["referee", "position", "organization"],
        )
        if not extracted.recommendation_letter.referee:
            missing.append("Referee name")
        if not extracted.recommendation_letter.strengths_mentioned:
            missing.append("Applicant strengths mentioned")
            suggestions.append("Ensure the letter highlights specific achievements")
        return _score_assessment(populated, total, suggestions)

    return "Partial", "Fair", ["Structured data not extracted"], ["Re-upload a clearer version of this document"]


def _score_assessment(
    populated: int,
    total: int,
    suggestions: list[str],
) -> tuple[str, str, list[str], list[str]]:
    ratio = populated / total if total else 0
    if ratio >= 0.9:
        completeness, quality = "Complete", "Good"
    elif ratio >= 0.6:
        completeness, quality = "Mostly Complete", "Fair"
    elif ratio >= 0.3:
        completeness, quality = "Partial", "Fair"
    else:
        completeness, quality = "Incomplete", "Poor"
    return completeness, quality, [], suggestions


def _build_document_assessment(
    documents: list[Document],
    profile: ApplicantProfile | None,
    document_evaluations: list[DocumentEvaluationResult] | None = None,
) -> list[DocumentAssessmentEntry]:
    if document_evaluations:
        return _build_document_assessment_from_evaluations(documents, document_evaluations)

    return _build_document_assessment_legacy(documents, profile)


def _build_document_assessment_from_evaluations(
    documents: list[Document],
    document_evaluations: list[DocumentEvaluationResult],
) -> list[DocumentAssessmentEntry]:
    """Build document assessment exclusively from professional per-document evaluations."""
    evaluations_by_doc_id = {
        evaluation.document_id: evaluation for evaluation in document_evaluations
    }
    evaluations_by_type: dict[str, DocumentEvaluationResult] = {}
    for evaluation in document_evaluations:
        evaluations_by_type.setdefault(evaluation.document_type, evaluation)

    assessments: list[DocumentAssessmentEntry] = []

    for slot_label, slot_types in DOCUMENT_SLOTS:
        uploaded_doc = next(
            (doc for doc in documents if doc.document_type in slot_types),
            None,
        )
        if uploaded_doc:
            evaluation = evaluations_by_doc_id.get(uploaded_doc.id) or evaluations_by_type.get(
                uploaded_doc.document_type or ""
            )
            if evaluation:
                assessments.append(_evaluation_to_assessment(evaluation))
            else:
                label = DOCUMENT_TYPE_LABELS.get(uploaded_doc.document_type or "", slot_label)
                assessments.append(
                    _unevaluated_upload_assessment(
                        label=label,
                        document_type=uploaded_doc.document_type,
                        file_name=uploaded_doc.file_name,
                        reason="Document uploaded but professional evaluation was not performed",
                        suggestions=["Re-run analysis to generate a professional document assessment"],
                    )
                )
        else:
            assessments.append(_missing_slot_assessment(slot_label, slot_types[0]))

    covered_types = {t for _, types in DOCUMENT_SLOTS for t in types}
    assessed_doc_ids = {evaluation.document_id for evaluation in document_evaluations}
    for doc in documents:
        if doc.id in assessed_doc_ids:
            continue
        if doc.document_type and doc.document_type in covered_types:
            continue

        evaluation = evaluations_by_doc_id.get(doc.id) or evaluations_by_type.get(doc.document_type or "")
        if evaluation:
            assessments.append(_evaluation_to_assessment(evaluation))
        else:
            label = DOCUMENT_TYPE_LABELS.get(doc.document_type or "", doc.file_name)
            assessments.append(
                _unevaluated_upload_assessment(
                    label=label,
                    document_type=doc.document_type,
                    file_name=doc.file_name,
                    reason="Document uploaded but professional evaluation was not performed",
                    suggestions=[],
                )
            )

    return assessments


def _build_document_assessment_legacy(
    documents: list[Document],
    profile: ApplicantProfile | None,
) -> list[DocumentAssessmentEntry]:
    """Fallback assessment from extracted profile data when professional evaluations are unavailable."""
    extracted_by_type: dict[str, ExtractedDocument] = {}
    if profile:
        for extracted in profile.documents:
            extracted_by_type[extracted.document_type] = extracted

    assessments: list[DocumentAssessmentEntry] = []

    for slot_label, slot_types in DOCUMENT_SLOTS:
        uploaded_doc = next(
            (doc for doc in documents if doc.document_type in slot_types),
            None,
        )
        if uploaded_doc:
            extracted = extracted_by_type.get(uploaded_doc.document_type or "")
            if extracted:
                assessments.append(_assess_extracted_document(extracted))
            else:
                label = DOCUMENT_TYPE_LABELS.get(uploaded_doc.document_type or "", slot_label)
                assessments.append(
                    _unevaluated_upload_assessment(
                        label=label,
                        document_type=uploaded_doc.document_type,
                        file_name=uploaded_doc.file_name,
                        reason="Document uploaded but structured extraction was not performed",
                        suggestions=["Document uploaded but structured extraction was not performed"],
                    )
                )
        else:
            assessments.append(_missing_slot_assessment(slot_label, slot_types[0]))

    covered_types = {t for _, types in DOCUMENT_SLOTS for t in types}
    for doc in documents:
        if doc.document_type and doc.document_type in covered_types:
            continue

        label = DOCUMENT_TYPE_LABELS.get(doc.document_type or "", doc.file_name)
        extracted = extracted_by_type.get(doc.document_type or "")
        if extracted:
            assessments.append(_assess_extracted_document(extracted))
        else:
            assessments.append(
                _unevaluated_upload_assessment(
                    label=label,
                    document_type=doc.document_type,
                    file_name=doc.file_name,
                    reason="Document uploaded but structured extraction was not performed",
                    suggestions=[],
                )
            )

    return assessments


def _build_missing_documents(result: ApplicationAnalysisResult) -> list[dict]:
    entries: list[dict] = []
    for name in result.missing_documents:
        if not name.strip():
            continue
        priority = "high" if any(kw in name.lower() for kw in ("cv", "transcript", "ielts", "toefl", "passport")) else "medium"
        entries.append({"name": name.strip(), "priority": priority})
    return entries


def _build_timeline(
    result: ApplicationAnalysisResult,
    missing_docs: list[dict],
    application: Application,
    matching: RequirementMatchingResult | None = None,
) -> list[TimelineEntry]:
    today = date.today()
    entries: list[TimelineEntry] = []
    offset = 0

    high_priority = [doc["name"] for doc in missing_docs if doc.get("priority") == "high"]
    if high_priority:
        entries.append(
            TimelineEntry(
                date=(today + timedelta(days=7)).isoformat(),
                event=f"Upload high-priority documents: {', '.join(high_priority[:3])}",
                priority="high",
            )
        )
        offset = 7

    if result.weaknesses:
        entries.append(
            TimelineEntry(
                date=(today + timedelta(days=14 + offset)).isoformat(),
                event="Address identified weaknesses in your application profile",
                priority="high",
            )
        )

    if matching:
        for comparison in matching.comparisons:
            if comparison.status != MatchStatus.FAIL or not comparison.suggested_action:
                continue
            entries.append(
                TimelineEntry(
                    date=(today + timedelta(days=10 + len(entries) * 3)).isoformat(),
                    event=f"{comparison.field}: {comparison.suggested_action}",
                    priority="high",
                )
            )

    if result.next_steps:
        for index, step in enumerate(result.next_steps[:3]):
            entries.append(
                TimelineEntry(
                    date=(today + timedelta(days=21 + index * 7)).isoformat(),
                    event=step,
                    priority="medium",
                )
            )

    entries.append(
        TimelineEntry(
            date=(today + timedelta(days=45)).isoformat(),
            event=f"Complete and review application for {application.title or 'scholarship'}",
            priority="medium",
        )
    )

    entries.append(
        TimelineEntry(
            date=(today + timedelta(days=60)).isoformat(),
            event="Final submission — verify all documents and requirements",
            priority="high",
        )
    )

    return entries


def _build_final_verdict(
    score: int,
    result: ApplicationAnalysisResult,
    matching: RequirementMatchingResult | None,
) -> FinalVerdict:
    if matching:
        fail_count = sum(1 for c in matching.comparisons if c.status == MatchStatus.FAIL)
        partial_count = sum(1 for c in matching.comparisons if c.status == MatchStatus.PARTIAL)
        # Calculate high-confidence failures (100% confidence)
        high_conf_fail_count = sum(1 for c in matching.comparisons 
                                     if c.status == MatchStatus.FAIL and c.confidence >= 95)
    else:
        fail_count = 0
        partial_count = 0
        high_conf_fail_count = 0

    # Adjust score based on high-confidence failures
    adjusted_score = score
    if high_conf_fail_count > 0:
        # Deduct points for each high-confidence failure
        penalty = high_conf_fail_count * 15  # 15 points per high-confidence failure
        adjusted_score = max(0, score - penalty)

    if adjusted_score >= 80 and fail_count == 0:
        recommendation = "Proceed with Submission"
        confidence = "High"
        summary = (
            "Your application demonstrates strong readiness. "
            "Core documents are in place and eligibility requirements are largely met."
        )
    elif adjusted_score >= 60:
        recommendation = "Proceed with Improvements"
        confidence = "Moderate"
        summary = (
            f"Your application shows moderate readiness (adjusted score: {adjusted_score}/100). "
            f"Address {len(result.missing_documents)} missing document(s), "
            f"{fail_count} failed requirement(s), and {partial_count} partial match(es) before submitting."
        )
    elif adjusted_score >= 40:
        recommendation = "Significant Improvements Needed"
        confidence = "Low"
        summary = (
            f"Your application requires substantial work (adjusted score: {adjusted_score}/100). "
            f"Focus on {high_conf_fail_count} critical requirement(s) with 100% confidence failure."
        )
    else:
        recommendation = "Not Ready for Submission"
        confidence = "Very Low"
        summary = (
            f"Your application is not ready (adjusted score: {adjusted_score}/100). "
            f"Critical failures in {high_conf_fail_count} requirement(s) must be addressed."
        )

    return FinalVerdict(
        summary=summary,
        recommendation=recommendation,
        confidence=confidence,
    )


def build_readiness_report(
    result: ApplicationAnalysisResult,
    *,
    readiness_score: int,
    application: Application,
    documents: list[Document],
    requirements: list[Requirement],
    applicant_profile: ApplicantProfile | None = None,
    requirement_matching: RequirementMatchingResult | None = None,
    document_evaluations: list[DocumentEvaluationResult] | None = None,
) -> ReadinessReport:
    """Assemble the full AI Readiness Report from pipeline outputs."""
    missing_docs = _build_missing_documents(result)
    document_assessment = _build_document_assessment(
        documents,
        applicant_profile,
        document_evaluations,
    )
    timeline = _build_timeline(result, missing_docs, application, requirement_matching)
    missing_requirements = _build_missing_requirements(requirement_matching, requirements)
    all_recommendations = _personalized_recommendations(result, requirement_matching)
    
    # Calculate adjusted score based on high-confidence failures
    adjusted_score = readiness_score
    if requirement_matching:
        high_conf_fail_count = sum(1 for c in requirement_matching.comparisons 
                                     if c.status == MatchStatus.FAIL and c.confidence >= 95)
        if high_conf_fail_count > 0:
            penalty = high_conf_fail_count * 15  # 15 points per high-confidence failure
            adjusted_score = max(0, readiness_score - penalty)

    return ReadinessReport(
        overall_readiness=OverallReadiness(
            readiness_score=adjusted_score,
            status=_derive_readiness_status(adjusted_score),
        ),
        executive_summary=_build_executive_summary(
            application=application,
            readiness_score=adjusted_score,
            matching=requirement_matching,
            result=result,
        ),
        applicant_profile_summary=_build_profile_summary(applicant_profile),
        eligibility_comparison=_build_eligibility_comparison(requirement_matching),
        missing_requirements=missing_requirements,
        document_assessment=document_assessment,
        missing_documents=missing_docs,
        strengths=result.strengths,
        weaknesses=result.weaknesses,
        recommendations=all_recommendations,
        timeline=timeline,
        final_verdict=_build_final_verdict(adjusted_score, result, requirement_matching),
    )


def document_assessment_to_evaluations(
    assessments: list[DocumentAssessmentEntry],
) -> list[dict]:
    """Map document assessments to legacy document_evaluations format for backward compatibility."""
    evaluations: list[dict] = []
    for entry in assessments:
        status = "present" if entry.uploaded else "missing"
        notes_parts = [f"Completeness: {entry.completeness}", f"Quality: {entry.quality}"]
        if entry.quality_score is not None:
            notes_parts.append(f"Quality Score: {entry.quality_score}/100")
        if entry.completeness_level:
            notes_parts.append(f"Completeness Level: {entry.completeness_level}")
        if entry.strengths:
            notes_parts.append(f"Strengths: {', '.join(entry.strengths[:3])}")
        if entry.weaknesses:
            notes_parts.append(f"Weaknesses: {', '.join(entry.weaknesses[:3])}")
        if entry.missing_information:
            notes_parts.append(f"Missing: {', '.join(entry.missing_information)}")
        if entry.suggestions:
            notes_parts.append(entry.suggestions[0])
        if entry.confidence is not None:
            notes_parts.append(f"Confidence: {entry.confidence:.0%}")

        legacy_entry: dict = {
            "name": entry.name,
            "status": status,
            "notes": " · ".join(notes_parts),
            "completeness": entry.completeness,
            "quality": entry.quality,
            "missing_information": entry.missing_information,
            "suggestions": entry.suggestions,
        }
        if entry.document_name is not None:
            legacy_entry["document_name"] = entry.document_name
        if entry.document_type is not None:
            legacy_entry["document_type"] = entry.document_type
        legacy_entry["uploaded"] = entry.uploaded
        if entry.quality_score is not None:
            legacy_entry["quality_score"] = entry.quality_score
        if entry.completeness_level is not None:
            legacy_entry["completeness_level"] = entry.completeness_level
        if entry.strengths:
            legacy_entry["strengths"] = entry.strengths
        if entry.weaknesses:
            legacy_entry["weaknesses"] = entry.weaknesses
        if entry.extracted_information:
            legacy_entry["extracted_information"] = entry.extracted_information
        if entry.confidence is not None:
            legacy_entry["confidence"] = entry.confidence
        evaluations.append(legacy_entry)
    return evaluations


def timeline_to_legacy(timeline: list[TimelineEntry]) -> list[dict]:
    """Map timeline entries to legacy timeline format."""
    return [{"date": entry.date, "event": entry.event} for entry in timeline]
