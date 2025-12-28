"""
Unit tests for standalone configuration builders.

Covers: data.py, logging_config.py, risk.py, streaming.py
"""

from __future__ import annotations

from config.data import build_data_engine_config
from config.logging_config import build_logging_config
from config.risk import build_risk_engine_config
from config.streaming import build_streaming_config
from config.models import LoggingSettings, StreamingSettings, TradingNodeSettings


class TestBuildDataEngineConfig:
    """Tests for build_data_engine_config function."""

    def test_returns_data_engine_config(self):
        """build_data_engine_config should return a LiveDataEngineConfig."""
        config = build_data_engine_config()
        assert config is not None

    def test_queue_size(self):
        """Config should have large queue size."""
        config = build_data_engine_config()
        assert config.qsize == 100000

    def test_validate_data_sequence(self):
        """Config should validate data sequence."""
        config = build_data_engine_config()
        assert config.validate_data_sequence is True


class TestBuildLoggingConfig:
    """Tests for build_logging_config function."""

    def test_returns_logging_config(self, valid_logging_settings: LoggingSettings):
        """build_logging_config should return a LoggingConfig."""
        config = build_logging_config(valid_logging_settings)
        assert config is not None

    def test_uses_log_level(self, valid_logging_settings: LoggingSettings):
        """Config should use log level from settings."""
        config = build_logging_config(valid_logging_settings)
        assert config.log_level == valid_logging_settings.log_level

    def test_json_format(self, valid_logging_settings: LoggingSettings):
        """Config should handle JSON format."""
        valid_logging_settings.log_format = "json"
        config = build_logging_config(valid_logging_settings)
        assert config.log_file_format == "json"

    def test_text_format_none(self, valid_logging_settings: LoggingSettings):
        """Config should set None for text format."""
        valid_logging_settings.log_format = "text"
        config = build_logging_config(valid_logging_settings)
        assert config.log_file_format is None


class TestBuildRiskEngineConfig:
    """Tests for build_risk_engine_config function."""

    def test_returns_risk_engine_config(
        self, valid_trading_node_settings: TradingNodeSettings
    ):
        """build_risk_engine_config should return a LiveRiskEngineConfig."""
        config = build_risk_engine_config(valid_trading_node_settings)
        assert config is not None

    def test_bypass_false(self, valid_trading_node_settings: TradingNodeSettings):
        """Config should never bypass risk engine."""
        config = build_risk_engine_config(valid_trading_node_settings)
        assert config.bypass is False

    def test_uses_rate_limits(self, valid_trading_node_settings: TradingNodeSettings):
        """Config should use rate limits from settings."""
        config = build_risk_engine_config(valid_trading_node_settings)
        assert (
            config.max_order_submit_rate
            == valid_trading_node_settings.max_order_submit_rate
        )


class TestBuildStreamingConfig:
    """Tests for build_streaming_config function."""

    def test_returns_streaming_config(
        self, valid_streaming_settings: StreamingSettings
    ):
        """build_streaming_config should return a StreamingConfig."""
        config = build_streaming_config(valid_streaming_settings)
        assert config is not None

    def test_uses_catalog_path(self, valid_streaming_settings: StreamingSettings):
        """Config should use catalog path from settings."""
        config = build_streaming_config(valid_streaming_settings)
        assert config.catalog_path == valid_streaming_settings.catalog_path

    def test_rotation_mode_size(self, valid_streaming_settings: StreamingSettings):
        """Config should handle SIZE rotation mode."""
        valid_streaming_settings.rotation_mode = "SIZE"
        config = build_streaming_config(valid_streaming_settings)
        assert "SIZE" in str(config.rotation_mode)

    def test_rotation_mode_none(self, valid_streaming_settings: StreamingSettings):
        """Config should handle NONE rotation mode."""
        valid_streaming_settings.rotation_mode = "NONE"
        config = build_streaming_config(valid_streaming_settings)
        assert "NO_ROTATION" in str(config.rotation_mode)
