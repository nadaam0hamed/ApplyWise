"""Unit tests for the AI Readiness Report builder."""

from datetime import datetime

from app.chains.extraction_parser import (
    ApplicantProfile,
    CVFields,
    ExtractedDocument,
    LanguageTestFields,
    PassportFields,
    TranscriptFields,
)
from app.chains.output_parser import ApplicationAnalysisResult
from app.models import Application, Document
from app.schemas.requirement_matching import FieldComparison, MatchStatus, RequirementMatchingResult
from app.services.readiness_report_builder import (
    build_readiness_report,
    document_assessment_to_evaluations,
    timeline_to_legacy,
)


def _application() -> Application:
    return Application(
        id="app-1",
        user_id="user-1",
        application_type="scholarship",
        status="in_progress",
        title="Fulbright Scholarship",
        country="USA",
        source_url=None,
        readiness_score=None,
        created_at=datetime(2026, 1, 1),
    )


def _document(doc_type: str, file_name: str) -> Document:
    return Document(
        id=f"doc-{doc_type}",
        application_id="app-1",
        file_name=file_name,
        document_type=doc_type,
        storage_path=f"/docs/{file_name}",
        uploaded_at=datetime(2026, 1, 15),
        file_size=1024,
        mime_type="application/pdf",
    )


def _analysis_result() -> ApplicationAnalysisResult:
    return ApplicationAnalysisResult(
        readiness_score=72,
        strengths=["Strong academic record", "IELTS score on file"],
        weaknesses=["Missing recommendation letter"],
        missing_documents=["Recommendation Letter", "Statement of Purpose"],
        recommendations=["Upload missing documents", "Strengthen your SOP"],
        next_steps=["Request recommendation letter from professor"],
    )


def test_build_readiness_report_includes_all_sections():
    profile = ApplicantProfile(
        passport=PassportFields(full_name="Jane Doe", nationality="Egyptian"),
        transcript=TranscriptFields(university="Cairo University", gpa="3.8", degree="BSc"),
        language_test=LanguageTestFields(test_type="IELTS", overall_score="7.5"),
        cv=CVFields(skills=["Python", "Research"], experience=["Intern at Tech Co"], leadership=["Club President"]),
        documents=[
            ExtractedDocument(
                document_id="doc-cv",
                file_name="cv.pdf",
                document_type="cv",
                cv=CVFields(skills=["Python"], experience=["Intern"], leadership=["President"]),
            ),
            ExtractedDocument(
                document_id="doc-transcript",
                file_name="transcript.pdf",
                document_type="academic_transcript",
                transcript=TranscriptFields(university="Cairo University", gpa="3.8", degree="BSc", major="CS"),
            ),
        ],
    )

    matching = RequirementMatchingResult(
        comparisons=[
            FieldComparison(
                field="Minimum GPA",
                requirement="3.5",
                applicant="3.8",
                status=MatchStatus.PASS,
                reason="GPA meets minimum requirement",
                confidence=0.95,
            ),
            FieldComparison(
                field="IELTS",
                requirement="7.0",
                applicant="7.5",
                status=MatchStatus.PASS,
                reason="IELTS score exceeds minimum",
            ),
        ]
    )

    documents = [
        _document("cv", "cv.pdf"),
        _document("academic_transcript", "transcript.pdf"),
        _document("ielts_score", "ielts.pdf"),
    ]

    report = build_readiness_report(
        _analysis_result(),
        readiness_score=72,
        application=_application(),
        documents=documents,
        requirements=[],
        applicant_profile=profile,
        requirement_matching=matching,
    )

    assert report.overall_readiness.readiness_score == 72
    assert report.overall_readiness.status == "Moderate Readiness"
    assert report.executive_summary
    assert report.applicant_profile_summary.personal_information.full_name == "Jane Doe"
    assert report.applicant_profile_summary.academic_information.gpa == "3.8"
    assert report.applicant_profile_summary.language_scores.overall_score == "7.5"
    assert "Python" in report.applicant_profile_summary.skills
    assert len(report.eligibility_comparison) == 2
    assert report.eligibility_comparison[0].requirement_name == "Minimum GPA"
    assert report.eligibility_comparison[0].explanation
    assert report.eligibility_comparison[0].confidence > 0
    assert len(report.document_assessment) >= 3
    assert len(report.missing_documents) == 2
    assert len(report.strengths) == 2
    assert len(report.weaknesses) == 1
    assert len(report.recommendations) >= 2
    assert len(report.timeline) >= 2
    assert report.final_verdict.recommendation
    assert report.final_verdict.summary


