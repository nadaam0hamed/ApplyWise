"""Prompt templates for application analysis chains."""

from langchain_core.prompts import PromptTemplate

from app.chains.output_parser import APPLICATION_ANALYSIS_JSON_EXAMPLE


def _escape_prompt_braces(text: str) -> str:
    """Escape curly braces so LangChain PromptTemplate does not treat JSON as variables."""
    return text.replace("{", "{{").replace("}", "}}")


ANALYSIS_PROMPT_TEMPLATE = PromptTemplate(
    input_variables=[
        "application_information",
        "document_summaries",
        "rag_context",
        "format_instructions",
    ],
    template="""You are an expert scholarship and university application advisor for ApplyWise.

Analyze the applicant's materials using the application details, summaries of uploaded documents, and retrieved reference knowledge. Be specific, actionable, and grounded in the provided context. If information is missing, say so explicitly in weaknesses, missing_documents, or recommendations.

## Application information
{application_information}

## Uploaded document summaries
{document_summaries}

## Retrieved knowledge (RAG context)
{rag_context}

Produce a structured assessment. Assign readiness_score as a number from 0 to 100.

## Response format — mandatory

Your entire reply MUST be a single JSON object and nothing else.

Rules:
- Return ONLY valid JSON.
- Never return markdown.
- Never wrap JSON inside ``` blocks or any other fences.
- Never add explanations, labels, headings, or text before or after the JSON.
- The JSON must exactly match the ApplicationAnalysisResult schema described below.
- Use double quotes for all keys and string values.
- Do not include trailing commas or comments in the JSON.

## Complete example (exact shape required)

""" + _escape_prompt_braces(APPLICATION_ANALYSIS_JSON_EXAMPLE) + """

## JSON schema — strict (your response must match exactly)

{format_instructions}
""",
)

ANALYSIS_JSON_RETRY_PROMPT_TEMPLATE = PromptTemplate(
    input_variables=["previous_output", "format_instructions"],
    template="""Your previous answer could not be parsed as valid JSON.

Convert ONLY your previous answer into valid JSON that matches the ApplicationAnalysisResult schema below.

Rules:
- Return ONLY valid JSON.
- Never return markdown.
- Never wrap JSON inside ``` blocks or any other fences.
- Never add explanations, labels, headings, or text before or after the JSON.
- Preserve the meaning of your previous answer; only fix the format.
- The JSON must exactly match ApplicationAnalysisResult.

## Previous answer
{previous_output}

## JSON schema — strict (your response must match exactly)

{format_instructions}
""",
)


def get_analysis_prompt_template() -> PromptTemplate:
    """Return the analysis PromptTemplate used by the hybrid RAG chain."""
    return ANALYSIS_PROMPT_TEMPLATE


def get_analysis_json_retry_prompt_template() -> PromptTemplate:
    """Return the one-shot JSON repair prompt used after a parse failure."""
    return ANALYSIS_JSON_RETRY_PROMPT_TEMPLATE
