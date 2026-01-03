"""Configuration models for meta-learning.

Provides Pydantic models for MetaModelConfig and WalkForwardConfig.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class MetaModelConfig(BaseModel):
    """Configuration for meta-model training.

    The meta-model predicts P(primary_model_correct) using RandomForest.
    Based on meta-labeling framework from AFML.

    Attributes:
        n_estimators: Number of RandomForest trees.
        max_depth: Maximum tree depth (None = unlimited).
        min_samples_split: Minimum samples required to split a node.
        min_samples_leaf: Minimum samples required at each leaf.
        random_state: Random seed for reproducibility.
        n_jobs: Number of parallel jobs (-1 = all cores).
        default_confidence: Default confidence when insufficient training data.
        min_training_samples: Minimum samples required for training.

    Example:
        >>> config = MetaModelConfig(
        ...     n_estimators=100,
        ...     max_depth=5,
        ... )
    """

    n_estimators: int = Field(
        default=100, ge=10, le=1000, description="Number of trees"
    )
    max_depth: int | None = Field(
        default=5, ge=1, le=20, description="Maximum tree depth"
    )
    min_samples_split: int = Field(
        default=10, ge=2, description="Minimum samples to split"
    )
    min_samples_leaf: int = Field(
        default=5, ge=1, description="Minimum samples per leaf"
    )
    random_state: int = Field(default=42, description="Random seed")
    n_jobs: int = Field(default=-1, description="Parallel jobs (-1 = all cores)")
    default_confidence: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Default confidence"
    )
    min_training_samples: int = Field(
        default=100, ge=20, description="Minimum training samples"
    )

    model_config = {"frozen": True}


class WalkForwardConfig(BaseModel):
    """Configuration for walk-forward validation.

    Implements rolling window train/test splits with embargo and purging
    to prevent look-ahead bias in meta-model training.

    Attributes:
        train_window: Training window size in bars.
        test_window: Test window size in bars.
        step_size: Step size between windows in bars.
        embargo_size: Gap between train and test to prevent leakage.

    Example:
        >>> config = WalkForwardConfig(
        ...     train_window=252,  # 1 year
        ...     test_window=63,    # 1 quarter
        ...     step_size=21,      # 1 month
        ...     embargo_size=5,    # 1 week
        ... )
    """

    train_window: int = Field(
        default=252, ge=50, le=1000, description="Training window (bars)"
    )
    test_window: int = Field(
        default=63, ge=10, le=252, description="Test window (bars)"
    )
    step_size: int = Field(default=21, ge=1, le=63, description="Step size (bars)")
    embargo_size: int = Field(default=5, ge=0, le=20, description="Embargo gap (bars)")

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def validate_windows(self) -> WalkForwardConfig:
        """Validate window size relationships."""
        if self.train_window <= self.test_window:
            msg = f"train_window ({self.train_window}) must be > test_window ({self.test_window})"
            raise ValueError(msg)
        if self.step_size > self.test_window:
            msg = f"step_size ({self.step_size}) should be <= test_window ({self.test_window})"
            raise ValueError(msg)
        if self.embargo_size >= self.test_window:
            msg = f"embargo_size ({self.embargo_size}) must be < test_window ({self.test_window})"
            raise ValueError(msg)
        return self
