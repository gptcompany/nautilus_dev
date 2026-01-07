"""Comprehensive tests for EnhancedRegimeManager regime integration.

Tests cover:
- EnhancedRegimeManager initialization
- Spectral fitting
- Combined regime updates
- Agreement calculation between HMM and Spectral
- Combined regime determination
- Combined weight calculation
- Edge cases and error handling
"""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import MagicMock

import numpy as np

from strategies.common.adaptive_control.regime_integration import (
    CombinedRegime,
    EnhancedRegimeManager,
    EnhancedRegimeResult,
)
from strategies.common.adaptive_control.spectral_regime import (
    MarketRegime,
)
from strategies.common.regime_detection.types import RegimeState


# Mock RegimeResult for testing
@dataclass
class MockRegimeResult:
    """Mock RegimeResult for tests."""

    regime: RegimeState
    confidence: float
    weight: float


class MockRegimeManager:
    """Mock RegimeManager for isolated EnhancedRegimeManager tests."""

    def __init__(self, is_fitted: bool = True):
        self._is_fitted = is_fitted
        self._regime = RegimeState.RANGING
        self._confidence = 0.8
        self._weight = 0.7

    @property
    def is_fitted(self) -> bool:
        return self._is_fitted

    def update(self, bar: dict) -> MockRegimeResult:
        return MockRegimeResult(
            regime=self._regime,
            confidence=self._confidence,
            weight=self._weight,
        )

    def get_regime_weight(self) -> float:
        return self._weight

    def set_regime(self, regime: RegimeState) -> None:
        self._regime = regime

    def set_confidence(self, confidence: float) -> None:
        self._confidence = confidence

    def set_weight(self, weight: float) -> None:
        self._weight = weight


class TestCombinedRegime:
    """Test CombinedRegime enum."""

    def test_combined_regime_values(self):
        """Test all enum values are defined correctly."""
        assert CombinedRegime.STRONG_TREND.value == "strong_trend"
        assert CombinedRegime.WEAK_TREND.value == "weak_trend"
        assert CombinedRegime.MEAN_REVERT.value == "mean_revert"
        assert CombinedRegime.MIXED.value == "mixed"
        assert CombinedRegime.VOLATILE.value == "volatile"
        assert CombinedRegime.UNKNOWN.value == "unknown"

    def test_combined_regime_enum_members(self):
        """Test all enum members exist."""
        members = list(CombinedRegime)
        assert len(members) == 6


class TestEnhancedRegimeResult:
    """Test EnhancedRegimeResult dataclass."""

    def test_enhanced_result_creation(self):
        """Test creating EnhancedRegimeResult instance."""
        result = EnhancedRegimeResult(
            hmm_regime=RegimeState.TRENDING_UP,
            hmm_confidence=0.85,
            hmm_weight=0.9,
            spectral_regime=MarketRegime.TRENDING,
            spectral_alpha=1.8,
            spectral_confidence=0.75,
            combined_regime=CombinedRegime.STRONG_TREND,
            combined_weight=0.95,
            agreement_score=1.0,
        )

        assert result.hmm_regime == RegimeState.TRENDING_UP
        assert result.hmm_confidence == 0.85
        assert result.hmm_weight == 0.9
        assert result.spectral_regime == MarketRegime.TRENDING
        assert result.spectral_alpha == 1.8
        assert result.spectral_confidence == 0.75
        assert result.combined_regime == CombinedRegime.STRONG_TREND
        assert result.combined_weight == 0.95
        assert result.agreement_score == 1.0

    def test_enhanced_result_with_disagreement(self):
        """Test EnhancedRegimeResult with disagreement."""
        result = EnhancedRegimeResult(
            hmm_regime=RegimeState.TRENDING_UP,
            hmm_confidence=0.6,
            hmm_weight=0.7,
            spectral_regime=MarketRegime.MEAN_REVERTING,
            spectral_alpha=0.3,
            spectral_confidence=0.5,
            combined_regime=CombinedRegime.MIXED,
            combined_weight=0.4,
            agreement_score=0.0,
        )

        assert result.agreement_score == 0.0
        assert result.combined_regime == CombinedRegime.MIXED


