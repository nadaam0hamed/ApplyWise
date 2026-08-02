"""Unit tests for requirement extraction and matching (no LLM / vector store)."""

from datetime import date, datetime, timedelta

from langchain_core.documents import Document

from app.chains.extraction_parser import (
    ApplicantProfile,
    CVFields,
    DegreeCertificateFields,
    LanguageTestFields,
    PassportFields,
    RecommendationLetterFields,
    TranscriptFields,
)
from app.models import Document as AppDocument
from app.schemas.requirement_matching import MatchStatus, RetrievedRequirement
from app.services.requirement_extractor import extract_requirements_from_documents
from app.services.requirement_matching_engine import (
    _compare_degree,
    _compare_document_presence,
    _compare_duolingo,
    _compare_english_requirement,
    _compare_gpa,
    _compare_language_test,
    _compare_major,
    _compare_nationality_or_country,
    _compare_passport,
    _compare_publications,
    _compare_recommendation_letters,
    _compare_required_documents,
    _compare_work_experience,
    _enrich_comparison,
    _parse_requirement_number,
    _requirement_by_field,
)


def _doc(text: str, source: str = "static") -> Document:
    return Document(page_content=text, metadata={"retrieved_from": source})


def _app_doc(doc_type: str, file_name: str | None = None) -> AppDocument:
    return AppDocument(
        id=f"doc-{doc_type}",
        application_id="app-1",
        file_name=file_name or f"{doc_type}.pdf",
        document_type=doc_type,
        storage_path="path",
        uploaded_at=datetime.now(),
        file_size=100,
        mime_type="application/pdf",
    )


def _requirement(
    field: str,
    value: str,
    *,
    structured: dict | None = None,
    source: str = "static",
) -> RetrievedRequirement:
    return RetrievedRequirement(
        field=field,
        value=value,
        source=source,
        structured=structured,
    )


def _extract(text: str, source: str = "static") -> dict[str, RetrievedRequirement]:
    return _requirement_by_field(extract_requirements_from_documents([_doc(text, source)]))


# --- GPA ---


def test_extract_gpa_from_static_kb():
    docs = [
        _doc("Applicants must have a minimum GPA of 3.5 on a 4.0 scale.", "static"),
    ]
    requirements = extract_requirements_from_documents(docs)
    gpa_req = _requirement_by_field(requirements).get("gpa")
    assert gpa_req is not None
    assert "3.5" in gpa_req.value
    assert gpa_req.source == "static"
    assert gpa_req.structured is not None
    assert gpa_req.structured.type == "gpa"
    assert gpa_req.structured.operator == ">="
    assert gpa_req.structured.value == 3.5


def test_extract_gpa_candidates_should_wording():
    req = _extract("Candidates should maintain a GPA of 3.2 or higher.")["gpa"]
    assert req.structured.value == 3.2
    assert req.structured.operator == ">="


def test_extract_gpa_required_gpa_wording():
    req = _extract("Required GPA: 3.0")["gpa"]
    assert req.structured.value == 3.0


def test_application_kb_overrides_static():
    docs = [
        _doc("Minimum GPA of 3.0 required.", "static"),
        _doc("Minimum GPA of 3.5 required for this scholarship.", "application"),
    ]
    requirements = extract_requirements_from_documents(docs)
    gpa_req = _requirement_by_field(requirements)["gpa"]
    assert "3.5" in gpa_req.value
    assert gpa_req.source == "application"
    assert gpa_req.structured.value == 3.5


# --- Language tests ---


def test_extract_ielts_overall():
    req = _extract("IELTS overall 6.5 is required for admission.")["ielts"]
    assert req.structured.type == "ielts"
    assert req.structured.value == 6.5
    assert "6.5" in req.value


def test_extract_ielts_language_requirement_section():
    req = _extract(
        "Language requirement: applicants must achieve an IELTS score of 7.0."
    )["ielts"]
    assert req.structured.value == 7.0


def test_extract_toefl():
    req = _extract("Minimum TOEFL iBT score of 90 required.")["toefl"]
    assert req.structured.type == "toefl"
    assert req.structured.value == 90


