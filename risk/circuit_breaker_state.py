"""
Circuit Breaker State Enum.

Defines the state machine states for the circuit breaker.
"""

from enum import Enum


class CircuitBreakerState(Enum):
    """
    Circuit breaker state machine states.

    States represent graduated levels of risk reduction based on drawdown.

    Attributes
    ----------
    ACTIVE
        Normal trading - all entries allowed, full position sizes.
    WARNING
        Drawdown > level1 - entries allowed, reduced position sizes (50%).
    REDUCING
        Drawdown > level2 - no new entries, only exits allowed.
    HALTED
        Drawdown > level3 - trading halted, manual intervention required.
    """

    ACTIVE = "active"
    """Normal trading - all entries allowed, full position sizes."""

    WARNING = "warning"
    """Drawdown > level1 - entries allowed, reduced position sizes (50%)."""

    REDUCING = "reducing"
    """Drawdown > level2 - no new entries, only exits allowed."""

    HALTED = "halted"
    """Drawdown > level3 - trading halted, manual intervention required."""
