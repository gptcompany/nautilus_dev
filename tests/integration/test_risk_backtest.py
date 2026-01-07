"""
Integration tests for Risk Management with BacktestNode.

Tests cover:
- T033: Stop-loss execution on price drop
- T034: Stop-loss with gap-through scenario
- T035: Position limit rejection in backtest
- T036: Multiple positions with separate stops
"""

from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from nautilus_trader.model.currencies import USDT
from nautilus_trader.model.enums import OrderSide, PositionSide
from nautilus_trader.model.identifiers import (
    ClientOrderId,
    InstrumentId,
    PositionId,
    StrategyId,
    TraderId,
)
from nautilus_trader.model.objects import Money, Price, Quantity

from risk import RiskConfig, RiskManager

# --- Fixtures ---


@pytest.fixture
def instrument_id() -> InstrumentId:
    """Test instrument ID."""
    return InstrumentId.from_str("BTC/USDT.BINANCE")


@pytest.fixture
def mock_strategy(instrument_id: InstrumentId) -> MagicMock:
    """Create mock strategy with required attributes."""
    strategy = MagicMock()
    strategy.trader_id = TraderId("TESTER-001")
    strategy.strategy_id = StrategyId("RiskManagedStrategy-001")

    # Mock order factory
    strategy.order_factory = MagicMock()
    mock_stop_order = MagicMock()
    mock_stop_order.client_order_id = ClientOrderId("O-STOP-001")
    strategy.order_factory.stop_market = MagicMock(return_value=mock_stop_order)

    # Mock cache
    strategy.cache = MagicMock()
    strategy.cache.positions_open = MagicMock(return_value=[])
    strategy.cache.position = MagicMock(return_value=None)

    # Mock portfolio
    strategy.portfolio = MagicMock()
    strategy.portfolio.net_exposure = MagicMock(return_value=Money(0, USDT))

    # Mock instrument
    mock_instrument = MagicMock()
    mock_instrument.make_price = lambda p: Price.from_str(str(round(float(p), 2)))
    mock_instrument.make_qty = lambda q: Quantity.from_str(str(q))
    strategy.cache.instrument = MagicMock(return_value=mock_instrument)

    return strategy


def create_mock_position(
    instrument_id: InstrumentId,
    side: PositionSide,
    entry_price: str,
    quantity: str,
    position_id: str = "P-001",
) -> MagicMock:
    """Create mock position."""
    from nautilus_trader.model.position import Position

    position = MagicMock(spec=Position)
    position.id = PositionId(position_id)
    position.instrument_id = instrument_id
    position.side = side
    position.avg_px_open = float(entry_price)
    position.quantity = Quantity.from_str(quantity)
    position.signed_qty = float(quantity) if side == PositionSide.LONG else -float(quantity)
    return position


def create_position_opened_event(position: MagicMock) -> MagicMock:
    """Create mock PositionOpened event."""
    from nautilus_trader.model.events import PositionOpened

    event = MagicMock(spec=PositionOpened)
    event.position_id = position.id
    event.instrument_id = position.instrument_id
    event.position_side = position.side
    event.avg_px_open = position.avg_px_open
    event.quantity = position.quantity
    return event


def create_position_closed_event(position: MagicMock) -> MagicMock:
    """Create mock PositionClosed event."""
    from nautilus_trader.model.events import PositionClosed

    event = MagicMock(spec=PositionClosed)
    event.position_id = position.id
    event.instrument_id = position.instrument_id
    return event


# --- T033: Stop-loss execution on price drop ---


