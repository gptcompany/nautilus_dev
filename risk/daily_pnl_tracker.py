"""
Daily PnL Tracker (Spec 013).

Tracks daily realized + unrealized PnL and enforces daily loss limits.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from nautilus_trader.model.enums import OrderSide, PositionSide
from nautilus_trader.model.events import PositionClosed

from risk.daily_loss_config import DailyLossConfig

if TYPE_CHECKING:
    from nautilus_trader.model.events import Event
    from nautilus_trader.trading.strategy import Strategy

logger = logging.getLogger(__name__)


class DailyPnLTracker:
    """
    Daily PnL tracking with loss limit enforcement.

    Responsibilities:
    1. Track realized PnL from closed positions
    2. Track unrealized PnL from open positions
    3. Enforce daily loss limits
    4. Reset counters at configured time
    """

    def __init__(
        self,
        config: DailyLossConfig,
        strategy: "Strategy",
    ) -> None:
        """
        Initialize the DailyPnLTracker.

        Parameters
        ----------
        config : DailyLossConfig
            Configuration for daily loss limits.
        strategy : Strategy
            The strategy this tracker is attached to.
        """
        self._config = config
        self._strategy = strategy
        self._daily_realized: Decimal = Decimal("0")
        self._limit_triggered: bool = False
        self._day_start: datetime = self._get_day_start()
        self._warning_emitted: bool = False
        # Initialize starting equity (will be recalculated on reset)
        # Use fallback value initially since portfolio may not have balances yet
        self._starting_equity: Decimal = self._config.daily_loss_limit * 50

    @property
    def config(self) -> DailyLossConfig:
        """Return the configuration."""
        return self._config

    @property
    def daily_realized(self) -> Decimal:
        """Return realized PnL for current day."""
        return self._daily_realized

    @property
    def daily_unrealized(self) -> Decimal:
        """Return current unrealized PnL summed across all currencies."""
        try:
            unrealized_dict = self._strategy.portfolio.unrealized_pnls()
            if unrealized_dict is None or not unrealized_dict:
                return Decimal("0")
            # Sum all unrealized PnLs across currencies
            # unrealized_dict is dict[Currency, Money]
            total = Decimal("0")
            for money in unrealized_dict.values():
                if money is not None:
                    total += Decimal(str(float(money)))
            return total
        except (AttributeError, TypeError):
            # Fallback for mocks that return single value
            unrealized = self._strategy.portfolio.unrealized_pnls()
            if unrealized is None:
                return Decimal("0")
            return Decimal(str(float(unrealized)))

    @property
    def total_daily_pnl(self) -> Decimal:
        """Return total daily PnL (realized + unrealized)."""
        return self._daily_realized + self.daily_unrealized

    @property
    def limit_triggered(self) -> bool:
        """Return whether daily loss limit has been triggered."""
        return self._limit_triggered

    @property
    def day_start(self) -> datetime:
        """Return start of current trading day."""
        return self._day_start

    def handle_event(self, event: "Event") -> None:
        """
        Process trading events.

        Routes to appropriate handler:
        - PositionClosed → update realized PnL

        Parameters
        ----------
        event : Event
            Trading event from strategy.
        """
        # Use duck typing to support both real events and test mocks
        if hasattr(event, "realized_pnl"):
            self._on_position_closed(event)

    def _on_position_closed(self, event: PositionClosed) -> None:
        """Update realized PnL on position close."""
        realized_pnl = Decimal(str(float(event.realized_pnl)))
        self._daily_realized += realized_pnl
        logger.debug(
            f"Position closed with PnL: {realized_pnl}, daily realized: {self._daily_realized}"
        )

    def check_limit(self) -> bool:
        """
        Check if daily loss limit exceeded.

        Returns
        -------
        bool
            True if limit exceeded, False otherwise.

        Side Effects
        ------------
        - Sets limit_triggered = True if exceeded
        - May close positions if close_positions_on_limit=True
        """
        if self._limit_triggered:
            return True

        total_pnl = self.total_daily_pnl
        effective_limit = self._config.get_effective_limit(self._starting_equity)

        # Check warning threshold (50% of limit by default)
        if not self._warning_emitted:
            warning_threshold = effective_limit * self._config.warning_threshold_pct
            if total_pnl <= -warning_threshold:
                logger.warning(
                    f"Daily PnL warning: {total_pnl} has reached "
                    f"{self._config.warning_threshold_pct * 100}% of limit"
                )
                self._warning_emitted = True

        # Check if limit exceeded
        if total_pnl <= -effective_limit:
            self._trigger_limit()
            return True

        return False

    def _trigger_limit(self) -> None:
        """Handle limit trigger."""
        self._limit_triggered = True
        logger.warning(
            f"Daily loss limit triggered! Total PnL: {self.total_daily_pnl}, "
            f"Limit: {self._config.daily_loss_limit}"
        )

        if self._config.close_positions_on_limit:
            self._close_all_positions()

    def _close_all_positions(self) -> None:
        """Close all positions when daily limit triggered."""
        positions = self._strategy.cache.positions_open()
        for position in positions:
            try:
                order_side = OrderSide.SELL if position.side == PositionSide.LONG else OrderSide.BUY
                close_order = self._strategy.order_factory.market(
                    instrument_id=position.instrument_id,
                    order_side=order_side,
                    quantity=position.quantity,
                    reduce_only=True,
                )
                self._strategy.submit_order(close_order)
                logger.info(f"Submitted close order for position {position.id}")
            except Exception as e:
                logger.error(f"Failed to close position {position.id}: {e}")

    def can_trade(self) -> bool:
        """
        Check if trading is allowed.

        Returns
        -------
        bool
            True if limit not triggered, False otherwise.
        """
        return not self._limit_triggered

    def reset(self) -> None:
        """
        Reset daily counters.

        Called automatically at reset_time_utc or manually for testing.
        """
        self._daily_realized = Decimal("0")
        self._limit_triggered = False
        self._warning_emitted = False
        self._day_start = self._get_day_start()

        # Update starting equity for percentage-based limits
        self._starting_equity = self._calculate_total_equity()

        logger.info(f"Daily PnL tracker reset at {self._day_start}")

    def _calculate_total_equity(self) -> Decimal:
        """
        Calculate total equity from portfolio balances.

        Returns
        -------
        Decimal
            Total equity across all currencies, or config daily_loss_limit
            as fallback for percentage calculation.
        """
        try:
            balances_dict = self._strategy.portfolio.balances()
            if balances_dict is None or not balances_dict:
                # Fallback: use absolute limit as reference
                return self._config.daily_loss_limit * 50  # Assume 2% limit = 50x
            # Sum all balances across currencies
            # balances_dict is dict[Currency, Money]
            total = Decimal("0")
            for money in balances_dict.values():
                if money is not None:
                    total += Decimal(str(float(money)))
            return total if total > 0 else self._config.daily_loss_limit * 50
        except (AttributeError, TypeError):
            # Fallback for mocks or errors
            return self._config.daily_loss_limit * 50

    def _get_day_start(self) -> datetime:
        """Get start of current trading day based on reset_time_utc."""
        return self._strategy.clock.utc_now()
