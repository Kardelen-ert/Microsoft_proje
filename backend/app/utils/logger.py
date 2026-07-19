"""Logging helpers."""

from __future__ import annotations

import logging

from app.core.config import get_settings


def configure_logging() -> None:
    """Configure console and file logging once at application startup."""

    settings = get_settings()
    settings.logs_dir.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(settings.log_file, encoding="utf-8"),
        ],
    )


def get_logger(name: str) -> logging.Logger:
    """Return a named logger."""

    return logging.getLogger(name)
