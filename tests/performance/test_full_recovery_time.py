"""Performance test for full recovery time < 30s (NFR-001 - T043).

Tests that full state recovery (positions + warmup) completes within
the p95 target of 30 seconds. This validates the NFR-001 requirement
from Spec 017.

NFR-001: Recovery Time
- Position recovery < 5 seconds (p95)
- Full state recovery < 30 seconds (p95)
"""

from __future__ import annotations

import time
from decimal import Decimal
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from strategies.common.recovery.config import RecoveryConfig
from strategies.common.recovery.models import RecoveryStatus
from strategies.common.recovery.recoverable_strategy import (
    RecoverableStrategy,
    RecoverableStrategyConfig,
)


# NFR-001 target: Full state recovery < 30 seconds (p95)
FULL_RECOVERY_TARGET_SECS = 30.0


class ConcreteRecoverableStrategy(RecoverableStrategy):
    """Concrete subclass for performance testing."""

    def __init__(self, config: RecoverableStrategyConfig) -> None:
        super().__init__(config)
        self.position_recovered_calls: list = []
        self.historical_data_calls: list = []
        self.warmup_complete_called: bool = False

    def on_position_recovered(self, position) -> None:
        """Track position recovered calls."""
        self.position_recovered_calls.append(position)

    def on_historical_data(self, bar) -> None:
        """Track historical data processing."""
        self.historical_data_calls.append(bar)

    def on_warmup_complete(self) -> None:
        """Track warmup completion."""
        self.warmup_complete_called = True


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


def create_mock_bar(ts_offset: int) -> MagicMock:
    """Factory to create mock bars with offset timestamp."""
    bar = MagicMock()
    bar.ts_event = 1704067200000000000 + (ts_offset * 60_000_000_000)  # 1 min offset
    bar.close = Decimal("42500.00")
    bar.open = Decimal("42000.00")
    bar.high = Decimal("42700.00")
    bar.low = Decimal("41800.00")
    bar.volume = Decimal("100.0")
    return bar


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
    start_ns = int(time.time() * 1e9)
    clock.timestamp_ns.return_value = start_ns
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
            trader_id="PERF-TESTER-001",
            recovery_enabled=True,
            warmup_lookback_days=2,  # 2 days of warmup
            startup_delay_secs=5.0,  # Minimum valid value
            max_recovery_time_secs=30.0,
        ),
    )


