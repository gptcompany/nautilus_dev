"""
Live Trading Node Configuration Builder.

This module provides a configuration builder for NautilusTrader's TradingNode
with production-ready defaults for reconciliation and caching.
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

from config.reconciliation.config import ReconciliationConfig
from config.reconciliation.presets import ReconciliationPreset

logger = logging.getLogger(__name__)


class LiveTradingNodeConfig(BaseModel):
    """
    Builder for live TradingNode configuration.

    This builder creates validated configurations for NautilusTrader's TradingNode
    with reconciliation and Redis caching enabled by default.

    Example:
        >>> config = LiveTradingNodeConfig(trader_id="TRADER-001")
        >>> exec_config = config.build_exec_engine_config()
        >>> cache_config = config.build_cache_config()
    """

    # Identification
    trader_id: str = Field(
        description="Unique trader identifier (e.g., 'TRADER-001')",
    )

    # Reconciliation
    reconciliation: ReconciliationConfig | ReconciliationPreset = Field(
        default_factory=lambda: ReconciliationPreset.STANDARD,
        description="Reconciliation configuration or preset",
    )

    # Cache settings
    redis_host: str = Field(
        default="localhost",
        description="Redis server hostname",
    )
    redis_port: int = Field(
        default=6379,
        ge=1,
        le=65535,
        description="Redis server port",
    )
    persist_account_events: bool = Field(
        default=True,
        description="Persist account events for recovery (CRITICAL for production)",
    )

    # Safety settings
    graceful_shutdown_on_exception: bool = Field(
        default=True,
        description="Gracefully shutdown on unhandled exceptions",
    )

    model_config = {"frozen": True}

    def _get_reconciliation_config(self) -> ReconciliationConfig:
        """Get ReconciliationConfig from preset or direct config."""
        if isinstance(self.reconciliation, ReconciliationPreset):
            return self.reconciliation.to_config()
        return self.reconciliation

    def build_exec_engine_config(self) -> dict[str, Any]:
        """
        Build execution engine configuration dictionary.

        Returns:
            Dictionary of parameters for LiveExecEngineConfig.

        Example:
            >>> from nautilus_trader.config import LiveExecEngineConfig
            >>> config = LiveTradingNodeConfig(trader_id="TRADER-001")
            >>> exec_kwargs = config.build_exec_engine_config()
            >>> exec_config = LiveExecEngineConfig(**exec_kwargs)
        """
        recon_config = self._get_reconciliation_config()
        exec_config = recon_config.to_live_exec_engine_config()

        # Add safety settings
        exec_config["graceful_shutdown_on_exception"] = self.graceful_shutdown_on_exception

        self._log_exec_config(exec_config)
        return exec_config

    def build_cache_config(self) -> dict[str, Any]:
        """
        Build cache configuration dictionary.

        Returns:
            Dictionary of parameters for CacheConfig.

        Example:
            >>> from nautilus_trader.config import CacheConfig, DatabaseConfig
            >>> config = LiveTradingNodeConfig(trader_id="TRADER-001")
            >>> cache_kwargs = config.build_cache_config()
            >>> # Use with CacheConfig(database=DatabaseConfig(**), **rest)
        """
        cache_config = {
            "database": {
                "type": "redis",
                "host": self.redis_host,
                "port": self.redis_port,
            },
            "persist_account_events": self.persist_account_events,
        }

        self._log_cache_config(cache_config)
        return cache_config

    def build_trading_node_config(self) -> dict[str, Any]:
        """
        Build complete TradingNode configuration dictionary.

        Returns:
            Dictionary with all TradingNode configuration sections.

        Example:
            >>> config = LiveTradingNodeConfig(trader_id="TRADER-001")
            >>> node_config = config.build_trading_node_config()
            >>> # Use sections: node_config["exec_engine"], node_config["cache"]
        """
        return {
            "trader_id": self.trader_id,
            "exec_engine": self.build_exec_engine_config(),
            "cache": self.build_cache_config(),
        }

    def _log_exec_config(self, config: dict[str, Any]) -> None:
        """Log execution engine configuration."""
        logger.info("Execution Engine Configuration for %s:", self.trader_id)
        logger.info("  Reconciliation enabled: %s", config.get("reconciliation"))
        logger.info(
            "  Startup delay: %.1fs",
            config.get("reconciliation_startup_delay_secs", 0),
        )
        logger.info(
            "  Lookback: %s mins",
            config.get("reconciliation_lookback_mins") or "unlimited",
        )
        logger.info(
            "  In-flight check: every %dms, threshold %dms",
            config.get("inflight_check_interval_ms", 0),
            config.get("inflight_check_threshold_ms", 0),
        )
        logger.info(
            "  Open check: every %.1fs, lookback %d mins",
            config.get("open_check_interval_secs") or 0,
            config.get("open_check_lookback_mins", 0),
        )
        logger.info(
            "  Graceful shutdown: %s",
            config.get("graceful_shutdown_on_exception"),
        )

    def _log_cache_config(self, config: dict[str, Any]) -> None:
        """Log cache configuration."""
        db = config.get("database", {})
        logger.info("Cache Configuration for %s:", self.trader_id)
        logger.info("  Redis: %s:%d", db.get("host"), db.get("port"))
        logger.info(
            "  Persist account events: %s",
            config.get("persist_account_events"),
        )

    def log_all(self) -> None:
        """Log all configuration settings."""
        logger.info("=" * 60)
        logger.info("TradingNode Configuration: %s", self.trader_id)
        logger.info("=" * 60)
        self.build_exec_engine_config()
        self.build_cache_config()
        logger.info("=" * 60)
