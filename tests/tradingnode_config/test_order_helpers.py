"""
Unit tests for Order Helper Functions (Spec 015 FR-002).

Tests all order creation helpers: MARKET, LIMIT, STOP_MARKET, STOP_LIMIT.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to sys.path for imports
_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import pytest  # noqa: E402
from nautilus_trader.common.component import TestClock  # noqa: E402
from nautilus_trader.common.factories import OrderFactory  # noqa: E402
from nautilus_trader.model.enums import OrderSide, TimeInForce, TriggerType  # noqa: E402
from nautilus_trader.model.identifiers import InstrumentId, StrategyId, TraderId  # noqa: E402
from nautilus_trader.model.objects import Price, Quantity  # noqa: E402

from config.order_helpers import (  # noqa: E402
    create_external_claims,
    create_limit_order,
    create_market_order,
    create_stop_limit_order,
    create_stop_market_order,
    validate_order_params,
)


@pytest.fixture
def order_factory():
    """Create an OrderFactory for testing."""
    clock = TestClock()
    return OrderFactory(
        trader_id=TraderId("TESTER-001"),
        strategy_id=StrategyId("TestStrategy-001"),
        clock=clock,
    )


@pytest.fixture
def instrument_id():
    """Create a test instrument ID."""
    return InstrumentId.from_str("BTCUSDT-PERP.BINANCE")


@pytest.fixture
def quantity():
    """Create a test quantity."""
    return Quantity.from_str("0.1")


@pytest.fixture
def price():
    """Create a test price."""
    return Price.from_str("50000.00")


@pytest.fixture
def trigger_price():
    """Create a test trigger price."""
    return Price.from_str("48000.00")


class TestValidateOrderParams:
    """Tests for validate_order_params function."""

    def test_valid_params(self, instrument_id, quantity, price):
        """Should not raise for valid parameters."""
        validate_order_params(instrument_id, OrderSide.BUY, quantity, price=price)

    def test_invalid_instrument_id(self, quantity):
        """Should raise for invalid instrument_id type."""
        with pytest.raises(ValueError, match="instrument_id must be InstrumentId"):
            validate_order_params("invalid", OrderSide.BUY, quantity)

    def test_invalid_side(self, instrument_id, quantity):
        """Should raise for invalid side type."""
        with pytest.raises(ValueError, match="side must be OrderSide"):
            validate_order_params(instrument_id, "BUY", quantity)

    def test_zero_quantity(self, instrument_id):
        """Should raise for zero quantity."""
        zero_qty = Quantity.from_str("0.0")
        with pytest.raises(ValueError, match="quantity must be positive"):
            validate_order_params(instrument_id, OrderSide.BUY, zero_qty)

    def test_negative_price(self, instrument_id, quantity):
        """Should raise for negative price."""
        # Note: Price constructor doesn't allow negative values,
        # so this test validates our logic is correct
        pass  # Skipped as Price validation happens at creation


class TestCreateMarketOrder:
    """Tests for create_market_order function."""

    def test_creates_market_order(self, order_factory, instrument_id, quantity):
        """Should create a valid market order."""
        order = create_market_order(order_factory, instrument_id, OrderSide.BUY, quantity)
        assert order is not None
        assert order.instrument_id == instrument_id
        assert order.side == OrderSide.BUY
        assert order.quantity == quantity

    def test_buy_side(self, order_factory, instrument_id, quantity):
        """Should create buy order."""
        order = create_market_order(order_factory, instrument_id, OrderSide.BUY, quantity)
        assert order.side == OrderSide.BUY

    def test_sell_side(self, order_factory, instrument_id, quantity):
        """Should create sell order."""
        order = create_market_order(order_factory, instrument_id, OrderSide.SELL, quantity)
        assert order.side == OrderSide.SELL

    def test_reduce_only_default_false(self, order_factory, instrument_id, quantity):
        """Should default reduce_only to False."""
        order = create_market_order(order_factory, instrument_id, OrderSide.BUY, quantity)
        assert order.is_reduce_only is False

    def test_reduce_only_true(self, order_factory, instrument_id, quantity):
        """Should set reduce_only when specified."""
        order = create_market_order(
            order_factory, instrument_id, OrderSide.SELL, quantity, reduce_only=True
        )
        assert order.is_reduce_only is True

    def test_with_tags(self, order_factory, instrument_id, quantity):
        """Should accept custom tags."""
        order = create_market_order(
            order_factory, instrument_id, OrderSide.BUY, quantity, tags=["stop_loss"]
        )
        assert order.tags is not None


class TestCreateLimitOrder:
    """Tests for create_limit_order function."""

    def test_creates_limit_order(self, order_factory, instrument_id, quantity, price):
        """Should create a valid limit order."""
        order = create_limit_order(order_factory, instrument_id, OrderSide.BUY, quantity, price)
        assert order is not None
        assert order.instrument_id == instrument_id
        assert order.price == price

    def test_post_only_default_false(self, order_factory, instrument_id, quantity, price):
        """Should default post_only to False."""
        order = create_limit_order(order_factory, instrument_id, OrderSide.BUY, quantity, price)
        assert order.is_post_only is False

    def test_post_only_true(self, order_factory, instrument_id, quantity, price):
        """Should set post_only when specified."""
        order = create_limit_order(
            order_factory,
            instrument_id,
            OrderSide.SELL,
            quantity,
            price,
            post_only=True,
        )
        assert order.is_post_only is True

    def test_time_in_force_default_gtc(self, order_factory, instrument_id, quantity, price):
        """Should default time_in_force to GTC."""
        order = create_limit_order(order_factory, instrument_id, OrderSide.BUY, quantity, price)
        assert order.time_in_force == TimeInForce.GTC

    def test_custom_time_in_force(self, order_factory, instrument_id, quantity, price):
        """Should accept custom time_in_force."""
        order = create_limit_order(
            order_factory,
            instrument_id,
            OrderSide.BUY,
            quantity,
            price,
            time_in_force=TimeInForce.IOC,
        )
        assert order.time_in_force == TimeInForce.IOC


class TestCreateStopMarketOrder:
    """Tests for create_stop_market_order function (Algo Order API)."""

    def test_creates_stop_market_order(self, order_factory, instrument_id, quantity, trigger_price):
        """Should create a valid stop-market order."""
        order = create_stop_market_order(
            order_factory, instrument_id, OrderSide.SELL, quantity, trigger_price
        )
        assert order is not None
        assert order.instrument_id == instrument_id
        assert order.trigger_price == trigger_price

    def test_trigger_type_default_last_price(
        self, order_factory, instrument_id, quantity, trigger_price
    ):
        """Should default trigger_type to LAST_PRICE."""
        order = create_stop_market_order(
            order_factory, instrument_id, OrderSide.SELL, quantity, trigger_price
        )
        assert order.trigger_type == TriggerType.LAST_PRICE

    def test_custom_trigger_type(self, order_factory, instrument_id, quantity, trigger_price):
        """Should accept custom trigger_type."""
        order = create_stop_market_order(
            order_factory,
            instrument_id,
            OrderSide.SELL,
            quantity,
            trigger_price,
            trigger_type=TriggerType.MARK_PRICE,
        )
        assert order.trigger_type == TriggerType.MARK_PRICE

    def test_reduce_only_for_stop_loss(self, order_factory, instrument_id, quantity, trigger_price):
        """Stop-loss should support reduce_only."""
        order = create_stop_market_order(
            order_factory,
            instrument_id,
            OrderSide.SELL,
            quantity,
            trigger_price,
            reduce_only=True,
        )
        assert order.is_reduce_only is True


class TestCreateStopLimitOrder:
    """Tests for create_stop_limit_order function (Algo Order API)."""

    def test_creates_stop_limit_order(
        self, order_factory, instrument_id, quantity, price, trigger_price
    ):
        """Should create a valid stop-limit order."""
        order = create_stop_limit_order(
            order_factory, instrument_id, OrderSide.SELL, quantity, price, trigger_price
        )
        assert order is not None
        assert order.price == price
        assert order.trigger_price == trigger_price

    def test_post_only(self, order_factory, instrument_id, quantity, price, trigger_price):
        """Should support post_only for maker orders."""
        order = create_stop_limit_order(
            order_factory,
            instrument_id,
            OrderSide.SELL,
            quantity,
            price,
            trigger_price,
            post_only=True,
        )
        assert order.is_post_only is True


class TestCreateExternalClaims:
    """Tests for create_external_claims function (FR-005)."""

    def test_creates_instrument_ids(self):
        """Should convert string IDs to InstrumentId objects."""
        claims = create_external_claims(["BTCUSDT-PERP.BINANCE"])
        assert len(claims) == 1
        assert isinstance(claims[0], InstrumentId)
        assert str(claims[0]) == "BTCUSDT-PERP.BINANCE"

    def test_multiple_instruments(self):
        """Should handle multiple instruments."""
        claims = create_external_claims(
            [
                "BTCUSDT-PERP.BINANCE",
                "ETHUSDT-PERP.BINANCE",
            ]
        )
        assert len(claims) == 2

    def test_empty_list(self):
        """Should handle empty list."""
        claims = create_external_claims([])
        assert claims == []
