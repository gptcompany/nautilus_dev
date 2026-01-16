"""Regime detection components for NautilusTrader strategies.

This module provides:
- HMMRegimeFilter: Hidden Markov Model for regime detection
- GMMVolatilityFilter: Gaussian Mixture Model for volatility clustering
- RegimeManager: Unified facade for regime detection
- RegimeState, VolatilityCluster: Enum types for regime states
- BOCD: Bayesian Online Changepoint Detection (Spec 026)
- BOCDConfig: Configuration for BOCD detector
- RegimeEnsemble: Ensemble voting across multiple detectors (Spec 036)
- EnsembleConfig: Configuration for ensemble voting
- Adapters: BOCDAdapter, HMMAdapter, GMMAdapter for protocol compatibility
"""

from strategies.common.regime_detection.bocd import BOCD, Changepoint
from strategies.common.regime_detection.config import BOCDConfig, EnsembleConfig, RegimeConfig
from strategies.common.regime_detection.ensemble import (
    BaseRegimeDetector,
    BOCDAdapter,
    GMMAdapter,
    HMMAdapter,
    RegimeEnsemble,
)
from strategies.common.regime_detection.events import RegimeChangeEvent, RegimeVote
from strategies.common.regime_detection.gmm_filter import GMMVolatilityFilter
from strategies.common.regime_detection.hmm_filter import HMMRegimeFilter
from strategies.common.regime_detection.regime_manager import (
    RegimeManager,
    RegimeResult,
)
from strategies.common.regime_detection.types import RegimeState, VolatilityCluster

__all__ = [
    "BaseRegimeDetector",
    "BOCD",
    "BOCDAdapter",
    "BOCDConfig",
    "Changepoint",
    "EnsembleConfig",
    "GMMAdapter",
    "GMMVolatilityFilter",
    "HMMAdapter",
    "HMMRegimeFilter",
    "RegimeChangeEvent",
    "RegimeConfig",
    "RegimeEnsemble",
    "RegimeManager",
    "RegimeResult",
    "RegimeState",
    "RegimeVote",
    "VolatilityCluster",
]
