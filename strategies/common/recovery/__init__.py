"""Position Recovery Module (Spec 017).

This module provides position recovery capabilities for NautilusTrader
strategies, enabling seamless state restoration after TradingNode restarts.

Key Components:
- RecoveryConfig: Configuration for recovery behavior
- RecoverableStrategy: Base class with recovery support
- PositionRecoveryProvider: Position loading and reconciliation
- RecoveryEventEmitter: Event emission for monitoring
- RecoveryStateManager: State tracking and persistence
- EventReplayManager: Event replay and synthetic event generation (FR-004)
"""

from strategies.common.recovery.config import RecoveryConfig
from strategies.common.recovery.event_emitter import RecoveryEventEmitter
from strategies.common.recovery.event_replay import EventReplayManager, SyntheticEvent
from strategies.common.recovery.events import (
    IndicatorsReadyEvent,
    IndicatorsWarmingEvent,
    PositionDiscrepancyEvent,
    PositionLoadedEvent,
    PositionReconciledEvent,
    RecoveryCompletedEvent,
    RecoveryEventType,
    RecoveryFailedEvent,
    RecoveryStartedEvent,
    RecoveryTimeoutEvent,
)
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
from strategies.common.recovery.state_manager import RecoveryStateManager

__all__ = [
    # Config
    "RecoveryConfig",
    # Models
    "RecoveryStatus",
    "RecoveryState",
    "PositionSnapshot",
    "IndicatorState",
    "StrategySnapshot",
    # Events
    "RecoveryEventType",
    "RecoveryStartedEvent",
    "PositionLoadedEvent",
    "PositionReconciledEvent",
    "PositionDiscrepancyEvent",
    "IndicatorsWarmingEvent",
    "IndicatorsReadyEvent",
    "RecoveryCompletedEvent",
    "RecoveryFailedEvent",
    "RecoveryTimeoutEvent",
    # Provider
    "PositionRecoveryProvider",
    # Event Emitter
    "RecoveryEventEmitter",
    # Event Replay (FR-004)
    "EventReplayManager",
    "SyntheticEvent",
    # State Manager
    "RecoveryStateManager",
    # Strategy
    "RecoverableStrategy",
    "RecoverableStrategyConfig",
]
