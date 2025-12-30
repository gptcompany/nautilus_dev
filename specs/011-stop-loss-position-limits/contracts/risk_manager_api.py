"""
API Contract: RiskManager

This module defines the public interface for the RiskManager class.
Implementation should adhere to these contracts.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nautilus_trader.model.events import (
        Event,
        PositionOpened,
        PositionClosed,
        PositionChanged,
    )
    from nautilus_trader.model.identifiers import ClientOrderId, PositionId
    from nautilus_trader.model.objects import Price
    from nautilus_trader.model.orders import Order
    from nautilus_trader.model.position import Position
    from nautilus_trader.trading.strategy import Strategy

    from .config import RiskConfig


class IRiskManager(ABC):
    """
    Interface for risk management operations.

    The RiskManager is responsible for:
    1. Generating stop-loss orders when positions open
    2. Canceling stop-loss orders when positions close
    3. Updating trailing stops on position changes
    4. Validating orders against position limits
    """

    @abstractmethod
    def __init__(self, config: "RiskConfig", strategy: "Strategy") -> None:
        """
        Initialize the risk manager.

        Parameters
        ----------
        config : RiskConfig
            Risk management configuration.
        strategy : Strategy
            The parent strategy instance (for order submission).
        """
        ...

    @property
    @abstractmethod
    def config(self) -> "RiskConfig":
        """Return the risk configuration."""
        ...

    @property
    @abstractmethod
    def active_stops(self) -> dict["PositionId", "ClientOrderId"]:
        """Return mapping of position IDs to their stop order IDs."""
        ...

    @abstractmethod
    def handle_event(self, event: "Event") -> None:
        """
        Route position events to appropriate handlers.

        Supported events:
        - PositionOpened: Creates stop-loss order
        - PositionClosed: Cancels stop-loss order
        - PositionChanged: Updates trailing stop

        Parameters
        ----------
        event : Event
            The event to handle.
        """
        ...

    @abstractmethod
    def validate_order(self, order: "Order") -> bool:
        """
        Pre-flight check against position limits.

        Checks:
        1. Order quantity + current position <= max_position_size
        2. Total exposure after order <= max_total_exposure

        Parameters
        ----------
        order : Order
            The order to validate.

        Returns
        -------
        bool
            True if order passes all checks, False otherwise.
        """
        ...

    # --- Private Methods (for documentation) ---

    @abstractmethod
    def _on_position_opened(self, event: "PositionOpened") -> None:
        """
        Generate stop-loss when position opens.

        Steps:
        1. Calculate stop price based on entry and config
        2. Create stop order (market/limit/emulated)
        3. Submit order to strategy
        4. Store mapping in active_stops
        """
        ...

    @abstractmethod
    def _on_position_closed(self, event: "PositionClosed") -> None:
        """
        Cancel stop-loss when position closes.

        Steps:
        1. Look up stop order ID from active_stops
        2. Cancel the stop order
        3. Remove from active_stops mapping
        """
        ...

    @abstractmethod
    def _on_position_changed(self, event: "PositionChanged") -> None:
        """
        Update trailing stop when position changes.

        Only active when config.trailing_stop = True.

        Steps:
        1. Calculate new stop price based on favorable move
        2. Modify existing stop order (or cancel/recreate)
        """
        ...

    @abstractmethod
    def _calculate_stop_price(self, position: "Position") -> "Price":
        """
        Calculate stop price based on position and config.

        For LONG positions:
            stop_price = entry_price * (1 - stop_loss_pct)

        For SHORT positions:
            stop_price = entry_price * (1 + stop_loss_pct)

        Parameters
        ----------
        position : Position
            The position to calculate stop price for.

        Returns
        -------
        Price
            The calculated stop price.
        """
        ...

    @abstractmethod
    def _create_stop_order(self, position: "Position", stop_price: "Price") -> "Order":
        """
        Create appropriate stop order based on config.

        Uses order_factory.stop_market() or stop_limit() based on
        config.stop_loss_type.

        CRITICAL: Always set reduce_only=True to prevent position flip.

        Parameters
        ----------
        position : Position
            The position to protect.
        stop_price : Price
            The trigger price for the stop.

        Returns
        -------
        Order
            The stop order (not yet submitted).
        """
        ...


# --- Type Definitions ---

StopOrderMapping = dict["PositionId", "ClientOrderId"]
"""Mapping of position IDs to their corresponding stop order IDs."""

PositionLimitDict = dict[str, Decimal]
"""Mapping of instrument ID strings to maximum position sizes."""
