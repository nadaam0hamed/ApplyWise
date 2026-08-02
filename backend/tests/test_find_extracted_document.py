"""Unit tests for find_extracted_document()."""

from datetime import datetime

from app.chains.extraction_parser import ApplicantProfile, CVFields, ExtractedDocument, PassportFields
from app.models import Document
from app.services.document_evaluation.evaluators.base import find_extracted_document


def _document(doc_id: str, doc_type: str, file_name: str) -> Document:
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


def _extracted(
    doc_id: str,
    doc_type: str,
    file_name: str,
    *,
    extraction_status: str = "success",
) -> ExtractedDocument:
    return ExtractedDocument(
        document_id=doc_id,
        file_name=file_name,
        document_type=doc_type,
        extraction_status=extraction_status,
        cv=CVFields(skills=["Python"]) if doc_type == "cv" else None,
        passport=PassportFields(full_name="Jane Doe") if doc_type == "passport" else None,
    )


def test_find_extracted_document_single_document():
    profile = ApplicantProfile(
        documents=[_extracted("doc-cv", "cv", "cv.pdf")],
    )

    result = find_extracted_document(profile, _document("doc-cv", "cv", "cv.pdf"))

    assert result is not None
    assert result.document_id == "doc-cv"
    assert result.document_type == "cv"


def test_find_extracted_document_duplicate_document_types():
    """When multiple extracted docs share a type and no document_id matches, return the first."""
    profile = ApplicantProfile(
        documents=[
            _extracted("doc-cv-1", "cv", "cv.pdf"),
            _extracted("doc-cv-2", "cv", "cv_scanned.pdf"),
        ],
    )

    result = find_extracted_document(
        profile,
        _document("doc-cv-unknown", "cv", "new_cv.pdf"),
    )

    assert result is not None
    assert result.document_id == "doc-cv-1"
    assert result.file_name == "cv.pdf"


def test_find_extracted_document_document_id_precedence_over_duplicate_types():
    profile = ApplicantProfile(
        documents=[
            _extracted("doc-cv-1", "cv", "cv.pdf"),
            _extracted("doc-cv-2", "cv", "cv_scanned.pdf", extraction_status="skipped"),
        ],
    )

    result = find_extracted_document(profile, _document("doc-cv-2", "cv", "cv_scanned.pdf"))

    assert result is not None
    assert result.document_id == "doc-cv-2"
    assert result.extraction_status == "skipped"


def test_find_extracted_document_fallback_by_document_type():
    profile = ApplicantProfile(
        documents=[_extracted("doc-passport", "passport", "passport.pdf")],
    )

    result = find_extracted_document(
        profile,
        _document("doc-new-passport", "passport", "passport_reupload.pdf"),
    )

    assert result is not None
    assert result.document_id == "doc-passport"
    assert result.document_type == "passport"


def test_find_extracted_document_returns_none_when_no_match():
    profile = ApplicantProfile(
        documents=[_extracted("doc-cv", "cv", "cv.pdf")],
    )

    result = find_extracted_document(profile, _document("doc-sop", "statement_of_purpose", "sop.pdf"))

    assert result is None


def test_find_extracted_document_returns_none_when_profile_missing():
    result = find_extracted_document(None, _document("doc-cv", "cv", "cv.pdf"))

    assert result is None
