"""
Risk Management Module.

Provides automatic stop-loss, position limit management, and portfolio-level
drawdown protection for NautilusTrader strategies.

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
CircuitBreaker
    Portfolio-level drawdown protection with graduated risk reduction.
CircuitBreakerConfig
    Configuration for circuit breaker thresholds and behavior.
CircuitBreakerState
    State machine states for circuit breaker.

Examples
--------
>>> from decimal import Decimal
>>> from risk import RiskConfig, RiskManager
>>> config = RiskConfig(stop_loss_pct=Decimal("0.02"))

>>> from risk import CircuitBreaker, CircuitBreakerConfig
>>> cb_config = CircuitBreakerConfig(level1_drawdown_pct=Decimal("0.10"))
>>> circuit_breaker = CircuitBreaker(config=cb_config, portfolio=portfolio)
"""

from risk.circuit_breaker import CircuitBreaker
from risk.circuit_breaker_config import CircuitBreakerConfig
from risk.circuit_breaker_state import CircuitBreakerState
from risk.config import RiskConfig, StopLossType, TrailingOffsetType
from risk.manager import RiskManager

__all__ = [
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerState",
    "RiskConfig",
    "RiskManager",
    "StopLossType",
    "TrailingOffsetType",
]
