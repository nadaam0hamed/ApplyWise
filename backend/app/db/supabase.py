"""Supabase client factory for backend services."""

from functools import lru_cache

from supabase import Client, create_client

from app.utils.config import Settings, get_settings


class SupabaseConfigurationError(RuntimeError):
    """Raised when Supabase environment variables are missing or invalid."""


def _require_supabase_settings(settings: Settings | None = None) -> Settings:
    resolved = settings or get_settings()
    missing: list[str] = []

    if not resolved.supabase_url:
        missing.append("SUPABASE_URL")
    if not resolved.supabase_service_role_key:
        missing.append("SUPABASE_SERVICE_ROLE_KEY")

    if missing:
        keys = ", ".join(missing)
        raise SupabaseConfigurationError(
            f"Supabase is not configured. Set {keys} in backend `.env`."
        )

    return resolved


@lru_cache
def get_supabase_client() -> Client:
    settings = _require_supabase_settings()
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
