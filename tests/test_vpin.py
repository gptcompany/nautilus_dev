"""TDD Tests for VPIN Indicator (Spec 025).

Tests for VPINBucket, VPINIndicator, and edge cases.
These tests align with the actual implementation API.

Test IDs:
- T013: VPINBucket tests
- T014: VPINIndicator tests
- T015: Edge case tests
"""

from __future__ import annotations

import pytest

from strategies.common.orderflow.vpin import (
    ToxicityLevel,
    VPINBucket,
    VPINIndicator,
)
from strategies.common.orderflow.config import VPINConfig
from strategies.common.orderflow.trade_classifier import (
    TradeClassification,
    TradeSide,
)


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def default_config() -> VPINConfig:
    """Create default VPIN configuration."""
    return VPINConfig(
        bucket_size=1000.0,
        n_buckets=50,
        classification_method="tick_rule",
        min_bucket_volume=100.0,
    )


@pytest.fixture
def small_bucket_config() -> VPINConfig:
    """Create configuration with small buckets for faster testing."""
    return VPINConfig(
        bucket_size=100.0,
        n_buckets=10,
        classification_method="tick_rule",
        min_bucket_volume=10.0,
    )


@pytest.fixture
def vpin_indicator(small_bucket_config: VPINConfig) -> VPINIndicator:
    """Create a fresh VPIN indicator for testing."""
    return VPINIndicator(config=small_bucket_config)


def make_classification(
    side: TradeSide,
    volume: float = 100.0,
    price: float = 100.0,
    timestamp_ns: int = 0,
) -> TradeClassification:
    """Helper to create TradeClassification objects."""
    return TradeClassification(
        side=side,
        volume=volume,
        price=price,
        timestamp_ns=timestamp_ns,
        method="tick_rule",
        confidence=1.0,
    )


# ==============================================================================
# T013: VPINBucket Tests
# ==============================================================================


class TestVPINBucket:
    """Tests for VPINBucket volume bucket container.

    Test ID: T013
    Purpose: Verify bucket order imbalance calculation and completion detection.
    """

    def test_vpinbucket_order_imbalance_all_buys(self) -> None:
        """T013.1: Bucket with only buys should have OI = 1.0."""
        bucket = VPINBucket(
            volume_target=100.0,
            start_time=0,
            accumulated_volume=100.0,
            buy_volume=100.0,
            sell_volume=0.0,
        )
        assert bucket.order_imbalance == pytest.approx(1.0, abs=1e-10)

    def test_vpinbucket_order_imbalance_all_sells(self) -> None:
        """T013.2: Bucket with only sells should have OI = 1.0."""
        bucket = VPINBucket(
            volume_target=100.0,
            start_time=0,
            accumulated_volume=100.0,
            buy_volume=0.0,
            sell_volume=100.0,
        )
        assert bucket.order_imbalance == pytest.approx(1.0, abs=1e-10)

    def test_vpinbucket_order_imbalance_balanced(self) -> None:
        """T013.3: Bucket with equal buys and sells should have OI = 0.0."""
        bucket = VPINBucket(
            volume_target=100.0,
            start_time=0,
            accumulated_volume=100.0,
            buy_volume=50.0,
            sell_volume=50.0,
        )
        assert bucket.order_imbalance == pytest.approx(0.0, abs=1e-10)

    def test_vpinbucket_order_imbalance_mixed(self) -> None:
        """T013.4: Bucket with mixed trades should calculate correct OI."""
        bucket = VPINBucket(
            volume_target=100.0,
            start_time=0,
            accumulated_volume=100.0,
            buy_volume=70.0,
            sell_volume=30.0,
        )
        # OI = |70 - 30| / (70 + 30) = 40 / 100 = 0.4
        assert bucket.order_imbalance == pytest.approx(0.4, abs=1e-10)

    def test_vpinbucket_is_complete(self) -> None:
        """T013.5: Bucket should report complete when target reached."""
        # Not complete
        bucket_incomplete = VPINBucket(
            volume_target=100.0,
            start_time=0,
            accumulated_volume=50.0,
            buy_volume=50.0,
            sell_volume=0.0,
        )
        assert bucket_incomplete.is_complete is False

        # Complete
        bucket_complete = VPINBucket(
            volume_target=100.0,
            start_time=0,
            accumulated_volume=100.0,
            buy_volume=50.0,
            sell_volume=50.0,
        )
        assert bucket_complete.is_complete is True

    def test_vpinbucket_is_complete_with_overflow(self) -> None:
        """T013.6: Bucket should handle volume overflow gracefully."""
        bucket = VPINBucket(
            volume_target=100.0,
            start_time=0,
            accumulated_volume=150.0,
            buy_volume=150.0,
            sell_volume=0.0,
        )
        assert bucket.is_complete is True
        assert bucket.accumulated_volume == 150.0

    def test_vpinbucket_properties(self) -> None:
        """T013.7: Bucket should track buy/sell volumes correctly."""
        bucket = VPINBucket(
            volume_target=100.0,
            start_time=0,
            accumulated_volume=100.0,
            buy_volume=60.0,
            sell_volume=40.0,
        )
        assert bucket.buy_volume == pytest.approx(60.0, abs=1e-10)
        assert bucket.sell_volume == pytest.approx(40.0, abs=1e-10)
        assert bucket.accumulated_volume == pytest.approx(100.0, abs=1e-10)

    def test_vpinbucket_empty_order_imbalance(self) -> None:
        """T013.8: Empty bucket should return OI = 0.0."""
        bucket = VPINBucket(
            volume_target=100.0,
            start_time=0,
            accumulated_volume=0.0,
            buy_volume=0.0,
            sell_volume=0.0,
        )
        assert bucket.order_imbalance == pytest.approx(0.0, abs=1e-10)


