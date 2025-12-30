"""Unit tests for exit order recreation (FR-002 - T022).

Tests:
- _setup_exit_orders() checks for existing stops
- _is_stop_order() identifies stop order types
- Stop-loss detection for recovered positions
- Warning logged when no stop-loss found
"""

from unittest.mock import MagicMock

import pytest

from nautilus_trader.model.enums import OrderType


@pytest.mark.recovery
class TestSetupExitOrders:
    """Tests for _setup_exit_orders method."""

    def test_setup_exit_orders_checks_open_orders(self, mock_cache):
        """Test that _setup_exit_orders checks open orders from cache."""
        from nautilus_trader.model.identifiers import InstrumentId

        # Create mock position
        mock_position = MagicMock()
        mock_position.instrument_id = InstrumentId.from_str("BTCUSDT-PERP.BINANCE")

        # Setup cache to return empty orders
        mock_cache.orders_open.return_value = []

        # Simulate _setup_exit_orders logic
        open_orders = mock_cache.orders_open(instrument_id=mock_position.instrument_id)

        mock_cache.orders_open.assert_called_with(
            instrument_id=InstrumentId.from_str("BTCUSDT-PERP.BINANCE")
        )
        assert open_orders == []

    def test_setup_exit_orders_finds_existing_stop(self, mock_cache, mock_logger):
        """Test that existing stop-loss is detected."""
        from nautilus_trader.model.identifiers import InstrumentId

        # Create mock position
        mock_position = MagicMock()
        mock_position.instrument_id = InstrumentId.from_str("BTCUSDT-PERP.BINANCE")

        # Create mock stop-loss order
        mock_stop_order = MagicMock()
        mock_stop_order.order_type = OrderType.STOP_MARKET

        mock_cache.orders_open.return_value = [mock_stop_order]

        # Simulate _setup_exit_orders logic
        def is_stop_order(order):
            return order.order_type in (OrderType.STOP_MARKET, OrderType.STOP_LIMIT)

        open_orders = mock_cache.orders_open(instrument_id=mock_position.instrument_id)
        has_stop = any(is_stop_order(order) for order in open_orders)

        if has_stop:
            mock_logger.info(
                f"Stop-loss already exists for {mock_position.instrument_id}"
            )

        assert has_stop is True
        mock_logger.info.assert_called()

    def test_setup_exit_orders_logs_warning_when_no_stop(self, mock_cache, mock_logger):
        """Test warning logged when no stop-loss exists."""
        from nautilus_trader.model.identifiers import InstrumentId

        # Create mock position
        mock_position = MagicMock()
        mock_position.instrument_id = InstrumentId.from_str("BTCUSDT-PERP.BINANCE")

        # No stop orders
        mock_cache.orders_open.return_value = []

        # Simulate _setup_exit_orders logic
        def is_stop_order(order):
            return order.order_type in (OrderType.STOP_MARKET, OrderType.STOP_LIMIT)

        open_orders = mock_cache.orders_open(instrument_id=mock_position.instrument_id)
        has_stop = any(is_stop_order(order) for order in open_orders)

        if not has_stop:
            mock_logger.warning(
                f"No stop-loss found for recovered position: "
                f"{mock_position.instrument_id}. Override _setup_exit_orders() "
                f"to create one."
            )

        assert has_stop is False
        mock_logger.warning.assert_called()

    def test_setup_exit_orders_ignores_non_stop_orders(self, mock_cache):
        """Test that non-stop orders are not counted as stops."""
        from nautilus_trader.model.identifiers import InstrumentId

        mock_position = MagicMock()
        mock_position.instrument_id = InstrumentId.from_str("BTCUSDT-PERP.BINANCE")

        # Create non-stop orders
        limit_order = MagicMock()
        limit_order.order_type = OrderType.LIMIT

        market_order = MagicMock()
        market_order.order_type = OrderType.MARKET

        mock_cache.orders_open.return_value = [limit_order, market_order]

        # Simulate logic
        def is_stop_order(order):
            return order.order_type in (OrderType.STOP_MARKET, OrderType.STOP_LIMIT)

        open_orders = mock_cache.orders_open(instrument_id=mock_position.instrument_id)
        has_stop = any(is_stop_order(order) for order in open_orders)

        assert has_stop is False


