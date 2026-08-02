"""LangChain chain for structured extraction from uploaded application documents."""

from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import Runnable
from pydantic import BaseModel

from app.chains.extraction_parser import (
    ApplicantProfile,
    CVFields,
    DegreeCertificateFields,
    ExtractedDocument,
    LanguageTestFields,
    PassportFields,
    RecommendationLetterFields,
    SOPFields,
    TranscriptFields,
    get_cv_output_parser,
    get_degree_certificate_output_parser,
    get_language_test_output_parser,
    get_passport_output_parser,
    get_recommendation_letter_output_parser,
    get_sop_output_parser,
    get_transcript_output_parser,
)
from app.chains.extraction_prompts import (
    get_extraction_prompt_template,
    get_field_instructions,
)
from app.models import Document
from app.models.constants import DOCUMENT_TYPE_LABELS
from app.services.document_content_service import DocumentContentError, load_document_text

SUPPORTED_EXTRACTION_TYPES = frozenset(
    {
        "passport",
        "academic_transcript",
        "diploma",
        "ielts_score",
        "toefl_score",
        "cv",
        "statement_of_purpose",
        "motivation_letter",
        "letter_of_recommendation",
    }
)


class DocumentExtractionChain:
    """
    Extract structured applicant information from uploaded documents using the shared LLM.

    Runs before ``ApplicationAnalysisChain`` and returns an ``ApplicantProfile`` without
    modifying the RAG pipeline or ``HybridRetriever``.
    """

    def __init__(self, *, llm: BaseChatModel) -> None:
        self.llm = llm
        self.prompt = get_extraction_prompt_template()
        self._runnables = _build_type_runnables(self.prompt, llm)

    def extract(self, documents: list[Document]) -> ApplicantProfile:
        extracted_documents: list[ExtractedDocument] = []

        for document in documents:
            extracted_documents.append(self._extract_single(document))

        return _merge_profile(extracted_documents)

    def _extract_single(self, document: Document) -> ExtractedDocument:
        document_type = document.document_type or "other"
        base = ExtractedDocument(
            document_id=document.id,
            file_name=document.file_name,
            document_type=document_type,
        )

        if document_type not in SUPPORTED_EXTRACTION_TYPES:
            return base.model_copy(
                update={
                    "extraction_status": "skipped",
                    "error_message": "Document type is not supported for structured extraction.",
                }
            )

        try:
            document_text = load_document_text(document)
        except DocumentContentError as exc:
            return base.model_copy(
                update={
                    "extraction_status": "skipped",
                    "error_message": str(exc),
                }
            )

        try:
            parsed = self._invoke_for_type(document_type, document, document_text)
        except Exception as exc:
            # Log the error but try to continue with empty profile
            print(f"Extraction error for {document.file_name}: {exc}")
            return base.model_copy(
                update={
                    "extraction_status": "error",
                    "error_message": str(exc),
                }
            )

        return _attach_parsed_fields(base, document_type, parsed)

    def _invoke_for_type(
        self,
        document_type: str,
        document: Document,
        document_text: str,
    ) -> BaseModel:
        runnable = self._runnables[document_type]
        parser = _parser_for_type(document_type)
        label = DOCUMENT_TYPE_LABELS.get(document_type, document_type)

        prompt_inputs = {
            "document_type_label": label,
            "file_name": document.file_name,
            "document_text": document_text,
            "field_instructions": get_field_instructions(document_type),
            "format_instructions": parser.get_format_instructions(),
        }

        result = runnable.invoke(prompt_inputs)
        if isinstance(result, BaseModel):
            return result
        return parser.pydantic_object.model_validate(result)


def _build_type_runnables(
    prompt: Runnable,
    llm: BaseChatModel,
) -> dict[str, Runnable]:
    runnables: dict[str, Runnable] = {}
    for document_type in SUPPORTED_EXTRACTION_TYPES:
        parser = _parser_for_type(document_type)
        runnables[document_type] = prompt | llm | parser
    return runnables


def _parser_for_type(document_type: str) -> PydanticOutputParser:
    parser_map: dict[str, PydanticOutputParser] = {
        "passport": get_passport_output_parser(),
        "academic_transcript": get_transcript_output_parser(),
        "diploma": get_degree_certificate_output_parser(),
        "ielts_score": get_language_test_output_parser(),
        "toefl_score": get_language_test_output_parser(),
        "cv": get_cv_output_parser(),
        "statement_of_purpose": get_sop_output_parser(),
        "motivation_letter": get_sop_output_parser(),
        "letter_of_recommendation": get_recommendation_letter_output_parser(),
    }
    return parser_map[document_type]


def _attach_parsed_fields(
    base: ExtractedDocument,
    document_type: str,
    parsed: BaseModel,
) -> ExtractedDocument:
    updates: dict[str, Any] = {"extraction_status": "success"}

    if document_type == "passport" and isinstance(parsed, PassportFields):
        updates["passport"] = parsed
    elif document_type == "academic_transcript" and isinstance(parsed, TranscriptFields):
        updates["transcript"] = parsed
    elif document_type == "diploma" and isinstance(parsed, DegreeCertificateFields):
        updates["degree_certificate"] = parsed
    elif document_type in {"ielts_score", "toefl_score"} and isinstance(parsed, LanguageTestFields):
        if not parsed.test_type:
            parsed = parsed.model_copy(
                update={"test_type": "IELTS" if document_type == "ielts_score" else "TOEFL"}
            )
        updates["language_test"] = parsed
    elif document_type == "cv" and isinstance(parsed, CVFields):
        updates["cv"] = parsed
    elif document_type in {"statement_of_purpose", "motivation_letter"} and isinstance(parsed, SOPFields):
        updates["sop"] = parsed
    elif document_type == "letter_of_recommendation" and isinstance(parsed, RecommendationLetterFields):
        updates["recommendation_letter"] = parsed

    return base.model_copy(update=updates)


