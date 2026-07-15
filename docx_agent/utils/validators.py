"""Input validation helpers used across the docx_agent package."""

from __future__ import annotations

from pathlib import Path


class ValidationError(Exception):
    """Raised when a validation check fails."""


def validate_docx_path(path: str | Path) -> Path:
    """Validate that *path* points to a readable .docx file.

    Parameters
    ----------
    path:
        File-system path to validate.

    Returns
    -------
    Path
        Resolved :class:`pathlib.Path` object.

    Raises
    ------
    ValidationError
        If the path does not exist, is not a file, or does not have a
        ``.docx`` extension.
    """
    resolved = Path(path).resolve()

    if not resolved.exists():
        raise ValidationError(f"File not found: {resolved}")

    if not resolved.is_file():
        raise ValidationError(f"Path is not a file: {resolved}")

    if resolved.suffix.lower() != ".docx":
        raise ValidationError(
            f"Expected a .docx file, got '{resolved.suffix}': {resolved}"
        )

    return resolved


def validate_output_dir(path: str | Path) -> Path:
    """Ensure *path* is a writable directory, creating it if necessary.

    Parameters
    ----------
    path:
        Target directory path.

    Returns
    -------
    Path
        Resolved :class:`pathlib.Path` object.

    Raises
    ------
    ValidationError
        If the path exists but is not a directory, or cannot be created.
    """
    resolved = Path(path).resolve()

    if resolved.exists() and not resolved.is_dir():
        raise ValidationError(f"Path exists but is not a directory: {resolved}")

    try:
        resolved.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ValidationError(f"Cannot create output directory: {resolved}") from exc

    return resolved


def validate_severity(severity: str) -> str:
    """Validate that *severity* is one of the accepted string values.

    Parameters
    ----------
    severity:
        Severity string to validate.

    Returns
    -------
    str
        The validated severity string (lower-cased).

    Raises
    ------
    ValidationError
        If *severity* is not one of ``'error'``, ``'warning'``, or ``'info'``.
    """
    allowed = {"error", "warning", "info"}
    lower = severity.lower()
    if lower not in allowed:
        raise ValidationError(
            f"Invalid severity '{severity}'. Must be one of: {', '.join(sorted(allowed))}"
        )
    return lower
