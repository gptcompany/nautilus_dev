"""Integration test for strategy recovery (FR-002).

Tests that RecoverableStrategy correctly:
- Starts with recovered positions from cache
- Requests historical warmup data
- Calls on_warmup_complete() hook
- Blocks trading during warmup (is_warming_up)
- Reports is_ready after warmup completes
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from strategies.common.recovery.config import RecoveryConfig
from strategies.common.recovery.models import RecoveryStatus
from strategies.common.recovery.recoverable_strategy import (
    RecoverableStrategy,
    RecoverableStrategyConfig,
)


@pytest.fixture
def mock_instrument():
    """Create a mock instrument for testing."""
    instrument = MagicMock()
    instrument.id.value = "BTCUSDT-PERP.BINANCE"
    return instrument


@pytest.fixture
def mock_position():
    """Create a mock open position for recovery testing."""
    position = MagicMock()
    position.instrument_id.value = "BTCUSDT-PERP.BINANCE"
    position.side.value = "LONG"
    position.quantity.as_decimal.return_value = Decimal("1.5")
    position.avg_px_open = Decimal("42000.00")
    position.is_open = True
    return position


@pytest.fixture
def mock_bar():
    """Create a mock bar for warmup testing."""
    bar = MagicMock()
    bar.ts_event = 1704067200000000000  # 2024-01-01 00:00:00 UTC
    bar.close = Decimal("42500.00")
    bar.open = Decimal("42000.00")
    bar.high = Decimal("42700.00")
    bar.low = Decimal("41800.00")
    bar.volume = Decimal("100.0")
    return bar


@pytest.fixture
def strategy_config():
    """Create a RecoverableStrategyConfig for testing."""
    return RecoverableStrategyConfig(
        instrument_id="BTCUSDT-PERP.BINANCE",
        bar_type="BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL",
        recovery=RecoveryConfig(
            trader_id="TESTER-001",
            recovery_enabled=True,
            warmup_lookback_days=2,
            startup_delay_secs=10.0,
            max_recovery_time_secs=30.0,
        ),
    )


@pytest.fixture
def strategy_config_disabled():
    """Create a RecoverableStrategyConfig with recovery disabled."""
    return RecoverableStrategyConfig(
        instrument_id="BTCUSDT-PERP.BINANCE",
        bar_type="BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL",
        recovery=RecoveryConfig(
            trader_id="TESTER-001",
            recovery_enabled=False,
            warmup_lookback_days=2,
        ),
    )


class ConcreteRecoverableStrategy(RecoverableStrategy):
    """Concrete subclass for testing that tracks hook calls.

    Named 'Concrete...' instead of 'Test...' to avoid pytest collection warning.
    """

    def __init__(self, config: RecoverableStrategyConfig) -> None:
        super().__init__(config)
        self.position_recovered_calls: list = []
        self.historical_data_calls: list = []
        self.warmup_complete_called: bool = False

    def on_position_recovered(self, position) -> None:
        """Track position recovered calls."""
        self.position_recovered_calls.append(position)

    def on_historical_data(self, bar) -> None:
        """Track historical data processing calls."""
        self.historical_data_calls.append(bar)

    def on_warmup_complete(self) -> None:
        """Track warmup complete calls."""
        self.warmup_complete_called = True


def create_strategy_with_mocks(
    strategy_config,
    mock_cache,
    mock_clock,
):
    """Helper to create strategy with mocked dependencies."""
    strategy = ConcreteRecoverableStrategy(strategy_config)

    # Patch cache and clock properties using object.__setattr__ for Cython objects
    # We need to patch at the class level for properties
    return strategy, mock_cache, mock_clock


@pytest.mark.integration
@pytest.mark.recovery
class TestStrategyRecovery:
    """Integration tests for RecoverableStrategy (FR-002)."""

    def test_strategy_starts_with_recovered_position(
        self,
        mock_cache,
        mock_clock,
        mock_instrument,
        mock_position,
        strategy_config,
    ):
        """Test strategy detects and processes recovered position from cache."""
        # Setup
        mock_cache.instrument.return_value = mock_instrument
        mock_cache.positions.return_value = [mock_position]
        mock_cache.orders_open.return_value = []

        strategy = ConcreteRecoverableStrategy(strategy_config)

        # Patch the properties at class level
        with patch.object(
            type(strategy), "cache", new_callable=PropertyMock
        ) as cache_prop:
            with patch.object(
                type(strategy), "clock", new_callable=PropertyMock
            ) as clock_prop:
                with patch.object(
                    type(strategy), "log", new_callable=PropertyMock
                ) as log_prop:
                    cache_prop.return_value = mock_cache
                    clock_prop.return_value = mock_clock
                    log_prop.return_value = MagicMock()

                    # Patch request_bars and subscribe_bars
                    with patch.object(strategy, "request_bars"):
                        with patch.object(strategy, "subscribe_bars"):
                            strategy.on_start()

                    # Verify position was recovered
                    assert strategy.recovered_positions_count == 1
                    assert len(strategy.position_recovered_calls) == 1
                    assert strategy.position_recovered_calls[0] == mock_position
                    assert strategy.recovery_state.positions_recovered == 1

    def test_strategy_requests_warmup_data(
        self,
        mock_cache,
        mock_clock,
        mock_instrument,
        strategy_config,
    ):
        """Test strategy requests historical bars for indicator warmup."""
        # Setup
        mock_cache.instrument.return_value = mock_instrument
        mock_cache.positions.return_value = []

        strategy = ConcreteRecoverableStrategy(strategy_config)
        request_bars_mock = MagicMock()

        with patch.object(
            type(strategy), "cache", new_callable=PropertyMock
        ) as cache_prop:
            with patch.object(
                type(strategy), "clock", new_callable=PropertyMock
            ) as clock_prop:
                with patch.object(
                    type(strategy), "log", new_callable=PropertyMock
                ) as log_prop:
                    cache_prop.return_value = mock_cache
                    clock_prop.return_value = mock_clock
                    log_prop.return_value = MagicMock()

                    with patch.object(strategy, "request_bars", request_bars_mock):
                        with patch.object(strategy, "subscribe_bars"):
                            strategy.on_start()

                    # Verify request_bars was called with correct parameters
                    assert request_bars_mock.called
                    call_kwargs = request_bars_mock.call_args
                    assert call_kwargs.kwargs["bar_type"] == strategy.bar_type

                    # Verify start time is approximately warmup_lookback_days ago
                    expected_start = mock_clock.utc_now.return_value - timedelta(days=2)
                    assert call_kwargs.kwargs["start"] == expected_start

    def test_warmup_data_processed_and_complete_called(
        self,
        mock_cache,
        mock_clock,
        mock_instrument,
        mock_bar,
        strategy_config,
    ):
        """Test historical data is processed and on_warmup_complete is called."""
        # Setup
        mock_cache.instrument.return_value = mock_instrument
        mock_cache.positions.return_value = []

        strategy = ConcreteRecoverableStrategy(strategy_config)

        # Create multiple warmup bars
        bars = []
        for i in range(5):
            bar = MagicMock()
            bar.ts_event = 1704067200000000000 + (i * 60_000_000_000)  # 1 min apart
            bars.append(bar)

        with patch.object(
            type(strategy), "cache", new_callable=PropertyMock
        ) as cache_prop:
            with patch.object(
                type(strategy), "clock", new_callable=PropertyMock
            ) as clock_prop:
                with patch.object(
                    type(strategy), "log", new_callable=PropertyMock
                ) as log_prop:
                    cache_prop.return_value = mock_cache
                    clock_prop.return_value = mock_clock
                    log_prop.return_value = MagicMock()

                    # Start strategy (with patched request_bars)
                    with patch.object(strategy, "request_bars"):
                        with patch.object(strategy, "subscribe_bars"):
                            strategy.on_start()

                    # Simulate warmup data callback
                    strategy._on_warmup_data_received(bars)

                    # Verify all bars were processed
                    assert len(strategy.historical_data_calls) == 5
                    assert strategy._warmup_bars_processed == 5

                    # Verify on_warmup_complete was called
                    assert strategy.warmup_complete_called

    def test_strategy_is_ready_after_warmup(
        self,
        mock_cache,
        mock_clock,
        mock_instrument,
        strategy_config,
    ):
        """Test strategy is_ready returns True after warmup completes."""
        # Setup
        mock_cache.instrument.return_value = mock_instrument
        mock_cache.positions.return_value = []

        strategy = ConcreteRecoverableStrategy(strategy_config)

        with patch.object(
            type(strategy), "cache", new_callable=PropertyMock
        ) as cache_prop:
            with patch.object(
                type(strategy), "clock", new_callable=PropertyMock
            ) as clock_prop:
                with patch.object(
                    type(strategy), "log", new_callable=PropertyMock
                ) as log_prop:
                    cache_prop.return_value = mock_cache
                    clock_prop.return_value = mock_clock
                    log_prop.return_value = MagicMock()

                    # Start strategy
                    with patch.object(strategy, "request_bars"):
                        with patch.object(strategy, "subscribe_bars"):
                            strategy.on_start()

                    # Before warmup complete
                    assert strategy.is_warming_up
                    assert not strategy.is_ready

                    # Simulate warmup completion
                    strategy._on_warmup_data_received(
                        [MagicMock(ts_event=1704067200000000000)]
                    )

                    # After warmup complete
                    assert not strategy.is_warming_up
                    assert strategy.is_ready
                    assert strategy.recovery_state.status == RecoveryStatus.COMPLETED

    def test_strategy_blocks_trading_during_warmup(
        self,
        mock_cache,
        mock_clock,
        mock_instrument,
        strategy_config,
    ):
        """Test is_warming_up is True during warmup phase."""
        # Setup
        mock_cache.instrument.return_value = mock_instrument
        mock_cache.positions.return_value = []

        strategy = ConcreteRecoverableStrategy(strategy_config)

        with patch.object(
            type(strategy), "cache", new_callable=PropertyMock
        ) as cache_prop:
            with patch.object(
                type(strategy), "clock", new_callable=PropertyMock
            ) as clock_prop:
                with patch.object(
                    type(strategy), "log", new_callable=PropertyMock
                ) as log_prop:
                    cache_prop.return_value = mock_cache
                    clock_prop.return_value = mock_clock
                    log_prop.return_value = MagicMock()

                    # Start strategy
                    with patch.object(strategy, "request_bars"):
                        with patch.object(strategy, "subscribe_bars"):
                            strategy.on_start()

                    # Strategy should be warming up (blocking trades)
                    assert strategy.is_warming_up
                    assert not strategy._warmup_complete
                    assert strategy.recovery_state.status == RecoveryStatus.IN_PROGRESS

    def test_recovery_state_transitions(
        self,
        mock_cache,
        mock_clock,
        mock_instrument,
        mock_position,
        strategy_config,
    ):
        """Test recovery state transitions through lifecycle."""
        # Setup
        mock_cache.instrument.return_value = mock_instrument
        mock_cache.positions.return_value = [mock_position]
        mock_cache.orders_open.return_value = []

        strategy = ConcreteRecoverableStrategy(strategy_config)

        # Initial state (before on_start)
        assert strategy.recovery_state.status == RecoveryStatus.PENDING

        with patch.object(
            type(strategy), "cache", new_callable=PropertyMock
        ) as cache_prop:
            with patch.object(
                type(strategy), "clock", new_callable=PropertyMock
            ) as clock_prop:
                with patch.object(
                    type(strategy), "log", new_callable=PropertyMock
                ) as log_prop:
                    cache_prop.return_value = mock_cache
                    clock_prop.return_value = mock_clock
                    log_prop.return_value = MagicMock()

                    # Start strategy
                    with patch.object(strategy, "request_bars"):
                        with patch.object(strategy, "subscribe_bars"):
                            strategy.on_start()

                    # After on_start (in progress)
                    assert strategy.recovery_state.status == RecoveryStatus.IN_PROGRESS
                    assert strategy.recovery_state.positions_recovered == 1
                    assert not strategy.recovery_state.indicators_warmed

                    # After warmup complete
                    strategy._on_warmup_data_received(
                        [MagicMock(ts_event=1704067200000000000)]
                    )

                    # Final state
                    assert strategy.recovery_state.status == RecoveryStatus.COMPLETED
                    assert strategy.recovery_state.indicators_warmed
                    assert strategy.recovery_state.orders_reconciled
                    assert strategy.recovery_state.is_complete

    def test_empty_warmup_data_still_completes(
        self,
        mock_cache,
        mock_clock,
        mock_instrument,
        strategy_config,
    ):
        """Test warmup completes even with no historical data."""
        # Setup
        mock_cache.instrument.return_value = mock_instrument
        mock_cache.positions.return_value = []

        strategy = ConcreteRecoverableStrategy(strategy_config)

        with patch.object(
            type(strategy), "cache", new_callable=PropertyMock
        ) as cache_prop:
            with patch.object(
                type(strategy), "clock", new_callable=PropertyMock
            ) as clock_prop:
                with patch.object(
                    type(strategy), "log", new_callable=PropertyMock
                ) as log_prop:
                    cache_prop.return_value = mock_cache
                    clock_prop.return_value = mock_clock
                    log_prop.return_value = MagicMock()

                    # Start strategy
                    with patch.object(strategy, "request_bars"):
                        with patch.object(strategy, "subscribe_bars"):
                            strategy.on_start()

                    # Simulate empty warmup data
                    strategy._on_warmup_data_received([])

                    # Should still complete warmup
                    assert strategy.warmup_complete_called
                    assert strategy.is_ready
                    assert strategy._warmup_bars_processed == 0

    def test_recovery_disabled_skips_position_detection(
        self,
        mock_cache,
        mock_clock,
        mock_instrument,
        mock_position,
        strategy_config_disabled,
    ):
        """Test position detection is skipped when recovery disabled."""
        # Setup
        mock_cache.instrument.return_value = mock_instrument
        mock_cache.positions.return_value = [mock_position]

        strategy = ConcreteRecoverableStrategy(strategy_config_disabled)

        with patch.object(
            type(strategy), "cache", new_callable=PropertyMock
        ) as cache_prop:
            with patch.object(
                type(strategy), "clock", new_callable=PropertyMock
            ) as clock_prop:
                with patch.object(
                    type(strategy), "log", new_callable=PropertyMock
                ) as log_prop:
                    cache_prop.return_value = mock_cache
                    clock_prop.return_value = mock_clock
                    log_prop.return_value = MagicMock()

                    # Start strategy
                    with patch.object(strategy, "request_bars"):
                        with patch.object(strategy, "subscribe_bars"):
                            strategy.on_start()

                    # Position detection should be skipped
                    assert strategy.recovered_positions_count == 0
                    assert len(strategy.position_recovered_calls) == 0

    def test_multiple_positions_recovered(
        self,
        mock_cache,
        mock_clock,
        mock_instrument,
        strategy_config,
    ):
        """Test multiple positions are recovered correctly."""
        # Setup multiple positions
        positions = []
        for i, qty in enumerate([Decimal("1.0"), Decimal("2.0")]):
            pos = MagicMock()
            pos.instrument_id = mock_instrument.id
            pos.instrument_id.value = "BTCUSDT-PERP.BINANCE"
            pos.side.value = "LONG"
            pos.quantity = qty
            pos.avg_px_open = Decimal("42000.00")
            pos.is_open = True
            positions.append(pos)

        mock_cache.instrument.return_value = mock_instrument
        mock_cache.positions.return_value = positions
        mock_cache.orders_open.return_value = []

        strategy = ConcreteRecoverableStrategy(strategy_config)

        with patch.object(
            type(strategy), "cache", new_callable=PropertyMock
        ) as cache_prop:
            with patch.object(
                type(strategy), "clock", new_callable=PropertyMock
            ) as clock_prop:
                with patch.object(
                    type(strategy), "log", new_callable=PropertyMock
                ) as log_prop:
                    cache_prop.return_value = mock_cache
                    clock_prop.return_value = mock_clock
                    log_prop.return_value = MagicMock()

                    # Start strategy
                    with patch.object(strategy, "request_bars"):
                        with patch.object(strategy, "subscribe_bars"):
                            strategy.on_start()

                    # Both positions should be recovered
                    assert strategy.recovered_positions_count == 2
                    assert len(strategy.position_recovered_calls) == 2
                    assert strategy.recovery_state.positions_recovered == 2

    def test_closed_positions_not_recovered(
        self,
        mock_cache,
        mock_clock,
        mock_instrument,
        strategy_config,
    ):
        """Test closed positions are not processed as recovered."""
        # Setup closed position
        closed_position = MagicMock()
        closed_position.instrument_id.value = "BTCUSDT-PERP.BINANCE"
        closed_position.is_open = False

        mock_cache.instrument.return_value = mock_instrument
        mock_cache.positions.return_value = [closed_position]
        mock_cache.orders_open.return_value = []

        strategy = ConcreteRecoverableStrategy(strategy_config)

        with patch.object(
            type(strategy), "cache", new_callable=PropertyMock
        ) as cache_prop:
            with patch.object(
                type(strategy), "clock", new_callable=PropertyMock
            ) as clock_prop:
                with patch.object(
                    type(strategy), "log", new_callable=PropertyMock
                ) as log_prop:
                    cache_prop.return_value = mock_cache
                    clock_prop.return_value = mock_clock
                    log_prop.return_value = MagicMock()

                    # Start strategy
                    with patch.object(strategy, "request_bars"):
                        with patch.object(strategy, "subscribe_bars"):
                            strategy.on_start()

                    # Closed position should not be recovered
                    assert strategy.recovered_positions_count == 0
                    assert len(strategy.position_recovered_calls) == 0

    def test_instrument_not_found_stops_strategy(
        self,
        mock_cache,
        mock_clock,
        strategy_config,
    ):
        """Test strategy stops if instrument not found in cache."""
        # Setup
        mock_cache.instrument.return_value = None

        strategy = ConcreteRecoverableStrategy(strategy_config)
        stop_mock = MagicMock()

        with patch.object(
            type(strategy), "cache", new_callable=PropertyMock
        ) as cache_prop:
            with patch.object(
                type(strategy), "clock", new_callable=PropertyMock
            ) as clock_prop:
                with patch.object(
                    type(strategy), "log", new_callable=PropertyMock
                ) as log_prop:
                    cache_prop.return_value = mock_cache
                    clock_prop.return_value = mock_clock
                    log_prop.return_value = MagicMock()

                    with patch.object(strategy, "stop", stop_mock):
                        strategy.on_start()

                    # Strategy should call stop due to missing instrument
                    assert stop_mock.called

    def test_warmup_bars_sorted_by_timestamp(
        self,
        mock_cache,
        mock_clock,
        mock_instrument,
        strategy_config,
    ):
        """Test warmup bars are processed in chronological order."""
        # Setup
        mock_cache.instrument.return_value = mock_instrument
        mock_cache.positions.return_value = []

        strategy = ConcreteRecoverableStrategy(strategy_config)

        # Create bars in reverse order
        bars = []
        timestamps = [1704067260000000000, 1704067200000000000, 1704067320000000000]
        for ts in timestamps:
            bar = MagicMock()
            bar.ts_event = ts
            bars.append(bar)

        with patch.object(
            type(strategy), "cache", new_callable=PropertyMock
        ) as cache_prop:
            with patch.object(
                type(strategy), "clock", new_callable=PropertyMock
            ) as clock_prop:
                with patch.object(
                    type(strategy), "log", new_callable=PropertyMock
                ) as log_prop:
                    cache_prop.return_value = mock_cache
                    clock_prop.return_value = mock_clock
                    log_prop.return_value = MagicMock()

                    # Start strategy
                    with patch.object(strategy, "request_bars"):
                        with patch.object(strategy, "subscribe_bars"):
                            strategy.on_start()

                    # Process warmup data
                    strategy._on_warmup_data_received(bars)

                    # Verify bars were processed in sorted order (oldest first)
                    processed_timestamps = [
                        b.ts_event for b in strategy.historical_data_calls
                    ]
                    assert processed_timestamps == sorted(timestamps)
