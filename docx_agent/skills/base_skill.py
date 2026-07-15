"""Abstract base class shared by every proofreading skill."""

from __future__ import annotations

import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Issue:
    """A single proofreading issue found in the document.

    Attributes
    ----------
    category:
        High-level category, e.g. ``'spelling'``, ``'font'``, ``'format'``.
    severity:
        One of ``'error'``, ``'warning'``, or ``'info'``.
    message:
        Human-readable description of the issue.
    location:
        Free-form location string, e.g. ``'Paragraph 3'`` or ``'Table 1, Row 2'``.
    suggestion:
        Optional corrective suggestion.
    context:
        Short snippet of the surrounding text for reference.
    """

    category: str
    severity: str
    message: str
    location: str = ""
    suggestion: str = ""
    context: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "severity": self.severity,
            "message": self.message,
            "location": self.location,
            "suggestion": self.suggestion,
            "context": self.context,
        }


@dataclass
class SkillResult:
    """Container returned by every skill's :meth:`execute` method.

    Attributes
    ----------
    skill_name:
        Identifier for the skill that produced this result.
    success:
        ``True`` when the skill ran to completion without an unhandled error.
    issues:
        List of :class:`Issue` objects discovered during execution.
    metadata:
        Arbitrary key/value pairs that provide extra context (e.g. document
        statistics).
    error:
        Error message if *success* is ``False``.
    """

    skill_name: str
    success: bool = True
    issues: list[Issue] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str = ""

    # Convenience helpers ------------------------------------------------

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")

    @property
    def info_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "info")

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_name": self.skill_name,
            "success": self.success,
            "issues": [i.to_dict() for i in self.issues],
            "metadata": self.metadata,
            "error": self.error,
            "summary": {
                "errors": self.error_count,
                "warnings": self.warning_count,
                "infos": self.info_count,
            },
        }


class BaseSkill(ABC):
    """Abstract base class for all docx_agent skills.

    Subclasses must implement :meth:`execute`.  Error handling and
    result wrapping are provided here so individual skills can stay
    focused on their domain logic.
    """

    #: Override in subclasses to give the skill a descriptive name.
    name: str = "base_skill"

    def __init__(self) -> None:
        from docx_agent.utils.logger import get_logger

        self._logger = get_logger(f"docx_agent.skills.{self.name}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, *args: Any, **kwargs: Any) -> SkillResult:
        """Execute the skill, catching any unexpected exceptions.

        Returns a :class:`SkillResult` with ``success=False`` and an
        ``error`` message when an exception is raised instead of
        propagating it to the caller.
        """
        try:
            return self.execute(*args, **kwargs)
        except Exception:  # noqa: BLE001
            tb = traceback.format_exc()
            self._logger.error("Unhandled exception in skill '%s':\n%s", self.name, tb)
            return SkillResult(
                skill_name=self.name,
                success=False,
                error=tb,
            )

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> SkillResult:
        """Perform the skill's work and return a :class:`SkillResult`.

        Parameters are skill-specific; see the concrete implementations
        for the exact signatures.
        """