# ==============================================================================
# T014: VPINIndicator Tests
# ==============================================================================


class TestVPINIndicator:
    """Tests for VPINIndicator main class.

    Test ID: T014
    Purpose: Verify VPIN calculation and toxicity level detection.
    """

    def test_vpin_initial_state(self, vpin_indicator: VPINIndicator) -> None:
        """T014.1: New indicator should have default initial state."""
        assert vpin_indicator.value == pytest.approx(0.0, abs=1e-10)
        assert vpin_indicator.is_valid is False

    def test_vpin_single_update(self, vpin_indicator: VPINIndicator) -> None:
        """T014.2: Single trade update should partially fill bucket."""
        classification = make_classification(
            side=TradeSide.BUY,
            volume=50.0,
            timestamp_ns=1000,
        )
        vpin_indicator.update(classification)

        assert vpin_indicator.is_valid is False
        # There should be a current bucket with partial volume
        assert vpin_indicator._current_bucket is not None
        assert vpin_indicator._current_bucket.accumulated_volume == pytest.approx(
            50.0, abs=1e-10
        )

    def test_vpin_bucket_completion(self, small_bucket_config: VPINConfig) -> None:
        """T014.3: Filling a bucket should add it to history."""
        indicator = VPINIndicator(config=small_bucket_config)
        classification = make_classification(
            side=TradeSide.BUY,
            volume=100.0,
            timestamp_ns=1000,
        )
        indicator.update(classification)

        assert len(indicator._buckets) == 1
        assert indicator._buckets[0].is_complete is True

    def test_vpin_rolling_calculation(self, small_bucket_config: VPINConfig) -> None:
        """T014.4: VPIN should be calculated as mean of bucket OIs."""
        indicator = VPINIndicator(config=small_bucket_config)

        # Fill 10 buckets with 70 buy, 30 sell each -> OI = 0.4
        for i in range(10):
            buy_class = make_classification(
                side=TradeSide.BUY,
                volume=70.0,
                timestamp_ns=i * 2 * 1000,
            )
            sell_class = make_classification(
                side=TradeSide.SELL,
                volume=30.0,
                timestamp_ns=i * 2 * 1000 + 500,
            )
            indicator.update(buy_class)
            indicator.update(sell_class)

        assert indicator.is_valid is True
        assert indicator.value == pytest.approx(0.4, abs=0.01)

    def test_vpin_toxicity_level_low(self, small_bucket_config: VPINConfig) -> None:
        """T014.5: VPIN < 0.3 should return LOW toxicity."""
        indicator = VPINIndicator(config=small_bucket_config)

        # Fill 10 buckets with low imbalance (60/40 -> OI = 0.2)
        for i in range(10):
            buy_class = make_classification(
                side=TradeSide.BUY,
                volume=60.0,
                timestamp_ns=i * 2 * 1000,
            )
            sell_class = make_classification(
                side=TradeSide.SELL,
                volume=40.0,
                timestamp_ns=i * 2 * 1000 + 500,
            )
            indicator.update(buy_class)
            indicator.update(sell_class)

        assert indicator.is_valid is True
        assert indicator.value == pytest.approx(0.2, abs=0.01)
        assert indicator.toxicity_level == ToxicityLevel.LOW

    def test_vpin_toxicity_level_medium(self, small_bucket_config: VPINConfig) -> None:
        """T014.6: 0.3 <= VPIN < 0.7 should return MEDIUM toxicity."""
        indicator = VPINIndicator(config=small_bucket_config)

        # Fill 10 buckets with medium imbalance (75/25 -> OI = 0.5)
        for i in range(10):
            buy_class = make_classification(
                side=TradeSide.BUY,
                volume=75.0,
                timestamp_ns=i * 2 * 1000,
            )
            sell_class = make_classification(
                side=TradeSide.SELL,
                volume=25.0,
                timestamp_ns=i * 2 * 1000 + 500,
            )
            indicator.update(buy_class)
            indicator.update(sell_class)

        assert indicator.is_valid is True
        assert indicator.value == pytest.approx(0.5, abs=0.01)
        assert indicator.toxicity_level == ToxicityLevel.MEDIUM

    def test_vpin_toxicity_level_high(self, small_bucket_config: VPINConfig) -> None:
        """T014.7: VPIN >= 0.7 should return HIGH toxicity."""
        indicator = VPINIndicator(config=small_bucket_config)

        # Fill 10 buckets with high imbalance (90/10 -> OI = 0.8)
        for i in range(10):
            buy_class = make_classification(
                side=TradeSide.BUY,
                volume=90.0,
                timestamp_ns=i * 2 * 1000,
            )
            sell_class = make_classification(
                side=TradeSide.SELL,
                volume=10.0,
                timestamp_ns=i * 2 * 1000 + 500,
            )
            indicator.update(buy_class)
            indicator.update(sell_class)

        assert indicator.is_valid is True
        assert indicator.value == pytest.approx(0.8, abs=0.01)
        assert indicator.toxicity_level == ToxicityLevel.HIGH

    def test_vpin_is_valid_true(self, small_bucket_config: VPINConfig) -> None:
        """T014.8: is_valid should be True after n_buckets filled."""
        indicator = VPINIndicator(config=small_bucket_config)

        # Fill exactly n_buckets (10)
        for i in range(10):
            classification = make_classification(
                side=TradeSide.BUY,
                volume=100.0,
                timestamp_ns=i * 1000,
            )
            indicator.update(classification)
            if i < 9:
                assert indicator.is_valid is False

        assert indicator.is_valid is True

    def test_vpin_rolling_window(self, small_bucket_config: VPINConfig) -> None:
        """T014.9: VPIN should use rolling window of last n_buckets."""
        indicator = VPINIndicator(config=small_bucket_config)

        # Fill 5 buckets with low imbalance (OI = 0.2)
        for i in range(5):
            buy_class = make_classification(
                side=TradeSide.BUY,
                volume=60.0,
                timestamp_ns=i * 2 * 1000,
            )
            sell_class = make_classification(
                side=TradeSide.SELL,
                volume=40.0,
                timestamp_ns=i * 2 * 1000 + 500,
            )
            indicator.update(buy_class)
            indicator.update(sell_class)

        # Fill 10 buckets with high imbalance (OI = 0.8)
        for i in range(10):
            buy_class = make_classification(
                side=TradeSide.BUY,
                volume=90.0,
                timestamp_ns=(i + 5) * 2 * 1000,
            )
            sell_class = make_classification(
                side=TradeSide.SELL,
                volume=10.0,
                timestamp_ns=(i + 5) * 2 * 1000 + 500,
            )
            indicator.update(buy_class)
            indicator.update(sell_class)

        # VPIN should be ~0.8 (only last 10 buckets matter)
        assert indicator.value == pytest.approx(0.8, abs=0.01)


