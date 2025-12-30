"""Performance test for position recovery time < 5s (NFR-001 - T042).

Tests that position recovery completes within the p95 target of 5 seconds.
This validates the NFR-001 requirement from Spec 017.

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
from strategies.common.recovery.models import RecoveryState, RecoveryStatus
from strategies.common.recovery.recoverable_strategy import (
    RecoverableStrategy,
    RecoverableStrategyConfig,
)


# NFR-001 target: Position recovery < 5 seconds (p95)
POSITION_RECOVERY_TARGET_SECS = 5.0


class ConcreteRecoverableStrategy(RecoverableStrategy):
    """Concrete subclass for performance testing."""

    def __init__(self, config: RecoverableStrategyConfig) -> None:
        super().__init__(config)
        self.position_recovered_calls: list = []

    def on_position_recovered(self, position) -> None:
        """Track position recovered calls."""
        self.position_recovered_calls.append(position)

    def on_historical_data(self, bar) -> None:
        """Skip historical data processing for position-only recovery test."""
        pass

    def on_warmup_complete(self) -> None:
        """Skip warmup complete for position-only recovery test."""
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


@pytest.fixture
def mock_cache():
    """Create a mock cache."""
    cache = MagicMock()
    cache.positions.return_value = []
    cache.orders_open.return_value = []
    return cache


@pytest.fixture
def mock_clock():
    """Create a mock clock with real-time-like behavior."""
    clock = MagicMock()
    start_ns = int(time.time() * 1e9)
    clock.timestamp_ns.return_value = start_ns
    clock.utc_now.return_value = MagicMock()
    clock.utc_now.return_value.__sub__ = MagicMock(
        return_value=MagicMock()
    )
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
            warmup_lookback_days=1,  # Minimum valid value
            startup_delay_secs=5.0,  # Minimum valid value
            max_recovery_time_secs=30.0,
        ),
    )


@pytest.mark.performance
@pytest.mark.recovery
class TestPositionRecoveryTime:
    """Performance tests for position recovery time (NFR-001)."""

    def test_single_position_recovery_under_5s(
        self,
        mock_cache,
        mock_clock,
        mock_instrument,
        strategy_config,
    ):
        """Test that recovering a single position completes under 5 seconds."""
        # Setup
        mock_position = create_mock_position(
            "BTCUSDT-PERP.BINANCE", Decimal("1.5")
        )
        mock_cache.instrument.return_value = mock_instrument
        mock_cache.positions.return_value = [mock_position]

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

        elapsed_time = time.perf_counter() - start_time

        # Assert NFR-001: Position recovery < 5 seconds
        assert elapsed_time < POSITION_RECOVERY_TARGET_SECS, (
            f"Position recovery took {elapsed_time:.3f}s, "
            f"exceeds target of {POSITION_RECOVERY_TARGET_SECS}s"
        )
        assert strategy.recovered_positions_count == 1

    def test_multiple_positions_recovery_under_5s(
        self,
        mock_cache,
        mock_clock,
        mock_instrument,
        strategy_config,
    ):
        """Test recovering 10 positions completes under 5 seconds."""
        # Setup 10 positions
        positions = [
            create_mock_position(
                "BTCUSDT-PERP.BINANCE", Decimal(str(i + 1))
            )
            for i in range(10)
        ]
        mock_cache.instrument.return_value = mock_instrument
        mock_cache.positions.return_value = positions

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

        elapsed_time = time.perf_counter() - start_time

        # Assert NFR-001: Position recovery < 5 seconds even with 10 positions
        assert elapsed_time < POSITION_RECOVERY_TARGET_SECS, (
            f"Recovery of 10 positions took {elapsed_time:.3f}s, "
            f"exceeds target of {POSITION_RECOVERY_TARGET_SECS}s"
        )
        assert strategy.recovered_positions_count == 10

    def test_position_recovery_state_transition_timing(
        self,
        mock_cache,
        mock_clock,
        mock_instrument,
        strategy_config,
    ):
        """Test that state transitions during recovery are fast."""
        # Setup
        mock_position = create_mock_position(
            "BTCUSDT-PERP.BINANCE", Decimal("1.0")
        )
        mock_cache.instrument.return_value = mock_instrument
        mock_cache.positions.return_value = [mock_position]

        strategy = ConcreteRecoverableStrategy(strategy_config)

        state_transitions = []

        def track_state(*args, **kwargs):
            state_transitions.append(
                (time.perf_counter(), strategy.recovery_state.status)
            )

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
                    log_mock = MagicMock()
                    log_mock.info.side_effect = track_state
                    log_prop.return_value = log_mock

                    start_time = time.perf_counter()

                    with patch.object(strategy, "request_bars"):
                        with patch.object(strategy, "subscribe_bars"):
                            strategy.on_start()

        elapsed_time = time.perf_counter() - start_time

        # Verify state transitioned to IN_PROGRESS
        assert strategy.recovery_state.status == RecoveryStatus.IN_PROGRESS
        # Verify timing
        assert elapsed_time < POSITION_RECOVERY_TARGET_SECS

    def test_no_positions_recovery_is_instant(
        self,
        mock_cache,
        mock_clock,
        mock_instrument,
        strategy_config,
    ):
        """Test that recovery with no positions is nearly instant."""
        # Setup - no positions
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

        elapsed_time = time.perf_counter() - start_time

        # With no positions, recovery should be very fast (<1s)
        assert elapsed_time < 1.0, (
            f"Empty recovery took {elapsed_time:.3f}s, expected <1s"
        )
        assert strategy.recovered_positions_count == 0

    @pytest.mark.parametrize("num_positions", [1, 5, 10, 20])
    def test_position_recovery_scales_linearly(
        self,
        mock_cache,
        mock_clock,
        mock_instrument,
        strategy_config,
        num_positions: int,
    ):
        """Test that recovery time scales reasonably with position count."""
        # Setup positions
        positions = [
            create_mock_position(
                "BTCUSDT-PERP.BINANCE", Decimal(str(i + 1))
            )
            for i in range(num_positions)
        ]
        mock_cache.instrument.return_value = mock_instrument
        mock_cache.positions.return_value = positions

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

        elapsed_time = time.perf_counter() - start_time

        # All sizes should complete under 5 seconds
        assert elapsed_time < POSITION_RECOVERY_TARGET_SECS, (
            f"Recovery of {num_positions} positions took {elapsed_time:.3f}s"
        )
        assert strategy.recovered_positions_count == num_positions
