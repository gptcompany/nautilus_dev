"""
Unit tests for TradingNodeSettings validation (T011).

TDD: RED phase - tests written before implementation.
"""

from __future__ import annotations


import pytest
from pydantic import ValidationError

from config.models import (
    BinanceCredentials,
    BybitCredentials,
    ConfigEnvironment,
    ExchangeCredentials,
    LoggingSettings,
    RedisConfig,
    StreamingSettings,
    TradingNodeSettings,
)


class TestConfigEnvironment:
    """Tests for ConfigEnvironment model."""

    def test_valid_trader_id(self, valid_trader_id: str):
        """Valid trader ID should be accepted."""
        env = ConfigEnvironment(trader_id=valid_trader_id)
        assert env.trader_id == valid_trader_id
        assert env.environment == "SANDBOX"  # default

    def test_invalid_trader_id_too_short(self):
        """Trader ID under 3 chars should fail."""
        with pytest.raises(ValidationError) as exc_info:
            ConfigEnvironment(trader_id="AB")
        assert "trader_id must be 3-32 characters" in str(exc_info.value)

    def test_invalid_trader_id_too_long(self):
        """Trader ID over 32 chars should fail."""
        with pytest.raises(ValidationError) as exc_info:
            ConfigEnvironment(trader_id="A" * 33)
        assert "trader_id must be 3-32 characters" in str(exc_info.value)

    def test_invalid_trader_id_pattern(self):
        """Trader ID with lowercase should fail."""
        with pytest.raises(ValidationError):
            ConfigEnvironment(trader_id="invalid-id")

    def test_environment_default_sandbox(self):
        """Environment should default to SANDBOX."""
        env = ConfigEnvironment(trader_id="TEST-001")
        assert env.environment == "SANDBOX"

    def test_environment_live(self):
        """LIVE environment should be accepted."""
        env = ConfigEnvironment(trader_id="TEST-001", environment="LIVE")
        assert env.environment == "LIVE"

    def test_invalid_environment(self):
        """Invalid environment should fail."""
        with pytest.raises(ValidationError):
            ConfigEnvironment(trader_id="TEST-001", environment="PRODUCTION")


class TestRedisConfig:
    """Tests for RedisConfig model."""

    def test_defaults(self):
        """RedisConfig should have sensible defaults."""
        config = RedisConfig()
        assert config.host == "localhost"
        assert config.port == 6379
        assert config.password is None
        assert config.timeout == 2.0

    def test_invalid_port_too_low(self):
        """Port below 1 should fail."""
        with pytest.raises(ValidationError):
            RedisConfig(port=0)

    def test_invalid_port_too_high(self):
        """Port above 65535 should fail."""
        with pytest.raises(ValidationError):
            RedisConfig(port=65536)

    def test_timeout_bounds(self):
        """Timeout should be within bounds."""
        with pytest.raises(ValidationError):
            RedisConfig(timeout=0.05)  # too low
        with pytest.raises(ValidationError):
            RedisConfig(timeout=31.0)  # too high


