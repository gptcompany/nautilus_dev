"""Configuration models for Orderflow Indicators (Spec 025).

Provides Pydantic v2 models for VPIN and Hawkes OFI configuration.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator
from pydantic_core.core_schema import ValidationInfo


class VPINConfig(BaseModel):
    """Configuration for VPIN (Volume-Synchronized Probability of Informed Trading).

    VPIN measures the probability of informed trading by analyzing order flow
    imbalance across volume-synchronized buckets.

    Attributes:
        bucket_size: Volume per bucket (e.g., 1000 contracts).
        n_buckets: Number of buckets for rolling VPIN calculation.
        classification_method: Trade classification method to use.
        min_bucket_volume: Minimum volume to form a valid bucket.
    """

    bucket_size: float = Field(
        default=1000.0,
        gt=0,
        description="Volume per bucket (e.g., 1000 contracts)",
    )
    n_buckets: int = Field(
        default=50,
        ge=10,
        le=200,
        description="Number of buckets for rolling VPIN",
    )
    classification_method: str = Field(
        default="tick_rule",
        description="Trade classification: 'tick_rule', 'bvc', 'close_vs_open'",
    )
    min_bucket_volume: float = Field(
        default=100.0,
        ge=0,
        description="Minimum volume to form a valid bucket",
    )

    @field_validator("classification_method")
    @classmethod
    def validate_classification(cls, v: str) -> str:
        """Validate classification method is one of allowed values."""
        valid = {"tick_rule", "bvc", "close_vs_open"}
        if v not in valid:
            raise ValueError(f"classification_method must be one of {valid}")
        return v

    model_config = {"frozen": True}


class HawkesConfig(BaseModel):
    """Configuration for Hawkes process Order Flow Imbalance.

    Hawkes processes model self-exciting point processes where past events
    increase the probability of future events. Used to measure order flow
    imbalance with temporal clustering effects.

    Attributes:
        decay_rate: Exponential decay rate (beta) for kernel.
        lookback_ticks: Number of ticks to keep in buffer.
        refit_interval: Refit Hawkes model every N ticks.
        use_fixed_params: Use fixed parameters instead of online fitting.
        fixed_baseline: Fixed baseline intensity (mu) when use_fixed_params=True.
        fixed_excitation: Fixed excitation (alpha) when use_fixed_params=True.
    """

    decay_rate: float = Field(
        default=1.0,
        gt=0,
        description="Exponential decay rate (beta)",
    )
    lookback_ticks: int = Field(
        default=10000,
        ge=100,
        le=100000,
        description="Number of ticks to keep in buffer",
    )
    refit_interval: int = Field(
        default=100,
        ge=10,
        description="Refit Hawkes model every N ticks",
    )
    use_fixed_params: bool = Field(
        default=False,
        description="Use fixed mu, alpha, beta instead of online fitting",
    )
    fixed_baseline: float = Field(
        default=0.1,
        ge=0,
        description="Fixed baseline intensity mu (if use_fixed_params)",
    )
    fixed_excitation: float = Field(
        default=0.5,
        ge=0,
        lt=1,
        description="Fixed excitation alpha (if use_fixed_params, must be < decay for stationarity)",
    )

    @field_validator("fixed_excitation")
    @classmethod
    def validate_branching_ratio(cls, v: float, info: ValidationInfo) -> float:
        """Ensure branching ratio < 1 for stationarity.

        For a stationary Hawkes process, the branching ratio eta = alpha/beta
        must be less than 1. This is equivalent to alpha < beta.
        """
        decay = info.data.get("decay_rate", 1.0)
        if v >= decay:
            raise ValueError(
                f"fixed_excitation ({v}) must be < decay_rate ({decay}) for stationarity"
            )
        return v

    model_config = {"frozen": True}


class OrderflowConfig(BaseModel):
    """Configuration for OrderflowManager.

    Unified configuration for all orderflow indicators, allowing selective
    enabling of VPIN and Hawkes OFI components.

    Attributes:
        vpin: Configuration for VPIN indicator.
        hawkes: Configuration for Hawkes OFI indicator.
        enable_vpin: Whether to enable VPIN calculation.
        enable_hawkes: Whether to enable Hawkes OFI calculation.
    """

    vpin: VPINConfig = Field(default_factory=VPINConfig)
    hawkes: HawkesConfig = Field(default_factory=HawkesConfig)
    enable_vpin: bool = Field(
        default=True,
        description="Enable VPIN indicator",
    )
    enable_hawkes: bool = Field(
        default=True,
        description="Enable Hawkes OFI indicator",
    )

    model_config = {"frozen": True}
