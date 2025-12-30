"""
API Contract: GracefulShutdownHandler

This defines the public interface for graceful shutdown.
Implementation will be in config/shutdown/shutdown_handler.py
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    pass


class ShutdownReason(Enum):
    """Reason for shutdown."""

    SIGNAL_SIGTERM = "SIGTERM"
    SIGNAL_SIGINT = "SIGINT"
    EXCEPTION = "exception"
    MANUAL = "manual"
    TIMEOUT = "timeout"


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
        if not 5.0 <= self.timeout_secs <= 300.0:
            raise ValueError("timeout_secs must be between 5 and 300")
        if self.log_level not in ("DEBUG", "INFO", "WARNING", "ERROR"):
            raise ValueError(f"Invalid log_level: {self.log_level}")


class ShutdownHandlerProtocol(Protocol):
    """Protocol for shutdown handler implementations."""

    def setup_signal_handlers(self) -> None:
        """Register signal handlers for SIGTERM/SIGINT."""
        ...

    async def shutdown(self, reason: str = "signal") -> None:
        """Execute graceful shutdown sequence.

        Sequence:
        1. Halt trading (TradingState.HALTED)
        2. Cancel all pending orders
        3. Verify stop-losses for open positions
        4. Flush cache (native NautilusTrader behavior)
        5. Close exchange connections
        6. Exit

        Args:
            reason: Why shutdown was triggered (for logging)
        """
        ...

    def is_shutdown_requested(self) -> bool:
        """Check if shutdown has been requested."""
        ...


# Type alias for implementation
GracefulShutdownHandler = ShutdownHandlerProtocol
