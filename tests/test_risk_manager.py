"""
Unit tests for RiskManager.

Tests cover:
- User Story 1: Automatic Stop-Loss (T010-T014)
- User Story 2: Position Limits (T025-T027)
- User Story 4: Advanced Features (T041-T042)
"""

from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from nautilus_trader.model.enums import OrderSide, PositionSide
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
from risk.manager import RiskManager

# Create USDT currency constant for Money objects
USDT = Currency.from_str("USDT")


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
    strategy.strategy_id = StrategyId("TestStrategy-001")

    # Mock order factory
    strategy.order_factory = MagicMock()
    strategy.order_factory.stop_market = MagicMock(return_value=MagicMock())

    # Mock cache
    strategy.cache = MagicMock()
    strategy.cache.positions_open = MagicMock(return_value=[])
    strategy.cache.position = MagicMock(return_value=None)

    # Mock portfolio
    strategy.portfolio = MagicMock()
    strategy.portfolio.net_exposure = MagicMock(return_value=Money(0, USDT))

    # Mock instrument
    mock_instrument = MagicMock()
    mock_instrument.make_price = lambda p: Price.from_str(str(p))
    mock_instrument.make_qty = lambda q: Quantity.from_str(str(q))
    strategy.cache.instrument = MagicMock(return_value=mock_instrument)

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


def create_mock_position_opened_event(position: MagicMock) -> MagicMock:
    """Create mock PositionOpened event."""
    from nautilus_trader.model.events import PositionOpened

    event = MagicMock(spec=PositionOpened)
    event.position_id = position.id
    event.instrument_id = position.instrument_id
    event.position_side = position.side
    event.avg_px_open = position.avg_px_open
    event.quantity = position.quantity
    return event


def create_mock_position_closed_event(position: MagicMock) -> MagicMock:
    """Create mock PositionClosed event."""
    from nautilus_trader.model.events import PositionClosed

    event = MagicMock(spec=PositionClosed)
    event.position_id = position.id
    event.instrument_id = position.instrument_id
    return event


# --- User Story 1: Automatic Stop-Loss Tests (T010-T014) ---