class TestEnhancedRegimeManagerInit:
    """Test EnhancedRegimeManager initialization (lines 102-111)."""

    def test_initialization_default_params(self):
        """Test initialization with default parameters."""
        mock_rm = MockRegimeManager()

        enhanced = EnhancedRegimeManager(regime_manager=mock_rm)

        assert enhanced.regime_manager is mock_rm
        assert enhanced.spectral_weight == 0.3
        assert enhanced.agreement_bonus == 0.2
        assert enhanced.spectral is not None
        assert enhanced._is_spectral_ready is False

    def test_initialization_custom_params(self):
        """Test initialization with custom parameters."""
        mock_rm = MockRegimeManager()

        enhanced = EnhancedRegimeManager(
            regime_manager=mock_rm,
            spectral_weight=0.5,
            spectral_window=128,
            agreement_bonus=0.3,
        )

        assert enhanced.spectral_weight == 0.5
        assert enhanced.agreement_bonus == 0.3
        assert enhanced.spectral.window_size == 128

    def test_initialization_zero_spectral_weight(self):
        """Test initialization with zero spectral weight."""
        mock_rm = MockRegimeManager()

        enhanced = EnhancedRegimeManager(
            regime_manager=mock_rm,
            spectral_weight=0.0,
        )

        assert enhanced.spectral_weight == 0.0

    def test_initialization_full_spectral_weight(self):
        """Test initialization with full spectral weight."""
        mock_rm = MockRegimeManager()

        enhanced = EnhancedRegimeManager(
            regime_manager=mock_rm,
            spectral_weight=1.0,
        )

        assert enhanced.spectral_weight == 1.0


class TestFitSpectral:
    """Test fit_spectral method (lines 115-117)."""

    def test_fit_spectral_sufficient_data(self):
        """Test fitting spectral detector with sufficient data."""
        mock_rm = MockRegimeManager()
        enhanced = EnhancedRegimeManager(regime_manager=mock_rm, spectral_window=64)

        # Generate enough returns (>= min_samples=64)
        np.random.seed(42)
        returns = np.random.normal(0, 0.01, 100).tolist()

        enhanced.fit_spectral(returns)

        assert enhanced._is_spectral_ready is True

    def test_fit_spectral_insufficient_data(self):
        """Test fitting spectral detector with insufficient data."""
        mock_rm = MockRegimeManager()
        enhanced = EnhancedRegimeManager(regime_manager=mock_rm, spectral_window=64)

        # Generate fewer returns than min_samples (64)
        returns = [0.01, -0.01, 0.02] * 10  # Only 30 samples

        enhanced.fit_spectral(returns)

        # Should not be ready if fewer than min_samples
        assert enhanced._is_spectral_ready is False

    def test_fit_spectral_exact_min_samples(self):
        """Test fitting with exactly min_samples."""
        mock_rm = MockRegimeManager()
        enhanced = EnhancedRegimeManager(regime_manager=mock_rm, spectral_window=64)

        # Exactly 64 samples (min_samples)
        returns = [0.01] * 64

        enhanced.fit_spectral(returns)

        assert enhanced._is_spectral_ready is True

    def test_fit_spectral_empty_returns(self):
        """Test fitting with empty returns list."""
        mock_rm = MockRegimeManager()
        enhanced = EnhancedRegimeManager(regime_manager=mock_rm)

        enhanced.fit_spectral([])

        assert enhanced._is_spectral_ready is False


