"""
Comprehensive tests for DailyPnLTracker (Spec 013).

Tests cover:
1. Initialization and configuration
2. PnL tracking (realized and unrealized)
3. Daily limit checking and triggering
4. Day boundary handling and resets
5. Position closing on limit
6. Edge cases: negative PnL, zero, large values, timezone handling

This is a PRODUCTION trading system handling REAL MONEY.
"""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from nautilus_trader.model.enums import OrderSide, PositionSide
from nautilus_trader.model.events import PositionClosed
from nautilus_trader.model.objects import Currency

from risk.daily_loss_config import DailyLossConfig
from risk.daily_pnl_tracker import DailyPnLTracker

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def default_config():
    """Create default DailyLossConfig for testing."""
    return DailyLossConfig(
        daily_loss_limit=Decimal("1000"),
        reset_time_utc="00:00",
        per_strategy=False,
        close_positions_on_limit=True,
        warning_threshold_pct=Decimal("0.5"),
    )


@pytest.fixture
def percentage_config():
    """Create percentage-based DailyLossConfig for testing."""
    return DailyLossConfig(
        daily_loss_limit=Decimal("1000"),
        daily_loss_pct=Decimal("0.02"),  # 2% of equity
        reset_time_utc="00:00",
        per_strategy=False,
        close_positions_on_limit=True,
        warning_threshold_pct=Decimal("0.5"),
    )


@pytest.fixture
def no_close_config():
    """Create config that doesn't close positions on limit."""
    return DailyLossConfig(
        daily_loss_limit=Decimal("500"),
        reset_time_utc="00:00",
        per_strategy=False,
        close_positions_on_limit=False,
        warning_threshold_pct=Decimal("0.5"),
    )


@pytest.fixture
def mock_strategy():
    """Create mock strategy with portfolio and cache."""
    strategy = MagicMock()

    # Mock portfolio
    strategy.portfolio.unrealized_pnls.return_value = {}
    strategy.portfolio.balances.return_value = {}

    # Mock cache
    strategy.cache.positions_open.return_value = []

    # Mock clock
    strategy.clock.utc_now.return_value = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)

    # Mock order factory
    strategy.order_factory.market = MagicMock()
    strategy.submit_order = MagicMock()

    return strategy


@pytest.fixture
def mock_position_closed_event():
    """Create mock PositionClosed event."""
    event = MagicMock(spec=PositionClosed)
    pnl = MagicMock()
    pnl.__float__ = MagicMock(return_value=100.0)
    event.realized_pnl = pnl
    return event


@pytest.fixture
def tracker(default_config, mock_strategy):
    """Create DailyPnLTracker instance for testing."""
    return DailyPnLTracker(config=default_config, strategy=mock_strategy)


# =============================================================================
# T001: Initialization Tests
# =============================================================================


class TestInitialization:
    """Tests for DailyPnLTracker initialization."""

    def test_tracker_initializes_with_config(self, default_config, mock_strategy):
        """Tracker should initialize with provided config."""
        tracker = DailyPnLTracker(config=default_config, strategy=mock_strategy)

        assert tracker.config == default_config
        assert tracker._strategy == mock_strategy

    def test_daily_realized_starts_at_zero(self, tracker):
        """Daily realized PnL should start at zero."""
        assert tracker.daily_realized == Decimal("0")

    def test_limit_not_triggered_initially(self, tracker):
        """Limit should not be triggered on initialization."""
        assert tracker.limit_triggered is False

    def test_day_start_set_on_init(self, tracker, mock_strategy):
        """Day start should be set to current time on init."""
        expected_time = mock_strategy.clock.utc_now.return_value
        assert tracker.day_start == expected_time

    def test_starting_equity_calculated(self, tracker):
        """Starting equity should be calculated on init."""
        # Fallback: 50x daily_loss_limit (1000 * 50 = 50000)
        assert tracker._starting_equity == Decimal("50000")


# =============================================================================
# T002: Property Tests
# =============================================================================


