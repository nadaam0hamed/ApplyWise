"""Unit tests for professional document quality evaluation."""

from datetime import datetime
from unittest.mock import MagicMock, patch

from app.chains.extraction_parser import CVFields, ExtractedDocument
from app.models import Document
from app.schemas.document_evaluation import (
    DocumentCompletenessLevel,
    DocumentEvaluation,
    DocumentEvaluationLLMOutput,
    DocumentEvaluationResult,
    SubjectiveWritingLLMOutput,
    score_to_completeness_level,
)
from app.services.document_evaluation import DocumentEvaluationService
from app.services.document_evaluation.evaluators.cv import CVEvaluator
from app.services.readiness_report_builder import build_readiness_report, _evaluation_to_assessment
from app.chains.output_parser import ApplicationAnalysisResult
from app.models import Application


def _document(doc_type: str, file_name: str, doc_id: str = "doc-1") -> Document:
    return Document(
        id=doc_id,
        application_id="app-1",
        file_name=file_name,
        document_type=doc_type,
        storage_path=f"/docs/{file_name}",
        uploaded_at=datetime(2026, 1, 15),
        file_size=1024,
        mime_type="application/pdf",
    )


def test_cv_evaluator_rule_based_scores_strengths_and_weaknesses():
    evaluator = CVEvaluator()
    extracted = ExtractedDocument(
        document_id="doc-cv",
        file_name="cv.pdf",
        document_type="cv",
        cv=CVFields(
            skills=["Python", "Machine Learning"],
            experience=["Software Intern at Tech Co"],
            projects=["ApplyWise"],
            leadership=["Club President"],
        ),
    )

    result = evaluator.evaluate_rule_based(
        document=_document("cv", "cv.pdf"),
        extracted=extracted,
        applicant_profile=None,
        requirements=[],
        document_text=(
            "Experience\nEducation\nSkills\n"
            "Improved deployment speed by 30%\n"
            "github.com/applicant"
        ),
    )

    assert result.quality_score >= 70
    assert any("skills" in item.lower() for item in result.strengths)
    assert result.weaknesses == [] or isinstance(result.weaknesses, list)


def test_document_evaluation_service_routes_by_type():
    service = DocumentEvaluationService(llm=None)
    documents = [
        _document("cv", "cv.pdf", "doc-cv"),
        _document("passport", "passport.pdf", "doc-passport"),
    ]

    with patch("app.services.document_evaluation.evaluator.load_document_text", return_value="sample text"):
        results = service.evaluate_all(documents, applicant_profile=None, requirements=[])

    assert len(results) == 2
    assert {result.document_type for result in results} == {"cv", "passport"}
    assert all(0 <= result.quality_score <= 100 for result in results)


def test_document_evaluation_service_resolves_other_type_from_filename():
    service = DocumentEvaluationService(llm=None)
    document = _document("other", "research_proposal.pdf")

    with patch("app.services.document_evaluation.evaluator.load_document_text", return_value="research methodology objectives"):
        result = service.evaluate_document(document, applicant_profile=None, requirements=[])

    assert result.document_type == "research_proposal"
    assert result.quality_score > 0


def test_evaluation_maps_into_readiness_report_assessment():
    evaluation = DocumentEvaluationResult(
        document_id="doc-cv",
        file_name="cv.pdf",
        document_type="cv",
        quality_score=91,
        completeness="Complete",
        quality_rating="Excellent",
        strengths=["ATS friendly", "Good technical skills"],
        weaknesses=["No quantified achievements"],
        suggestions=["Add GitHub", "Add measurable impact"],
    )

    entry = _evaluation_to_assessment(evaluation)
    assert entry.quality == "91/100 (Excellent)"
    assert entry.quality_score == 91
    assert entry.completeness_level == DocumentCompletenessLevel.COMPLETE.value
    assert entry.document_name == "cv.pdf"
    assert entry.strengths == ["ATS friendly", "Good technical skills"]
    assert entry.weaknesses == ["No quantified achievements"]
    assert "No quantified achievements" in entry.missing_information
    assert entry.suggestions == ["Add GitHub", "Add measurable impact"]
    assert "Strength:" not in " ".join(entry.suggestions)


