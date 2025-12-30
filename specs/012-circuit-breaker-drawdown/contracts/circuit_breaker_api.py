"""
API Contract: CircuitBreaker

This module defines the public interface for the CircuitBreaker class.
Implementation should adhere to these contracts.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

    from nautilus_trader.model.events import AccountState
    from nautilus_trader.portfolio.portfolio import Portfolio


class CircuitBreakerState(Enum):
    """
    Circuit breaker state machine states.

    States represent graduated levels of risk reduction based on drawdown.
    """

    ACTIVE = "active"
    """Normal trading - all entries allowed, full position sizes."""

    WARNING = "warning"
    """Drawdown > level1 - entries allowed, reduced position sizes (50%)."""

    REDUCING = "reducing"
    """Drawdown > level2 - no new entries, only exits allowed."""

    HALTED = "halted"
    """Drawdown > level3 - trading halted, manual intervention required."""


class ICircuitBreaker(ABC):
    """
    Interface for circuit breaker operations.

    The CircuitBreaker is responsible for:
    1. Tracking portfolio equity and peak (high water mark)
    2. Calculating current drawdown
    3. Managing state transitions based on drawdown thresholds
    4. Providing position sizing guidance to strategies
    """

    @abstractmethod
    def __init__(
        self,
        config: "CircuitBreakerConfig",
        portfolio: "Portfolio",
    ) -> None:
        """
        Initialize the circuit breaker.

        Parameters
        ----------
        config : CircuitBreakerConfig
            Circuit breaker configuration.
        portfolio : Portfolio
            The portfolio to monitor for equity changes.
        """
        ...

    @property
    @abstractmethod
    def config(self) -> "CircuitBreakerConfig":
        """Return the circuit breaker configuration."""
        ...

    @property
    @abstractmethod
    def state(self) -> CircuitBreakerState:
        """Return the current circuit breaker state."""
        ...

    @property
    @abstractmethod
    def peak_equity(self) -> Decimal:
        """Return the peak equity (high water mark)."""
        ...

    @property
    @abstractmethod
    def current_equity(self) -> Decimal:
        """Return the last known equity value."""
        ...

    @property
    @abstractmethod
    def current_drawdown(self) -> Decimal:
        """
        Return the current drawdown as a decimal.

        Returns
        -------
        Decimal
            Drawdown value (e.g., 0.15 = 15% drawdown).
        """
        ...

    @property
    @abstractmethod
    def last_check(self) -> "datetime":
        """Return the timestamp of the last update."""
        ...

    @abstractmethod
    def update(self) -> None:
        """
        Check current equity and update state.

        Steps:
        1. Get current equity from portfolio
        2. Update peak if current > peak
        3. Calculate drawdown
        4. Transition state if thresholds crossed
        5. Update last_check timestamp
        """
        ...

    @abstractmethod
    def can_open_position(self) -> bool:
        """
        Check if new positions are allowed.

        Returns
        -------
        bool
            True if state is ACTIVE or WARNING, False otherwise.
        """
        ...

    @abstractmethod
    def position_size_multiplier(self) -> Decimal:
        """
        Get position size adjustment based on current state.

        Returns
        -------
        Decimal
            Multiplier to apply to base position size.
            - ACTIVE: 1.0 (100%)
            - WARNING: config.warning_size_multiplier (default 0.5)
            - REDUCING: 0.0
            - HALTED: 0.0
        """
        ...

    @abstractmethod
    def reset(self) -> None:
        """
        Manually reset circuit breaker to ACTIVE state.

        Only valid when:
        - Current state is HALTED
        - config.auto_recovery is False

        Raises
        ------
        ValueError
            If reset called when auto_recovery=True or state != HALTED.
        """
        ...


class ICircuitBreakerActor(ABC):
    """
    Interface for CircuitBreakerActor.

    The actor maintains circuit breaker state and integrates
    with NautilusTrader's event-driven architecture.
    """

    @abstractmethod
    def on_start(self) -> None:
        """
        Start the actor.

        Steps:
        1. Subscribe to account state updates
        2. Set up periodic timer for safety checks
        3. Initialize peak equity from current balance
        """
        ...

    @abstractmethod
    def on_stop(self) -> None:
        """
        Stop the actor.

        Steps:
        1. Cancel timers
        2. Log final state
        """
        ...

    @abstractmethod
    def on_account_state(self, event: "AccountState") -> None:
        """
        Handle account state updates.

        Parameters
        ----------
        event : AccountState
            Account state change event.

        Steps:
        1. Update equity from event
        2. Call circuit_breaker.update()
        3. Emit metric to QuestDB if state changed
        """
        ...


# --- Type Definitions ---

CircuitBreakerMetricDict = dict
"""Dictionary representation of a circuit breaker metric for QuestDB."""
