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

    def test_testnet_from_credentials(
        self, valid_binance_credentials: BinanceCredentials
    ):
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

    def test_returns_data_client_config(
        self, valid_binance_credentials: BinanceCredentials
    ):
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
    """Tests for Binance exec client config builder (T029)."""

    def test_returns_exec_client_config(
        self, valid_binance_credentials: BinanceCredentials
    ):
        """Builder should return a valid exec client config."""
        config = build_binance_exec_client_config(valid_binance_credentials)
        assert config is not None

    def test_uses_reduce_only(self, valid_binance_credentials: BinanceCredentials):
        """Config should use reduce_only for safety."""
        config = build_binance_exec_client_config(valid_binance_credentials)
        assert config.use_reduce_only is True

    def test_uses_position_ids(self, valid_binance_credentials: BinanceCredentials):
        """Config should use position_ids for hedging mode."""
        config = build_binance_exec_client_config(valid_binance_credentials)
        assert config.use_position_ids is True

    def test_recv_window(self, valid_binance_credentials: BinanceCredentials):
        """Config should have appropriate recv_window."""
        config = build_binance_exec_client_config(valid_binance_credentials)
        assert config.recv_window_ms == 5000

    def test_max_retries(self, valid_binance_credentials: BinanceCredentials):
        """Config should have 3 max retries."""
        config = build_binance_exec_client_config(valid_binance_credentials)
        assert config.max_retries == 3


class TestBybitDataClientConfig:
    """Tests for Bybit data client config builder (T030)."""

    def test_returns_data_client_config(
        self, valid_bybit_credentials: BybitCredentials
    ):
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

    def test_returns_exec_client_config(
        self, valid_bybit_credentials: BybitCredentials
    ):
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