def test_build_readiness_report_uses_professional_evaluations():
    application = Application(
        id="app-1",
        user_id="user-1",
        application_type="scholarship",
        status="in_progress",
        title="Test Scholarship",
        country="UK",
        source_url=None,
        readiness_score=None,
        created_at=datetime(2026, 1, 1),
    )
    documents = [_document("cv", "cv.pdf")]
    evaluations = [
        DocumentEvaluationResult(
            document_id="doc-1",
            file_name="cv.pdf",
            document_type="cv",
            quality_score=88,
            completeness="Complete",
            quality_rating="Good",
            strengths=["Strong projects section"],
            weaknesses=["Summary could be stronger"],
            suggestions=["Tailor summary to the program"],
        )
    ]
    result = ApplicationAnalysisResult(
        readiness_score=80,
        strengths=["Good CV"],
        weaknesses=[],
        missing_documents=["Passport"],
        recommendations=["Upload passport"],
        next_steps=["Upload passport"],
    )

    report = build_readiness_report(
        result,
        readiness_score=80,
        application=application,
        documents=documents,
        requirements=[],
        document_evaluations=evaluations,
    )

    cv_assessment = next(item for item in report.document_assessment if item.document_type == "cv")
    assert cv_assessment.quality == "88/100 (Good)"
    assert cv_assessment.quality_score == 88
    assert cv_assessment.document_name == "cv.pdf"
    assert cv_assessment.strengths == ["Strong projects section"]
    assert cv_assessment.weaknesses == ["Summary could be stronger"]
    assert cv_assessment.suggestions == ["Tailor summary to the program"]
    assert cv_assessment.completeness_level == DocumentCompletenessLevel.COMPLETE.value


def test_cv_evaluator_uses_llm_for_subjective_writing_only():
    evaluator = CVEvaluator()
    mock_llm = MagicMock()
    subjective_output = SubjectiveWritingLLMOutput(
        writing_quality_score=95,
        strengths=["Excellent formatting"],
        weaknesses=[],
        suggestions=["Minor grammar polish"],
        confidence=0.9,
    )

    with patch.object(CVEvaluator, "_evaluate_subjective_with_llm", return_value=subjective_output):
        result = evaluator.evaluate(
            document=_document("cv", "cv.pdf"),
            applicant_profile=None,
            requirements=[],
            document_text=(
                "john@example.com\nExperience\nEducation\nSkills\n"
                "Improved deployment speed by 30%\n"
                "github.com/applicant\nlinkedin.com/in/applicant"
            ),
            llm=mock_llm,
            document_type_label="CV / Resume",
        )

    # Objective rule-based score merged with subjective LLM (70/30)
    assert 0 < result.quality_score < 100
    assert any("skills" in s.lower() or "formatting" in s.lower() for s in result.strengths)
    assert result.completeness_level in {
        DocumentCompletenessLevel.COMPLETE,
        DocumentCompletenessLevel.PARTIAL,
    }
    assert 0.0 <= result.confidence <= 1.0


def test_document_evaluation_schema_conversion():
    evaluation = DocumentEvaluationResult(
        document_id="doc-cv",
        file_name="cv.pdf",
        document_type="cv",
        quality_score=82,
        completeness="Mostly Complete",
        quality_rating="Good",
        strengths=["Clear structure"],
        weaknesses=["Missing portfolio link"],
        suggestions=["Add portfolio URL"],
        confidence=0.88,
        extracted_information={"cv": {"skills": ["Python"]}},
    )

    canonical = evaluation.to_document_evaluation()
    assert isinstance(canonical, DocumentEvaluation)
    assert canonical.document_name == "cv.pdf"
    assert canonical.completeness == DocumentCompletenessLevel.COMPLETE
    assert canonical.extracted_information == {"cv": {"skills": ["Python"]}}
    assert canonical.confidence == 0.88