def test_extract_duolingo():
    req = _extract("Duolingo English Test score of 120 or above.")["duolingo"]
    assert req.structured.type == "duolingo"
    assert req.structured.value == 120


def test_extract_english_proficiency_boolean():
    req = _extract("Applicants must demonstrate English language proficiency.")[
        "english_requirement"
    ]
    assert req.structured.type == "english_requirement"
    assert req.structured.value is True


# --- Degree & major ---


def test_extract_bachelor_degree():
    req = _extract("Applicants must hold a Bachelor degree.")["degree"]
    assert req.structured.type == "degree"
    assert req.structured.value == "Bachelor"
    assert "Bachelor" in req.value


def test_extract_master_degree():
    req = _extract("A Master's degree is required.")["degree"]
    assert req.structured.value == "Master"


def test_extract_phd_degree():
    req = _extract("Candidates should possess a PhD or doctoral degree.")["degree"]
    assert req.structured.value == "Doctoral"


def test_extract_major_field_of_study():
    req = _extract("Major in Computer Science is required.")["major"]
    assert req.structured.type == "major"
    assert "Computer Science" in req.structured.value


# --- Nationality & country ---


def test_extract_nationality_applicants_from():
    req = _extract("Applicants from Egypt are eligible to apply.")["nationality"]
    assert req.structured.type == "nationality"
    assert req.structured.value == "Egypt"


def test_extract_nationality_citizens_of():
    req = _extract("Eligible applicants include citizens of Kenya and Uganda.")[
        "nationality"
    ]
    assert "Kenya" in req.structured.value


def test_extract_country_eligibility():
    req = _extract("Eligible countries: Nigeria, Ghana, and South Africa.")[
        "country_eligibility"
    ]
    assert req.structured.type == "country"
    assert "Nigeria" in req.structured.value


# --- Documents ---


def test_extract_passport():
    req = _extract("Applicants must submit a valid passport.")["passport"]
    assert req.structured.type == "passport"
    assert req.structured.value is True


def test_extract_transcript():
    req = _extract("An official academic transcript is required.")["transcript"]
    assert req.structured.type == "academic_transcript"
    assert req.structured.value is True


def test_extract_cv():
    req = _extract("Submit a current CV or resume with your application.")["cv"]
    assert req.structured.type == "cv"


def test_extract_statement_of_purpose():
    req = _extract("A statement of purpose is required.")["statement_of_purpose"]
    assert req.structured.type == "statement_of_purpose"


def test_extract_motivation_letter():
    req = _extract("Applicants must upload a motivation letter.")["motivation_letter"]
    assert req.structured.type == "motivation_letter"


def test_extract_graduation_certificate():
    req = _extract("Copy of your degree certificate is required.")["graduation_certificate"]
    assert req.structured.type == "graduation_certificate"


def test_extract_recommendation_letters_numeric():
    req = _extract("At least two recommendation letters are required.")[
        "recommendation_letters"
    ]
    assert req.structured.type == "recommendation_letters"
    assert req.structured.value == 2
    assert req.structured.operator == ">="


def test_extract_recommendation_letters_digit():
    req = _extract("3 letters of recommendation must be submitted.")[
        "recommendation_letters"
    ]
    assert req.structured.value == 3


def test_extract_required_documents_section():
    req = _extract(
        "Required documents include: passport, academic transcript, CV, "
        "and two recommendation letters."
    )["required_documents"]
    assert req.structured.type == "required_documents"
    assert "passport" in req.structured.value
    assert "academic_transcript" in req.structured.value
    assert "cv" in req.structured.value
    assert "recommendation_letters" in req.structured.value


# --- Experience & research ---


def test_extract_work_experience():
    req = _extract("Minimum of 3 years work experience required.")["work_experience"]
    assert req.structured.type == "work_experience"
    assert req.structured.value == 3
    assert req.structured.operator == ">="


def test_extract_publications_count():
    req = _extract("At least 2 publications are expected.")["publications"]
    assert req.structured.value == 2


def test_extract_publications_boolean():
    req = _extract("Publications are required for doctoral applicants.")["publications"]
    assert req.structured.value is True


def test_extract_research_proposal():
    req = _extract("Submit a research proposal aligned with the program.")["research_proposal"]
    assert req.structured.type == "research_proposal"


