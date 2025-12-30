"""
API Contract: BaseEvolveStrategy

This file defines the interface contract for evolvable strategy base class.
Implementation must adhere to this contract.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol

from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.trading.strategy import Strategy


@dataclass(frozen=True)
class EquityPoint:
    """Single equity curve entry."""

    timestamp: datetime
    equity: float


class BaseEvolveConfig(StrategyConfig, frozen=True):
    """Configuration for evolvable strategy base class."""

    instrument_id: InstrumentId
    bar_type: BarType
    trade_size: Decimal


class BaseEvolveStrategyProtocol(Protocol):
    """
    Protocol defining the required interface for evolvable strategies.

    All evolvable strategies MUST implement this interface.
    """

    # === Lifecycle Methods (inherited from Strategy) ===

    def on_start(self) -> None:
        """Initialize strategy: get instrument, register indicators, subscribe to bars."""
        ...

    def on_bar(self, bar: Bar) -> None:
        """Handle bar: call _on_bar_evolved, record equity."""
        ...

    def on_stop(self) -> None:
        """Cleanup: cancel orders, close positions."""
        ...

    def on_reset(self) -> None:
        """Reset: clear indicators and equity curve."""
        ...

    # === Abstract Methods (must be implemented) ===

    def _on_bar_evolved(self, bar: Bar) -> None:
        """
        Handle bar with evolvable decision logic.

        This method MUST contain EVOLVE-BLOCK markers:

            # === EVOLVE-BLOCK: decision_logic ===
            # Trading logic here
            # === END EVOLVE-BLOCK ===

        Everything outside the markers is fixed infrastructure.
        Everything inside is subject to mutation.
        """
        ...

    # === Equity Tracking ===

    def get_equity_curve(self) -> list[EquityPoint]:
        """
        Return recorded equity curve.

        Returns:
            List of EquityPoint entries, one per bar processed.
        """
        ...

    # === Order Helpers ===

    def _enter_long(self, quantity: Decimal) -> None:
        """
        Submit market buy order.

        If currently short, closes short position first.

        Args:
            quantity: Size to buy (in base currency units)
        """
        ...

    def _enter_short(self, quantity: Decimal) -> None:
        """
        Submit market sell order.

        If currently long, closes long position first.

        Args:
            quantity: Size to sell (in base currency units)
        """
        ...

    def _close_position(self) -> None:
        """Close all positions for configured instrument."""
        ...

    def _get_position_size(self) -> Decimal:
        """
        Get current net position size.

        Returns:
            Positive for long, negative for short, zero for flat.
        """
        ...

    def _get_equity(self) -> float:
        """
        Get current account equity.

        Returns:
            Account balance + unrealized PnL
        """
        ...


# === Abstract Base Class ===


class BaseEvolveStrategy(Strategy, ABC):
    """
    Abstract base class for evolvable strategies.

    Provides:
    - Equity curve tracking
    - Order helper methods
    - Lifecycle management

    Subclasses must implement:
    - _on_bar_evolved(bar): Contains EVOLVE-BLOCK markers
    """

    def __init__(self, config: BaseEvolveConfig) -> None:
        super().__init__(config)
        self.instrument = None
        self._equity_curve: list[EquityPoint] = []

    @abstractmethod
    def _on_bar_evolved(self, bar: Bar) -> None:
        """Handle bar with evolvable decision logic. Must contain EVOLVE-BLOCK markers."""
        ...

    def get_equity_curve(self) -> list[EquityPoint]:
        """Return recorded equity curve."""
        return self._equity_curve.copy()

    # Order helpers defined in implementation
    # _enter_long, _enter_short, _close_position, _get_position_size, _get_equity
