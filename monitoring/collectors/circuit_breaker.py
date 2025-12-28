# monitoring.collectors.circuit_breaker - CircuitBreakerCollector for drawdown monitoring
#
# T030: Create CircuitBreakerCollector for QuestDB metrics

import logging
from datetime import datetime, timezone
from typing import Callable, Literal

from monitoring.models import CircuitBreakerMetrics

logger = logging.getLogger(__name__)


class CircuitBreakerCollector:
    """Collector for circuit breaker state metrics.

    Emits metrics to QuestDB when circuit breaker state changes.
    Designed to be called by CircuitBreakerActor on state transitions.
    """

    def __init__(
        self,
        trader_id: str,
        env: Literal["prod", "staging", "dev"] = "dev",
        on_metrics: Callable[[CircuitBreakerMetrics], None] | None = None,
    ):
        """Initialize CircuitBreakerCollector.

        Args:
            trader_id: Trader identifier for tagging metrics.
            env: Environment (prod/staging/dev).
            on_metrics: Optional callback for when metrics are emitted.
        """
        self._trader_id = trader_id
        self._env = env
        self._on_metrics = on_metrics
        self._last_state: str | None = None

    def set_on_metrics(self, callback: Callable[[CircuitBreakerMetrics], None]) -> None:
        """Set callback for when metrics are collected.

        Args:
            callback: Function to call with collected metrics.
        """
        self._on_metrics = callback

    def emit(
        self,
        state: Literal["active", "warning", "reducing", "halted"],
        current_drawdown: float,
        peak_equity: float,
        current_equity: float,
        force: bool = False,
    ) -> CircuitBreakerMetrics | None:
        """Emit circuit breaker metrics.

        Only emits if state changed or force=True.

        Args:
            state: Current circuit breaker state.
            current_drawdown: Current drawdown as decimal.
            peak_equity: High water mark equity.
            current_equity: Current equity value.
            force: Force emit even if state unchanged.

        Returns:
            CircuitBreakerMetrics if emitted, None otherwise.
        """
        # Only emit on state change (unless forced)
        if not force and state == self._last_state:
            return None

        self._last_state = state

        metrics = CircuitBreakerMetrics(
            timestamp=datetime.now(timezone.utc),
            trader_id=self._trader_id,
            state=state,
            current_drawdown=current_drawdown,
            peak_equity=peak_equity,
            current_equity=current_equity,
            env=self._env,
        )

        if self._on_metrics:
            try:
                self._on_metrics(metrics)
            except Exception as e:
                logger.error(f"Error emitting circuit breaker metrics: {e}")

        logger.info(
            f"Circuit breaker state: {state}, "
            f"drawdown: {current_drawdown:.2%}, "
            f"equity: {current_equity:.2f}/{peak_equity:.2f}"
        )

        return metrics

    def emit_from_circuit_breaker(
        self,
        circuit_breaker: "CircuitBreaker",
        force: bool = False,
    ) -> CircuitBreakerMetrics | None:
        """Emit metrics from a CircuitBreaker instance.

        Args:
            circuit_breaker: CircuitBreaker to extract state from.
            force: Force emit even if state unchanged.

        Returns:
            CircuitBreakerMetrics if emitted, None otherwise.
        """
        return self.emit(
            state=circuit_breaker.state.value,
            current_drawdown=float(circuit_breaker.current_drawdown),
            peak_equity=float(circuit_breaker.peak_equity),
            current_equity=float(circuit_breaker.current_equity),
            force=force,
        )


# Type hint for CircuitBreaker import
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from risk.circuit_breaker import CircuitBreaker


__all__ = ["CircuitBreakerCollector"]
