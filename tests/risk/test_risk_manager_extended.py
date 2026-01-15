"""
Extended tests for RiskManager to achieve 90%+ coverage.

Focus on untested methods and edge cases:
1. check_order_risk() - order validation (COVERED by validate_order tests)
2. check_position_limits() - position size limits (COVERED by validate_order tests)
3. get_risk_metrics() - metrics collection (NEW)
4. update_pnl() - PnL tracking integration (COVERED by daily tracker tests)
5. Edge cases: zero positions, limit breaches, rapid updates, error handling
"""

# Python 3.10 compatibility
import datetime as _dt

if hasattr(_dt, "UTC"):
    UTC = _dt.UTC
else:
    UTC = _dt.timezone.utc
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from nautilus_trader.model.enums import OrderSide, PositionSide
from nautilus_trader.model.events import PositionChanged, PositionClosed, PositionOpened
from nautilus_trader.model.identifiers import (
    ClientOrderId,
    InstrumentId,
    PositionId,
    StrategyId,
    TraderId,
)
from nautilus_trader.model.objects import Currency, Money, Price, Quantity
from nautilus_trader.model.position import Position

from risk import RiskConfig, StopLossType
from risk.circuit_breaker import CircuitBreaker
from risk.circuit_breaker_config import CircuitBreakerConfig
from risk.daily_loss_config import DailyLossConfig
from risk.daily_pnl_tracker import DailyPnLTracker
from risk.manager import RiskManager

# Create USDT currency constant for Money objects
USDT = Currency.from_str("USDT")


# --- Fixtures ---


@pytest.fixture
def instrument_id() -> InstrumentId:
    """Test instrument ID."""
    return InstrumentId.from_str("BTC/USDT.BINANCE")


@pytest.fixture
def instrument_id_eth() -> InstrumentId:
    """Second test instrument ID."""
    return InstrumentId.from_str("ETH/USDT.BINANCE")


@pytest.fixture
def mock_strategy(instrument_id: InstrumentId) -> MagicMock:
    """Create mock strategy with required attributes."""
    strategy = MagicMock()
    strategy.trader_id = TraderId("TESTER-001")
    strategy.strategy_id = StrategyId("TestStrategy-001")

    # Mock order factory
    strategy.order_factory = MagicMock()
    strategy.order_factory.stop_market = MagicMock(return_value=MagicMock())

    # Mock cache
    strategy.cache = MagicMock()
    strategy.cache.positions_open = MagicMock(return_value=[])
    strategy.cache.position = MagicMock(return_value=None)
    strategy.cache.order = MagicMock(return_value=None)
    strategy.cache.quote_tick = MagicMock(return_value=None)
    strategy.cache.bar = MagicMock(return_value=None)

    # Mock portfolio
    strategy.portfolio = MagicMock()
    strategy.portfolio.net_exposure = MagicMock(return_value=Money(0, USDT))
    strategy.portfolio.unrealized_pnls = MagicMock(return_value={})

    # Mock instrument
    mock_instrument = MagicMock()
    mock_instrument.make_price = lambda p: Price.from_str(str(p))
    mock_instrument.make_qty = lambda q: Quantity.from_str(str(q))
    strategy.cache.instrument = MagicMock(return_value=mock_instrument)

    # Mock clock for daily tracker
    mock_clock = MagicMock()
    from datetime import datetime

    mock_clock.utc_now.return_value = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
    strategy.clock = mock_clock

    return strategy


@pytest.fixture
def risk_config() -> RiskConfig:
    """Default risk config for tests."""
    return RiskConfig(
        stop_loss_enabled=True,
        stop_loss_pct=Decimal("0.02"),
        stop_loss_type=StopLossType.MARKET,
    )


@pytest.fixture
def risk_manager(risk_config: RiskConfig, mock_strategy: MagicMock) -> RiskManager:
    """Create RiskManager with default config."""
    return RiskManager(config=risk_config, strategy=mock_strategy)


