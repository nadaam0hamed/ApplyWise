"""Normalize readiness_score values for validation and Supabase persistence."""

from __future__ import annotations

from typing import Any


def normalize_readiness_score(value: Any) -> int:
    """Convert numeric readiness_score values to an integer in ``[0, 100]``.

    Accepts integers, floats, and numeric strings such as ``"70"`` or ``"70.0"``.
    """
    if isinstance(value, bool):
        raise ValueError("readiness_score must be a number, not a boolean.")

    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            raise ValueError("readiness_score cannot be empty.")
        try:
            numeric = float(stripped)
        except ValueError as exc:
            raise ValueError(f"readiness_score must be numeric, got {value!r}.") from exc
    elif isinstance(value, int):
        numeric = float(value)
    elif isinstance(value, float):
        numeric = value
    else:
        raise ValueError(
            "readiness_score must be a number or numeric string, "
            f"got {type(value).__name__}."
        )

    score = int(round(numeric))
    if score < 0 or score > 100:
        raise ValueError(f"readiness_score must be between 0 and 100, got {score}.")
    return score
