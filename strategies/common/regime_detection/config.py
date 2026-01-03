"""Configuration models for regime detection.

Provides Pydantic models for HMM and GMM configuration.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class RegimeConfig(BaseModel):
    """Configuration for RegimeManager and HMM regime detection.

    Attributes:
        hmm_states: Number of HMM states to fit (2-5 recommended).
        gmm_clusters: Number of GMM volatility clusters (typically 3).
        hmm_lookback: Number of bars for HMM training window.
        hmm_n_iter: Maximum HMM fitting iterations.
        hmm_n_init: Number of random initializations for HMM.
        min_bars_for_fit: Minimum bars required before fitting.
        refit_interval: Bars between HMM refitting (0 = no refit).
        volatility_window: Rolling window for volatility calculation.
    """

    hmm_states: int = Field(default=3, ge=2, le=5)
    gmm_clusters: int = Field(default=3, ge=2, le=5)
    hmm_lookback: int = Field(default=252, ge=50)
    hmm_n_iter: int = Field(default=100, ge=10)
    hmm_n_init: int = Field(default=10, ge=1)
    min_bars_for_fit: int = Field(default=100, ge=20)
    refit_interval: int = Field(default=0, ge=0)
    volatility_window: int = Field(default=20, ge=5)

    model_config = {"frozen": True}


class BOCDConfig(BaseModel):
    """Configuration for Bayesian Online Changepoint Detection.

    Implements Adams & MacKay (2007) algorithm for detecting
    regime changes in real-time streaming data.

    Attributes:
        hazard_rate: P(changepoint) per step (1/expected_run_length).
        mu0: Prior mean for Gaussian observations.
        kappa0: Prior precision weight (pseudo-observations for mean).
        alpha0: Prior shape parameter (Student-t degrees of freedom).
        beta0: Prior scale parameter (variance scaling).
        max_run_length: Maximum tracked run length (truncation for efficiency).
        detection_threshold: Threshold for is_changepoint() method.

    Example:
        >>> config = BOCDConfig(
        ...     hazard_rate=1/250,  # Expect 1 change per 250 bars
        ...     detection_threshold=0.8,
        ... )
    """

    hazard_rate: float = Field(
        default=0.004, gt=0.0, lt=1.0, description="P(changepoint) per step"
    )
    mu0: float = Field(default=0.0, description="Prior mean")
    kappa0: float = Field(default=1.0, gt=0.0, description="Prior precision weight")
    alpha0: float = Field(default=1.0, gt=0.0, description="Prior shape (df/2)")
    beta0: float = Field(default=1.0, gt=0.0, description="Prior scale")
    max_run_length: int = Field(
        default=500, ge=100, description="Maximum tracked run length"
    )
    detection_threshold: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Changepoint detection threshold"
    )

    model_config = {"frozen": True}