class TestCalculateStopPrice:
    """T010: Unit test for _calculate_stop_price() LONG/SHORT."""

    def test_long_position_stop_price_below_entry(
        self,
        risk_manager: RiskManager,
        instrument_id: InstrumentId,
    ) -> None:
        """LONG stop price should be below entry price."""
        position = create_mock_position(
            instrument_id=instrument_id,
            side=PositionSide.LONG,
            entry_price="50000.00",
            quantity="0.1",
        )

        stop_price = risk_manager._calculate_stop_price(position)

        # 50000 * (1 - 0.02) = 49000
        expected = Decimal("50000.00") * (1 - Decimal("0.02"))
        assert float(stop_price) == pytest.approx(float(expected), rel=1e-6)

    def test_short_position_stop_price_above_entry(
        self,
        risk_manager: RiskManager,
        instrument_id: InstrumentId,
    ) -> None:
        """SHORT stop price should be above entry price."""
        position = create_mock_position(
            instrument_id=instrument_id,
            side=PositionSide.SHORT,
            entry_price="50000.00",
            quantity="0.1",
        )

        stop_price = risk_manager._calculate_stop_price(position)

        # 50000 * (1 + 0.02) = 51000
        expected = Decimal("50000.00") * (1 + Decimal("0.02"))
        assert float(stop_price) == pytest.approx(float(expected), rel=1e-6)

    def test_stop_price_with_custom_percentage(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """Stop price should respect custom stop_loss_pct."""
        config = RiskConfig(stop_loss_pct=Decimal("0.05"))  # 5%
        manager = RiskManager(config=config, strategy=mock_strategy)

        position = create_mock_position(
            instrument_id=instrument_id,
            side=PositionSide.LONG,
            entry_price="100.00",
            quantity="1.0",
        )

        stop_price = manager._calculate_stop_price(position)

        # 100 * (1 - 0.05) = 95
        expected = Decimal("95.00")
        assert float(stop_price) == pytest.approx(float(expected), rel=1e-6)


class TestCreateStopOrder:
    """T011: Unit test for _create_stop_order() with reduce_only."""

    def test_stop_order_has_reduce_only_true(
        self,
        risk_manager: RiskManager,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """Stop order must have reduce_only=True to prevent position flip."""
        position = create_mock_position(
            instrument_id=instrument_id,
            side=PositionSide.LONG,
            entry_price="50000.00",
            quantity="0.1",
        )
        stop_price = Price.from_str("49000.00")

        risk_manager._create_stop_order(position, stop_price)

        # Verify stop_market was called with reduce_only=True
        mock_strategy.order_factory.stop_market.assert_called_once()
        call_kwargs = mock_strategy.order_factory.stop_market.call_args[1]
        assert call_kwargs.get("reduce_only") is True

    def test_long_position_creates_sell_stop(
        self,
        risk_manager: RiskManager,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """LONG position should create SELL stop order."""
        position = create_mock_position(
            instrument_id=instrument_id,
            side=PositionSide.LONG,
            entry_price="50000.00",
            quantity="0.1",
        )
        stop_price = Price.from_str("49000.00")

        risk_manager._create_stop_order(position, stop_price)

        call_kwargs = mock_strategy.order_factory.stop_market.call_args[1]
        assert call_kwargs.get("order_side") == OrderSide.SELL

    def test_short_position_creates_buy_stop(
        self,
        risk_manager: RiskManager,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """SHORT position should create BUY stop order."""
        position = create_mock_position(
            instrument_id=instrument_id,
            side=PositionSide.SHORT,
            entry_price="50000.00",
            quantity="0.1",
        )
        stop_price = Price.from_str("51000.00")

        risk_manager._create_stop_order(position, stop_price)

        call_kwargs = mock_strategy.order_factory.stop_market.call_args[1]
        assert call_kwargs.get("order_side") == OrderSide.BUY


class TestHandleEvent:
    """T012: Unit test for handle_event() routing."""

    def test_routes_position_opened_event(
        self,
        risk_manager: RiskManager,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """PositionOpened event should be routed to _on_position_opened."""

        position = create_mock_position(
            instrument_id=instrument_id,
            side=PositionSide.LONG,
            entry_price="50000.00",
            quantity="0.1",
        )
        mock_strategy.cache.position.return_value = position

        event = create_mock_position_opened_event(position)

        risk_manager.handle_event(event)

        # Should have created a stop order
        mock_strategy.order_factory.stop_market.assert_called_once()

    def test_routes_position_closed_event(
        self,
        risk_manager: RiskManager,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """PositionClosed event should be routed to _on_position_closed."""
        position = create_mock_position(
            instrument_id=instrument_id,
            side=PositionSide.LONG,
            entry_price="50000.00",
            quantity="0.1",
        )

        # First open position to create stop
        mock_strategy.cache.position.return_value = position
        open_event = create_mock_position_opened_event(position)
        risk_manager.handle_event(open_event)

        # Now close position
        close_event = create_mock_position_closed_event(position)
        risk_manager.handle_event(close_event)

        # Should have attempted to cancel the stop order
        mock_strategy.cancel_order.assert_called()

    def test_ignores_unknown_events(
        self,
        risk_manager: RiskManager,
        mock_strategy: MagicMock,
    ) -> None:
        """Unknown events should be ignored without error."""
        unknown_event = MagicMock()
        unknown_event.__class__.__name__ = "UnknownEvent"

        # Should not raise
        risk_manager.handle_event(unknown_event)

        # Should not have called any order methods
        mock_strategy.order_factory.stop_market.assert_not_called()
        mock_strategy.cancel_order.assert_not_called()


class TestOnPositionOpened:
    """T013: Unit test for _on_position_opened() creates stop."""

    def test_creates_stop_order_on_position_opened(
        self,
        risk_manager: RiskManager,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """Should create and submit stop order when position opens."""
        position = create_mock_position(
            instrument_id=instrument_id,
            side=PositionSide.LONG,
            entry_price="50000.00",
            quantity="0.1",
        )
        mock_strategy.cache.position.return_value = position

        event = create_mock_position_opened_event(position)
        risk_manager.handle_event(event)

        # Verify stop order created
        mock_strategy.order_factory.stop_market.assert_called_once()

        # Verify order submitted
        mock_strategy.submit_order.assert_called_once()

    def test_stores_position_to_stop_mapping(
        self,
        risk_manager: RiskManager,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """Should store mapping from position ID to stop order ID."""
        position = create_mock_position(
            instrument_id=instrument_id,
            side=PositionSide.LONG,
            entry_price="50000.00",
            quantity="0.1",
        )
        mock_strategy.cache.position.return_value = position

        # Set up mock stop order with client_order_id
        mock_stop_order = MagicMock()
        mock_stop_order.client_order_id = ClientOrderId("O-STOP-001")
        mock_strategy.order_factory.stop_market.return_value = mock_stop_order

        event = create_mock_position_opened_event(position)
        risk_manager.handle_event(event)

        # Verify mapping stored
        assert position.id in risk_manager.active_stops
        assert risk_manager.active_stops[position.id] == mock_stop_order.client_order_id

    def test_does_not_create_stop_when_disabled(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """Should not create stop order when stop_loss_enabled=False."""
        config = RiskConfig(stop_loss_enabled=False)
        manager = RiskManager(config=config, strategy=mock_strategy)

        position = create_mock_position(
            instrument_id=instrument_id,
            side=PositionSide.LONG,
            entry_price="50000.00",
            quantity="0.1",
        )
        mock_strategy.cache.position.return_value = position

        event = create_mock_position_opened_event(position)
        manager.handle_event(event)

        # Should not have created stop order
        mock_strategy.order_factory.stop_market.assert_not_called()


class TestOnPositionClosed:
    """T014: Unit test for _on_position_closed() cancels stop."""

    def test_cancels_stop_order_on_position_closed(
        self,
        risk_manager: RiskManager,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """Should cancel stop order when position closes."""
        position = create_mock_position(
            instrument_id=instrument_id,
            side=PositionSide.LONG,
            entry_price="50000.00",
            quantity="0.1",
        )

        # Set up mock stop order
        mock_stop_order = MagicMock()
        mock_stop_order.client_order_id = ClientOrderId("O-STOP-001")
        mock_strategy.order_factory.stop_market.return_value = mock_stop_order
        mock_strategy.cache.position.return_value = position

        # Open position to create stop
        open_event = create_mock_position_opened_event(position)
        risk_manager.handle_event(open_event)

        # Close position
        close_event = create_mock_position_closed_event(position)
        risk_manager.handle_event(close_event)

        # Verify cancel called with stop order ID
        mock_strategy.cancel_order.assert_called_once()
        call_args = mock_strategy.cancel_order.call_args[0]
        # Use string comparison for cross-version compatibility
        assert str(call_args[0]) == str(mock_stop_order.client_order_id)

    def test_removes_mapping_on_position_closed(
        self,
        risk_manager: RiskManager,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """Should remove position from active_stops mapping."""
        position = create_mock_position(
            instrument_id=instrument_id,
            side=PositionSide.LONG,
            entry_price="50000.00",
            quantity="0.1",
        )

        mock_stop_order = MagicMock()
        mock_stop_order.client_order_id = ClientOrderId("O-STOP-001")
        mock_strategy.order_factory.stop_market.return_value = mock_stop_order
        mock_strategy.cache.position.return_value = position

        # Open then close
        open_event = create_mock_position_opened_event(position)
        risk_manager.handle_event(open_event)

        close_event = create_mock_position_closed_event(position)
        risk_manager.handle_event(close_event)

        # Mapping should be removed
        assert position.id not in risk_manager.active_stops

    def test_handles_close_without_stop(
        self,
        risk_manager: RiskManager,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """Should handle position close when no stop exists (e.g., stop disabled)."""
        position = create_mock_position(
            instrument_id=instrument_id,
            side=PositionSide.LONG,
            entry_price="50000.00",
            quantity="0.1",
        )

        # Close without opening (simulates external close or stop disabled)
        close_event = create_mock_position_closed_event(position)

        # Should not raise
        risk_manager.handle_event(close_event)

        # Should not have called cancel
        mock_strategy.cancel_order.assert_not_called()


# --- User Story 2: Position Limits Tests (T025-T027) ---


class TestValidateOrderPerInstrumentLimit:
    """T025: Unit test for validate_order() per-instrument limit."""

    def test_rejects_order_exceeding_per_instrument_limit(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """Order should be rejected if it exceeds per-instrument max position."""
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

        # New order: 0.3 BTC (total would be 0.6, exceeds 0.5 limit)
        order = MagicMock()
        order.instrument_id = instrument_id
        order.quantity = Quantity.from_str("0.3")
        order.side = OrderSide.BUY

        result = manager.validate_order(order)

        assert result is False

    def test_allows_order_within_per_instrument_limit(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """Order should be allowed if within per-instrument limit."""
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

        # New order: 0.1 BTC (total would be 0.4, within 0.5 limit)
        order = MagicMock()
        order.instrument_id = instrument_id
        order.quantity = Quantity.from_str("0.1")
        order.side = OrderSide.BUY

        result = manager.validate_order(order)

        assert result is True


class TestValidateOrderTotalExposureLimit:
    """T026: Unit test for validate_order() total exposure limit."""

    def test_rejects_order_exceeding_total_exposure(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """Order should be rejected if total exposure exceeds limit."""
        config = RiskConfig(max_total_exposure=Decimal("10000"))
        manager = RiskManager(config=config, strategy=mock_strategy)

        # Current exposure: $9000
        mock_strategy.portfolio.net_exposure.return_value = Money(9000, USDT)

        # New order would add $2000 (total $11000 > $10000 limit)
        order = MagicMock()
        order.instrument_id = instrument_id
        order.quantity = Quantity.from_str("0.04")  # 0.04 BTC @ $50000 = $2000
        order.side = OrderSide.BUY

        # Mock quote_tick for notional calculation (new implementation)
        mock_quote = MagicMock()
        mock_quote.ask_price = Price.from_str("50000.00")
        mock_strategy.cache.quote_tick.return_value = mock_quote

        result = manager.validate_order(order)

        assert result is False

    def test_allows_order_within_total_exposure(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """Order should be allowed if within total exposure limit."""
        config = RiskConfig(max_total_exposure=Decimal("10000"))
        manager = RiskManager(config=config, strategy=mock_strategy)

        # Current exposure: $5000
        mock_strategy.portfolio.net_exposure.return_value = Money(5000, USDT)

        # New order would add $2000 (total $7000 < $10000 limit)
        order = MagicMock()
        order.instrument_id = instrument_id
        order.quantity = Quantity.from_str("0.04")
        order.side = OrderSide.BUY

        result = manager.validate_order(order)

        assert result is True


class TestValidateOrderReturnsTrue:
    """T027: Unit test for validate_order() returns True when within limits."""

    def test_returns_true_with_no_limits_configured(
        self,
        risk_manager: RiskManager,
        instrument_id: InstrumentId,
    ) -> None:
        """Order should be allowed when no limits are configured."""
        order = MagicMock()
        order.instrument_id = instrument_id
        order.quantity = Quantity.from_str("100.0")  # Large quantity
        order.side = OrderSide.BUY

        result = risk_manager.validate_order(order)

        assert result is True

    def test_returns_true_for_reduce_only_orders(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """Reduce-only orders should always be allowed (they reduce risk)."""
        config = RiskConfig(max_position_size={"BTC/USDT.BINANCE": Decimal("0.5")})
        manager = RiskManager(config=config, strategy=mock_strategy)

        # Current position at limit: 0.5 BTC LONG
        current_position = create_mock_position(
            instrument_id=instrument_id,
            side=PositionSide.LONG,
            entry_price="50000.00",
            quantity="0.5",
        )
        mock_strategy.cache.positions_open.return_value = [current_position]

        # SELL order to close (reduce_only would decrease position)
        order = MagicMock()
        order.instrument_id = instrument_id
        order.quantity = Quantity.from_str("0.5")
        order.side = OrderSide.SELL

        result = manager.validate_order(order)

        assert result is True


# --- User Story 4: Advanced Features Tests (T041-T042) ---


class TestOnPositionChangedTrailing:
    """T041: Unit test for _on_position_changed() trailing update."""

    def test_updates_trailing_stop_on_favorable_move(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """Trailing stop should update when price moves favorably."""
        config = RiskConfig(
            trailing_stop=True,
            trailing_distance_pct=Decimal("0.01"),  # 1%
        )
        manager = RiskManager(config=config, strategy=mock_strategy)

        position = create_mock_position(
            instrument_id=instrument_id,
            side=PositionSide.LONG,
            entry_price="50000.00",
            quantity="0.1",
        )

        # Set up mock stop order
        mock_stop_order = MagicMock()
        mock_stop_order.client_order_id = ClientOrderId("O-STOP-001")
        mock_strategy.order_factory.stop_market.return_value = mock_stop_order
        mock_strategy.cache.position.return_value = position

        # Open position
        open_event = create_mock_position_opened_event(position)
        manager.handle_event(open_event)

        # Simulate price move to $55000 (favorable for LONG)
        from nautilus_trader.model.events import PositionChanged

        changed_event = MagicMock(spec=PositionChanged)
        changed_event.position_id = position.id
        changed_event.instrument_id = instrument_id

        # Update position's best price
        position.avg_px_open = 55000.0

        manager.handle_event(changed_event)

        # Should have modified or recreated stop order
        # (implementation may cancel + create new, or modify)
        assert mock_strategy.cancel_order.called or mock_strategy.modify_order.called


class TestCreateStopLimitOrder:
    """T042: Unit test for _create_stop_order() with STOP_LIMIT type."""

    def test_creates_stop_limit_when_configured(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """Should create STOP_LIMIT order when stop_loss_type is LIMIT."""
        config = RiskConfig(
            stop_loss_type=StopLossType.LIMIT,
            stop_loss_pct=Decimal("0.02"),
        )
        manager = RiskManager(config=config, strategy=mock_strategy)

        # Set up mock stop_limit method
        mock_strategy.order_factory.stop_limit = MagicMock(return_value=MagicMock())

        position = create_mock_position(
            instrument_id=instrument_id,
            side=PositionSide.LONG,
            entry_price="50000.00",
            quantity="0.1",
        )
        stop_price = Price.from_str("49000.00")

        manager._create_stop_order(position, stop_price)

        # Should call stop_limit instead of stop_market
        mock_strategy.order_factory.stop_limit.assert_called_once()


# --- T023-T024: Circuit Breaker Integration Tests ---


class TestRiskManagerWithCircuitBreaker:
    """T023: Unit test for RiskManager with circuit_breaker parameter."""

    def test_accepts_circuit_breaker_parameter(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """RiskManager should accept optional circuit_breaker parameter."""
        from risk import CircuitBreaker, CircuitBreakerConfig

        cb_config = CircuitBreakerConfig()
        circuit_breaker = CircuitBreaker(config=cb_config, portfolio=None)

        config = RiskConfig()
        manager = RiskManager(
            config=config,
            strategy=mock_strategy,
            circuit_breaker=circuit_breaker,
        )

        assert manager.circuit_breaker is circuit_breaker

    def test_circuit_breaker_is_optional(
        self,
        risk_manager: RiskManager,
    ) -> None:
        """RiskManager should work without circuit_breaker."""
        assert risk_manager.circuit_breaker is None


class TestOrderRejectionOnHaltedState:
    """T024: Unit test for order rejection on HALTED state."""

    def test_rejects_order_when_circuit_breaker_halted(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """Order should be rejected when circuit breaker is in HALTED state."""
        from risk import CircuitBreaker, CircuitBreakerConfig

        cb_config = CircuitBreakerConfig()
        circuit_breaker = CircuitBreaker(config=cb_config, portfolio=None)
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("80000"))  # 20% drawdown -> HALTED

        config = RiskConfig()
        manager = RiskManager(
            config=config,
            strategy=mock_strategy,
            circuit_breaker=circuit_breaker,
        )

        order = MagicMock()
        order.instrument_id = instrument_id
        order.quantity = Quantity.from_str("0.1")
        order.side = OrderSide.BUY

        result = manager.validate_order(order)

        assert result is False

    def test_rejects_order_when_circuit_breaker_reducing(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """Order should be rejected when circuit breaker is in REDUCING state."""
        from risk import CircuitBreaker, CircuitBreakerConfig

        cb_config = CircuitBreakerConfig()
        circuit_breaker = CircuitBreaker(config=cb_config, portfolio=None)
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("85000"))  # 15% drawdown -> REDUCING

        config = RiskConfig()
        manager = RiskManager(
            config=config,
            strategy=mock_strategy,
            circuit_breaker=circuit_breaker,
        )

        order = MagicMock()
        order.instrument_id = instrument_id
        order.quantity = Quantity.from_str("0.1")
        order.side = OrderSide.BUY

        result = manager.validate_order(order)

        assert result is False

    def test_allows_order_when_circuit_breaker_active(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """Order should be allowed when circuit breaker is in ACTIVE state."""
        from risk import CircuitBreaker, CircuitBreakerConfig

        cb_config = CircuitBreakerConfig()
        circuit_breaker = CircuitBreaker(config=cb_config, portfolio=None)
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("100000"))  # 0% drawdown -> ACTIVE

        config = RiskConfig()
        manager = RiskManager(
            config=config,
            strategy=mock_strategy,
            circuit_breaker=circuit_breaker,
        )

        order = MagicMock()
        order.instrument_id = instrument_id
        order.quantity = Quantity.from_str("0.1")
        order.side = OrderSide.BUY

        result = manager.validate_order(order)

        assert result is True

    def test_allows_order_when_circuit_breaker_warning(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """Order should be allowed when circuit breaker is in WARNING state."""
        from risk import CircuitBreaker, CircuitBreakerConfig

        cb_config = CircuitBreakerConfig()
        circuit_breaker = CircuitBreaker(config=cb_config, portfolio=None)
        circuit_breaker.set_initial_equity(Decimal("100000"))
        circuit_breaker.update(equity=Decimal("90000"))  # 10% drawdown -> WARNING

        config = RiskConfig()
        manager = RiskManager(
            config=config,
            strategy=mock_strategy,
            circuit_breaker=circuit_breaker,
        )

        order = MagicMock()
        order.instrument_id = instrument_id
        order.quantity = Quantity.from_str("0.1")
        order.side = OrderSide.BUY

        result = manager.validate_order(order)

        assert result is True


# --- T030-T034: Daily PnL Tracker Integration Tests ---


class TestRiskManagerWithDailyTracker:
    """T030: Unit test for RiskManager with daily_tracker parameter."""

    def test_accepts_daily_tracker_parameter(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """RiskManager should accept optional daily_tracker parameter."""
        from risk import DailyLossConfig, DailyPnLTracker

        daily_config = DailyLossConfig()
        daily_tracker = DailyPnLTracker(config=daily_config, strategy=mock_strategy)

        config = RiskConfig()
        manager = RiskManager(
            config=config,
            strategy=mock_strategy,
            daily_tracker=daily_tracker,
        )

        assert manager.daily_tracker is daily_tracker

    def test_daily_tracker_is_optional(
        self,
        risk_manager: RiskManager,
    ) -> None:
        """RiskManager should work without daily_tracker."""
        assert risk_manager.daily_tracker is None


class TestRiskManagerWithoutDailyTracker:
    """T031: Unit test for RiskManager without daily_tracker."""

    def test_validates_order_without_daily_tracker(
        self,
        risk_manager: RiskManager,
        instrument_id: InstrumentId,
    ) -> None:
        """Order validation should work without daily_tracker."""
        order = MagicMock()
        order.instrument_id = instrument_id
        order.quantity = Quantity.from_str("0.1")
        order.side = OrderSide.BUY

        result = risk_manager.validate_order(order)

        assert result is True


class TestDailyTrackerEventRouting:
    """T032/T033: Test event routing to daily_tracker."""

    def test_routes_position_closed_to_daily_tracker(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """PositionClosed event should be routed to daily_tracker."""
        from risk import DailyLossConfig, DailyPnLTracker

        daily_config = DailyLossConfig()
        daily_tracker = DailyPnLTracker(config=daily_config, strategy=mock_strategy)

        config = RiskConfig(stop_loss_enabled=False)
        manager = RiskManager(
            config=config,
            strategy=mock_strategy,
            daily_tracker=daily_tracker,
        )

        position = create_mock_position(
            instrument_id=instrument_id,
            side=PositionSide.LONG,
            entry_price="50000.00",
            quantity="0.1",
        )

        # Create PositionClosed event with realized_pnl
        close_event = create_mock_position_closed_event(position)
        from nautilus_trader.model.objects import Money

        close_event.realized_pnl = Money(100.0, USDT)

        manager.handle_event(close_event)

        # Daily tracker should have accumulated the realized PnL
        assert daily_tracker.daily_realized == Decimal("100")


class TestDailyTrackerValidateOrderIntegration:
    """T034: Test validate_order() integration with daily_tracker.can_trade()."""

    def test_rejects_order_when_daily_limit_triggered(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """Order should be rejected when daily loss limit is triggered."""
        from risk import DailyLossConfig, DailyPnLTracker

        daily_config = DailyLossConfig(daily_loss_limit=Decimal("100"))
        daily_tracker = DailyPnLTracker(config=daily_config, strategy=mock_strategy)

        config = RiskConfig()
        manager = RiskManager(
            config=config,
            strategy=mock_strategy,
            daily_tracker=daily_tracker,
        )

        # Create a PositionClosed event to trigger the daily limit
        position = create_mock_position(
            instrument_id=instrument_id,
            side=PositionSide.LONG,
            entry_price="50000.00",
            quantity="0.1",
        )
        close_event = create_mock_position_closed_event(position)
        from nautilus_trader.model.objects import Money

        close_event.realized_pnl = Money(-150.0, USDT)  # Loss exceeds $100 limit

        manager.handle_event(close_event)
        daily_tracker.check_limit()

        # Now try to place an order
        order = MagicMock()
        order.instrument_id = instrument_id
        order.quantity = Quantity.from_str("0.1")
        order.side = OrderSide.BUY

        result = manager.validate_order(order)

        assert result is False

    def test_allows_order_when_daily_limit_not_triggered(
        self,
        mock_strategy: MagicMock,
        instrument_id: InstrumentId,
    ) -> None:
        """Order should be allowed when daily loss limit not triggered."""
        from risk import DailyLossConfig, DailyPnLTracker

        daily_config = DailyLossConfig(daily_loss_limit=Decimal("1000"))
        daily_tracker = DailyPnLTracker(config=daily_config, strategy=mock_strategy)

        config = RiskConfig()
        manager = RiskManager(
            config=config,
            strategy=mock_strategy,
            daily_tracker=daily_tracker,
        )

        order = MagicMock()
        order.instrument_id = instrument_id
        order.quantity = Quantity.from_str("0.1")
        order.side = OrderSide.BUY

        result = manager.validate_order(order)

        assert result is True
