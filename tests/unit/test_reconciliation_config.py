"""
Unit tests for ReconciliationConfig.

Tests cover:
- Default values (T011)
- Field validation (T012, T018, T020, T021, T024, T025)
- Conversion to LiveExecEngineConfig (T013)
"""

import pytest

from config.reconciliation.config import ReconciliationConfig
from config.reconciliation.presets import ReconciliationPreset


class TestReconciliationConfigDefaults:
    """T011: Test ReconciliationConfig default values."""

    def test_default_values(self):
        """Verify all default values match spec."""
        config = ReconciliationConfig()

        # Startup defaults
        assert config.enabled is True
        assert config.startup_delay_secs == 10.0
        assert config.lookback_mins is None

        # In-flight defaults
        assert config.inflight_check_interval_ms == 2000
        assert config.inflight_check_threshold_ms == 5000
        assert config.inflight_check_retries == 5

        # Open check defaults
        assert config.open_check_interval_secs == 5.0
        assert config.open_check_lookback_mins == 60
        assert config.open_check_threshold_ms == 5000

        # Purge defaults
        assert config.purge_closed_orders_interval_mins == 10
        assert config.purge_closed_orders_buffer_mins == 60

    def test_config_is_immutable(self):
        """Config should be frozen (immutable)."""
        config = ReconciliationConfig()
        with pytest.raises(Exception):  # ValidationError for frozen model
            config.enabled = False


class TestReconciliationConfigValidation:
    """T012: Test ReconciliationConfig validation."""

    def test_startup_delay_minimum(self):
        """Startup delay must be >= 10.0 seconds (T018)."""
        # Valid: exactly 10.0
        config = ReconciliationConfig(startup_delay_secs=10.0)
        assert config.startup_delay_secs == 10.0

        # Valid: above minimum
        config = ReconciliationConfig(startup_delay_secs=15.0)
        assert config.startup_delay_secs == 15.0

        # Invalid: below minimum
        with pytest.raises(ValueError):
            ReconciliationConfig(startup_delay_secs=9.9)

        with pytest.raises(ValueError):
            ReconciliationConfig(startup_delay_secs=0.0)

    def test_open_check_lookback_minimum(self):
        """Open check lookback must be >= 60 minutes (T020)."""
        # Valid: exactly 60
        config = ReconciliationConfig(open_check_lookback_mins=60)
        assert config.open_check_lookback_mins == 60

        # Valid: above minimum
        config = ReconciliationConfig(open_check_lookback_mins=120)
        assert config.open_check_lookback_mins == 120

        # Invalid: below minimum
        with pytest.raises(ValueError):
            ReconciliationConfig(open_check_lookback_mins=59)

        with pytest.raises(ValueError):
            ReconciliationConfig(open_check_lookback_mins=30)

    def test_inflight_threshold_must_exceed_interval(self):
        """In-flight threshold must be >= interval (T025)."""
        # Valid: threshold equals interval
        config = ReconciliationConfig(
            inflight_check_interval_ms=2000,
            inflight_check_threshold_ms=2000,
        )
        assert config.inflight_check_threshold_ms >= config.inflight_check_interval_ms

        # Valid: threshold exceeds interval
        config = ReconciliationConfig(
            inflight_check_interval_ms=2000,
            inflight_check_threshold_ms=5000,
        )
        assert config.inflight_check_threshold_ms >= config.inflight_check_interval_ms

        # Invalid: threshold below interval
        with pytest.raises(ValueError, match="inflight_check_threshold_ms"):
            ReconciliationConfig(
                inflight_check_interval_ms=5000,
                inflight_check_threshold_ms=2000,
            )

    def test_inflight_check_interval_minimum(self):
        """In-flight check interval must be >= 1000ms (T024)."""
        # Valid: exactly 1000
        config = ReconciliationConfig(inflight_check_interval_ms=1000)
        assert config.inflight_check_interval_ms == 1000

        # Invalid: below minimum
        with pytest.raises(ValueError):
            ReconciliationConfig(inflight_check_interval_ms=999)

    def test_inflight_check_threshold_minimum(self):
        """In-flight check threshold must be >= 1000ms (T024)."""
        # Valid: exactly 1000
        config = ReconciliationConfig(
            inflight_check_interval_ms=1000,
            inflight_check_threshold_ms=1000,
        )
        assert config.inflight_check_threshold_ms == 1000

        # Invalid: below minimum
        with pytest.raises(ValueError):
            ReconciliationConfig(inflight_check_threshold_ms=999)

    def test_inflight_check_retries_minimum(self):
        """In-flight check retries must be >= 1 (T024)."""
        # Valid: exactly 1
        config = ReconciliationConfig(inflight_check_retries=1)
        assert config.inflight_check_retries == 1

        # Invalid: below minimum
        with pytest.raises(ValueError):
            ReconciliationConfig(inflight_check_retries=0)

    def test_open_check_interval_minimum(self):
        """Open check interval must be >= 1.0 seconds (T020)."""
        # Valid: exactly 1.0
        config = ReconciliationConfig(open_check_interval_secs=1.0)
        assert config.open_check_interval_secs == 1.0

        # Valid: None (disabled)
        config = ReconciliationConfig(open_check_interval_secs=None)
        assert config.open_check_interval_secs is None

        # Invalid: below minimum
        with pytest.raises(ValueError):
            ReconciliationConfig(open_check_interval_secs=0.5)

    def test_open_check_threshold_minimum(self):
        """Open check threshold must be >= 1000ms (T020)."""
        # Valid: exactly 1000
        config = ReconciliationConfig(open_check_threshold_ms=1000)
        assert config.open_check_threshold_ms == 1000

        # Invalid: below minimum
        with pytest.raises(ValueError):
            ReconciliationConfig(open_check_threshold_ms=999)

    def test_purge_interval_minimum(self):
        """Purge interval must be >= 1 minute."""
        # Valid: exactly 1
        config = ReconciliationConfig(purge_closed_orders_interval_mins=1)
        assert config.purge_closed_orders_interval_mins == 1

        # Invalid: below minimum
        with pytest.raises(ValueError):
            ReconciliationConfig(purge_closed_orders_interval_mins=0)

    def test_purge_buffer_minimum(self):
        """Purge buffer must be >= 1 minute."""
        # Valid: exactly 1
        config = ReconciliationConfig(purge_closed_orders_buffer_mins=1)
        assert config.purge_closed_orders_buffer_mins == 1

        # Invalid: below minimum
        with pytest.raises(ValueError):
            ReconciliationConfig(purge_closed_orders_buffer_mins=0)


