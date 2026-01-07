"""Recovery Event Emitter (Spec 017).

This module implements the RecoveryEventEmitter for emitting recovery events.
Events are used for logging, monitoring, and alerting.

Implementation Note:
    MVP uses logging-based emission. Future versions may integrate with
    NautilusTrader message bus for pub/sub event distribution.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import TYPE_CHECKING

from strategies.common.recovery.events import (
    IndicatorsReadyEvent,
    IndicatorsWarmingEvent,
    PositionDiscrepancyEvent,
    PositionLoadedEvent,
    PositionReconciledEvent,
    RecoveryCompletedEvent,
    RecoveryFailedEvent,
    RecoveryStartedEvent,
    RecoveryTimeoutEvent,
)

if TYPE_CHECKING:
    from pydantic import BaseModel


# Module logger
_log = logging.getLogger(__name__)


def _now_ns() -> int:
    """Get current time in nanoseconds."""
    return int(time.time() * 1_000_000_000)


class RecoveryEventEmitter:
    """Emitter for recovery events.

    Provides methods to emit recovery events for monitoring and alerting.
    MVP implementation logs events; can be extended for message bus integration.

    Attributes:
        trader_id: Trader identifier for all emitted events.
        logger: Logger instance for event output.

    Example:
        >>> emitter = RecoveryEventEmitter(trader_id="TRADER-001")
        >>> emitter.emit_recovery_started(cached_positions_count=3)
        >>> emitter.emit_position_loaded(
        ...     instrument_id="BTCUSDT-PERP.BINANCE",
        ...     side="LONG",
        ...     quantity="1.5",
        ...     avg_entry_price="42000.00",
        ... )
        >>> emitter.emit_recovery_completed(
        ...     positions_recovered=3,
        ...     discrepancies_resolved=1,
        ...     total_duration_ms=1500.5,
        ...     strategies_ready=2,
        ... )
    """

    def __init__(
        self,
        trader_id: str,
        logger: logging.Logger | None = None,
        on_event: Callable[[BaseModel], None] | None = None,
    ) -> None:
        """Initialize the RecoveryEventEmitter.

        Args:
            trader_id: Trader identifier for all emitted events.
            logger: Optional custom logger. If None, uses module logger.
            on_event: Optional callback invoked for each emitted event.
                     Useful for message bus integration or testing.
        """
        self._trader_id = trader_id
        self._log = logger or _log
        self._on_event = on_event

    @property
    def trader_id(self) -> str:
        """Trader identifier for all emitted events."""
        return self._trader_id

    def _emit(self, event: BaseModel) -> None:
        """Emit an event via logging and optional callback.

        Args:
            event: The Pydantic event model to emit.
        """
        # Log the event as JSON for structured logging
        self._log.info(
            "Recovery event: %s",
            event.model_dump_json(),
        )

        # Invoke callback if registered
        if self._on_event is not None:
            self._on_event(event)

    def emit_recovery_started(
        self,
        cached_positions_count: int,
        ts_event: int | None = None,
    ) -> RecoveryStartedEvent:
        """Emit RecoveryStartedEvent when recovery begins.

        Args:
            cached_positions_count: Number of positions in cache.
            ts_event: Event timestamp (nanoseconds). If None, uses current time.

        Returns:
            The emitted event.
        """
        event = RecoveryStartedEvent(
            trader_id=self._trader_id,
            ts_event=ts_event or _now_ns(),
            cached_positions_count=cached_positions_count,
        )
        self._emit(event)
        return event

    def emit_position_loaded(
        self,
        instrument_id: str,
        side: str,
        quantity: str,
        avg_entry_price: str,
        ts_event: int | None = None,
    ) -> PositionLoadedEvent:
        """Emit PositionLoadedEvent when a position is loaded from cache.

        Args:
            instrument_id: Position instrument ID.
            side: Position side (LONG/SHORT).
            quantity: Position quantity as string.
            avg_entry_price: Average entry price as string.
            ts_event: Event timestamp (nanoseconds). If None, uses current time.

        Returns:
            The emitted event.
        """
        event = PositionLoadedEvent(
            trader_id=self._trader_id,
            ts_event=ts_event or _now_ns(),
            instrument_id=instrument_id,
            side=side,
            quantity=quantity,
            avg_entry_price=avg_entry_price,
        )
        self._emit(event)
        return event

    def emit_position_reconciled(
        self,
        instrument_id: str,
        cached_quantity: str,
        exchange_quantity: str,
        reconciled: bool,
        ts_event: int | None = None,
    ) -> PositionReconciledEvent:
        """Emit PositionReconciledEvent when a position is reconciled.

        Args:
            instrument_id: Position instrument ID.
            cached_quantity: Quantity from cache.
            exchange_quantity: Quantity from exchange.
            reconciled: Whether reconciliation succeeded.
            ts_event: Event timestamp (nanoseconds). If None, uses current time.

        Returns:
            The emitted event.
        """
        event = PositionReconciledEvent(
            trader_id=self._trader_id,
            ts_event=ts_event or _now_ns(),
            instrument_id=instrument_id,
            cached_quantity=cached_quantity,
            exchange_quantity=exchange_quantity,
            reconciled=reconciled,
        )
        self._emit(event)
        return event

    def emit_position_discrepancy(
        self,
        instrument_id: str,
        resolution: str,
        cached_side: str | None = None,
        exchange_side: str | None = None,
        cached_quantity: str | None = None,
        exchange_quantity: str | None = None,
        ts_event: int | None = None,
    ) -> PositionDiscrepancyEvent:
        """Emit PositionDiscrepancyEvent when cache and exchange differ.

        Args:
            instrument_id: Position instrument ID.
            resolution: How discrepancy was resolved.
            cached_side: Side from cache (optional).
            exchange_side: Side from exchange (optional).
            cached_quantity: Quantity from cache (optional).
            exchange_quantity: Quantity from exchange (optional).
            ts_event: Event timestamp (nanoseconds). If None, uses current time.

        Returns:
            The emitted event.
        """
        event = PositionDiscrepancyEvent(
            trader_id=self._trader_id,
            ts_event=ts_event or _now_ns(),
            instrument_id=instrument_id,
            cached_side=cached_side,
            exchange_side=exchange_side,
            cached_quantity=cached_quantity,
            exchange_quantity=exchange_quantity,
            resolution=resolution,
        )
        self._emit(event)
        return event

    def emit_indicators_warming(
        self,
        strategy_id: str,
        indicator_count: int,
        lookback_days: int,
        ts_event: int | None = None,
    ) -> IndicatorsWarmingEvent:
        """Emit IndicatorsWarmingEvent when indicator warmup begins.

        Args:
            strategy_id: Strategy identifier.
            indicator_count: Number of indicators to warm.
            lookback_days: Historical data lookback in days.
            ts_event: Event timestamp (nanoseconds). If None, uses current time.

        Returns:
            The emitted event.
        """
        event = IndicatorsWarmingEvent(
            trader_id=self._trader_id,
            strategy_id=strategy_id,
            ts_event=ts_event or _now_ns(),
            indicator_count=indicator_count,
            lookback_days=lookback_days,
        )
        self._emit(event)
        return event

    def emit_warmup_complete(
        self,
        strategy_id: str,
        warmup_duration_ms: float,
        bars_processed: int,
        ts_event: int | None = None,
    ) -> IndicatorsReadyEvent:
        """Emit IndicatorsReadyEvent when indicator warmup completes.

        Args:
            strategy_id: Strategy identifier.
            warmup_duration_ms: Warmup duration in milliseconds.
            bars_processed: Number of bars processed during warmup.
            ts_event: Event timestamp (nanoseconds). If None, uses current time.

        Returns:
            The emitted event.
        """
        event = IndicatorsReadyEvent(
            trader_id=self._trader_id,
            strategy_id=strategy_id,
            ts_event=ts_event or _now_ns(),
            warmup_duration_ms=warmup_duration_ms,
            bars_processed=bars_processed,
        )
        self._emit(event)
        return event

    def emit_reconciliation_complete(
        self,
        positions_recovered: int,
        discrepancies_resolved: int,
        total_duration_ms: float,
        strategies_ready: int,
        ts_event: int | None = None,
    ) -> RecoveryCompletedEvent:
        """Emit RecoveryCompletedEvent when recovery completes successfully.

        Args:
            positions_recovered: Number of positions recovered.
            discrepancies_resolved: Number of discrepancies resolved.
            total_duration_ms: Total recovery duration in milliseconds.
            strategies_ready: Number of strategies ready for trading.
            ts_event: Event timestamp (nanoseconds). If None, uses current time.

        Returns:
            The emitted event.
        """
        event = RecoveryCompletedEvent(
            trader_id=self._trader_id,
            ts_event=ts_event or _now_ns(),
            positions_recovered=positions_recovered,
            discrepancies_resolved=discrepancies_resolved,
            total_duration_ms=total_duration_ms,
            strategies_ready=strategies_ready,
        )
        self._emit(event)
        return event

    def emit_recovery_failed(
        self,
        error_code: str,
        error_message: str,
        positions_recovered: int,
        recoverable: bool,
        ts_event: int | None = None,
    ) -> RecoveryFailedEvent:
        """Emit RecoveryFailedEvent when recovery fails.

        Args:
            error_code: Error code for categorization.
            error_message: Human-readable error message.
            positions_recovered: Positions recovered before failure.
            recoverable: Whether recovery can be retried.
            ts_event: Event timestamp (nanoseconds). If None, uses current time.

        Returns:
            The emitted event.
        """
        event = RecoveryFailedEvent(
            trader_id=self._trader_id,
            ts_event=ts_event or _now_ns(),
            error_code=error_code,
            error_message=error_message,
            positions_recovered=positions_recovered,
            recoverable=recoverable,
        )
        self._emit(event)
        return event

    def emit_recovery_timeout(
        self,
        timeout_secs: float,
        elapsed_secs: float,
        positions_recovered: int,
        ts_event: int | None = None,
    ) -> RecoveryTimeoutEvent:
        """Emit RecoveryTimeoutEvent when recovery exceeds max time.

        Args:
            timeout_secs: Configured timeout in seconds.
            elapsed_secs: Actual elapsed time in seconds.
            positions_recovered: Positions recovered before timeout.
            ts_event: Event timestamp (nanoseconds). If None, uses current time.

        Returns:
            The emitted event.
        """
        event = RecoveryTimeoutEvent(
            trader_id=self._trader_id,
            ts_event=ts_event or _now_ns(),
            timeout_secs=timeout_secs,
            elapsed_secs=elapsed_secs,
            positions_recovered=positions_recovered,
        )
        self._emit(event)
        return event
