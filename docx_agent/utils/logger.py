"""Centralised logging configuration for the docx_agent package."""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

from docx_agent.config import LOG_DATE_FORMAT, LOG_DIR, LOG_FORMAT, LOG_LEVEL


def get_logger(name: str) -> logging.Logger:
    """Return a named logger that writes to both the console and a rotating file.

    Parameters
    ----------
    name:
        Typically ``__name__`` from the calling module.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers when the function is called multiple times
    if logger.handlers:
        return logger

    logger.setLevel(LOG_LEVEL)

    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Rotating file handler (10 MB per file, keep 5 backups)
    log_file: Path = LOG_DIR / "docx_agent.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
