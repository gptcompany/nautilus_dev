"""
LiveRiskEngineConfig builder (T026).

Builds NautilusTrader LiveRiskEngineConfig with rate limits.
"""

from __future__ import annotations

from nautilus_trader.config import LiveRiskEngineConfig

from config.models import TradingNodeSettings


def build_risk_engine_config(
    settings: TradingNodeSettings,
) -> LiveRiskEngineConfig:
    """
    Build LiveRiskEngineConfig with rate limits.

    Parameters
    ----------
    settings : TradingNodeSettings
        Trading node settings with rate limit configuration.

    Returns
    -------
    LiveRiskEngineConfig
        NautilusTrader live risk engine configuration.

    Notes
    -----
    - NEVER bypass risk engine in production
    - 100 orders/second is well within exchange limits
    - Binance Futures: 1200/min, Bybit: similar limits
    """
    return LiveRiskEngineConfig(
        bypass=False,
        max_order_submit_rate=settings.max_order_submit_rate,
        max_order_modify_rate=settings.max_order_modify_rate,
    )
