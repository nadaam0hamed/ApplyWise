"""LangChain chain definitions for ApplyWise analysis."""

from app.chains.analysis_chain import (
    ApplicationAnalysisChain,
    build_retrieval_query,
    format_document_summaries,
    format_rag_context,
)
from app.chains.document_extraction_chain import DocumentExtractionChain
from app.chains.extraction_parser import ApplicantProfile
from app.chains.huggingface_provider import (
    HuggingFaceAnalysisLLMProvider,
    HuggingFaceInferenceConfigurationError,
    resolve_huggingface_api_token,
)
from app.chains.llm_provider import AnalysisLLMProvider
from app.chains.output_parser import (
    APPLICATION_ANALYSIS_JSON_EXAMPLE,
    ApplicationAnalysisResult,
    bind_analysis_json_generation,
    get_analysis_output_parser,
)
from app.chains.prompts import (
    ANALYSIS_JSON_RETRY_PROMPT_TEMPLATE,
    ANALYSIS_PROMPT_TEMPLATE,
    get_analysis_json_retry_prompt_template,
    get_analysis_prompt_template,
)

__all__ = [
    "ANALYSIS_JSON_RETRY_PROMPT_TEMPLATE",
    "ANALYSIS_PROMPT_TEMPLATE",
    "APPLICATION_ANALYSIS_JSON_EXAMPLE",
    "AnalysisLLMProvider",
    "ApplicantProfile",
    "ApplicationAnalysisChain",
    "DocumentExtractionChain",
    "HuggingFaceAnalysisLLMProvider",
    "HuggingFaceInferenceConfigurationError",
    "ApplicationAnalysisResult",
    "bind_analysis_json_generation",
    "build_retrieval_query",
    "format_document_summaries",
    "format_rag_context",
    "get_analysis_json_retry_prompt_template",
    "get_analysis_output_parser",
    "get_analysis_prompt_template",
    "resolve_huggingface_api_token",
]
