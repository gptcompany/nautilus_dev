"""
Unit tests for Exchange Client Configurations (T027-T030).

TDD: RED phase - tests written before implementation.
"""

from __future__ import annotations

from config.clients.binance import (
    build_binance_data_client_config,
    build_binance_exec_client_config,
)
from config.clients.bybit import (
    build_bybit_data_client_config,
    build_bybit_exec_client_config,
)
from config.models import BinanceCredentials, BybitCredentials


class TestBinanceCredentialsModel:
    """Tests for BinanceCredentials model (T027)."""

    def test_default_account_type(self, valid_binance_credentials: BinanceCredentials):
        """Default account type should be USDT_FUTURES."""
        assert valid_binance_credentials.account_type == "USDT_FUTURES"

    def test_default_us(self, valid_binance_credentials: BinanceCredentials):
        """Default US should be False."""
        assert valid_binance_credentials.us is False

    def test_testnet_from_credentials(self, valid_binance_credentials: BinanceCredentials):
        """Testnet should be set from credentials."""
        assert valid_binance_credentials.testnet is True

    def test_spot_account_type(self):
        """SPOT account type should be valid."""
        creds = BinanceCredentials(
            api_key="test_api_key_12345678",
            api_secret="test_api_secret_12345678",
            account_type="SPOT",
        )
        assert creds.account_type == "SPOT"

    def test_coin_futures_account_type(self):
        """COIN_FUTURES account type should be valid."""
        creds = BinanceCredentials(
            api_key="test_api_key_12345678",
            api_secret="test_api_secret_12345678",
            account_type="COIN_FUTURES",
        )
        assert creds.account_type == "COIN_FUTURES"


class TestBybitCredentialsModel:
    """Tests for BybitCredentials model (T028)."""

    def test_default_product_types(self, valid_bybit_credentials: BybitCredentials):
        """Default product types should be LINEAR."""
        assert valid_bybit_credentials.product_types == ["LINEAR"]

    def test_default_demo(self, valid_bybit_credentials: BybitCredentials):
        """Default demo should be False."""
        assert valid_bybit_credentials.demo is False

    def test_testnet_from_credentials(self, valid_bybit_credentials: BybitCredentials):
        """Testnet should be set from credentials."""
        assert valid_bybit_credentials.testnet is True

    def test_multiple_product_types(self):
        """Multiple product types should be valid (except SPOT mixing)."""
        creds = BybitCredentials(
            api_key="test_api_key_12345678",
            api_secret="test_api_secret_12345678",
            product_types=["LINEAR", "INVERSE"],
        )
        assert creds.product_types == ["LINEAR", "INVERSE"]


class TestBinanceDataClientConfig:
    """Tests for Binance data client config builder (T029)."""

    def test_returns_data_client_config(self, valid_binance_credentials: BinanceCredentials):
        """Builder should return a valid data client config."""
        config = build_binance_data_client_config(valid_binance_credentials)
        assert config is not None

    def test_uses_account_type(self, valid_binance_credentials: BinanceCredentials):
        """Config should use account type from credentials."""
        config = build_binance_data_client_config(valid_binance_credentials)
        # Account type is an enum, check the value
        assert "USDT_FUTURES" in str(config.account_type)

    def test_uses_testnet(self, valid_binance_credentials: BinanceCredentials):
        """Config should use testnet from credentials."""
        config = build_binance_data_client_config(valid_binance_credentials)
        assert config.testnet is True

    def test_uses_us(self, valid_binance_credentials: BinanceCredentials):
        """Config should use US setting from credentials."""
        config = build_binance_data_client_config(valid_binance_credentials)
        assert config.us is False

    def test_instrument_provider(self, valid_binance_credentials: BinanceCredentials):
        """Config should have instrument provider configured."""
        config = build_binance_data_client_config(valid_binance_credentials)
        assert config.instrument_provider is not None


