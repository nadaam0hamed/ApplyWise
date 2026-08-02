"""Shared service-layer exceptions."""

class ApplicationNotFoundError(LookupError):
    """Raised when an application id does not exist in Supabase."""


class AnalysisServiceError(RuntimeError):
    """Raised when AI analysis or persistence fails."""
