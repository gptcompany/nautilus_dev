"""Unit tests for Trade Classification (Spec 025 - T012).

Tests for TickRuleClassifier, BVCClassifier, and CloseVsOpenClassifier.
"""

import pytest

from strategies.common.orderflow.trade_classifier import (
    BVCClassifier,
    CloseVsOpenClassifier,
    TickRuleClassifier,
    TradeClassification,
    TradeSide,
    create_classifier,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def tick_classifier() -> TickRuleClassifier:
    """Create a fresh TickRuleClassifier."""
    return TickRuleClassifier()


@pytest.fixture
def bvc_classifier() -> BVCClassifier:
    """Create a fresh BVCClassifier."""
    return BVCClassifier()


@pytest.fixture
def close_vs_open_classifier() -> CloseVsOpenClassifier:
    """Create a fresh CloseVsOpenClassifier."""
    return CloseVsOpenClassifier()


# =============================================================================
# TradeClassification Tests
# =============================================================================


class TestTradeClassification:
    """Tests for TradeClassification dataclass."""

    def test_trade_classification_creation(self):
        """Test basic TradeClassification instantiation."""
        tc = TradeClassification(
            side=TradeSide.BUY,
            volume=100.0,
            price=50000.0,
            timestamp_ns=1000000000,
            method="tick_rule",
            confidence=0.9,
        )
        assert tc.side == TradeSide.BUY
        assert tc.volume == 100.0
        assert tc.price == 50000.0
        assert tc.timestamp_ns == 1000000000
        assert tc.method == "tick_rule"
        assert tc.confidence == 0.9

    def test_trade_classification_default_confidence(self):
        """Test TradeClassification with default confidence."""
        tc = TradeClassification(
            side=TradeSide.SELL,
            volume=50.0,
            price=49000.0,
            timestamp_ns=2000000000,
            method="bvc",
        )
        assert tc.confidence == 1.0


# =============================================================================
# TradeSide Enum Tests
# =============================================================================


class TestTradeSide:
    """Tests for TradeSide enum."""

    def test_trade_side_values(self):
        """Test TradeSide enum values."""
        assert TradeSide.BUY.value == 1
        assert TradeSide.SELL.value == -1
        assert TradeSide.UNKNOWN.value == 0


# =============================================================================
# TickRuleClassifier Tests
# =============================================================================


class TestTickRuleClassifier:
    """Tests for TickRuleClassifier."""

    def test_tick_rule_buy_uptick(self, tick_classifier: TickRuleClassifier):
        """Price increase should classify as BUY."""
        result = tick_classifier.classify(
            price=100.0,
            volume=10.0,
            timestamp_ns=1000,
            prev_price=99.0,
        )
        assert result.side == TradeSide.BUY
        assert result.method == "tick_rule"

    def test_tick_rule_sell_downtick(self, tick_classifier: TickRuleClassifier):
        """Price decrease should classify as SELL."""
        result = tick_classifier.classify(
            price=99.0,
            volume=10.0,
            timestamp_ns=1000,
            prev_price=100.0,
        )
        assert result.side == TradeSide.SELL
        assert result.method == "tick_rule"

    def test_tick_rule_zero_tick_uses_previous(
        self, tick_classifier: TickRuleClassifier
    ):
        """Zero tick should use previous classification."""
        # First uptick → BUY
        tick_classifier.classify(
            price=100.0, volume=10.0, timestamp_ns=1000, prev_price=99.0
        )
        # Zero tick → should still be BUY
        result = tick_classifier.classify(
            price=100.0,
            volume=10.0,
            timestamp_ns=2000,
            prev_price=100.0,
        )
        assert result.side == TradeSide.BUY

    def test_tick_rule_initial_zero_tick(self, tick_classifier: TickRuleClassifier):
        """Initial zero tick with no history should be UNKNOWN."""
        result = tick_classifier.classify(
            price=100.0,
            volume=10.0,
            timestamp_ns=1000,
            prev_price=100.0,
        )
        assert result.side == TradeSide.UNKNOWN

    def test_tick_rule_no_prev_price_first_call(
        self, tick_classifier: TickRuleClassifier
    ):
        """First call without prev_price should be UNKNOWN."""
        result = tick_classifier.classify(
            price=100.0,
            volume=10.0,
            timestamp_ns=1000,
        )
        assert result.side == TradeSide.UNKNOWN

    def test_tick_rule_tracks_internal_prev_price(
        self, tick_classifier: TickRuleClassifier
    ):
        """Classifier should track previous price internally."""
        # First call with no prev_price
        tick_classifier.classify(price=100.0, volume=10.0, timestamp_ns=1000)
        # Second call - should use internal prev_price
        result = tick_classifier.classify(price=101.0, volume=10.0, timestamp_ns=2000)
        assert result.side == TradeSide.BUY


# =============================================================================
# BVCClassifier Tests
# =============================================================================


class TestBVCClassifier:
    """Tests for Bulk Volume Classification (BVC)."""

    def test_bvc_close_at_high(self, bvc_classifier: BVCClassifier):
        """Close at high should classify as BUY."""
        result = bvc_classifier.classify(
            price=100.0,  # close
            volume=10.0,
            timestamp_ns=1000,
            high=100.0,
            low=90.0,
        )
        assert result.side == TradeSide.BUY
        assert result.confidence > 0.9  # High confidence

    def test_bvc_close_at_low(self, bvc_classifier: BVCClassifier):
        """Close at low should classify as SELL."""
        result = bvc_classifier.classify(
            price=90.0,  # close
            volume=10.0,
            timestamp_ns=1000,
            high=100.0,
            low=90.0,
        )
        assert result.side == TradeSide.SELL
        assert result.confidence > 0.9  # High confidence

    def test_bvc_close_at_midpoint(self, bvc_classifier: BVCClassifier):
        """Close at midpoint should have low confidence."""
        result = bvc_classifier.classify(
            price=95.0,  # close at midpoint
            volume=10.0,
            timestamp_ns=1000,
            high=100.0,
            low=90.0,
        )
        assert result.confidence < 0.2  # Low confidence at midpoint

    def test_bvc_missing_high_low(self, bvc_classifier: BVCClassifier):
        """Missing high/low should return UNKNOWN."""
        result = bvc_classifier.classify(
            price=100.0,
            volume=10.0,
            timestamp_ns=1000,
        )
        assert result.side == TradeSide.UNKNOWN

    def test_bvc_zero_range(self, bvc_classifier: BVCClassifier):
        """Zero range (high == low) should handle gracefully."""
        result = bvc_classifier.classify(
            price=100.0,
            volume=10.0,
            timestamp_ns=1000,
            high=100.0,
            low=100.0,
        )
        # Should not crash - with epsilon close == low, buy_ratio near 0, so SELL
        # The important thing is it doesn't crash on division by zero
        assert result.side in (TradeSide.BUY, TradeSide.SELL, TradeSide.UNKNOWN)


# =============================================================================
# CloseVsOpenClassifier Tests
# =============================================================================


class TestCloseVsOpenClassifier:
    """Tests for CloseVsOpenClassifier."""

    def test_close_vs_open_bullish(
        self, close_vs_open_classifier: CloseVsOpenClassifier
    ):
        """Close > Open should classify as BUY."""
        result = close_vs_open_classifier.classify(
            price=105.0,  # close
            volume=10.0,
            timestamp_ns=1000,
            open_price=100.0,
        )
        assert result.side == TradeSide.BUY
        assert result.method == "close_vs_open"

    def test_close_vs_open_bearish(
        self, close_vs_open_classifier: CloseVsOpenClassifier
    ):
        """Close < Open should classify as SELL."""
        result = close_vs_open_classifier.classify(
            price=95.0,  # close
            volume=10.0,
            timestamp_ns=1000,
            open_price=100.0,
        )
        assert result.side == TradeSide.SELL

    def test_close_vs_open_doji(self, close_vs_open_classifier: CloseVsOpenClassifier):
        """Close == Open should classify as UNKNOWN."""
        result = close_vs_open_classifier.classify(
            price=100.0,
            volume=10.0,
            timestamp_ns=1000,
            open_price=100.0,
        )
        assert result.side == TradeSide.UNKNOWN

    def test_close_vs_open_missing_open(
        self, close_vs_open_classifier: CloseVsOpenClassifier
    ):
        """Missing open_price should return UNKNOWN."""
        result = close_vs_open_classifier.classify(
            price=100.0,
            volume=10.0,
            timestamp_ns=1000,
        )
        assert result.side == TradeSide.UNKNOWN


# =============================================================================
# Factory Function Tests
# =============================================================================


class TestCreateClassifier:
    """Tests for create_classifier factory function."""

    def test_create_tick_rule(self):
        """Create tick_rule classifier."""
        clf = create_classifier("tick_rule")
        assert isinstance(clf, TickRuleClassifier)

    def test_create_bvc(self):
        """Create bvc classifier."""
        clf = create_classifier("bvc")
        assert isinstance(clf, BVCClassifier)

    def test_create_close_vs_open(self):
        """Create close_vs_open classifier."""
        clf = create_classifier("close_vs_open")
        assert isinstance(clf, CloseVsOpenClassifier)

    def test_create_invalid_method(self):
        """Invalid method should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid classification method"):
            create_classifier("invalid_method")