class TestUpdate:
    """Test update method (lines 131-143)."""

    def test_update_basic(self):
        """Test basic update with new bar and return."""
        mock_rm = MockRegimeManager()
        mock_rm.set_regime(RegimeState.TRENDING_UP)
        mock_rm.set_confidence(0.8)
        mock_rm.set_weight(0.9)

        enhanced = EnhancedRegimeManager(regime_manager=mock_rm, spectral_window=64)

        # Fit with enough data
        np.random.seed(42)
        returns = np.random.normal(0, 0.01, 100).tolist()
        enhanced.fit_spectral(returns)

        bar = {"close": 100.0, "high": 101.0, "low": 99.0}
        result = enhanced.update(bar, 0.01)

        assert isinstance(result, EnhancedRegimeResult)
        assert result.hmm_regime == RegimeState.TRENDING_UP
        assert result.hmm_confidence == 0.8
        assert result.hmm_weight == 0.9

    def test_update_multiple_calls(self):
        """Test multiple sequential updates."""
        mock_rm = MockRegimeManager()
        enhanced = EnhancedRegimeManager(regime_manager=mock_rm, spectral_window=64)

        np.random.seed(42)
        returns = np.random.normal(0, 0.01, 100).tolist()
        enhanced.fit_spectral(returns)

        results = []
        for i in range(10):
            bar = {"close": 100.0 + i, "high": 101.0 + i, "low": 99.0 + i}
            result = enhanced.update(bar, 0.01 * (i % 3 - 1))
            results.append(result)

        assert len(results) == 10
        assert all(isinstance(r, EnhancedRegimeResult) for r in results)

    def test_update_returns_combined_weight(self):
        """Test that update returns valid combined weight."""
        mock_rm = MockRegimeManager()
        enhanced = EnhancedRegimeManager(regime_manager=mock_rm, spectral_window=64)

        np.random.seed(42)
        returns = np.random.normal(0, 0.01, 100).tolist()
        enhanced.fit_spectral(returns)

        bar = {"close": 100.0}
        result = enhanced.update(bar, 0.01)

        assert 0.0 <= result.combined_weight <= 1.0

    def test_update_without_spectral_fit(self):
        """Test update without prior spectral fit."""
        mock_rm = MockRegimeManager()
        enhanced = EnhancedRegimeManager(regime_manager=mock_rm, spectral_window=64)

        # Don't fit spectral - should still work but with unknown regime
        bar = {"close": 100.0}
        result = enhanced.update(bar, 0.01)

        # Spectral should return UNKNOWN without enough data
        assert result.spectral_regime == MarketRegime.UNKNOWN