class TestProperties:
    """Tests for tracker property getters."""

    def test_config_property_returns_config(self, tracker, default_config):
        """config property should return the config."""
        assert tracker.config == default_config

    def test_daily_realized_property(self, tracker):
        """daily_realized property should return realized PnL."""
        tracker._daily_realized = Decimal("150.50")
        assert tracker.daily_realized == Decimal("150.50")

    def test_daily_unrealized_with_empty_portfolio(self, tracker):
        """daily_unrealized should return 0 for empty portfolio."""
        assert tracker.daily_unrealized == Decimal("0")

    def test_daily_unrealized_with_dict_values(self, tracker, mock_strategy):
        """daily_unrealized should sum values from dict[Currency, Money]."""
        usd = Currency.from_str("USD")
        btc = Currency.from_str("BTC")

        money_usd = MagicMock()
        money_usd.__float__ = MagicMock(return_value=250.0)

        money_btc = MagicMock()
        money_btc.__float__ = MagicMock(return_value=150.0)

        mock_strategy.portfolio.unrealized_pnls.return_value = {
            usd: money_usd,
            btc: money_btc,
        }

        assert tracker.daily_unrealized == Decimal("400")

    def test_daily_unrealized_with_none_values(self, tracker, mock_strategy):
        """daily_unrealized should handle None values in dict."""
        usd = Currency.from_str("USD")

        mock_strategy.portfolio.unrealized_pnls.return_value = {
            usd: None,
        }

        assert tracker.daily_unrealized == Decimal("0")

    def test_total_daily_pnl_sums_realized_and_unrealized(self, tracker, mock_strategy):
        """total_daily_pnl should sum realized and unrealized."""
        tracker._daily_realized = Decimal("200")

        money = MagicMock()
        money.__float__ = MagicMock(return_value=150.0)
        mock_strategy.portfolio.unrealized_pnls.return_value = {
            Currency.from_str("USD"): money
        }

        assert tracker.total_daily_pnl == Decimal("350")

    def test_limit_triggered_property(self, tracker):
        """limit_triggered property should reflect internal state."""
        assert tracker.limit_triggered is False

        tracker._limit_triggered = True
        assert tracker.limit_triggered is True

    def test_day_start_property(self, tracker):
        """day_start property should return day start time."""
        expected = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)
        assert tracker.day_start == expected


# =============================================================================
# T003: Event Handling Tests
# =============================================================================


class TestEventHandling:
    """Tests for event handling and PnL updates."""

    def test_handle_position_closed_event(self, tracker, mock_position_closed_event):
        """handle_event should process PositionClosed events."""
        tracker.handle_event(mock_position_closed_event)

        assert tracker.daily_realized == Decimal("100")

    def test_handle_event_uses_duck_typing(self, tracker):
        """handle_event should accept any object with realized_pnl attribute."""
        event = MagicMock()
        pnl = MagicMock()
        pnl.__float__ = MagicMock(return_value=50.0)
        event.realized_pnl = pnl

        tracker.handle_event(event)

        assert tracker.daily_realized == Decimal("50")

    def test_handle_event_ignores_events_without_pnl(self, tracker):
        """handle_event should ignore events without realized_pnl."""
        event = MagicMock(spec=[])  # No realized_pnl attribute

        tracker.handle_event(event)

        assert tracker.daily_realized == Decimal("0")

    def test_multiple_position_closed_events_accumulate(self, tracker):
        """Multiple events should accumulate realized PnL."""
        event1 = MagicMock()
        pnl1 = MagicMock()
        pnl1.__float__ = MagicMock(return_value=100.0)
        event1.realized_pnl = pnl1

        event2 = MagicMock()
        pnl2 = MagicMock()
        pnl2.__float__ = MagicMock(return_value=50.0)
        event2.realized_pnl = pnl2

        tracker.handle_event(event1)
        tracker.handle_event(event2)

        assert tracker.daily_realized == Decimal("150")

    def test_negative_pnl_tracked_correctly(self, tracker):
        """Negative PnL should be tracked correctly."""
        event = MagicMock()
        pnl = MagicMock()
        pnl.__float__ = MagicMock(return_value=-250.0)
        event.realized_pnl = pnl

        tracker.handle_event(event)

        assert tracker.daily_realized == Decimal("-250")

    def test_zero_pnl_handled(self, tracker):
        """Zero PnL should be handled without errors."""
        event = MagicMock()
        pnl = MagicMock()
        pnl.__float__ = MagicMock(return_value=0.0)
        event.realized_pnl = pnl

        tracker.handle_event(event)

        assert tracker.daily_realized == Decimal("0")

    def test_large_pnl_values(self, tracker):
        """Large PnL values should be handled correctly."""
        event = MagicMock()
        pnl = MagicMock()
        pnl.__float__ = MagicMock(return_value=1_000_000.0)
        event.realized_pnl = pnl

        tracker.handle_event(event)

        assert tracker.daily_realized == Decimal("1000000")


