"""
Daily Loss Config Contract (Spec 013).

This file defines the configuration model for DailyPnLTracker.
"""

from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, model_validator


class DailyLossConfig(BaseModel):
    """
    Configuration for daily PnL tracking and loss limits.

    Attributes
    ----------
    daily_loss_limit : Decimal
        Absolute daily loss limit in quote currency (e.g., USD).
        Must be > 0.
    daily_loss_pct : Decimal | None
        Alternative: daily loss as % of starting capital.
        Takes precedence over daily_loss_limit if set.
        Must be between 0 and 1 (e.g., 0.02 = 2%).
    reset_time_utc : str
        Time to reset daily counters in UTC (HH:MM format).
        Default: "00:00"
    per_strategy : bool
        If True, track limits per strategy.
        If False, track global limit across all strategies.
    close_positions_on_limit : bool
        If True, close all positions when limit triggered.
        If False, only block new entries.
    warning_threshold_pct : Decimal
        Alert when PnL reaches this % of limit.
        Default: 0.5 (50% of limit).

    Examples
    --------
    >>> config = DailyLossConfig(daily_loss_limit=Decimal("1000"))
    >>> config.daily_loss_limit
    Decimal('1000')

    >>> config = DailyLossConfig(daily_loss_pct=Decimal("0.02"))
    >>> config.daily_loss_pct
    Decimal('0.02')
    """

    daily_loss_limit: Annotated[Decimal, Field(gt=0)] = Decimal("1000")
    daily_loss_pct: Annotated[Decimal | None, Field(gt=0, lt=1)] = None
    reset_time_utc: str = "00:00"
    per_strategy: bool = False
    close_positions_on_limit: bool = True
    warning_threshold_pct: Annotated[Decimal, Field(gt=0, lt=1)] = Decimal("0.5")

    model_config = {"frozen": False, "validate_assignment": True}

    @model_validator(mode="after")
    def validate_reset_time(self) -> "DailyLossConfig":
        """Ensure reset_time_utc is valid HH:MM format."""
        try:
            parts = self.reset_time_utc.split(":")
            if len(parts) != 2:
                raise ValueError
            hour, minute = int(parts[0]), int(parts[1])
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError
        except (ValueError, AttributeError) as err:
            raise ValueError(
                f"reset_time_utc must be in HH:MM format, got: {self.reset_time_utc}"
            ) from err
        return self

    def get_effective_limit(self, starting_equity: Decimal) -> Decimal:
        """
        Get effective limit value.

        Parameters
        ----------
        starting_equity : Decimal
            Starting equity for percentage calculation.

        Returns
        -------
        Decimal
            Absolute limit value.
        """
        if self.daily_loss_pct is not None:
            return starting_equity * self.daily_loss_pct
        return self.daily_loss_limit
