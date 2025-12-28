"""
LiveDataEngineConfig builder (T025).

Builds NautilusTrader LiveDataEngineConfig.
"""

from __future__ import annotations

from nautilus_trader.config import LiveDataEngineConfig


def build_data_engine_config() -> LiveDataEngineConfig:
    """
    Build LiveDataEngineConfig with production settings.

    Returns
    -------
    LiveDataEngineConfig
        NautilusTrader live data engine configuration.

    Notes
    -----
    - Large queue (100000) prevents data loss during spikes
    - validate_data_sequence catches data issues early
    - time_bars_timestamp_on_close for accurate bar timing
    """
    return LiveDataEngineConfig(
        qsize=100000,
        time_bars_build_with_no_updates=True,
        time_bars_timestamp_on_close=True,
        validate_data_sequence=True,
    )
