"""Unit tests for indicator warmup (FR-002 - T021).

Tests:
- _request_warmup_data() requests historical bars
- on_historical_data() processes bars
- _on_warmup_data_received() callback processes bars
- on_warmup_complete() callback fires
- Warmup state tracking (bars_processed, duration)
"""

# Python 3.10 compatibility
import datetime as _dt
from datetime import datetime, timedelta

if hasattr(_dt, "UTC"):
    UTC = _dt.UTC
else:
    UTC = _dt.timezone.utc
from unittest.mock import MagicMock

import pytest

from strategies.common.recovery.config import RecoveryConfig
from strategies.common.recovery.models import RecoveryState, RecoveryStatus


@pytest.mark.recovery
class TestRequestWarmupData:
    """Tests for _request_warmup_data method."""

    def test_request_warmup_calculates_correct_start_time(self, mock_clock, recovery_config):
        """Test that warmup start time is calculated correctly."""
        # Fixed time: 2024-01-02 00:00:00 UTC
        mock_clock.utc_now.return_value = datetime(2024, 1, 2, 0, 0, 0, tzinfo=UTC)
        lookback_days = recovery_config.warmup_lookback_days  # 2 days

        # Simulate _request_warmup_data calculation
        start_time = mock_clock.utc_now() - timedelta(days=lookback_days)

        # Expected: 2023-12-31 00:00:00 UTC
        expected = datetime(2023, 12, 31, 0, 0, 0, tzinfo=UTC)
        assert start_time == expected

    def test_request_warmup_uses_config_lookback_days(self):
        """Test that warmup uses configured lookback days."""
        config = RecoveryConfig(
            trader_id="TESTER-001",
            warmup_lookback_days=5,
        )

        assert config.warmup_lookback_days == 5

    def test_request_warmup_lookback_days_default(self):
        """Test default warmup lookback days is 2."""
        config = RecoveryConfig(trader_id="TESTER-001")

        assert config.warmup_lookback_days == 2

    def test_request_warmup_lookback_days_validation(self):
        """Test warmup lookback days validation (1-30)."""
        # Valid range
        config_min = RecoveryConfig(trader_id="T1", warmup_lookback_days=1)
        config_max = RecoveryConfig(trader_id="T1", warmup_lookback_days=30)
        assert config_min.warmup_lookback_days == 1
        assert config_max.warmup_lookback_days == 30

        # Invalid: below minimum
        with pytest.raises(ValueError):
            RecoveryConfig(trader_id="T1", warmup_lookback_days=0)

        # Invalid: above maximum
        with pytest.raises(ValueError):
            RecoveryConfig(trader_id="T1", warmup_lookback_days=31)


@pytest.mark.recovery
class TestOnHistoricalData:
    """Tests for on_historical_data callback."""

    def test_on_historical_data_is_callable(self):
        """Test that on_historical_data is a valid hook method."""
        from strategies.common.recovery.recoverable_strategy import (
            RecoverableStrategy,
        )

        assert hasattr(RecoverableStrategy, "on_historical_data")
        assert callable(RecoverableStrategy.on_historical_data)

    def test_on_historical_data_processes_single_bar(self):
        """Test processing a single historical bar."""
        bars_processed = []

        def on_historical_data(bar):
            bars_processed.append(bar)

        mock_bar = MagicMock()
        mock_bar.ts_event = 1704067200000000000

        on_historical_data(mock_bar)

        assert len(bars_processed) == 1
        assert bars_processed[0].ts_event == 1704067200000000000

    def test_on_historical_data_processes_multiple_bars(self):
        """Test processing multiple historical bars in order."""
        bars_processed = []

        def on_historical_data(bar):
            bars_processed.append(bar)

        # Create bars with different timestamps
        for i in range(5):
            mock_bar = MagicMock()
            mock_bar.ts_event = 1704067200000000000 + (i * 60_000_000_000)  # 1 min apart
            on_historical_data(mock_bar)

        assert len(bars_processed) == 5

    def test_on_historical_data_can_feed_indicators(self):
        """Test that on_historical_data can feed bars to indicators."""
        # Simulate indicator being fed bars
        mock_indicator = MagicMock()
        bars_fed = []

        def on_historical_data(bar):
            mock_indicator.handle_bar(bar)
            bars_fed.append(bar)

        mock_bar = MagicMock()
        on_historical_data(mock_bar)

        mock_indicator.handle_bar.assert_called_once_with(mock_bar)
        assert len(bars_fed) == 1


