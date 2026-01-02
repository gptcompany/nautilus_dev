"""Configuration models for position sizing.

Provides Pydantic models for Giller sub-linear sizing.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class GillerConfig(BaseModel):
    """Configuration for Giller sub-linear position sizing.

    Based on Graham Giller research on optimal position sizing
    with sub-linear scaling to avoid over-betting on strong signals.

    Attributes:
        base_size: Base position size multiplier (before scaling).
        exponent: Sub-linear exponent (0.5 = sqrt scaling).
        max_size: Maximum position size (absolute cap).
        min_size: Minimum position size (to avoid tiny positions).
        use_toxicity_penalty: Apply VPIN toxicity penalty if available.
    """

    base_size: float = Field(default=1.0, gt=0.0)
    exponent: float = Field(default=0.5, gt=0.0, le=1.0)
    max_size: float = Field(default=5.0, gt=0.0)
    min_size: float = Field(default=0.1, ge=0.0)
    use_toxicity_penalty: bool = Field(default=True)

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def validate_size_bounds(self) -> GillerConfig:
        """Validate that min_size <= max_size."""
        if self.min_size > self.max_size:
            msg = f"min_size ({self.min_size}) must be <= max_size ({self.max_size})"
            raise ValueError(msg)
        return self