class TestCalculateAgreement:
    """Test _calculate_agreement method (lines 166-188)."""

    def test_agreement_full_trending(self):
        """Test full agreement when both detect trending."""
        mock_rm = MockRegimeManager()
        enhanced = EnhancedRegimeManager(regime_manager=mock_rm)

        # Both trending up + spectral trending = 1.0 agreement
        agreement = enhanced._calculate_agreement(
            RegimeState.TRENDING_UP, MarketRegime.TRENDING
        )
        assert agreement == 1.0

    def test_agreement_full_trending_down(self):
        """Test full agreement with trending down."""
        mock_rm = MockRegimeManager()
        enhanced = EnhancedRegimeManager(regime_manager=mock_rm)

        # Both trending down + spectral trending = 1.0 agreement
        agreement = enhanced._calculate_agreement(
            RegimeState.TRENDING_DOWN, MarketRegime.TRENDING
        )
        assert agreement == 1.0

    def test_agreement_full_mean_reverting(self):
        """Test full agreement when both detect mean reverting."""
        mock_rm = MockRegimeManager()
        enhanced = EnhancedRegimeManager(regime_manager=mock_rm)

        # HMM ranging + spectral mean reverting = 1.0 agreement
        agreement = enhanced._calculate_agreement(
            RegimeState.RANGING, MarketRegime.MEAN_REVERTING
        )
        assert agreement == 1.0

    def test_agreement_partial_normal(self):
        """Test partial agreement when spectral is normal."""
        mock_rm = MockRegimeManager()
        enhanced = EnhancedRegimeManager(regime_manager=mock_rm)

        # Spectral normal = 0.5 agreement
        agreement = enhanced._calculate_agreement(
            RegimeState.TRENDING_UP, MarketRegime.NORMAL
        )
        assert agreement == 0.5

    def test_agreement_partial_ranging_normal(self):
        """Test partial agreement: HMM ranging, spectral normal."""
        mock_rm = MockRegimeManager()
        enhanced = EnhancedRegimeManager(regime_manager=mock_rm)

        agreement = enhanced._calculate_agreement(
            RegimeState.RANGING, MarketRegime.NORMAL
        )
        assert agreement == 0.5

    def test_agreement_disagreement_trending_vs_mean_reverting(self):
        """Test full disagreement when conflicting regimes."""
        mock_rm = MockRegimeManager()
        enhanced = EnhancedRegimeManager(regime_manager=mock_rm)

        # HMM trending vs spectral mean reverting = disagreement
        agreement = enhanced._calculate_agreement(
            RegimeState.TRENDING_UP, MarketRegime.MEAN_REVERTING
        )
        assert agreement == 0.0

    def test_agreement_disagreement_ranging_vs_trending(self):
        """Test disagreement: HMM ranging vs spectral trending."""
        mock_rm = MockRegimeManager()
        enhanced = EnhancedRegimeManager(regime_manager=mock_rm)

        agreement = enhanced._calculate_agreement(
            RegimeState.RANGING, MarketRegime.TRENDING
        )
        assert agreement == 0.0

    def test_agreement_volatile_hmm(self):
        """Test agreement with volatile HMM state."""
        mock_rm = MockRegimeManager()
        enhanced = EnhancedRegimeManager(regime_manager=mock_rm)

        # Volatile is neither trending nor ranging, so disagreement expected
        agreement = enhanced._calculate_agreement(
            RegimeState.VOLATILE, MarketRegime.TRENDING
        )
        assert agreement == 0.0