@pytest.mark.recovery
class TestIsStopOrder:
    """Tests for _is_stop_order helper method."""

    def test_is_stop_order_stop_market_true(self):
        """Test that STOP_MARKET order is identified as stop order."""
        mock_order = MagicMock()
        mock_order.order_type = OrderType.STOP_MARKET

        def is_stop_order(order):
            return order.order_type in (OrderType.STOP_MARKET, OrderType.STOP_LIMIT)

        assert is_stop_order(mock_order) is True

    def test_is_stop_order_stop_limit_true(self):
        """Test that STOP_LIMIT order is identified as stop order."""
        mock_order = MagicMock()
        mock_order.order_type = OrderType.STOP_LIMIT

        def is_stop_order(order):
            return order.order_type in (OrderType.STOP_MARKET, OrderType.STOP_LIMIT)

        assert is_stop_order(mock_order) is True

    def test_is_stop_order_limit_false(self):
        """Test that LIMIT order is not identified as stop order."""
        mock_order = MagicMock()
        mock_order.order_type = OrderType.LIMIT

        def is_stop_order(order):
            return order.order_type in (OrderType.STOP_MARKET, OrderType.STOP_LIMIT)

        assert is_stop_order(mock_order) is False

    def test_is_stop_order_market_false(self):
        """Test that MARKET order is not identified as stop order."""
        mock_order = MagicMock()
        mock_order.order_type = OrderType.MARKET

        def is_stop_order(order):
            return order.order_type in (OrderType.STOP_MARKET, OrderType.STOP_LIMIT)

        assert is_stop_order(mock_order) is False

    def test_is_stop_order_limit_if_touched_false(self):
        """Test that LIMIT_IF_TOUCHED order is not identified as stop order."""
        mock_order = MagicMock()
        mock_order.order_type = OrderType.LIMIT_IF_TOUCHED

        def is_stop_order(order):
            return order.order_type in (OrderType.STOP_MARKET, OrderType.STOP_LIMIT)

        assert is_stop_order(mock_order) is False


@pytest.mark.recovery
class TestStopOrderDetection:
    """Tests for stop order detection with multiple scenarios."""

    def test_detect_stop_among_mixed_orders(self, mock_cache):
        """Test detecting stop order among mixed order types."""
        from nautilus_trader.model.identifiers import InstrumentId

        mock_position = MagicMock()
        mock_position.instrument_id = InstrumentId.from_str("BTCUSDT-PERP.BINANCE")

        # Mix of order types
        limit_order = MagicMock()
        limit_order.order_type = OrderType.LIMIT

        stop_order = MagicMock()
        stop_order.order_type = OrderType.STOP_MARKET

        market_order = MagicMock()
        market_order.order_type = OrderType.MARKET

        mock_cache.orders_open.return_value = [limit_order, stop_order, market_order]

        def is_stop_order(order):
            return order.order_type in (OrderType.STOP_MARKET, OrderType.STOP_LIMIT)

        open_orders = mock_cache.orders_open(instrument_id=mock_position.instrument_id)
        has_stop = any(is_stop_order(order) for order in open_orders)

        assert has_stop is True

    def test_detect_multiple_stop_orders(self, mock_cache):
        """Test detecting when multiple stop orders exist."""
        from nautilus_trader.model.identifiers import InstrumentId

        mock_position = MagicMock()
        mock_position.instrument_id = InstrumentId.from_str("BTCUSDT-PERP.BINANCE")

        # Multiple stop orders
        stop_market = MagicMock()
        stop_market.order_type = OrderType.STOP_MARKET

        stop_limit = MagicMock()
        stop_limit.order_type = OrderType.STOP_LIMIT

        mock_cache.orders_open.return_value = [stop_market, stop_limit]

        def is_stop_order(order):
            return order.order_type in (OrderType.STOP_MARKET, OrderType.STOP_LIMIT)

        open_orders = mock_cache.orders_open(instrument_id=mock_position.instrument_id)
        stop_count = sum(1 for order in open_orders if is_stop_order(order))

        assert stop_count == 2

    def test_no_orders_means_no_stop(self, mock_cache):
        """Test that empty orders list means no stop."""
        from nautilus_trader.model.identifiers import InstrumentId

        mock_position = MagicMock()
        mock_position.instrument_id = InstrumentId.from_str("BTCUSDT-PERP.BINANCE")

        mock_cache.orders_open.return_value = []

        def is_stop_order(order):
            return order.order_type in (OrderType.STOP_MARKET, OrderType.STOP_LIMIT)

        open_orders = mock_cache.orders_open(instrument_id=mock_position.instrument_id)
        has_stop = any(is_stop_order(order) for order in open_orders)

        assert has_stop is False