# --- Financial, visa, deadline ---


def test_extract_financial_documents():
    req = _extract("Proof of financial support is required.")["financial_documents"]
    assert req.structured.type == "financial_documents"


def test_extract_visa():
    req = _extract("A valid student visa is required.")["visa"]
    assert req.structured.type == "visa"


def test_extract_application_deadline():
    req = _extract("Application deadline: March 15, 2026")["application_deadline"]
    assert req.structured.type == "application_deadline"
    assert "March 15, 2026" in req.structured.value


def test_extract_apply_by_deadline():
    req = _extract("Apply by 1 September 2026.")["application_deadline"]
    assert "September 2026" in req.structured.value


# --- Structured value used by matching ---


def test_parse_requirement_number_uses_structured_value():
    requirement = RetrievedRequirement(
        field="gpa",
        value="Minimum GPA: 3.5",
        source="static",
        structured={"type": "gpa", "operator": ">=", "value": 3.5},
    )
    assert _parse_requirement_number(requirement) == 3.5


def test_parse_requirement_number_falls_back_to_value_string():
    requirement = RetrievedRequirement(
        field="ielts",
        value="Minimum IELTS: 7.0",
        source="static",
    )
    assert _parse_requirement_number(requirement) == 7.0


# --- Matching (unchanged behavior) ---


def test_compare_gpa_pass():
    profile = ApplicantProfile(transcript=TranscriptFields(gpa="3.8"))
    requirement = RetrievedRequirement(
        field="gpa",
        value="Minimum GPA: 3.5",
        source="static",
        structured={"type": "gpa", "operator": ">=", "value": 3.5},
    )
    result = _compare_gpa(profile, requirement)
    assert result.status == MatchStatus.PASS
    assert result.applicant == "3.8"


def test_compare_gpa_not_verified_when_no_requirement():
    profile = ApplicantProfile(transcript=TranscriptFields(gpa="3.8"))
    result = _compare_gpa(profile, None)
    assert result.status == MatchStatus.UNKNOWN


def test_compare_ielts_fail():
    profile = ApplicantProfile(
        language_test=LanguageTestFields(test_type="IELTS", overall_score="6.0")
    )
    requirement = RetrievedRequirement(
        field="ielts",
        value="Minimum IELTS: 7.0",
        source="application",
        structured={"type": "ielts", "operator": ">=", "value": 7.0},
    )
    result = _compare_language_test(
        profile,
        [],
        field_label="IELTS",
        requirement=requirement,
        test_name="IELTS",
    )
    assert result.status == MatchStatus.FAIL
    assert result.confidence == 1.0


def test_compare_passport_pass():
    future = (date.today() + timedelta(days=730)).strftime("%Y-%m-%d")
    profile = ApplicantProfile(
        passport=PassportFields(full_name="Jane Doe", expiry_date=future),
    )
    documents = [
        AppDocument(
            id="1",
            application_id="app-1",
            file_name="passport.pdf",
            document_type="passport",
            storage_path="path",
            uploaded_at=datetime.now(),
            file_size=100,
            mime_type="application/pdf",
        )
    ]
    requirement = RetrievedRequirement(
        field="passport",
        value="Passport required",
        source="static",
        structured={"type": "passport", "value": True},
    )
    result = _compare_passport(profile, documents, requirement)
    assert result.status == MatchStatus.PASS
    assert "Uploaded" in (result.applicant or "")


def test_no_hallucination_when_kb_empty():
    requirements = extract_requirements_from_documents([])
    assert requirements == []


def test_extract_multiple_requirements_from_single_chunk():
    text = (
        "Eligible applicants from Egypt must hold a Bachelor degree with "
        "minimum GPA 3.5. IELTS overall 6.5 required. Required documents "
        "include passport and academic transcript."
    )
    found = _extract(text)
    assert "gpa" in found
    assert "ielts" in found
    assert "degree" in found
    assert "nationality" in found
    assert "passport" in found or "required_documents" in found


def test_backward_compatible_value_strings():
    """Legacy consumers reading only ``value`` still get human-readable strings."""
    req = _extract("Applicants must have a minimum GPA of 3.5 on a 4.0 scale.")["gpa"]
    assert isinstance(req.value, str)
    assert "3.5" in req.value
    assert req.field == "gpa"


