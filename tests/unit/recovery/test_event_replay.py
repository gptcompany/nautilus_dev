"""Unit tests for event replay logic (FR-004, T037).

Tests:
- Replaying events from cache
- Event ordering by timestamp
- Handling empty event cache
- Handling multiple event types
- Sequence number maintenance
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest


@pytest.mark.recovery
class TestEventReplayManager:
    """Tests for EventReplayManager functionality."""

    def test_replay_events_empty_cache(self, mock_cache):
        """Test replaying events when cache is empty."""
        from strategies.common.recovery.event_replay import EventReplayManager

        mock_cache.position_events.return_value = []
        manager = EventReplayManager(cache=mock_cache)

        events = manager.replay_events(trader_id="TESTER-001")

        assert events == []
        mock_cache.position_events.assert_called_once()

    def test_replay_events_single_event(self, mock_cache):
        """Test replaying a single position event."""
        from strategies.common.recovery.event_replay import EventReplayManager

        mock_event = MagicMock()
        mock_event.ts_event = 1704153600000000000
        mock_event.instrument_id = MagicMock()
        mock_event.instrument_id.value = "BTCUSDT-PERP.BINANCE"

        mock_cache.position_events.return_value = [mock_event]
        manager = EventReplayManager(cache=mock_cache)

        events = manager.replay_events(trader_id="TESTER-001")

        assert len(events) == 1
        assert events[0].ts_event == 1704153600000000000

    def test_replay_events_ordered_by_timestamp(self, mock_cache):
        """Test that replayed events are ordered by timestamp."""
        from strategies.common.recovery.event_replay import EventReplayManager

        # Create events out of order
        event1 = MagicMock()
        event1.ts_event = 1704153700000000000  # Later

        event2 = MagicMock()
        event2.ts_event = 1704153600000000000  # Earlier

        mock_cache.position_events.return_value = [event1, event2]
        manager = EventReplayManager(cache=mock_cache)

        events = manager.replay_events(trader_id="TESTER-001")

        assert len(events) == 2
        assert events[0].ts_event < events[1].ts_event  # Ordered ascending

    def test_replay_events_filters_by_instrument(self, mock_cache):
        """Test filtering events by instrument ID."""
        from strategies.common.recovery.event_replay import EventReplayManager

        btc_event = MagicMock()
        btc_event.ts_event = 1704153600000000000
        btc_event.instrument_id = MagicMock()
        btc_event.instrument_id.value = "BTCUSDT-PERP.BINANCE"

        eth_event = MagicMock()
        eth_event.ts_event = 1704153700000000000
        eth_event.instrument_id = MagicMock()
        eth_event.instrument_id.value = "ETHUSDT-PERP.BINANCE"

        mock_cache.position_events.return_value = [btc_event, eth_event]
        manager = EventReplayManager(cache=mock_cache)

        events = manager.replay_events(
            trader_id="TESTER-001",
            instrument_id="BTCUSDT-PERP.BINANCE",
        )

        assert len(events) == 1
        assert events[0].instrument_id.value == "BTCUSDT-PERP.BINANCE"

    def test_replay_events_filters_by_time_range(self, mock_cache):
        """Test filtering events by time range."""
        from strategies.common.recovery.event_replay import EventReplayManager

        old_event = MagicMock()
        old_event.ts_event = 1704067200000000000  # 2024-01-01

        recent_event = MagicMock()
        recent_event.ts_event = 1704153600000000000  # 2024-01-02

        mock_cache.position_events.return_value = [old_event, recent_event]
        manager = EventReplayManager(cache=mock_cache)

        events = manager.replay_events(
            trader_id="TESTER-001",
            start_ns=1704100000000000000,  # After old_event
        )

        assert len(events) == 1
        assert events[0].ts_event == 1704153600000000000


@pytest.mark.recovery
class TestEventSequencing:
    """Tests for event sequence number maintenance."""

    def test_get_next_sequence_number_empty(self, mock_cache):
        """Test getting sequence number when no prior events."""
        from strategies.common.recovery.event_replay import EventReplayManager

        mock_cache.position_events.return_value = []
        manager = EventReplayManager(cache=mock_cache)

        seq = manager.get_next_sequence_number(trader_id="TESTER-001")

        assert seq == 1  # Start from 1

    def test_get_next_sequence_number_increments(self, mock_cache):
        """Test that sequence numbers increment correctly."""
        from strategies.common.recovery.event_replay import EventReplayManager

        mock_event = MagicMock()
        mock_event.sequence = 5

        mock_cache.position_events.return_value = [mock_event]
        # Simulate sequence tracking
        mock_cache.get_sequence.return_value = 5

        manager = EventReplayManager(cache=mock_cache)
        manager._sequence_number = 5

        seq = manager.get_next_sequence_number(trader_id="TESTER-001")

        assert seq == 6

    def test_reset_sequence_number(self, mock_cache):
        """Test resetting sequence number to specific value."""
        from strategies.common.recovery.event_replay import EventReplayManager

        manager = EventReplayManager(cache=mock_cache)
        manager._sequence_number = 10

        manager.reset_sequence(sequence=1)

        assert manager._sequence_number == 1

    def test_sequence_maintained_across_replays(self, mock_cache):
        """Test that sequence is maintained across multiple replays."""
        from strategies.common.recovery.event_replay import EventReplayManager

        event1 = MagicMock()
        event1.ts_event = 1704153600000000000

        event2 = MagicMock()
        event2.ts_event = 1704153700000000000

        mock_cache.position_events.return_value = [event1, event2]
        manager = EventReplayManager(cache=mock_cache)

        # First replay
        manager.replay_events(trader_id="TESTER-001")

        # Sequence should track events
        assert manager._replay_count == 1

        # Second replay
        manager.replay_events(trader_id="TESTER-001")
        assert manager._replay_count == 2
