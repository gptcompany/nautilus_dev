"""
LiveExecEngineConfig builder (T023).

Builds NautilusTrader LiveExecEngineConfig with reconciliation settings.
"""

from __future__ import annotations

from nautilus_trader.config import LiveExecEngineConfig

from config.models import TradingNodeSettings


def build_exec_engine_config(
    settings: TradingNodeSettings,
) -> LiveExecEngineConfig:
    """
    Build LiveExecEngineConfig with reconciliation settings.

    Parameters
    ----------
    settings : TradingNodeSettings
        Trading node settings with reconciliation configuration.

    Returns
    -------
    LiveExecEngineConfig
        NautilusTrader live execution engine configuration.

    Notes
    -----
    Production requirements:
    - reconciliation_lookback_mins >= 60 (catches orders placed before restart)
    - reconciliation_startup_delay_secs >= 10 (allows venue sync)
    - snapshot_positions = True (enables faster recovery)
    - graceful_shutdown_on_exception = True (prevents data loss)
    """
    return LiveExecEngineConfig(
        # Reconciliation
        reconciliation=True,
        reconciliation_lookback_mins=settings.reconciliation_lookback_mins,
        reconciliation_startup_delay_secs=settings.reconciliation_startup_delay_secs,
        # In-flight order monitoring
        inflight_check_interval_ms=2000,
        inflight_check_threshold_ms=5000,
        inflight_check_retries=5,
        # Continuous open order checks
        open_check_interval_secs=5,
        open_check_lookback_mins=60,
        open_check_threshold_ms=5000,
        open_check_missing_retries=5,
        # Position snapshots
        snapshot_positions=True,
        snapshot_positions_interval_secs=60,
        # Memory management
        purge_closed_orders_interval_mins=15,
        purge_closed_orders_buffer_mins=60,
        purge_closed_positions_interval_mins=15,
        purge_closed_positions_buffer_mins=60,
        # Safety
        graceful_shutdown_on_exception=True,
        qsize=100000,
    )