# --- Rule-based comparison tests ---


def test_compare_gpa_fail_and_confidence():
    profile = ApplicantProfile(transcript=TranscriptFields(gpa="3.2"))
    requirement = _requirement(
        "gpa",
        "Minimum GPA: 3.5",
        structured={"type": "gpa", "operator": ">=", "value": 3.5},
    )
    result = _compare_gpa(profile, requirement)
    assert result.status == MatchStatus.FAIL
    assert result.confidence == 1.0
    enriched = _enrich_comparison(result)
    assert enriched.suggested_action == "Not eligible unless the program allows exceptions."


def test_compare_gpa_partial_within_tolerance():
    profile = ApplicantProfile(transcript=TranscriptFields(gpa="3.4"))
    requirement = _requirement(
        "gpa",
        "Minimum GPA: 3.5",
        structured={"type": "gpa", "operator": ">=", "value": 3.5},
    )
    result = _compare_gpa(profile, requirement)
    assert result.status == MatchStatus.PARTIAL
    assert result.confidence == 0.8


def test_compare_gpa_pass_confidence():
    profile = ApplicantProfile(transcript=TranscriptFields(gpa="3.82"))
    requirement = _requirement(
        "gpa",
        "Minimum GPA: 3.5",
        structured={"type": "gpa", "operator": ">=", "value": 3.5},
    )
    result = _compare_gpa(profile, requirement)
    assert result.status == MatchStatus.PASS
    assert result.confidence == 1.0


def test_compare_ielts_pass():
    profile = ApplicantProfile(
        language_test=LanguageTestFields(test_type="IELTS", overall_score="8.0")
    )
    requirement = _requirement(
        "ielts",
        "Minimum IELTS: 6.5",
        structured={"type": "ielts", "operator": ">=", "value": 6.5},
    )
    result = _compare_language_test(
        profile, [], field_label="IELTS", requirement=requirement, test_name="IELTS"
    )
    assert result.status == MatchStatus.PASS
    assert result.confidence == 1.0


def test_compare_ielts_partial_within_tolerance():
    profile = ApplicantProfile(
        language_test=LanguageTestFields(test_type="IELTS", overall_score="6.2")
    )
    requirement = _requirement(
        "ielts",
        "Minimum IELTS: 6.5",
        structured={"type": "ielts", "operator": ">=", "value": 6.5},
    )
    result = _compare_language_test(
        profile, [], field_label="IELTS", requirement=requirement, test_name="IELTS"
    )
    assert result.status == MatchStatus.PARTIAL
    assert result.confidence == 0.8


def test_compare_ielts_suggested_action_on_fail():
    profile = ApplicantProfile(
        language_test=LanguageTestFields(test_type="IELTS", overall_score="5.5")
    )
    requirement = _requirement(
        "ielts",
        "Minimum IELTS: 6.5",
        structured={"type": "ielts", "operator": ">=", "value": 6.5},
    )
    result = _enrich_comparison(
        _compare_language_test(
            profile, [], field_label="IELTS", requirement=requirement, test_name="IELTS"
        )
    )
    assert result.status == MatchStatus.FAIL
    assert "Retake IELTS" in (result.suggested_action or "")


def test_compare_toefl_pass():
    profile = ApplicantProfile(
        language_test=LanguageTestFields(test_type="TOEFL", overall_score="100")
    )
    requirement = _requirement(
        "toefl",
        "Minimum TOEFL: 90",
        structured={"type": "toefl", "operator": ">=", "value": 90},
    )
    result = _compare_language_test(
        profile, [], field_label="TOEFL", requirement=requirement, test_name="TOEFL"
    )
    assert result.status == MatchStatus.PASS


def test_compare_duolingo_pass():
    profile = ApplicantProfile(
        language_test=LanguageTestFields(test_type="Duolingo", overall_score="130")
    )
    requirement = _requirement(
        "duolingo",
        "Minimum Duolingo: 120",
        structured={"type": "duolingo", "operator": ">=", "value": 120},
    )
    result = _compare_duolingo(profile, [], requirement)
    assert result.status == MatchStatus.PASS


