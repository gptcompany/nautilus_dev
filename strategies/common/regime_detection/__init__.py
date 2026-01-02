"""Regime detection components for NautilusTrader strategies.

This module provides:
- HMMRegimeFilter: Hidden Markov Model for regime detection
- GMMVolatilityFilter: Gaussian Mixture Model for volatility clustering
- RegimeManager: Unified facade for regime detection
- RegimeState, VolatilityCluster: Enum types for regime states
"""

from strategies.common.regime_detection.config import RegimeConfig
from strategies.common.regime_detection.gmm_filter import GMMVolatilityFilter
from strategies.common.regime_detection.hmm_filter import HMMRegimeFilter
from strategies.common.regime_detection.regime_manager import (
    RegimeManager,
    RegimeResult,
)
from strategies.common.regime_detection.types import RegimeState, VolatilityCluster

__all__ = [
    "GMMVolatilityFilter",
    "HMMRegimeFilter",
    "RegimeConfig",
    "RegimeManager",
    "RegimeResult",
    "RegimeState",
    "VolatilityCluster",
]
