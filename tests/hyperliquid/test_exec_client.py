"""Unit tests for Hyperliquid execution client configuration (Spec 021 - US3).

Tests the factory functions for creating HyperliquidExecClientConfig.
"""

from nautilus_trader.adapters.hyperliquid import HYPERLIQUID
from nautilus_trader.adapters.hyperliquid import HyperliquidExecClientConfig
from nautilus_trader.config import TradingNodeConfig

from configs.hyperliquid.exec_client import create_hyperliquid_exec_client
from configs.hyperliquid.testnet import create_testnet_trading_node
from configs.hyperliquid.data_client import DEFAULT_INSTRUMENTS


class TestCreateHyperliquidExecClient:
    """Tests for create_hyperliquid_exec_client factory."""

    def test_returns_dict_with_hyperliquid_key(self):
        """Factory returns dict with HYPERLIQUID key."""
        result = create_hyperliquid_exec_client()

        assert isinstance(result, dict)
        assert HYPERLIQUID in result
        assert isinstance(result[HYPERLIQUID], HyperliquidExecClientConfig)

    def test_default_uses_testnet(self):
        """Default configuration uses testnet (safety first)."""
        result = create_hyperliquid_exec_client()

        assert result[HYPERLIQUID].testnet is True

    def test_mainnet_config(self):
        """Can configure for mainnet."""
        result = create_hyperliquid_exec_client(testnet=False)

        assert result[HYPERLIQUID].testnet is False

    def test_private_key_is_none(self):
        """Private key is None (loaded from env)."""
        result = create_hyperliquid_exec_client()

        assert result[HYPERLIQUID].private_key is None

    def test_default_instruments_loaded(self):
        """Default instruments are loaded."""
        result = create_hyperliquid_exec_client()

        config = result[HYPERLIQUID]
        assert config.instrument_provider.load_all is False
        assert config.instrument_provider.load_ids == DEFAULT_INSTRUMENTS

    def test_custom_instruments(self):
        """Custom instruments can be specified."""
        custom_instruments = ["SOL-USD-PERP.HYPERLIQUID"]
        result = create_hyperliquid_exec_client(instruments=custom_instruments)

        config = result[HYPERLIQUID]
        assert config.instrument_provider.load_ids == custom_instruments

    def test_load_all_instruments(self):
        """load_all=True enables loading all instruments."""
        result = create_hyperliquid_exec_client(load_all=True)

        config = result[HYPERLIQUID]
        assert config.instrument_provider.load_all is True

    def test_retry_configuration(self):
        """Retry parameters are configurable."""
        result = create_hyperliquid_exec_client(
            max_retries=5,
            retry_delay_initial_ms=200,
            retry_delay_max_ms=10000,
        )

        config = result[HYPERLIQUID]
        assert config.max_retries == 5
        assert config.retry_delay_initial_ms == 200
        assert config.retry_delay_max_ms == 10000

    def test_http_timeout_configuration(self):
        """HTTP timeout is configurable."""
        result = create_hyperliquid_exec_client(http_timeout_secs=15)

        assert result[HYPERLIQUID].http_timeout_secs == 15


class TestCreateTestnetTradingNode:
    """Tests for create_testnet_trading_node factory."""

    def test_returns_trading_node_config(self):
        """Factory returns TradingNodeConfig."""
        result = create_testnet_trading_node()

        assert isinstance(result, TradingNodeConfig)

    def test_default_trader_id(self):
        """Default trader_id is TRADER-HL-TESTNET."""
        result = create_testnet_trading_node()

        assert str(result.trader_id) == "TRADER-HL-TESTNET"

    def test_custom_trader_id(self):
        """Custom trader_id is used."""
        result = create_testnet_trading_node(trader_id="CUSTOM-TESTNET")

        assert str(result.trader_id) == "CUSTOM-TESTNET"

    def test_data_clients_configured(self):
        """Data clients are configured for testnet."""
        result = create_testnet_trading_node()

        assert HYPERLIQUID in result.data_clients
        assert result.data_clients[HYPERLIQUID].testnet is True

    def test_exec_clients_configured(self):
        """Exec clients are configured for testnet."""
        result = create_testnet_trading_node()

        assert HYPERLIQUID in result.exec_clients
        assert result.exec_clients[HYPERLIQUID].testnet is True

    def test_private_key_is_none(self):
        """Private key is None (loaded from env)."""
        result = create_testnet_trading_node()

        assert result.exec_clients[HYPERLIQUID].private_key is None

    def test_instruments_propagated(self):
        """Instruments parameter propagates to both clients."""
        custom_instruments = ["SOL-USD-PERP.HYPERLIQUID"]
        result = create_testnet_trading_node(instruments=custom_instruments)

        data_config = result.data_clients[HYPERLIQUID]
        exec_config = result.exec_clients[HYPERLIQUID]

        assert data_config.instrument_provider.load_ids == custom_instruments
        assert exec_config.instrument_provider.load_ids == custom_instruments

    def test_max_retries_applied(self):
        """max_retries parameter is applied."""
        result = create_testnet_trading_node(max_retries=5)

        assert result.exec_clients[HYPERLIQUID].max_retries == 5