def test_compare_duolingo_fail_when_missing():
    requirement = _requirement(
        "duolingo",
        "Minimum Duolingo: 120",
        structured={"type": "duolingo", "operator": ">=", "value": 120},
    )
    result = _compare_duolingo(ApplicantProfile(), [], requirement)
    assert result.status == MatchStatus.FAIL
    assert result.applicant == "Not uploaded"


def test_compare_english_requirement_pass():
    profile = ApplicantProfile(
        language_test=LanguageTestFields(test_type="IELTS", overall_score="7.0")
    )
    requirement = _requirement(
        "english_requirement",
        "English proficiency required",
        structured={"type": "english_requirement", "value": True},
    )
    result = _compare_english_requirement(profile, [], requirement, {})
    assert result.status == MatchStatus.PASS


def test_compare_english_requirement_deferred_when_specific_tests_exist():
    profile = ApplicantProfile(
        language_test=LanguageTestFields(test_type="IELTS", overall_score="7.0")
    )
    requirement = _requirement(
        "english_requirement",
        "English proficiency required",
        structured={"type": "english_requirement", "value": True},
    )
    result = _compare_english_requirement(
        profile,
        [],
        requirement,
        {"ielts": _requirement("ielts", "6.5", structured={"type": "ielts", "value": 6.5})},
    )
    assert result.status == MatchStatus.UNKNOWN
    assert "IELTS" in result.reason


def test_compare_degree_pass():
    profile = ApplicantProfile(transcript=TranscriptFields(degree="Bachelor of Science"))
    requirement = _requirement(
        "degree",
        "Bachelor degree required",
        structured={"type": "degree", "value": "Bachelor"},
    )
    result = _compare_degree(profile, requirement)
    assert result.status == MatchStatus.PASS


def test_compare_degree_fail():
    profile = ApplicantProfile(transcript=TranscriptFields(degree="Associate"))
    requirement = _requirement(
        "degree",
        "Master degree required",
        structured={"type": "degree", "value": "Master"},
    )
    result = _compare_degree(profile, requirement)
    assert result.status == MatchStatus.FAIL


def test_compare_major_pass():
    profile = ApplicantProfile(transcript=TranscriptFields(major="Computer Science"))
    requirement = _requirement(
        "major",
        "Major in Computer Science",
        structured={"type": "major", "value": "Computer Science"},
    )
    result = _compare_major(profile, requirement)
    assert result.status == MatchStatus.PASS


def test_compare_nationality_pass():
    profile = ApplicantProfile(passport=PassportFields(nationality="Egypt"))
    requirement = _requirement(
        "nationality",
        "Applicants from Egypt",
        structured={"type": "nationality", "value": "Egypt"},
    )
    result = _compare_nationality_or_country(
        field_label="Nationality",
        requirement=requirement,
        applicant_value="Egypt",
    )
    assert result.status == MatchStatus.PASS


def test_compare_country_eligibility_fail():
    profile = ApplicantProfile(passport=PassportFields(nationality="Brazil"))
    requirement = _requirement(
        "country_eligibility",
        "Eligible countries: Nigeria, Ghana",
        structured={"type": "country", "value": ["Nigeria", "Ghana"]},
    )
    result = _compare_nationality_or_country(
        field_label="Country Eligibility",
        requirement=requirement,
        applicant_value=profile.passport.nationality,
    )
    assert result.status == MatchStatus.FAIL


def test_compare_passport_fail_when_missing():
    requirement = _requirement(
        "passport",
        "Passport required",
        structured={"type": "passport", "value": True},
    )
    result = _compare_passport(ApplicantProfile(), [], requirement)
    assert result.status == MatchStatus.FAIL
    assert result.applicant == "Missing"
    enriched = _enrich_comparison(result)
    assert "passport" in (enriched.suggested_action or "").lower()


def test_compare_transcript_fail_when_missing():
    requirement = _requirement(
        "transcript",
        "Official transcript required",
        structured={"type": "academic_transcript", "value": True},
    )
    result = _compare_document_presence(
        field_label="Academic Transcript",
        document_type="academic_transcript",
        documents=[],
        requirement=requirement,
    )
    assert result.status == MatchStatus.FAIL
    enriched = _enrich_comparison(result)
    assert enriched.suggested_action == "Upload official transcript."


