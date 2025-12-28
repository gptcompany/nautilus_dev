"""
Risk Management Module.

Provides automatic stop-loss and position limit management for NautilusTrader strategies.

Public API
----------
RiskConfig
    Configuration for risk management behavior.
RiskManager
    Runtime risk manager attached to strategy.
StopLossType
    Enum for stop order types (market/limit/emulated).
TrailingOffsetType
    Enum for trailing stop distance measurement.

Examples
--------
>>> from decimal import Decimal
>>> from risk import RiskConfig, RiskManager
>>> config = RiskConfig(stop_loss_pct=Decimal("0.02"))
"""

from risk.config import RiskConfig, StopLossType, TrailingOffsetType
from risk.manager import RiskManager

__all__ = [
    "RiskConfig",
    "RiskManager",
    "StopLossType",
    "TrailingOffsetType",
]