class TestStopLossExecution:
    """T033: Integration test for stop-loss execution on price drop."""

    def test_stop_loss_created_at_correct_price_for_long(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """
        Scenario: LONG position opened at $50,000 with 2% stop-loss.

        Expected: Stop order created at $49,000 (50000 * 0.98).
        """
        config = RiskConfig(stop_loss_pct=Decimal("0.02"))
        manager = RiskManager(config=config, strategy=mock_strategy)

        position = create_mock_position(
            instrument_id=instrument_id,
            side=PositionSide.LONG,
            entry_price="50000.00",
            quantity="0.1",
        )
        mock_strategy.cache.position.return_value = position

        event = create_position_opened_event(position)
        manager.handle_event(event)

        # Verify stop order created
        mock_strategy.order_factory.stop_market.assert_called_once()
        call_kwargs = mock_strategy.order_factory.stop_market.call_args[1]

        # Check stop price is 2% below entry
        trigger_price = call_kwargs["trigger_price"]
        assert float(trigger_price) == pytest.approx(49000.0, rel=0.01)

        # Check order side is SELL (to close LONG)
        assert call_kwargs["order_side"] == OrderSide.SELL

        # Check reduce_only is True
        assert call_kwargs["reduce_only"] is True

    def test_stop_loss_created_at_correct_price_for_short(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """
        Scenario: SHORT position opened at $50,000 with 2% stop-loss.

        Expected: Stop order created at $51,000 (50000 * 1.02).
        """
        config = RiskConfig(stop_loss_pct=Decimal("0.02"))
        manager = RiskManager(config=config, strategy=mock_strategy)

        position = create_mock_position(
            instrument_id=instrument_id,
            side=PositionSide.SHORT,
            entry_price="50000.00",
            quantity="0.1",
        )
        mock_strategy.cache.position.return_value = position

        event = create_position_opened_event(position)
        manager.handle_event(event)

        call_kwargs = mock_strategy.order_factory.stop_market.call_args[1]

        # Check stop price is 2% above entry for SHORT
        trigger_price = call_kwargs["trigger_price"]
        assert float(trigger_price) == pytest.approx(51000.0, rel=0.01)

        # Check order side is BUY (to close SHORT)
        assert call_kwargs["order_side"] == OrderSide.BUY


# --- T034: Stop-loss with gap-through scenario ---


class TestGapThroughScenario:
    """T034: Integration test for stop-loss with gap-through scenario."""

    def test_stop_order_quantity_matches_position_size(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """
        Scenario: Position of 0.5 BTC opened.

        Expected: Stop order quantity is 0.5 BTC (full position).
        This ensures gap-through fills close the entire position.
        """
        config = RiskConfig(stop_loss_pct=Decimal("0.02"))
        manager = RiskManager(config=config, strategy=mock_strategy)

        position = create_mock_position(
            instrument_id=instrument_id,
            side=PositionSide.LONG,
            entry_price="50000.00",
            quantity="0.5",
        )
        mock_strategy.cache.position.return_value = position

        event = create_position_opened_event(position)
        manager.handle_event(event)

        call_kwargs = mock_strategy.order_factory.stop_market.call_args[1]
        assert call_kwargs["quantity"] == position.quantity

    def test_stop_order_uses_stop_market_for_gap_protection(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """
        Scenario: Default config uses STOP_MARKET.

        Expected: Stop order is STOP_MARKET (fills at market in gap).
        """
        config = RiskConfig(stop_loss_pct=Decimal("0.02"))
        manager = RiskManager(config=config, strategy=mock_strategy)

        position = create_mock_position(
            instrument_id=instrument_id,
            side=PositionSide.LONG,
            entry_price="50000.00",
            quantity="0.1",
        )
        mock_strategy.cache.position.return_value = position

        event = create_position_opened_event(position)
        manager.handle_event(event)

        # STOP_MARKET is the default, so stop_market should be called
        mock_strategy.order_factory.stop_market.assert_called_once()
        # stop_limit should NOT be called
        mock_strategy.order_factory.stop_limit.assert_not_called()


# --- T035: Position limit rejection in backtest ---


class TestPositionLimitRejection:
    """T035: Integration test for position limit rejection."""

    def test_order_rejected_when_exceeds_per_instrument_limit(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """
        Scenario: Max position 0.5 BTC, current 0.3 BTC, trying to buy 0.3 BTC.

        Expected: Order rejected (0.3 + 0.3 = 0.6 > 0.5 limit).
        """
        config = RiskConfig(max_position_size={"BTC/USDT.BINANCE": Decimal("0.5")})
        manager = RiskManager(config=config, strategy=mock_strategy)

        # Current position: 0.3 BTC
        current_position = create_mock_position(
            instrument_id=instrument_id,
            side=PositionSide.LONG,
            entry_price="50000.00",
            quantity="0.3",
        )
        mock_strategy.cache.positions_open.return_value = [current_position]

        # New order: 0.3 BTC
        order = MagicMock()
        order.instrument_id = instrument_id
        order.quantity = Quantity.from_str("0.3")
        order.side = OrderSide.BUY

        result = manager.validate_order(order)

        assert result is False

    def test_order_allowed_when_within_per_instrument_limit(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """
        Scenario: Max position 0.5 BTC, current 0.3 BTC, trying to buy 0.1 BTC.

        Expected: Order allowed (0.3 + 0.1 = 0.4 < 0.5 limit).
        """
        config = RiskConfig(max_position_size={"BTC/USDT.BINANCE": Decimal("0.5")})
        manager = RiskManager(config=config, strategy=mock_strategy)

        current_position = create_mock_position(
            instrument_id=instrument_id,
            side=PositionSide.LONG,
            entry_price="50000.00",
            quantity="0.3",
        )
        mock_strategy.cache.positions_open.return_value = [current_position]

        order = MagicMock()
        order.instrument_id = instrument_id
        order.quantity = Quantity.from_str("0.1")
        order.side = OrderSide.BUY

        result = manager.validate_order(order)

        assert result is True

    def test_sell_orders_always_allowed_for_risk_reduction(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """
        Scenario: Max position 0.5 BTC, current 0.5 BTC (at limit), selling 0.2 BTC.

        Expected: SELL order allowed (reduces risk, doesn't increase position).
        """
        config = RiskConfig(max_position_size={"BTC/USDT.BINANCE": Decimal("0.5")})
        manager = RiskManager(config=config, strategy=mock_strategy)

        current_position = create_mock_position(
            instrument_id=instrument_id,
            side=PositionSide.LONG,
            entry_price="50000.00",
            quantity="0.5",
        )
        mock_strategy.cache.positions_open.return_value = [current_position]

        order = MagicMock()
        order.instrument_id = instrument_id
        order.quantity = Quantity.from_str("0.2")
        order.side = OrderSide.SELL

        result = manager.validate_order(order)

        assert result is True


# --- T036: Multiple positions with separate stops ---


class TestMultiplePositionsSeparateStops:
    """T036: Integration test for multiple positions with separate stops."""

    def test_each_position_gets_own_stop(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """
        Scenario: Open two separate positions.

        Expected: Each position has its own stop order in active_stops.
        """
        config = RiskConfig(stop_loss_pct=Decimal("0.02"))
        manager = RiskManager(config=config, strategy=mock_strategy)

        # First position
        position1 = create_mock_position(
            instrument_id=instrument_id,
            side=PositionSide.LONG,
            entry_price="50000.00",
            quantity="0.1",
            position_id="P-001",
        )

        # Second position (different position ID)
        position2 = create_mock_position(
            instrument_id=instrument_id,
            side=PositionSide.LONG,
            entry_price="51000.00",
            quantity="0.2",
            position_id="P-002",
        )

        # Set up unique stop order IDs
        stop_order_1 = MagicMock()
        stop_order_1.client_order_id = ClientOrderId("O-STOP-001")

        stop_order_2 = MagicMock()
        stop_order_2.client_order_id = ClientOrderId("O-STOP-002")

        mock_strategy.order_factory.stop_market.side_effect = [
            stop_order_1,
            stop_order_2,
        ]

        # Open first position
        mock_strategy.cache.position.return_value = position1
        event1 = create_position_opened_event(position1)
        manager.handle_event(event1)

        # Open second position
        mock_strategy.cache.position.return_value = position2
        event2 = create_position_opened_event(position2)
        manager.handle_event(event2)

        # Verify both positions have stops
        assert position1.id in manager.active_stops
        assert position2.id in manager.active_stops
        assert manager.active_stops[position1.id] == stop_order_1.client_order_id
        assert manager.active_stops[position2.id] == stop_order_2.client_order_id

    def test_closing_one_position_only_cancels_its_stop(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """
        Scenario: Two positions open, close one.

        Expected: Only the closed position's stop is cancelled.
        """
        config = RiskConfig(stop_loss_pct=Decimal("0.02"))
        manager = RiskManager(config=config, strategy=mock_strategy)

        position1 = create_mock_position(
            instrument_id=instrument_id,
            side=PositionSide.LONG,
            entry_price="50000.00",
            quantity="0.1",
            position_id="P-001",
        )

        position2 = create_mock_position(
            instrument_id=instrument_id,
            side=PositionSide.LONG,
            entry_price="51000.00",
            quantity="0.2",
            position_id="P-002",
        )

        stop_order_1 = MagicMock()
        stop_order_1.client_order_id = ClientOrderId("O-STOP-001")

        stop_order_2 = MagicMock()
        stop_order_2.client_order_id = ClientOrderId("O-STOP-002")

        mock_strategy.order_factory.stop_market.side_effect = [
            stop_order_1,
            stop_order_2,
        ]

        # Open both positions
        mock_strategy.cache.position.return_value = position1
        manager.handle_event(create_position_opened_event(position1))

        mock_strategy.cache.position.return_value = position2
        manager.handle_event(create_position_opened_event(position2))

        # Close first position
        close_event = create_position_closed_event(position1)
        manager.handle_event(close_event)

        # Position 1 stop should be cancelled and removed
        assert position1.id not in manager.active_stops

        # Position 2 stop should still be active
        assert position2.id in manager.active_stops
        assert manager.active_stops[position2.id] == stop_order_2.client_order_id

        # Cancel should have been called with position 1's stop
        mock_strategy.cancel_order.assert_called_once_with(stop_order_1.client_order_id)


# --- Edge Cases (T039-T040) ---


class TestEdgeCases:
    """T039-T040: Edge case handling tests."""

    def test_position_closed_before_stop_created_no_error(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """
        T039: Position closed event received when no stop exists.

        Expected: No error, gracefully handled.
        """
        config = RiskConfig(stop_loss_pct=Decimal("0.02"))
        manager = RiskManager(config=config, strategy=mock_strategy)

        position = create_mock_position(
            instrument_id=instrument_id,
            side=PositionSide.LONG,
            entry_price="50000.00",
            quantity="0.1",
        )

        # Close without opening (simulates race condition)
        close_event = create_position_closed_event(position)

        # Should not raise
        manager.handle_event(close_event)

        # Should not have tried to cancel anything
        mock_strategy.cancel_order.assert_not_called()

    def test_stop_disabled_no_stop_created(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """
        Scenario: stop_loss_enabled=False.

        Expected: No stop order created on position open.
        """
        config = RiskConfig(stop_loss_enabled=False)
        manager = RiskManager(config=config, strategy=mock_strategy)

        position = create_mock_position(
            instrument_id=instrument_id,
            side=PositionSide.LONG,
            entry_price="50000.00",
            quantity="0.1",
        )
        mock_strategy.cache.position.return_value = position

        event = create_position_opened_event(position)
        manager.handle_event(event)

        # No stop order should be created
        mock_strategy.order_factory.stop_market.assert_not_called()
        assert len(manager.active_stops) == 0


# --- T039-T042: Daily Loss Limit Integration Tests (Spec 013) ---


class TestDailyLossLimitSingleStrategy:
    """T039: Integration test for daily loss limit with single strategy."""

    def test_daily_limit_triggers_on_cumulative_loss(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """
        Scenario: Daily limit $1000, three losing trades totaling $1200.

        Expected: can_trade() returns False after cumulative loss exceeds limit.
        """
        from risk import DailyLossConfig, DailyPnLTracker, RiskConfig, RiskManager

        daily_config = DailyLossConfig(daily_loss_limit=Decimal("1000"))
        daily_tracker = DailyPnLTracker(config=daily_config, strategy=mock_strategy)

        config = RiskConfig(stop_loss_enabled=False)
        manager = RiskManager(
            config=config,
            strategy=mock_strategy,
            daily_tracker=daily_tracker,
        )

        # Three losing trades
        losses = [-400.0, -500.0, -300.0]  # Total: -$1200

        for i, loss in enumerate(losses):
            position = create_mock_position(
                instrument_id=instrument_id,
                side=PositionSide.LONG,
                entry_price="50000.00",
                quantity="0.1",
                position_id=f"P-{i}",
            )
            close_event = create_position_closed_event(position)
            close_event.realized_pnl = Money(loss, USDT)

            manager.handle_event(close_event)

        # Check limit
        daily_tracker.check_limit()

        # Should have triggered
        assert daily_tracker.limit_triggered is True
        assert daily_tracker.can_trade() is False

        # New orders should be rejected
        order = MagicMock()
        order.instrument_id = instrument_id
        order.quantity = Quantity.from_str("0.1")
        order.side = OrderSide.BUY

        assert manager.validate_order(order) is False

    def test_daily_limit_not_triggered_with_mixed_results(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """
        Scenario: Daily limit $1000, wins and losses netting to -$500.

        Expected: can_trade() returns True (under limit).
        """
        from risk import DailyLossConfig, DailyPnLTracker, RiskConfig, RiskManager

        daily_config = DailyLossConfig(daily_loss_limit=Decimal("1000"))
        daily_tracker = DailyPnLTracker(config=daily_config, strategy=mock_strategy)

        config = RiskConfig(stop_loss_enabled=False)
        manager = RiskManager(
            config=config,
            strategy=mock_strategy,
            daily_tracker=daily_tracker,
        )

        # Mixed trades: net -$500
        pnls = [200.0, -400.0, 100.0, -400.0]  # Total: -$500

        for i, pnl in enumerate(pnls):
            position = create_mock_position(
                instrument_id=instrument_id,
                side=PositionSide.LONG,
                entry_price="50000.00",
                quantity="0.1",
                position_id=f"P-{i}",
            )
            close_event = create_position_closed_event(position)
            close_event.realized_pnl = Money(pnl, USDT)

            manager.handle_event(close_event)

        daily_tracker.check_limit()

        # Should NOT have triggered
        assert daily_tracker.limit_triggered is False
        assert daily_tracker.can_trade() is True


class TestDailyLossLimitMultiPosition:
    """T040: Integration test for daily loss limit with multiple positions."""

    def test_positions_closed_on_limit_trigger(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """
        Scenario: Daily limit $100 with close_positions_on_limit=True,
                  two open positions when limit triggered.

        Expected: Both positions receive close orders.
        """
        from risk import DailyLossConfig, DailyPnLTracker, RiskConfig, RiskManager

        daily_config = DailyLossConfig(
            daily_loss_limit=Decimal("100"),
            close_positions_on_limit=True,
        )
        daily_tracker = DailyPnLTracker(config=daily_config, strategy=mock_strategy)

        config = RiskConfig(stop_loss_enabled=False)
        manager = RiskManager(
            config=config,
            strategy=mock_strategy,
            daily_tracker=daily_tracker,
        )

        # Two open positions
        open_positions = [
            create_mock_position(
                instrument_id=instrument_id,
                side=PositionSide.LONG,
                entry_price="50000.00",
                quantity="0.1",
                position_id="P-001",
            ),
            create_mock_position(
                instrument_id=instrument_id,
                side=PositionSide.SHORT,
                entry_price="51000.00",
                quantity="0.2",
                position_id="P-002",
            ),
        ]
        mock_strategy.cache.positions_open.return_value = open_positions

        # Trigger daily limit with big loss
        position = create_mock_position(
            instrument_id=instrument_id,
            side=PositionSide.LONG,
            entry_price="50000.00",
            quantity="0.1",
            position_id="P-CLOSED",
        )
        close_event = create_position_closed_event(position)
        close_event.realized_pnl = Money(-150.0, USDT)

        manager.handle_event(close_event)
        daily_tracker.check_limit()

        # Should have submitted close orders for both positions
        assert mock_strategy.submit_order.call_count == 2


class TestDailyLossLimitReset:
    """T041: Integration test for daily loss limit reset at midnight."""

    def test_reset_clears_triggered_state(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """
        Scenario: Daily limit triggered, then reset() called.

        Expected: can_trade() returns True after reset.
        """
        from risk import DailyLossConfig, DailyPnLTracker, RiskConfig, RiskManager

        daily_config = DailyLossConfig(daily_loss_limit=Decimal("100"))
        daily_tracker = DailyPnLTracker(config=daily_config, strategy=mock_strategy)

        config = RiskConfig(stop_loss_enabled=False)
        manager = RiskManager(
            config=config,
            strategy=mock_strategy,
            daily_tracker=daily_tracker,
        )

        # Trigger limit
        position = create_mock_position(
            instrument_id=instrument_id,
            side=PositionSide.LONG,
            entry_price="50000.00",
            quantity="0.1",
        )
        close_event = create_position_closed_event(position)
        close_event.realized_pnl = Money(-150.0, USDT)

        manager.handle_event(close_event)
        daily_tracker.check_limit()

        assert daily_tracker.can_trade() is False

        # Reset (simulates midnight)
        daily_tracker.reset()

        assert daily_tracker.can_trade() is True
        assert daily_tracker.daily_realized == Decimal("0")
        assert daily_tracker.limit_triggered is False


class TestMidnightEdgeCases:
    """T042: Edge cases for positions spanning midnight."""

    def test_unrealized_pnl_not_reset(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """
        Scenario: Position open at midnight with unrealized loss.

        Expected: After reset, unrealized PnL still counts toward limit.
        """
        from risk import DailyLossConfig, DailyPnLTracker

        # Mock portfolio with unrealized loss
        mock_strategy.portfolio.unrealized_pnls.return_value = Money(-500.0, USDT)

        daily_config = DailyLossConfig(daily_loss_limit=Decimal("400"))
        daily_tracker = DailyPnLTracker(config=daily_config, strategy=mock_strategy)

        # Reset (simulates midnight)
        daily_tracker.reset()

        # Realized is 0, but unrealized is -500
        assert daily_tracker.daily_realized == Decimal("0")
        assert daily_tracker.daily_unrealized == Decimal("-500")
        assert daily_tracker.total_daily_pnl == Decimal("-500")

        # Check limit - should trigger because unrealized exceeds limit
        daily_tracker.check_limit()
        assert daily_tracker.limit_triggered is True
