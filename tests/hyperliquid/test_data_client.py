"""Unit tests for Hyperliquid data client configuration (Spec 021).

Tests the factory functions for creating HyperliquidDataClientConfig.
"""

import pytest

# Skip entire module if Hyperliquid adapter not available
pytest.importorskip("nautilus_trader.adapters.hyperliquid")

from nautilus_trader.adapters.hyperliquid import HYPERLIQUID
from nautilus_trader.adapters.hyperliquid import HyperliquidDataClientConfig
from nautilus_trader.config import TradingNodeConfig

from configs.hyperliquid.data_client import (
    create_hyperliquid_data_client,
    create_data_only_trading_node,
    DEFAULT_INSTRUMENTS,
)


class TestCreateHyperliquidDataClient:
    """Tests for create_hyperliquid_data_client factory."""

    def test_default_config_returns_dict_with_hyperliquid_key(self):
        """Factory returns dict with HYPERLIQUID key."""
        result = create_hyperliquid_data_client()

        assert isinstance(result, dict)
        assert HYPERLIQUID in result
        assert isinstance(result[HYPERLIQUID], HyperliquidDataClientConfig)

    def test_default_config_uses_mainnet(self):
        """Default configuration uses mainnet (testnet=False)."""
        result = create_hyperliquid_data_client()

        assert result[HYPERLIQUID].testnet is False

    def test_testnet_config(self):
        """Testnet parameter is correctly passed."""
        result = create_hyperliquid_data_client(testnet=True)

        assert result[HYPERLIQUID].testnet is True

    def test_default_instruments_loaded(self):
        """Default instruments are BTC and ETH perpetuals."""
        result = create_hyperliquid_data_client()

        config = result[HYPERLIQUID]
        assert config.instrument_provider.load_all is False
        assert config.instrument_provider.load_ids == DEFAULT_INSTRUMENTS

    def test_custom_instruments(self):
        """Custom instruments override defaults."""
        custom_instruments = ["SOL-USD-PERP.HYPERLIQUID"]
        result = create_hyperliquid_data_client(instruments=custom_instruments)

        config = result[HYPERLIQUID]
        assert config.instrument_provider.load_ids == custom_instruments

    def test_load_all_instruments(self):
        """load_all=True enables loading all instruments."""
        result = create_hyperliquid_data_client(load_all=True)

        config = result[HYPERLIQUID]
        assert config.instrument_provider.load_all is True

    def test_http_timeout_configuration(self):
        """HTTP timeout is configurable."""
        result = create_hyperliquid_data_client(http_timeout_secs=15)

        assert result[HYPERLIQUID].http_timeout_secs == 15


class TestCreateDataOnlyTradingNode:
    """Tests for create_data_only_trading_node factory."""

    def test_returns_trading_node_config(self):
        """Factory returns TradingNodeConfig."""
        result = create_data_only_trading_node()

        assert isinstance(result, TradingNodeConfig)

    def test_default_trader_id(self):
        """Default trader_id is TRADER-HL-DATA."""
        result = create_data_only_trading_node()

        assert str(result.trader_id) == "TRADER-HL-DATA"

    def test_custom_trader_id(self):
        """Custom trader_id is used."""
        result = create_data_only_trading_node(trader_id="CUSTOM-TRADER")

        assert str(result.trader_id) == "CUSTOM-TRADER"

    def test_data_clients_configured(self):
        """Data clients are properly configured."""
        result = create_data_only_trading_node()

        assert HYPERLIQUID in result.data_clients
        assert isinstance(result.data_clients[HYPERLIQUID], HyperliquidDataClientConfig)

    def test_no_exec_clients_by_default(self):
        """Data-only config has no execution clients."""
        result = create_data_only_trading_node()

        assert result.exec_clients is None or len(result.exec_clients) == 0

    def test_testnet_propagated(self):
        """Testnet parameter propagates to data client."""
        result = create_data_only_trading_node(testnet=True)

        assert result.data_clients[HYPERLIQUID].testnet is True

    def test_instruments_propagated(self):
        """Instruments parameter propagates to data client."""
        custom_instruments = ["SOL-USD-PERP.HYPERLIQUID"]
        result = create_data_only_trading_node(instruments=custom_instruments)

        config = result.data_clients[HYPERLIQUID]
        assert config.instrument_provider.load_ids == custom_instruments


class TestDefaultInstruments:
    """Tests for DEFAULT_INSTRUMENTS constant."""

    def test_contains_btc_perp(self):
        """BTC-USD-PERP is in default instruments."""
        assert "BTC-USD-PERP.HYPERLIQUID" in DEFAULT_INSTRUMENTS

    def test_contains_eth_perp(self):
        """ETH-USD-PERP is in default instruments."""
        assert "ETH-USD-PERP.HYPERLIQUID" in DEFAULT_INSTRUMENTS

    def test_has_hyperliquid_venue(self):
        """All instruments have HYPERLIQUID venue suffix."""
        for instrument in DEFAULT_INSTRUMENTS:
            assert instrument.endswith(".HYPERLIQUID")
