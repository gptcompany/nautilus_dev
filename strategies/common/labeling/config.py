"""Configuration models for triple barrier labeling.

Provides Pydantic models for TripleBarrierConfig per AFML specification.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class TripleBarrierConfig(BaseModel):
    """Configuration for triple barrier labeling.

    Based on Marcos Lopez de Prado's Advances in Financial Machine Learning (AFML).
    Labels trade outcomes as take-profit (+1), stop-loss (-1), or timeout (0).

    Attributes:
        pt_multiplier: Take-profit distance as multiple of ATR.
        sl_multiplier: Stop-loss distance as multiple of ATR.
        max_holding_bars: Maximum bars before timeout (vertical barrier).
        atr_period: Period for ATR calculation.
        min_return: Minimum return to assign non-zero label on timeout.

    Example:
        >>> config = TripleBarrierConfig(
        ...     pt_multiplier=2.0,
        ...     sl_multiplier=1.0,
        ...     max_holding_bars=10,
        ... )
    """

    pt_multiplier: float = Field(default=2.0, gt=0.0, description="Take-profit ATR multiplier")
    sl_multiplier: float = Field(default=1.0, gt=0.0, description="Stop-loss ATR multiplier")
    max_holding_bars: int = Field(default=10, ge=1, description="Maximum holding period in bars")
    atr_period: int = Field(default=14, ge=2, description="ATR calculation period")
    min_return: float = Field(
        default=0.0, ge=0.0, description="Minimum return for non-zero timeout label"
    )

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def validate_multipliers(self) -> TripleBarrierConfig:
        """Validate that pt_multiplier >= sl_multiplier for positive expectancy."""
        if self.pt_multiplier < self.sl_multiplier:
            msg = f"pt_multiplier ({self.pt_multiplier}) should be >= sl_multiplier ({self.sl_multiplier}) for positive expectancy"
            raise ValueError(msg)
        return self
