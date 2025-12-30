"""
Graceful shutdown module for NautilusTrader TradingNode.

Provides GracefulShutdownHandler for orderly shutdown on SIGTERM/SIGINT.
"""

from config.shutdown.shutdown_config import (
    ShutdownConfig,
    ShutdownConfigError,
    ShutdownReason,
)
from config.shutdown.shutdown_handler import GracefulShutdownHandler

__all__ = [
    "GracefulShutdownHandler",
    "ShutdownConfig",
    "ShutdownConfigError",
    "ShutdownReason",
]
