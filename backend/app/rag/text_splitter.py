from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.utils.config import Settings, get_settings


def get_text_splitter(settings: Settings | None = None) -> RecursiveCharacterTextSplitter:
    """Create a configured RecursiveCharacterTextSplitter."""
    config = settings or get_settings()
    return RecursiveCharacterTextSplitter(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
        length_function=len,
        is_separator_regex=False,
    )


def split_documents(
    documents: list[Document],
    settings: Settings | None = None,
) -> list[Document]:
    """Chunk documents for embedding and vector storage."""
    if not documents:
        return []

    splitter = get_text_splitter(settings)
    chunks = splitter.split_documents(documents)

    for index, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = index

    return chunks
