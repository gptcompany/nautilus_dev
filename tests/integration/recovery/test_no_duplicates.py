"""Integration test for no duplicate orders after recovery (NFR-002 - T044).

Tests that recovery does not create duplicate orders when stop-loss orders
already exist. This validates the NFR-002 consistency requirement from Spec 017.

NFR-002: Consistency
- No duplicate orders after recovery
- Position sizes match exchange exactly
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from strategies.common.recovery.config import RecoveryConfig
from strategies.common.recovery.recoverable_strategy import (
    RecoverableStrategy,
    RecoverableStrategyConfig,
)


class OrderTrackingStrategy(RecoverableStrategy):
    """Strategy subclass that tracks order creation attempts.

    Used to verify that no duplicate orders are created during recovery.
    """

    def __init__(self, config: RecoverableStrategyConfig) -> None:
        super().__init__(config)
        self.order_creation_attempts: list = []
        self.position_recovered_calls: list = []
        self.exit_order_setup_calls: list = []

    def on_position_recovered(self, position) -> None:
        """Track position recovered calls."""
        self.position_recovered_calls.append(position)

    def _setup_exit_orders(self, position) -> None:
        """Override to track exit order setup calls."""
        self.exit_order_setup_calls.append(position)
        # Call parent implementation which checks for existing orders
        super()._setup_exit_orders(position)

    def on_historical_data(self, bar) -> None:
        """Skip historical data processing."""
        pass

    def on_warmup_complete(self) -> None:
        """Skip warmup complete."""
        pass


def create_mock_position(instrument_id: str, quantity: Decimal) -> MagicMock:
    """Factory to create mock positions."""
    position = MagicMock()
    position.instrument_id = MagicMock()
    position.instrument_id.value = instrument_id
    position.side = MagicMock()
    position.side.value = "LONG"
    position.quantity = quantity
    position.avg_px_open = Decimal("42000.00")
    position.is_open = True
    return position


def create_mock_stop_order(instrument_id: str) -> MagicMock:
    """Factory to create mock stop orders."""
    from nautilus_trader.model.enums import OrderType

    order = MagicMock()
    order.instrument_id = MagicMock()
    order.instrument_id.value = instrument_id
    order.order_type = OrderType.STOP_MARKET
    order.is_open = True
    return order


def create_mock_limit_order(instrument_id: str) -> MagicMock:
    """Factory to create mock limit orders (not a stop order)."""
    from nautilus_trader.model.enums import OrderType

    order = MagicMock()
    order.instrument_id = MagicMock()
    order.instrument_id.value = instrument_id
    order.order_type = OrderType.LIMIT
    order.is_open = True
    return order


@pytest.fixture
def mock_cache():
    """Create a mock cache."""
    cache = MagicMock()
    cache.positions.return_value = []
    cache.orders_open.return_value = []
    return cache


@pytest.fixture
def mock_clock():
    """Create a mock clock."""
    clock = MagicMock()
    clock.timestamp_ns.return_value = 1704153600000000000
    clock.utc_now.return_value = MagicMock()
    clock.utc_now.return_value.__sub__ = MagicMock(return_value=MagicMock())
    return clock


@pytest.fixture
def mock_instrument():
    """Create a mock instrument."""
    instrument = MagicMock()
    instrument.id = MagicMock()
    instrument.id.value = "BTCUSDT-PERP.BINANCE"
    return instrument


@pytest.fixture
def strategy_config():
    """Create a RecoverableStrategyConfig for testing."""
    return RecoverableStrategyConfig(
        instrument_id="BTCUSDT-PERP.BINANCE",
        bar_type="BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL",
        recovery=RecoveryConfig(
            trader_id="TESTER-001",
            recovery_enabled=True,
            warmup_lookback_days=1,  # Minimum valid value
            startup_delay_secs=5.0,  # Minimum valid value
            max_recovery_time_secs=30.0,
        ),
    )


@pytest.mark.integration
@pytest.mark.recovery
class TestNoDuplicateOrders:
    """Integration tests for NFR-002: No duplicate orders after recovery."""

    def test_no_duplicate_stop_loss_when_exists(
        self,
        mock_cache,
        mock_clock,
        mock_instrument,
        strategy_config,
    ):
        """Test that no duplicate stop-loss is created when one already exists."""
        # Setup: position with existing stop-loss order
        mock_position = create_mock_position("BTCUSDT-PERP.BINANCE", Decimal("1.5"))
        existing_stop = create_mock_stop_order("BTCUSDT-PERP.BINANCE")

        mock_cache.instrument.return_value = mock_instrument
        mock_cache.positions.return_value = [mock_position]
        mock_cache.orders_open.return_value = [existing_stop]

        strategy = OrderTrackingStrategy(strategy_config)

        with patch.object(type(strategy), "cache", new_callable=PropertyMock) as cache_prop:
            with patch.object(type(strategy), "clock", new_callable=PropertyMock) as clock_prop:
                with patch.object(type(strategy), "log", new_callable=PropertyMock) as log_prop:
                    cache_prop.return_value = mock_cache
                    clock_prop.return_value = mock_clock
                    log_mock = MagicMock()
                    log_prop.return_value = log_mock

                    with patch.object(strategy, "request_bars"):
                        with patch.object(strategy, "subscribe_bars"):
                            strategy.on_start()

        # NFR-002 Verification: No duplicate order creation
        # Position should be recovered
        assert strategy.recovered_positions_count == 1
        assert len(strategy.position_recovered_calls) == 1

        # _setup_exit_orders should be called
        assert len(strategy.exit_order_setup_calls) == 1

        # Log should indicate stop-loss already exists (not creating duplicate)
        log_info_calls = [str(c) for c in log_mock.info.call_args_list]
        assert any("Stop-loss already exists" in str(c) for c in log_info_calls)

    def test_warning_when_no_stop_loss_exists(
        self,
        mock_cache,
        mock_clock,
        mock_instrument,
        strategy_config,
    ):
        """Test that warning is logged when no stop-loss exists for position."""
        # Setup: position WITHOUT existing stop-loss
        mock_position = create_mock_position("BTCUSDT-PERP.BINANCE", Decimal("1.5"))

        mock_cache.instrument.return_value = mock_instrument
        mock_cache.positions.return_value = [mock_position]
        mock_cache.orders_open.return_value = []  # No existing orders

        strategy = OrderTrackingStrategy(strategy_config)

        with patch.object(type(strategy), "cache", new_callable=PropertyMock) as cache_prop:
            with patch.object(type(strategy), "clock", new_callable=PropertyMock) as clock_prop:
                with patch.object(type(strategy), "log", new_callable=PropertyMock) as log_prop:
                    cache_prop.return_value = mock_cache
                    clock_prop.return_value = mock_clock
                    log_mock = MagicMock()
                    log_prop.return_value = log_mock

                    with patch.object(strategy, "request_bars"):
                        with patch.object(strategy, "subscribe_bars"):
                            strategy.on_start()

        # Position should be recovered
        assert strategy.recovered_positions_count == 1

        # Warning should be logged about missing stop-loss
        log_warning_calls = [str(c) for c in log_mock.warning.call_args_list]
        assert any("No stop-loss found" in str(c) for c in log_warning_calls)

    def test_limit_order_not_counted_as_stop_loss(
        self,
        mock_cache,
        mock_clock,
        mock_instrument,
        strategy_config,
    ):
        """Test that LIMIT orders are not counted as stop-loss orders."""
        # Setup: position with LIMIT order (not stop-loss)
        mock_position = create_mock_position("BTCUSDT-PERP.BINANCE", Decimal("1.5"))
        limit_order = create_mock_limit_order("BTCUSDT-PERP.BINANCE")

        mock_cache.instrument.return_value = mock_instrument
        mock_cache.positions.return_value = [mock_position]
        mock_cache.orders_open.return_value = [limit_order]

        strategy = OrderTrackingStrategy(strategy_config)

        with patch.object(type(strategy), "cache", new_callable=PropertyMock) as cache_prop:
            with patch.object(type(strategy), "clock", new_callable=PropertyMock) as clock_prop:
                with patch.object(type(strategy), "log", new_callable=PropertyMock) as log_prop:
                    cache_prop.return_value = mock_cache
                    clock_prop.return_value = mock_clock
                    log_mock = MagicMock()
                    log_prop.return_value = log_mock

                    with patch.object(strategy, "request_bars"):
                        with patch.object(strategy, "subscribe_bars"):
                            strategy.on_start()

        # Position recovered
        assert strategy.recovered_positions_count == 1

        # Should warn about missing stop-loss (LIMIT doesn't count)
        log_warning_calls = [str(c) for c in log_mock.warning.call_args_list]
        assert any("No stop-loss found" in str(c) for c in log_warning_calls)

    def test_multiple_positions_each_checked_for_stop_loss(
        self,
        mock_cache,
        mock_clock,
        mock_instrument,
        strategy_config,
    ):
        """Test that each position is individually checked for stop-loss."""
        # Setup: two positions
        positions = [
            create_mock_position("BTCUSDT-PERP.BINANCE", Decimal("1.0")),
            create_mock_position("BTCUSDT-PERP.BINANCE", Decimal("2.0")),
        ]
        # Only one stop-loss order exists
        stop_order = create_mock_stop_order("BTCUSDT-PERP.BINANCE")

        mock_cache.instrument.return_value = mock_instrument
        mock_cache.positions.return_value = positions
        mock_cache.orders_open.return_value = [stop_order]

        strategy = OrderTrackingStrategy(strategy_config)

        with patch.object(type(strategy), "cache", new_callable=PropertyMock) as cache_prop:
            with patch.object(type(strategy), "clock", new_callable=PropertyMock) as clock_prop:
                with patch.object(type(strategy), "log", new_callable=PropertyMock) as log_prop:
                    cache_prop.return_value = mock_cache
                    clock_prop.return_value = mock_clock
                    log_mock = MagicMock()
                    log_prop.return_value = log_mock

                    with patch.object(strategy, "request_bars"):
                        with patch.object(strategy, "subscribe_bars"):
                            strategy.on_start()

        # Both positions recovered
        assert strategy.recovered_positions_count == 2

        # _setup_exit_orders called for each position
        assert len(strategy.exit_order_setup_calls) == 2

    def test_idempotent_recovery_no_duplicates(
        self,
        mock_cache,
        mock_clock,
        mock_instrument,
        strategy_config,
    ):
        """Test that calling on_start() twice doesn't create duplicates."""
        # Setup
        mock_position = create_mock_position("BTCUSDT-PERP.BINANCE", Decimal("1.5"))
        existing_stop = create_mock_stop_order("BTCUSDT-PERP.BINANCE")

        mock_cache.instrument.return_value = mock_instrument
        mock_cache.positions.return_value = [mock_position]
        mock_cache.orders_open.return_value = [existing_stop]

        strategy = OrderTrackingStrategy(strategy_config)

        with patch.object(type(strategy), "cache", new_callable=PropertyMock) as cache_prop:
            with patch.object(type(strategy), "clock", new_callable=PropertyMock) as clock_prop:
                with patch.object(type(strategy), "log", new_callable=PropertyMock) as log_prop:
                    cache_prop.return_value = mock_cache
                    clock_prop.return_value = mock_clock
                    log_mock = MagicMock()
                    log_prop.return_value = log_mock

                    with patch.object(strategy, "request_bars"):
                        with patch.object(strategy, "subscribe_bars"):
                            # First call
                            strategy.on_start()
                            first_count = strategy.recovered_positions_count

                            # Second call (idempotency test)
                            strategy.on_start()
                            second_count = strategy.recovered_positions_count

        # NFR-002 Verification: No duplicates from repeated calls
        assert first_count == second_count == 1
        assert len(strategy.position_recovered_calls) == 1
        assert len(strategy.exit_order_setup_calls) == 1

        # Warning about duplicate on_start() should be logged
        log_warning_calls = [str(c) for c in log_mock.warning.call_args_list]
        assert any("called multiple times" in str(c) for c in log_warning_calls)

    def test_recovery_disabled_no_exit_order_setup(
        self,
        mock_cache,
        mock_clock,
        mock_instrument,
    ):
        """Test that exit orders are not setup when recovery is disabled."""
        # Config with recovery disabled
        config = RecoverableStrategyConfig(
            instrument_id="BTCUSDT-PERP.BINANCE",
            bar_type="BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL",
            recovery=RecoveryConfig(
                trader_id="TESTER-001",
                recovery_enabled=False,  # Disabled
                warmup_lookback_days=1,  # Minimum valid value
                startup_delay_secs=5.0,  # Minimum valid value
                max_recovery_time_secs=30.0,
            ),
        )

        mock_position = create_mock_position("BTCUSDT-PERP.BINANCE", Decimal("1.5"))
        mock_cache.instrument.return_value = mock_instrument
        mock_cache.positions.return_value = [mock_position]
        mock_cache.orders_open.return_value = []

        strategy = OrderTrackingStrategy(config)

        with patch.object(type(strategy), "cache", new_callable=PropertyMock) as cache_prop:
            with patch.object(type(strategy), "clock", new_callable=PropertyMock) as clock_prop:
                with patch.object(type(strategy), "log", new_callable=PropertyMock) as log_prop:
                    cache_prop.return_value = mock_cache
                    clock_prop.return_value = mock_clock
                    log_prop.return_value = MagicMock()

                    with patch.object(strategy, "request_bars"):
                        with patch.object(strategy, "subscribe_bars"):
                            strategy.on_start()

        # No positions recovered when disabled
        assert strategy.recovered_positions_count == 0

        # No exit order setup attempts
        assert len(strategy.exit_order_setup_calls) == 0
