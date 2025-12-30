"""Recovery Configuration (Spec 017).

This module defines the configuration model for position recovery behavior.
"""

from pydantic import BaseModel, Field, field_validator


class RecoveryConfig(BaseModel):
    """Configuration for position recovery on TradingNode restart.

    This configuration controls how position recovery behaves, including
    warmup parameters, timing delays, and external position handling.

    Attributes:
        trader_id: Unique identifier for the trader instance.
        recovery_enabled: Enable position recovery from cache.
        warmup_lookback_days: Days of historical data for indicator warmup.
        startup_delay_secs: Delay before reconciliation starts.
        max_recovery_time_secs: Maximum time allowed for full recovery.
        claim_external_positions: Claim positions opened outside NautilusTrader.
    """

    trader_id: str = Field(
        description="Unique identifier for the trader instance",
    )
    recovery_enabled: bool = Field(
        default=True,
        description="Enable position recovery from cache",
    )
    warmup_lookback_days: int = Field(
        default=2,
        ge=1,
        le=30,
        description="Days of historical data for indicator warmup",
    )
    startup_delay_secs: float = Field(
        default=10.0,
        ge=5.0,
        le=60.0,
        description="Delay before reconciliation starts",
    )
    max_recovery_time_secs: float = Field(
        default=30.0,
        ge=10.0,
        le=120.0,
        description="Maximum time allowed for full recovery",
    )
    claim_external_positions: bool = Field(
        default=True,
        description="Claim positions opened outside NautilusTrader",
    )

    @field_validator("max_recovery_time_secs")
    @classmethod
    def validate_max_recovery_time(cls, v: float, info) -> float:
        """Ensure max_recovery_time exceeds startup_delay."""
        startup_delay = info.data.get("startup_delay_secs", 10.0)
        if v <= startup_delay:
            raise ValueError(
                f"max_recovery_time_secs ({v}) must exceed startup_delay_secs ({startup_delay})"
            )
        return v

    model_config = {"frozen": True}
