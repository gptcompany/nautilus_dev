"""Circuit Breaker pattern for fault tolerance.

Prevents cascading failures by stopping requests after repeated failures.
Used in production algo trading systems to protect against exchange outages.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Failures exceeded threshold, requests blocked
- HALF_OPEN: Testing if service recovered

Reference: Martin Fowler's Circuit Breaker pattern
"""

import asyncio
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, TypeVar

from scripts.ccxt_pipeline.utils.logging import get_logger

logger = get_logger("circuit_breaker")

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior.

    Attributes:
        failure_threshold: Failures before opening circuit (default: 5).
        success_threshold: Successes in half-open to close (default: 2).
        timeout_seconds: Time before attempting recovery (default: 60).
        half_open_max_calls: Max concurrent calls in half-open (default: 1).
    """

    failure_threshold: int = 5
    success_threshold: int = 2
    timeout_seconds: float = 60.0
    half_open_max_calls: int = 1


@dataclass
class CircuitBreakerStats:
    """Statistics for monitoring circuit breaker health."""

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    state_changes: int = 0
    last_failure_time: float | None = None
    last_success_time: float | None = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0


class CircuitBreaker:
    """Circuit breaker for protecting against cascading failures.

    Usage:
        breaker = CircuitBreaker("binance_oi")

        async def fetch_oi():
            return await breaker.call(exchange.fetch_open_interest, symbol)

    The circuit breaker will:
    1. Allow calls when CLOSED (normal)
    2. Block calls when OPEN (after threshold failures)
    3. Allow limited calls when HALF_OPEN (testing recovery)
    4. Auto-transition based on success/failure patterns
    """

    def __init__(
        self,
        name: str,
        config: CircuitBreakerConfig | None = None,
        on_state_change: Callable[[str, CircuitState, CircuitState], None] | None = None,
    ) -> None:
        """Initialize circuit breaker.

        Args:
            name: Identifier for this breaker (for logging).
            config: Configuration options.
            on_state_change: Optional callback on state transitions.
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._on_state_change = on_state_change

        self._state = CircuitState.CLOSED
        self._last_failure_time: float = 0
        self._half_open_calls = 0

        self.stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        """Current circuit state."""
        return self._state

    @property
    def is_closed(self) -> bool:
        """True if circuit is closed (normal operation)."""
        return self._state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """True if circuit is open (blocking requests)."""
        return self._state == CircuitState.OPEN

    def _should_attempt_reset(self) -> bool:
        """Check if timeout elapsed and we should try half-open."""
        if self._state != CircuitState.OPEN:
            return False
        elapsed = time.time() - self._last_failure_time
        return elapsed >= self.config.timeout_seconds

    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to new state with logging and callback."""
        if self._state == new_state:
            return

        old_state = self._state
        self._state = new_state
        self.stats.state_changes += 1

        logger.warning(f"Circuit breaker '{self.name}': {old_state.value} -> {new_state.value}")

        if self._on_state_change:
            self._on_state_change(self.name, old_state, new_state)

    def _record_success(self) -> None:
        """Record successful call."""
        self.stats.successful_calls += 1
        self.stats.last_success_time = time.time()
        self.stats.consecutive_successes += 1
        self.stats.consecutive_failures = 0

        if self._state == CircuitState.HALF_OPEN:
            if self.stats.consecutive_successes >= self.config.success_threshold:
                self._transition_to(CircuitState.CLOSED)
                self._half_open_calls = 0

    def _record_failure(self) -> None:
        """Record failed call."""
        self.stats.failed_calls += 1
        self.stats.last_failure_time = time.time()
        self._last_failure_time = time.time()
        self.stats.consecutive_failures += 1
        self.stats.consecutive_successes = 0

        if self._state == CircuitState.HALF_OPEN:
            # Any failure in half-open reopens circuit
            self._transition_to(CircuitState.OPEN)
            self._half_open_calls = 0
        elif self._state == CircuitState.CLOSED:
            if self.stats.consecutive_failures >= self.config.failure_threshold:
                self._transition_to(CircuitState.OPEN)

    async def call(
        self,
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Execute function with circuit breaker protection.

        Args:
            func: Async function to call.
            *args: Positional arguments for func.
            **kwargs: Keyword arguments for func.

        Returns:
            Result from func.

        Raises:
            CircuitOpenError: If circuit is open.
            Exception: Any exception from func (after recording failure).
        """
        async with self._lock:
            self.stats.total_calls += 1

            # Check if we should transition from OPEN to HALF_OPEN
            if self._should_attempt_reset():
                self._transition_to(CircuitState.HALF_OPEN)
                self._half_open_calls = 0

            # Block if open
            if self._state == CircuitState.OPEN:
                self.stats.rejected_calls += 1
                raise CircuitOpenError(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Retry after {self.config.timeout_seconds}s"
                )

            # Limit calls in half-open
            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.config.half_open_max_calls:
                    self.stats.rejected_calls += 1
                    raise CircuitOpenError(
                        f"Circuit breaker '{self.name}' is HALF_OPEN, max concurrent calls reached"
                    )
                self._half_open_calls += 1

        # Execute outside lock
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            async with self._lock:
                self._record_success()

            return result

        except Exception:
            async with self._lock:
                self._record_failure()
            raise

    def reset(self) -> None:
        """Manually reset circuit to closed state."""
        self._state = CircuitState.CLOSED
        self.stats.consecutive_failures = 0
        self.stats.consecutive_successes = 0
        self._half_open_calls = 0
        logger.info(f"Circuit breaker '{self.name}' manually reset to CLOSED")

    def get_status(self) -> dict[str, Any]:
        """Get current status for monitoring."""
        return {
            "name": self.name,
            "state": self._state.value,
            "stats": {
                "total_calls": self.stats.total_calls,
                "successful_calls": self.stats.successful_calls,
                "failed_calls": self.stats.failed_calls,
                "rejected_calls": self.stats.rejected_calls,
                "consecutive_failures": self.stats.consecutive_failures,
                "state_changes": self.stats.state_changes,
            },
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "timeout_seconds": self.config.timeout_seconds,
            },
        }


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open and blocking requests."""

    pass