# =============================================================================
# T004: Limit Checking Tests
# =============================================================================


class TestLimitChecking:
    """Tests for daily loss limit checking."""

    def test_check_limit_returns_false_when_not_exceeded(self, tracker):
        """check_limit should return False when limit not exceeded."""
        tracker._daily_realized = Decimal("-500")  # Below 1000 limit

        assert tracker.check_limit() is False

    def test_check_limit_returns_true_when_exceeded(self, tracker, mock_strategy):
        """check_limit should return True when limit exceeded."""
        tracker._daily_realized = Decimal("-1001")  # Exceeds 1000 limit

        assert tracker.check_limit() is True
        assert tracker.limit_triggered is True

    def test_check_limit_uses_total_pnl(self, tracker, mock_strategy):
        """check_limit should use total PnL (realized + unrealized)."""
        tracker._daily_realized = Decimal("-600")

        money = MagicMock()
        money.__float__ = MagicMock(return_value=-450.0)
        mock_strategy.portfolio.unrealized_pnls.return_value = {
            Currency.from_str("USD"): money
        }

        # Total: -600 + (-450) = -1050, exceeds 1000
        assert tracker.check_limit() is True

    def test_check_limit_exact_limit_value(self, tracker):
        """check_limit should trigger at exact limit value."""
        tracker._daily_realized = Decimal("-1000")

        assert tracker.check_limit() is True

    def test_check_limit_returns_immediately_if_already_triggered(self, tracker):
        """check_limit should return immediately if already triggered."""
        tracker._limit_triggered = True
        tracker._daily_realized = Decimal("0")  # Positive PnL

        assert tracker.check_limit() is True

    def test_warning_threshold_emits_warning(self, tracker, caplog):
        """check_limit should emit warning at 50% threshold."""
        import logging
        caplog.set_level(logging.WARNING)

        # 50% of 1000 = 500
        tracker._daily_realized = Decimal("-500")

        tracker.check_limit()

        assert "Daily PnL warning" in caplog.text
        assert tracker._warning_emitted is True

    def test_warning_only_emitted_once(self, tracker, caplog):
        """Warning should only be emitted once."""
        import logging
        caplog.set_level(logging.WARNING)

        tracker._daily_realized = Decimal("-500")
        tracker.check_limit()

        caplog.clear()

        tracker._daily_realized = Decimal("-600")
        tracker.check_limit()

        assert "Daily PnL warning" not in caplog.text

    def test_percentage_based_limit(self, percentage_config, mock_strategy):
        """check_limit should use percentage-based limit when configured."""
        # Mock starting equity of 50000
        mock_strategy.portfolio.balances.return_value = {}

        tracker = DailyPnLTracker(config=percentage_config, strategy=mock_strategy)
        tracker._starting_equity = Decimal("50000")

        # 2% of 50000 = 1000
        tracker._daily_realized = Decimal("-1001")

        assert tracker.check_limit() is True

    def test_positive_pnl_does_not_trigger_limit(self, tracker):
        """Positive PnL should never trigger limit."""
        tracker._daily_realized = Decimal("5000")

        assert tracker.check_limit() is False
        assert tracker.limit_triggered is False