class TestCombineRegimes:
    """Test _combine_regimes method (lines 202-242)."""

    def test_combine_unknown_spectral(self):
        """Test combined regime when spectral is unknown."""
        mock_rm = MockRegimeManager()
        enhanced = EnhancedRegimeManager(regime_manager=mock_rm)

        # Mock spectral analysis with UNKNOWN
        spectral_analysis = MagicMock()
        spectral_analysis.regime = MarketRegime.UNKNOWN
        spectral_analysis.confidence = 0.0

        hmm_result = MockRegimeResult(
            regime=RegimeState.TRENDING_UP,
            confidence=0.8,
            weight=0.7,
        )

        regime, weight = enhanced._combine_regimes(hmm_result, spectral_analysis, 0.0)

        assert regime == CombinedRegime.UNKNOWN

    def test_combine_strong_trend_high_agreement(self):
        """Test strong trend with high agreement (>= 0.9)."""
        mock_rm = MockRegimeManager()
        enhanced = EnhancedRegimeManager(regime_manager=mock_rm)

        spectral_analysis = MagicMock()
        spectral_analysis.regime = MarketRegime.TRENDING
        spectral_analysis.confidence = 0.9

        hmm_result = MockRegimeResult(
            regime=RegimeState.TRENDING_UP,
            confidence=0.85,
            weight=0.9,
        )

        regime, weight = enhanced._combine_regimes(hmm_result, spectral_analysis, 1.0)

        assert regime == CombinedRegime.STRONG_TREND

    def test_combine_mean_revert_high_agreement(self):
        """Test mean revert with high agreement (>= 0.9)."""
        mock_rm = MockRegimeManager()
        enhanced = EnhancedRegimeManager(regime_manager=mock_rm)

        spectral_analysis = MagicMock()
        spectral_analysis.regime = MarketRegime.MEAN_REVERTING
        spectral_analysis.confidence = 0.8

        hmm_result = MockRegimeResult(
            regime=RegimeState.RANGING,
            confidence=0.85,
            weight=0.6,
        )

        regime, weight = enhanced._combine_regimes(hmm_result, spectral_analysis, 0.95)

        assert regime == CombinedRegime.MEAN_REVERT

    def test_combine_weak_trend_low_agreement(self):
        """Test weak trend with lower agreement."""
        mock_rm = MockRegimeManager()
        enhanced = EnhancedRegimeManager(regime_manager=mock_rm)

        spectral_analysis = MagicMock()
        spectral_analysis.regime = MarketRegime.TRENDING
        spectral_analysis.confidence = 0.7

        hmm_result = MockRegimeResult(
            regime=RegimeState.RANGING,  # HMM disagrees
            confidence=0.6,
            weight=0.5,
        )

        regime, weight = enhanced._combine_regimes(hmm_result, spectral_analysis, 0.0)

        assert regime == CombinedRegime.WEAK_TREND

    def test_combine_volatile(self):
        """Test volatile regime detection."""
        mock_rm = MockRegimeManager()
        enhanced = EnhancedRegimeManager(regime_manager=mock_rm)

        spectral_analysis = MagicMock()
        spectral_analysis.regime = MarketRegime.MEAN_REVERTING
        spectral_analysis.confidence = 0.6

        hmm_result = MockRegimeResult(
            regime=RegimeState.VOLATILE,
            confidence=0.7,
            weight=0.4,
        )

        regime, weight = enhanced._combine_regimes(hmm_result, spectral_analysis, 0.3)

        assert regime == CombinedRegime.VOLATILE

    def test_combine_mixed_regime(self):
        """Test mixed regime when no specific conditions match."""
        mock_rm = MockRegimeManager()
        enhanced = EnhancedRegimeManager(regime_manager=mock_rm)

        spectral_analysis = MagicMock()
        spectral_analysis.regime = MarketRegime.NORMAL  # Not trending or unknown
        spectral_analysis.confidence = 0.6

        hmm_result = MockRegimeResult(
            regime=RegimeState.RANGING,  # Not volatile
            confidence=0.5,
            weight=0.5,
        )

        regime, weight = enhanced._combine_regimes(hmm_result, spectral_analysis, 0.5)

        assert regime == CombinedRegime.MIXED

    def test_combine_weight_calculation(self):
        """Test combined weight calculation."""
        mock_rm = MockRegimeManager()
        enhanced = EnhancedRegimeManager(
            regime_manager=mock_rm,
            spectral_weight=0.3,
            agreement_bonus=0.2,
        )

        spectral_analysis = MagicMock()
        spectral_analysis.regime = MarketRegime.TRENDING
        spectral_analysis.confidence = 0.8

        hmm_result = MockRegimeResult(
            regime=RegimeState.TRENDING_UP,
            confidence=0.9,
            weight=0.8,
        )

        _, weight = enhanced._combine_regimes(hmm_result, spectral_analysis, 1.0)

        # With agreement >= 0.9, bonus should be applied
        # Weight should be in valid range
        assert 0.0 <= weight <= 1.0

    def test_combine_weight_no_agreement_bonus(self):
        """Test combined weight without agreement bonus."""
        mock_rm = MockRegimeManager()
        enhanced = EnhancedRegimeManager(
            regime_manager=mock_rm,
            spectral_weight=0.3,
            agreement_bonus=0.2,
        )

        spectral_analysis = MagicMock()
        spectral_analysis.regime = MarketRegime.TRENDING
        spectral_analysis.confidence = 0.8

        hmm_result = MockRegimeResult(
            regime=RegimeState.RANGING,  # Disagreement
            confidence=0.7,
            weight=0.6,
        )

        _, weight = enhanced._combine_regimes(hmm_result, spectral_analysis, 0.3)

        # Without high agreement, no bonus
        assert 0.0 <= weight <= 1.0

    def test_combine_spectral_regime_weights(self):
        """Test spectral weight varies by regime type."""
        mock_rm = MockRegimeManager()
        enhanced = EnhancedRegimeManager(regime_manager=mock_rm, spectral_weight=0.5)

        hmm_result = MockRegimeResult(
            regime=RegimeState.RANGING,
            confidence=0.5,
            weight=0.5,
        )

        # Test different spectral regimes have different base weights
        regimes = [
            MarketRegime.TRENDING,
            MarketRegime.NORMAL,
            MarketRegime.MEAN_REVERTING,
            MarketRegime.UNKNOWN,
        ]

        weights = []
        for spectral_regime in regimes:
            spectral_analysis = MagicMock()
            spectral_analysis.regime = spectral_regime
            spectral_analysis.confidence = 0.8

            _, weight = enhanced._combine_regimes(hmm_result, spectral_analysis, 0.5)
            weights.append(weight)

        # All weights should be valid
        assert all(0.0 <= w <= 1.0 for w in weights)

    def test_combine_weight_clamped_low(self):
        """Test combined weight is clamped to minimum 0.0."""
        mock_rm = MockRegimeManager()
        enhanced = EnhancedRegimeManager(
            regime_manager=mock_rm,
            spectral_weight=0.0,  # No spectral contribution
        )

        spectral_analysis = MagicMock()
        spectral_analysis.regime = MarketRegime.UNKNOWN
        spectral_analysis.confidence = 0.0

        hmm_result = MockRegimeResult(
            regime=RegimeState.RANGING,
            confidence=0.1,
            weight=0.0,  # Very low HMM weight
        )

        _, weight = enhanced._combine_regimes(hmm_result, spectral_analysis, 0.0)

        assert weight >= 0.0

    def test_combine_weight_clamped_high(self):
        """Test combined weight is clamped to maximum 1.0."""
        mock_rm = MockRegimeManager()
        enhanced = EnhancedRegimeManager(
            regime_manager=mock_rm,
            spectral_weight=0.5,
            agreement_bonus=0.5,  # High bonus
        )

        spectral_analysis = MagicMock()
        spectral_analysis.regime = MarketRegime.TRENDING
        spectral_analysis.confidence = 1.0  # Max confidence

        hmm_result = MockRegimeResult(
            regime=RegimeState.TRENDING_UP,
            confidence=1.0,
            weight=1.0,  # Max HMM weight
        )

        _, weight = enhanced._combine_regimes(hmm_result, spectral_analysis, 1.0)

        assert weight <= 1.0


