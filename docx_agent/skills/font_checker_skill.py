"""Font Checker Skill – validate font consistency across a DOCX document."""

from __future__ import annotations

from typing import Any

from docx_agent.config import (
    ALLOWED_FONT_FAMILIES,
    FONT_SIZE_MAX_PT,
    FONT_SIZE_MIN_PT,
)
from docx_agent.skills.base_skill import BaseSkill, Issue, SkillResult


class FontCheckerSkill(BaseSkill):
    """Validate font families, sizes, and colours in a parsed document."""

    name = "font_checker"

    def __init__(
        self,
        allowed_families: list[str] | None = None,
        size_min_pt: float = FONT_SIZE_MIN_PT,
        size_max_pt: float = FONT_SIZE_MAX_PT,
    ) -> None:
        super().__init__()
        self._allowed_families: list[str] = (
            allowed_families if allowed_families is not None else ALLOWED_FONT_FAMILIES
        )
        self._size_min = size_min_pt
        self._size_max = size_max_pt

    def execute(self, document_data: dict[str, Any]) -> SkillResult:  # type: ignore[override]
        """Check all runs in *document_data* for font violations.

        Parameters
        ----------
        document_data:
            The ``"document"`` dict produced by :class:`DocxReaderSkill`.

        Returns
        -------
        SkillResult
        """
        self._logger.info("Running font checks…")
        issues: list[Issue] = []

        paragraphs: list[dict[str, Any]] = document_data.get("paragraphs", [])

        # Collect all font families used so we can detect inconsistency
        font_family_usage: dict[str, int] = {}

        for para in paragraphs:
            para_location = f"Paragraph {para['index'] + 1}"
            for run in para.get("runs", []):
                if not run.get("text", "").strip():
                    continue

                run_location = f"{para_location}, run '{run['text'][:30]}'"

                # --- Font family ---
                font_name: str | None = run.get("font_name")
                if font_name:
                    font_family_usage[font_name] = (
                        font_family_usage.get(font_name, 0) + 1
                    )
                    if (
                        self._allowed_families
                        and font_name not in self._allowed_families
                    ):
                        issues.append(
                            Issue(
                                category="font",
                                severity="warning",
                                message=(
                                    f"Non-standard font family '{font_name}'. "
                                    f"Allowed: {', '.join(self._allowed_families)}"
                                ),
                                location=run_location,
                                suggestion=f"Change to one of: {', '.join(self._allowed_families[:3])}",
                                context=run.get("text", "")[:80],
                            )
                        )

                # --- Font size ---
                size_pt: float | None = run.get("font_size_pt")
                if size_pt is not None:
                    if size_pt < self._size_min:
                        issues.append(
                            Issue(
                                category="font",
                                severity="error",
                                message=(
                                    f"Font size {size_pt:.1f}pt is below minimum "
                                    f"{self._size_min:.1f}pt."
                                ),
                                location=run_location,
                                suggestion=f"Increase to at least {self._size_min:.1f}pt.",
                                context=run.get("text", "")[:80],
                            )
                        )
                    elif size_pt > self._size_max:
                        issues.append(
                            Issue(
                                category="font",
                                severity="warning",
                                message=(
                                    f"Font size {size_pt:.1f}pt exceeds maximum "
                                    f"{self._size_max:.1f}pt."
                                ),
                                location=run_location,
                                suggestion=f"Reduce to at most {self._size_max:.1f}pt.",
                                context=run.get("text", "")[:80],
                            )
                        )

        # Warn if more than 3 distinct font families are used
        if len(font_family_usage) > 3:
            issues.append(
                Issue(
                    category="font",
                    severity="warning",
                    message=(
                        f"Document uses {len(font_family_usage)} different font "
                        "families, which may look inconsistent."
                    ),
                    location="Document-wide",
                    suggestion="Limit to 1–2 font families for a professional look.",
                    context=", ".join(sorted(font_family_usage.keys())),
                )
            )

        metadata = {
            "font_families_found": font_family_usage,
            "runs_checked": sum(len(p.get("runs", [])) for p in paragraphs),
        }

        self._logger.info("Font check complete – %d issues found.", len(issues))
        return SkillResult(
            skill_name=self.name,
            success=True,
            issues=issues,
            metadata=metadata,
        )
