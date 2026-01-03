"""TDD Tests for VPIN Indicator (Spec 025).

These tests are written FIRST (Red phase) - they will FAIL initially
since vpin.py doesn't exist yet. This follows the Test-Driven Development
methodology.

Test IDs:
- T013: VPINBucket tests
- T014: VPINIndicator tests
- T015: Edge case tests
"""

from __future__ import annotations


import pytest

# These imports will fail until implementation exists
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


@pytest.fixture
def buy_classification() -> TradeClassification:
    """Create a buy trade classification."""
    return TradeClassification(
        side=TradeSide.BUY,
        confidence=1.0,
    )


@pytest.fixture
def sell_classification() -> TradeClassification:
    """Create a sell trade classification."""
    return TradeClassification(
        side=TradeSide.SELL,
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
        """T013.1: Bucket with only buys should have OI = 1.0.

        Given: A bucket with buy_volume=100, sell_volume=0
        When: Order imbalance is calculated
        Then: OI should equal 1.0 (maximum buy imbalance)

        Formula: OI = |V_buy - V_sell| / (V_buy + V_sell)
        """
        bucket = VPINBucket(target_volume=100.0)
        bucket.add_volume(volume=100.0, side=TradeSide.BUY)

        oi = bucket.order_imbalance

        assert oi == pytest.approx(1.0, abs=1e-10)

    def test_vpinbucket_order_imbalance_all_sells(self) -> None:
        """T013.2: Bucket with only sells should have OI = 1.0.

        Given: A bucket with buy_volume=0, sell_volume=100
        When: Order imbalance is calculated
        Then: OI should equal 1.0 (maximum sell imbalance)

        Formula: OI = |V_buy - V_sell| / (V_buy + V_sell)
        """
        bucket = VPINBucket(target_volume=100.0)
        bucket.add_volume(volume=100.0, side=TradeSide.SELL)

        oi = bucket.order_imbalance

        assert oi == pytest.approx(1.0, abs=1e-10)

    def test_vpinbucket_order_imbalance_balanced(self) -> None:
        """T013.3: Bucket with equal buys and sells should have OI = 0.0.

        Given: A bucket with buy_volume=50, sell_volume=50
        When: Order imbalance is calculated
        Then: OI should equal 0.0 (perfectly balanced)

        Formula: OI = |50 - 50| / (50 + 50) = 0 / 100 = 0.0
        """
        bucket = VPINBucket(target_volume=100.0)
        bucket.add_volume(volume=50.0, side=TradeSide.BUY)
        bucket.add_volume(volume=50.0, side=TradeSide.SELL)

        oi = bucket.order_imbalance

        assert oi == pytest.approx(0.0, abs=1e-10)

    def test_vpinbucket_order_imbalance_mixed(self) -> None:
        """T013.4: Bucket with mixed trades should calculate correct OI.

        Given: A bucket with buy_volume=70, sell_volume=30
        When: Order imbalance is calculated
        Then: OI should equal 0.4

        Formula: OI = |70 - 30| / (70 + 30) = 40 / 100 = 0.4
        """
        bucket = VPINBucket(target_volume=100.0)
        bucket.add_volume(volume=70.0, side=TradeSide.BUY)
        bucket.add_volume(volume=30.0, side=TradeSide.SELL)

        oi = bucket.order_imbalance

        assert oi == pytest.approx(0.4, abs=1e-10)

    def test_vpinbucket_is_complete(self) -> None:
        """T013.5: Bucket should report complete when target reached.

        Given: A bucket with target_volume=100
        When: Accumulated volume >= target_volume
        Then: is_complete should return True
        """
        bucket = VPINBucket(target_volume=100.0)

        # Not complete yet
        bucket.add_volume(volume=50.0, side=TradeSide.BUY)
        assert bucket.is_complete is False

        # Now complete
        bucket.add_volume(volume=50.0, side=TradeSide.SELL)
        assert bucket.is_complete is True

    def test_vpinbucket_is_complete_with_overflow(self) -> None:
        """T013.6: Bucket should handle volume overflow gracefully.

        Given: A bucket with target_volume=100
        When: A trade with volume > remaining target is added
        Then: is_complete should be True, overflow tracked
        """
        bucket = VPINBucket(target_volume=100.0)
        bucket.add_volume(volume=150.0, side=TradeSide.BUY)

        assert bucket.is_complete is True
        assert bucket.total_volume == 150.0
        assert bucket.overflow_volume == 50.0

    def test_vpinbucket_properties(self) -> None:
        """T013.7: Bucket should track buy/sell volumes separately.

        Given: A bucket with mixed trades
        When: Properties are accessed
        Then: buy_volume and sell_volume should be correct
        """
        bucket = VPINBucket(target_volume=100.0)
        bucket.add_volume(volume=60.0, side=TradeSide.BUY)
        bucket.add_volume(volume=40.0, side=TradeSide.SELL)

        assert bucket.buy_volume == pytest.approx(60.0, abs=1e-10)
        assert bucket.sell_volume == pytest.approx(40.0, abs=1e-10)
        assert bucket.total_volume == pytest.approx(100.0, abs=1e-10)


# ==============================================================================
# T014: VPINIndicator Tests
# ==============================================================================


class TestVPINIndicator:
    """Tests for VPINIndicator main class.

    Test ID: T014
    Purpose: Verify VPIN calculation and toxicity level detection.
    """

    def test_vpin_initial_state(self, vpin_indicator: VPINIndicator) -> None:
        """T014.1: New indicator should have default initial state.

        Given: A freshly created VPINIndicator
        When: Initial state is checked
        Then: value = 0.0, is_valid = False
        """
        assert vpin_indicator.value == pytest.approx(0.0, abs=1e-10)
        assert vpin_indicator.is_valid is False

    def test_vpin_single_update(
        self,
        vpin_indicator: VPINIndicator,
        buy_classification: TradeClassification,
    ) -> None:
        """T014.2: Single trade update should partially fill bucket.

        Given: A VPINIndicator with bucket_size=100
        When: A trade with volume=50 is processed
        Then: Current bucket is partially filled, VPIN not yet valid
        """
        vpin_indicator.update(
            price=100.0,
            volume=50.0,
            classification=buy_classification,
        )

        assert vpin_indicator.is_valid is False
        # Bucket should be partially filled
        assert vpin_indicator.current_bucket.total_volume == pytest.approx(
            50.0, abs=1e-10
        )
        assert vpin_indicator.current_bucket.is_complete is False

    def test_vpin_bucket_completion(
        self,
        small_bucket_config: VPINConfig,
    ) -> None:
        """T014.3: Filling a bucket should add it to history.

        Given: A VPINIndicator with bucket_size=100
        When: Trades totaling >=100 volume are processed
        Then: Bucket should be added to history, new bucket created
        """
        indicator = VPINIndicator(config=small_bucket_config)
        buy = TradeClassification(side=TradeSide.BUY, confidence=1.0)

        # Fill exactly one bucket
        indicator.update(price=100.0, volume=100.0, classification=buy)

        assert len(indicator.bucket_history) == 1
        assert indicator.bucket_history[0].is_complete is True

    def test_vpin_rolling_calculation(
        self,
        small_bucket_config: VPINConfig,
    ) -> None:
        """T014.4: VPIN should be calculated as mean of bucket OIs.

        Given: A VPINIndicator with n_buckets=10
        When: 10 buckets are filled with known imbalances
        Then: VPIN equals mean of order imbalances
        """
        indicator = VPINIndicator(config=small_bucket_config)
        buy = TradeClassification(side=TradeSide.BUY, confidence=1.0)
        sell = TradeClassification(side=TradeSide.SELL, confidence=1.0)

        # Fill 10 buckets with alternating patterns
        # Each bucket: 70 buy, 30 sell -> OI = 0.4
        for _ in range(10):
            indicator.update(price=100.0, volume=70.0, classification=buy)
            indicator.update(price=100.0, volume=30.0, classification=sell)

        assert indicator.is_valid is True
        # All buckets have OI=0.4, so VPIN should be 0.4
        assert indicator.value == pytest.approx(0.4, abs=1e-10)

    def test_vpin_toxicity_level_low(
        self,
        small_bucket_config: VPINConfig,
    ) -> None:
        """T014.5: VPIN < 0.3 should return LOW toxicity.

        Given: A VPINIndicator with VPIN value = 0.2
        When: toxicity_level is queried
        Then: Returns ToxicityLevel.LOW
        """
        indicator = VPINIndicator(config=small_bucket_config)
        buy = TradeClassification(side=TradeSide.BUY, confidence=1.0)
        sell = TradeClassification(side=TradeSide.SELL, confidence=1.0)

        # Fill 10 buckets with low imbalance (60/40 -> OI = 0.2)
        for _ in range(10):
            indicator.update(price=100.0, volume=60.0, classification=buy)
            indicator.update(price=100.0, volume=40.0, classification=sell)

        assert indicator.is_valid is True
        assert indicator.value == pytest.approx(0.2, abs=1e-10)
        assert indicator.toxicity_level == ToxicityLevel.LOW

    def test_vpin_toxicity_level_medium(
        self,
        small_bucket_config: VPINConfig,
    ) -> None:
        """T014.6: 0.3 <= VPIN < 0.7 should return MEDIUM toxicity.

        Given: A VPINIndicator with VPIN value = 0.5
        When: toxicity_level is queried
        Then: Returns ToxicityLevel.MEDIUM
        """
        indicator = VPINIndicator(config=small_bucket_config)
        buy = TradeClassification(side=TradeSide.BUY, confidence=1.0)
        sell = TradeClassification(side=TradeSide.SELL, confidence=1.0)

        # Fill 10 buckets with medium imbalance (75/25 -> OI = 0.5)
        for _ in range(10):
            indicator.update(price=100.0, volume=75.0, classification=buy)
            indicator.update(price=100.0, volume=25.0, classification=sell)

        assert indicator.is_valid is True
        assert indicator.value == pytest.approx(0.5, abs=1e-10)
        assert indicator.toxicity_level == ToxicityLevel.MEDIUM

    def test_vpin_toxicity_level_high(
        self,
        small_bucket_config: VPINConfig,
    ) -> None:
        """T014.7: VPIN >= 0.7 should return HIGH toxicity.

        Given: A VPINIndicator with VPIN value = 0.8
        When: toxicity_level is queried
        Then: Returns ToxicityLevel.HIGH
        """
        indicator = VPINIndicator(config=small_bucket_config)
        buy = TradeClassification(side=TradeSide.BUY, confidence=1.0)
        sell = TradeClassification(side=TradeSide.SELL, confidence=1.0)

        # Fill 10 buckets with high imbalance (90/10 -> OI = 0.8)
        for _ in range(10):
            indicator.update(price=100.0, volume=90.0, classification=buy)
            indicator.update(price=100.0, volume=10.0, classification=sell)

        assert indicator.is_valid is True
        assert indicator.value == pytest.approx(0.8, abs=1e-10)
        assert indicator.toxicity_level == ToxicityLevel.HIGH

    def test_vpin_is_valid_true(
        self,
        small_bucket_config: VPINConfig,
    ) -> None:
        """T014.8: is_valid should be True after n_buckets filled.

        Given: A VPINIndicator with n_buckets=10
        When: 10 buckets have been completed
        Then: is_valid returns True
        """
        indicator = VPINIndicator(config=small_bucket_config)
        buy = TradeClassification(side=TradeSide.BUY, confidence=1.0)

        # Fill exactly n_buckets
        for i in range(10):
            indicator.update(price=100.0, volume=100.0, classification=buy)
            if i < 9:
                assert indicator.is_valid is False

        assert indicator.is_valid is True

    def test_vpin_rolling_window(
        self,
        small_bucket_config: VPINConfig,
    ) -> None:
        """T014.9: VPIN should use rolling window of last n_buckets.

        Given: A VPINIndicator with n_buckets=10
        When: 15 buckets are filled
        Then: VPIN is calculated from last 10 buckets only
        """
        indicator = VPINIndicator(config=small_bucket_config)
        buy = TradeClassification(side=TradeSide.BUY, confidence=1.0)
        sell = TradeClassification(side=TradeSide.SELL, confidence=1.0)

        # Fill 5 buckets with low imbalance (OI = 0.2)
        for _ in range(5):
            indicator.update(price=100.0, volume=60.0, classification=buy)
            indicator.update(price=100.0, volume=40.0, classification=sell)

        # Fill 10 buckets with high imbalance (OI = 0.8)
        for _ in range(10):
            indicator.update(price=100.0, volume=90.0, classification=buy)
            indicator.update(price=100.0, volume=10.0, classification=sell)

        # VPIN should be ~0.8 (only last 10 buckets matter)
        assert indicator.value == pytest.approx(0.8, abs=1e-10)


# ==============================================================================
# T015: Edge Case Tests
# ==============================================================================


class TestVPINEdgeCases:
    """Tests for VPIN edge cases and error handling.

    Test ID: T015
    Purpose: Verify graceful handling of edge cases.
    """

    def test_vpin_zero_volume(self, vpin_indicator: VPINIndicator) -> None:
        """T015.1: Zero volume trade should be handled gracefully.

        Given: A VPINIndicator
        When: A trade with volume=0 is processed
        Then: Trade is ignored, no error raised
        """
        buy = TradeClassification(side=TradeSide.BUY, confidence=1.0)

        # Should not raise
        vpin_indicator.update(price=100.0, volume=0.0, classification=buy)

        # State should be unchanged
        assert vpin_indicator.current_bucket.total_volume == pytest.approx(
            0.0, abs=1e-10
        )

    def test_vpin_empty_after_reset(
        self,
        small_bucket_config: VPINConfig,
    ) -> None:
        """T015.2: reset() should return indicator to initial state.

        Given: A VPINIndicator with some data
        When: reset() is called
        Then: Indicator returns to initial state
        """
        indicator = VPINIndicator(config=small_bucket_config)
        buy = TradeClassification(side=TradeSide.BUY, confidence=1.0)

        # Add some data
        for _ in range(10):
            indicator.update(price=100.0, volume=100.0, classification=buy)

        assert indicator.is_valid is True

        # Reset
        indicator.reset()

        # Should be back to initial state
        assert indicator.value == pytest.approx(0.0, abs=1e-10)
        assert indicator.is_valid is False
        assert len(indicator.bucket_history) == 0

    def test_vpin_nan_handling(self, vpin_indicator: VPINIndicator) -> None:
        """T015.3: NaN price/volume should be handled gracefully.

        Given: A VPINIndicator
        When: A trade with NaN price or volume is processed
        Then: Trade is skipped, no error raised
        """
        buy = TradeClassification(side=TradeSide.BUY, confidence=1.0)

        # NaN price should be skipped
        vpin_indicator.update(price=float("nan"), volume=100.0, classification=buy)
        assert vpin_indicator.current_bucket.total_volume == pytest.approx(
            0.0, abs=1e-10
        )

        # NaN volume should be skipped
        vpin_indicator.update(price=100.0, volume=float("nan"), classification=buy)
        assert vpin_indicator.current_bucket.total_volume == pytest.approx(
            0.0, abs=1e-10
        )

    def test_vpin_negative_volume(self, vpin_indicator: VPINIndicator) -> None:
        """T015.4: Negative volume should be handled gracefully.

        Given: A VPINIndicator
        When: A trade with negative volume is processed
        Then: Trade is ignored, no error raised
        """
        buy = TradeClassification(side=TradeSide.BUY, confidence=1.0)

        # Negative volume should be ignored
        vpin_indicator.update(price=100.0, volume=-50.0, classification=buy)

        assert vpin_indicator.current_bucket.total_volume == pytest.approx(
            0.0, abs=1e-10
        )

    def test_vpin_negative_price(self, vpin_indicator: VPINIndicator) -> None:
        """T015.5: Negative price should be handled gracefully.

        Given: A VPINIndicator
        When: A trade with negative price is processed
        Then: Trade is ignored, no error raised
        """
        buy = TradeClassification(side=TradeSide.BUY, confidence=1.0)

        # Negative price should be ignored
        vpin_indicator.update(price=-100.0, volume=50.0, classification=buy)

        assert vpin_indicator.current_bucket.total_volume == pytest.approx(
            0.0, abs=1e-10
        )

    def test_vpin_inf_handling(self, vpin_indicator: VPINIndicator) -> None:
        """T015.6: Infinity values should be handled gracefully.

        Given: A VPINIndicator
        When: A trade with inf price or volume is processed
        Then: Trade is skipped, no error raised
        """
        buy = TradeClassification(side=TradeSide.BUY, confidence=1.0)

        # Inf price should be skipped
        vpin_indicator.update(price=float("inf"), volume=100.0, classification=buy)
        assert vpin_indicator.current_bucket.total_volume == pytest.approx(
            0.0, abs=1e-10
        )

        # Inf volume should be skipped
        vpin_indicator.update(price=100.0, volume=float("inf"), classification=buy)
        assert vpin_indicator.current_bucket.total_volume == pytest.approx(
            0.0, abs=1e-10
        )

    def test_vpin_empty_bucket_order_imbalance(self) -> None:
        """T015.7: Empty bucket should return OI = 0.0.

        Given: An empty VPINBucket
        When: order_imbalance is queried
        Then: Returns 0.0 (avoid division by zero)
        """
        bucket = VPINBucket(target_volume=100.0)

        # Empty bucket should have OI = 0.0
        assert bucket.order_imbalance == pytest.approx(0.0, abs=1e-10)

    def test_vpin_toxicity_level_before_valid(
        self,
        vpin_indicator: VPINIndicator,
    ) -> None:
        """T015.8: Toxicity level should be None before indicator is valid.

        Given: A VPINIndicator that is not yet valid
        When: toxicity_level is queried
        Then: Returns None or raises appropriate error
        """
        assert vpin_indicator.is_valid is False
        # Should return None when not valid
        assert vpin_indicator.toxicity_level is None

    def test_vpin_bucket_overflow_carried_to_next(
        self,
        small_bucket_config: VPINConfig,
    ) -> None:
        """T015.9: Overflow volume should be carried to next bucket.

        Given: A VPINIndicator with bucket_size=100
        When: A trade with volume=150 is processed
        Then: First bucket filled with 100, overflow of 50 goes to next bucket
        """
        indicator = VPINIndicator(config=small_bucket_config)
        buy = TradeClassification(side=TradeSide.BUY, confidence=1.0)

        # Trade larger than bucket size
        indicator.update(price=100.0, volume=150.0, classification=buy)

        # First bucket should be complete
        assert len(indicator.bucket_history) >= 1
        assert indicator.bucket_history[0].total_volume == pytest.approx(
            100.0, abs=1e-10
        )

        # Current bucket should have overflow
        assert indicator.current_bucket.total_volume == pytest.approx(50.0, abs=1e-10)

    def test_vpin_very_small_volume(
        self,
        small_bucket_config: VPINConfig,
    ) -> None:
        """T015.10: Very small volumes should accumulate correctly.

        Given: A VPINIndicator
        When: Many very small trades are processed
        Then: Volumes accumulate correctly, bucket eventually fills
        """
        indicator = VPINIndicator(config=small_bucket_config)
        buy = TradeClassification(side=TradeSide.BUY, confidence=1.0)

        # Add many small trades
        for _ in range(1000):
            indicator.update(price=100.0, volume=0.1, classification=buy)

        # Should have filled 1 bucket (1000 * 0.1 = 100)
        assert len(indicator.bucket_history) == 1

    def test_vpin_boundary_toxicity_0_3(
        self,
        small_bucket_config: VPINConfig,
    ) -> None:
        """T015.11: VPIN exactly 0.3 should be MEDIUM toxicity.

        Given: A VPINIndicator with VPIN value = 0.3
        When: toxicity_level is queried
        Then: Returns ToxicityLevel.MEDIUM (boundary case)
        """
        indicator = VPINIndicator(config=small_bucket_config)
        buy = TradeClassification(side=TradeSide.BUY, confidence=1.0)
        sell = TradeClassification(side=TradeSide.SELL, confidence=1.0)

        # Fill 10 buckets with OI = 0.3 (65/35)
        for _ in range(10):
            indicator.update(price=100.0, volume=65.0, classification=buy)
            indicator.update(price=100.0, volume=35.0, classification=sell)

        assert indicator.is_valid is True
        assert indicator.value == pytest.approx(0.3, abs=1e-10)
        # 0.3 is the boundary - should be MEDIUM (>= 0.3)
        assert indicator.toxicity_level == ToxicityLevel.MEDIUM

    def test_vpin_boundary_toxicity_0_7(
        self,
        small_bucket_config: VPINConfig,
    ) -> None:
        """T015.12: VPIN exactly 0.7 should be HIGH toxicity.

        Given: A VPINIndicator with VPIN value = 0.7
        When: toxicity_level is queried
        Then: Returns ToxicityLevel.HIGH (boundary case)
        """
        indicator = VPINIndicator(config=small_bucket_config)
        buy = TradeClassification(side=TradeSide.BUY, confidence=1.0)
        sell = TradeClassification(side=TradeSide.SELL, confidence=1.0)

        # Fill 10 buckets with OI = 0.7 (85/15)
        for _ in range(10):
            indicator.update(price=100.0, volume=85.0, classification=buy)
            indicator.update(price=100.0, volume=15.0, classification=sell)

        assert indicator.is_valid is True
        assert indicator.value == pytest.approx(0.7, abs=1e-10)
        # 0.7 is the boundary - should be HIGH (>= 0.7)
        assert indicator.toxicity_level == ToxicityLevel.HIGH


# ==============================================================================
# Additional Integration Tests
# ==============================================================================


class TestVPINIntegration:
    """Integration tests for VPIN indicator workflow.

    Purpose: Verify complete VPIN workflow from data input to toxicity output.
    """

    def test_vpin_complete_workflow(
        self,
        small_bucket_config: VPINConfig,
    ) -> None:
        """Test complete VPIN workflow from start to finish.

        Given: A fresh VPINIndicator
        When: Trades are processed simulating a flash crash scenario
        Then: VPIN correctly detects increasing toxicity
        """
        indicator = VPINIndicator(config=small_bucket_config)
        buy = TradeClassification(side=TradeSide.BUY, confidence=1.0)
        sell = TradeClassification(side=TradeSide.SELL, confidence=1.0)

        # Phase 1: Normal market (balanced trades)
        for _ in range(10):
            indicator.update(price=100.0, volume=50.0, classification=buy)
            indicator.update(price=100.0, volume=50.0, classification=sell)

        assert indicator.is_valid is True
        assert indicator.toxicity_level == ToxicityLevel.LOW
        initial_vpin = indicator.value

        # Phase 2: Market stress (imbalanced trades)
        for _ in range(10):
            indicator.update(price=99.0, volume=90.0, classification=sell)
            indicator.update(price=99.0, volume=10.0, classification=buy)

        # VPIN should increase
        assert indicator.value > initial_vpin
        assert indicator.toxicity_level == ToxicityLevel.HIGH

    def test_vpin_config_validation(self) -> None:
        """Test that VPINIndicator validates its config.

        Given: Various configurations
        When: VPINIndicator is created
        Then: Invalid configs are rejected
        """
        # Valid config
        valid_config = VPINConfig(bucket_size=100.0, n_buckets=10)
        indicator = VPINIndicator(config=valid_config)
        assert indicator is not None

        # Config validation is done by Pydantic at config level
        with pytest.raises(Exception):  # ValidationError
            VPINConfig(bucket_size=-100.0)

        with pytest.raises(Exception):  # ValidationError
            VPINConfig(n_buckets=5)  # Must be >= 10

    def test_vpin_bucket_timestamps(
        self,
        small_bucket_config: VPINConfig,
    ) -> None:
        """Test that buckets track timestamps.

        Given: A VPINIndicator
        When: Trades with timestamps are processed
        Then: Buckets track start and end timestamps
        """
        indicator = VPINIndicator(config=small_bucket_config)
        buy = TradeClassification(side=TradeSide.BUY, confidence=1.0)

        # Fill a bucket with timestamp
        indicator.update(
            price=100.0,
            volume=100.0,
            classification=buy,
            timestamp_ns=1000000000,  # 1 second in nanoseconds
        )

        assert len(indicator.bucket_history) == 1
        bucket = indicator.bucket_history[0]

        # Bucket should have timestamp info
        assert hasattr(bucket, "start_timestamp_ns")
        assert hasattr(bucket, "end_timestamp_ns")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