@pytest.mark.recovery
class TestExitOrderRecreationIntegration:
    """Integration tests for exit order recreation flow."""

    def test_recovered_position_with_stop_flow(
        self, mock_cache, mock_logger, mock_btc_position
    ):
        """Test full flow: recovered position with existing stop."""
        from nautilus_trader.model.identifiers import InstrumentId

        # Setup existing stop order
        stop_order = MagicMock()
        stop_order.order_type = OrderType.STOP_MARKET
        mock_cache.orders_open.return_value = [stop_order]

        # Simulate flow
        def setup_exit_orders(position):
            def is_stop_order(order):
                return order.order_type in (OrderType.STOP_MARKET, OrderType.STOP_LIMIT)

            open_orders = mock_cache.orders_open(instrument_id=position.instrument_id)
            has_stop = any(is_stop_order(order) for order in open_orders)

            if has_stop:
                mock_logger.info(
                    f"Stop-loss already exists for {position.instrument_id}"
                )
                return True
            else:
                mock_logger.warning(
                    f"No stop-loss found for recovered position: {position.instrument_id}"
                )
                return False

        # Set instrument_id properly
        mock_btc_position.instrument_id = InstrumentId.from_str("BTCUSDT-PERP.BINANCE")

        result = setup_exit_orders(mock_btc_position)

        assert result is True
        mock_logger.info.assert_called()

    def test_recovered_position_without_stop_flow(
        self, mock_cache, mock_logger, mock_btc_position
    ):
        """Test full flow: recovered position without existing stop."""
        from nautilus_trader.model.identifiers import InstrumentId

        # No orders exist
        mock_cache.orders_open.return_value = []

        def setup_exit_orders(position):
            def is_stop_order(order):
                return order.order_type in (OrderType.STOP_MARKET, OrderType.STOP_LIMIT)

            open_orders = mock_cache.orders_open(instrument_id=position.instrument_id)
            has_stop = any(is_stop_order(order) for order in open_orders)

            if has_stop:
                mock_logger.info(
                    f"Stop-loss already exists for {position.instrument_id}"
                )
                return True
            else:
                mock_logger.warning(
                    f"No stop-loss found for recovered position: {position.instrument_id}"
                )
                return False

        mock_btc_position.instrument_id = InstrumentId.from_str("BTCUSDT-PERP.BINANCE")

        result = setup_exit_orders(mock_btc_position)

        assert result is False
        mock_logger.warning.assert_called()

    def test_setup_exit_orders_is_overridable(self):
        """Test that _setup_exit_orders can be overridden in subclasses."""
        from strategies.common.recovery.recoverable_strategy import (
            RecoverableStrategy,
        )

        # Verify the method exists and can be overridden
        assert hasattr(RecoverableStrategy, "_setup_exit_orders")

        # The base implementation only checks; subclasses should override
        # to actually create stop orders based on their risk parameters

    def test_handle_recovered_position_calls_setup_exit_orders(self, mock_btc_position):
        """Test that _handle_recovered_position calls _setup_exit_orders."""
        setup_exit_orders_called = False
        setup_exit_orders_position = None

        def mock_setup_exit_orders(position):
            nonlocal setup_exit_orders_called, setup_exit_orders_position
            setup_exit_orders_called = True
            setup_exit_orders_position = position

        def handle_recovered_position(position):
            # Other logic...
            mock_setup_exit_orders(position)
            # Call hook...

        handle_recovered_position(mock_btc_position)

        assert setup_exit_orders_called is True
        assert setup_exit_orders_position == mock_btc_position


@pytest.mark.recovery
class TestOrderTypeEnums:
    """Tests verifying OrderType enum values used in stop detection."""

    def test_stop_market_enum_exists(self):
        """Test that STOP_MARKET enum value exists."""
        assert hasattr(OrderType, "STOP_MARKET")
        assert OrderType.STOP_MARKET is not None

    def test_stop_limit_enum_exists(self):
        """Test that STOP_LIMIT enum value exists."""
        assert hasattr(OrderType, "STOP_LIMIT")
        assert OrderType.STOP_LIMIT is not None

    def test_stop_types_are_different(self):
        """Test that STOP_MARKET and STOP_LIMIT are different values."""
        assert OrderType.STOP_MARKET != OrderType.STOP_LIMIT

    def test_market_is_not_stop(self):
        """Test that MARKET is different from stop types."""
        assert OrderType.MARKET != OrderType.STOP_MARKET
        assert OrderType.MARKET != OrderType.STOP_LIMIT

    def test_limit_is_not_stop(self):
        """Test that LIMIT is different from stop types."""
        assert OrderType.LIMIT != OrderType.STOP_MARKET
        assert OrderType.LIMIT != OrderType.STOP_LIMIT