def test_readiness_status_thresholds():
    for score, expected in [(85, "Ready"), (65, "Moderate Readiness"), (45, "Needs Improvement"), (30, "Not Ready")]:
        report = build_readiness_report(
            ApplicationAnalysisResult(readiness_score=score),
            readiness_score=score,
            application=_application(),
            documents=[],
            requirements=[],
        )
        assert report.overall_readiness.status == expected


def test_document_assessment_marks_missing_slots():
    report = build_readiness_report(
        _analysis_result(),
        readiness_score=50,
        application=_application(),
        documents=[_document("cv", "cv.pdf")],
        requirements=[],
    )

    missing = [entry for entry in report.document_assessment if not entry.uploaded]
    assert len(missing) >= 1
    assert any(entry.completeness == "Missing" for entry in missing)


def test_document_assessment_to_evaluations_backward_compat():
    report = build_readiness_report(
        _analysis_result(),
        readiness_score=72,
        application=_application(),
        documents=[_document("cv", "cv.pdf")],
        requirements=[],
    )

    evaluations = document_assessment_to_evaluations(report.document_assessment)
    assert len(evaluations) > 0
    assert "name" in evaluations[0]
    assert "status" in evaluations[0]
    assert "notes" in evaluations[0]
    assert "completeness" in evaluations[0]


def test_build_readiness_report_uses_professional_evaluation_fields():
    from app.schemas.document_evaluation import DocumentEvaluationResult

    evaluations = [
        DocumentEvaluationResult(
            document_id="doc-cv",
            file_name="cv.pdf",
            document_type="cv",
            quality_score=88,
            completeness="Complete",
            quality_rating="Good",
            strengths=["Strong projects section"],
            weaknesses=["Summary could be stronger"],
            missing_information=["Summary could be stronger"],
            suggestions=["Tailor summary to the program"],
            confidence=0.91,
        )
    ]

    report = build_readiness_report(
        _analysis_result(),
        readiness_score=72,
        application=_application(),
        documents=[_document("cv", "cv.pdf")],
        requirements=[],
        document_evaluations=evaluations,
    )

    cv_assessment = next(item for item in report.document_assessment if item.document_type == "cv")
    assert cv_assessment.document_name == "cv.pdf"
    assert cv_assessment.quality_score == 88
    assert cv_assessment.completeness == "Complete"
    assert cv_assessment.completeness_level == "COMPLETE"
    assert cv_assessment.strengths == ["Strong projects section"]
    assert cv_assessment.weaknesses == ["Summary could be stronger"]
    assert cv_assessment.missing_information == ["Summary could be stronger"]
    assert cv_assessment.suggestions == ["Tailor summary to the program"]
    assert cv_assessment.confidence == 0.91
    assert cv_assessment.uploaded is True
    assert cv_assessment.quality == "88/100 (Good)"

    missing = next(item for item in report.document_assessment if not item.uploaded)
    assert missing.quality_score == 0
    assert missing.completeness_level == "MISSING"
    assert missing.confidence == 0.0
    assert missing.weaknesses


def test_timeline_to_legacy_format():
    report = build_readiness_report(
        _analysis_result(),
        readiness_score=72,
        application=_application(),
        documents=[],
        requirements=[],
    )

    legacy = timeline_to_legacy(report.timeline)
    assert all("date" in entry and "event" in entry for entry in legacy)


def test_final_verdict_recommends_proceed_when_ready():
    matching = RequirementMatchingResult(
        comparisons=[
            FieldComparison(
                field="Minimum GPA",
                requirement="3.0",
                applicant="3.8",
                status=MatchStatus.PASS,
                reason="Pass",
                confidence=0.9,
            )
        ]
    )

    report = build_readiness_report(
        ApplicationAnalysisResult(readiness_score=85, strengths=["All good"]),
        readiness_score=85,
        application=_application(),
        documents=[_document("cv", "cv.pdf")],
        requirements=[],
        requirement_matching=matching,
    )

    assert report.final_verdict.recommendation == "Proceed with Submission"
    assert report.final_verdict.confidence == "High"
