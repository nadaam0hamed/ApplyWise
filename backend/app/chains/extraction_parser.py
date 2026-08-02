"""Structured output models for document extraction."""

from __future__ import annotations

from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser


class PassportFields(BaseModel):
    full_name: str | None = Field(default=None, description="Full name as shown on the passport or in document")
    nationality: str | None = Field(default=None, description="Nationality or citizenship")
    passport_number: str | None = Field(default=None, description="Passport identification number")
    expiry_date: str | None = Field(default=None, description="Passport expiry date (ISO or as written)")
    date_of_birth: str | None = Field(default=None, description="Date of birth if shown on passport")
    place_of_birth: str | None = Field(default=None, description="Place of birth if shown on passport")


class TranscriptFields(BaseModel):
    university: str | None = Field(default=None, description="Name of the issuing university.")
    degree: str | None = Field(default=None, description="Degree level or title awarded.")
    major: str | None = Field(default=None, description="Field of study or major.")
    gpa: str | None = Field(default=None, description="GPA or equivalent grade average.")
    graduation_year: str | None = Field(default=None, description="Year of graduation or expected graduation.")


class DegreeCertificateFields(BaseModel):
    university: str | None = Field(default=None, description="Name of the issuing institution.")
    degree: str | None = Field(default=None, description="Degree or qualification awarded.")
    major: str | None = Field(default=None, description="Field of study or specialization.")
    graduation_year: str | None = Field(default=None, description="Year the degree was conferred.")


class LanguageTestFields(BaseModel):
    test_type: str | None = Field(default=None, description="IELTS, TOEFL, or other test name")
    overall_score: str | None = Field(default=None, description="Overall band or total score")
    reading: str | None = Field(default=None, description="Reading section score")
    listening: str | None = Field(default=None, description="Listening section score")
    writing: str | None = Field(default=None, description="Writing section score")
    speaking: str | None = Field(default=None, description="Speaking section score")
    test_date: str | None = Field(default=None, description="Test date if mentioned in the document")
    expiry_date: str | None = Field(default=None, description="Expiry date or validity period if mentioned")


class CVFields(BaseModel):
    full_name: str | None = Field(default=None, description="Full name of the applicant from CV header or personal info section")
    email: str | None = Field(default=None, description="Email address from contact section")
    phone: str | None = Field(default=None, description="Phone number from contact section")
    linkedin: str | None = Field(default=None, description="LinkedIn profile URL from contact section")
    github: str | None = Field(default=None, description="GitHub profile URL from contact section")
    skills: list[str] = Field(default_factory=list, description="Technical and soft skills from skills section")
    experience: list[str] = Field(default_factory=list, description="Work or internship experience entries with titles, companies, and dates")
    projects: list[str] = Field(default_factory=list, description="Notable projects with technologies and outcomes")
    leadership: list[str] = Field(default_factory=list, description="Leadership roles or activities from experience or activities section")
    volunteering: list[str] = Field(default_factory=list, description="Volunteering or community service activities")
    education: list[str] = Field(default_factory=list, description="Education entries with universities, degrees, and graduation years")
    nationality: str | None = Field(default=None, description="Nationality or citizenship if mentioned in CV")


class SOPFields(BaseModel):
    motivation: str | None = Field(default=None, description="Applicant motivation for applying.")
    career_goals: str | None = Field(default=None, description="Short- and long-term career goals.")
    leadership: str | None = Field(default=None, description="Leadership experiences or qualities described.")
    study_goals: str | None = Field(default=None, description="Academic or research goals for the program.")


class RecommendationLetterFields(BaseModel):
    referee: str | None = Field(default=None, description="Name of the referee or recommender.")
    position: str | None = Field(default=None, description="Referee job title or role.")
    organization: str | None = Field(default=None, description="Referee organization or institution.")
    strengths_mentioned: list[str] = Field(
        default_factory=list,
        description="Strengths or qualities highlighted about the applicant.",
    )