def test_compare_transcript_pass_when_uploaded():
    requirement = _requirement(
        "transcript",
        "Official transcript required",
        structured={"type": "academic_transcript", "value": True},
    )
    result = _compare_document_presence(
        field_label="Academic Transcript",
        document_type="academic_transcript",
        documents=[_app_doc("academic_transcript")],
        requirement=requirement,
        profile_detail="Uploaded (GPA 3.8)",
    )
    assert result.status == MatchStatus.PASS
    assert result.confidence == 1.0


def test_compare_graduation_certificate_pass():
    requirement = _requirement(
        "graduation_certificate",
        "Degree certificate required",
        structured={"type": "graduation_certificate", "value": True},
    )
    result = _compare_document_presence(
        field_label="Graduation Certificate",
        document_type="diploma",
        documents=[_app_doc("diploma")],
        requirement=requirement,
    )
    assert result.status == MatchStatus.PASS


def test_compare_cv_fail_when_missing():
    requirement = _requirement(
        "cv",
        "CV required",
        structured={"type": "cv", "value": True},
    )
    result = _compare_document_presence(
        field_label="CV / Resume",
        document_type="cv",
        documents=[],
        requirement=requirement,
    )
    assert result.status == MatchStatus.FAIL


def test_compare_statement_of_purpose_pass():
    requirement = _requirement(
        "statement_of_purpose",
        "Statement of purpose required",
        structured={"type": "statement_of_purpose", "value": True},
    )
    result = _compare_document_presence(
        field_label="Statement of Purpose",
        document_type="statement_of_purpose",
        documents=[_app_doc("statement_of_purpose")],
        requirement=requirement,
    )
    assert result.status == MatchStatus.PASS


def test_compare_motivation_letter_fail():
    requirement = _requirement(
        "motivation_letter",
        "Motivation letter required",
        structured={"type": "motivation_letter", "value": True},
    )
    result = _compare_document_presence(
        field_label="Motivation Letter",
        document_type="motivation_letter",
        documents=[],
        requirement=requirement,
    )
    assert result.status == MatchStatus.FAIL


def test_compare_recommendation_letters_partial():
    profile = ApplicantProfile(
        recommendation_letters=[RecommendationLetterFields(referee="Prof. Smith")]
    )
    requirement = _requirement(
        "recommendation_letters",
        "Two recommendation letters required",
        structured={"type": "recommendation_letters", "operator": ">=", "value": 2},
    )
    result = _compare_recommendation_letters(profile, [], requirement)
    assert result.status == MatchStatus.PARTIAL
    assert result.confidence == 0.8
    enriched = _enrich_comparison(result)
    assert enriched.suggested_action == "Request one additional recommendation letter."


def test_compare_recommendation_letters_pass():
    profile = ApplicantProfile(
        recommendation_letters=[
            RecommendationLetterFields(referee="Prof. Smith"),
            RecommendationLetterFields(referee="Dr. Jones"),
        ]
    )
    requirement = _requirement(
        "recommendation_letters",
        "Two recommendation letters required",
        structured={"type": "recommendation_letters", "operator": ">=", "value": 2},
    )
    result = _compare_recommendation_letters(profile, [], requirement)
    assert result.status == MatchStatus.PASS


def test_compare_work_experience_pass():
    profile = ApplicantProfile(
        cv=CVFields(experience=["Software Engineer — 3 years", "Intern — 1 year"])
    )
    requirement = _requirement(
        "work_experience",
        "Minimum 2 years work experience",
        structured={"type": "work_experience", "operator": ">=", "value": 2},
    )
    result = _compare_work_experience(profile, [_app_doc("cv")], requirement)
    assert result.status == MatchStatus.PASS


def test_compare_work_experience_fail_no_cv():
    requirement = _requirement(
        "work_experience",
        "Minimum 2 years work experience",
        structured={"type": "work_experience", "operator": ">=", "value": 2},
    )
    result = _compare_work_experience(ApplicantProfile(), [], requirement)
    assert result.status == MatchStatus.FAIL
    assert result.applicant == "Not uploaded"