def test_score_to_completeness_level_mapping():
    assert score_to_completeness_level(90) == DocumentCompletenessLevel.COMPLETE
    assert score_to_completeness_level(55) == DocumentCompletenessLevel.PARTIAL
    assert score_to_completeness_level(10) == DocumentCompletenessLevel.MISSING
    assert (
        score_to_completeness_level(80, evaluation_status="skipped")
        == DocumentCompletenessLevel.MISSING
    )


def test_passport_evaluator_checks_expiry_and_fields():
    from app.services.document_evaluation.evaluators.passport import PassportEvaluator
    from app.chains.extraction_parser import PassportFields

    evaluator = PassportEvaluator()
    extracted = ExtractedDocument(
        document_id="doc-passport",
        file_name="passport.pdf",
        document_type="passport",
        passport=PassportFields(
            full_name="Jane Doe",
            nationality="US",
            passport_number="AB1234567",
            expiry_date="2030-12-31",
        ),
    )

    result = evaluator.evaluate_rule_based(
        document=_document("passport", "passport.pdf"),
        extracted=extracted,
        applicant_profile=None,
        requirements=[],
        document_text="PASSPORT Jane Doe AB1234567 Expiry 2030-12-31",
    )

    assert result.quality_score >= 80
    assert any("name" in s.lower() for s in result.strengths)
    assert not any("expired" in w.lower() for w in result.weaknesses)


def test_motivation_letter_evaluator_checks_structure():
    from app.services.document_evaluation.evaluators.motivation import MotivationLetterEvaluator
    from app.chains.extraction_parser import SOPFields

    evaluator = MotivationLetterEvaluator()
    extracted = ExtractedDocument(
        document_id="doc-motivation",
        file_name="motivation.pdf",
        document_type="motivation_letter",
        sop=SOPFields(
            motivation="I am motivated to join this program.",
            career_goals="I aim to become a researcher.",
        ),
    )
    letter_text = (
        "Dear Admissions Committee,\n\n"
        "When I worked on my undergraduate thesis, I discovered my passion for research. "
        "During my internship, I developed skills that align with this scholarship program. "
        "My experience leading a student club shaped my career goals in academia. "
        "This program fits my long-term aspirations perfectly.\n\n"
        "Yours sincerely,\nApplicant"
    ) + " word" * 260

    result = evaluator.evaluate_rule_based(
        document=_document("motivation_letter", "motivation.pdf"),
        extracted=extracted,
        applicant_profile=None,
        requirements=[],
        document_text=letter_text,
    )

    assert result.quality_score >= 60
    assert any("motivation" in s.lower() for s in result.strengths)
    assert any("closing" in s.lower() or "opening" in s.lower() for s in result.strengths)


def test_ielts_evaluator_checks_component_scores():
    from app.services.document_evaluation.evaluators.language_certificate import LanguageCertificateEvaluator
    from app.chains.extraction_parser import LanguageTestFields

    evaluator = LanguageCertificateEvaluator()
    extracted = ExtractedDocument(
        document_id="doc-ielts",
        file_name="ielts.pdf",
        document_type="ielts_score",
        language_test=LanguageTestFields(
            test_type="IELTS",
            overall_score="7.5",
            reading="8.0",
            listening="7.5",
            writing="7.0",
            speaking="7.5",
        ),
    )

    result = evaluator.evaluate_rule_based(
        document=_document("ielts_score", "ielts.pdf"),
        extracted=extracted,
        applicant_profile=None,
        requirements=[],
        document_text="IELTS Test Report Form Test Date 2025-06-15 Overall 7.5",
    )

    assert result.quality_score >= 70
    assert any("overall" in s.lower() for s in result.strengths)
    assert any("section" in s.lower() for s in result.strengths)
