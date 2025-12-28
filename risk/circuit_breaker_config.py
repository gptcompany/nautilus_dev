"""
Configuration for Circuit Breaker.

This module defines the configuration model for the CircuitBreaker.
Copied from contracts/circuit_breaker_config.py with implementation.
"""

from decimal import Decimal

from pydantic import BaseModel, field_validator, model_validator


class CircuitBreakerConfig(BaseModel):
    """
    Configuration for circuit breaker.

    Attributes
    ----------
    level1_drawdown_pct : Decimal
        WARNING threshold (default: 10%).
    level2_drawdown_pct : Decimal
        REDUCING threshold (default: 15%).
    level3_drawdown_pct : Decimal
        HALTED threshold (default: 20%).
    recovery_drawdown_pct : Decimal
        Threshold to return to ACTIVE (default: 5%).
    auto_recovery : bool
        If True, automatically return to ACTIVE after HALTED when
        drawdown recovers below recovery_drawdown_pct.
        If False, require manual reset() call.
    check_interval_secs : int
        Interval for periodic state checks (seconds).
    warning_size_multiplier : Decimal
        Position size multiplier when in WARNING state.
    reducing_size_multiplier : Decimal
        Position size multiplier when in REDUCING state (usually 0).

    Example
    -------
    >>> config = CircuitBreakerConfig(
    ...     level1_drawdown_pct=Decimal("0.10"),
    ...     level2_drawdown_pct=Decimal("0.15"),
    ...     level3_drawdown_pct=Decimal("0.20"),
    ...     auto_recovery=False,
    ... )
    """

    # Drawdown thresholds
    level1_drawdown_pct: Decimal = Decimal("0.10")  # 10% - WARNING
    level2_drawdown_pct: Decimal = Decimal("0.15")  # 15% - REDUCING
    level3_drawdown_pct: Decimal = Decimal("0.20")  # 20% - HALTED

    # Recovery threshold
    recovery_drawdown_pct: Decimal = Decimal("0.05")  # 5% - return to ACTIVE

    # Recovery mode
    auto_recovery: bool = False

    # Check interval
    check_interval_secs: int = 60

    # Position size multipliers
    warning_size_multiplier: Decimal = Decimal("0.5")  # 50% in WARNING
    reducing_size_multiplier: Decimal = Decimal("0.0")  # 0% in REDUCING

    @field_validator(
        "level1_drawdown_pct",
        "level2_drawdown_pct",
        "level3_drawdown_pct",
        "recovery_drawdown_pct",
    )
    @classmethod
    def validate_percentage(cls, v: Decimal) -> Decimal:
        """Validate that percentage is in range (0, 1)."""
        if not (Decimal("0") < v < Decimal("1")):
            raise ValueError("Percentage must be between 0 and 1 (exclusive)")
        return v

    @field_validator("warning_size_multiplier", "reducing_size_multiplier")
    @classmethod
    def validate_multiplier(cls, v: Decimal) -> Decimal:
        """Validate that multiplier is in range [0, 1]."""
        if not (Decimal("0") <= v <= Decimal("1")):
            raise ValueError("Multiplier must be between 0 and 1 (inclusive)")
        return v

    @field_validator("check_interval_secs")
    @classmethod
    def validate_interval(cls, v: int) -> int:
        """Validate that interval is positive."""
        if v <= 0:
            raise ValueError("check_interval_secs must be positive")
        return v

    @model_validator(mode="after")
    def validate_threshold_ordering(self) -> "CircuitBreakerConfig":
        """Validate that thresholds are in ascending order."""
        if not (
            self.level1_drawdown_pct
            < self.level2_drawdown_pct
            < self.level3_drawdown_pct
        ):
            raise ValueError("Thresholds must be ordered: level1 < level2 < level3")
        if self.recovery_drawdown_pct >= self.level1_drawdown_pct:
            raise ValueError(
                "recovery_drawdown_pct must be less than level1_drawdown_pct "
                "(hysteresis)"
            )
        return self

    model_config = {"frozen": True}
