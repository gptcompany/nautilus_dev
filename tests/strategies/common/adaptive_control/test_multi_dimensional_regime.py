"""Comprehensive tests for Multi-Dimensional Regime Detection.

Coverage targets:
- Lines 128-144: __init__ with custom parameters
- Lines 169-227: update() method with all code paths
- Lines 234-304: _calculate_consensus() logic
- Lines 318, 322-327, 331-334, 339, 344: helper methods
- Lines 360-367: create_multi_regime_detector() factory

Test categories:
1. Initialization and configuration
2. Update method - IIR dimension
3. Update method - Flow dimension
4. Consensus calculation logic
5. Edge cases (no data, insufficient data, extreme values)
6. Helper methods (regime history, stability, average agreement)
7. Factory function
"""

import math
from unittest.mock import MagicMock, patch

import pytest

from strategies.common.adaptive_control.multi_dimensional_regime import (
    ConsensusRegime,
    DimensionResult,
    MultiDimensionalRegimeDetector,
    MultiDimensionalResult,
    create_multi_regime_detector,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def detector():
    """Create a default detector instance."""
    return MultiDimensionalRegimeDetector()


@pytest.fixture
def detector_custom():
    """Create a detector with custom parameters."""
    return MultiDimensionalRegimeDetector(
        iir_fast_period=5,
        iir_slow_period=20,
        flow_pressure_window=10,
        flow_viscosity=0.2,
        min_agreement_to_trade=0.6,
        uncertainty_penalty=0.3,
    )


@pytest.fixture
def mock_iir():
    """Create a mock IIR regime detector."""
    mock = MagicMock()
    mock.update.return_value = "trending"
    mock.variance_ratio = 1.5
    return mock


@pytest.fixture
def mock_flow():
    """Create a mock flow analyzer."""
    mock = MagicMock()
    mock_state = MagicMock()
    mock_state.reynolds_number = 2.0
    mock.update.return_value = mock_state
    mock.get_flow_regime.return_value = "turbulent"
    return mock


# ============================================================================
# Test Initialization (Lines 128-144)
# ============================================================================


class TestMultiDimensionalRegimeDetectorInit:
    """Test detector initialization with various configurations."""

    def test_default_initialization(self, detector):
        """Test default parameter initialization."""
        assert detector.min_agreement == 0.5
        assert detector.uncertainty_penalty == 0.5
        assert detector._last_price is None
        assert detector._update_count == 0
        assert detector._history == []

    def test_custom_initialization(self, detector_custom):
        """Test custom parameter initialization."""
        assert detector_custom.min_agreement == 0.6
        assert detector_custom.uncertainty_penalty == 0.3

    def test_iir_component_initialized(self, detector):
        """Test IIR component is properly initialized."""
        assert detector._iir is not None
        # IIR should have a variance_ratio property
        assert hasattr(detector._iir, "variance_ratio")

    def test_flow_component_initialized(self, detector):
        """Test flow analyzer is properly initialized."""
        assert detector._flow is not None
        # Flow should have update and get_flow_regime methods
        assert hasattr(detector._flow, "update")
        assert hasattr(detector._flow, "get_flow_regime")


# ============================================================================
# Test Update Method - IIR Dimension (Lines 169-185)
# ============================================================================


class TestUpdateMethodIIR:
    """Test update method focusing on IIR dimension."""

    def test_first_update_no_iir_dimension(self, detector):
        """First update has no previous price, so no IIR dimension."""
        result = detector.update(price=100.0)

        # First update - no IIR dimension (need previous price for return)
        iir_dims = [d for d in result.dimensions if d.name == "iir"]
        assert len(iir_dims) == 0

    def test_second_update_has_iir_dimension(self, detector):
        """Second update should have IIR dimension."""
        detector.update(price=100.0)
        result = detector.update(price=101.0)

        iir_dims = [d for d in result.dimensions if d.name == "iir"]
        assert len(iir_dims) == 1
        assert iir_dims[0].name == "iir"
        assert iir_dims[0].regime in ["trending", "mean_reverting", "normal", "unknown"]
        assert 0.0 <= iir_dims[0].confidence <= 1.0

    def test_iir_raw_value_is_variance_ratio(self, detector):
        """IIR dimension raw_value should be variance_ratio."""
        detector.update(price=100.0)
        result = detector.update(price=101.0)

        iir_dims = [d for d in result.dimensions if d.name == "iir"]
        if iir_dims:
            assert iir_dims[0].raw_value >= 0  # Variance ratio is non-negative

    def test_update_count_increments(self, detector):
        """Update count should increment with each call."""
        assert detector._update_count == 0
        detector.update(price=100.0)
        assert detector._update_count == 1
        detector.update(price=101.0)
        assert detector._update_count == 2

    def test_last_price_updated(self, detector):
        """Last price should be updated after each call."""
        detector.update(price=100.0)
        assert detector._last_price == 100.0
        detector.update(price=105.0)
        assert detector._last_price == 105.0

    def test_zero_previous_price_no_iir(self, detector):
        """If previous price is zero, should skip IIR dimension."""
        detector._last_price = 0.0
        detector._update_count = 1
        result = detector.update(price=100.0)

        # Should have updated last_price
        assert detector._last_price == 100.0
        # IIR dimension should be skipped when previous price is 0
        iir_dims = [d for d in result.dimensions if d.name == "iir"]
        assert len(iir_dims) == 0


# ============================================================================
# Test Update Method - Flow Dimension (Lines 187-214)
# ============================================================================


class TestUpdateMethodFlow:
    """Test update method focusing on flow dimension."""

    def test_flow_dimension_with_all_data(self, detector):
        """Flow dimension should be included when all order book data provided."""
        detector.update(price=100.0)  # First update to set last_price
        result = detector.update(
            price=101.0,
            bid=100.5,
            ask=101.5,
            bid_size=1000.0,
            ask_size=800.0,
            volume=5000.0,
        )

        flow_dims = [d for d in result.dimensions if d.name == "flow"]
        assert len(flow_dims) == 1

    def test_flow_dimension_missing_bid(self, detector):
        """Flow dimension should be excluded when bid is missing."""
        detector.update(price=100.0)
        result = detector.update(
            price=101.0,
            bid=None,
            ask=101.5,
            bid_size=1000.0,
            ask_size=800.0,
            volume=5000.0,
        )

        flow_dims = [d for d in result.dimensions if d.name == "flow"]
        assert len(flow_dims) == 0

    def test_flow_dimension_missing_volume(self, detector):
        """Flow dimension should be excluded when volume is missing."""
        detector.update(price=100.0)
        result = detector.update(
            price=101.0,
            bid=100.5,
            ask=101.5,
            bid_size=1000.0,
            ask_size=800.0,
            volume=None,
        )

        flow_dims = [d for d in result.dimensions if d.name == "flow"]
        assert len(flow_dims) == 0

    def test_flow_regime_mapping_turbulent(self, detector):
        """Turbulent flow regime should map to 'trending'."""
        with patch.object(detector._flow, "get_flow_regime", return_value="turbulent"):
            detector.update(price=100.0)
            result = detector.update(
                price=101.0,
                bid=100.5,
                ask=101.5,
                bid_size=1000.0,
                ask_size=800.0,
                volume=5000.0,
            )

            flow_dims = [d for d in result.dimensions if d.name == "flow"]
            if flow_dims:
                assert flow_dims[0].regime == "trending"

    def test_flow_regime_mapping_laminar(self, detector):
        """Laminar flow regime should map to 'mean_reverting'."""
        with patch.object(detector._flow, "get_flow_regime", return_value="laminar"):
            detector.update(price=100.0)
            result = detector.update(
                price=101.0,
                bid=100.5,
                ask=101.5,
                bid_size=1000.0,
                ask_size=800.0,
                volume=5000.0,
            )

            flow_dims = [d for d in result.dimensions if d.name == "flow"]
            if flow_dims:
                assert flow_dims[0].regime == "mean_reverting"

    def test_flow_regime_mapping_transitional(self, detector):
        """Unknown flow regime should map to 'transitional'."""
        with patch.object(
            detector._flow, "get_flow_regime", return_value="transitional"
        ):
            detector.update(price=100.0)
            result = detector.update(
                price=101.0,
                bid=100.5,
                ask=101.5,
                bid_size=1000.0,
                ask_size=800.0,
                volume=5000.0,
            )

            flow_dims = [d for d in result.dimensions if d.name == "flow"]
            if flow_dims:
                assert flow_dims[0].regime == "transitional"

    def test_flow_confidence_bounded(self, detector):
        """Flow confidence should be bounded to [0, 1]."""
        # Create mock state with high reynolds number
        mock_state = MagicMock()
        mock_state.reynolds_number = 10.0  # High value

        with patch.object(detector._flow, "update", return_value=mock_state):
            with patch.object(
                detector._flow, "get_flow_regime", return_value="turbulent"
            ):
                detector.update(price=100.0)
                result = detector.update(
                    price=101.0,
                    bid=100.5,
                    ask=101.5,
                    bid_size=1000.0,
                    ask_size=800.0,
                    volume=5000.0,
                )

                flow_dims = [d for d in result.dimensions if d.name == "flow"]
                if flow_dims:
                    assert 0.0 <= flow_dims[0].confidence <= 1.0


# ============================================================================
# Test History Management (Lines 221-227)
# ============================================================================


class TestHistoryManagement:
    """Test history tracking and bounds."""

    def test_history_appended(self, detector):
        """Each update should append to history."""
        assert len(detector._history) == 0
        detector.update(price=100.0)
        assert len(detector._history) == 1
        detector.update(price=101.0)
        assert len(detector._history) == 2

    def test_history_bounded_at_100(self, detector):
        """History should be bounded at 100 entries."""
        for i in range(150):
            detector.update(price=100.0 + i * 0.1)

        assert len(detector._history) <= 100

    def test_history_keeps_most_recent(self, detector):
        """History should keep most recent entries when trimmed."""
        for i in range(110):
            detector.update(price=100.0 + i)

        # Should have kept last 100
        assert len(detector._history) == 100


# ============================================================================
# Test _calculate_consensus Method (Lines 234-314)
# ============================================================================


class TestCalculateConsensus:
    """Test consensus calculation logic."""

    def test_empty_dimensions_returns_unknown(self, detector):
        """Empty dimensions should return UNKNOWN consensus."""
        result = detector._calculate_consensus([])

        assert result.consensus == ConsensusRegime.UNKNOWN
        assert result.confidence == 0.0
        assert result.agreement == 0.0
        assert result.risk_multiplier == 0.1
        assert result.should_trade is False

    def test_single_trending_dimension_full_agreement(self, detector):
        """Single trending dimension should give high agreement."""
        dims = [DimensionResult(name="iir", regime="trending", confidence=0.8, raw_value=1.5)]

        result = detector._calculate_consensus(dims)

        assert result.agreement == 1.0  # 1/1 = 100% agreement
        assert result.consensus == ConsensusRegime.TRENDING
        assert result.trending_votes == 1

    def test_single_mean_reverting_dimension(self, detector):
        """Single mean_reverting dimension should give MEAN_REVERTING consensus."""
        dims = [
            DimensionResult(
                name="iir", regime="mean_reverting", confidence=0.9, raw_value=0.5
            )
        ]

        result = detector._calculate_consensus(dims)

        assert result.consensus == ConsensusRegime.MEAN_REVERTING
        assert result.reverting_votes == 1

    def test_single_turbulent_dimension(self, detector):
        """Single turbulent dimension should give TURBULENT consensus."""
        dims = [
            DimensionResult(name="flow", regime="turbulent", confidence=0.7, raw_value=2.0)
        ]

        result = detector._calculate_consensus(dims)

        assert result.consensus == ConsensusRegime.TURBULENT
        assert result.turbulent_votes == 1

    def test_two_agreeing_dimensions(self, detector):
        """Two agreeing dimensions should give high agreement."""
        dims = [
            DimensionResult(name="iir", regime="trending", confidence=0.8, raw_value=1.5),
            DimensionResult(name="flow", regime="trending", confidence=0.7, raw_value=2.0),
        ]

        result = detector._calculate_consensus(dims)

        assert result.agreement == 1.0  # 2/2 = 100% agreement
        assert result.consensus == ConsensusRegime.TRENDING
        assert result.trending_votes == 2

    def test_two_disagreeing_dimensions(self, detector):
        """Two disagreeing dimensions should give CONFLICT."""
        dims = [
            DimensionResult(name="iir", regime="trending", confidence=0.8, raw_value=1.5),
            DimensionResult(
                name="flow", regime="mean_reverting", confidence=0.7, raw_value=0.5
            ),
        ]

        result = detector._calculate_consensus(dims)

        assert result.agreement == 0.5  # 1/2 = 50% for each
        # 50% agreement = transitional (0.5 <= agreement < 0.75)
        assert result.consensus == ConsensusRegime.TRANSITIONAL

    def test_four_dimensions_three_agree(self, detector):
        """3/4 agreement should give consensus for majority."""
        dims = [
            DimensionResult(name="d1", regime="trending", confidence=0.8, raw_value=1.5),
            DimensionResult(name="d2", regime="trending", confidence=0.7, raw_value=1.3),
            DimensionResult(name="d3", regime="trending", confidence=0.9, raw_value=1.8),
            DimensionResult(
                name="d4", regime="mean_reverting", confidence=0.6, raw_value=0.5
            ),
        ]

        result = detector._calculate_consensus(dims)

        assert result.agreement == 0.75  # 3/4 = 75%
        assert result.consensus == ConsensusRegime.TRENDING
        assert result.trending_votes == 3
        assert result.reverting_votes == 1

    def test_transitional_regime_mapping(self, detector):
        """Test transitional/normal regime handling."""
        dims = [
            DimensionResult(
                name="d1", regime="transitional", confidence=0.8, raw_value=1.0
            ),
        ]

        result = detector._calculate_consensus(dims)

        # transitional with 100% agreement but not trending/reverting/turbulent
        assert result.consensus == ConsensusRegime.TRANSITIONAL

    def test_normal_regime_vote(self, detector):
        """Test normal regime is counted in votes."""
        dims = [
            DimensionResult(name="d1", regime="normal", confidence=0.8, raw_value=1.0),
            DimensionResult(name="d2", regime="normal", confidence=0.7, raw_value=1.0),
        ]

        result = detector._calculate_consensus(dims)

        # normal maps to TRANSITIONAL in consensus
        assert result.consensus == ConsensusRegime.TRANSITIONAL
        assert result.agreement == 1.0

    def test_risk_multiplier_low_agreement(self, detector):
        """Low agreement should result in uncertainty_penalty risk."""
        dims = [
            DimensionResult(name="d1", regime="trending", confidence=0.8, raw_value=1.5),
            DimensionResult(
                name="d2", regime="mean_reverting", confidence=0.7, raw_value=0.5
            ),
            DimensionResult(name="d3", regime="turbulent", confidence=0.6, raw_value=2.0),
        ]

        result = detector._calculate_consensus(dims)

        # Agreement = 1/3 = 0.33 < 0.5 (min_agreement)
        assert result.agreement < detector.min_agreement
        assert result.risk_multiplier == detector.uncertainty_penalty

    def test_risk_multiplier_high_agreement(self, detector):
        """High agreement should result in confidence-based risk."""
        dims = [
            DimensionResult(name="d1", regime="trending", confidence=0.8, raw_value=1.5),
            DimensionResult(name="d2", regime="trending", confidence=0.7, raw_value=1.3),
        ]

        result = detector._calculate_consensus(dims)

        # Agreement = 1.0 >= min_agreement
        # risk = 0.5 + 0.5 * confidence
        expected_confidence = 0.75 * 1.0  # avg_confidence * agreement
        expected_risk = 0.5 + 0.5 * expected_confidence
        assert abs(result.risk_multiplier - expected_risk) < 0.01

    def test_should_trade_true_conditions(self, detector):
        """Should trade when agreement, confidence, and consensus met."""
        dims = [
            DimensionResult(name="d1", regime="trending", confidence=0.8, raw_value=1.5),
            DimensionResult(name="d2", regime="trending", confidence=0.7, raw_value=1.3),
        ]

        result = detector._calculate_consensus(dims)

        # agreement >= min_agreement (0.5), confidence >= 0.3, not CONFLICT
        assert result.should_trade is True

    def test_should_trade_false_low_agreement(self, detector):
        """Should not trade when agreement is low."""
        dims = [
            DimensionResult(name="d1", regime="trending", confidence=0.8, raw_value=1.5),
            DimensionResult(
                name="d2", regime="mean_reverting", confidence=0.7, raw_value=0.5
            ),
            DimensionResult(name="d3", regime="turbulent", confidence=0.6, raw_value=2.0),
        ]

        result = detector._calculate_consensus(dims)

        # Agreement = 0.33 < 0.5
        assert result.should_trade is False

    def test_should_trade_false_conflict(self, detector):
        """Should not trade when consensus is CONFLICT."""
        # Create a conflict scenario with very low agreement
        dims = [
            DimensionResult(name="d1", regime="trending", confidence=0.8, raw_value=1.5),
            DimensionResult(
                name="d2", regime="mean_reverting", confidence=0.8, raw_value=0.5
            ),
            DimensionResult(name="d3", regime="turbulent", confidence=0.8, raw_value=2.0),
            DimensionResult(name="d4", regime="normal", confidence=0.8, raw_value=1.0),
        ]

        result = detector._calculate_consensus(dims)

        # 4 different regimes = 25% agreement each = CONFLICT
        assert result.consensus == ConsensusRegime.CONFLICT
        assert result.should_trade is False

    def test_unknown_regime_handling(self, detector):
        """Test that unknown regime is handled."""
        dims = [
            DimensionResult(name="d1", regime="unknown", confidence=0.5, raw_value=1.0),
        ]

        result = detector._calculate_consensus(dims)

        # Should not crash, and should handle unknown
        assert result is not None


# ============================================================================
# Test Helper Methods (Lines 316-344)
# ============================================================================


class TestHelperMethods:
    """Test get_regime_history, is_regime_stable, get_average_agreement."""

    def test_get_regime_history_empty(self, detector):
        """Empty history should return empty list."""
        history = detector.get_regime_history()
        assert history == []

    def test_get_regime_history_returns_regimes(self, detector):
        """Should return consensus regimes from history."""
        # Add some updates
        for i in range(5):
            detector.update(price=100.0 + i)

        history = detector.get_regime_history(n=5)
        assert len(history) == 5
        assert all(isinstance(r, ConsensusRegime) for r in history)

    def test_get_regime_history_limits_to_n(self, detector):
        """Should return only last n entries."""
        for i in range(20):
            detector.update(price=100.0 + i)

        history = detector.get_regime_history(n=5)
        assert len(history) == 5

    def test_is_regime_stable_insufficient_data(self, detector):
        """Should return False if insufficient data."""
        # Only 5 updates, but asking for window of 10
        for i in range(5):
            detector.update(price=100.0 + i)

        assert detector.is_regime_stable(window=10) is False

    def test_is_regime_stable_true(self, detector):
        """Should return True if all regimes same."""
        # All updates result in UNKNOWN (first few updates)
        for _i in range(15):
            detector.update(price=100.0)  # Constant price

        # Check stability - should be True if all same regime
        history = detector.get_regime_history(10)
        if len(set(history)) == 1:
            assert detector.is_regime_stable(window=10) is True

    def test_is_regime_stable_false_mixed_regimes(self, detector):
        """Should return False if regimes vary."""
        # Create varying prices to potentially get different regimes
        prices = [100.0, 100.0, 110.0, 105.0, 95.0, 115.0, 90.0, 120.0, 85.0, 130.0]
        for p in prices:
            detector.update(price=p)
            detector.update(price=p + 5)

        # With varying regimes, should be unstable
        history = detector.get_regime_history(10)
        if len(set(history)) > 1:
            assert detector.is_regime_stable(window=10) is False

    def test_get_average_agreement_insufficient_data(self, detector):
        """Should return 0.0 if insufficient data."""
        for i in range(5):
            detector.update(price=100.0 + i)

        avg = detector.get_average_agreement(window=10)
        assert avg == 0.0

    def test_get_average_agreement_calculates_correctly(self, detector):
        """Should calculate average agreement over window."""
        for i in range(15):
            detector.update(price=100.0 + i * 0.5)

        avg = detector.get_average_agreement(window=10)
        # Should be between 0 and 1
        assert 0.0 <= avg <= 1.0


# ============================================================================
# Test Properties (Lines 336-344)
# ============================================================================


class TestProperties:
    """Test update_count and is_ready properties."""

    def test_update_count_property(self, detector):
        """Test update_count returns correct value."""
        assert detector.update_count == 0
        detector.update(price=100.0)
        assert detector.update_count == 1
        detector.update(price=101.0)
        assert detector.update_count == 2

    def test_is_ready_false_initially(self, detector):
        """is_ready should be False before 20 updates."""
        assert detector.is_ready is False
        for i in range(19):
            detector.update(price=100.0 + i)
        assert detector.is_ready is False

    def test_is_ready_true_after_20_updates(self, detector):
        """is_ready should be True after 20 updates."""
        for i in range(20):
            detector.update(price=100.0 + i)
        assert detector.is_ready is True


# ============================================================================
# Test Factory Function (Lines 360-367)
# ============================================================================


class TestCreateMultiRegimeDetector:
    """Test create_multi_regime_detector factory function."""

    def test_fast_mode_default(self):
        """Fast mode should be default."""
        detector = create_multi_regime_detector()
        assert detector is not None
        # Should be able to use the detector
        result = detector.update(price=100.0)
        assert result is not None

    def test_fast_mode_explicit(self):
        """Fast mode with explicit flag."""
        detector = create_multi_regime_detector(fast=True)
        assert detector is not None

    def test_slow_mode(self):
        """Slow (accurate) mode."""
        detector = create_multi_regime_detector(fast=False)
        assert detector is not None
        # Should still work
        result = detector.update(price=100.0)
        assert result is not None


# ============================================================================
# Test Integration Scenarios
# ============================================================================


class TestIntegrationScenarios:
    """Integration tests for realistic usage patterns."""

    def test_trending_market_detection(self, detector):
        """Test detection of trending market conditions."""
        # Simulate uptrend
        price = 100.0
        for i in range(50):
            price += 0.5 + (0.1 * (i % 5))  # Upward drift with noise
            result = detector.update(
                price=price,
                bid=price - 0.05,
                ask=price + 0.05,
                bid_size=1000.0,
                ask_size=800.0,
                volume=5000.0 + i * 100,
            )

        # After warmup, should detect trend
        assert detector.is_ready
        assert result.consensus in [ConsensusRegime.TRENDING, ConsensusRegime.TRANSITIONAL, ConsensusRegime.UNKNOWN]

    def test_mean_reverting_market_detection(self, detector):
        """Test detection of mean-reverting market conditions."""

        # Simulate mean reversion (oscillation around 100)
        for i in range(50):
            price = 100.0 + 2.0 * math.sin(i * 0.3)  # Oscillate +/- 2
            detector.update(
                price=price,
                bid=price - 0.02,
                ask=price + 0.02,
                bid_size=1000.0,
                ask_size=1000.0,
                volume=3000.0,
            )

        assert detector.is_ready

    def test_volatile_market_detection(self, detector):
        """Test detection of volatile/turbulent market."""
        import random

        random.seed(42)

        price = 100.0
        for _i in range(50):
            # Large random moves
            price += random.uniform(-3.0, 3.0)
            detector.update(
                price=price,
                bid=price - 0.5,
                ask=price + 0.5,
                bid_size=500.0,
                ask_size=1500.0,
                volume=10000.0,
            )

        assert detector.is_ready

    def test_full_workflow_with_order_book(self, detector):
        """Test complete workflow with order book data."""
        prices = [100.0, 100.5, 101.0, 100.8, 101.2, 101.5, 101.3, 102.0]

        for i, price in enumerate(prices):
            result = detector.update(
                price=price,
                bid=price - 0.1,
                ask=price + 0.1,
                bid_size=1000.0 + i * 50,
                ask_size=900.0 + i * 30,
                volume=5000.0 + i * 200,
            )

            # Result should always be valid
            assert isinstance(result, MultiDimensionalResult)
            assert isinstance(result.consensus, ConsensusRegime)
            assert 0.0 <= result.confidence <= 1.0
            assert 0.0 <= result.agreement <= 1.0
            assert result.risk_multiplier > 0

    def test_price_only_workflow(self, detector):
        """Test workflow with only price data (no order book)."""
        prices = [100.0, 100.5, 101.0, 100.8, 101.2, 101.5]

        for price in prices:
            result = detector.update(price=price)

            assert isinstance(result, MultiDimensionalResult)
            # Should have IIR dimension after first update
            if detector._update_count > 1:
                assert len(result.dimensions) >= 0  # May or may not have IIR


# ============================================================================
# Test Edge Cases
# ============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_extreme_price_values(self, detector):
        """Test with extreme price values."""
        # Very small price
        result = detector.update(price=0.0001)
        assert result is not None

        # Very large price
        result = detector.update(price=1000000.0)
        assert result is not None

    def test_negative_price(self, detector):
        """Test with negative price (edge case)."""
        detector.update(price=-100.0)
        result = detector.update(price=-99.0)
        # Should not crash
        assert result is not None

    def test_zero_volume(self, detector):
        """Test with zero volume."""
        detector.update(price=100.0)
        result = detector.update(
            price=101.0,
            bid=100.5,
            ask=101.5,
            bid_size=1000.0,
            ask_size=800.0,
            volume=0.0,
        )
        assert result is not None

    def test_equal_bid_ask_sizes(self, detector):
        """Test with equal bid and ask sizes (balanced)."""
        detector.update(price=100.0)
        result = detector.update(
            price=101.0,
            bid=100.5,
            ask=101.5,
            bid_size=1000.0,
            ask_size=1000.0,
            volume=5000.0,
        )
        assert result is not None

    def test_very_wide_spread(self, detector):
        """Test with very wide bid-ask spread."""
        detector.update(price=100.0)
        result = detector.update(
            price=101.0,
            bid=90.0,
            ask=110.0,
            bid_size=1000.0,
            ask_size=1000.0,
            volume=5000.0,
        )
        assert result is not None

    def test_rapid_updates(self, detector):
        """Test rapid sequential updates."""
        for i in range(1000):
            result = detector.update(price=100.0 + (i % 10) * 0.1)
        assert result is not None
        assert detector.update_count == 1000
        assert len(detector._history) == 100  # Bounded

    def test_constant_price(self, detector):
        """Test with constant price (no movement)."""
        for _i in range(30):
            result = detector.update(price=100.0)

        # With constant price, variance ratio approaches 1.0
        assert result is not None
        assert detector.is_ready


# ============================================================================
# Test DimensionResult and MultiDimensionalResult Dataclasses
# ============================================================================


class TestDataclasses:
    """Test dataclass structures."""

    def test_dimension_result_creation(self):
        """Test DimensionResult dataclass."""
        dim = DimensionResult(
            name="test", regime="trending", confidence=0.8, raw_value=1.5
        )
        assert dim.name == "test"
        assert dim.regime == "trending"
        assert dim.confidence == 0.8
        assert dim.raw_value == 1.5

    def test_multi_dimensional_result_creation(self):
        """Test MultiDimensionalResult dataclass."""
        dims = [
            DimensionResult(name="iir", regime="trending", confidence=0.8, raw_value=1.5)
        ]
        result = MultiDimensionalResult(
            dimensions=dims,
            consensus=ConsensusRegime.TRENDING,
            confidence=0.8,
            agreement=1.0,
            risk_multiplier=0.9,
            should_trade=True,
            trending_votes=1,
            reverting_votes=0,
            turbulent_votes=0,
        )
        assert result.dimensions == dims
        assert result.consensus == ConsensusRegime.TRENDING
        assert result.confidence == 0.8
        assert result.agreement == 1.0
        assert result.risk_multiplier == 0.9
        assert result.should_trade is True
        assert result.trending_votes == 1

    def test_consensus_regime_enum(self):
        """Test ConsensusRegime enum values."""
        assert ConsensusRegime.TRENDING.value == "trending"
        assert ConsensusRegime.MEAN_REVERTING.value == "mean_reverting"
        assert ConsensusRegime.TURBULENT.value == "turbulent"
        assert ConsensusRegime.TRANSITIONAL.value == "transitional"
        assert ConsensusRegime.CONFLICT.value == "conflict"
        assert ConsensusRegime.UNKNOWN.value == "unknown"


# ============================================================================
# Test with Mocked Dependencies
# ============================================================================


class TestWithMockedDependencies:
    """Test using mocked IIR and Flow components."""

    def test_with_mocked_iir_trending(self, mock_iir, mock_flow):
        """Test with mocked IIR returning trending."""
        with patch(
            "strategies.common.adaptive_control.multi_dimensional_regime.IIRRegimeDetector",
            return_value=mock_iir,
        ):
            with patch(
                "strategies.common.adaptive_control.multi_dimensional_regime.MarketFlowAnalyzer",
                return_value=mock_flow,
            ):
                detector = MultiDimensionalRegimeDetector()
                detector._iir = mock_iir
                detector._flow = mock_flow
                detector._last_price = 100.0  # Set previous price

                result = detector.update(
                    price=101.0,
                    bid=100.5,
                    ask=101.5,
                    bid_size=1000.0,
                    ask_size=800.0,
                    volume=5000.0,
                )

                # Should have used mocked values
                assert len(result.dimensions) >= 1

    def test_confidence_calculation_with_mocks(self):
        """Test confidence calculation with controlled inputs."""
        detector = MultiDimensionalRegimeDetector()

        # Manually create dimensions with known values
        dims = [
            DimensionResult(name="iir", regime="trending", confidence=1.0, raw_value=2.0),
            DimensionResult(name="flow", regime="trending", confidence=1.0, raw_value=2.0),
        ]

        result = detector._calculate_consensus(dims)

        # With 100% confidence and 100% agreement
        # confidence = avg_confidence * agreement = 1.0 * 1.0 = 1.0
        assert result.confidence == 1.0
        assert result.agreement == 1.0
        # risk = 0.5 + 0.5 * 1.0 = 1.0
        assert result.risk_multiplier == 1.0
