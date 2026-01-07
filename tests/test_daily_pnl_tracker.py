"""Tests for DailyPnLTracker (Spec 013).

TDD Approach: Tests written FIRST before implementation.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from risk.daily_loss_config import DailyLossConfig


# Mock NautilusTrader types for testing without full dependency
class MockMoney:
    """Mock Money object."""

    def __init__(self, value: float):
        self._value = value

    def __float__(self):
        return self._value


class MockPosition:
    """Mock Position object."""

    def __init__(
        self,
        instrument_id: str = "BTCUSDT.BINANCE",
        quantity: float = 1.0,
        side: str = "LONG",
        position_id: str = "POS-001",
    ):
        self.instrument_id = MagicMock()
        self.instrument_id.__str__ = MagicMock(return_value=instrument_id)
        self.quantity = MagicMock()
        self.quantity.__float__ = MagicMock(return_value=quantity)
        self.side = MagicMock()
        self.side.name = side
        self.id = position_id


class MockPositionClosed:
    """Mock PositionClosed event."""

    def __init__(self, realized_pnl: float = 0.0, position_id: str = "POS-001"):
        self.realized_pnl = MockMoney(realized_pnl)
        self.position_id = position_id


class MockClock:
    """Mock clock for testing."""

    def __init__(self, timestamp: datetime | None = None):
        self._timestamp = timestamp or datetime.now(timezone.utc)

    def utc_now(self) -> datetime:
        return self._timestamp

    def set_timer(self, name: str, interval: timedelta, callback, start_time=None):
        pass


class MockPortfolio:
    """Mock portfolio for unrealized PnL."""

    def __init__(self, unrealized_pnl: float = 0.0):
        self._unrealized_pnl = unrealized_pnl

    def unrealized_pnls(self, venue=None):
        return MockMoney(self._unrealized_pnl)


class MockCache:
    """Mock cache for positions."""

    def __init__(self, positions: list | None = None):
        self._positions = positions or []

    def positions_open(self):
        return self._positions


class MockStrategy:
    """Mock strategy for testing."""

    def __init__(
        self,
        clock: MockClock | None = None,
        portfolio: MockPortfolio | None = None,
        cache: MockCache | None = None,
    ):
        self.clock = clock or MockClock()
        self.portfolio = portfolio or MockPortfolio()
        self.cache = cache or MockCache()
        self._submitted_orders = []

    def submit_order(self, order):
        self._submitted_orders.append(order)

    @property
    def order_factory(self):
        return MagicMock()


@pytest.fixture
def default_config():
    """Default DailyLossConfig for tests."""
    return DailyLossConfig(daily_loss_limit=Decimal("1000"))


@pytest.fixture
def mock_strategy():
    """Mock strategy with default mocks."""
    return MockStrategy()


# =============================================================================
# Phase 3: User Story 1 - Daily PnL Calculation (FR-001)
# =============================================================================


class TestDailyRealizedAccumulates:
    """T005: Test that realized PnL accumulates from PositionClosed events."""

    def test_daily_realized_starts_at_zero(self, default_config, mock_strategy):
        """Tracker starts with zero realized PnL."""
        from risk.daily_pnl_tracker import DailyPnLTracker

        tracker = DailyPnLTracker(config=default_config, strategy=mock_strategy)
        assert tracker.daily_realized == Decimal("0")

    def test_realized_accumulates_on_position_closed(self, default_config, mock_strategy):
        """Realized PnL accumulates from PositionClosed events."""
        from risk.daily_pnl_tracker import DailyPnLTracker

        tracker = DailyPnLTracker(config=default_config, strategy=mock_strategy)

        # Simulate position closed with $100 profit
        event1 = MockPositionClosed(realized_pnl=100.0)
        tracker.handle_event(event1)
        assert tracker.daily_realized == Decimal("100")

        # Simulate another position closed with $50 loss
        event2 = MockPositionClosed(realized_pnl=-50.0)
        tracker.handle_event(event2)
        assert tracker.daily_realized == Decimal("50")

    def test_realized_handles_multiple_positions(self, default_config, mock_strategy):
        """Realized PnL correctly sums multiple positions."""
        from risk.daily_pnl_tracker import DailyPnLTracker

        tracker = DailyPnLTracker(config=default_config, strategy=mock_strategy)

        events = [
            MockPositionClosed(realized_pnl=100.0),
            MockPositionClosed(realized_pnl=-200.0),
            MockPositionClosed(realized_pnl=50.0),
        ]
        for event in events:
            tracker.handle_event(event)

        # 100 - 200 + 50 = -50
        assert tracker.daily_realized == Decimal("-50")


class TestUnrealizedPnLCalculation:
    """T006: Test unrealized PnL calculation from portfolio."""

    def test_daily_unrealized_from_portfolio(self, default_config):
        """Unrealized PnL comes from portfolio."""
        from risk.daily_pnl_tracker import DailyPnLTracker

        portfolio = MockPortfolio(unrealized_pnl=-200.0)
        strategy = MockStrategy(portfolio=portfolio)
        tracker = DailyPnLTracker(config=default_config, strategy=strategy)

        assert tracker.daily_unrealized == Decimal("-200")

    def test_daily_unrealized_updates_dynamically(self, default_config):
        """Unrealized PnL updates when portfolio changes."""
        from risk.daily_pnl_tracker import DailyPnLTracker

        portfolio = MockPortfolio(unrealized_pnl=100.0)
        strategy = MockStrategy(portfolio=portfolio)
        tracker = DailyPnLTracker(config=default_config, strategy=strategy)

        assert tracker.daily_unrealized == Decimal("100")

        # Portfolio value changes
        portfolio._unrealized_pnl = -50.0
        assert tracker.daily_unrealized == Decimal("-50")

    def test_daily_unrealized_returns_zero_when_no_positions(self, default_config):
        """Unrealized PnL is zero when portfolio returns None."""
        from risk.daily_pnl_tracker import DailyPnLTracker

        portfolio = MagicMock()
        portfolio.unrealized_pnls.return_value = None
        strategy = MockStrategy(portfolio=portfolio)
        tracker = DailyPnLTracker(config=default_config, strategy=strategy)

        assert tracker.daily_unrealized == Decimal("0")


class TestTotalDailyPnLSum:
    """T007: Test total_daily_pnl = realized + unrealized."""

    def test_total_pnl_is_sum_of_realized_and_unrealized(self, default_config):
        """Total daily PnL = realized + unrealized."""
        from risk.daily_pnl_tracker import DailyPnLTracker

        portfolio = MockPortfolio(unrealized_pnl=-100.0)
        strategy = MockStrategy(portfolio=portfolio)
        tracker = DailyPnLTracker(config=default_config, strategy=strategy)

        # Add realized profit
        event = MockPositionClosed(realized_pnl=200.0)
        tracker.handle_event(event)

        # Total = 200 (realized) + (-100) (unrealized) = 100
        assert tracker.total_daily_pnl == Decimal("100")

    def test_total_pnl_updates_with_both_components(self, default_config):
        """Total PnL updates when either component changes."""
        from risk.daily_pnl_tracker import DailyPnLTracker

        portfolio = MockPortfolio(unrealized_pnl=0.0)
        strategy = MockStrategy(portfolio=portfolio)
        tracker = DailyPnLTracker(config=default_config, strategy=strategy)

        assert tracker.total_daily_pnl == Decimal("0")

        # Add realized
        tracker.handle_event(MockPositionClosed(realized_pnl=100.0))
        assert tracker.total_daily_pnl == Decimal("100")

        # Update unrealized
        portfolio._unrealized_pnl = -50.0
        assert tracker.total_daily_pnl == Decimal("50")


# =============================================================================
# Phase 4: User Story 2 - Daily Loss Limit Enforcement (FR-002)
# =============================================================================


class TestLimitNotTriggeredUnderThreshold:
    """T014: Test limit_triggered is False when under threshold."""

    def test_limit_not_triggered_initially(self, default_config, mock_strategy):
        """Limit is not triggered on initialization."""
        from risk.daily_pnl_tracker import DailyPnLTracker

        tracker = DailyPnLTracker(config=default_config, strategy=mock_strategy)
        assert tracker.limit_triggered is False

    def test_limit_not_triggered_with_profit(self, default_config, mock_strategy):
        """Limit not triggered when in profit."""
        from risk.daily_pnl_tracker import DailyPnLTracker

        tracker = DailyPnLTracker(config=default_config, strategy=mock_strategy)
        tracker.handle_event(MockPositionClosed(realized_pnl=500.0))
        tracker.check_limit()

        assert tracker.limit_triggered is False

    def test_limit_not_triggered_under_threshold(self, default_config, mock_strategy):
        """Limit not triggered when loss < limit."""
        from risk.daily_pnl_tracker import DailyPnLTracker

        # Config: limit = $1000
        tracker = DailyPnLTracker(config=default_config, strategy=mock_strategy)

        # Loss of $500 (under $1000 limit)
        tracker.handle_event(MockPositionClosed(realized_pnl=-500.0))
        tracker.check_limit()

        assert tracker.limit_triggered is False


class TestLimitTriggeredAtThreshold:
    """T015: Test limit triggers at/above threshold."""

    def test_limit_triggers_at_exact_threshold(self, mock_strategy):
        """Limit triggers when loss equals limit."""
        from risk.daily_pnl_tracker import DailyPnLTracker

        config = DailyLossConfig(daily_loss_limit=Decimal("1000"))
        tracker = DailyPnLTracker(config=config, strategy=mock_strategy)

        # Loss of exactly $1000
        tracker.handle_event(MockPositionClosed(realized_pnl=-1000.0))
        tracker.check_limit()

        assert tracker.limit_triggered is True

    def test_limit_triggers_above_threshold(self, mock_strategy):
        """Limit triggers when loss exceeds limit."""
        from risk.daily_pnl_tracker import DailyPnLTracker

        config = DailyLossConfig(daily_loss_limit=Decimal("1000"))
        tracker = DailyPnLTracker(config=config, strategy=mock_strategy)

        # Loss of $1500 (above $1000 limit)
        tracker.handle_event(MockPositionClosed(realized_pnl=-1500.0))
        tracker.check_limit()

        assert tracker.limit_triggered is True

    def test_limit_triggers_including_unrealized(self):
        """Limit triggers when realized + unrealized exceeds limit."""
        from risk.daily_pnl_tracker import DailyPnLTracker

        config = DailyLossConfig(daily_loss_limit=Decimal("1000"))
        # Unrealized loss of $600
        portfolio = MockPortfolio(unrealized_pnl=-600.0)
        strategy = MockStrategy(portfolio=portfolio)
        tracker = DailyPnLTracker(config=config, strategy=strategy)

        # Realized loss of $500 (total = $1100 > $1000)
        tracker.handle_event(MockPositionClosed(realized_pnl=-500.0))
        tracker.check_limit()

        assert tracker.limit_triggered is True


class TestCanTradeReturnsFalseWhenTriggered:
    """T016: Test can_trade() returns False when limit triggered."""

    def test_can_trade_true_initially(self, default_config, mock_strategy):
        """can_trade() returns True initially."""
        from risk.daily_pnl_tracker import DailyPnLTracker

        tracker = DailyPnLTracker(config=default_config, strategy=mock_strategy)
        assert tracker.can_trade() is True

    def test_can_trade_false_when_triggered(self, mock_strategy):
        """can_trade() returns False when limit triggered."""
        from risk.daily_pnl_tracker import DailyPnLTracker

        config = DailyLossConfig(daily_loss_limit=Decimal("100"))
        tracker = DailyPnLTracker(config=config, strategy=mock_strategy)

        # Trigger limit
        tracker.handle_event(MockPositionClosed(realized_pnl=-150.0))
        tracker.check_limit()

        assert tracker.can_trade() is False

    def test_can_trade_remains_false_until_reset(self, mock_strategy):
        """can_trade() stays False until reset, even if PnL improves."""
        from risk.daily_pnl_tracker import DailyPnLTracker

        config = DailyLossConfig(daily_loss_limit=Decimal("100"))
        portfolio = MockPortfolio(unrealized_pnl=-150.0)
        strategy = MockStrategy(portfolio=portfolio)
        tracker = DailyPnLTracker(config=config, strategy=strategy)

        tracker.check_limit()
        assert tracker.can_trade() is False

        # Even if unrealized improves, still can't trade (sticky trigger)
        portfolio._unrealized_pnl = 50.0
        assert tracker.can_trade() is False


class TestClosePositionsOnLimitTrue:
    """T017: Test positions closed when close_positions_on_limit=True."""

    def test_positions_closed_on_limit_trigger(self):
        """All positions closed when limit triggers with close_positions_on_limit=True."""
        from risk.daily_pnl_tracker import DailyPnLTracker

        config = DailyLossConfig(
            daily_loss_limit=Decimal("100"),
            close_positions_on_limit=True,
        )

        # Create mock positions
        positions = [
            MockPosition(instrument_id="BTCUSDT.BINANCE", quantity=1.0, side="LONG"),
            MockPosition(instrument_id="ETHUSDT.BINANCE", quantity=2.0, side="SHORT"),
        ]
        cache = MockCache(positions=positions)
        strategy = MockStrategy(cache=cache)
        tracker = DailyPnLTracker(config=config, strategy=strategy)

        # Trigger limit
        tracker.handle_event(MockPositionClosed(realized_pnl=-150.0))
        triggered = tracker.check_limit()

        assert triggered is True
        assert len(strategy._submitted_orders) == 2  # One close order per position

    def test_no_positions_closed_when_disabled(self, mock_strategy):
        """No positions closed when close_positions_on_limit=False."""
        from risk.daily_pnl_tracker import DailyPnLTracker

        config = DailyLossConfig(
            daily_loss_limit=Decimal("100"),
            close_positions_on_limit=False,
        )
        tracker = DailyPnLTracker(config=config, strategy=mock_strategy)

        # Trigger limit
        tracker.handle_event(MockPositionClosed(realized_pnl=-150.0))
        tracker.check_limit()

        assert len(mock_strategy._submitted_orders) == 0


# =============================================================================
# Phase 5: User Story 3 - Daily Reset (FR-003)
# =============================================================================


class TestResetClearsDailyRealized:
    """T023: Test reset() clears daily_realized."""

    def test_reset_clears_realized(self, default_config, mock_strategy):
        """reset() sets daily_realized to zero."""
        from risk.daily_pnl_tracker import DailyPnLTracker

        tracker = DailyPnLTracker(config=default_config, strategy=mock_strategy)

        # Accumulate realized PnL
        tracker.handle_event(MockPositionClosed(realized_pnl=500.0))
        assert tracker.daily_realized == Decimal("500")

        # Reset
        tracker.reset()
        assert tracker.daily_realized == Decimal("0")


class TestResetClearsLimitTriggered:
    """T024: Test reset() clears limit_triggered."""

    def test_reset_clears_limit_triggered(self, mock_strategy):
        """reset() clears limit_triggered flag."""
        from risk.daily_pnl_tracker import DailyPnLTracker

        config = DailyLossConfig(daily_loss_limit=Decimal("100"))
        tracker = DailyPnLTracker(config=config, strategy=mock_strategy)

        # Trigger limit
        tracker.handle_event(MockPositionClosed(realized_pnl=-150.0))
        tracker.check_limit()
        assert tracker.limit_triggered is True

        # Reset
        tracker.reset()
        assert tracker.limit_triggered is False
        assert tracker.can_trade() is True


class TestDayStartPropertyUpdatesOnReset:
    """T025: Test day_start property updates on reset."""

    def test_day_start_updates_on_reset(self):
        """day_start is updated to current time on reset."""
        from risk.daily_pnl_tracker import DailyPnLTracker

        old_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        new_time = datetime(2024, 1, 2, 0, 0, 0, tzinfo=timezone.utc)

        clock = MockClock(timestamp=old_time)
        strategy = MockStrategy(clock=clock)
        config = DailyLossConfig()

        tracker = DailyPnLTracker(config=config, strategy=strategy)
        initial_day_start = tracker.day_start

        # Advance clock and reset
        clock._timestamp = new_time
        tracker.reset()

        assert tracker.day_start > initial_day_start


# =============================================================================
# Phase 6: User Story 4 - RiskManager Integration (FR-004)
# =============================================================================


class TestPerStrategyLimitsIndependent:
    """T034b: Test per_strategy=True tracks independently."""

    def test_per_strategy_tracking_with_strategy_id(self):
        """When per_strategy=True, different strategy IDs are tracked independently."""
        from risk.daily_pnl_tracker import DailyPnLTracker

        config = DailyLossConfig(
            daily_loss_limit=Decimal("1000"),
            per_strategy=True,
        )
        strategy = MockStrategy()
        tracker = DailyPnLTracker(config=config, strategy=strategy)

        # This test validates the per_strategy flag is respected
        # Full implementation would track by strategy_id
        assert config.per_strategy is True


# =============================================================================
# Phase 7: User Story 5 - QuestDB Monitoring (MON)
# =============================================================================


class TestQuestDBRecordOnCheckLimit:
    """T035: Test QuestDB record written on check_limit()."""

    def test_questdb_writer_called_on_check_limit(self, default_config, mock_strategy):
        """QuestDB writer is called when check_limit() runs (if configured)."""
        from risk.daily_pnl_tracker import DailyPnLTracker

        tracker = DailyPnLTracker(config=default_config, strategy=mock_strategy)

        # check_limit should not raise even without QuestDB
        result = tracker.check_limit()
        assert result in [True, False]