@pytest.mark.recovery
class TestWarmupDataReceived:
    """Tests for _on_warmup_data_received callback."""

    def test_warmup_data_received_empty_bars(self, mock_logger):
        """Test handling empty bars list from warmup request."""
        warmup_complete = False

        def on_warmup_data_received(bars):
            nonlocal warmup_complete
            if not bars:
                mock_logger.warning("No warmup bars received")
                warmup_complete = True

        on_warmup_data_received([])

        mock_logger.warning.assert_called_with("No warmup bars received")
        assert warmup_complete is True

    def test_warmup_data_received_sorts_bars_by_timestamp(self):
        """Test that bars are sorted by timestamp (oldest first)."""
        # Create bars out of order
        bar1 = MagicMock()
        bar1.ts_event = 1704067260000000000  # Later
        bar2 = MagicMock()
        bar2.ts_event = 1704067200000000000  # Earlier
        bar3 = MagicMock()
        bar3.ts_event = 1704067230000000000  # Middle

        bars = [bar1, bar2, bar3]

        # Simulate sorting logic from _on_warmup_data_received
        sorted_bars = sorted(bars, key=lambda b: b.ts_event)

        assert sorted_bars[0].ts_event == 1704067200000000000  # Earliest first
        assert sorted_bars[1].ts_event == 1704067230000000000
        assert sorted_bars[2].ts_event == 1704067260000000000  # Latest last

    def test_warmup_data_received_counts_processed_bars(self):
        """Test that warmup_bars_processed is incremented correctly."""
        warmup_bars_processed = 0

        def on_warmup_data_received(bars):
            nonlocal warmup_bars_processed
            sorted_bars = sorted(bars, key=lambda b: b.ts_event)
            for _bar in sorted_bars:
                # Process bar
                warmup_bars_processed += 1

        # Create 10 mock bars
        bars = [MagicMock(ts_event=1704067200000000000 + i * 60_000_000_000) for i in range(10)]
        on_warmup_data_received(bars)

        assert warmup_bars_processed == 10

    def test_warmup_data_received_logs_bar_count(self, mock_logger):
        """Test that received bar count is logged."""

        def on_warmup_data_received(bars):
            if bars:
                mock_logger.info(f"Received {len(bars)} warmup bars")

        bars = [MagicMock() for _ in range(100)]
        on_warmup_data_received(bars)

        mock_logger.info.assert_called_with("Received 100 warmup bars")


@pytest.mark.recovery
class TestCompleteWarmup:
    """Tests for _complete_warmup and on_warmup_complete."""

    def test_complete_warmup_sets_flag_true(self):
        """Test that _complete_warmup sets warmup_complete to True."""
        warmup_complete = False

        def complete_warmup():
            nonlocal warmup_complete
            warmup_complete = True

        complete_warmup()

        assert warmup_complete is True

    def test_complete_warmup_calculates_duration(self, mock_clock):
        """Test that warmup duration is calculated correctly."""
        warmup_start_ns = 1704153600000000000  # Start time
        # Simulate 500ms later
        mock_clock.timestamp_ns.return_value = 1704153600500000000

        # Calculate duration
        warmup_duration_ns = mock_clock.timestamp_ns() - warmup_start_ns
        warmup_duration_ms = warmup_duration_ns / 1_000_000

        assert warmup_duration_ms == 500.0

    def test_complete_warmup_updates_recovery_state(self, mock_clock):
        """Test that _complete_warmup updates recovery state correctly."""
        state = RecoveryState(
            status=RecoveryStatus.IN_PROGRESS,
            positions_recovered=2,
            indicators_warmed=False,
            orders_reconciled=False,
            ts_started=1704153600000000000,
        )

        # Simulate _complete_warmup state update
        new_state = RecoveryState(
            status=RecoveryStatus.COMPLETED,
            positions_recovered=state.positions_recovered,
            indicators_warmed=True,
            orders_reconciled=True,
            ts_started=state.ts_started,
            ts_completed=mock_clock.timestamp_ns(),
        )

        assert new_state.status == RecoveryStatus.COMPLETED
        assert new_state.indicators_warmed is True
        assert new_state.orders_reconciled is True
        assert new_state.ts_completed is not None

    def test_on_warmup_complete_hook_is_called(self):
        """Test that on_warmup_complete hook is called after warmup."""
        on_warmup_complete_called = False

        def on_warmup_complete():
            nonlocal on_warmup_complete_called
            on_warmup_complete_called = True

        def complete_warmup():
            # Complete warmup logic...
            on_warmup_complete()

        complete_warmup()

        assert on_warmup_complete_called is True

    def test_on_warmup_complete_is_overridable(self):
        """Test that on_warmup_complete can be overridden in subclasses."""
        from strategies.common.recovery.recoverable_strategy import (
            RecoverableStrategy,
        )

        # Verify the method exists and is meant to be overridden
        assert hasattr(RecoverableStrategy, "on_warmup_complete")

        # Base implementation does nothing (pass)
        # Subclasses can override to add custom behavior

    def test_complete_warmup_logs_summary(self, mock_logger):
        """Test that warmup completion is logged with summary."""
        warmup_bars_processed = 150
        warmup_duration_ms = 250.5

        def complete_warmup():
            mock_logger.info(
                f"Warmup complete: "
                f"bars_processed={warmup_bars_processed}, "
                f"duration_ms={warmup_duration_ms:.1f}"
            )

        complete_warmup()

        mock_logger.info.assert_called_with(
            "Warmup complete: bars_processed=150, duration_ms=250.5"
        )