def _merge_profile(extracted_documents: list[ExtractedDocument]) -> ApplicantProfile:
    profile = ApplicantProfile(documents=extracted_documents)

    for extracted in extracted_documents:
        if extracted.extraction_status != "success":
            continue
        
        # Merge passport data
        if extracted.passport:
            if profile.passport is None:
                profile.passport = extracted.passport
            else:
                # Fill in missing fields from additional passport documents
                if not profile.passport.full_name and extracted.passport.full_name:
                    profile.passport.full_name = extracted.passport.full_name
                if not profile.passport.nationality and extracted.passport.nationality:
                    profile.passport.nationality = extracted.passport.nationality
                if not profile.passport.passport_number and extracted.passport.passport_number:
                    profile.passport.passport_number = extracted.passport.passport_number
                if not profile.passport.expiry_date and extracted.passport.expiry_date:
                    profile.passport.expiry_date = extracted.passport.expiry_date
        
        # Merge transcript data
        if extracted.transcript:
            if profile.transcript is None:
                profile.transcript = extracted.transcript
            else:
                # Fill in missing fields
                if not profile.transcript.university and extracted.transcript.university:
                    profile.transcript.university = extracted.transcript.university
                if not profile.transcript.degree and extracted.transcript.degree:
                    profile.transcript.degree = extracted.transcript.degree
                if not profile.transcript.major and extracted.transcript.major:
                    profile.transcript.major = extracted.transcript.major
                if not profile.transcript.gpa and extracted.transcript.gpa:
                    profile.transcript.gpa = extracted.transcript.gpa
                if not profile.transcript.graduation_year and extracted.transcript.graduation_year:
                    profile.transcript.graduation_year = extracted.transcript.graduation_year
        
        # Merge degree certificate data
        if extracted.degree_certificate:
            if profile.degree_certificate is None:
                profile.degree_certificate = extracted.degree_certificate
            else:
                # Fill in missing fields
                if not profile.degree_certificate.university and extracted.degree_certificate.university:
                    profile.degree_certificate.university = extracted.degree_certificate.university
                if not profile.degree_certificate.degree and extracted.degree_certificate.degree:
                    profile.degree_certificate.degree = extracted.degree_certificate.degree
                if not profile.degree_certificate.major and extracted.degree_certificate.major:
                    profile.degree_certificate.major = extracted.degree_certificate.major
                if not profile.degree_certificate.graduation_year and extracted.degree_certificate.graduation_year:
                    profile.degree_certificate.graduation_year = extracted.degree_certificate.graduation_year
        
        # Merge language test data
        if extracted.language_test:
            if profile.language_test is None:
                profile.language_test = extracted.language_test
            else:
                # Fill in missing fields
                if not profile.language_test.test_type and extracted.language_test.test_type:
                    profile.language_test.test_type = extracted.language_test.test_type
                if not profile.language_test.overall_score and extracted.language_test.overall_score:
                    profile.language_test.overall_score = extracted.language_test.overall_score
                if not profile.language_test.reading and extracted.language_test.reading:
                    profile.language_test.reading = extracted.language_test.reading
                if not profile.language_test.listening and extracted.language_test.listening:
                    profile.language_test.listening = extracted.language_test.listening
                if not profile.language_test.writing and extracted.language_test.writing:
                    profile.language_test.writing = extracted.language_test.writing
                if not profile.language_test.speaking and extracted.language_test.speaking:
                    profile.language_test.speaking = extracted.language_test.speaking
        
        # Merge CV data (most important for personal info)
        if extracted.cv:
            if profile.cv is None:
                profile.cv = extracted.cv
            else:
                # Fill in missing fields from CV
                if not profile.cv.full_name and extracted.cv.full_name:
                    profile.cv.full_name = extracted.cv.full_name
                if not profile.cv.email and extracted.cv.email:
                    profile.cv.email = extracted.cv.email
                if not profile.cv.phone and extracted.cv.phone:
                    profile.cv.phone = extracted.cv.phone
                if not profile.cv.linkedin and extracted.cv.linkedin:
                    profile.cv.linkedin = extracted.cv.linkedin
                if not profile.cv.github and extracted.cv.github:
                    profile.cv.github = extracted.cv.github
                if not profile.cv.nationality and extracted.cv.nationality:
                    profile.cv.nationality = extracted.cv.nationality
                # Merge lists
                profile.cv.skills.extend(extracted.cv.skills)
                profile.cv.experience.extend(extracted.cv.experience)
                profile.cv.projects.extend(extracted.cv.projects)
                profile.cv.leadership.extend(extracted.cv.leadership)
                profile.cv.volunteering.extend(extracted.cv.volunteering)
                profile.cv.education.extend(extracted.cv.education)
        
        # Merge SOP data
        if extracted.sop:
            if profile.sop is None:
                profile.sop = extracted.sop
            else:
                # Fill in missing fields
                if not profile.sop.motivation and extracted.sop.motivation:
                    profile.sop.motivation = extracted.sop.motivation
                if not profile.sop.career_goals and extracted.sop.career_goals:
                    profile.sop.career_goals = extracted.sop.career_goals
                if not profile.sop.leadership and extracted.sop.leadership:
                    profile.sop.leadership = extracted.sop.leadership
                if not profile.sop.study_goals and extracted.sop.study_goals:
                    profile.sop.study_goals = extracted.sop.study_goals
        
        # Collect recommendation letters
        if extracted.recommendation_letter:
            profile.recommendation_letters.append(extracted.recommendation_letter)

    return profile
