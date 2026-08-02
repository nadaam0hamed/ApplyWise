"""Download and text extraction for uploaded application documents."""

from __future__ import annotations

import tempfile
from pathlib import Path

from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader

from app.db.supabase import get_supabase_client
from app.models import Document

DOCUMENTS_BUCKET = "documents"
MAX_DOCUMENT_TEXT_CHARS = 12000

IMAGE_MIME_TYPES = frozenset({"image/png", "image/jpeg", "image/jpg"})


class DocumentContentError(RuntimeError):
    """Raised when document content cannot be loaded."""


def download_document_bytes(document: Document) -> bytes:
    response = get_supabase_client().storage.from_(DOCUMENTS_BUCKET).download(document.storage_path)
    if not response:
        raise DocumentContentError(f"Empty download for {document.file_name}")
    return response


def extract_text_from_bytes(content: bytes, *, file_name: str, mime_type: str) -> str:
    if mime_type in IMAGE_MIME_TYPES:
        raise DocumentContentError(
            f"Image files are not supported for text extraction (no OCR): {file_name}"
        )

    suffix = _suffix_for_mime(mime_type, file_name)

    # Try to extract text without temporary files first
    try:
        if suffix == ".pdf" or mime_type == "application/pdf":
            return _extract_pdf_text_from_bytes(content)
        if suffix == ".docx" or mime_type == (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ):
            return _extract_docx_text_from_bytes(content)
        if suffix in {".txt", ".md"} or mime_type.startswith("text/"):
            return content.decode("utf-8", errors="replace")
    except Exception as e:
        print(f"Direct extraction failed, trying temp file: {e}")

    # Fallback to temp file method
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
        temp_file.write(content)
        temp_path = Path(temp_file.name)

    try:
        if suffix == ".pdf" or mime_type == "application/pdf":
            return _extract_pdf_text(temp_path)
        if suffix == ".docx" or mime_type == (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ):
            return _extract_docx_text(temp_path)
        if suffix in {".txt", ".md"} or mime_type.startswith("text/"):
            return temp_path.read_text(encoding="utf-8", errors="replace")
        raise DocumentContentError(f"Unsupported file type for extraction: {mime_type or suffix}")
    finally:
        temp_path.unlink(missing_ok=True)


def load_document_text(document: Document) -> str:
    content = download_document_bytes(document)
    text = extract_text_from_bytes(
        content,
        file_name=document.file_name,
        mime_type=document.mime_type,
    )
    cleaned = text.strip()
    if not cleaned:
        raise DocumentContentError(f"No extractable text in {document.file_name}")
    if len(cleaned) > MAX_DOCUMENT_TEXT_CHARS:
        return cleaned[:MAX_DOCUMENT_TEXT_CHARS]
    return cleaned


def _extract_pdf_text(file_path: Path) -> str:
    loader = PyPDFLoader(str(file_path))
    pages = loader.load()
    return "\n\n".join(page.page_content for page in pages if page.page_content.strip())


def _extract_pdf_text_from_bytes(content: bytes) -> str:
    """Extract PDF text directly from bytes without temp file."""
    try:
        import io
        from langchain_community.document_loaders import PyPDFLoader
        
        # Create a file-like object from bytes
        pdf_file = io.BytesIO(content)
        loader = PyPDFLoader(pdf_file)
        pages = loader.load()
        return "\n\n".join(page.page_content for page in pages if page.page_content.strip())
    except Exception as e:
        raise DocumentContentError(f"Failed to extract PDF text from bytes: {e}")


def _extract_docx_text(file_path: Path) -> str:
    loader = Docx2txtLoader(str(file_path))
    pages = loader.load()
    return "\n\n".join(page.page_content for page in pages if page.page_content.strip())


def _extract_docx_text_from_bytes(content: bytes) -> str:
    """Extract DOCX text directly from bytes without temp file."""
    try:
        import io
        from langchain_community.document_loaders import Docx2txtLoader
        
        # Create a file-like object from bytes
        docx_file = io.BytesIO(content)
        loader = Docx2txtLoader(docx_file)
        pages = loader.load()
        return "\n\n".join(page.page_content for page in pages if page.page_content.strip())
    except Exception as e:
        raise DocumentContentError(f"Failed to extract DOCX text from bytes: {e}")


def _suffix_for_mime(mime_type: str, file_name: str) -> str:
    extension = Path(file_name).suffix.lower()
    if extension:
        return extension

    mime_suffix_map = {
        "application/pdf": ".pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "text/plain": ".txt",
    }
    return mime_suffix_map.get(mime_type, ".bin")
