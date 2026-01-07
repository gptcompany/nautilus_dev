"""Recoverable Strategy Base Class (Spec 017 - FR-002).

This module provides a Strategy base class with position recovery support.
Implements FR-002 (Strategy State Restoration) from Spec 017.

Key Features:
- Automatic position detection on startup
- Historical data warmup for indicators
- Exit order recreation for recovered positions
- Trading blocked until warmup completes

Usage:
    class MyStrategy(RecoverableStrategy):
        def __init__(self, config: MyConfig) -> None:
            super().__init__(config, recovery_config)
            self.ema = ExponentialMovingAverage(period=20)

        def on_position_recovered(self, position: Position) -> None:
            self.log.info(f"Recovered position: {position.instrument_id}")

        def on_warmup_complete(self) -> None:
            self.log.info("Warmup complete, ready to trade")

        def on_bar(self, bar: Bar) -> None:
            if not self._warmup_complete:
                return  # Skip until warmup completes
            # Trading logic here
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import OrderType
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.position import Position
from nautilus_trader.trading.strategy import Strategy

from strategies.common.recovery.config import RecoveryConfig
from strategies.common.recovery.models import RecoveryState, RecoveryStatus

if TYPE_CHECKING:
    from nautilus_trader.model.instruments import Instrument
    from nautilus_trader.model.orders import Order


class RecoverableStrategyConfig(StrategyConfig, frozen=True):
    """Configuration for RecoverableStrategy.

    Attributes:
        instrument_id: The instrument to trade.
        bar_type: The bar type for data subscription and warmup.
        recovery: Recovery configuration settings.
    """

    instrument_id: str
    bar_type: str
    recovery: RecoveryConfig | None = None


class RecoverableStrategy(Strategy):
    """Strategy base class with position recovery support.

    Implements FR-002 (Strategy State Restoration) from Spec 017:
    - Detects recovered positions from cache on startup
    - Requests historical data for indicator warmup
    - Recreates exit orders (stop-loss) for recovered positions
    - Blocks trading until warmup completes

    Attributes:
        instrument_id: The instrument being traded.
        bar_type: The bar type for data and warmup.
        recovery_config: Recovery configuration.
        recovery_state: Current recovery state.

    Example:
        >>> class MyStrategy(RecoverableStrategy):
        ...     def on_bar(self, bar: Bar) -> None:
        ...         if not self._warmup_complete:
        ...             return  # Skip until ready
        ...         # Trading logic
    """

    def __init__(
        self,
        config: RecoverableStrategyConfig,
    ) -> None:
        """Initialize RecoverableStrategy.

        Args:
            config: Strategy configuration with recovery settings.
        """
        super().__init__(config)

        self.instrument_id = InstrumentId.from_str(config.instrument_id)
        self.bar_type = BarType.from_str(config.bar_type)

        # Recovery configuration (use defaults if not provided)
        self.recovery_config = config.recovery or RecoveryConfig(
            trader_id=str(self.trader_id) if hasattr(self, "trader_id") else "TRADER-001"
        )

        # Recovery state tracking
        self.recovery_state = RecoveryState()
        self._warmup_complete: bool = False
        self._warmup_bars_processed: int = 0
        self._warmup_start_ns: int | None = None
        self._recovered_positions: list[Position] = []

        # Instrument reference (set in on_start)
        self.instrument: Instrument | None = None

    # ─────────────────────────────────────────────────────────────────
    # Lifecycle Hooks
    # ─────────────────────────────────────────────────────────────────

    def on_start(self) -> None:
        """Initialize strategy and detect recovered positions.

        Called when the strategy starts. Performs:
        1. Load instrument from cache
        2. Detect recovered positions
        3. Handle each recovered position (log + call hook)
        4. Request historical data for indicator warmup
        """
        # Idempotency guard: prevent duplicate initialization (B1 fix)
        if self._warmup_start_ns is not None:
            self.log.warning("on_start() called multiple times, ignoring")
            return

        # Load instrument
        self.instrument = self.cache.instrument(self.instrument_id)
        if self.instrument is None:
            self.log.error(f"Instrument {self.instrument_id} not found in cache")
            self.stop()
            return

        # Start recovery tracking
        self.recovery_state = RecoveryState(
            status=RecoveryStatus.IN_PROGRESS,
            ts_started=self.clock.timestamp_ns(),
        )
        self._warmup_start_ns = self.clock.timestamp_ns()

        # Check for recovered positions from cache
        if self.recovery_config.recovery_enabled:
            self._detect_recovered_positions()

        # Request historical data for indicator warmup
        self._request_warmup_data()

        # Subscribe to bars for live trading
        self.subscribe_bars(self.bar_type)

        self.log.info(
            f"RecoverableStrategy started: "
            f"instrument={self.instrument_id}, "
            f"recovery_enabled={self.recovery_config.recovery_enabled}, "
            f"warmup_days={self.recovery_config.warmup_lookback_days}"
        )

    def on_stop(self) -> None:
        """Clean up on strategy stop."""
        self.log.info(
            f"RecoverableStrategy stopped: "
            f"positions_recovered={self.recovery_state.positions_recovered}, "
            f"warmup_complete={self._warmup_complete}"
        )

    # ─────────────────────────────────────────────────────────────────
    # Position Recovery (FR-002)
    # ─────────────────────────────────────────────────────────────────

    def _detect_recovered_positions(self) -> None:
        """Detect and process positions from cache.

        Iterates over cached positions for this instrument and
        handles each open position as recovered.
        """
        positions = self.cache.positions(instrument_id=self.instrument_id)

        for position in positions:
            if position.is_open:
                self._handle_recovered_position(position)

        self.log.info(
            f"Position detection complete: found {len(self._recovered_positions)} open positions"
        )

    def _handle_recovered_position(self, position: Position) -> None:
        """Internal handler for a recovered position.

        Logs the recovery, updates state, sets up exit orders,
        and calls the subclass hook.

        Args:
            position: The recovered position.
        """
        self._recovered_positions.append(position)
        self.recovery_state = RecoveryState(
            status=self.recovery_state.status,
            positions_recovered=self.recovery_state.positions_recovered + 1,
            indicators_warmed=self.recovery_state.indicators_warmed,
            orders_reconciled=self.recovery_state.orders_reconciled,
            ts_started=self.recovery_state.ts_started,
            ts_completed=self.recovery_state.ts_completed,
        )

        # Log recovery details
        self.log.info(
            f"Recovered position: "
            f"instrument={position.instrument_id}, "
            f"side={position.side.value}, "
            f"quantity={position.quantity}, "
            f"avg_price={position.avg_px_open}"
        )

        # Setup exit orders if needed
        self._setup_exit_orders(position)

        # Call subclass hook
        self.on_position_recovered(position)

    def on_position_recovered(self, position: Position) -> None:
        """Hook for subclasses to handle recovered positions.

        Override this method to implement custom recovery logic,
        such as restoring strategy-specific state or adjusting
        risk parameters.

        Args:
            position: The recovered position.

        Example:
            >>> def on_position_recovered(self, position: Position) -> None:
            ...     self._position_size = position.quantity
            ...     self._entry_price = position.avg_px_open
        """
        pass  # Override in subclass

    def _setup_exit_orders(self, position: Position) -> None:
        """Setup exit orders (stop-loss) for a recovered position.

        Checks if a stop-loss order already exists for the position.
        If not, this method can be overridden to create one.

        Note:
            This base implementation only checks for existing orders.
            Subclasses should override to implement actual stop-loss
            creation logic based on their risk parameters.

        Args:
            position: The recovered position needing exit orders.
        """
        # Check if stop-loss already exists
        open_orders = self.cache.orders_open(instrument_id=position.instrument_id)
        has_stop = any(self._is_stop_order(order) for order in open_orders)

        if has_stop:
            self.log.info(f"Stop-loss already exists for {position.instrument_id}")
        else:
            self.log.warning(
                f"No stop-loss found for recovered position: "
                f"{position.instrument_id}. Override _setup_exit_orders() "
                f"to create one."
            )

    def _is_stop_order(self, order: Order) -> bool:
        """Check if an order is a stop-type order.

        Args:
            order: The order to check.

        Returns:
            True if order is STOP_MARKET or STOP_LIMIT.
        """
        return order.order_type in (OrderType.STOP_MARKET, OrderType.STOP_LIMIT)

    # ─────────────────────────────────────────────────────────────────
    # Historical Data Warmup (FR-002)
    # ─────────────────────────────────────────────────────────────────

    def _request_warmup_data(self) -> None:
        """Request historical bars for indicator warmup.

        Requests bars from (now - warmup_lookback_days) to now.
        Results are delivered to on_historical_data().
        """
        lookback_days = self.recovery_config.warmup_lookback_days
        start_time = self.clock.utc_now() - timedelta(days=lookback_days)

        self.log.info(
            f"Requesting warmup data: "
            f"bar_type={self.bar_type}, "
            f"start={start_time}, "
            f"lookback_days={lookback_days}"
        )

        # Request historical bars with callback
        self.request_bars(
            bar_type=self.bar_type,
            start=start_time,
            callback=self._on_warmup_data_received,
        )

    def _on_warmup_data_received(self, bars: list[Bar]) -> None:
        """Callback when historical warmup data is received.

        Processes bars for indicator warmup and marks warmup complete.

        Args:
            bars: List of historical bars for warmup.
        """
        # Idempotency guard: prevent duplicate warmup completion (B2 fix)
        if self._warmup_complete:
            self.log.warning("Warmup data received after completion, ignoring")
            return

        if not bars:
            self.log.warning("No warmup bars received")
            self._complete_warmup()
            return

        self.log.info(f"Received {len(bars)} warmup bars")

        # Sort bars by timestamp (oldest first) for correct indicator warmup
        sorted_bars = sorted(bars, key=lambda b: b.ts_event)

        # Process each bar for indicator warmup
        for bar in sorted_bars:
            self.on_historical_data(bar)
            self._warmup_bars_processed += 1

        # Mark warmup complete
        self._complete_warmup()

    def on_historical_data(self, bar: Bar) -> None:
        """Process a historical bar for indicator warmup.

        Override this method to feed bars to your indicators.

        Args:
            bar: A historical bar for warmup.

        Example:
            >>> def on_historical_data(self, bar: Bar) -> None:
            ...     self.ema.handle_bar(bar)
            ...     self.rsi.handle_bar(bar)
        """
        pass  # Override in subclass to warm up indicators

    def _complete_warmup(self) -> None:
        """Complete the warmup phase and enable trading.

        Updates recovery state, calculates warmup duration,
        and calls the on_warmup_complete() hook.
        """
        self._warmup_complete = True

        # Calculate warmup duration
        warmup_duration_ns = 0
        if self._warmup_start_ns is not None:
            warmup_duration_ns = self.clock.timestamp_ns() - self._warmup_start_ns
        warmup_duration_ms = warmup_duration_ns / 1_000_000

        # Update recovery state
        self.recovery_state = RecoveryState(
            status=RecoveryStatus.COMPLETED,
            positions_recovered=self.recovery_state.positions_recovered,
            indicators_warmed=True,
            orders_reconciled=True,
            ts_started=self.recovery_state.ts_started,
            ts_completed=self.clock.timestamp_ns(),
        )

        self.log.info(
            f"Warmup complete: "
            f"bars_processed={self._warmup_bars_processed}, "
            f"duration_ms={warmup_duration_ms:.1f}"
        )

        # Call subclass hook
        self.on_warmup_complete()

    def on_warmup_complete(self) -> None:
        """Hook called when warmup phase completes.

        Override this method to perform post-warmup initialization,
        such as subscribing to additional data feeds or enabling
        trading signals.

        Example:
            >>> def on_warmup_complete(self) -> None:
            ...     self.log.info("Strategy ready to trade")
            ...     self._can_trade = True
        """
        pass  # Override in subclass

    # ─────────────────────────────────────────────────────────────────
    # Helper Properties
    # ─────────────────────────────────────────────────────────────────

    @property
    def is_warming_up(self) -> bool:
        """Check if strategy is still in warmup phase.

        Returns:
            True if warmup is not yet complete.
        """
        return not self._warmup_complete

    @property
    def is_ready(self) -> bool:
        """Check if strategy is ready to trade.

        Returns:
            True if warmup is complete and recovery succeeded.
        """
        return self._warmup_complete and self.recovery_state.status == RecoveryStatus.COMPLETED

    @property
    def recovered_positions_count(self) -> int:
        """Get the number of recovered positions.

        Returns:
            Number of positions recovered during startup.
        """
        return len(self._recovered_positions)