# =============================================================================
# T005: Position Closing Tests
# =============================================================================


class TestPositionClosing:
    """Tests for closing positions when limit triggered."""

    def test_trigger_limit_closes_positions_when_configured(self, tracker, mock_strategy):
        """_trigger_limit should close positions if close_positions_on_limit=True."""
        # Mock open position
        position = MagicMock()
        position.side = PositionSide.LONG
        position.instrument_id = "BTCUSDT-PERP.BINANCE"
        position.quantity = Decimal("1.5")
        position.id = "POS-001"

        mock_strategy.cache.positions_open.return_value = [position]

        tracker._trigger_limit()

        # Should create close order
        mock_strategy.order_factory.market.assert_called_once()
        mock_strategy.submit_order.assert_called_once()

    def test_trigger_limit_creates_sell_order_for_long(self, tracker, mock_strategy):
        """Should create SELL order to close LONG position."""
        position = MagicMock()
        position.side = PositionSide.LONG
        position.instrument_id = "BTCUSDT-PERP.BINANCE"
        position.quantity = Decimal("1.5")
        position.id = "POS-001"

        mock_strategy.cache.positions_open.return_value = [position]

        tracker._trigger_limit()

        call_args = mock_strategy.order_factory.market.call_args
        assert call_args[1]["order_side"] == OrderSide.SELL

    def test_trigger_limit_creates_buy_order_for_short(self, tracker, mock_strategy):
        """Should create BUY order to close SHORT position."""
        position = MagicMock()
        position.side = PositionSide.SHORT
        position.instrument_id = "BTCUSDT-PERP.BINANCE"
        position.quantity = Decimal("1.5")
        position.id = "POS-001"

        mock_strategy.cache.positions_open.return_value = [position]

        tracker._trigger_limit()

        call_args = mock_strategy.order_factory.market.call_args
        assert call_args[1]["order_side"] == OrderSide.BUY

    def test_trigger_limit_sets_reduce_only(self, tracker, mock_strategy):
        """Close orders should have reduce_only=True."""
        position = MagicMock()
        position.side = PositionSide.LONG
        position.instrument_id = "BTCUSDT-PERP.BINANCE"
        position.quantity = Decimal("1.5")
        position.id = "POS-001"

        mock_strategy.cache.positions_open.return_value = [position]

        tracker._trigger_limit()

        call_args = mock_strategy.order_factory.market.call_args
        assert call_args[1]["reduce_only"] is True

    def test_trigger_limit_closes_multiple_positions(self, tracker, mock_strategy):
        """Should close all open positions."""
        position1 = MagicMock()
        position1.side = PositionSide.LONG
        position1.instrument_id = "BTCUSDT-PERP.BINANCE"
        position1.quantity = Decimal("1.5")
        position1.id = "POS-001"

        position2 = MagicMock()
        position2.side = PositionSide.SHORT
        position2.instrument_id = "ETHUSDT-PERP.BINANCE"
        position2.quantity = Decimal("5.0")
        position2.id = "POS-002"

        mock_strategy.cache.positions_open.return_value = [position1, position2]

        tracker._trigger_limit()

        assert mock_strategy.order_factory.market.call_count == 2
        assert mock_strategy.submit_order.call_count == 2

    def test_trigger_limit_no_close_when_configured(self, no_close_config, mock_strategy):
        """Should not close positions if close_positions_on_limit=False."""
        tracker = DailyPnLTracker(config=no_close_config, strategy=mock_strategy)

        position = MagicMock()
        position.side = PositionSide.LONG
        mock_strategy.cache.positions_open.return_value = [position]

        tracker._trigger_limit()

        mock_strategy.order_factory.market.assert_not_called()
        mock_strategy.submit_order.assert_not_called()

    def test_trigger_limit_handles_close_errors(self, tracker, mock_strategy, caplog):
        """Should log errors but continue closing other positions."""
        import logging
        caplog.set_level(logging.ERROR)

        position1 = MagicMock()
        position1.side = PositionSide.LONG
        position1.instrument_id = "BTCUSDT-PERP.BINANCE"
        position1.quantity = Decimal("1.5")
        position1.id = "POS-001"

        position2 = MagicMock()
        position2.side = PositionSide.SHORT
        position2.instrument_id = "ETHUSDT-PERP.BINANCE"
        position2.quantity = Decimal("5.0")
        position2.id = "POS-002"

        mock_strategy.cache.positions_open.return_value = [position1, position2]

        # First call raises error, second succeeds
        mock_strategy.order_factory.market.side_effect = [Exception("Order error"), MagicMock()]

        tracker._trigger_limit()

        assert "Failed to close position" in caplog.text
        # Second position should still be processed
        assert mock_strategy.order_factory.market.call_count == 2