class ExtractedDocument(BaseModel):
    document_id: str
    file_name: str
    document_type: str
    extraction_status: str = Field(default="success", description="success, skipped, or error")
    error_message: str | None = None
    passport: PassportFields | None = None
    transcript: TranscriptFields | None = None
    degree_certificate: DegreeCertificateFields | None = None
    language_test: LanguageTestFields | None = None
    cv: CVFields | None = None
    sop: SOPFields | None = None
    recommendation_letter: RecommendationLetterFields | None = None


class ApplicantProfile(BaseModel):
    """Aggregated structured profile built from all uploaded documents."""

    passport: PassportFields | None = None
    transcript: TranscriptFields | None = None
    degree_certificate: DegreeCertificateFields | None = None
    language_test: LanguageTestFields | None = None
    cv: CVFields | None = None
    sop: SOPFields | None = None
    recommendation_letters: list[RecommendationLetterFields] = Field(default_factory=list)
    documents: list[ExtractedDocument] = Field(default_factory=list)

    def to_summary_lines(self) -> list[str]:
        """Render structured extractions as human-readable summaries for the analysis chain."""
        lines: list[str] = []

        for extracted in self.documents:
            if extracted.extraction_status == "skipped":
                lines.append(
                    f"{extracted.file_name} ({extracted.document_type}): "
                    f"skipped — {extracted.error_message or 'unsupported or empty content'}"
                )
                continue
            if extracted.extraction_status == "error":
                lines.append(
                    f"{extracted.file_name} ({extracted.document_type}): "
                    f"extraction failed — {extracted.error_message or 'unknown error'}"
                )
                continue

            if extracted.cv:
                cv = extracted.cv
                if cv.full_name:
                    lines.append(f"CV Name: {cv.full_name}")
                if cv.email:
                    lines.append(f"CV Email: {cv.email}")
                if cv.phone:
                    lines.append(f"CV Phone: {cv.phone}")
                if cv.linkedin:
                    lines.append(f"CV LinkedIn: {cv.linkedin}")
                if cv.github:
                    lines.append(f"CV GitHub: {cv.github}")
                if cv.nationality:
                    lines.append(f"CV Nationality: {cv.nationality}")
                if cv.skills:
                    lines.append(f"CV Skills: {', '.join(cv.skills[:5])}")  # First 5 skills
                if cv.experience:
                    lines.append(f"CV Experience: {len(cv.experience)} entries")
                if cv.projects:
                    lines.append(f"CV Projects: {len(cv.projects)} entries")
                if cv.leadership:
                    lines.append(f"CV Leadership: {len(cv.leadership)} entries")
                if cv.education:
                    lines.append(f"CV Education: {len(cv.education)} entries")

            if extracted.passport:
                passport = extracted.passport
                if passport.full_name:
                    lines.append(f"Passport Name: {passport.full_name}")
                if passport.nationality:
                    lines.append(f"Passport Nationality: {passport.nationality}")
                if passport.passport_number:
                    lines.append(f"Passport Number: {passport.passport_number}")
                if passport.expiry_date:
                    lines.append(f"Passport Expiry: {passport.expiry_date}")

            if extracted.language_test:
                lang = extracted.language_test
                if lang.test_type:
                    lines.append(f"Language Test: {lang.test_type}")
                if lang.overall_score:
                    lines.append(f"Overall Score: {lang.overall_score}")
                if lang.test_date:
                    lines.append(f"Test Date: {lang.test_date}")
                if lang.expiry_date:
                    lines.append(f"Expiry Date: {lang.expiry_date}")

            if extracted.transcript:
                transcript = extracted.transcript
                if transcript.university:
                    lines.append(f"University: {transcript.university}")
                if transcript.degree:
                    lines.append(f"Degree: {transcript.degree}")
                if transcript.major:
                    lines.append(f"Major: {transcript.major}")
                if transcript.gpa:
                    lines.append(f"GPA: {transcript.gpa}")
                if transcript.graduation_year:
                    lines.append(f"Graduation Year: {transcript.graduation_year}")

        return lines


