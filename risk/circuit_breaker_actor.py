"""
Circuit Breaker Actor.

Provides an actor-based interface for integrating CircuitBreaker with
NautilusTrader's event-driven architecture.
"""

from decimal import Decimal
from typing import TYPE_CHECKING

from risk.circuit_breaker import CircuitBreaker
from risk.circuit_breaker_config import CircuitBreakerConfig
from risk.circuit_breaker_state import CircuitBreakerState

if TYPE_CHECKING:
    from nautilus_trader.model.events import AccountState


class CircuitBreakerActor:
    """
    Actor for managing circuit breaker in trading context.

    The CircuitBreakerActor is responsible for:
    1. Maintaining the CircuitBreaker instance
    2. Handling account state updates to track equity
    3. Providing periodic timer checks for safety
    4. Exposing circuit breaker state for strategies

    Parameters
    ----------
    config : CircuitBreakerConfig
        Circuit breaker configuration.

    Example
    -------
    >>> config = CircuitBreakerConfig()
    >>> actor = CircuitBreakerActor(config=config)
    >>> # In strategy on_event:
    >>> if isinstance(event, AccountState):
    ...     actor.handle_account_state(event)
    ...     if not actor.circuit_breaker.can_open_position():
    ...         return  # Skip entry
    """

    def __init__(self, config: CircuitBreakerConfig) -> None:
        self._config = config
        self._circuit_breaker = CircuitBreaker(config=config, portfolio=None)
        self._previous_state = CircuitBreakerState.ACTIVE

    @property
    def circuit_breaker(self) -> CircuitBreaker:
        """Return the underlying circuit breaker."""
        return self._circuit_breaker

    @property
    def check_interval_secs(self) -> int:
        """Return the configured check interval in seconds."""
        return self._config.check_interval_secs

    @property
    def state(self) -> CircuitBreakerState:
        """Return the current circuit breaker state."""
        return self._circuit_breaker.state

    def handle_account_state(self, event: "AccountState") -> None:
        """
        Handle account state update event.

        Extracts total balance from the event and updates circuit breaker.

        Parameters
        ----------
        event : AccountState
            Account state change event from NautilusTrader.
        """
        # Extract total equity from account balances
        if event.balances:
            # Use first balance's total as equity
            # In production, might need to sum all balances
            equity = event.balances[0].total.as_decimal()
            self._circuit_breaker.update(equity=equity)

            # Check for state change
            self._check_state_change()

    def on_timer_check(self) -> None:
        """
        Periodic timer check for circuit breaker state.

        Called by a timer to ensure state is updated even without
        account state events.
        """
        # Recalculate state with current equity values
        self._circuit_breaker._current_drawdown = (
            self._circuit_breaker._calculate_drawdown()
        )
        self._circuit_breaker._update_state(self._circuit_breaker._current_drawdown)

        # Check for state change
        self._check_state_change()

    def _check_state_change(self) -> None:
        """Check if state changed and log if needed."""
        current_state = self._circuit_breaker.state
        if current_state != self._previous_state:
            self._previous_state = current_state
            # In production, would emit metric to QuestDB here

    def can_open_position(self) -> bool:
        """Delegate to circuit breaker."""
        return self._circuit_breaker.can_open_position()

    def position_size_multiplier(self) -> Decimal:
        """Delegate to circuit breaker."""
        return self._circuit_breaker.position_size_multiplier()

    def reset(self) -> None:
        """Delegate to circuit breaker."""
        self._circuit_breaker.reset()