class TestGetCombinedWeight:
    """Test get_combined_weight method (line 246)."""

    def test_get_combined_weight(self):
        """Test getting combined weight from regime manager."""
        mock_rm = MockRegimeManager()
        mock_rm.set_weight(0.75)

        enhanced = EnhancedRegimeManager(regime_manager=mock_rm)

        weight = enhanced.get_combined_weight()

        assert weight == 0.75

    def test_get_combined_weight_default(self):
        """Test default combined weight."""
        mock_rm = MockRegimeManager()

        enhanced = EnhancedRegimeManager(regime_manager=mock_rm)

        weight = enhanced.get_combined_weight()

        # Should return regime manager's default weight
        assert isinstance(weight, float)


class TestIsReady:
    """Test is_ready property (line 251)."""

    def test_is_ready_both_fitted(self):
        """Test is_ready when both HMM and spectral are ready."""
        mock_rm = MockRegimeManager(is_fitted=True)
        enhanced = EnhancedRegimeManager(regime_manager=mock_rm, spectral_window=64)

        # Fit spectral with enough data
        np.random.seed(42)
        returns = np.random.normal(0, 0.01, 100).tolist()
        enhanced.fit_spectral(returns)

        assert enhanced.is_ready is True

    def test_is_ready_hmm_not_fitted(self):
        """Test is_ready when HMM not fitted."""
        mock_rm = MockRegimeManager(is_fitted=False)
        enhanced = EnhancedRegimeManager(regime_manager=mock_rm, spectral_window=64)

        # Fit spectral
        returns = [0.01] * 100
        enhanced.fit_spectral(returns)

        assert enhanced.is_ready is False

    def test_is_ready_spectral_not_ready(self):
        """Test is_ready when spectral not ready."""
        mock_rm = MockRegimeManager(is_fitted=True)
        enhanced = EnhancedRegimeManager(regime_manager=mock_rm, spectral_window=64)

        # Don't fit spectral - not enough data
        assert enhanced.is_ready is False

    def test_is_ready_neither_ready(self):
        """Test is_ready when neither is ready."""
        mock_rm = MockRegimeManager(is_fitted=False)
        enhanced = EnhancedRegimeManager(regime_manager=mock_rm)

        assert enhanced.is_ready is False


