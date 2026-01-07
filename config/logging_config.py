"""
LoggingConfig builder (T042).

Builds NautilusTrader LoggingConfig.
"""

from __future__ import annotations

from nautilus_trader.config import LoggingConfig

from config.models import LoggingSettings


def build_logging_config(
    settings: LoggingSettings,
) -> LoggingConfig:
    """
    Build LoggingConfig from settings.

    Parameters
    ----------
    settings : LoggingSettings
        Logging configuration settings.

    Returns
    -------
    LoggingConfig
        NautilusTrader logging configuration.

    Notes
    -----
    Production settings:
    - JSON format for log aggregation (Grafana Loki, ELK)
    - DEBUG level for file, INFO for console
    - 100MB file rotation with 10 backups
    """
    return LoggingConfig(
        log_level=settings.log_level,
        log_level_file=settings.log_level_file,
        log_directory=settings.log_directory,
        log_file_format=(settings.log_format if settings.log_format != "text" else None),
        log_file_max_size=settings.max_size_mb * 1024 * 1024,
        log_file_max_backup_count=settings.max_backup_count,
        log_colors=True,
    )
