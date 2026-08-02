"""Pluggable LLM providers for analysis chains (OpenAI, HuggingFace, etc.)."""

from typing import Protocol

from langchain_core.language_models.chat_models import BaseChatModel


class AnalysisLLMProvider(Protocol):
    """
    Factory for chat models used in analysis pipelines.

    Implementations can wrap OpenAI, HuggingFace, or other LangChain chat model
    integrations without the chain layer importing a specific vendor.
    """

    def create_chat_model(self) -> BaseChatModel:
        """Build and return a LangChain-compatible chat model."""
        ...