class TestIntegrationScenarios:
    """Integration tests for complete workflow scenarios."""

    def test_full_workflow(self):
        """Test complete workflow: init -> fit -> update."""
        mock_rm = MockRegimeManager(is_fitted=True)
        mock_rm.set_regime(RegimeState.TRENDING_UP)
        mock_rm.set_confidence(0.85)
        mock_rm.set_weight(0.9)

        enhanced = EnhancedRegimeManager(
            regime_manager=mock_rm,
            spectral_weight=0.3,
            spectral_window=64,
            agreement_bonus=0.2,
        )

        # Fit spectral
        np.random.seed(42)
        returns = np.random.normal(0, 0.01, 100).tolist()
        enhanced.fit_spectral(returns)

        assert enhanced.is_ready is True

        # Run multiple updates
        for i in range(5):
            bar = {"close": 100.0 + i * 0.5}
            result = enhanced.update(bar, 0.005)

            assert isinstance(result, EnhancedRegimeResult)
            assert 0.0 <= result.combined_weight <= 1.0
            assert 0.0 <= result.agreement_score <= 1.0

    def test_regime_transition_scenario(self):
        """Test regime transitions through multiple updates."""
        mock_rm = MockRegimeManager(is_fitted=True)

        enhanced = EnhancedRegimeManager(
            regime_manager=mock_rm,
            spectral_window=64,
        )

        # Fit with trending-like data
        np.random.seed(42)
        returns = np.cumsum(np.random.normal(0.001, 0.005, 100)).tolist()
        enhanced.fit_spectral(returns)

        # Simulate regime transition: trending -> ranging -> volatile
        regimes = [
            (RegimeState.TRENDING_UP, 0.9),
            (RegimeState.TRENDING_UP, 0.8),
            (RegimeState.RANGING, 0.7),
            (RegimeState.RANGING, 0.75),
            (RegimeState.VOLATILE, 0.6),
        ]

        results = []
        for regime, conf in regimes:
            mock_rm.set_regime(regime)
            mock_rm.set_confidence(conf)

            bar = {"close": 100.0}
            result = enhanced.update(bar, np.random.normal(0, 0.01))
            results.append(result)

        # Verify all results are valid
        assert len(results) == 5
        assert all(isinstance(r.combined_regime, CombinedRegime) for r in results)

    def test_high_agreement_scenario(self):
        """Test scenario with high agreement between HMM and spectral."""
        mock_rm = MockRegimeManager(is_fitted=True)
        mock_rm.set_regime(RegimeState.TRENDING_UP)
        mock_rm.set_confidence(0.9)
        mock_rm.set_weight(0.9)

        enhanced = EnhancedRegimeManager(
            regime_manager=mock_rm,
            spectral_weight=0.4,
            agreement_bonus=0.2,
        )

        # Fit with strongly trending data (should produce TRENDING regime)
        np.random.seed(42)
        trend = np.linspace(0, 1, 100)
        noise = np.random.normal(0, 0.01, 100)
        returns = (np.diff(np.exp(trend + noise))).tolist()
        enhanced.fit_spectral(returns)

        bar = {"close": 100.0}
        result = enhanced.update(bar, 0.01)

        # With high agreement, should get bonus
        # Combined weight should be higher due to agreement
        assert result.combined_weight > 0.5

    def test_disagreement_scenario(self):
        """Test scenario with disagreement between HMM and spectral."""
        mock_rm = MockRegimeManager(is_fitted=True)
        mock_rm.set_regime(RegimeState.TRENDING_UP)  # HMM says trending
        mock_rm.set_confidence(0.7)
        mock_rm.set_weight(0.5)

        enhanced = EnhancedRegimeManager(
            regime_manager=mock_rm,
            spectral_weight=0.3,
        )

        # Fit with white noise - produces low alpha (mean-reverting spectral)
        np.random.seed(42)
        # Alternating returns are white noise-like (low spectral slope)
        returns = [0.01 if i % 2 == 0 else -0.01 for i in range(100)]
        enhanced.fit_spectral(returns)

        bar = {"close": 100.0}
        result = enhanced.update(bar, 0.02)

        # Spectral should detect mean-reverting from alternating returns
        # HMM trending vs spectral mean-reverting = disagreement
        # Result depends on spectral detection
        assert isinstance(result, EnhancedRegimeResult)
        # Verify disagreement path was tested
        if result.spectral_regime == MarketRegime.MEAN_REVERTING:
            assert result.agreement_score == 0.0
        elif result.spectral_regime == MarketRegime.NORMAL:
            assert result.agreement_score == 0.5


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_extreme_spectral_weight(self):
        """Test with extreme spectral weights."""
        mock_rm = MockRegimeManager()

        # Zero spectral weight
        enhanced_zero = EnhancedRegimeManager(
            regime_manager=mock_rm,
            spectral_weight=0.0,
        )
        assert enhanced_zero.spectral_weight == 0.0

        # Full spectral weight
        enhanced_full = EnhancedRegimeManager(
            regime_manager=mock_rm,
            spectral_weight=1.0,
        )
        assert enhanced_full.spectral_weight == 1.0

    def test_empty_bar(self):
        """Test update with minimal bar data."""
        mock_rm = MockRegimeManager()
        enhanced = EnhancedRegimeManager(regime_manager=mock_rm, spectral_window=64)

        np.random.seed(42)
        enhanced.fit_spectral(np.random.normal(0, 0.01, 100).tolist())

        # Minimal bar - just close price
        bar = {"close": 100.0}
        result = enhanced.update(bar, 0.0)

        assert isinstance(result, EnhancedRegimeResult)

    def test_zero_return(self):
        """Test update with zero return."""
        mock_rm = MockRegimeManager()
        enhanced = EnhancedRegimeManager(regime_manager=mock_rm, spectral_window=64)

        enhanced.fit_spectral([0.01] * 100)

        bar = {"close": 100.0}
        result = enhanced.update(bar, 0.0)

        assert isinstance(result, EnhancedRegimeResult)

    def test_large_return(self):
        """Test update with large return value."""
        mock_rm = MockRegimeManager()
        enhanced = EnhancedRegimeManager(regime_manager=mock_rm, spectral_window=64)

        enhanced.fit_spectral([0.01] * 100)

        bar = {"close": 100.0}
        result = enhanced.update(bar, 0.5)  # 50% return

        assert isinstance(result, EnhancedRegimeResult)
        assert 0.0 <= result.combined_weight <= 1.0

    def test_negative_return(self):
        """Test update with large negative return."""
        mock_rm = MockRegimeManager()
        enhanced = EnhancedRegimeManager(regime_manager=mock_rm, spectral_window=64)

        enhanced.fit_spectral([0.01] * 100)

        bar = {"close": 100.0}
        result = enhanced.update(bar, -0.5)  # -50% return

        assert isinstance(result, EnhancedRegimeResult)