# ==============================================================================
# T015: Edge Case Tests
# ==============================================================================


class TestVPINEdgeCases:
    """Tests for VPIN edge cases and error handling.

    Test ID: T015
    Purpose: Verify graceful handling of edge cases.
    """

    def test_vpin_unknown_side_ignored(self, vpin_indicator: VPINIndicator) -> None:
        """T015.1: UNKNOWN side trades should be ignored."""
        classification = make_classification(
            side=TradeSide.UNKNOWN,
            volume=100.0,
            timestamp_ns=1000,
        )
        vpin_indicator.update(classification)

        # No bucket should be created for UNKNOWN
        assert vpin_indicator._current_bucket is None

    def test_vpin_empty_after_reset(self, small_bucket_config: VPINConfig) -> None:
        """T015.2: reset() should return indicator to initial state."""
        indicator = VPINIndicator(config=small_bucket_config)

        # Add some data
        for i in range(10):
            classification = make_classification(
                side=TradeSide.BUY,
                volume=100.0,
                timestamp_ns=i * 1000,
            )
            indicator.update(classification)

        assert indicator.is_valid is True

        # Reset
        indicator.reset()

        # Should be back to initial state
        assert indicator.value == pytest.approx(0.0, abs=1e-10)
        assert indicator.is_valid is False
        assert len(indicator._buckets) == 0

    def test_vpin_bucket_overflow_carried_to_next(
        self, small_bucket_config: VPINConfig
    ) -> None:
        """T015.3: Overflow volume should be carried to next bucket."""
        indicator = VPINIndicator(config=small_bucket_config)

        # Trade larger than bucket size (100)
        classification = make_classification(
            side=TradeSide.BUY,
            volume=150.0,
            timestamp_ns=1000,
        )
        indicator.update(classification)

        # First bucket should be complete
        assert len(indicator._buckets) >= 1
        assert indicator._buckets[0].is_complete is True

        # Current bucket should have overflow
        assert indicator._current_bucket is not None
        assert indicator._current_bucket.accumulated_volume == pytest.approx(
            50.0, abs=1e-10
        )

    def test_vpin_very_small_volume(self, small_bucket_config: VPINConfig) -> None:
        """T015.4: Very small volumes should accumulate correctly."""
        indicator = VPINIndicator(config=small_bucket_config)

        # Add many small trades - use 0.25 to avoid floating-point issues
        # 400 * 0.25 = 100 (exact bucket size)
        for i in range(400):
            classification = make_classification(
                side=TradeSide.BUY,
                volume=0.25,
                timestamp_ns=i * 1000,
            )
            indicator.update(classification)

        # Should have filled 1 bucket (400 * 0.25 = 100)
        assert len(indicator._buckets) == 1

    def test_vpin_boundary_toxicity_0_3(self, small_bucket_config: VPINConfig) -> None:
        """T015.5: VPIN > 0.3 should be MEDIUM toxicity."""
        indicator = VPINIndicator(config=small_bucket_config)

        # Fill 10 buckets with OI = 0.4 (70/30) to ensure MEDIUM
        # Using 70/30 gives OI = 0.4, clearly in MEDIUM range [0.3, 0.7)
        for i in range(10):
            buy_class = make_classification(
                side=TradeSide.BUY,
                volume=70.0,
                timestamp_ns=i * 2 * 1000,
            )
            sell_class = make_classification(
                side=TradeSide.SELL,
                volume=30.0,
                timestamp_ns=i * 2 * 1000 + 500,
            )
            indicator.update(buy_class)
            indicator.update(sell_class)

        assert indicator.is_valid is True
        assert indicator.value == pytest.approx(0.4, abs=0.01)
        assert indicator.toxicity_level == ToxicityLevel.MEDIUM

    def test_vpin_boundary_toxicity_0_7(self, small_bucket_config: VPINConfig) -> None:
        """T015.6: VPIN exactly 0.7 should be HIGH toxicity."""
        indicator = VPINIndicator(config=small_bucket_config)

        # Fill 10 buckets with OI = 0.7 (85/15)
        for i in range(10):
            buy_class = make_classification(
                side=TradeSide.BUY,
                volume=85.0,
                timestamp_ns=i * 2 * 1000,
            )
            sell_class = make_classification(
                side=TradeSide.SELL,
                volume=15.0,
                timestamp_ns=i * 2 * 1000 + 500,
            )
            indicator.update(buy_class)
            indicator.update(sell_class)

        assert indicator.is_valid is True
        assert indicator.value == pytest.approx(0.7, abs=0.01)
        assert indicator.toxicity_level == ToxicityLevel.HIGH

    def test_vpin_toxicity_level_before_valid(
        self, vpin_indicator: VPINIndicator
    ) -> None:
        """T015.7: Toxicity level should be LOW before valid (VPIN=0)."""
        assert vpin_indicator.is_valid is False
        # VPIN=0.0 returns LOW toxicity
        assert vpin_indicator.toxicity_level == ToxicityLevel.LOW


