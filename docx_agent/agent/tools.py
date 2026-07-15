"""LangChain tool definitions that wrap each proofreading skill.

These tools are consumed by the :class:`ProofreadingAgent` as the callable
interface that the LLM can invoke.  Each tool accepts a JSON-serialisable
``input`` string, calls the underlying skill, and returns a JSON-encoded
:class:`SkillResult` summary.
"""

from __future__ import annotations

import json
from typing import Any

from langchain_core.tools import StructuredTool, Tool
from pydantic import BaseModel, Field

from docx_agent.skills.content_checker_skill import ContentCheckerSkill
from docx_agent.skills.docx_reader_skill import DocxReaderSkill
from docx_agent.skills.font_checker_skill import FontCheckerSkill
from docx_agent.skills.format_checker_skill import FormatCheckerSkill
from docx_agent.utils.logger import get_logger

_logger = get_logger("docx_agent.tools")


# ---------------------------------------------------------------------------
# Singleton skill instances (created once, reused across tool calls)
# ---------------------------------------------------------------------------
_reader = DocxReaderSkill()
_content = ContentCheckerSkill()
_font = FontCheckerSkill()
_format = FormatCheckerSkill()


# ---------------------------------------------------------------------------
# Input schemas (Pydantic v2 compatible)
# ---------------------------------------------------------------------------


class DocxPathInput(BaseModel):
    docx_path: str = Field(..., description="Absolute or relative path to the .docx file.")


class DocumentDataInput(BaseModel):
    document_data_json: str = Field(
        ...,
        description=(
            "JSON string of the document data dict previously returned by the "
            "read_docx tool (key: 'document')."
        ),
    )


# ---------------------------------------------------------------------------
# Tool helper
# ---------------------------------------------------------------------------


def _to_json(result: Any) -> str:
    try:
        return json.dumps(result.to_dict(), ensure_ascii=False, indent=2)
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"error": str(exc)})


def _parse_document_data(document_data_json: str) -> dict[str, Any]:
    """Parse the JSON string and return the inner document dict."""
    data = json.loads(document_data_json)
    # Accept either the full SkillResult dict or the bare document dict
    if "document" in data:
        return data["document"]
    if "metadata" in data and "document" in data["metadata"]:
        return data["metadata"]["document"]
    return data


# ---------------------------------------------------------------------------
# Tool functions
# ---------------------------------------------------------------------------


def _read_docx(docx_path: str) -> str:
    _logger.info("Tool: read_docx('%s')", docx_path)
    result = _reader.run(docx_path=docx_path)
    return _to_json(result)


def _check_content(document_data_json: str) -> str:
    _logger.info("Tool: check_content")
    doc = _parse_document_data(document_data_json)
    result = _content.run(document_data=doc)
    return _to_json(result)


def _check_fonts(document_data_json: str) -> str:
    _logger.info("Tool: check_fonts")
    doc = _parse_document_data(document_data_json)
    result = _font.run(document_data=doc)
    return _to_json(result)


def _check_format(document_data_json: str) -> str:
    _logger.info("Tool: check_format")
    doc = _parse_document_data(document_data_json)
    result = _format.run(document_data=doc)
    return _to_json(result)


# ---------------------------------------------------------------------------
# Public tool registry
# ---------------------------------------------------------------------------


def get_tools() -> list[StructuredTool]:
    """Return all proofreading tools ready for use with a LangChain agent."""
    return [
        StructuredTool.from_function(
            func=_read_docx,
            name="read_docx",
            description=(
                "Read a .docx file and return a structured JSON representation of "
                "its paragraphs, tables, fonts, and formatting.  Call this first "
                "before any other proofreading tool."
            ),
            args_schema=DocxPathInput,
        ),
        StructuredTool.from_function(
            func=_check_content,
            name="check_content",
            description=(
                "Run spell and grammar checks on the document data produced by "
                "read_docx.  Pass the full JSON returned by read_docx."
            ),
            args_schema=DocumentDataInput,
        ),
        StructuredTool.from_function(
            func=_check_fonts,
            name="check_fonts",
            description=(
                "Validate font families, sizes, and colours in the document data "
                "produced by read_docx.  Pass the full JSON returned by read_docx."
            ),
            args_schema=DocumentDataInput,
        ),
        StructuredTool.from_function(
            func=_check_format,
            name="check_format",
            description=(
                "Check paragraph alignment, heading hierarchy, spacing, and "
                "indentation in the document data produced by read_docx.  Pass the "
                "full JSON returned by read_docx."
            ),
            args_schema=DocumentDataInput,
        ),
    ]