class TestReconciliationConfigConversion:
    """T013: Test conversion to LiveExecEngineConfig kwargs."""

    def test_to_live_exec_engine_config_returns_dict(self):
        """Conversion returns a dictionary."""
        config = ReconciliationConfig()
        result = config.to_live_exec_engine_config()
        assert isinstance(result, dict)

    def test_to_live_exec_engine_config_contains_all_fields(self):
        """All reconciliation fields are present in output."""
        config = ReconciliationConfig()
        result = config.to_live_exec_engine_config()

        expected_keys = {
            "reconciliation",
            "reconciliation_startup_delay_secs",
            "reconciliation_lookback_mins",
            "inflight_check_interval_ms",
            "inflight_check_threshold_ms",
            "inflight_check_retries",
            "open_check_interval_secs",
            "open_check_lookback_mins",
            "open_check_threshold_ms",
            "purge_closed_orders_interval_mins",
            "purge_closed_orders_buffer_mins",
        }

        assert set(result.keys()) == expected_keys

    def test_to_live_exec_engine_config_values_match(self):
        """Output values match config values."""
        config = ReconciliationConfig(
            enabled=True,
            startup_delay_secs=15.0,
            lookback_mins=120,
            inflight_check_interval_ms=3000,
            inflight_check_threshold_ms=6000,
            inflight_check_retries=3,
            open_check_interval_secs=10.0,
            open_check_lookback_mins=90,
            open_check_threshold_ms=3000,
            purge_closed_orders_interval_mins=5,
            purge_closed_orders_buffer_mins=30,
        )
        result = config.to_live_exec_engine_config()

        assert result["reconciliation"] is True
        assert result["reconciliation_startup_delay_secs"] == 15.0
        assert result["reconciliation_lookback_mins"] == 120
        assert result["inflight_check_interval_ms"] == 3000
        assert result["inflight_check_threshold_ms"] == 6000
        assert result["inflight_check_retries"] == 3
        assert result["open_check_interval_secs"] == 10.0
        assert result["open_check_lookback_mins"] == 90
        assert result["open_check_threshold_ms"] == 3000
        assert result["purge_closed_orders_interval_mins"] == 5
        assert result["purge_closed_orders_buffer_mins"] == 30

    def test_to_live_exec_engine_config_handles_none_values(self):
        """Conversion handles None values correctly."""
        config = ReconciliationConfig(
            lookback_mins=None,
            open_check_interval_secs=None,
        )
        result = config.to_live_exec_engine_config()

        assert result["reconciliation_lookback_mins"] is None
        assert result["open_check_interval_secs"] is None


class TestReconciliationPresets:
    """T021: Test preset configurations."""

    def test_standard_preset_values(self):
        """STANDARD preset has expected values."""
        config = ReconciliationPreset.STANDARD.to_config()

        assert config.enabled is True
        assert config.startup_delay_secs == 10.0
        assert config.lookback_mins is None
        assert config.open_check_interval_secs == 5.0
        assert config.open_check_lookback_mins == 60

    def test_conservative_preset_values(self):
        """CONSERVATIVE preset has longer delays."""
        config = ReconciliationPreset.CONSERVATIVE.to_config()

        assert config.enabled is True
        assert config.startup_delay_secs == 15.0
        assert config.lookback_mins == 120
        assert config.open_check_interval_secs == 10.0
        assert config.open_check_lookback_mins == 120

    def test_aggressive_preset_values(self):
        """AGGRESSIVE preset has shorter intervals."""
        config = ReconciliationPreset.AGGRESSIVE.to_config()

        assert config.enabled is True
        assert config.startup_delay_secs == 10.0
        assert config.lookback_mins == 30
        assert config.open_check_interval_secs == 2.0
        assert config.inflight_check_interval_ms == 1000

    def test_disabled_preset_values(self):
        """DISABLED preset disables reconciliation."""
        config = ReconciliationPreset.DISABLED.to_config()

        assert config.enabled is False
        assert config.open_check_interval_secs is None

    def test_all_presets_produce_valid_configs(self):
        """All presets produce valid configurations."""
        for preset in ReconciliationPreset:
            config = preset.to_config()
            # Should not raise
            result = config.to_live_exec_engine_config()
            assert isinstance(result, dict)

    def test_preset_to_config_returns_reconciliation_config(self):
        """Preset.to_config() returns ReconciliationConfig instance."""
        for preset in ReconciliationPreset:
            config = preset.to_config()
            assert isinstance(config, ReconciliationConfig)
