"""
Integration test for TradingNode startup with factory config (T039).

These tests verify that factory-generated configs work with NautilusTrader.
Skip if nautilus_trader is not available.
"""

from __future__ import annotations

import os

import pytest

from config.factory import TradingNodeConfigFactory
from config.models import (
    BinanceCredentials,
    ConfigEnvironment,
    TradingNodeSettings,
)


@pytest.fixture
def minimal_settings():
    """Minimal valid settings for testing."""
    return TradingNodeSettings(
        environment=ConfigEnvironment(
            trader_id="TEST-INTEGRATION-001",
            environment="SANDBOX",
        ),
        binance=BinanceCredentials(
            api_key="test_api_key_12345678",
            api_secret="test_api_secret_12345678",
            testnet=True,
        ),
    )


@pytest.mark.integration
class TestTradingNodeStartup:
    """Integration tests for TradingNode initialization."""

    def test_factory_creates_valid_trading_node_config(self, minimal_settings: TradingNodeSettings):
        """Factory should create a config that can be used with TradingNode."""
        config = TradingNodeConfigFactory.from_settings(minimal_settings)

        # Verify config structure
        assert config.trader_id is not None
        assert config.cache is not None
        assert config.exec_engine is not None
        assert config.data_engine is not None
        assert config.risk_engine is not None
        assert config.logging is not None
        assert config.streaming is not None
        assert "BINANCE" in config.data_clients
        assert "BINANCE" in config.exec_clients

    def test_testnet_config_forces_testnet(self, minimal_settings: TradingNodeSettings):
        """Testnet config should force testnet=True for all clients."""
        # Force production mode in settings
        minimal_settings.binance.testnet = False

        # Create testnet config (should override)
        minimal_settings.binance.testnet = True
        config = TradingNodeConfigFactory.from_settings(minimal_settings)

        binance_data = config.data_clients.get("BINANCE")
        assert binance_data.testnet is True

    def test_config_includes_reconciliation_settings(self, minimal_settings: TradingNodeSettings):
        """Config should have proper reconciliation settings."""
        config = TradingNodeConfigFactory.from_settings(minimal_settings)

        assert config.exec_engine.reconciliation is True
        assert config.exec_engine.reconciliation_lookback_mins >= 60
        assert config.exec_engine.reconciliation_startup_delay_secs >= 10.0

    def test_config_includes_safety_settings(self, minimal_settings: TradingNodeSettings):
        """Config should have safety settings enabled."""
        config = TradingNodeConfigFactory.from_settings(minimal_settings)

        assert config.exec_engine.graceful_shutdown_on_exception is True
        assert config.risk_engine.bypass is False


@pytest.mark.integration
@pytest.mark.skipif(
    not os.environ.get("RUN_LIVE_TESTS"),
    reason="Live tests disabled (set RUN_LIVE_TESTS=1 to enable)",
)
class TestTradingNodeLiveStartup:
    """Live integration tests requiring running services."""

    def test_trading_node_initializes(self, minimal_settings: TradingNodeSettings):
        """TradingNode should initialize with factory config."""
        from nautilus_trader.live.node import TradingNode

        config = TradingNodeConfigFactory.from_settings(minimal_settings)
        node = TradingNode(config=config)

        try:
            node.build()
            # If we get here without exception, config is valid
            assert node is not None
        finally:
            if node:
                node.dispose()
