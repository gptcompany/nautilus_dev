"""
Daily PnL Tracker Contract (Spec 013).

This file defines the public interface for DailyPnLTracker.
Implementation details are in risk/daily_pnl_tracker.py.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nautilus_trader.model.events import Event


class IDailyPnLTracker(ABC):
    """
    Interface for daily PnL tracking and loss limit enforcement.

    Responsibilities:
    1. Track realized PnL from closed positions
    2. Track unrealized PnL from open positions
    3. Enforce daily loss limits
    4. Reset counters at configured time
    """

    @property
    @abstractmethod
    def daily_realized(self) -> Decimal:
        """Return realized PnL for current day."""
        ...

    @property
    @abstractmethod
    def daily_unrealized(self) -> Decimal:
        """Return current unrealized PnL."""
        ...

    @property
    @abstractmethod
    def total_daily_pnl(self) -> Decimal:
        """Return total daily PnL (realized + unrealized)."""
        ...

    @property
    @abstractmethod
    def limit_triggered(self) -> bool:
        """Return whether daily loss limit has been triggered."""
        ...

    @property
    @abstractmethod
    def day_start(self) -> datetime:
        """Return start of current trading day."""
        ...

    @abstractmethod
    def handle_event(self, event: "Event") -> None:
        """
        Process trading events.

        Routes to appropriate handler:
        - PositionClosed → update realized PnL
        - PositionChanged → recalculate unrealized PnL

        Parameters
        ----------
        event : Event
            Trading event from strategy.
        """
        ...

    @abstractmethod
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
        - Publishes to QuestDB
        """
        ...

    @abstractmethod
    def reset(self) -> None:
        """
        Reset daily counters.

        Called automatically at reset_time_utc or manually for testing.
        Resets: daily_realized, limit_triggered, starting_equity
        """
        ...

    @abstractmethod
    def can_trade(self) -> bool:
        """
        Check if trading is allowed.

        Returns
        -------
        bool
            True if limit not triggered, False otherwise.
        """
        ...
