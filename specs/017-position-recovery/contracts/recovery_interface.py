"""Position Recovery Interface Contracts (Spec 017).

This module defines the abstract interfaces for position recovery components.
These contracts ensure consistent behavior across implementations.
"""

from abc import ABC, abstractmethod
from typing import Callable

from nautilus_trader.model.identifiers import InstrumentId, TraderId
from nautilus_trader.model.position import Position


class PositionRecoveryProvider(ABC):
    """Interface for position recovery data providers."""

    @abstractmethod
    def get_cached_positions(self, trader_id: TraderId) -> list[Position]:
        """Load positions from cache.

        Args:
            trader_id: The trader identifier.

        Returns:
            List of cached positions.
        """

    @abstractmethod
    def get_exchange_positions(self, trader_id: TraderId) -> list[Position]:
        """Query current positions from exchange.

        Args:
            trader_id: The trader identifier.

        Returns:
            List of positions reported by exchange.
        """

    @abstractmethod
    def reconcile_positions(
        self,
        cached: list[Position],
        exchange: list[Position],
    ) -> tuple[list[Position], list[str]]:
        """Reconcile cached positions with exchange positions.

        Args:
            cached: Positions loaded from cache.
            exchange: Positions from exchange query.

        Returns:
            Tuple of (reconciled_positions, discrepancy_messages).
        """


class StrategyRecoveryHandler(ABC):
    """Interface for strategy-level recovery handling."""

    @abstractmethod
    def on_position_recovered(self, position: Position) -> None:
        """Handle a recovered position.

        Called for each position recovered during startup.

        Args:
            position: The recovered position.
        """

    @abstractmethod
    def on_recovery_complete(self) -> None:
        """Called when all positions have been recovered."""

    @abstractmethod
    def request_warmup_data(
        self,
        instrument_id: InstrumentId,
        lookback_days: int,
        callback: Callable[[], None],
    ) -> None:
        """Request historical data for indicator warmup.

        Args:
            instrument_id: Instrument to request data for.
            lookback_days: Number of days of historical data.
            callback: Function to call when warmup completes.
        """


class RecoveryStateManager(ABC):
    """Interface for managing recovery state persistence."""

    @abstractmethod
    def save_recovery_state(
        self,
        trader_id: TraderId,
        positions_recovered: int,
        indicators_warmed: bool,
    ) -> None:
        """Save current recovery state to cache.

        Args:
            trader_id: The trader identifier.
            positions_recovered: Number of positions recovered.
            indicators_warmed: Whether indicator warmup is complete.
        """

    @abstractmethod
    def load_recovery_state(self, trader_id: TraderId) -> dict | None:
        """Load recovery state from cache.

        Args:
            trader_id: The trader identifier.

        Returns:
            Recovery state dict or None if not found.
        """

    @abstractmethod
    def clear_recovery_state(self, trader_id: TraderId) -> None:
        """Clear recovery state from cache.

        Args:
            trader_id: The trader identifier.
        """


class RecoveryEventEmitter(ABC):
    """Interface for emitting recovery events."""

    @abstractmethod
    def emit_recovery_started(self, trader_id: TraderId) -> None:
        """Emit event when recovery process starts."""

    @abstractmethod
    def emit_position_recovered(
        self,
        trader_id: TraderId,
        position: Position,
    ) -> None:
        """Emit event when a position is recovered."""

    @abstractmethod
    def emit_recovery_completed(
        self,
        trader_id: TraderId,
        positions_count: int,
        duration_ms: float,
    ) -> None:
        """Emit event when recovery completes successfully."""

    @abstractmethod
    def emit_recovery_failed(
        self,
        trader_id: TraderId,
        error: str,
    ) -> None:
        """Emit event when recovery fails."""
