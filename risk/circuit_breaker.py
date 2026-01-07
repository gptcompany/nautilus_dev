"""
Circuit Breaker Implementation.

Provides portfolio-level drawdown protection by monitoring equity and
enforcing graduated risk reduction as drawdown increases.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from risk.circuit_breaker_config import CircuitBreakerConfig
from risk.circuit_breaker_state import CircuitBreakerState

if TYPE_CHECKING:
    from nautilus_trader.portfolio.portfolio import Portfolio


class CircuitBreaker:
    """
    Global circuit breaker for drawdown protection.

    The CircuitBreaker is responsible for:
    1. Tracking portfolio equity and peak (high water mark)
    2. Calculating current drawdown
    3. Managing state transitions based on drawdown thresholds
    4. Providing position sizing guidance to strategies

    Parameters
    ----------
    config : CircuitBreakerConfig
        Circuit breaker configuration.
    portfolio : Portfolio
        The portfolio to monitor for equity changes.

    Example
    -------
    >>> config = CircuitBreakerConfig(
    ...     level1_drawdown_pct=Decimal("0.10"),
    ...     level2_drawdown_pct=Decimal("0.15"),
    ...     level3_drawdown_pct=Decimal("0.20"),
    ... )
    >>> circuit_breaker = CircuitBreaker(config=config, portfolio=portfolio)
    >>> circuit_breaker.update()
    >>> if circuit_breaker.can_open_position():
    ...     size = base_size * circuit_breaker.position_size_multiplier()
    """

    def __init__(
        self,
        config: CircuitBreakerConfig,
        portfolio: "Portfolio | None" = None,
    ) -> None:
        self._config = config
        self._portfolio = portfolio
        self._state = CircuitBreakerState.ACTIVE
        self._peak_equity = Decimal("0")
        self._current_equity = Decimal("0")
        self._current_drawdown = Decimal("0")
        self._last_check = datetime.now(timezone.utc)

    @property
    def config(self) -> CircuitBreakerConfig:
        """Return the circuit breaker configuration."""
        return self._config

    @property
    def state(self) -> CircuitBreakerState:
        """Return the current circuit breaker state."""
        return self._state

    @property
    def peak_equity(self) -> Decimal:
        """Return the peak equity (high water mark)."""
        return self._peak_equity

    @property
    def current_equity(self) -> Decimal:
        """Return the last known equity value."""
        return self._current_equity

    @property
    def current_drawdown(self) -> Decimal:
        """
        Return the current drawdown as a decimal.

        Returns
        -------
        Decimal
            Drawdown value (e.g., 0.15 = 15% drawdown).
        """
        return self._current_drawdown

    @property
    def last_check(self) -> datetime:
        """Return the timestamp of the last update."""
        return self._last_check

    def update(self, equity: Decimal | None = None) -> None:
        """
        Check current equity and update state.

        Parameters
        ----------
        equity : Decimal | None
            Optional equity value. If not provided, will be read from portfolio.

        Steps:
        1. Get current equity from portfolio or parameter
        2. Update peak if current > peak
        3. Calculate drawdown
        4. Transition state if thresholds crossed
        5. Update last_check timestamp
        """
        # Get current equity
        if equity is not None:
            self._current_equity = equity
        elif self._portfolio is not None:
            account = self._portfolio.account(self._portfolio.venue)
            if account is not None:
                balance = account.balance_total()
                if balance is not None:
                    self._current_equity = Decimal(str(balance))
        # else: keep existing equity (for testing)

        # Update peak equity (high water mark)
        if self._current_equity > self._peak_equity:
            self._peak_equity = self._current_equity

        # Calculate drawdown
        self._current_drawdown = self._calculate_drawdown()

        # Update state based on drawdown
        self._update_state(self._current_drawdown)

        # Update timestamp
        self._last_check = datetime.now(timezone.utc)

    def can_open_position(self) -> bool:
        """
        Check if new positions are allowed.

        Returns
        -------
        bool
            True if state is ACTIVE or WARNING, False otherwise.
        """
        return self._state in (CircuitBreakerState.ACTIVE, CircuitBreakerState.WARNING)

    def position_size_multiplier(self) -> Decimal:
        """
        Get position size adjustment based on current state.

        Returns
        -------
        Decimal
            Multiplier to apply to base position size.
            - ACTIVE: 1.0 (100%)
            - WARNING: config.warning_size_multiplier (default 0.5)
            - REDUCING: config.reducing_size_multiplier (default 0.0)
            - HALTED: 0.0
        """
        match self._state:
            case CircuitBreakerState.ACTIVE:
                return Decimal("1.0")
            case CircuitBreakerState.WARNING:
                return self._config.warning_size_multiplier
            case CircuitBreakerState.REDUCING:
                return self._config.reducing_size_multiplier
            case CircuitBreakerState.HALTED:
                return Decimal("0.0")
            case _:
                return Decimal("0.0")

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
        if self._config.auto_recovery:
            raise ValueError("Cannot manually reset when auto_recovery is enabled")
        if self._state != CircuitBreakerState.HALTED:
            raise ValueError(f"Cannot reset from state {self._state.value}, only from HALTED")
        self._state = CircuitBreakerState.ACTIVE
        self._last_check = datetime.now(timezone.utc)

    def _calculate_drawdown(self) -> Decimal:
        """
        Calculate current drawdown.

        Returns
        -------
        Decimal
            Drawdown as decimal (0.20 = 20% drawdown).
            Returns 0 if peak_equity is 0 (startup condition).
        """
        if self._peak_equity <= 0:
            return Decimal("0")
        return (self._peak_equity - self._current_equity) / self._peak_equity

    def _update_state(self, drawdown: Decimal) -> None:
        """
        Update state based on current drawdown.

        State transitions follow graduated thresholds:
        - >= level3: HALTED
        - >= level2: REDUCING
        - >= level1: WARNING
        - < recovery: ACTIVE (if not HALTED or auto_recovery enabled)

        Parameters
        ----------
        drawdown : Decimal
            Current drawdown as decimal.
        """
        if drawdown >= self._config.level3_drawdown_pct:
            self._state = CircuitBreakerState.HALTED
        elif drawdown >= self._config.level2_drawdown_pct:
            self._state = CircuitBreakerState.REDUCING
        elif drawdown >= self._config.level1_drawdown_pct:
            self._state = CircuitBreakerState.WARNING
        elif self._state == CircuitBreakerState.HALTED:
            # Recovery from HALTED requires manual reset OR auto_recovery
            if self._config.auto_recovery and drawdown <= self._config.recovery_drawdown_pct:
                self._state = CircuitBreakerState.ACTIVE
            # else: stay HALTED until manual reset()
        else:
            # Recovery from WARNING/REDUCING
            if drawdown <= self._config.recovery_drawdown_pct:
                self._state = CircuitBreakerState.ACTIVE

    def set_initial_equity(self, equity: Decimal) -> None:
        """
        Set initial equity for testing or startup.

        This sets both current and peak equity to the same value.

        Parameters
        ----------
        equity : Decimal
            Initial equity value.
        """
        self._current_equity = equity
        self._peak_equity = equity
        self._current_drawdown = Decimal("0")