# =============================================================================
# T006: Trading Permission Tests
# =============================================================================


class TestTradingPermission:
    """Tests for can_trade() method."""

    def test_can_trade_returns_true_initially(self, tracker):
        """can_trade should return True when limit not triggered."""
        assert tracker.can_trade() is True

    def test_can_trade_returns_false_after_limit(self, tracker):
        """can_trade should return False after limit triggered."""
        tracker._limit_triggered = True

        assert tracker.can_trade() is False

    def test_can_trade_after_limit_check(self, tracker):
        """can_trade should respect limit_triggered state."""
        tracker._daily_realized = Decimal("-1001")
        tracker.check_limit()

        assert tracker.can_trade() is False


# =============================================================================
# T007: Reset Tests
# =============================================================================


class TestReset:
    """Tests for daily reset functionality."""

    def test_reset_clears_realized_pnl(self, tracker):
        """reset should clear daily realized PnL."""
        tracker._daily_realized = Decimal("-500")

        tracker.reset()

        assert tracker.daily_realized == Decimal("0")

    def test_reset_clears_limit_triggered(self, tracker):
        """reset should clear limit_triggered flag."""
        tracker._limit_triggered = True

        tracker.reset()

        assert tracker.limit_triggered is False

    def test_reset_clears_warning_emitted(self, tracker):
        """reset should clear warning_emitted flag."""
        tracker._warning_emitted = True

        tracker.reset()

        assert tracker._warning_emitted is False

    def test_reset_updates_day_start(self, tracker, mock_strategy):
        """reset should update day_start to current time."""
        old_day_start = tracker.day_start

        # Advance clock
        mock_strategy.clock.utc_now.return_value = datetime(
            2024, 1, 16, 0, 0, 0, tzinfo=UTC
        )

        tracker.reset()

        assert tracker.day_start != old_day_start
        assert tracker.day_start == mock_strategy.clock.utc_now.return_value

    def test_reset_recalculates_starting_equity(self, tracker, mock_strategy):
        """reset should recalculate starting equity."""
        # Mock new balance
        money = MagicMock()
        money.__float__ = MagicMock(return_value=75000.0)
        mock_strategy.portfolio.balances.return_value = {
            Currency.from_str("USD"): money
        }

        tracker.reset()

        assert tracker._starting_equity == Decimal("75000")

    def test_reset_logs_info_message(self, tracker, caplog):
        """reset should log info message."""
        import logging
        caplog.set_level(logging.INFO)

        tracker.reset()

        assert "Daily PnL tracker reset" in caplog.text


# =============================================================================
# T008: Equity Calculation Tests
# =============================================================================


