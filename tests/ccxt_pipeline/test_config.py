"""Unit tests for configuration."""

from pathlib import Path

import pytest

from scripts.ccxt_pipeline.config import CCXTPipelineConfig, get_config


class TestCCXTPipelineConfig:
    """Tests for CCXTPipelineConfig."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = CCXTPipelineConfig()
        assert config.exchanges == ["binance", "bybit", "hyperliquid"]
        assert config.symbols == ["BTCUSDT-PERP", "ETHUSDT-PERP"]
        assert config.oi_fetch_interval_seconds == 300
        assert config.funding_fetch_interval_seconds == 3600
        assert config.log_level == "INFO"

    def test_custom_catalog_path(self, temp_catalog_path: Path) -> None:
        """Test custom catalog path."""
        config = CCXTPipelineConfig(catalog_path=temp_catalog_path)
        assert config.catalog_path == temp_catalog_path

    def test_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test environment variable override."""
        monkeypatch.setenv("CCXT_LOG_LEVEL", "DEBUG")
        config = CCXTPipelineConfig()
        assert config.log_level == "DEBUG"

    def test_api_keys_default_none(self) -> None:
        """Test API keys default to None."""
        config = CCXTPipelineConfig()
        assert config.binance_api_key is None
        assert config.binance_api_secret is None
        assert config.bybit_api_key is None
        assert config.bybit_api_secret is None

    def test_api_keys_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test API keys can be set from environment."""
        monkeypatch.setenv("CCXT_BINANCE_API_KEY", "test_key")
        monkeypatch.setenv("CCXT_BINANCE_API_SECRET", "test_secret")
        config = CCXTPipelineConfig()
        assert config.binance_api_key == "test_key"
        assert config.binance_api_secret == "test_secret"

    def test_max_concurrent_requests(self) -> None:
        """Test max concurrent requests setting."""
        config = CCXTPipelineConfig(max_concurrent_requests=10)
        assert config.max_concurrent_requests == 10

    def test_custom_exchanges(self) -> None:
        """Test custom exchange list."""
        config = CCXTPipelineConfig(exchanges=["binance"])
        assert config.exchanges == ["binance"]

    def test_custom_symbols(self) -> None:
        """Test custom symbol list."""
        config = CCXTPipelineConfig(symbols=["BTCUSDT-PERP"])
        assert config.symbols == ["BTCUSDT-PERP"]


class TestGetConfig:
    """Tests for get_config function."""

    def test_get_config_returns_config(self) -> None:
        """Test that get_config returns a CCXTPipelineConfig."""
        config = get_config()
        assert isinstance(config, CCXTPipelineConfig)