class TestLoggingSettings:
    """Tests for LoggingSettings model."""

    def test_defaults(self):
        """LoggingSettings should have sensible defaults."""
        settings = LoggingSettings()
        assert settings.log_level == "INFO"
        assert settings.log_level_file == "DEBUG"
        assert settings.log_format == "json"

    def test_valid_log_levels(self):
        """Valid log levels should be accepted."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            settings = LoggingSettings(log_level=level)
            assert settings.log_level == level

    def test_invalid_log_level(self):
        """Invalid log level should fail."""
        with pytest.raises(ValidationError):
            LoggingSettings(log_level="TRACE")


class TestStreamingSettings:
    """Tests for StreamingSettings model."""

    def test_defaults(self):
        """StreamingSettings should have sensible defaults."""
        settings = StreamingSettings()
        assert settings.catalog_path == "/data/nautilus/catalog"
        assert settings.flush_interval_ms == 2000
        assert settings.rotation_mode == "SIZE"

    def test_flush_interval_bounds(self):
        """Flush interval should be within bounds."""
        with pytest.raises(ValidationError):
            StreamingSettings(flush_interval_ms=50)  # too low
        with pytest.raises(ValidationError):
            StreamingSettings(flush_interval_ms=15000)  # too high


class TestExchangeCredentials:
    """Tests for ExchangeCredentials model."""

    def test_valid_credentials(self):
        """Valid credentials should be accepted."""
        creds = ExchangeCredentials(
            api_key="valid_api_key_12345678",
            api_secret="valid_api_secret_12345678",
        )
        assert creds.testnet is False  # default

    def test_api_key_too_short(self):
        """API key under 16 chars should fail."""
        with pytest.raises(ValidationError):
            ExchangeCredentials(
                api_key="short",
                api_secret="valid_api_secret_12345678",
            )

    def test_placeholder_credentials_rejected(self):
        """Placeholder credentials should fail."""
        with pytest.raises(ValidationError) as exc_info:
            ExchangeCredentials(
                api_key="xxx_placeholder_key_here",
                api_secret="valid_api_secret_12345678",
            )
        assert "Placeholder credentials not allowed" in str(exc_info.value)


class TestBinanceCredentials:
    """Tests for BinanceCredentials model."""

    def test_defaults(self, valid_binance_credentials: BinanceCredentials):
        """BinanceCredentials should have sensible defaults."""
        assert valid_binance_credentials.account_type == "USDT_FUTURES"
        assert valid_binance_credentials.us is False

    def test_account_types(self):
        """Valid account types should be accepted."""
        for account_type in ["SPOT", "USDT_FUTURES", "COIN_FUTURES"]:
            creds = BinanceCredentials(
                api_key="valid_api_key_12345678",
                api_secret="valid_api_secret_12345678",
                account_type=account_type,
            )
            assert creds.account_type == account_type


class TestBybitCredentials:
    """Tests for BybitCredentials model."""

    def test_defaults(self, valid_bybit_credentials: BybitCredentials):
        """BybitCredentials should have sensible defaults."""
        assert valid_bybit_credentials.product_types == ["LINEAR"]
        assert valid_bybit_credentials.demo is False

    def test_spot_cannot_mix_with_derivatives(self):
        """SPOT cannot be mixed with derivative types."""
        with pytest.raises(ValidationError) as exc_info:
            BybitCredentials(
                api_key="valid_api_key_12345678",
                api_secret="valid_api_secret_12345678",
                product_types=["SPOT", "LINEAR"],
            )
        assert "SPOT cannot be mixed with derivatives" in str(exc_info.value)


class TestTradingNodeSettings:
    """Tests for TradingNodeSettings model."""

    def test_valid_settings_binance_only(self, valid_trading_node_settings: TradingNodeSettings):
        """Valid settings with Binance only should be accepted."""
        assert valid_trading_node_settings.binance is not None
        assert valid_trading_node_settings.bybit is None

    def test_valid_settings_both_exchanges(
        self, valid_trading_node_settings_both_exchanges: TradingNodeSettings
    ):
        """Valid settings with both exchanges should be accepted."""
        assert valid_trading_node_settings_both_exchanges.binance is not None
        assert valid_trading_node_settings_both_exchanges.bybit is not None

    def test_at_least_one_exchange_required(self, valid_config_environment: ConfigEnvironment):
        """At least one exchange must be configured."""
        with pytest.raises(ValidationError) as exc_info:
            TradingNodeSettings(
                environment=valid_config_environment,
            )
        assert "At least one exchange must be configured" in str(exc_info.value)

    def test_reconciliation_lookback_minimum(
        self,
        valid_config_environment: ConfigEnvironment,
        valid_binance_credentials: BinanceCredentials,
    ):
        """Reconciliation lookback must be >= 60 minutes."""
        with pytest.raises(ValidationError):
            TradingNodeSettings(
                environment=valid_config_environment,
                binance=valid_binance_credentials,
                reconciliation_lookback_mins=30,  # too low
            )

    def test_reconciliation_startup_delay_minimum(
        self,
        valid_config_environment: ConfigEnvironment,
        valid_binance_credentials: BinanceCredentials,
    ):
        """Reconciliation startup delay must be >= 10 seconds."""
        with pytest.raises(ValidationError):
            TradingNodeSettings(
                environment=valid_config_environment,
                binance=valid_binance_credentials,
                reconciliation_startup_delay_secs=5.0,  # too low
            )

    def test_from_env_with_binance(self, set_env_vars):
        """from_env() should load settings from environment."""
        settings = TradingNodeSettings.from_env()
        assert settings.environment.trader_id == "TEST-TRADER-001"
        assert settings.environment.environment == "SANDBOX"
        assert settings.binance is not None
        assert settings.binance.testnet is True
        assert settings.bybit is None

    def test_from_env_missing_trader_id(self, clean_env):
        """from_env() should fail if NAUTILUS_TRADER_ID is missing."""
        with pytest.raises(KeyError):
            TradingNodeSettings.from_env()