class TestEquityCalculation:
    """Tests for _calculate_total_equity method."""

    def test_calculate_equity_sums_all_balances(self, tracker, mock_strategy):
        """Should sum all balances across currencies."""
        usd = MagicMock()
        usd.__float__ = MagicMock(return_value=50000.0)

        btc = MagicMock()
        btc.__float__ = MagicMock(return_value=25000.0)

        mock_strategy.portfolio.balances.return_value = {
            Currency.from_str("USD"): usd,
            Currency.from_str("BTC"): btc,
        }

        equity = tracker._calculate_total_equity()

        assert equity == Decimal("75000")

    def test_calculate_equity_handles_none_balances(self, tracker, mock_strategy):
        """Should handle None balances in dict."""
        usd = MagicMock()
        usd.__float__ = MagicMock(return_value=50000.0)

        mock_strategy.portfolio.balances.return_value = {
            Currency.from_str("USD"): usd,
            Currency.from_str("BTC"): None,
        }

        equity = tracker._calculate_total_equity()

        assert equity == Decimal("50000")

    def test_calculate_equity_fallback_on_empty(self, tracker, mock_strategy):
        """Should use fallback value when balances empty."""
        mock_strategy.portfolio.balances.return_value = {}

        equity = tracker._calculate_total_equity()

        # Fallback: 50x daily_loss_limit = 50 * 1000 = 50000
        assert equity == Decimal("50000")

    def test_calculate_equity_fallback_on_none(self, tracker, mock_strategy):
        """Should use fallback value when balances None."""
        mock_strategy.portfolio.balances.return_value = None

        equity = tracker._calculate_total_equity()

        assert equity == Decimal("50000")

    def test_calculate_equity_fallback_on_error(self, tracker, mock_strategy):
        """Should use fallback value on AttributeError."""
        mock_strategy.portfolio.balances.side_effect = AttributeError

        equity = tracker._calculate_total_equity()

        assert equity == Decimal("50000")

    def test_calculate_equity_fallback_on_zero(self, tracker, mock_strategy):
        """Should use fallback when total is zero or negative."""
        money = MagicMock()
        money.__float__ = MagicMock(return_value=0.0)

        mock_strategy.portfolio.balances.return_value = {
            Currency.from_str("USD"): money
        }

        equity = tracker._calculate_total_equity()

        assert equity == Decimal("50000")


# =============================================================================
# T009: Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_very_small_pnl_values(self, tracker):
        """Should handle very small PnL values (precision)."""
        event = MagicMock()
        pnl = MagicMock()
        pnl.__float__ = MagicMock(return_value=0.00001)
        event.realized_pnl = pnl

        tracker.handle_event(event)

        assert tracker.daily_realized > Decimal("0")

    def test_very_large_negative_pnl(self, tracker):
        """Should handle very large negative PnL."""
        event = MagicMock()
        pnl = MagicMock()
        pnl.__float__ = MagicMock(return_value=-1_000_000_000.0)
        event.realized_pnl = pnl

        tracker.handle_event(event)

        assert tracker.daily_realized == Decimal("-1000000000")

    def test_accumulated_pnl_precision(self, tracker):
        """Should maintain precision with many small accumulations."""
        for _ in range(1000):
            event = MagicMock()
            pnl = MagicMock()
            pnl.__float__ = MagicMock(return_value=0.001)
            event.realized_pnl = pnl

            tracker.handle_event(event)

        # 1000 * 0.001 = 1.0
        assert tracker.daily_realized == Decimal("1")

    def test_mixed_positive_negative_pnl(self, tracker):
        """Should correctly handle mix of positive and negative PnL."""
        events = [
            (100.0, "profit"),
            (-50.0, "loss"),
            (75.0, "profit"),
            (-25.0, "loss"),
        ]

        for pnl_val, _ in events:
            event = MagicMock()
            pnl = MagicMock()
            pnl.__float__ = MagicMock(return_value=pnl_val)
            event.realized_pnl = pnl

            tracker.handle_event(event)

        # 100 - 50 + 75 - 25 = 100
        assert tracker.daily_realized == Decimal("100")

    def test_limit_check_with_zero_total_pnl(self, tracker):
        """Should handle zero total PnL correctly."""
        tracker._daily_realized = Decimal("0")

        assert tracker.check_limit() is False

    def test_warning_threshold_edge_case(self, tracker):
        """Should trigger warning at exact threshold value."""
        import pytest

        # Exactly 50% of 1000 = -500
        tracker._daily_realized = Decimal("-500")

        with pytest.raises(AssertionError) if False else nullcontext():
            result = tracker.check_limit()
            assert result is False
            assert tracker._warning_emitted is True

    def test_limit_exactly_at_boundary(self, tracker):
        """Should trigger at exact limit boundary (-1000)."""
        tracker._daily_realized = Decimal("-1000")

        result = tracker.check_limit()

        assert result is True
        assert tracker.limit_triggered is True

    def test_no_positions_to_close(self, tracker, mock_strategy):
        """Should handle case with no open positions gracefully."""
        mock_strategy.cache.positions_open.return_value = []

        tracker._trigger_limit()  # Should not raise exception

        mock_strategy.order_factory.market.assert_not_called()

    def test_timezone_aware_datetime(self, tracker):
        """Day start should be timezone-aware UTC datetime."""
        assert tracker.day_start.tzinfo == UTC

    def test_concurrent_event_processing(self, tracker):
        """Should handle rapid successive events (simulated)."""
        events = []
        for i in range(100):
            event = MagicMock()
            pnl = MagicMock()
            pnl.__float__ = MagicMock(return_value=10.0 if i % 2 == 0 else -5.0)
            event.realized_pnl = pnl
            events.append(event)

        for event in events:
            tracker.handle_event(event)

        # 50 * 10 + 50 * (-5) = 500 - 250 = 250
        expected = Decimal("250")
        assert tracker.daily_realized == expected


