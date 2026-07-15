"""Format Checker Skill – validate paragraph formatting and document structure."""

from __future__ import annotations

from typing import Any

from docx_agent.config import HEADING_FONT_SIZES
from docx_agent.skills.base_skill import BaseSkill, Issue, SkillResult


class FormatCheckerSkill(BaseSkill):
    """Check paragraph alignment, spacing, indentation, and heading hierarchy."""

    name = "format_checker"

    def execute(self, document_data: dict[str, Any]) -> SkillResult:  # type: ignore[override]
        """Validate formatting of all paragraphs and tables.

        Parameters
        ----------
        document_data:
            The ``"document"`` dict produced by :class:`DocxReaderSkill`.

        Returns
        -------
        SkillResult
        """
        self._logger.info("Running format checks…")
        issues: list[Issue] = []

        paragraphs: list[dict[str, Any]] = document_data.get("paragraphs", [])
        tables: list[dict[str, Any]] = document_data.get("tables", [])

        issues.extend(self._check_headings(paragraphs))
        issues.extend(self._check_alignment(paragraphs))
        issues.extend(self._check_spacing(paragraphs))
        issues.extend(self._check_indentation(paragraphs))
        issues.extend(self._check_tables(tables))

        metadata = {
            "paragraphs_checked": len(paragraphs),
            "tables_checked": len(tables),
        }

        self._logger.info("Format check complete – %d issues found.", len(issues))
        return SkillResult(
            skill_name=self.name,
            success=True,
            issues=issues,
            metadata=metadata,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _check_headings(self, paragraphs: list[dict[str, Any]]) -> list[Issue]:
        """Validate heading hierarchy and font sizes."""
        issues: list[Issue] = []
        last_heading_level: int = 0

        for para in paragraphs:
            style: str = para.get("style", "Normal")
            location = f"Paragraph {para['index'] + 1}"

            if not style.startswith("Heading"):
                continue

            # Parse heading level (e.g. "Heading 1" → 1)
            parts = style.split()
            try:
                level = int(parts[-1])
            except (ValueError, IndexError):
                continue

            # Heading hierarchy must not skip levels
            if level > last_heading_level + 1 and last_heading_level != 0:
                issues.append(
                    Issue(
                        category="format",
                        severity="warning",
                        message=(
                            f"Heading level jumps from {last_heading_level} to {level}. "
                            "Heading levels should not be skipped."
                        ),
                        location=location,
                        suggestion=f"Ensure a Heading {last_heading_level + 1} precedes this.",
                        context=para.get("text", "")[:80],
                    )
                )

            last_heading_level = level

            # Check expected font size for heading level
            expected_size = HEADING_FONT_SIZES.get(level)
            if expected_size is None:
                continue

            for run in para.get("runs", []):
                size_pt: float | None = run.get("font_size_pt")
                if size_pt is not None and abs(size_pt - expected_size) > 1.0:
                    issues.append(
                        Issue(
                            category="format",
                            severity="info",
                            message=(
                                f"Heading {level} font size is {size_pt:.1f}pt; "
                                f"expected ~{expected_size:.1f}pt."
                            ),
                            location=location,
                            suggestion=f"Set font size to {expected_size:.1f}pt for Heading {level}.",
                            context=run.get("text", "")[:80],
                        )
                    )

        return issues

    def _check_alignment(self, paragraphs: list[dict[str, Any]]) -> list[Issue]:
        """Detect inconsistent paragraph alignment."""
        issues: list[Issue] = []
        alignment_counts: dict[str, int] = {}

        for para in paragraphs:
            align = para.get("alignment", "inherited")
            if align and align != "inherited":
                alignment_counts[align] = alignment_counts.get(align, 0) + 1

        dominant = (
            max(alignment_counts, key=lambda k: alignment_counts[k])
            if alignment_counts
            else None
        )

        if dominant and len(alignment_counts) > 2:
            minority = sorted(
                (a for a in alignment_counts if a != dominant),
                key=lambda a: alignment_counts[a],
            )
            for align in minority:
                paras_with_align = [
                    p
                    for p in paragraphs
                    if p.get("alignment") == align and p.get("text", "").strip()
                ]
                for para in paras_with_align:
                    issues.append(
                        Issue(
                            category="format",
                            severity="info",
                            message=(
                                f"Paragraph has '{align}' alignment, while most "
                                f"paragraphs use '{dominant}'."
                            ),
                            location=f"Paragraph {para['index'] + 1}",
                            suggestion=f"Consider changing alignment to '{dominant}' for consistency.",
                            context=para.get("text", "")[:80],
                        )
                    )

        return issues

    def _check_spacing(self, paragraphs: list[dict[str, Any]]) -> list[Issue]:
        """Flag unusually large spacing values."""
        issues: list[Issue] = []
        MAX_SPACE_PT = 72.0

        for para in paragraphs:
            location = f"Paragraph {para['index'] + 1}"
            text = para.get("text", "").strip()
            if not text:
                continue

            space_before = para.get("space_before_pt")
            space_after = para.get("space_after_pt")

            if space_before is not None and space_before > MAX_SPACE_PT:
                issues.append(
                    Issue(
                        category="format",
                        severity="warning",
                        message=f"Unusually large space-before: {space_before:.1f}pt.",
                        location=location,
                        suggestion=f"Reduce to ≤ {MAX_SPACE_PT:.0f}pt.",
                        context=text[:80],
                    )
                )

            if space_after is not None and space_after > MAX_SPACE_PT:
                issues.append(
                    Issue(
                        category="format",
                        severity="warning",
                        message=f"Unusually large space-after: {space_after:.1f}pt.",
                        location=location,
                        suggestion=f"Reduce to ≤ {MAX_SPACE_PT:.0f}pt.",
                        context=text[:80],
                    )
                )

        return issues

    def _check_indentation(self, paragraphs: list[dict[str, Any]]) -> list[Issue]:
        """Detect inconsistent first-line indentation."""
        issues: list[Issue] = []
        indent_values: list[float] = []

        for para in paragraphs:
            indent = para.get("first_line_indent_pt")
            if indent is not None and indent > 0:
                indent_values.append(indent)

        if not indent_values:
            return issues

        # Find the most common indentation
        from statistics import mode as stat_mode

        try:
            dominant_indent = stat_mode(
                [round(v, 0) for v in indent_values]
            )
        except Exception:  # noqa: BLE001
            return issues

        for para in paragraphs:
            indent = para.get("first_line_indent_pt")
            if indent is None or indent <= 0:
                continue
            if abs(indent - dominant_indent) > 2.0:
                issues.append(
                    Issue(
                        category="format",
                        severity="info",
                        message=(
                            f"First-line indentation {indent:.1f}pt differs from "
                            f"dominant value {dominant_indent:.1f}pt."
                        ),
                        location=f"Paragraph {para['index'] + 1}",
                        suggestion=f"Change first-line indent to {dominant_indent:.1f}pt for consistency.",
                        context=para.get("text", "")[:80],
                    )
                )

        return issues

    def _check_tables(self, tables: list[dict[str, Any]]) -> list[Issue]:
        """Validate basic table structure."""
        issues: list[Issue] = []

        for table in tables:
            location = f"Table {table['index'] + 1}"

            if table.get("row_count", 0) == 0:
                issues.append(
                    Issue(
                        category="format",
                        severity="error",
                        message="Table has no rows.",
                        location=location,
                    )
                )
                continue

            # Check row width consistency
            col_counts = [len(row) for row in table.get("rows", [])]
            if len(set(col_counts)) > 1:
                issues.append(
                    Issue(
                        category="format",
                        severity="warning",
                        message=(
                            f"Table has inconsistent column counts across rows: "
                            f"{sorted(set(col_counts))}."
                        ),
                        location=location,
                        suggestion="Ensure all rows have the same number of columns.",
                    )
                )

        return issues
