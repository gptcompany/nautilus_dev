"""Test fixtures for regime detection module.

Provides fixtures for BOCD, HMM, GMM detectors and ensemble testing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

from strategies.common.regime_detection import (
    BOCD,
    BOCDAdapter,
    BOCDConfig,
    EnsembleConfig,
    GMMAdapter,
    GMMVolatilityFilter,
    HMMAdapter,
    HMMRegimeFilter,
    RegimeEnsemble,
    RegimeState,
)

if TYPE_CHECKING:
    from numpy.typing import NDArray


# =============================================================================
# Data Fixtures
# =============================================================================


@pytest.fixture
def trending_up_returns() -> NDArray[np.floating]:
    """Generate returns for an upward trending market.

    Positive mean with moderate volatility.
    """
    np.random.seed(42)
    n = 200
    trend = 0.002  # 0.2% daily drift
    volatility = 0.01  # 1% daily volatility
    returns = np.random.normal(trend, volatility, n)
    return returns


@pytest.fixture
def trending_down_returns() -> NDArray[np.floating]:
    """Generate returns for a downward trending market.

    Negative mean with moderate volatility.
    """
    np.random.seed(43)
    n = 200
    trend = -0.002  # -0.2% daily drift
    volatility = 0.01
    returns = np.random.normal(trend, volatility, n)
    return returns


@pytest.fixture
def ranging_returns() -> NDArray[np.floating]:
    """Generate returns for a ranging/sideways market.

    Zero mean with low volatility.
    """
    np.random.seed(44)
    n = 200
    volatility = 0.005  # 0.5% daily volatility
    returns = np.random.normal(0, volatility, n)
    return returns


@pytest.fixture
def volatile_returns() -> NDArray[np.floating]:
    """Generate returns for a volatile market.

    Zero mean with high volatility.
    """
    np.random.seed(45)
    n = 200
    volatility = 0.03  # 3% daily volatility
    returns = np.random.normal(0, volatility, n)
    return returns


@pytest.fixture
def regime_change_returns() -> NDArray[np.floating]:
    """Generate returns with a clear regime change in the middle.

    First half: low volatility trending up
    Second half: high volatility ranging
    """
    np.random.seed(46)
    n = 200

    # First half: trending up with low volatility
    first_half = np.random.normal(0.002, 0.008, n // 2)

    # Second half: high volatility ranging
    second_half = np.random.normal(0, 0.025, n // 2)

    return np.concatenate([first_half, second_half])


@pytest.fixture
def covid_crash_returns() -> NDArray[np.floating]:
    """Simulate COVID-19 crash pattern (Feb-Mar 2020).

    Sharp transition from low-volatility trending to
    high-volatility crash.
    """
    np.random.seed(47)

    # Pre-crash: 50 bars of calm uptrend
    pre_crash = np.random.normal(0.001, 0.008, 50)

    # Crash: 20 bars of sharp decline with extreme volatility
    crash = np.random.normal(-0.02, 0.035, 20)

    # Recovery: 30 bars of volatile recovery
    recovery = np.random.normal(0.005, 0.025, 30)

    return np.concatenate([pre_crash, crash, recovery])


@pytest.fixture
def prices_from_returns(trending_up_returns: NDArray[np.floating]) -> NDArray[np.floating]:
    """Convert returns to prices starting from 100."""
    initial_price = 100.0
    prices = initial_price * np.cumprod(1 + trending_up_returns)
    return np.insert(prices, 0, initial_price)


# =============================================================================
# Detector Fixtures
# =============================================================================


@pytest.fixture
def bocd_config() -> BOCDConfig:
    """Default BOCD configuration for testing."""
    return BOCDConfig(
        hazard_rate=0.01,  # Expect change every 100 bars
        detection_threshold=0.5,
        max_run_length=200,
    )


@pytest.fixture
def bocd_detector(bocd_config: BOCDConfig) -> BOCD:
    """Fresh BOCD detector instance."""
    return BOCD(bocd_config)


@pytest.fixture
def bocd_adapter(bocd_detector: BOCD) -> BOCDAdapter:
    """BOCD adapter for ensemble testing."""
    return BOCDAdapter(bocd_detector, warmup_bars=20)


@pytest.fixture
def hmm_filter() -> HMMRegimeFilter:
    """Fresh HMM filter instance."""
    return HMMRegimeFilter(
        n_states=3,
        n_iter=50,
        n_init=3,
        min_samples=50,
    )


@pytest.fixture
def hmm_adapter(hmm_filter: HMMRegimeFilter) -> HMMAdapter:
    """HMM adapter for ensemble testing."""
    return HMMAdapter(hmm_filter, warmup_bars=50, volatility_window=20)


@pytest.fixture
def gmm_filter() -> GMMVolatilityFilter:
    """Fresh GMM filter instance."""
    return GMMVolatilityFilter(
        n_clusters=3,
        n_init=3,
        min_samples=50,
    )


@pytest.fixture
def gmm_adapter(gmm_filter: GMMVolatilityFilter) -> GMMAdapter:
    """GMM adapter for ensemble testing."""
    return GMMAdapter(gmm_filter, warmup_bars=50, volatility_window=20)


# =============================================================================
# Ensemble Fixtures
# =============================================================================


@pytest.fixture
def ensemble_config() -> EnsembleConfig:
    """Default ensemble configuration for testing."""
    return EnsembleConfig(
        voting_threshold=0.5,
        min_detectors=2,
        use_weighted_voting=True,
        default_weights={"bocd": 0.4, "hmm": 0.35, "gmm": 0.25},
    )


@pytest.fixture
def basic_ensemble(
    bocd_adapter: BOCDAdapter,
    hmm_adapter: HMMAdapter,
    gmm_adapter: GMMAdapter,
) -> RegimeEnsemble:
    """Basic ensemble with all three detectors (equal weights)."""
    return RegimeEnsemble(
        detectors={
            "bocd": bocd_adapter,
            "hmm": hmm_adapter,
            "gmm": gmm_adapter,
        },
        weights={"bocd": 1.0, "hmm": 1.0, "gmm": 1.0},
        voting_threshold=0.5,
        min_detectors=2,
        use_weighted_voting=False,
    )


@pytest.fixture
def weighted_ensemble(
    bocd_adapter: BOCDAdapter,
    hmm_adapter: HMMAdapter,
    gmm_adapter: GMMAdapter,
    ensemble_config: EnsembleConfig,
) -> RegimeEnsemble:
    """Weighted ensemble with configured weights."""
    return RegimeEnsemble(
        detectors={
            "bocd": bocd_adapter,
            "hmm": hmm_adapter,
            "gmm": gmm_adapter,
        },
        weights=ensemble_config.default_weights,
        voting_threshold=ensemble_config.voting_threshold,
        min_detectors=ensemble_config.min_detectors,
        use_weighted_voting=ensemble_config.use_weighted_voting,
    )


# =============================================================================
# Mock Detector Fixtures (for unit testing)
# =============================================================================


class MockDetector:
    """Mock detector for testing ensemble voting logic."""

    def __init__(
        self,
        regime: RegimeState = RegimeState.RANGING,
        confidence: float = 0.8,
        warmed_up: bool = True,
    ) -> None:
        """Initialize mock detector.

        Args:
            regime: Fixed regime to return.
            confidence: Fixed confidence to return.
            warmed_up: Whether detector is warmed up.
        """
        self._regime = regime
        self._confidence = confidence
        self._warmed_up = warmed_up
        self.update_count = 0

    def update(self, value: float) -> None:
        """Track update calls."""
        self.update_count += 1

    def current_regime(self) -> RegimeState:
        """Return fixed regime."""
        return self._regime

    def confidence(self) -> float:
        """Return fixed confidence."""
        return self._confidence

    def is_warmed_up(self) -> bool:
        """Return warmup status."""
        return self._warmed_up

    def set_regime(self, regime: RegimeState) -> None:
        """Update the regime (for testing)."""
        self._regime = regime

    def set_confidence(self, confidence: float) -> None:
        """Update confidence (for testing)."""
        self._confidence = confidence


@pytest.fixture
def mock_trending_detector() -> MockDetector:
    """Mock detector that always returns TRENDING_UP."""
    return MockDetector(RegimeState.TRENDING_UP, confidence=0.8)


@pytest.fixture
def mock_ranging_detector() -> MockDetector:
    """Mock detector that always returns RANGING."""
    return MockDetector(RegimeState.RANGING, confidence=0.7)


@pytest.fixture
def mock_volatile_detector() -> MockDetector:
    """Mock detector that always returns VOLATILE."""
    return MockDetector(RegimeState.VOLATILE, confidence=0.9)


@pytest.fixture
def mock_cold_detector() -> MockDetector:
    """Mock detector that is not warmed up."""
    return MockDetector(RegimeState.RANGING, confidence=0.5, warmed_up=False)
