"""
Configuration settings for the DOCX proofreading agent.
All tuneable values live here so the rest of the code stays clean.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR: Path = Path(__file__).parent
SAMPLE_DOCX_DIR: Path = BASE_DIR / "sample_docx"
REPORT_OUTPUT_DIR: Path = BASE_DIR / "reports"
LOG_DIR: Path = BASE_DIR / "logs"

# Create output directories if they do not exist yet
REPORT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# LLM / OpenAI settings
# ---------------------------------------------------------------------------
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0"))
OPENAI_MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", "2048"))

# ---------------------------------------------------------------------------
# Font validation rules
# ---------------------------------------------------------------------------
ALLOWED_FONT_FAMILIES: list[str] = [
    "Times New Roman",
    "Arial",
    "Calibri",
    "Cambria",
    "微軟正黑體",
    "新細明體",
]

FONT_SIZE_MIN_PT: float = 8.0
FONT_SIZE_MAX_PT: float = 72.0

HEADING_FONT_SIZES: dict[int, float] = {
    1: 16.0,
    2: 14.0,
    3: 12.0,
}

# ---------------------------------------------------------------------------
# Spell / grammar checking
# ---------------------------------------------------------------------------
SPELL_CHECK_LANGUAGES: list[str] = ["en", "zh"]
GRAMMAR_CHECK_LANGUAGE: str = "en-US"

# ---------------------------------------------------------------------------
# Severity levels
# ---------------------------------------------------------------------------
SEVERITY_ERROR: str = "error"
SEVERITY_WARNING: str = "warning"
SEVERITY_INFO: str = "info"

SEVERITY_COLORS: dict[str, str] = {
    SEVERITY_ERROR: "#dc3545",
    SEVERITY_WARNING: "#ffc107",
    SEVERITY_INFO: "#17a2b8",
}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT: str = "%(asctime)s [%(levelname)s] %(name)s – %(message)s"
LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
