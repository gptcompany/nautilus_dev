"""Position Recovery Module (Spec 017).

This module provides position recovery capabilities for NautilusTrader
strategies, enabling seamless state restoration after TradingNode restarts.

Key Components:
- RecoveryConfig: Configuration for recovery behavior
- RecoverableStrategy: Base class with recovery support
- PositionRecoveryProvider: Position loading and reconciliation
- RecoveryEventEmitter: Event emission for monitoring
"""

from strategies.common.recovery.config import RecoveryConfig
from strategies.common.recovery.models import (
    IndicatorState,
    PositionSnapshot,
    RecoveryState,
    RecoveryStatus,
    StrategySnapshot,
)
from strategies.common.recovery.provider import PositionRecoveryProvider
from strategies.common.recovery.recoverable_strategy import (
    RecoverableStrategy,
    RecoverableStrategyConfig,
)

__all__ = [
    # Config
    "RecoveryConfig",
    # Models
    "RecoveryStatus",
    "RecoveryState",
    "PositionSnapshot",
    "IndicatorState",
    "StrategySnapshot",
    # Provider
    "PositionRecoveryProvider",
    # Strategy
    "RecoverableStrategy",
    "RecoverableStrategyConfig",
]
