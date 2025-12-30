"""
Reconciliation Configuration for NautilusTrader.

This module provides a Pydantic configuration model that wraps NautilusTrader's
native reconciliation parameters with sensible defaults and validation.
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field, model_validator


logger = logging.getLogger(__name__)


class ReconciliationConfig(BaseModel):
    """
    Configuration for NautilusTrader order reconciliation.

    This model provides validated configuration for:
    - Startup reconciliation (sync state on TradingNode start)
    - In-flight order monitoring (track pending order confirmations)
    - Continuous polling (periodic exchange state checks)
    - Memory management (purge closed orders from cache)

    All defaults follow NautilusTrader community best practices from Discord.
    """

    # Startup reconciliation
    enabled: bool = Field(
        default=True,
        description="Enable startup reconciliation",
    )
    startup_delay_secs: float = Field(
        default=10.0,
        ge=10.0,
        description="Delay before reconciliation starts (minimum 10s for account connections)",
    )
    lookback_mins: int | None = Field(
        default=None,
        ge=0,
        description="History lookback in minutes (None = maximum available)",
    )

    # In-flight order monitoring
    inflight_check_interval_ms: int = Field(
        default=2000,
        ge=1000,
        description="Interval for checking in-flight orders (milliseconds)",
    )
    inflight_check_threshold_ms: int = Field(
        default=5000,
        ge=1000,
        description="Threshold before querying venue for in-flight orders (milliseconds)",
    )
    inflight_check_retries: int = Field(
        default=5,
        ge=1,
        description="Maximum retry attempts for in-flight order resolution",
    )

    # Continuous polling
    open_check_interval_secs: float | None = Field(
        default=5.0,
        ge=1.0,
        description="Interval for continuous open order polling (seconds, None = disabled)",
    )
    open_check_lookback_mins: int = Field(
        default=60,
        ge=60,
        description="Lookback window for open order checks (minimum 60 minutes)",
    )
    open_check_threshold_ms: int = Field(
        default=5000,
        ge=1000,
        description="Threshold before acting on discrepancies (milliseconds)",
    )

    # Memory management
    purge_closed_orders_interval_mins: int = Field(
        default=10,
        ge=1,
        description="Interval for purging closed orders from memory (minutes)",
    )
    purge_closed_orders_buffer_mins: int = Field(
        default=60,
        ge=1,
        description="Grace period before purging closed orders (minutes)",
    )

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def validate_inflight_threshold_exceeds_interval(self) -> ReconciliationConfig:
        """Ensure in-flight threshold >= interval (threshold must allow at least one check)."""
        if self.inflight_check_threshold_ms < self.inflight_check_interval_ms:
            msg = (
                f"inflight_check_threshold_ms ({self.inflight_check_threshold_ms}) must be >= "
                f"inflight_check_interval_ms ({self.inflight_check_interval_ms})"
            )
            raise ValueError(msg)
        return self

    def to_live_exec_engine_config(self) -> dict[str, Any]:
        """
        Convert to kwargs for LiveExecEngineConfig.

        Returns:
            Dictionary of parameters for NautilusTrader's LiveExecEngineConfig.

        Example:
            >>> config = ReconciliationConfig()
            >>> exec_config = LiveExecEngineConfig(**config.to_live_exec_engine_config())
        """
        return {
            "reconciliation": self.enabled,
            "reconciliation_startup_delay_secs": self.startup_delay_secs,
            "reconciliation_lookback_mins": self.lookback_mins,
            "inflight_check_interval_ms": self.inflight_check_interval_ms,
            "inflight_check_threshold_ms": self.inflight_check_threshold_ms,
            "inflight_check_retries": self.inflight_check_retries,
            "open_check_interval_secs": self.open_check_interval_secs,
            "open_check_lookback_mins": self.open_check_lookback_mins,
            "open_check_threshold_ms": self.open_check_threshold_ms,
            "purge_closed_orders_interval_mins": self.purge_closed_orders_interval_mins,
            "purge_closed_orders_buffer_mins": self.purge_closed_orders_buffer_mins,
        }

    def log_configuration(self) -> None:
        """Log the current reconciliation configuration."""
        logger.info("Reconciliation Configuration:")
        logger.info("  Enabled: %s", self.enabled)
        logger.info("  Startup delay: %.1fs", self.startup_delay_secs)
        logger.info("  Lookback: %s mins", self.lookback_mins or "unlimited")
        logger.info(
            "  In-flight check: every %dms, threshold %dms, %d retries",
            self.inflight_check_interval_ms,
            self.inflight_check_threshold_ms,
            self.inflight_check_retries,
        )
        logger.info(
            "  Open check: every %.1fs, lookback %d mins",
            self.open_check_interval_secs or 0,
            self.open_check_lookback_mins,
        )
        logger.info(
            "  Purge: every %d mins, buffer %d mins",
            self.purge_closed_orders_interval_mins,
            self.purge_closed_orders_buffer_mins,
        )