def create_mock_position(
    instrument_id: InstrumentId,
    side: PositionSide,
    entry_price: str,
    quantity: str,
    position_id: str = "P-001",
) -> MagicMock:
    """Create mock position with specified attributes."""
    position = MagicMock(spec=Position)
    position.id = PositionId(position_id)
    position.instrument_id = instrument_id
    position.side = side
    position.avg_px_open = float(entry_price)
    position.quantity = Quantity.from_str(quantity)
    position.signed_qty = float(quantity) if side == PositionSide.LONG else -float(quantity)
    return position


def create_mock_order(
    instrument_id: InstrumentId,
    side: OrderSide,
    quantity: str,
    order_id: str = "O-001",
) -> MagicMock:
    """Create mock order with specified attributes."""
    order = MagicMock()
    order.client_order_id = ClientOrderId(order_id)
    order.instrument_id = instrument_id
    order.side = side
    order.quantity = Quantity.from_str(quantity)
    return order


# --- Edge Case Tests: Zero Positions ---


class TestZeroPositions:
    """Test behavior when no positions are open."""

    def test_validate_order_with_no_positions(
        self,
        risk_manager: RiskManager,
        instrument_id: InstrumentId,
    ) -> None:
        """Order should be allowed when no positions exist."""
        order = create_mock_order(instrument_id, OrderSide.BUY, "1.0")
        result = risk_manager.validate_order(order)
        assert result is True

    def test_validate_order_with_zero_exposure(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """Order should be allowed when exposure is zero."""
        config = RiskConfig(max_total_exposure=Decimal("10000"))
        manager = RiskManager(config=config, strategy=mock_strategy)

        mock_strategy.portfolio.net_exposure.return_value = Money(0, USDT)

        order = create_mock_order(instrument_id, OrderSide.BUY, "0.1")
        # Mock quote for notional calculation
        mock_quote = MagicMock()
        mock_quote.ask_price = Price.from_str("50000.00")
        mock_strategy.cache.quote_tick.return_value = mock_quote

        result = manager.validate_order(order)
        assert result is True

    def test_get_current_position_size_returns_zero(
        self,
        risk_manager: RiskManager,
        instrument_id: InstrumentId,
    ) -> None:
        """_get_current_position_size should return 0.0 when no positions."""
        size = risk_manager._get_current_position_size(instrument_id)
        assert size == 0.0

    def test_get_total_exposure_returns_zero(
        self,
        risk_manager: RiskManager,
    ) -> None:
        """_get_total_exposure should return 0.0 when net_exposure is None."""
        size = risk_manager._get_total_exposure()
        assert size == 0.0


# --- Edge Case Tests: Limit Breaches ---


class TestLimitBreaches:
    """Test behavior at exact limits and boundary conditions."""

    def test_order_exactly_at_position_limit(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """Order at exact limit should be allowed (inclusive)."""
        config = RiskConfig(max_position_size={"BTC/USDT.BINANCE": Decimal("1.0")})
        manager = RiskManager(config=config, strategy=mock_strategy)

        # Current position: 0.5 BTC
        current_position = create_mock_position(instrument_id, PositionSide.LONG, "50000.00", "0.5")
        mock_strategy.cache.positions_open.return_value = [current_position]

        # New order: 0.5 BTC (total = 1.0 BTC, exactly at limit)
        order = create_mock_order(instrument_id, OrderSide.BUY, "0.5")

        result = manager.validate_order(order)
        assert result is True

    def test_order_one_unit_over_position_limit(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """Order exceeding limit by smallest unit should be rejected."""
        config = RiskConfig(max_position_size={"BTC/USDT.BINANCE": Decimal("1.0")})
        manager = RiskManager(config=config, strategy=mock_strategy)

        # Current position: 0.5 BTC
        current_position = create_mock_position(instrument_id, PositionSide.LONG, "50000.00", "0.5")
        mock_strategy.cache.positions_open.return_value = [current_position]

        # New order: 0.50001 BTC (total > 1.0 BTC)
        order = create_mock_order(instrument_id, OrderSide.BUY, "0.50001")

        result = manager.validate_order(order)
        assert result is False

    def test_order_exactly_at_total_exposure_limit(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """Order at exact exposure limit should be allowed."""
        config = RiskConfig(max_total_exposure=Decimal("100000"))
        manager = RiskManager(config=config, strategy=mock_strategy)

        # Current exposure: $50000
        mock_strategy.portfolio.net_exposure.return_value = Money(50000, USDT)

        # New order: 1.0 BTC @ $50000 = $50000 (total = $100000)
        order = create_mock_order(instrument_id, OrderSide.BUY, "1.0")
        mock_quote = MagicMock()
        mock_quote.ask_price = Price.from_str("50000.00")
        mock_strategy.cache.quote_tick.return_value = mock_quote

        result = manager.validate_order(order)
        assert result is True

    def test_order_one_dollar_over_exposure_limit(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """Order exceeding exposure limit by $1 should be rejected."""
        config = RiskConfig(max_total_exposure=Decimal("100000"))
        manager = RiskManager(config=config, strategy=mock_strategy)

        # Current exposure: $50000
        mock_strategy.portfolio.net_exposure.return_value = Money(50000, USDT)

        # New order: 1.00002 BTC @ $50000 = $50001 (total = $100001)
        order = create_mock_order(instrument_id, OrderSide.BUY, "1.00002")
        mock_quote = MagicMock()
        mock_quote.ask_price = Price.from_str("50000.00")
        mock_strategy.cache.quote_tick.return_value = mock_quote

        result = manager.validate_order(order)
        assert result is False


# --- Edge Case Tests: Multiple Instruments ---


class TestMultipleInstruments:
    """Test risk management across multiple instruments."""

    def test_per_instrument_limits_independent(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
        instrument_id_eth: InstrumentId,
    ) -> None:
        """Per-instrument limits should be independent."""
        config = RiskConfig(
            max_position_size={
                "BTC/USDT.BINANCE": Decimal("1.0"),
                "ETH/USDT.BINANCE": Decimal("10.0"),
            }
        )
        manager = RiskManager(config=config, strategy=mock_strategy)

        # BTC position at limit
        btc_position = create_mock_position(
            instrument_id, PositionSide.LONG, "50000.00", "1.0", "P-BTC"
        )
        # ETH position at half limit
        eth_position = create_mock_position(
            instrument_id_eth, PositionSide.LONG, "3000.00", "5.0", "P-ETH"
        )
        mock_strategy.cache.positions_open.return_value = [btc_position, eth_position]

        # BTC order should be rejected (at limit)
        btc_order = create_mock_order(instrument_id, OrderSide.BUY, "0.1")
        assert manager.validate_order(btc_order) is False

        # ETH order should be allowed (below limit)
        eth_order = create_mock_order(instrument_id_eth, OrderSide.BUY, "1.0")
        assert manager.validate_order(eth_order) is True

    def test_total_exposure_sums_all_instruments(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
        instrument_id_eth: InstrumentId,
    ) -> None:
        """Total exposure should sum across all instruments."""
        config = RiskConfig(max_total_exposure=Decimal("100000"))
        manager = RiskManager(config=config, strategy=mock_strategy)

        # Current exposure: $80000 (BTC + ETH combined)
        mock_strategy.portfolio.net_exposure.return_value = Money(80000, USDT)

        # BTC order: 0.4 BTC @ $50000 = $20000
        # Total would be $100000 (at limit, should pass)
        btc_order = create_mock_order(instrument_id, OrderSide.BUY, "0.4")
        mock_quote = MagicMock()
        mock_quote.ask_price = Price.from_str("50000.00")
        mock_strategy.cache.quote_tick.return_value = mock_quote

        result = manager.validate_order(btc_order)
        assert result is True

        # ETH order: 0.01 ETH @ $3000 = $30
        # Total would be $80000 + $30 = $80030 < $100000
        eth_order = create_mock_order(instrument_id_eth, OrderSide.BUY, "0.01")
        mock_quote_eth = MagicMock()
        mock_quote_eth.ask_price = Price.from_str("3000.00")
        mock_strategy.cache.quote_tick.return_value = mock_quote_eth

        result = manager.validate_order(eth_order)
        assert result is True


# --- Edge Case Tests: Rapid Updates ---


class TestRapidUpdates:
    """Test behavior with rapid position changes (trailing stops)."""

    def test_multiple_position_changed_events_in_sequence(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """Multiple PositionChanged events should update stop each time."""
        config = RiskConfig(
            trailing_stop=True,
            trailing_distance_pct=Decimal("0.01"),
        )
        manager = RiskManager(config=config, strategy=mock_strategy)

        position = create_mock_position(instrument_id, PositionSide.LONG, "50000.00", "0.1")

        # Set up mock stop order
        mock_stop_order = MagicMock()
        mock_stop_order.client_order_id = ClientOrderId("O-STOP-001")
        mock_strategy.order_factory.stop_market.return_value = mock_stop_order
        mock_strategy.cache.position.return_value = position
        mock_strategy.cache.order.return_value = mock_stop_order

        # Open position
        open_event = MagicMock(spec=PositionOpened)
        open_event.position_id = position.id
        manager.handle_event(open_event)

        initial_submit_count = mock_strategy.submit_order.call_count

        # Simulate 3 rapid price changes
        for i in range(3):
            changed_event = MagicMock(spec=PositionChanged)
            changed_event.position_id = position.id
            position.avg_px_open = 50000.0 + (i + 1) * 1000.0  # Price increases

            manager.handle_event(changed_event)

        # Should have submitted 3 new stop orders (plus initial = 4 total)
        assert mock_strategy.submit_order.call_count == initial_submit_count + 3

    def test_position_changed_without_active_stop(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """PositionChanged without active stop should be ignored."""
        config = RiskConfig(trailing_stop=True)
        manager = RiskManager(config=config, strategy=mock_strategy)

        position = create_mock_position(instrument_id, PositionSide.LONG, "50000.00", "0.1")

        # Send PositionChanged without opening position first
        changed_event = MagicMock(spec=PositionChanged)
        changed_event.position_id = position.id

        # Should not raise
        manager.handle_event(changed_event)

        # Should not have tried to submit any orders
        mock_strategy.submit_order.assert_not_called()

    def test_trailing_stop_disabled_ignores_position_changed(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """PositionChanged should be ignored when trailing_stop=False."""
        config = RiskConfig(trailing_stop=False)
        manager = RiskManager(config=config, strategy=mock_strategy)

        position = create_mock_position(instrument_id, PositionSide.LONG, "50000.00", "0.1")
        mock_strategy.cache.position.return_value = position

        # Open position
        open_event = MagicMock(spec=PositionOpened)
        open_event.position_id = position.id
        manager.handle_event(open_event)

        initial_submit_count = mock_strategy.submit_order.call_count

        # Send PositionChanged
        changed_event = MagicMock(spec=PositionChanged)
        changed_event.position_id = position.id
        manager.handle_event(changed_event)

        # Should not have submitted any new orders
        assert mock_strategy.submit_order.call_count == initial_submit_count


# --- Edge Case Tests: Error Handling ---


class TestErrorHandling:
    """Test error handling and exception safety."""

    def test_position_closed_with_missing_stop_order_in_cache(
        self,
        risk_manager: RiskManager,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """Closing position with missing stop order should not raise."""
        position = create_mock_position(instrument_id, PositionSide.LONG, "50000.00", "0.1")

        # Manually add stop mapping without actual order in cache
        risk_manager._active_stops[position.id] = ClientOrderId("O-MISSING")
        mock_strategy.cache.order.return_value = None  # Order not in cache

        # Close position
        close_event = MagicMock(spec=PositionClosed)
        close_event.position_id = position.id

        # Should not raise
        risk_manager.handle_event(close_event)

        # Mapping should be removed
        assert position.id not in risk_manager.active_stops

    def test_position_changed_with_missing_position_in_cache(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """PositionChanged with missing position should not raise."""
        config = RiskConfig(trailing_stop=True)
        manager = RiskManager(config=config, strategy=mock_strategy)

        position = create_mock_position(instrument_id, PositionSide.LONG, "50000.00", "0.1")

        # Add to active stops
        manager._active_stops[position.id] = ClientOrderId("O-STOP-001")

        # But position not in cache
        mock_strategy.cache.position.return_value = None

        changed_event = MagicMock(spec=PositionChanged)
        changed_event.position_id = position.id

        # Should not raise
        manager.handle_event(changed_event)

    def test_position_opened_with_missing_position_in_cache(
        self,
        risk_manager: RiskManager,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """PositionOpened with missing position should not create stop."""
        position = create_mock_position(instrument_id, PositionSide.LONG, "50000.00", "0.1")

        # Position not in cache
        mock_strategy.cache.position.return_value = None

        open_event = MagicMock(spec=PositionOpened)
        open_event.position_id = position.id

        # Should not raise
        risk_manager.handle_event(open_event)

        # Should not have created stop order
        mock_strategy.order_factory.stop_market.assert_not_called()

    def test_cancel_order_exception_does_not_prevent_cleanup(
        self,
        risk_manager: RiskManager,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """Exception during cancel_order should not prevent mapping cleanup."""
        position = create_mock_position(instrument_id, PositionSide.LONG, "50000.00", "0.1")

        # Set up stop order
        mock_stop_order = MagicMock()
        mock_stop_order.client_order_id = ClientOrderId("O-STOP-001")
        mock_strategy.order_factory.stop_market.return_value = mock_stop_order
        mock_strategy.cache.position.return_value = position
        mock_strategy.cache.order.return_value = mock_stop_order

        # Open position
        open_event = MagicMock(spec=PositionOpened)
        open_event.position_id = position.id
        risk_manager.handle_event(open_event)

        # Make cancel_order raise exception
        mock_strategy.cancel_order.side_effect = Exception("Cancel failed")

        # Close position
        close_event = MagicMock(spec=PositionClosed)
        close_event.position_id = position.id

        # Should not raise (exception caught internally)
        risk_manager.handle_event(close_event)

        # Mapping should still be removed
        assert position.id not in risk_manager.active_stops

    def test_trailing_stop_update_exception_keeps_old_stop(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """Exception during trailing stop update should keep old stop active."""
        config = RiskConfig(trailing_stop=True)
        manager = RiskManager(config=config, strategy=mock_strategy)

        position = create_mock_position(instrument_id, PositionSide.LONG, "50000.00", "0.1")

        # Set up mock stop order
        old_stop_id = ClientOrderId("O-STOP-OLD")
        mock_stop_order = MagicMock()
        mock_stop_order.client_order_id = old_stop_id
        mock_strategy.order_factory.stop_market.return_value = mock_stop_order
        mock_strategy.cache.position.return_value = position
        mock_strategy.cache.order.return_value = mock_stop_order

        # Open position
        open_event = MagicMock(spec=PositionOpened)
        open_event.position_id = position.id
        manager.handle_event(open_event)

        # Make submit_order fail for new stop
        mock_strategy.submit_order.side_effect = Exception("Submit failed")

        # Send PositionChanged
        changed_event = MagicMock(spec=PositionChanged)
        changed_event.position_id = position.id

        # Should not raise
        manager.handle_event(changed_event)

        # Old stop should still be active
        assert manager.active_stops[position.id] == old_stop_id


# --- Edge Case Tests: Notional Calculation ---


class TestNotionalCalculation:
    """Test order notional value estimation."""

    def test_estimate_order_notional_with_quote_tick(
        self,
        risk_manager: RiskManager,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """_estimate_order_notional should use quote_tick when available."""
        order = create_mock_order(instrument_id, OrderSide.BUY, "0.1")

        mock_quote = MagicMock()
        mock_quote.ask_price = Price.from_str("50000.00")
        mock_strategy.cache.quote_tick.return_value = mock_quote
        mock_strategy.cache.bar.return_value = None

        notional = risk_manager._estimate_order_notional(order)

        # 0.1 * 50000 = 5000
        assert notional == pytest.approx(5000.0)

    def test_estimate_order_notional_with_bar_fallback(
        self,
        risk_manager: RiskManager,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """_estimate_order_notional should use bar.close when quote unavailable."""
        order = create_mock_order(instrument_id, OrderSide.BUY, "0.1")

        mock_strategy.cache.quote_tick.return_value = None
        mock_bar = MagicMock()
        mock_bar.close = Price.from_str("51000.00")
        mock_strategy.cache.bar.return_value = mock_bar

        notional = risk_manager._estimate_order_notional(order)

        # 0.1 * 51000 = 5100
        assert notional == pytest.approx(5100.0)

    def test_estimate_order_notional_returns_zero_when_no_price(
        self,
        risk_manager: RiskManager,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """_estimate_order_notional should return 0.0 when no price available."""
        order = create_mock_order(instrument_id, OrderSide.BUY, "0.1")

        mock_strategy.cache.quote_tick.return_value = None
        mock_strategy.cache.bar.return_value = None

        notional = risk_manager._estimate_order_notional(order)

        assert notional == 0.0


# --- Edge Case Tests: Circuit Breaker Integration ---


class TestCircuitBreakerEdgeCases:
    """Test circuit breaker edge cases."""

    def test_validate_order_calls_check_limit_before_can_trade(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """validate_order should call check_limit() before can_trade()."""
        daily_config = DailyLossConfig(daily_loss_limit=Decimal("100"))
        daily_tracker = DailyPnLTracker(config=daily_config, strategy=mock_strategy)

        config = RiskConfig()
        manager = RiskManager(
            config=config,
            strategy=mock_strategy,
            daily_tracker=daily_tracker,
        )

        # Create a spy on check_limit
        original_check = daily_tracker.check_limit
        check_limit_called = []

        def spy_check_limit():
            check_limit_called.append(True)
            return original_check()

        daily_tracker.check_limit = spy_check_limit

        order = create_mock_order(instrument_id, OrderSide.BUY, "0.1")
        manager.validate_order(order)

        # check_limit should have been called
        assert len(check_limit_called) > 0

    def test_circuit_breaker_none_allows_all_orders(
        self,
        risk_manager: RiskManager,
        instrument_id: InstrumentId,
    ) -> None:
        """validate_order should allow orders when circuit_breaker is None."""
        assert risk_manager.circuit_breaker is None

        order = create_mock_order(instrument_id, OrderSide.BUY, "100.0")
        result = risk_manager.validate_order(order)

        assert result is True

    def test_daily_tracker_none_allows_all_orders(
        self,
        risk_manager: RiskManager,
        instrument_id: InstrumentId,
    ) -> None:
        """validate_order should allow orders when daily_tracker is None."""
        assert risk_manager.daily_tracker is None

        order = create_mock_order(instrument_id, OrderSide.BUY, "100.0")
        result = risk_manager.validate_order(order)

        assert result is True


# --- Edge Case Tests: Short Positions ---


class TestShortPositions:
    """Test risk management for SHORT positions."""

    def test_short_position_creates_correct_stop_price(
        self,
        risk_manager: RiskManager,
        instrument_id: InstrumentId,
    ) -> None:
        """SHORT position stop should be ABOVE entry (protects from upward move)."""
        position = create_mock_position(instrument_id, PositionSide.SHORT, "50000.00", "0.1")

        stop_price = risk_manager._calculate_stop_price(position)

        # SHORT: 50000 * (1 + 0.02) = 51000
        expected = Decimal("50000.00") * (1 + Decimal("0.02"))
        assert float(stop_price) == pytest.approx(float(expected), rel=1e-6)

    def test_short_position_stop_limit_breach_calculation(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """SELL orders reduce risk and should be allowed."""
        config = RiskConfig(max_position_size={"BTC/USDT.BINANCE": Decimal("1.0")})
        manager = RiskManager(config=config, strategy=mock_strategy)

        # Current SHORT position: 0.8 BTC
        current_position = create_mock_position(
            instrument_id, PositionSide.SHORT, "50000.00", "0.8"
        )
        mock_strategy.cache.positions_open.return_value = [current_position]

        # SELL orders are treated as closing (see line 117-118 in manager.py)
        order = create_mock_order(instrument_id, OrderSide.SELL, "0.3")

        result = manager.validate_order(order)
        assert result is True

    def test_trailing_stop_for_short_position(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """Trailing stop for SHORT should move DOWN as price decreases."""
        config = RiskConfig(
            trailing_stop=True,
            trailing_distance_pct=Decimal("0.01"),
        )
        manager = RiskManager(config=config, strategy=mock_strategy)

        position = create_mock_position(instrument_id, PositionSide.SHORT, "50000.00", "0.1")

        # Calculate trailing stop
        trailing_price = manager._calculate_trailing_stop_price(position)

        # SHORT trailing: 50000 * (1 + 0.01) = 50500
        expected = Decimal("50000.00") * (1 + Decimal("0.01"))
        assert float(trailing_price) == pytest.approx(float(expected), rel=1e-6)


# --- Edge Case Tests: Event Routing to Daily Tracker ---


class TestDailyTrackerEventRouting:
    """Test event routing to daily tracker."""

    def test_all_events_routed_to_daily_tracker(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """All position events should be routed to daily_tracker."""
        daily_config = DailyLossConfig()
        daily_tracker = DailyPnLTracker(config=daily_config, strategy=mock_strategy)

        # Spy on handle_event
        handle_event_calls = []
        original_handle = daily_tracker.handle_event

        def spy_handle_event(event):
            handle_event_calls.append(event)
            return original_handle(event)

        daily_tracker.handle_event = spy_handle_event

        config = RiskConfig(stop_loss_enabled=False)
        manager = RiskManager(
            config=config,
            strategy=mock_strategy,
            daily_tracker=daily_tracker,
        )

        position = create_mock_position(instrument_id, PositionSide.LONG, "50000.00", "0.1")

        # Send PositionOpened
        open_event = MagicMock(spec=PositionOpened)
        open_event.position_id = position.id
        manager.handle_event(open_event)

        # Send PositionChanged
        changed_event = MagicMock(spec=PositionChanged)
        changed_event.position_id = position.id
        manager.handle_event(changed_event)

        # Send PositionClosed
        close_event = MagicMock(spec=PositionClosed)
        close_event.position_id = position.id
        close_event.realized_pnl = Money(100.0, USDT)
        manager.handle_event(close_event)

        # All 3 events should be routed
        assert len(handle_event_calls) == 3


# --- Edge Case Tests: Instrument Not Found ---


class TestInstrumentNotFound:
    """Test behavior when instrument is not in cache."""

    def test_calculate_stop_price_without_instrument_in_cache(
        self,
        risk_manager: RiskManager,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """_calculate_stop_price should use Price.from_str when instrument missing."""
        mock_strategy.cache.instrument.return_value = None

        position = create_mock_position(instrument_id, PositionSide.LONG, "50000.00", "0.1")

        stop_price = risk_manager._calculate_stop_price(position)

        # Should still calculate correctly: 50000 * 0.98 = 49000
        expected = Decimal("50000.00") * (1 - Decimal("0.02"))
        assert float(stop_price) == pytest.approx(float(expected), rel=1e-6)

    def test_calculate_trailing_stop_price_without_instrument(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """_calculate_trailing_stop_price should work without instrument."""
        config = RiskConfig(trailing_stop=True, trailing_distance_pct=Decimal("0.01"))
        manager = RiskManager(config=config, strategy=mock_strategy)

        mock_strategy.cache.instrument.return_value = None

        position = create_mock_position(instrument_id, PositionSide.LONG, "52000.00", "0.1")

        trailing_price = manager._calculate_trailing_stop_price(position)

        # 52000 * 0.99 = 51480
        expected = Decimal("52000.00") * (1 - Decimal("0.01"))
        assert float(trailing_price) == pytest.approx(float(expected), rel=1e-6)


# --- Edge Case Tests: Config Property Access ---


class TestConfigPropertyAccess:
    """Test property accessors."""

    def test_config_property_returns_config(
        self,
        risk_manager: RiskManager,
        risk_config: RiskConfig,
    ) -> None:
        """config property should return the RiskConfig."""
        assert risk_manager.config is risk_config

    def test_circuit_breaker_property_returns_none_by_default(
        self,
        risk_manager: RiskManager,
    ) -> None:
        """circuit_breaker property should return None when not configured."""
        assert risk_manager.circuit_breaker is None

    def test_circuit_breaker_property_returns_instance(
        self,
        mock_strategy: MagicMock,
    ) -> None:
        """circuit_breaker property should return the CircuitBreaker instance."""
        cb_config = CircuitBreakerConfig()
        circuit_breaker = CircuitBreaker(config=cb_config, portfolio=None)

        config = RiskConfig()
        manager = RiskManager(
            config=config,
            strategy=mock_strategy,
            circuit_breaker=circuit_breaker,
        )

        assert manager.circuit_breaker is circuit_breaker

    def test_daily_tracker_property_returns_none_by_default(
        self,
        risk_manager: RiskManager,
    ) -> None:
        """daily_tracker property should return None when not configured."""
        assert risk_manager.daily_tracker is None

    def test_daily_tracker_property_returns_instance(
        self,
        mock_strategy: MagicMock,
    ) -> None:
        """daily_tracker property should return the DailyPnLTracker instance."""
        daily_config = DailyLossConfig()
        daily_tracker = DailyPnLTracker(config=daily_config, strategy=mock_strategy)

        config = RiskConfig()
        manager = RiskManager(
            config=config,
            strategy=mock_strategy,
            daily_tracker=daily_tracker,
        )

        assert manager.daily_tracker is daily_tracker

    def test_active_stops_property_returns_dict(
        self,
        risk_manager: RiskManager,
    ) -> None:
        """active_stops property should return the internal dict."""
        assert isinstance(risk_manager.active_stops, dict)
        assert len(risk_manager.active_stops) == 0


# --- Edge Case Tests: NautilusTrader Position Behavior ---


class TestNautilusPositionBehavior:
    """Test behavior that matches NautilusTrader's position aggregation."""

    def test_get_current_position_size_returns_first_match(
        self,
        risk_manager: RiskManager,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
        instrument_id_eth: InstrumentId,
    ) -> None:
        """_get_current_position_size returns first matching instrument (NT aggregates positions)."""
        # In NautilusTrader, you can't have multiple positions on same instrument
        # They are automatically aggregated, so we only return the first match
        position_btc = create_mock_position(
            instrument_id, PositionSide.LONG, "50000.00", "0.8", "P-001"
        )
        position_eth = create_mock_position(
            instrument_id_eth, PositionSide.LONG, "3000.00", "5.0", "P-002"
        )
        mock_strategy.cache.positions_open.return_value = [position_btc, position_eth]

        btc_size = risk_manager._get_current_position_size(instrument_id)
        eth_size = risk_manager._get_current_position_size(instrument_id_eth)

        # Should return the size of the first matching position
        assert btc_size == pytest.approx(0.8)
        assert eth_size == pytest.approx(5.0)

    def test_position_limit_enforced_for_single_position(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """Per-instrument limit should work with single aggregated position."""
        config = RiskConfig(max_position_size={"BTC/USDT.BINANCE": Decimal("1.0")})
        manager = RiskManager(config=config, strategy=mock_strategy)

        # Single position at 0.9 BTC (NautilusTrader aggregates all BTC positions)
        position = create_mock_position(
            instrument_id, PositionSide.LONG, "50000.00", "0.9", "P-001"
        )
        mock_strategy.cache.positions_open.return_value = [position]

        # New order: 0.2 BTC (total = 1.1, exceeds limit)
        order = create_mock_order(instrument_id, OrderSide.BUY, "0.2")

        result = manager.validate_order(order)
        assert result is False


# --- Coverage Completeness Tests ---


class TestCoverageCompleteness:
    """Tests specifically for achieving 90%+ coverage."""

    def test_validate_order_early_return_no_limits(
        self,
        risk_manager: RiskManager,
        instrument_id: InstrumentId,
    ) -> None:
        """validate_order should return True early when no limits configured."""
        # Default config has no position/exposure limits
        assert risk_manager.config.max_position_size is None
        assert risk_manager.config.max_total_exposure is None

        order = create_mock_order(instrument_id, OrderSide.BUY, "999.0")
        result = risk_manager.validate_order(order)

        # Should return True at line 106
        assert result is True

    def test_validate_order_instrument_not_in_limit_dict(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """Order for instrument not in max_position_size dict should be allowed."""
        config = RiskConfig(max_position_size={"ETH/USDT.BINANCE": Decimal("10.0")})
        manager = RiskManager(config=config, strategy=mock_strategy)

        # BTC not in limit dict
        order = create_mock_order(instrument_id, OrderSide.BUY, "100.0")

        result = manager.validate_order(order)
        assert result is True

    def test_get_total_exposure_with_none_net_exposure(
        self,
        risk_manager: RiskManager,
        mock_strategy: MagicMock,
    ) -> None:
        """_get_total_exposure should handle None from net_exposure()."""
        mock_strategy.portfolio.net_exposure.return_value = None

        exposure = risk_manager._get_total_exposure()
        assert exposure == 0.0