# =============================================================================
# T010: Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_full_trading_day_cycle(self, tracker, mock_strategy):
        """Test complete cycle: trades -> limit check -> reset."""
        # Morning trades (profitable)
        event1 = MagicMock()
        pnl1 = MagicMock()
        pnl1.__float__ = MagicMock(return_value=200.0)
        event1.realized_pnl = pnl1
        tracker.handle_event(event1)

        assert tracker.daily_realized == Decimal("200")
        assert tracker.can_trade() is True

        # Afternoon trades (losing)
        event2 = MagicMock()
        pnl2 = MagicMock()
        pnl2.__float__ = MagicMock(return_value=-600.0)
        event2.realized_pnl = pnl2
        tracker.handle_event(event2)

        assert tracker.daily_realized == Decimal("-400")

        # Check limit (not exceeded yet)
        assert tracker.check_limit() is False

        # More losses (trigger limit)
        event3 = MagicMock()
        pnl3 = MagicMock()
        pnl3.__float__ = MagicMock(return_value=-650.0)
        event3.realized_pnl = pnl3
        tracker.handle_event(event3)

        assert tracker.check_limit() is True
        assert tracker.can_trade() is False

        # Next day reset
        tracker.reset()
        assert tracker.daily_realized == Decimal("0")
        assert tracker.can_trade() is True

    def test_warning_then_limit_progression(self, tracker, caplog):
        """Test progression from warning to limit trigger."""
        import logging
        caplog.set_level(logging.WARNING)

        # First loss - trigger warning
        tracker._daily_realized = Decimal("-500")
        assert tracker.check_limit() is False
        assert "Daily PnL warning" in caplog.text

        caplog.clear()

        # Second loss - trigger limit
        tracker._daily_realized = Decimal("-1001")
        assert tracker.check_limit() is True
        assert "Daily loss limit triggered" in caplog.text

    def test_multiple_resets_maintain_state(self, tracker):
        """Test that multiple resets properly maintain state."""
        for day in range(5):
            # Add some PnL
            tracker._daily_realized = Decimal(f"{100 * day}")

            # Reset for next day
            tracker.reset()

            # Verify clean state
            assert tracker.daily_realized == Decimal("0")
            assert tracker.limit_triggered is False
            assert tracker._warning_emitted is False


# =============================================================================
# Helper Context Manager
# =============================================================================


from contextlib import contextmanager


@contextmanager
def nullcontext():
    """Null context manager for Python 3.6 compatibility."""
    yield
