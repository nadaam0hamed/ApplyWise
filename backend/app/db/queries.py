"""Single-row PostgREST query helpers for supabase-py 2.31+."""

from __future__ import annotations

from typing import Any

from postgrest.base_request_builder import APIResponse


class MultipleRowsError(RuntimeError):
    """Raised when a query returned more rows than expected."""


def _require_single_row(
    rows: list[Any],
    *,
    not_found_message: str,
) -> dict[str, Any]:
    if len(rows) == 0:
        raise LookupError(not_found_message)
    if len(rows) > 1:
        raise MultipleRowsError(
            "The result contains more than one row when exactly one was expected."
        )
    return rows[0]


def fetch_maybe_single(builder: Any) -> dict[str, Any] | None:
    """Execute a select filter chain expecting zero or one row.

    Uses ``maybe_single()`` on ``SyncSelectRequestBuilder`` (supabase-py 2.31+).
    Returns ``None`` when no row matches. Raises ``MultipleRowsError`` when more
    than one row is returned.
    """
    result = builder.maybe_single().execute()
    if result is None:
        return None
    return result.data


def fetch_single_row(builder: Any, *, not_found_message: str) -> dict[str, Any]:
    """Execute a query builder and require exactly one row in the response.

    Use for insert/update/upsert chains (``SyncQueryRequestBuilder``) that do not
    expose ``.single()`` in supabase-py 2.31+.
    """
    response: APIResponse = builder.execute()
    return _require_single_row(response.data or [], not_found_message=not_found_message)
