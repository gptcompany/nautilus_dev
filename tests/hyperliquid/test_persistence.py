"""Tests for Hyperliquid data persistence configuration (Spec 021 - US2).

Tests the factory functions for creating persistence configurations.
"""

import tempfile
from pathlib import Path

import pytest

# Skip entire module if Hyperliquid adapter not available
pytest.importorskip("nautilus_trader.adapters.hyperliquid")

from nautilus_trader.adapters.hyperliquid import HYPERLIQUID
from nautilus_trader.config import TradingNodeConfig, StreamingConfig

from configs.hyperliquid.persistence import (
    create_persistence_config,
    create_recording_trading_node,
    DEFAULT_CATALOG_PATH,
)
from configs.hyperliquid.data_client import DEFAULT_INSTRUMENTS


class TestCreatePersistenceConfig:
    """Tests for create_persistence_config factory."""

    def test_returns_streaming_config(self):
        """Factory returns StreamingConfig."""
        result = create_persistence_config()

        assert isinstance(result, StreamingConfig)

    def test_default_catalog_path(self):
        """Default catalog path is used."""
        result = create_persistence_config()

        assert result.catalog_path == DEFAULT_CATALOG_PATH

    def test_custom_catalog_path_string(self):
        """Custom catalog path (string) is used."""
        custom_path = "/tmp/my_catalog"
        result = create_persistence_config(catalog_path=custom_path)

        assert result.catalog_path == custom_path

    def test_custom_catalog_path_object(self):
        """Custom catalog path (Path object) is used."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_path = Path(tmpdir) / "catalog"
            result = create_persistence_config(catalog_path=custom_path)

            assert result.catalog_path == str(custom_path)


class TestCreateRecordingTradingNode:
    """Tests for create_recording_trading_node factory."""

    def test_returns_trading_node_config(self):
        """Factory returns TradingNodeConfig."""
        result = create_recording_trading_node()

        assert isinstance(result, TradingNodeConfig)

    def test_default_trader_id(self):
        """Default trader_id is TRADER-HL-RECORD."""
        result = create_recording_trading_node()

        assert str(result.trader_id) == "TRADER-HL-RECORD"

    def test_data_clients_configured(self):
        """Data clients are properly configured."""
        result = create_recording_trading_node()

        assert HYPERLIQUID in result.data_clients

    def test_streaming_configured(self):
        """Streaming config is present for persistence."""
        result = create_recording_trading_node()

        assert result.streaming is not None
        assert isinstance(result.streaming, StreamingConfig)

    def test_default_catalog_path(self):
        """Default catalog path is applied."""
        result = create_recording_trading_node()

        assert result.streaming.catalog_path == DEFAULT_CATALOG_PATH

    def test_custom_catalog_path(self):
        """Custom catalog path is applied."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_path = str(Path(tmpdir) / "custom_catalog")
            result = create_recording_trading_node(catalog_path=custom_path)

            assert result.streaming.catalog_path == custom_path

    def test_testnet_propagated(self):
        """Testnet parameter propagates to data client."""
        result = create_recording_trading_node(testnet=True)

        assert result.data_clients[HYPERLIQUID].testnet is True

    def test_instruments_propagated(self):
        """Instruments parameter propagates to data client."""
        custom_instruments = ["SOL-USD-PERP.HYPERLIQUID"]
        result = create_recording_trading_node(instruments=custom_instruments)

        config = result.data_clients[HYPERLIQUID]
        assert config.instrument_provider.load_ids == custom_instruments

    def test_default_instruments_used(self):
        """Default instruments are used when not specified."""
        result = create_recording_trading_node()

        config = result.data_clients[HYPERLIQUID]
        assert config.instrument_provider.load_ids == DEFAULT_INSTRUMENTS


class TestDefaultCatalogPath:
    """Tests for DEFAULT_CATALOG_PATH constant."""

    def test_is_relative_path(self):
        """Default path is relative."""
        assert not Path(DEFAULT_CATALOG_PATH).is_absolute()

    def test_ends_with_hyperliquid(self):
        """Default path ends with 'hyperliquid' directory."""
        assert Path(DEFAULT_CATALOG_PATH).name == "hyperliquid"
