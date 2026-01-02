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
