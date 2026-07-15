"""Content Checker Skill – spell and grammar checking for DOCX documents."""

from __future__ import annotations

import re
from typing import Any

from docx_agent.skills.base_skill import BaseSkill, Issue, SkillResult

# Spellchecker import is optional (graceful degradation)
try:
    from spellchecker import SpellChecker  # type: ignore

    _SPELL_AVAILABLE = True
except ImportError:
    _SPELL_AVAILABLE = False

# language-tool-python import is optional (requires Java)
try:
    import language_tool_python  # type: ignore

    _GRAMMAR_AVAILABLE = True
except ImportError:
    _GRAMMAR_AVAILABLE = False


class ContentCheckerSkill(BaseSkill):
    """Check document text for spelling and grammar issues."""

    name = "content_checker"

    def __init__(self, language: str = "en") -> None:
        super().__init__()
        self._language = language
        self._spell: Any = None
        self._grammar_tool: Any = None

        if _SPELL_AVAILABLE:
            try:
                self._spell = SpellChecker(language=language)
                self._logger.info("SpellChecker initialised for language '%s'", language)
            except Exception as exc:  # noqa: BLE001
                self._logger.warning("SpellChecker init failed: %s", exc)
        else:
            self._logger.warning(
                "pyspellchecker not installed – spell checking disabled."
            )

    def execute(self, document_data: dict[str, Any]) -> SkillResult:  # type: ignore[override]
        """Run spell and grammar checks on the extracted document data.

        Parameters
        ----------
        document_data:
            The ``"document"`` dict produced by :class:`DocxReaderSkill`.

        Returns
        -------
        SkillResult
        """
        self._logger.info("Running content checks…")
        issues: list[Issue] = []

        paragraphs = document_data.get("paragraphs", [])

        for para in paragraphs:
            text: str = para.get("text", "").strip()
            if not text:
                continue

            location = f"Paragraph {para['index'] + 1}"

            # Spell check
            if self._spell is not None:
                issues.extend(self._spell_check(text, location))

            # Grammar check (lazy-initialise to avoid slow startup)
            issues.extend(self._grammar_check(text, location))

            # Additional heuristic checks
            issues.extend(self._heuristic_checks(text, location))

        metadata = {
            "paragraphs_checked": len(paragraphs),
            "spell_checking_available": _SPELL_AVAILABLE and self._spell is not None,
            "grammar_checking_available": _GRAMMAR_AVAILABLE,
        }

        self._logger.info("Content check complete – %d issues found.", len(issues))
        return SkillResult(
            skill_name=self.name,
            success=True,
            issues=issues,
            metadata=metadata,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _spell_check(self, text: str, location: str) -> list[Issue]:
        issues: list[Issue] = []
        # Extract English words (skip CJK and numbers)
        words = re.findall(r"[a-zA-Z']+", text)
        if not words:
            return issues

        misspelled = self._spell.unknown(words)
        for word in misspelled:
            candidates = self._spell.candidates(word) or set()
            suggestion = ", ".join(sorted(candidates)[:3]) if candidates else ""
            issues.append(
                Issue(
                    category="spelling",
                    severity="warning",
                    message=f"Possible misspelling: '{word}'",
                    location=location,
                    suggestion=suggestion,
                    context=text[:120],
                )
            )
        return issues

    def _grammar_check(self, text: str, location: str) -> list[Issue]:
        if not _GRAMMAR_AVAILABLE:
            return []

        issues: list[Issue] = []
        try:
            if self._grammar_tool is None:
                self._grammar_tool = language_tool_python.LanguageTool(
                    self._language if "-" in self._language else "en-US"
                )
                self._logger.info("LanguageTool initialised.")

            matches = self._grammar_tool.check(text)
            for match in matches:
                issues.append(
                    Issue(
                        category="grammar",
                        severity="warning",
                        message=match.message,
                        location=location,
                        suggestion=", ".join(match.replacements[:3]),
                        context=text[max(0, match.offset - 20): match.offset + 40],
                    )
                )
        except Exception as exc:  # noqa: BLE001
            self._logger.warning("Grammar check skipped: %s", exc)

        return issues

    def _heuristic_checks(self, text: str, location: str) -> list[Issue]:
        """Simple rule-based content checks that don't require external tools."""
        issues: list[Issue] = []

        # Double spaces
        if "  " in text:
            issues.append(
                Issue(
                    category="content",
                    severity="info",
                    message="Double space detected.",
                    location=location,
                    suggestion="Replace consecutive spaces with a single space.",
                    context=text[:120],
                )
            )

        # Trailing whitespace on non-empty lines
        if text != text.rstrip():
            issues.append(
                Issue(
                    category="content",
                    severity="info",
                    message="Trailing whitespace at end of paragraph.",
                    location=location,
                    suggestion="Remove trailing whitespace.",
                    context=text[:120],
                )
            )

        # Repeated punctuation (e.g. "!!" or "...")
        if re.search(r"[!?]{2,}", text):
            issues.append(
                Issue(
                    category="content",
                    severity="info",
                    message="Repeated exclamation or question marks.",
                    location=location,
                    suggestion="Use a single punctuation mark.",
                    context=text[:120],
                )
            )

        return issues