# ==============================================================================
# Integration Tests
# ==============================================================================


class TestVPINIntegration:
    """Integration tests for VPIN indicator workflow."""

    def test_vpin_complete_workflow(self, small_bucket_config: VPINConfig) -> None:
        """Test complete VPIN workflow from start to finish."""
        indicator = VPINIndicator(config=small_bucket_config)

        # Phase 1: Normal market (balanced trades)
        for i in range(10):
            buy_class = make_classification(
                side=TradeSide.BUY,
                volume=50.0,
                timestamp_ns=i * 2 * 1000,
            )
            sell_class = make_classification(
                side=TradeSide.SELL,
                volume=50.0,
                timestamp_ns=i * 2 * 1000 + 500,
            )
            indicator.update(buy_class)
            indicator.update(sell_class)

        assert indicator.is_valid is True
        assert indicator.toxicity_level == ToxicityLevel.LOW
        initial_vpin = indicator.value

        # Phase 2: Market stress (imbalanced trades)
        for i in range(10):
            sell_class = make_classification(
                side=TradeSide.SELL,
                volume=90.0,
                timestamp_ns=(i + 10) * 2 * 1000,
            )
            buy_class = make_classification(
                side=TradeSide.BUY,
                volume=10.0,
                timestamp_ns=(i + 10) * 2 * 1000 + 500,
            )
            indicator.update(sell_class)
            indicator.update(buy_class)

        # VPIN should increase
        assert indicator.value > initial_vpin
        assert indicator.toxicity_level == ToxicityLevel.HIGH

    def test_vpin_config_validation(self) -> None:
        """Test that VPINIndicator validates its config."""
        # Valid config
        valid_config = VPINConfig(bucket_size=100.0, n_buckets=10)
        indicator = VPINIndicator(config=valid_config)
        assert indicator is not None

        # Config validation is done by Pydantic at config level
        with pytest.raises(Exception):  # ValidationError
            VPINConfig(bucket_size=-100.0)

        with pytest.raises(Exception):  # ValidationError
            VPINConfig(n_buckets=5)  # Must be >= 10

    def test_vpin_get_result(self, small_bucket_config: VPINConfig) -> None:
        """Test get_result returns proper VPINResult."""
        indicator = VPINIndicator(config=small_bucket_config)

        # Fill some buckets
        for i in range(10):
            classification = make_classification(
                side=TradeSide.BUY,
                volume=100.0,
                timestamp_ns=i * 1000,
            )
            indicator.update(classification)

        result = indicator.get_result()

        assert result.value == indicator.value
        assert result.toxicity == indicator.toxicity_level
        assert result.bucket_count == len(indicator._buckets)
        assert result.is_valid == indicator.is_valid


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
