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


class IntegratedSizingConfig(BaseModel):
    """Configuration for integrated position sizing pipeline.

    Combines all factors (signal, meta-confidence, regime, toxicity)
    into a unified position sizing formula.

    Formula:
        size = direction * |signal|^giller_exponent * meta_confidence *
               regime_weight * (1 - toxicity) * fractional_kelly

    Attributes:
        giller_exponent: Sub-linear exponent for signal magnitude (0.5 = sqrt).
        fractional_kelly: Kelly fraction for position sizing safety.
        min_size: Minimum position size (after all adjustments).
        max_size: Maximum position size (hard cap).
        default_meta_confidence: Default when meta-model unavailable.
        default_regime_weight: Default when regime filter unavailable.
        default_toxicity: Default when VPIN unavailable.

    Example:
        >>> config = IntegratedSizingConfig(
        ...     giller_exponent=0.5,
        ...     fractional_kelly=0.5,
        ... )
    """

    giller_exponent: float = Field(default=0.5, gt=0.0, le=1.0, description="Sub-linear exponent")
    fractional_kelly: float = Field(default=0.5, gt=0.0, le=1.0, description="Kelly fraction")
    min_size: float = Field(default=0.01, ge=0.0, description="Minimum position size")
    max_size: float = Field(default=1.0, gt=0.0, description="Maximum position size")
    default_meta_confidence: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Default meta confidence"
    )
    default_regime_weight: float = Field(
        default=0.8, ge=0.0, le=1.5, description="Default regime weight"
    )
    default_toxicity: float = Field(default=0.0, ge=0.0, le=1.0, description="Default toxicity")

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def validate_size_bounds(self) -> IntegratedSizingConfig:
        """Validate that min_size <= max_size."""
        if self.min_size > self.max_size:
            msg = f"min_size ({self.min_size}) must be <= max_size ({self.max_size})"
            raise ValueError(msg)
        return self
