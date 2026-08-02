"""Database client and schema helpers."""

from app.db.queries import MultipleRowsError, fetch_maybe_single, fetch_single_row
from app.db.schema import (
    AI_ANALYSIS_COLUMNS,
    APPLICATION_COLUMNS,
    DOCUMENT_COLUMNS,
    REQUIREMENT_COLUMNS,
    REQUIREMENT_STATUS_COLUMNS,
)
from app.db.supabase import SupabaseConfigurationError, get_supabase_client

__all__ = [
    "AI_ANALYSIS_COLUMNS",
    "APPLICATION_COLUMNS",
    "DOCUMENT_COLUMNS",
    "REQUIREMENT_COLUMNS",
    "REQUIREMENT_STATUS_COLUMNS",
    "MultipleRowsError",
    "fetch_maybe_single",
    "fetch_single_row",
    "SupabaseConfigurationError",
    "get_supabase_client",
]