def test_compare_publications_pass():
    profile = ApplicantProfile(
        cv=CVFields(projects=["Published paper in IEEE journal on ML"])
    )
    requirement = _requirement(
        "publications",
        "Publications required",
        structured={"type": "publications", "value": True},
    )
    result = _compare_publications(profile, requirement)
    assert result.status == MatchStatus.PASS


def test_compare_research_proposal_pass():
    requirement = _requirement(
        "research_proposal",
        "Research proposal required",
        structured={"type": "research_proposal", "value": True},
    )
    result = _compare_document_presence(
        field_label="Research Proposal",
        document_type="other",
        documents=[_app_doc("other", "research_proposal.pdf")],
        requirement=requirement,
        filename_keywords=("research", "proposal"),
    )
    assert result.status == MatchStatus.PASS


def test_compare_financial_documents_fail():
    requirement = _requirement(
        "financial_documents",
        "Financial proof required",
        structured={"type": "financial_documents", "value": True},
    )
    result = _compare_document_presence(
        field_label="Financial Documents",
        document_type="other",
        documents=[],
        requirement=requirement,
        filename_keywords=("bank", "financial", "funds", "sponsor"),
    )
    assert result.status == MatchStatus.FAIL


def test_compare_visa_pass():
    requirement = _requirement(
        "visa",
        "Student visa required",
        structured={"type": "visa", "value": True},
    )
    result = _compare_document_presence(
        field_label="Visa",
        document_type="other",
        documents=[_app_doc("other", "student_visa.pdf")],
        requirement=requirement,
        filename_keywords=("visa",),
    )
    assert result.status == MatchStatus.PASS


def test_compare_required_documents_partial():
    requirement = _requirement(
        "required_documents",
        "Required documents",
        structured={
            "type": "required_documents",
            "value": ["passport", "academic_transcript", "cv"],
        },
    )
    documents = [_app_doc("passport"), _app_doc("academic_transcript")]
    result = _compare_required_documents(documents, requirement)
    assert result.status == MatchStatus.PARTIAL
    assert "2/3" in (result.applicant or "")


def test_compare_required_documents_pass():
    requirement = _requirement(
        "required_documents",
        "Required documents",
        structured={
            "type": "required_documents",
            "value": ["passport", "academic_transcript"],
        },
    )
    documents = [_app_doc("passport"), _app_doc("academic_transcript")]
    result = _compare_required_documents(documents, requirement)
    assert result.status == MatchStatus.PASS


def test_compare_application_deadline_pass():
    future = (date.today() + timedelta(days=30)).strftime("%B %d, %Y")
    requirement = _requirement(
        "application_deadline",
        f"Application deadline: {future}",
        structured={"type": "application_deadline", "value": future},
    )
    from app.services.requirement_matching_engine import _compare_application_deadline

    result = _compare_application_deadline(requirement)
    assert result.status == MatchStatus.PASS


def test_enrich_comparison_no_action_on_unknown():
    from app.schemas.requirement_matching import FieldComparison

    comparison = FieldComparison(
        field="Minimum GPA",
        requirement=None,
        applicant="3.8",
        status=MatchStatus.UNKNOWN,
        reason="No requirement",
        confidence=0.2,
        suggested_action="Should be cleared",
    )
    enriched = _enrich_comparison(comparison)
    assert enriched.suggested_action is None


def test_unknown_confidence_when_no_requirement():
    result = _compare_gpa(ApplicantProfile(transcript=TranscriptFields(gpa="3.8")), None)
    assert result.status == MatchStatus.UNKNOWN
    assert result.confidence == 0.2


def test_comparison_row_has_required_fields():
    profile = ApplicantProfile(transcript=TranscriptFields(gpa="3.8"))
    requirement = _requirement(
        "gpa",
        "Minimum GPA: 3.5",
        structured={"type": "gpa", "operator": ">=", "value": 3.5},
    )
    result = _enrich_comparison(_compare_gpa(profile, requirement))
    assert result.field == "Minimum GPA"
    assert result.requirement == "3.5"
    assert result.applicant == "3.8"
    assert result.status == MatchStatus.PASS
    assert result.reason
    assert result.confidence == 1.0
    assert result.suggested_action is None
