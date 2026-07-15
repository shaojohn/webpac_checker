"""Skills package – each skill encapsulates one discrete proofreading capability."""

from docx_agent.skills.base_skill import BaseSkill, SkillResult
from docx_agent.skills.content_checker_skill import ContentCheckerSkill
from docx_agent.skills.docx_reader_skill import DocxReaderSkill
from docx_agent.skills.font_checker_skill import FontCheckerSkill
from docx_agent.skills.format_checker_skill import FormatCheckerSkill

__all__ = [
    "BaseSkill",
    "SkillResult",
    "DocxReaderSkill",
    "ContentCheckerSkill",
    "FontCheckerSkill",
    "FormatCheckerSkill",
]
