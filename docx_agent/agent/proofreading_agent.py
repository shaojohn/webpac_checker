"""Proofreading Agent – orchestrates all skills using LangChain.

Two modes of operation are provided:

1. **LLM-driven** (`run_with_llm`): Uses a LangChain ReAct agent backed by an
   OpenAI chat model to decide which tools to invoke and in what order.

2. **Deterministic** (`run`): Skips the LLM and calls every skill in a fixed
   sequence.  Useful when no API key is available or in testing.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from docx_agent.agent.tools import (
    _check_content,
    _check_fonts,
    _check_format,
    _read_docx,
    get_tools,
)
from docx_agent.skills.base_skill import SkillResult
from docx_agent.utils.logger import get_logger
from docx_agent.utils.validators import validate_docx_path

_logger = get_logger("docx_agent.agent")


# ---------------------------------------------------------------------------
# Aggregated result container
# ---------------------------------------------------------------------------


class ProofreadingResult:
    """Holds the combined output of all proofreading skills.

    Attributes
    ----------
    docx_path:
        Path of the file that was analysed.
    skill_results:
        Mapping from skill name → raw :class:`SkillResult` dict.
    all_issues:
        Flat list of every issue found across all skills.
    document_data:
        Structured document representation from DocxReaderSkill.
    llm_summary:
        Optional summary text produced by the LLM agent (only when
        :meth:`run_with_llm` was used).
    """

    def __init__(
        self,
        docx_path: str,
        skill_results: dict[str, dict[str, Any]],
        document_data: dict[str, Any],
        llm_summary: str = "",
    ) -> None:
        self.docx_path = docx_path
        self.skill_results = skill_results
        self.document_data = document_data
        self.llm_summary = llm_summary

        # Flatten all issues
        self.all_issues: list[dict[str, Any]] = []
        for result in skill_results.values():
            self.all_issues.extend(result.get("issues", []))

    # Convenience aggregates ------------------------------------------------

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.all_issues if i.get("severity") == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.all_issues if i.get("severity") == "warning")

    @property
    def info_count(self) -> int:
        return sum(1 for i in self.all_issues if i.get("severity") == "info")

    @property
    def total_issues(self) -> int:
        return len(self.all_issues)

    def to_dict(self) -> dict[str, Any]:
        return {
            "docx_path": self.docx_path,
            "skill_results": self.skill_results,
            "all_issues": self.all_issues,
            "llm_summary": self.llm_summary,
            "statistics": {
                "total": self.total_issues,
                "errors": self.error_count,
                "warnings": self.warning_count,
                "infos": self.info_count,
            },
        }


# ---------------------------------------------------------------------------
# Agent class
# ---------------------------------------------------------------------------


class ProofreadingAgent:
    """Orchestrate all proofreading skills for a DOCX document.

    Parameters
    ----------
    openai_api_key:
        API key for OpenAI.  Only needed when calling :meth:`run_with_llm`.
    model_name:
        LLM model to use (default ``'gpt-4o-mini'``).
    temperature:
        Sampling temperature (default ``0``).
    """

    def __init__(
        self,
        openai_api_key: str = "",
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.0,
    ) -> None:
        self._api_key = openai_api_key
        self._model_name = model_name
        self._temperature = temperature

    # ------------------------------------------------------------------
    # Public API – deterministic mode
    # ------------------------------------------------------------------

    def run(self, docx_path: str | Path) -> ProofreadingResult:
        """Run every skill deterministically, without an LLM.

        This is the recommended entry-point when you do not need the LLM
        to decide which checks to run.

        Parameters
        ----------
        docx_path:
            Path to the ``.docx`` file.

        Returns
        -------
        ProofreadingResult
        """
        path = validate_docx_path(docx_path)
        path_str = str(path)

        _logger.info("Starting deterministic proofreading: %s", path_str)

        # Step 1 – read the document
        raw_reader = _read_docx(path_str)
        reader_result = json.loads(raw_reader)

        if not reader_result.get("success", False):
            _logger.error("DocxReaderSkill failed: %s", reader_result.get("error"))
            return ProofreadingResult(
                docx_path=path_str,
                skill_results={"docx_reader": reader_result},
                document_data={},
            )

        document_data = reader_result.get("metadata", {}).get("document", {})
        document_data_json = json.dumps({"document": document_data})

        # Step 2 – run checks
        raw_content = _check_content(document_data_json)
        raw_font = _check_fonts(document_data_json)
        raw_format = _check_format(document_data_json)

        skill_results = {
            "docx_reader": reader_result,
            "content_checker": json.loads(raw_content),
            "font_checker": json.loads(raw_font),
            "format_checker": json.loads(raw_format),
        }

        _logger.info("Deterministic proofreading complete.")
        return ProofreadingResult(
            docx_path=path_str,
            skill_results=skill_results,
            document_data=document_data,
        )

    # ------------------------------------------------------------------
    # Public API – LLM-driven mode
    # ------------------------------------------------------------------

    def run_with_llm(
        self, docx_path: str | Path, verbose: bool = False
    ) -> ProofreadingResult:
        """Run proofreading using a LangChain tool-calling agent.

        The agent is given a set of tools (one per skill) and autonomously
        decides how to use them.  Falls back to deterministic mode when no
        API key is configured or when optional packages are missing.

        Parameters
        ----------
        docx_path:
            Path to the ``.docx`` file.
        verbose:
            If ``True``, enable verbose logging during agent execution.

        Returns
        -------
        ProofreadingResult
        """
        if not self._api_key:
            _logger.warning(
                "No OpenAI API key – falling back to deterministic mode."
            )
            return self.run(docx_path)

        try:
            from langchain.agents import create_agent
            from langchain_openai import ChatOpenAI
        except ImportError as exc:
            _logger.warning(
                "LangChain/OpenAI packages not available (%s) – falling back to "
                "deterministic mode.",
                exc,
            )
            return self.run(docx_path)

        path = validate_docx_path(docx_path)
        path_str = str(path)

        tools = get_tools()
        llm = ChatOpenAI(
            model=self._model_name,
            temperature=self._temperature,
            api_key=self._api_key,
        )

        system_prompt = (
            "You are a professional document proofreader. "
            "Your task is to thoroughly proofread a DOCX file.\n"
            "Steps:\n"
            "1. Use read_docx to load the document.\n"
            "2. Use check_content to find spelling and grammar issues.\n"
            "3. Use check_fonts to validate font usage.\n"
            "4. Use check_format to check paragraph and heading formatting.\n"
            "5. Provide a concise summary of all findings."
        )

        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=system_prompt,
        )

        _logger.info("Running LLM-driven proofreading: %s", path_str)

        user_message = f"Please proofread the DOCX file at: {path_str}"
        response = agent.invoke({"messages": [("human", user_message)]})

        # Extract the final text response
        messages = response.get("messages", [])
        llm_summary = ""
        for msg in reversed(messages):
            content = getattr(msg, "content", "")
            if content and isinstance(content, str):
                llm_summary = content
                break

        # Also run deterministic checks to collect full issue lists
        det_result = self.run(path_str)
        det_result.llm_summary = llm_summary

        _logger.info("LLM-driven proofreading complete.")
        return det_result
