"""LangChain analysis pipeline built on Hybrid RAG retrieval."""

from __future__ import annotations

from typing import Sequence

from langchain_core.documents import Document
from langchain_core.exceptions import OutputParserException
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.runnables import Runnable

from app.chains.output_parser import (
    ApplicationAnalysisResult,
    bind_analysis_json_generation,
    get_analysis_output_parser,
)
from app.chains.prompts import (
    get_analysis_json_retry_prompt_template,
    get_analysis_prompt_template,
)
from app.rag.retriever import HybridRetriever
from app.utils.config import Settings, get_settings


def format_document_summaries(summaries: str | Sequence[str]) -> str:
    if isinstance(summaries, str):
        text = summaries.strip()
        return text if text else "No uploaded documents summarized yet."

    if not summaries:
        return "No uploaded documents summarized yet."

    lines: list[str] = []
    for index, summary in enumerate(summaries, start=1):
        cleaned = summary.strip()
        if cleaned:
            lines.append(f"{index}. {cleaned}")

    return "\n".join(lines) if lines else "No uploaded documents summarized yet."


def format_rag_context(documents: Sequence[Document]) -> str:
    if not documents:
        return "No relevant knowledge was retrieved from the vector store."

    blocks: list[str] = []
    for index, document in enumerate(documents, start=1):
        metadata = document.metadata or {}
        source = metadata.get("retrieved_from", metadata.get("knowledge_source", "unknown"))
        score = metadata.get("retrieval_score")
        header = f"[{index}] source={source}"
        if score is not None:
            header = f"{header}, score={score}"
        blocks.append(f"{header}\n{document.page_content.strip()}")

    return "\n\n".join(blocks)


def build_retrieval_query(
    application_information: str,
    *,
    override: str | None = None,
) -> str:
    if override and override.strip():
        return override.strip()
    return application_information.strip()


def _message_text(message: BaseMessage) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
        return "".join(parts)
    return str(content)


class ApplicationAnalysisChain:
    """
    Hybrid RAG + LLM chain that evaluates scholarship application readiness.

    Inject any LangChain ``BaseChatModel`` (from OpenAI, HuggingFace, etc.).
    """

    def __init__(
        self,
        *,
        llm: BaseChatModel,
        retriever: HybridRetriever,
        settings: Settings | None = None,
    ) -> None:
        self.llm = llm
        self.retriever = retriever
        self.settings = settings or get_settings()
        self.prompt = get_analysis_prompt_template()
        self.retry_prompt = get_analysis_json_retry_prompt_template()
        self.parser = get_analysis_output_parser()
        self.structured_llm = bind_analysis_json_generation(llm)
        self._llm_step: Runnable = self.prompt | self.structured_llm
        self._retry_llm_step: Runnable = self.retry_prompt | self.structured_llm
        self._runnable: Runnable = self.prompt | self.structured_llm | self.parser

    @property
    def runnable(self) -> Runnable:
        """LangChain runnable: prompt | llm | structured parser."""
        return self._runnable

    def _coerce_result(self, result: ApplicationAnalysisResult | object) -> ApplicationAnalysisResult:
        if isinstance(result, ApplicationAnalysisResult):
            return result
        return ApplicationAnalysisResult.model_validate(result)

    def _parse_llm_output(self, message: BaseMessage) -> ApplicationAnalysisResult:
        parsed = self.parser.invoke(message)
        return self._coerce_result(parsed)

    def _retry_json_parse(self, previous_output: str) -> ApplicationAnalysisResult:
        retry_message = self._retry_llm_step.invoke(
            {
                "previous_output": previous_output,
                "format_instructions": self.parser.get_format_instructions(),
            }
        )
        if not isinstance(retry_message, BaseMessage):
            retry_message = AIMessage(content=str(retry_message))
        return self._parse_llm_output(retry_message)

    def analyze(
        self,
        *,
        application_information: str,
        document_summaries: str | Sequence[str],
        retrieval_query: str | None = None,
        retrieval_k: int | None = None,
    ) -> ApplicationAnalysisResult:
        """
        Run retrieval with ``HybridRetriever``, then LLM analysis with structured output.

        Args:
            application_information: Structured or free-text application profile.
            document_summaries: Summaries of user-uploaded documents.
            retrieval_query: Optional override for the vector search query.
            retrieval_k: Optional top-k override; defaults to settings.retrieval_top_k.
        """
        query = build_retrieval_query(
            application_information,
            override=retrieval_query,
        )
        top_k = retrieval_k or self.settings.retrieval_top_k
        retrieved = self.retriever.retrieve(query, k=top_k)

        prompt_inputs = {
            "application_information": application_information.strip(),
            "document_summaries": format_document_summaries(document_summaries),
            "rag_context": format_rag_context(retrieved),
            "format_instructions": self.parser.get_format_instructions(),
        }

        llm_message = self._llm_step.invoke(prompt_inputs)
        if not isinstance(llm_message, BaseMessage):
            llm_message = AIMessage(content=str(llm_message))

        try:
            return self._parse_llm_output(llm_message)
        except OutputParserException:
            return self._retry_json_parse(_message_text(llm_message))
