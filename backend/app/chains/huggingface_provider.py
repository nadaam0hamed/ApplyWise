"""Hugging Face Inference API provider for application analysis chains."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

DEFAULT_HF_INFERENCE_MODEL = "microsoft/Phi-3-mini-4k-instruct"
HF_API_TOKEN_ENV_KEYS = ("HF_TOKEN", "HUGGINGFACEHUB_API_TOKEN", "HUGGINGFACE_HUB_TOKEN")
HF_INFERENCE_MODEL_ENV_KEY = "HUGGINGFACE_INFERENCE_MODEL"
SUPPORTED_INFERENCE_TASKS = frozenset({"conversational", "text-generation"})


class HuggingFaceInferenceConfigurationError(RuntimeError):
    """Raised when Hugging Face Inference API settings are invalid or incomplete."""


def resolve_huggingface_api_token() -> str:
    """
    Load a Hugging Face API token from the environment (.env via python-dotenv in config).

    Checks ``HF_TOKEN`` first, then legacy Hugging Face Hub variable names.
    """
    for env_key in HF_API_TOKEN_ENV_KEYS:
        value = os.getenv(env_key)
        if value and value.strip():
            return value.strip()

    keys_list = ", ".join(HF_API_TOKEN_ENV_KEYS)
    raise HuggingFaceInferenceConfigurationError(
        "Hugging Face API token is missing. "
        f"Set one of ({keys_list}) in your backend `.env` file. "
        "Create a token at https://huggingface.co/settings/tokens."
    )


def resolve_huggingface_inference_model(explicit_model: str | None = None) -> str:
    if explicit_model and explicit_model.strip():
        return explicit_model.strip()

    from_env = os.getenv(HF_INFERENCE_MODEL_ENV_KEY)
    if from_env and from_env.strip():
        return from_env.strip()

    return DEFAULT_HF_INFERENCE_MODEL


def validate_huggingface_inference_model(model: str) -> None:
    """
    Verify that ``model`` is listed for Hugging Face Inference Providers.

    Uses the Hub ``inferenceProviderMapping`` metadata (same source as the
    Inference Providers model catalog).
    """
    try:
        from huggingface_hub.inference._providers._common import (
            _fetch_inference_provider_mapping,
        )

        mapping = _fetch_inference_provider_mapping(model)
    except ValueError as exc:
        raise HuggingFaceInferenceConfigurationError(
            f"Hugging Face Inference model `{model}` is not supported by Hugging Face "
            "Inference Providers. Choose a supported chat/instruction model from "
            "https://huggingface.co/inference/models and set "
            f"`{HF_INFERENCE_MODEL_ENV_KEY}` in your backend `.env` file."
        ) from exc
    except Exception as exc:
        raise HuggingFaceInferenceConfigurationError(
            f"Unable to verify Hugging Face Inference model `{model}` against Inference "
            "Providers. Check the model id and your network connection, or pick a model "
            "from https://huggingface.co/inference/models."
        ) from exc

    available_tasks = {entry.task for entry in mapping}
    if not available_tasks.intersection(SUPPORTED_INFERENCE_TASKS):
        raise HuggingFaceInferenceConfigurationError(
            f"Hugging Face Inference model `{model}` is not supported for chat/instruction "
            f"inference via Inference Providers (available tasks: "
            f"{sorted(available_tasks)}). Set `{HF_INFERENCE_MODEL_ENV_KEY}` to a "
            "conversational model from https://huggingface.co/inference/models."
        )


@dataclass
class HuggingFaceAnalysisLLMProvider:
    """
    ``AnalysisLLMProvider`` implementation using the Hugging Face Inference API.

    Uses ``HuggingFaceEndpoint`` (remote ``huggingface_hub.InferenceClient``), not
    local ``transformers`` pipeline inference. Swap with OpenAI or Ollama providers
    at composition time without changing ``ApplicationAnalysisChain``.
    """

    model_id: str | None = None
    provider: str | None = None
    task: str = "text-generation"
    max_new_tokens: int = 512
    temperature: float = 0.1
    timeout: int = 60
    api_token: str | None = field(default=None, repr=False)

    def create_chat_model(self) -> BaseChatModel:
        token = self.api_token or resolve_huggingface_api_token()
        model = resolve_huggingface_inference_model(self.model_id)
        validate_huggingface_inference_model(model)

        try:
            endpoint = HuggingFaceEndpoint(
                repo_id=model,
                task=self.task,
                provider=self.provider,
                huggingfacehub_api_token=token,
                max_new_tokens=self.max_new_tokens,
                temperature=self.temperature,
                timeout=self.timeout,
            )
            return ChatHuggingFace(llm=endpoint)
        except ImportError as exc:
            raise HuggingFaceInferenceConfigurationError(
                "Hugging Face Inference dependencies are not installed. "
                "Ensure `langchain-huggingface` and `huggingface-hub` are available."
            ) from exc
        except ValueError as exc:
            raise HuggingFaceInferenceConfigurationError(
                f"Invalid Hugging Face Inference configuration for model `{model}`: {exc}"
            ) from exc