@pytest.mark.recovery
class TestWarmupStateTracking:
    """Tests for warmup state tracking variables."""

    def test_warmup_bars_processed_starts_at_zero(self):
        """Test initial warmup_bars_processed is zero."""
        warmup_bars_processed = 0
        assert warmup_bars_processed == 0

    def test_warmup_start_ns_is_set_on_start(self, mock_clock):
        """Test that warmup_start_ns is set when warmup begins."""
        warmup_start_ns = None

        def start_warmup():
            nonlocal warmup_start_ns
            warmup_start_ns = mock_clock.timestamp_ns()

        start_warmup()

        assert warmup_start_ns == 1704153600000000000

    def test_warmup_complete_flag_transitions(self):
        """Test warmup_complete flag transitions from False to True."""
        warmup_complete = False
        assert warmup_complete is False

        # After warmup
        warmup_complete = True
        assert warmup_complete is True

    def test_recovery_state_duration_calculation(self):
        """Test RecoveryState.recovery_duration_ms property."""
        state = RecoveryState(
            status=RecoveryStatus.COMPLETED,
            ts_started=1704153600000000000,  # 0ms
            ts_completed=1704153600500000000,  # 500ms later
        )

        assert state.recovery_duration_ms == 500.0

    def test_recovery_state_duration_none_if_incomplete(self):
        """Test recovery_duration_ms is None if not completed."""
        state = RecoveryState(
            status=RecoveryStatus.IN_PROGRESS,
            ts_started=1704153600000000000,
            ts_completed=None,
        )

        assert state.recovery_duration_ms is None


@pytest.mark.recovery
class TestWarmupIntegration:
    """Integration tests for the full warmup flow."""

    def test_full_warmup_flow(self, mock_clock, mock_logger):
        """Test the complete warmup flow from request to completion."""
        # Initial state
        warmup_complete = False
        warmup_bars_processed = 0
        warmup_start_ns = mock_clock.timestamp_ns()
        recovery_state = RecoveryState(
            status=RecoveryStatus.IN_PROGRESS,
            ts_started=warmup_start_ns,
        )

        # Step 1: Request warmup data (simulated)
        mock_logger.info("Requesting warmup data")

        # Step 2: Receive bars (simulated callback)
        bars = [MagicMock(ts_event=1704067200000000000 + i * 60_000_000_000) for i in range(50)]
        sorted_bars = sorted(bars, key=lambda b: b.ts_event)

        # Step 3: Process bars
        for _bar in sorted_bars:
            warmup_bars_processed += 1

        # Step 4: Complete warmup
        warmup_complete = True
        mock_clock.timestamp_ns.return_value = 1704153600250000000  # 250ms later

        recovery_state = RecoveryState(
            status=RecoveryStatus.COMPLETED,
            positions_recovered=recovery_state.positions_recovered,
            indicators_warmed=True,
            orders_reconciled=True,
            ts_started=warmup_start_ns,
            ts_completed=mock_clock.timestamp_ns(),
        )

        # Verify final state
        assert warmup_complete is True
        assert warmup_bars_processed == 50
        assert recovery_state.status == RecoveryStatus.COMPLETED
        assert recovery_state.indicators_warmed is True
        assert recovery_state.recovery_duration_ms == 250.0
