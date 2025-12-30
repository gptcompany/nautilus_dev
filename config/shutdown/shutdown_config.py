"""
Shutdown configuration for graceful TradingNode shutdown.

This module provides configuration dataclasses for the graceful shutdown handler.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ShutdownReason(Enum):
    """Reason for shutdown."""

    SIGNAL_SIGTERM = "SIGTERM"
    SIGNAL_SIGINT = "SIGINT"
    EXCEPTION = "exception"
    MANUAL = "manual"
    TIMEOUT = "timeout"


class ShutdownConfigError(Exception):
    """Raised when shutdown configuration is invalid."""

    pass


@dataclass
class ShutdownConfig:
    """Configuration for graceful shutdown.

    Attributes:
        timeout_secs: Maximum time for shutdown sequence (5-300s)
        cancel_orders: Cancel all pending orders on shutdown
        verify_stop_losses: Check positions have stop-losses
        flush_cache: Ensure cache persisted (handled by NautilusTrader)
        log_level: Logging verbosity during shutdown
    """

    timeout_secs: float = 30.0
    cancel_orders: bool = True
    verify_stop_losses: bool = True
    flush_cache: bool = True
    log_level: str = "INFO"

    def __post_init__(self) -> None:
        """Validate configuration."""
        # Validate timeout range
        if not isinstance(self.timeout_secs, (int, float)):
            raise ShutdownConfigError(
                f"timeout_secs must be a number, got: {type(self.timeout_secs).__name__}"
            )
        if not 5.0 <= self.timeout_secs <= 300.0:
            raise ShutdownConfigError(
                f"timeout_secs must be between 5 and 300, got: {self.timeout_secs}"
            )

        # Validate log_level
        valid_levels = ("DEBUG", "INFO", "WARNING", "ERROR")
        if self.log_level not in valid_levels:
            raise ShutdownConfigError(
                f"log_level must be one of {valid_levels}, got: {self.log_level!r}"
            )

        # Validate boolean fields
        if not isinstance(self.cancel_orders, bool):
            raise ShutdownConfigError(
                f"cancel_orders must be a boolean, got: {type(self.cancel_orders).__name__}"
            )
        if not isinstance(self.verify_stop_losses, bool):
            raise ShutdownConfigError(
                f"verify_stop_losses must be a boolean, got: {type(self.verify_stop_losses).__name__}"
            )
        if not isinstance(self.flush_cache, bool):
            raise ShutdownConfigError(
                f"flush_cache must be a boolean, got: {type(self.flush_cache).__name__}"
            )
