"""Structured output parsing for scholarship application analysis."""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.utils.function_calling import convert_to_json_schema
from pydantic import BaseModel, Field, field_validator

from app.utils.readiness_score import normalize_readiness_score


class ApplicationAnalysisResult(BaseModel):
    """Structured analysis returned by the LangChain analysis pipeline."""

    readiness_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Overall application readiness from 0 to 100.",
    )

    @field_validator("readiness_score", mode="before")
    @classmethod
    def _coerce_readiness_score(cls, value: object) -> int:
        return normalize_readiness_score(value)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    missing_documents: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)


APPLICATION_ANALYSIS_JSON_EXAMPLE = """{
  "readiness_score": 72,
  "strengths": [
    "Strong academic record with consistent GPA",
    "Relevant internship experience in the target field"
  ],
  "weaknesses": [
    "Statement of purpose lacks program-specific detail",
    "No language test scores on file"
  ],
  "missing_documents": [
    "IELTS or TOEFL certificate",
    "Official academic transcript"
  ],
  "recommendations": [
    "Tailor the statement of purpose to the target program",
    "Upload verified language test results before the deadline"
  ],
  "next_steps": [
    "Register for IELTS and schedule the earliest available sitting",
    "Request an official transcript from the registrar"
  ]
}"""


def get_analysis_output_parser() -> PydanticOutputParser:
    """Parser that coerces LLM output into ApplicationAnalysisResult."""
    return PydanticOutputParser(pydantic_object=ApplicationAnalysisResult)


def bind_analysis_json_generation(llm: BaseChatModel) -> BaseChatModel:
    """
    Enable native JSON generation on chat models that support Hugging Face
    ``response_format`` (e.g. ``ChatHuggingFace`` over ``HuggingFaceEndpoint``).

    Keeps ``PydanticOutputParser`` as the parser; this only constrains generation.
    """
    formatted_schema = convert_to_json_schema(ApplicationAnalysisResult)
    return llm.bind(
        response_format={"type": "json_object", "schema": formatted_schema},
        ls_structured_output_format={
            "kwargs": {"method": "json_schema"},
            "schema": ApplicationAnalysisResult,
        },
    )
