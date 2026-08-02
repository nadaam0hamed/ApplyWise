"""Unit tests for ApplicationAnalysisChain structured output handling."""

from unittest.mock import MagicMock, patch

from langchain_core.exceptions import OutputParserException
from langchain_core.messages import AIMessage

from app.chains.analysis_chain import ApplicationAnalysisChain
from app.chains.output_parser import ApplicationAnalysisResult, bind_analysis_json_generation


def test_analyze_retries_once_when_initial_parse_fails():
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = []
    mock_llm = MagicMock()

    chain = ApplicationAnalysisChain(llm=mock_llm, retriever=mock_retriever)
    chain._llm_step = MagicMock(
        return_value=AIMessage(content="Here is the analysis:\n```json\n{not valid}\n```")
    )
    chain._retry_llm_step = MagicMock(
        return_value=AIMessage(
            content=(
                '{"readiness_score": 75, "strengths": ["Good profile"], '
                '"weaknesses": ["Missing SOP"], "missing_documents": ["Statement of Purpose"], '
                '"recommendations": ["Upload SOP"], "next_steps": ["Draft SOP"]}'
            )
        )
    )

    with patch.object(
        chain,
        "_parse_llm_output",
        side_effect=[
            OutputParserException("Invalid json output"),
            ApplicationAnalysisResult(
                readiness_score=75,
                strengths=["Good profile"],
                weaknesses=["Missing SOP"],
                missing_documents=["Statement of Purpose"],
                recommendations=["Upload SOP"],
                next_steps=["Draft SOP"],
            ),
        ],
    ):
        result = chain.analyze(
            application_information="Applicant profile",
            document_summaries=["CV uploaded"],
        )

    assert result.readiness_score == 75
    chain._retry_llm_step.invoke.assert_called_once()


def test_bind_analysis_json_generation_uses_json_schema_response_format():
    from langchain_core.language_models.fake_chat_models import FakeListChatModel

    llm = FakeListChatModel(responses=['{"readiness_score": 50}'])
    bound = bind_analysis_json_generation(llm)

    assert bound.kwargs.get("response_format", {}).get("type") == "json_object"
    assert bound.kwargs.get("response_format", {}).get("schema") is not None
    assert bound.kwargs.get("ls_structured_output_format", {}).get("kwargs", {}).get("method") == "json_schema"


def test_analysis_prompt_includes_json_example_and_format_instructions():
    from app.chains.prompts import ANALYSIS_PROMPT_TEMPLATE

    rendered = ANALYSIS_PROMPT_TEMPLATE.format(
        application_information="info",
        document_summaries="docs",
        rag_context="context",
        format_instructions="SCHEMA_INSTRUCTIONS",
    )

    assert "Return ONLY valid JSON." in rendered
    assert "Never wrap JSON inside ``` blocks" in rendered
    assert '"readiness_score": 72' in rendered
    assert rendered.rstrip().endswith("SCHEMA_INSTRUCTIONS")
