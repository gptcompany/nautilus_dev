"""Logging configuration for CCXT pipeline."""

import logging
import os
import sys


def setup_logging(level: str | None = None) -> logging.Logger:
    """Configure logging for the CCXT pipeline.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR). Defaults to CCXT_LOG_LEVEL env var or INFO.

    Returns:
        Configured logger instance.
    """
    log_level = level or os.getenv("CCXT_LOG_LEVEL", "INFO")
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    logger = logging.getLogger("ccxt_pipeline")
    logger.setLevel(numeric_level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(numeric_level)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Get a logger for a specific module.

    Args:
        name: Module name (appended to ccxt_pipeline).

    Returns:
        Logger instance.
    """
    if name:
        return logging.getLogger(f"ccxt_pipeline.{name}")
    return logging.getLogger("ccxt_pipeline")
