"""
Reconciliation Presets for common scenarios.

This module provides named presets for common reconciliation configurations,
allowing quick selection of validated settings.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from config.reconciliation.config import ReconciliationConfig

if TYPE_CHECKING:
    pass


class ReconciliationPreset(str, Enum):
    """
    Named presets for reconciliation configuration.

    Presets provide validated configurations for common scenarios:
    - CONSERVATIVE: Safe defaults with longer delays (recommended for initial setup)
    - STANDARD: Production-recommended settings (balanced performance and safety)
    - AGGRESSIVE: Fast reconciliation for low-latency environments
    - DISABLED: Reconciliation completely disabled (testing only)
    """

    CONSERVATIVE = "conservative"
    STANDARD = "standard"
    AGGRESSIVE = "aggressive"
    DISABLED = "disabled"

    def to_config(self) -> ReconciliationConfig:
        """
        Create ReconciliationConfig from this preset.

        Returns:
            ReconciliationConfig with preset values.

        Example:
            >>> config = ReconciliationPreset.STANDARD.to_config()
            >>> exec_kwargs = config.to_live_exec_engine_config()
        """
        return _PRESET_CONFIGS[self]


# Preset configuration definitions
_PRESET_CONFIGS: dict[ReconciliationPreset, ReconciliationConfig] = {
    ReconciliationPreset.CONSERVATIVE: ReconciliationConfig(
        enabled=True,
        startup_delay_secs=15.0,
        lookback_mins=120,
        inflight_check_interval_ms=3000,
        inflight_check_threshold_ms=10000,
        inflight_check_retries=10,
        open_check_interval_secs=10.0,
        open_check_lookback_mins=120,
        open_check_threshold_ms=10000,
        purge_closed_orders_interval_mins=15,
        purge_closed_orders_buffer_mins=120,
    ),
    ReconciliationPreset.STANDARD: ReconciliationConfig(
        enabled=True,
        startup_delay_secs=10.0,
        lookback_mins=None,
        inflight_check_interval_ms=2000,
        inflight_check_threshold_ms=5000,
        inflight_check_retries=5,
        open_check_interval_secs=5.0,
        open_check_lookback_mins=60,
        open_check_threshold_ms=5000,
        purge_closed_orders_interval_mins=10,
        purge_closed_orders_buffer_mins=60,
    ),
    ReconciliationPreset.AGGRESSIVE: ReconciliationConfig(
        enabled=True,
        startup_delay_secs=10.0,
        lookback_mins=30,
        inflight_check_interval_ms=1000,
        inflight_check_threshold_ms=2000,
        inflight_check_retries=3,
        open_check_interval_secs=2.0,
        open_check_lookback_mins=60,
        open_check_threshold_ms=2000,
        purge_closed_orders_interval_mins=5,
        purge_closed_orders_buffer_mins=30,
    ),
    ReconciliationPreset.DISABLED: ReconciliationConfig(
        enabled=False,
        startup_delay_secs=10.0,
        lookback_mins=None,
        inflight_check_interval_ms=2000,
        inflight_check_threshold_ms=5000,
        inflight_check_retries=5,
        open_check_interval_secs=None,
        open_check_lookback_mins=60,
        open_check_threshold_ms=5000,
        purge_closed_orders_interval_mins=10,
        purge_closed_orders_buffer_mins=60,
    ),
}


def get_preset_description(preset: ReconciliationPreset) -> str:
    """
    Get human-readable description of a preset.

    Args:
        preset: The preset to describe.

    Returns:
        Description string.
    """
    descriptions = {
        ReconciliationPreset.CONSERVATIVE: (
            "Safe defaults with longer delays and larger lookback windows. "
            "Recommended for initial setup or unstable network conditions."
        ),
        ReconciliationPreset.STANDARD: (
            "Production-recommended settings with balanced performance and safety. "
            "Suitable for most trading scenarios."
        ),
        ReconciliationPreset.AGGRESSIVE: (
            "Fast reconciliation with minimal delays. "
            "For low-latency environments with stable connections."
        ),
        ReconciliationPreset.DISABLED: (
            "Reconciliation completely disabled. For testing only - NOT recommended for production."
        ),
    }
    return descriptions[preset]
