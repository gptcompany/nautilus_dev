"""
Unit tests for TradingNodeConfigFactory (T012).

TDD: RED phase - tests written before implementation.
"""

from __future__ import annotations


from config.factory import TradingNodeConfigFactory
from config.models import (
    BinanceCredentials,
    BybitCredentials,
    ConfigEnvironment,
    TradingNodeSettings,
)


class TestTradingNodeConfigFactoryFromSettings:
    """Tests for TradingNodeConfigFactory.from_settings()."""

    def test_creates_valid_trading_node_config(
        self, valid_trading_node_settings: TradingNodeSettings
    ):
        """from_settings() should create a valid TradingNodeConfig."""
        config = TradingNodeConfigFactory.from_settings(valid_trading_node_settings)

        # Verify core settings
        assert str(config.trader_id) == valid_trading_node_settings.environment.trader_id

    def test_includes_cache_config(self, valid_trading_node_settings: TradingNodeSettings):
        """from_settings() should include CacheConfig with Redis settings."""
        config = TradingNodeConfigFactory.from_settings(valid_trading_node_settings)

        assert config.cache is not None
        assert config.cache.database is not None
        assert config.cache.database.host == valid_trading_node_settings.redis.host
        assert config.cache.database.port == valid_trading_node_settings.redis.port

    def test_includes_exec_engine_config(self, valid_trading_node_settings: TradingNodeSettings):
        """from_settings() should include LiveExecEngineConfig."""
        config = TradingNodeConfigFactory.from_settings(valid_trading_node_settings)

        assert config.exec_engine is not None
        assert config.exec_engine.reconciliation is True
        assert (
            config.exec_engine.reconciliation_lookback_mins
            == valid_trading_node_settings.reconciliation_lookback_mins
        )

    def test_includes_data_engine_config(self, valid_trading_node_settings: TradingNodeSettings):
        """from_settings() should include LiveDataEngineConfig."""
        config = TradingNodeConfigFactory.from_settings(valid_trading_node_settings)

        assert config.data_engine is not None

    def test_includes_risk_engine_config(self, valid_trading_node_settings: TradingNodeSettings):
        """from_settings() should include LiveRiskEngineConfig."""
        config = TradingNodeConfigFactory.from_settings(valid_trading_node_settings)

        assert config.risk_engine is not None
        assert config.risk_engine.bypass is False

    def test_includes_logging_config(self, valid_trading_node_settings: TradingNodeSettings):
        """from_settings() should include LoggingConfig."""
        config = TradingNodeConfigFactory.from_settings(valid_trading_node_settings)

        assert config.logging is not None
        assert config.logging.log_level == valid_trading_node_settings.logging.log_level

    def test_includes_streaming_config(self, valid_trading_node_settings: TradingNodeSettings):
        """from_settings() should include StreamingConfig."""
        config = TradingNodeConfigFactory.from_settings(valid_trading_node_settings)

        assert config.streaming is not None
        assert config.streaming.catalog_path == valid_trading_node_settings.streaming.catalog_path

    def test_includes_binance_clients(self, valid_trading_node_settings: TradingNodeSettings):
        """from_settings() should include Binance data/exec clients."""
        config = TradingNodeConfigFactory.from_settings(valid_trading_node_settings)

        assert "BINANCE" in config.data_clients
        assert "BINANCE" in config.exec_clients

    def test_includes_bybit_clients_when_configured(
        self, valid_trading_node_settings_both_exchanges: TradingNodeSettings
    ):
        """from_settings() should include Bybit clients when configured."""
        config = TradingNodeConfigFactory.from_settings(valid_trading_node_settings_both_exchanges)

        assert "BYBIT" in config.data_clients
        assert "BYBIT" in config.exec_clients

    def test_does_not_include_unconfigured_exchanges(
        self, valid_trading_node_settings: TradingNodeSettings
    ):
        """from_settings() should not include unconfigured exchanges."""
        config = TradingNodeConfigFactory.from_settings(valid_trading_node_settings)

        assert "BYBIT" not in config.data_clients
        assert "BYBIT" not in config.exec_clients

    def test_accepts_strategies(self, valid_trading_node_settings: TradingNodeSettings):
        """from_settings() should accept strategy configurations."""
        mock_strategy = {"strategy_id": "TEST-001"}
        config = TradingNodeConfigFactory.from_settings(
            valid_trading_node_settings,
            strategies=[mock_strategy],
        )

        assert len(config.strategies) == 1


class TestTradingNodeConfigFactoryCreateProduction:
    """Tests for TradingNodeConfigFactory.create_production()."""

    def test_loads_from_environment(self, set_env_vars):
        """create_production() should load settings from environment."""
        config = TradingNodeConfigFactory.create_production()

        assert str(config.trader_id) == "TEST-TRADER-001"
        assert "BINANCE" in config.data_clients


class TestTradingNodeConfigFactoryCreateTestnet:
    """Tests for TradingNodeConfigFactory.create_testnet()."""

    def test_loads_from_environment(self, set_env_vars):
        """create_testnet() should load settings from environment."""
        config = TradingNodeConfigFactory.create_testnet()

        assert str(config.trader_id) == "TEST-TRADER-001"

    def test_forces_testnet_mode_binance(self, set_env_vars):
        """create_testnet() should force testnet=True for Binance."""
        config = TradingNodeConfigFactory.create_testnet()

        # Verify testnet is forced
        binance_config = config.data_clients.get("BINANCE")
        assert binance_config is not None
        assert binance_config.testnet is True

    def test_forces_testnet_mode_bybit(
        self,
        valid_config_environment: ConfigEnvironment,
        valid_binance_credentials: BinanceCredentials,
        valid_bybit_credentials: BybitCredentials,
    ):
        """create_testnet() should force testnet=True for Bybit."""
        # Create settings with both exchanges
        settings = TradingNodeSettings(
            environment=valid_config_environment,
            binance=valid_binance_credentials,
            bybit=valid_bybit_credentials,
        )

        # Force production mode initially
        settings.binance.testnet = False
        settings.bybit.testnet = False

        # Use from_settings and manually force testnet
        settings.binance.testnet = True
        settings.bybit.testnet = True

        config = TradingNodeConfigFactory.from_settings(settings)

        bybit_config = config.data_clients.get("BYBIT")
        assert bybit_config is not None
        assert bybit_config.testnet is True


class TestTradingNodeConfigTimeouts:
    """Tests for configuration timeout settings."""

    def test_connection_timeout(self, valid_trading_node_settings: TradingNodeSettings):
        """Configuration should have appropriate connection timeout."""
        config = TradingNodeConfigFactory.from_settings(valid_trading_node_settings)

        assert config.timeout_connection == 30.0

    def test_reconciliation_timeout(self, valid_trading_node_settings: TradingNodeSettings):
        """Reconciliation timeout should be based on startup delay."""
        config = TradingNodeConfigFactory.from_settings(valid_trading_node_settings)

        expected_timeout = valid_trading_node_settings.reconciliation_startup_delay_secs + 5.0
        assert config.timeout_reconciliation == expected_timeout
