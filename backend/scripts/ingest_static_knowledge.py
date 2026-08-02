"""Ingest static knowledge-base PDFs into ChromaDB."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.rag import StaticKnowledgeIngester  # noqa: E402
from app.utils.config import get_settings  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ingest static knowledge-base PDFs into ChromaDB.",
    )
    parser.add_argument(
        "--force-rebuild",
        action="store_true",
        help="Delete and recreate the static knowledge collection before ingesting.",
    )
    args = parser.parse_args()

    settings = get_settings()
    ingester = StaticKnowledgeIngester()
    result = ingester.ingest(force_rebuild=args.force_rebuild)

    print(f"Static knowledge directory: {settings.static_knowledge_dir.resolve()}")
    print(f"Chroma persist directory: {settings.chroma_persist_path.resolve()}")
    print(f"Collection: {settings.static_collection_name}")
    print(f"Embedding model: {settings.embedding_model}")
    print(f"Chunk size / overlap: {settings.chunk_size} / {settings.chunk_overlap}")
    print(f"PDF pages loaded: {result.documents_loaded}")
    print(f"Chunks created: {result.chunks_created}")
    print(f"Chunks stored: {result.chunks_stored}")

    if result.documents_loaded == 0:
        print(
            "Warning: no PDF files were found. "
            f"Add PDFs under {settings.static_knowledge_dir.resolve()}",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