def _format_extracted_document(extracted: ExtractedDocument) -> str:
    if extracted.passport:
        fields = extracted.passport
        return (
            f"Passport — name={fields.full_name or 'N/A'}, nationality={fields.nationality or 'N/A'}, "
            f"number={fields.passport_number or 'N/A'}, expiry={fields.expiry_date or 'N/A'}"
        )
    if extracted.transcript:
        fields = extracted.transcript
        return (
            f"Transcript — university={fields.university or 'N/A'}, degree={fields.degree or 'N/A'}, "
            f"major={fields.major or 'N/A'}, GPA={fields.gpa or 'N/A'}, "
            f"graduation={fields.graduation_year or 'N/A'}"
        )
    if extracted.degree_certificate:
        fields = extracted.degree_certificate
        return (
            f"Degree Certificate — university={fields.university or 'N/A'}, "
            f"degree={fields.degree or 'N/A'}, major={fields.major or 'N/A'}, "
            f"graduation={fields.graduation_year or 'N/A'}"
        )
    if extracted.language_test:
        fields = extracted.language_test
        return (
            f"{fields.test_type or 'Language test'} — overall={fields.overall_score or 'N/A'}, "
            f"reading={fields.reading or 'N/A'}, listening={fields.listening or 'N/A'}, "
            f"writing={fields.writing or 'N/A'}, speaking={fields.speaking or 'N/A'}"
        )
    if extracted.cv:
        fields = extracted.cv
        return (
            f"CV — name={fields.full_name or 'N/A'}, email={fields.email or 'N/A'}, "
            f"phone={fields.phone or 'N/A'}, linkedin={fields.linkedin or 'N/A'}, "
            f"github={fields.github or 'N/A'}, nationality={fields.nationality or 'N/A'}, "
            f"skills={_join_list(fields.skills)}, experience={_join_list(fields.experience)}, "
            f"projects={_join_list(fields.projects)}, leadership={_join_list(fields.leadership)}, "
            f"volunteering={_join_list(fields.volunteering)}, education={_join_list(fields.education)}"
        )
    if extracted.sop:
        fields = extracted.sop
        return (
            f"SOP — motivation={_truncate(fields.motivation)}, career_goals={_truncate(fields.career_goals)}, "
            f"leadership={_truncate(fields.leadership)}, study_goals={_truncate(fields.study_goals)}"
        )
    if extracted.recommendation_letter:
        fields = extracted.recommendation_letter
        return (
            f"Recommendation — referee={fields.referee or 'N/A'}, position={fields.position or 'N/A'}, "
            f"organization={fields.organization or 'N/A'}, strengths={_join_list(fields.strengths_mentioned)}"
        )
    return "No structured data extracted"


def _join_list(items: list[str] | None) -> str:
    if not items:
        return "N/A"
    return ", ".join(items[:5]) + ("..." if len(items) > 5 else "")


def _truncate(text: str | None, max_len: int = 50) -> str:
    if not text:
        return "N/A"
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def _join_list(items: list[str] | None, limit: int = 5) -> str:
    if not items:
        return "N/A"
    shown = items[:limit]
    suffix = f" (+{len(items) - limit} more)" if len(items) > limit else ""
    return "; ".join(shown) + suffix


def get_passport_output_parser() -> PydanticOutputParser:
    return PydanticOutputParser(pydantic_object=PassportFields)


def get_transcript_output_parser() -> PydanticOutputParser:
    return PydanticOutputParser(pydantic_object=TranscriptFields)


def get_degree_certificate_output_parser() -> PydanticOutputParser:
    return PydanticOutputParser(pydantic_object=DegreeCertificateFields)


def get_language_test_output_parser() -> PydanticOutputParser:
    return PydanticOutputParser(pydantic_object=LanguageTestFields)


def get_cv_output_parser() -> PydanticOutputParser:
    return PydanticOutputParser(pydantic_object=CVFields)


def get_sop_output_parser() -> PydanticOutputParser:
    return PydanticOutputParser(pydantic_object=SOPFields)


def get_recommendation_letter_output_parser() -> PydanticOutputParser:
    return PydanticOutputParser(pydantic_object=RecommendationLetterFields)