class TestBinanceExecClientConfig:
    """Tests for Binance exec client config builder (Spec 015 FR-001)."""

    def test_returns_exec_client_config(self, valid_binance_credentials: BinanceCredentials):
        """Builder should return a valid exec client config."""
        config = build_binance_exec_client_config(valid_binance_credentials)
        assert config is not None

    def test_uses_reduce_only(self, valid_binance_credentials: BinanceCredentials):
        """Config should use reduce_only for NETTING mode safety (HEDGE bug #3104)."""
        config = build_binance_exec_client_config(valid_binance_credentials)
        assert config.use_reduce_only is True

    def test_uses_position_ids(self, valid_binance_credentials: BinanceCredentials):
        """Config should use position_ids for position tracking."""
        config = build_binance_exec_client_config(valid_binance_credentials)
        assert config.use_position_ids is True

    def test_recv_window(self, valid_binance_credentials: BinanceCredentials):
        """Config should have appropriate recv_window."""
        config = build_binance_exec_client_config(valid_binance_credentials)
        assert config.recv_window_ms == 5000

    def test_max_retries(self, valid_binance_credentials: BinanceCredentials):
        """Config should have 3 max retries by default."""
        config = build_binance_exec_client_config(valid_binance_credentials)
        assert config.max_retries == 3

    def test_custom_max_retries(self, valid_binance_credentials: BinanceCredentials):
        """Config should accept custom max_retries."""
        config = build_binance_exec_client_config(valid_binance_credentials, max_retries=5)
        assert config.max_retries == 5

    def test_retry_delay_initial_ms(self, valid_binance_credentials: BinanceCredentials):
        """Config should have 500ms initial retry delay by default."""
        config = build_binance_exec_client_config(valid_binance_credentials)
        assert config.retry_delay_initial_ms == 500

    def test_retry_delay_max_ms(self, valid_binance_credentials: BinanceCredentials):
        """Config should have 5000ms max retry delay by default."""
        config = build_binance_exec_client_config(valid_binance_credentials)
        assert config.retry_delay_max_ms == 5000

    def test_custom_retry_delays(self, valid_binance_credentials: BinanceCredentials):
        """Config should accept custom retry delay parameters."""
        config = build_binance_exec_client_config(
            valid_binance_credentials,
            retry_delay_initial_ms=1000,
            retry_delay_max_ms=10000,
        )
        assert config.retry_delay_initial_ms == 1000
        assert config.retry_delay_max_ms == 10000

    def test_futures_leverages(self, valid_binance_credentials: BinanceCredentials):
        """Config should support futures leverage mapping."""
        config = build_binance_exec_client_config(
            valid_binance_credentials,
            futures_leverages={"BTCUSDT": 10, "ETHUSDT": 5},
        )
        assert config.futures_leverages is not None
        assert config.futures_leverages["BTCUSDT"] == 10
        assert config.futures_leverages["ETHUSDT"] == 5

    def test_futures_margin_types(self, valid_binance_credentials: BinanceCredentials):
        """Config should support futures margin type mapping."""
        from nautilus_trader.adapters.binance.futures.enums import (
            BinanceFuturesMarginType,
        )

        config = build_binance_exec_client_config(
            valid_binance_credentials,
            futures_margin_types={"BTCUSDT": "CROSS"},
        )
        assert config.futures_margin_types is not None
        assert config.futures_margin_types["BTCUSDT"] == BinanceFuturesMarginType.CROSS

    def test_futures_margin_types_isolated(self, valid_binance_credentials: BinanceCredentials):
        """Config should support ISOLATED margin type."""
        from nautilus_trader.adapters.binance.futures.enums import (
            BinanceFuturesMarginType,
        )

        config = build_binance_exec_client_config(
            valid_binance_credentials,
            futures_margin_types={"ETHUSDT": "ISOLATED"},
        )
        assert config.futures_margin_types["ETHUSDT"] == BinanceFuturesMarginType.ISOLATED

    def test_none_futures_config_by_default(self, valid_binance_credentials: BinanceCredentials):
        """Futures config should be None by default."""
        config = build_binance_exec_client_config(valid_binance_credentials)
        assert config.futures_leverages is None
        assert config.futures_margin_types is None


class TestBybitDataClientConfig:
    """Tests for Bybit data client config builder (T030)."""

    def test_returns_data_client_config(self, valid_bybit_credentials: BybitCredentials):
        """Builder should return a valid data client config."""
        config = build_bybit_data_client_config(valid_bybit_credentials)
        assert config is not None

    def test_uses_product_types(self, valid_bybit_credentials: BybitCredentials):
        """Config should use product types from credentials."""
        config = build_bybit_data_client_config(valid_bybit_credentials)
        assert len(config.product_types) == 1

    def test_uses_testnet(self, valid_bybit_credentials: BybitCredentials):
        """Config should use testnet from credentials."""
        config = build_bybit_data_client_config(valid_bybit_credentials)
        assert config.testnet is True

    def test_uses_demo(self, valid_bybit_credentials: BybitCredentials):
        """Config should use demo from credentials."""
        config = build_bybit_data_client_config(valid_bybit_credentials)
        assert config.demo is False


class TestBybitExecClientConfig:
    """Tests for Bybit exec client config builder (T030)."""

    def test_returns_exec_client_config(self, valid_bybit_credentials: BybitCredentials):
        """Builder should return a valid exec client config."""
        config = build_bybit_exec_client_config(valid_bybit_credentials)
        assert config is not None

    def test_recv_window(self, valid_bybit_credentials: BybitCredentials):
        """Config should have appropriate recv_window."""
        config = build_bybit_exec_client_config(valid_bybit_credentials)
        assert config.recv_window_ms == 5000

    def test_max_retries(self, valid_bybit_credentials: BybitCredentials):
        """Config should have 3 max retries."""
        config = build_bybit_exec_client_config(valid_bybit_credentials)
        assert config.max_retries == 3

    def test_retry_delays(self, valid_bybit_credentials: BybitCredentials):
        """Config should have appropriate retry delays."""
        config = build_bybit_exec_client_config(valid_bybit_credentials)
        assert config.retry_delay_initial_ms == 1000
        assert config.retry_delay_max_ms == 10000
