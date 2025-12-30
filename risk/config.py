"""
Risk Management Configuration.

Defines RiskConfig Pydantic model and related enums for stop-loss
and position limit management.
"""

from decimal import Decimal
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field, field_validator, model_validator


class StopLossType(str, Enum):
    """Defines how stop-loss orders are submitted."""

    MARKET = "market"  # Native STOP_MARKET order (default)
    LIMIT = "limit"  # Native STOP_LIMIT order
    EMULATED = "emulated"  # Strategy-managed via price checks


class TrailingOffsetType(str, Enum):
    """Defines how trailing distance is measured."""

    PRICE = "price"  # Absolute price offset
    BASIS_POINTS = "basis_points"  # Offset in basis points (1 bp = 0.01%)


class RiskConfig(BaseModel):
    """
    Configuration for risk management behavior.

    Controls automatic stop-loss generation and position limits.
    All fields are optional with sensible defaults.

    Attributes
    ----------
    stop_loss_enabled : bool
        Enable automatic stop-loss generation on position open.
    stop_loss_pct : Decimal
        Stop distance as fraction (0.02 = 2%). Must be > 0 and < 1.
    stop_loss_type : StopLossType
        Order type: market/limit/emulated.
    trailing_stop : bool
        Enable trailing stop mode (stop moves with favorable price).
    trailing_distance_pct : Decimal
        Trailing distance as fraction. Must be <= stop_loss_pct.
    trailing_offset_type : TrailingOffsetType
        How trailing distance is measured.
    max_position_size : dict[str, Decimal] | None
        Per-instrument max position (key = instrument ID string).
    max_total_exposure : Decimal | None
        Total portfolio exposure limit in quote currency.
    dynamic_boundaries : bool
        Enable OU-based optimal stopping boundaries (Phase 5).
    ou_lookback_days : int
        Days of history for OU parameter estimation.

    Examples
    --------
    >>> from decimal import Decimal
    >>> config = RiskConfig(stop_loss_pct=Decimal("0.02"))
    >>> config.stop_loss_enabled
    True
    """

    stop_loss_enabled: bool = True
    stop_loss_pct: Annotated[Decimal, Field(gt=0, lt=1)] = Decimal("0.02")
    stop_loss_type: StopLossType = StopLossType.MARKET
    trailing_stop: bool = False
    trailing_distance_pct: Annotated[Decimal, Field(gt=0, le=1)] = Decimal("0.01")
    trailing_offset_type: TrailingOffsetType = TrailingOffsetType.PRICE
    max_position_size: dict[str, Decimal] | None = None
    max_total_exposure: Annotated[Decimal | None, Field(gt=0)] = None
    dynamic_boundaries: bool = False
    ou_lookback_days: Annotated[int, Field(ge=7, le=365)] = 30

    model_config = {"frozen": False, "validate_assignment": True}

    @field_validator("max_position_size")
    @classmethod
    def validate_max_position_size(
        cls, v: dict[str, Decimal] | None
    ) -> dict[str, Decimal] | None:
        """Ensure all position sizes are positive."""
        if v is None:
            return None
        for instrument_id, size in v.items():
            if size <= 0:
                raise ValueError(
                    f"max_position_size[{instrument_id}] must be positive, got {size}"
                )
        return v

    @model_validator(mode="after")
    def validate_trailing_distance(self) -> "RiskConfig":
        """Ensure trailing distance <= stop loss distance."""
        if self.trailing_stop and self.trailing_distance_pct > self.stop_loss_pct:
            raise ValueError(
                f"trailing_distance_pct ({self.trailing_distance_pct}) must be "
                f"<= stop_loss_pct ({self.stop_loss_pct})"
            )
        return self
