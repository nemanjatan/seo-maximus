"""Logging configuration utilities."""

import logging
import sys
from typing import Optional

import structlog

from .config import settings


def configure_logging(level: int | str | None = None) -> None:
    """Configure application logging."""

    log_level = level or (logging.DEBUG if settings.debug else logging.INFO)

    timestamper = structlog.processors.TimeStamper(fmt="iso")

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            timestamper,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        stream=sys.stdout,
    )


def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """Create a structured logger."""

    return structlog.get_logger(name or "seo_maximus")

