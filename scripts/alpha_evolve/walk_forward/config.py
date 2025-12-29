"""Walk-forward validation configuration."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator


class WalkForwardConfig(BaseModel):
    """Configuration for walk-forward validation.

    Attributes:
        data_start: Start of data range for validation.
        data_end: End of data range for validation.
        train_months: Training window size in months.
        test_months: Test window size in months.
        step_months: Rolling step size in months.
        embargo_before_days: Pre-test purge period (Lopez de Prado PKCV).
        embargo_after_days: Post-test purge period.
        min_windows: Minimum number of windows required.
        min_profitable_windows_pct: Min % of windows that must be profitable.
        min_test_sharpe: Minimum Sharpe ratio in test windows.
        max_drawdown_threshold: Maximum allowed drawdown per window.
        min_robustness_score: Minimum robustness score to pass validation.
        seed: Random seed for reproducibility.

    Example:
        >>> config = WalkForwardConfig(
        ...     data_start=datetime(2023, 1, 1),
        ...     data_end=datetime(2024, 12, 1),
        ...     train_months=6,
        ...     test_months=3,
        ... )
    """

    # Date range
    data_start: datetime = Field(description="Start of data range")
    data_end: datetime = Field(description="End of data range")

    # Window sizes
    train_months: int = Field(
        default=6, ge=1, description="Training window size in months"
    )
    test_months: int = Field(default=3, ge=1, description="Test window size in months")
    step_months: int = Field(default=3, ge=1, description="Rolling step size in months")

    # Embargo periods (Lopez de Prado PKCV)
    embargo_before_days: int = Field(
        default=5,
        ge=0,
        description="Pre-test purge period to prevent leakage from lagging indicators",
    )
    embargo_after_days: int = Field(
        default=3,
        ge=0,
        description="Post-test purge period to prevent next train contamination",
    )

    # Validation criteria
    min_windows: int = Field(
        default=4, ge=2, description="Minimum number of windows required"
    )
    min_profitable_windows_pct: float = Field(
        default=0.75,
        gt=0,
        le=1.0,
        description="Min % of windows that must be profitable",
    )
    min_test_sharpe: float = Field(
        default=0.5,
        ge=0,
        description="Minimum Sharpe ratio in test windows",
    )
    max_drawdown_threshold: float = Field(
        default=0.30,
        gt=0,
        le=1.0,
        description="Maximum allowed drawdown per window",
    )
    min_robustness_score: float = Field(
        default=60.0,
        ge=0,
        le=100,
        description="Minimum robustness score to pass validation",
    )

    # Reproducibility
    seed: int | None = Field(
        default=None, description="Random seed for reproducibility"
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
    def validate_sufficient_data(self) -> "WalkForwardConfig":
        """Validate sufficient data for minimum windows."""
        total_days = (self.data_end - self.data_start).days

        # Calculate minimum days needed for min_windows
        train_days = self.train_months * 30
        test_days = self.test_months * 30
        step_days = self.step_months * 30
        embargo_days = self.embargo_before_days + self.embargo_after_days

        # First window needs train + embargo + test
        first_window_days = train_days + embargo_days + test_days

        # Additional windows need step_days each
        additional_windows_days = (self.min_windows - 1) * step_days

        min_required_days = first_window_days + additional_windows_days

        if total_days < min_required_days:
            raise ValueError(
                f"Insufficient data: {total_days} days available, "
                f"but {min_required_days} days required for {self.min_windows} windows"
            )

        return self

    model_config = {"frozen": False}
