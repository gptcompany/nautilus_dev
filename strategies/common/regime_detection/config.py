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

    hazard_rate: float = Field(default=0.004, gt=0.0, lt=1.0, description="P(changepoint) per step")
    mu0: float = Field(default=0.0, description="Prior mean")
    kappa0: float = Field(default=1.0, gt=0.0, description="Prior precision weight")
    alpha0: float = Field(default=1.0, gt=0.0, description="Prior shape (df/2)")
    beta0: float = Field(default=1.0, gt=0.0, description="Prior scale")
    max_run_length: int = Field(default=500, ge=100, description="Maximum tracked run length")
    detection_threshold: float = Field(
        default=0.8, ge=0.0, le=1.0, description="Changepoint detection threshold"
    )

    model_config = {"frozen": True}


class EnsembleConfig(BaseModel):
    """Configuration for RegimeEnsemble voting system.

    Configures ensemble voting behavior including threshold,
    minimum detectors, and voting strategy.

    Attributes:
        voting_threshold: Threshold for regime change confirmation (0.0-1.0).
                         For majority voting: fraction of detectors that must agree.
                         For weighted voting: minimum weighted confidence.
        min_detectors: Minimum number of warmed-up detectors required for voting.
        use_weighted_voting: If True, use confidence-weighted voting.
                            If False, use simple majority voting.
        data_gap_threshold_seconds: Threshold in seconds for detecting data gaps.
                                   If gap > threshold, reset BOCD priors (FR-012).
        default_weights: Default weights for each detector type.

    Example:
        >>> config = EnsembleConfig(
        ...     voting_threshold=0.6,
        ...     min_detectors=2,
        ...     use_weighted_voting=True,
        ...     default_weights={"bocd": 0.5, "hmm": 0.3, "gmm": 0.2},
        ... )
    """

    voting_threshold: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Threshold for regime change confirmation"
    )
    min_detectors: int = Field(default=2, ge=1, description="Minimum detectors required for voting")
    use_weighted_voting: bool = Field(default=True, description="Use weighted vs majority voting")
    data_gap_threshold_seconds: int = Field(
        default=3600, ge=60, description="Gap threshold for BOCD prior reset (seconds)"
    )
    default_weights: dict[str, float] = Field(
        default_factory=lambda: {"bocd": 0.4, "hmm": 0.35, "gmm": 0.25},
        description="Default detector weights",
    )

    model_config = {"frozen": True}
