"""Pydantic configuration models for baseline validation.

This module provides typed configuration models using Pydantic.
Ensures validation, serialization, and documentation of all config options.

Models:
    - ContenderConfig: Per-contender settings
    - ValidationConfig: Walk-forward validation settings
    - SuccessCriteriaConfig: GO/WAIT/STOP thresholds
    - OutputConfig: Report output settings
    - BaselineValidationConfig: Root configuration
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class AdaptiveContenderConfig(BaseModel):
    """Configuration for Adaptive contender (SOPS+Giller+Thompson)."""

    sops_k_base: float = Field(
        default=1.0,
        gt=0,
        description="Base k for SOPS tanh transformation",
    )
    giller_exponent: float = Field(
        default=0.5,
        gt=0,
        le=1,
        description="Power law exponent (0.5 = sqrt)",
    )
    thompson_decay: float = Field(
        default=0.99,
        gt=0,
        lt=1,
        description="Decay factor for Thompson sampling",
    )
    vol_alpha: float = Field(
        default=0.1,
        gt=0,
        lt=1,
        description="EMA alpha for volatility estimation",
    )
    enable_tape_weight: bool = Field(
        default=True,
        description="Whether to use tape speed weighting",
    )
    max_position_pct: float = Field(
        default=0.10,
        gt=0,
        le=1,
        description="Maximum position as % of equity",
    )


class FixedContenderConfig(BaseModel):
    """Configuration for Fixed Fractional contender."""

    risk_pct: float = Field(
        default=0.02,
        gt=0,
        le=1,
        description="Fraction of equity to risk per trade",
    )
    max_positions: int = Field(
        default=10,
        ge=1,
        description="Maximum number of concurrent positions",
    )
    stop_loss_pct: float = Field(
        default=0.05,
        gt=0,
        le=1,
        description="Stop loss as percentage of entry price",
    )


class BuyHoldContenderConfig(BaseModel):
    """Configuration for Buy & Hold contender."""

    allocation_pct: float = Field(
        default=1.0,
        gt=0,
        le=1,
        description="Fraction of equity to allocate",
    )


class ContenderConfig(BaseModel):
    """Configuration for a single contender."""

    name: str = Field(description="Display name for the contender")
    enabled: bool = Field(default=True, description="Whether to include in validation")
    config: dict[str, Any] = Field(
        default_factory=dict,
        description="Contender-specific configuration",
    )


class ValidationConfig(BaseModel):
    """Walk-forward validation configuration."""

    data_start: datetime = Field(description="Start of data range")
    data_end: datetime = Field(description="End of data range")

    train_months: int = Field(
        default=12,
        ge=1,
        description="Training period per window in months",
    )
    test_months: int = Field(
        default=1,
        ge=1,
        description="Test period per window in months",
    )
    step_months: int = Field(
        default=1,
        ge=1,
        description="Rolling step size in months",
    )

    embargo_before_days: int = Field(
        default=5,
        ge=0,
        description="Pre-test purge period (Lopez de Prado PKCV)",
    )
    embargo_after_days: int = Field(
        default=3,
        ge=0,
        description="Post-test purge period",
    )

    min_windows: int = Field(
        default=12,
        ge=2,
        description="Minimum windows for statistical validity",
    )

    transaction_cost_pct: float = Field(
        default=0.001,
        ge=0,
        le=0.1,
        description="Transaction cost as fraction (0.001 = 0.1%)",
    )

    @field_validator("data_end")
    @classmethod
    def validate_data_end(cls, v: datetime, info) -> datetime:
        """Validate data_end is after data_start."""
        data_start = info.data.get("data_start")
        if data_start and v <= data_start:
            raise ValueError("data_end must be after data_start")
        return v

    @model_validator(mode="after")
    def validate_sufficient_data(self) -> ValidationConfig:
        """Validate sufficient data for minimum windows."""
        total_days = (self.data_end - self.data_start).days

        # Calculate minimum days needed
        train_days = self.train_months * 30
        test_days = self.test_months * 30
        step_days = self.step_months * 30
        embargo_days = self.embargo_before_days + self.embargo_after_days

        first_window_days = train_days + embargo_days + test_days
        additional_windows_days = (self.min_windows - 1) * step_days
        min_required_days = first_window_days + additional_windows_days

        if total_days < min_required_days:
            raise ValueError(
                f"Insufficient data: {total_days} days available, "
                f"but {min_required_days} days required for {self.min_windows} windows"
            )

        return self


class SuccessCriteriaConfig(BaseModel):
    """Success criteria for GO/WAIT/STOP decision.

    Based on research_vs_repos_analysis.md and Lopez de Prado (2018).
    """

    sharpe_edge: float = Field(
        default=0.2,
        ge=0,
        description="Adaptive must beat Fixed by this Sharpe margin",
    )
    min_dsr: float = Field(
        default=0.5,
        ge=0,
        description="Minimum Deflated Sharpe Ratio (skill > luck)",
    )
    max_pbo: float = Field(
        default=0.5,
        gt=0,
        le=1,
        description="Maximum Probability of Backtest Overfitting",
    )
    max_drawdown: float = Field(
        default=0.30,
        gt=0,
        le=1,
        description="Maximum acceptable drawdown",
    )


class OutputConfig(BaseModel):
    """Report output configuration."""

    report_dir: Path = Field(
        default=Path("reports/baseline_validation"),
        description="Directory for output reports",
    )
    formats: list[str] = Field(
        default=["markdown", "json"],
        description="Output formats to generate",
    )
    generate_charts: bool = Field(
        default=True,
        description="Whether to generate equity curve charts",
    )
    verbose: bool = Field(
        default=False,
        description="Whether to include detailed per-window metrics",
    )


class BaselineValidationConfig(BaseModel):
    """Root configuration for baseline validation.

    Combines all sub-configurations into a single validated model.
    """

    validation: ValidationConfig
    contenders: dict[str, ContenderConfig]
    success_criteria: SuccessCriteriaConfig = Field(default_factory=SuccessCriteriaConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    seed: int | None = Field(
        default=42,
        description="Random seed for reproducibility",
    )

    @classmethod
    def from_yaml(cls, path: Path | str) -> BaselineValidationConfig:
        """Load configuration from YAML file.

        Args:
            path: Path to YAML configuration file.

        Returns:
            Validated BaselineValidationConfig.
        """
        import yaml

        with open(path) as f:
            data = yaml.safe_load(f)

        return cls.model_validate(data)

    @classmethod
    def default(cls) -> BaselineValidationConfig:
        """Create default configuration.

        Returns:
            BaselineValidationConfig with sensible defaults.
        """
        return cls(
            validation=ValidationConfig(
                data_start=datetime(2015, 1, 1),
                data_end=datetime(2025, 1, 1),
            ),
            contenders={
                "adaptive": ContenderConfig(
                    name="SOPS+Giller+Thompson",
                    enabled=True,
                    config=AdaptiveContenderConfig().model_dump(),
                ),
                "fixed": ContenderConfig(
                    name="Fixed 2%",
                    enabled=True,
                    config=FixedContenderConfig().model_dump(),
                ),
                "buyhold": ContenderConfig(
                    name="Buy & Hold",
                    enabled=True,
                    config=BuyHoldContenderConfig().model_dump(),
                ),
            },
        )

    def to_walk_forward_config(self) -> dict:
        """Convert to WalkForwardConfig compatible dict.

        Returns:
            Dict that can be used to create WalkForwardConfig.
        """
        return {
            "data_start": self.validation.data_start,
            "data_end": self.validation.data_end,
            "train_months": self.validation.train_months,
            "test_months": self.validation.test_months,
            "step_months": self.validation.step_months,
            "embargo_before_days": self.validation.embargo_before_days,
            "embargo_after_days": self.validation.embargo_after_days,
            "min_windows": self.validation.min_windows,
            "seed": self.seed,
        }
