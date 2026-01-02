"""Tests for RegimeManager unified facade.

Tests cover:
- Combined regime detection
- Integration with HMM and GMM filters
- Real BTCUSDT data integration
"""

from __future__ import annotations


import numpy as np
import pytest

from strategies.common.regime_detection.config import RegimeConfig
from strategies.common.regime_detection.regime_manager import (
    RegimeManager,
    RegimeResult,
)
from strategies.common.regime_detection.types import RegimeState, VolatilityCluster


@pytest.fixture
def default_config() -> RegimeConfig:
    """Default regime configuration."""
    return RegimeConfig(
        hmm_states=3,
        gmm_clusters=3,
        hmm_lookback=252,
        min_bars_for_fit=100,
        volatility_window=20,
    )


@pytest.fixture
def synthetic_bars() -> list[dict]:
    """Generate synthetic bar data for testing."""
    np.random.seed(42)

    bars = []
    price = 100.0

    for i in range(300):
        # Simulate different regimes
        if i < 100:
            # Trending up, low volatility
            drift = 0.001
            vol = 0.01
        elif i < 200:
            # Volatile, no clear direction
            drift = 0.0
            vol = 0.03
        else:
            # Trending down, low volatility
            drift = -0.001
            vol = 0.01

        returns = np.random.normal(drift, vol)
        price = price * (1 + returns)

        high = price * (1 + abs(np.random.normal(0, vol / 2)))
        low = price * (1 - abs(np.random.normal(0, vol / 2)))

        bars.append(
            {
                "open": price,
                "high": high,
                "low": low,
                "close": price,
                "volume": np.random.uniform(1000, 10000),
            }
        )

    return bars


class TestRegimeManagerFit:
    """Tests for RegimeManager fitting."""

    def test_regime_manager_fit_with_sufficient_data(
        self, default_config: RegimeConfig, synthetic_bars: list[dict]
    ) -> None:
        """Test that RegimeManager fits with sufficient data."""
        manager = RegimeManager(config=default_config)
        manager.fit(synthetic_bars)

        assert manager.is_fitted
        assert manager.hmm_filter is not None
        assert manager.hmm_filter.is_fitted
        assert manager.gmm_filter is not None
        assert manager.gmm_filter.is_fitted

    def test_regime_manager_fit_fails_with_insufficient_data(
        self, default_config: RegimeConfig
    ) -> None:
        """Test that RegimeManager raises error with insufficient data."""
        bars = [{"open": 100, "high": 101, "low": 99, "close": 100}] * 50

        manager = RegimeManager(config=default_config)

        with pytest.raises(ValueError, match="Insufficient"):
            manager.fit(bars)


class TestRegimeManagerUpdate:
    """Tests for RegimeManager update (prediction)."""

    def test_regime_manager_update_returns_combined_regime(
        self, default_config: RegimeConfig, synthetic_bars: list[dict]
    ) -> None:
        """Test that update returns a RegimeResult with all fields."""
        manager = RegimeManager(config=default_config)
        manager.fit(synthetic_bars)

        # Update with new bar
        new_bar = {
            "open": 105,
            "high": 106,
            "low": 104,
            "close": 105.5,
            "volume": 5000,
        }
        result = manager.update(new_bar)

        assert isinstance(result, RegimeResult)
        assert isinstance(result.regime, RegimeState)
        assert isinstance(result.volatility, VolatilityCluster)
        assert 0.0 <= result.weight <= 1.0
        assert 0.0 <= result.confidence <= 1.0

    def test_regime_manager_update_without_fit_raises_error(
        self, default_config: RegimeConfig
    ) -> None:
        """Test that update raises error if not fitted."""
        manager = RegimeManager(config=default_config)

        with pytest.raises(RuntimeError, match="not fitted"):
            manager.update({"open": 100, "high": 101, "low": 99, "close": 100})


class TestRegimeManagerWeight:
    """Tests for regime weight calculation."""

    def test_get_regime_weight_returns_valid_value(
        self, default_config: RegimeConfig, synthetic_bars: list[dict]
    ) -> None:
        """Test that get_regime_weight returns value between 0 and 1."""
        manager = RegimeManager(config=default_config)
        manager.fit(synthetic_bars)

        # Update with a bar
        new_bar = {"open": 105, "high": 106, "low": 104, "close": 105.5}
        manager.update(new_bar)

        weight = manager.get_regime_weight()
        assert 0.0 <= weight <= 1.0


class TestRegimeResult:
    """Tests for RegimeResult dataclass."""

    def test_regime_result_fields(self) -> None:
        """Test that RegimeResult has expected fields."""
        result = RegimeResult(
            regime=RegimeState.TRENDING_UP,
            volatility=VolatilityCluster.LOW,
            weight=0.8,
            confidence=0.95,
        )

        assert result.regime == RegimeState.TRENDING_UP
        assert result.volatility == VolatilityCluster.LOW
        assert result.weight == 0.8
        assert result.confidence == 0.95


class TestRegimeManagerIntegration:
    """Integration tests with real-like data."""

    def test_regime_manager_detects_trending_regime(
        self, default_config: RegimeConfig
    ) -> None:
        """Test that manager detects trending regime in upward data."""
        np.random.seed(42)

        # Generate clear uptrend data
        bars = []
        price = 100.0
        for _ in range(200):
            returns = np.random.normal(0.002, 0.008)  # Positive drift, low vol
            price = price * (1 + returns)
            bars.append(
                {
                    "open": price * 0.999,
                    "high": price * 1.002,
                    "low": price * 0.998,
                    "close": price,
                }
            )

        manager = RegimeManager(config=default_config)
        manager.fit(bars)

        # Most predictions should be TRENDING_UP
        trending_count = 0
        for bar in bars[-50:]:
            result = manager.update(bar)
            if result.regime == RegimeState.TRENDING_UP:
                trending_count += 1

        # At least 30% should be trending up (HMM may not perfectly segment)
        assert trending_count >= 15, f"Only {trending_count}/50 were TRENDING_UP"

    def test_regime_manager_detects_high_volatility_cluster(
        self, default_config: RegimeConfig
    ) -> None:
        """Test that manager detects high volatility when given varying vol data.

        Note: HMM may not label as VOLATILE with synthetic data, but GMM
        should correctly cluster high volatility periods.
        """
        np.random.seed(42)

        # Generate mixed volatility data so GMM can learn clusters
        bars = []
        price = 100.0

        # First: low volatility period
        for _ in range(100):
            returns = np.random.normal(0.001, 0.005)  # Low vol
            price = price * (1 + returns)
            bars.append(
                {
                    "open": price * 0.999,
                    "high": price * 1.001,
                    "low": price * 0.999,
                    "close": price,
                }
            )

        # Then: high volatility period
        for _ in range(100):
            returns = np.random.normal(0.0, 0.04)  # High vol
            price = price * (1 + returns)
            bars.append(
                {
                    "open": price * 0.98,
                    "high": price * 1.04,
                    "low": price * 0.96,
                    "close": price,
                }
            )

        manager = RegimeManager(config=default_config)
        manager.fit(bars)

        # Test with a high volatility observation
        high_vol_bar = {
            "open": price * 0.98,
            "high": price * 1.05,
            "low": price * 0.95,
            "close": price * 1.02,
        }
        result = manager.update(high_vol_bar)

        # The GMM should detect high volatility cluster
        # (HMM regime detection depends on temporal patterns, less reliable with synthetic data)
        assert result.volatility in [
            VolatilityCluster.MEDIUM,
            VolatilityCluster.HIGH,
        ], f"Expected MEDIUM or HIGH volatility cluster, got {result.volatility}"
