"""
Unit tests for LiveExecEngineConfig builder (T021-T022).

TDD: RED phase - tests written before implementation.
"""

from __future__ import annotations


from config.execution import build_exec_engine_config
from config.models import TradingNodeSettings


class TestBuildExecEngineConfig:
    """Tests for build_exec_engine_config function."""

    def test_returns_exec_engine_config(self, valid_trading_node_settings: TradingNodeSettings):
        """build_exec_engine_config should return a LiveExecEngineConfig."""
        config = build_exec_engine_config(valid_trading_node_settings)
        assert config is not None

    def test_reconciliation_enabled(self, valid_trading_node_settings: TradingNodeSettings):
        """Reconciliation should be enabled by default."""
        config = build_exec_engine_config(valid_trading_node_settings)
        assert config.reconciliation is True

    def test_reconciliation_lookback_from_settings(
        self, valid_trading_node_settings: TradingNodeSettings
    ):
        """Reconciliation lookback should use settings value."""
        config = build_exec_engine_config(valid_trading_node_settings)
        assert (
            config.reconciliation_lookback_mins
            == valid_trading_node_settings.reconciliation_lookback_mins
        )

    def test_reconciliation_startup_delay_from_settings(
        self, valid_trading_node_settings: TradingNodeSettings
    ):
        """Reconciliation startup delay should use settings value."""
        config = build_exec_engine_config(valid_trading_node_settings)
        assert (
            config.reconciliation_startup_delay_secs
            == valid_trading_node_settings.reconciliation_startup_delay_secs
        )


class TestReconciliationParameterValidation:
    """Tests for reconciliation parameter validation (T022)."""

    def test_lookback_minimum_60_minutes(self, valid_trading_node_settings: TradingNodeSettings):
        """Lookback must be at least 60 minutes."""
        config = build_exec_engine_config(valid_trading_node_settings)
        assert config.reconciliation_lookback_mins >= 60

    def test_startup_delay_minimum_10_seconds(
        self, valid_trading_node_settings: TradingNodeSettings
    ):
        """Startup delay must be at least 10 seconds."""
        config = build_exec_engine_config(valid_trading_node_settings)
        assert config.reconciliation_startup_delay_secs >= 10.0


class TestInflightOrderMonitoring:
    """Tests for in-flight order monitoring settings."""

    def test_inflight_check_interval(self, valid_trading_node_settings: TradingNodeSettings):
        """In-flight check interval should be 2000ms."""
        config = build_exec_engine_config(valid_trading_node_settings)
        assert config.inflight_check_interval_ms == 2000

    def test_inflight_check_threshold(self, valid_trading_node_settings: TradingNodeSettings):
        """In-flight check threshold should be 5000ms."""
        config = build_exec_engine_config(valid_trading_node_settings)
        assert config.inflight_check_threshold_ms == 5000

    def test_inflight_check_retries(self, valid_trading_node_settings: TradingNodeSettings):
        """In-flight check retries should be 5."""
        config = build_exec_engine_config(valid_trading_node_settings)
        assert config.inflight_check_retries == 5


class TestOpenOrderChecks:
    """Tests for continuous open order check settings."""

    def test_open_check_interval(self, valid_trading_node_settings: TradingNodeSettings):
        """Open check interval should be 5 seconds."""
        config = build_exec_engine_config(valid_trading_node_settings)
        assert config.open_check_interval_secs == 5

    def test_open_check_lookback(self, valid_trading_node_settings: TradingNodeSettings):
        """Open check lookback should be 60 minutes."""
        config = build_exec_engine_config(valid_trading_node_settings)
        assert config.open_check_lookback_mins == 60


class TestPositionSnapshots:
    """Tests for position snapshot settings."""

    def test_snapshot_positions_enabled(self, valid_trading_node_settings: TradingNodeSettings):
        """Position snapshots should be enabled."""
        config = build_exec_engine_config(valid_trading_node_settings)
        assert config.snapshot_positions is True

    def test_snapshot_interval(self, valid_trading_node_settings: TradingNodeSettings):
        """Snapshot interval should be 60 seconds."""
        config = build_exec_engine_config(valid_trading_node_settings)
        assert config.snapshot_positions_interval_secs == 60


class TestMemoryManagement:
    """Tests for memory purge settings."""

    def test_purge_closed_orders_interval(self, valid_trading_node_settings: TradingNodeSettings):
        """Purge closed orders interval should be 15 minutes."""
        config = build_exec_engine_config(valid_trading_node_settings)
        assert config.purge_closed_orders_interval_mins == 15

    def test_purge_closed_orders_buffer(self, valid_trading_node_settings: TradingNodeSettings):
        """Purge closed orders buffer should be 60 minutes."""
        config = build_exec_engine_config(valid_trading_node_settings)
        assert config.purge_closed_orders_buffer_mins == 60


class TestSafetySettings:
    """Tests for safety settings."""

    def test_graceful_shutdown_enabled(self, valid_trading_node_settings: TradingNodeSettings):
        """Graceful shutdown on exception should be enabled."""
        config = build_exec_engine_config(valid_trading_node_settings)
        assert config.graceful_shutdown_on_exception is True

    def test_queue_size(self, valid_trading_node_settings: TradingNodeSettings):
        """Queue size should be 100000."""
        config = build_exec_engine_config(valid_trading_node_settings)
        assert config.qsize == 100000