@pytest.mark.performance
@pytest.mark.recovery
class TestFullRecoveryTime:
    """Performance tests for full state recovery time (NFR-001)."""

    def test_full_recovery_with_positions_and_warmup_under_30s(
        self,
        mock_cache,
        mock_clock,
        mock_instrument,
        strategy_config,
    ):
        """Test full recovery with positions and warmup data completes under 30s."""
        # Setup position
        mock_position = create_mock_position(
            "BTCUSDT-PERP.BINANCE", Decimal("1.5")
        )
        mock_cache.instrument.return_value = mock_instrument
        mock_cache.positions.return_value = [mock_position]

        # Create warmup bars (2 days * 24 hours * 60 minutes = 2880 bars)
        warmup_bars = [create_mock_bar(i) for i in range(2880)]

        strategy = ConcreteRecoverableStrategy(strategy_config)

        # Measure full recovery time
        start_time = time.perf_counter()

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

                    # Start recovery (triggers position detection + warmup request)
                    with patch.object(strategy, "request_bars"):
                        with patch.object(strategy, "subscribe_bars"):
                            strategy.on_start()

                    # Simulate warmup data callback
                    strategy._on_warmup_data_received(warmup_bars)

        elapsed_time = time.perf_counter() - start_time

        # Assert NFR-001: Full state recovery < 30 seconds
        assert elapsed_time < FULL_RECOVERY_TARGET_SECS, (
            f"Full recovery took {elapsed_time:.3f}s, "
            f"exceeds target of {FULL_RECOVERY_TARGET_SECS}s"
        )
        assert strategy.recovered_positions_count == 1
        assert strategy.warmup_complete_called
        assert len(strategy.historical_data_calls) == 2880
        assert strategy.is_ready

    def test_full_recovery_with_no_positions_under_30s(
        self,
        mock_cache,
        mock_clock,
        mock_instrument,
        strategy_config,
    ):
        """Test full recovery with only warmup data completes under 30s."""
        # Setup - no positions
        mock_cache.instrument.return_value = mock_instrument
        mock_cache.positions.return_value = []

        # Create warmup bars
        warmup_bars = [create_mock_bar(i) for i in range(1440)]  # 1 day

        strategy = ConcreteRecoverableStrategy(strategy_config)

        # Measure full recovery time
        start_time = time.perf_counter()

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

                    with patch.object(strategy, "request_bars"):
                        with patch.object(strategy, "subscribe_bars"):
                            strategy.on_start()

                    # Simulate warmup completion
                    strategy._on_warmup_data_received(warmup_bars)

        elapsed_time = time.perf_counter() - start_time

        # Assert NFR-001: Full state recovery < 30 seconds
        assert elapsed_time < FULL_RECOVERY_TARGET_SECS
        assert strategy.warmup_complete_called
        assert strategy.is_ready

    def test_full_recovery_with_multiple_positions_under_30s(
        self,
        mock_cache,
        mock_clock,
        mock_instrument,
        strategy_config,
    ):
        """Test full recovery with multiple positions completes under 30s."""
        # Setup multiple positions
        positions = [
            create_mock_position(
                "BTCUSDT-PERP.BINANCE", Decimal(str(i + 1))
            )
            for i in range(5)
        ]
        mock_cache.instrument.return_value = mock_instrument
        mock_cache.positions.return_value = positions

        # Create warmup bars
        warmup_bars = [create_mock_bar(i) for i in range(2880)]

        strategy = ConcreteRecoverableStrategy(strategy_config)

        # Measure full recovery time
        start_time = time.perf_counter()

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

                    with patch.object(strategy, "request_bars"):
                        with patch.object(strategy, "subscribe_bars"):
                            strategy.on_start()

                    # Simulate warmup completion
                    strategy._on_warmup_data_received(warmup_bars)

        elapsed_time = time.perf_counter() - start_time

        # Assert NFR-001: Full state recovery < 30 seconds
        assert elapsed_time < FULL_RECOVERY_TARGET_SECS
        assert strategy.recovered_positions_count == 5
        assert strategy.warmup_complete_called

    def test_recovery_state_transitions_complete(
        self,
        mock_cache,
        mock_clock,
        mock_instrument,
        strategy_config,
    ):
        """Test that recovery state transitions correctly to COMPLETED."""
        # Setup
        mock_position = create_mock_position(
            "BTCUSDT-PERP.BINANCE", Decimal("1.0")
        )
        mock_cache.instrument.return_value = mock_instrument
        mock_cache.positions.return_value = [mock_position]

        warmup_bars = [create_mock_bar(i) for i in range(100)]

        strategy = ConcreteRecoverableStrategy(strategy_config)

        # Initial state
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

                    with patch.object(strategy, "request_bars"):
                        with patch.object(strategy, "subscribe_bars"):
                            strategy.on_start()

                    # After on_start: IN_PROGRESS
                    assert strategy.recovery_state.status == RecoveryStatus.IN_PROGRESS

                    # After warmup: COMPLETED
                    strategy._on_warmup_data_received(warmup_bars)
                    assert strategy.recovery_state.status == RecoveryStatus.COMPLETED

        # Final state validation
        assert strategy.recovery_state.is_complete
        assert strategy.recovery_state.indicators_warmed
        assert strategy.recovery_state.orders_reconciled

    def test_empty_warmup_recovery_under_30s(
        self,
        mock_cache,
        mock_clock,
        mock_instrument,
        strategy_config,
    ):
        """Test recovery with empty warmup data completes quickly."""
        # Setup
        mock_cache.instrument.return_value = mock_instrument
        mock_cache.positions.return_value = []

        strategy = ConcreteRecoverableStrategy(strategy_config)

        # Measure recovery time
        start_time = time.perf_counter()

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

                    with patch.object(strategy, "request_bars"):
                        with patch.object(strategy, "subscribe_bars"):
                            strategy.on_start()

                    # Empty warmup data
                    strategy._on_warmup_data_received([])

        elapsed_time = time.perf_counter() - start_time

        # Empty recovery should be very fast
        assert elapsed_time < 1.0
        assert strategy.is_ready
        assert strategy.warmup_complete_called

    @pytest.mark.parametrize("num_bars", [100, 500, 1000, 2880])
    def test_warmup_processing_scales(
        self,
        mock_cache,
        mock_clock,
        mock_instrument,
        strategy_config,
        num_bars: int,
    ):
        """Test that warmup processing scales reasonably with bar count."""
        # Setup
        mock_cache.instrument.return_value = mock_instrument
        mock_cache.positions.return_value = []

        warmup_bars = [create_mock_bar(i) for i in range(num_bars)]

        strategy = ConcreteRecoverableStrategy(strategy_config)

        # Measure warmup processing time
        start_time = time.perf_counter()

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

                    with patch.object(strategy, "request_bars"):
                        with patch.object(strategy, "subscribe_bars"):
                            strategy.on_start()

                    # Process warmup
                    strategy._on_warmup_data_received(warmup_bars)

        elapsed_time = time.perf_counter() - start_time

        # All sizes should complete under 30 seconds
        assert elapsed_time < FULL_RECOVERY_TARGET_SECS, (
            f"Warmup of {num_bars} bars took {elapsed_time:.3f}s"
        )
        assert len(strategy.historical_data_calls) == num_bars
        assert strategy.is_ready
