"""Unit tests for synthetic event generation (FR-004, T038).

Tests:
- Generating synthetic position opened events
- Generating synthetic position changed events
- Generating synthetic fill events for gap filling
- Event validation and field population
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest


@pytest.mark.recovery
class TestSyntheticEventGeneration:
    """Tests for synthetic event generation functionality."""

    def test_generate_position_opened_event(self, mock_cache, position_snapshot):
        """Test generating a synthetic position opened event."""
        from strategies.common.recovery.event_replay import EventReplayManager

        manager = EventReplayManager(cache=mock_cache)

        event = manager.generate_position_opened_event(
            position=position_snapshot,
            ts_event=1704153600000000000,
        )

        assert event is not None
        assert event.event_type == "position.opened"
        assert event.instrument_id == position_snapshot.instrument_id
        assert event.side == position_snapshot.side
        assert event.quantity == position_snapshot.quantity
        assert event.ts_event == 1704153600000000000

    def test_generate_position_changed_event(self, mock_cache, position_snapshot):
        """Test generating a synthetic position changed event."""
        from strategies.common.recovery.event_replay import EventReplayManager

        manager = EventReplayManager(cache=mock_cache)

        event = manager.generate_position_changed_event(
            position=position_snapshot,
            previous_quantity=Decimal("1.0"),
            ts_event=1704153600000000000,
        )

        assert event is not None
        assert event.event_type == "position.changed"
        assert event.quantity == position_snapshot.quantity
        assert event.previous_quantity == Decimal("1.0")
        assert event.ts_event == 1704153600000000000

    def test_generate_synthetic_fill_event(self, mock_cache, position_snapshot):
        """Test generating a synthetic fill event for gap filling."""
        from strategies.common.recovery.event_replay import EventReplayManager

        manager = EventReplayManager(cache=mock_cache)

        event = manager.generate_synthetic_fill_event(
            instrument_id=position_snapshot.instrument_id,
            side="BUY",
            quantity=Decimal("0.5"),
            price=Decimal("42100.00"),
            ts_event=1704153600000000000,
        )

        assert event is not None
        assert event.event_type == "order.filled"
        assert event.side == "BUY"
        assert event.quantity == Decimal("0.5")
        assert event.price == Decimal("42100.00")
        assert event.is_synthetic is True

    def test_generate_synthetic_events_for_position(self, mock_cache, position_snapshot):
        """Test generating all synthetic events for a position."""
        from strategies.common.recovery.event_replay import EventReplayManager

        manager = EventReplayManager(cache=mock_cache)

        events = manager.generate_synthetic_events(
            position=position_snapshot,
            ts_recovery=1704153600000000000,
        )

        assert len(events) >= 1
        # Should at least have a position opened event
        opened_events = [e for e in events if e.event_type == "position.opened"]
        assert len(opened_events) == 1

    def test_synthetic_events_have_synthetic_flag(self, mock_cache, position_snapshot):
        """Test that synthetic events are flagged as synthetic."""
        from strategies.common.recovery.event_replay import EventReplayManager

        manager = EventReplayManager(cache=mock_cache)

        events = manager.generate_synthetic_events(
            position=position_snapshot,
            ts_recovery=1704153600000000000,
        )

        for event in events:
            assert event.is_synthetic is True


@pytest.mark.recovery
class TestSyntheticEventValidation:
    """Tests for synthetic event validation."""

    def test_synthetic_event_requires_timestamp(self, mock_cache, position_snapshot):
        """Test that synthetic events require a timestamp."""
        from strategies.common.recovery.event_replay import EventReplayManager

        manager = EventReplayManager(cache=mock_cache)

        with pytest.raises(ValueError, match="ts_event is required"):
            manager.generate_position_opened_event(
                position=position_snapshot,
                ts_event=None,
            )

    def test_synthetic_event_requires_valid_position(self, mock_cache):
        """Test that synthetic events require a valid position."""
        from strategies.common.recovery.event_replay import EventReplayManager

        manager = EventReplayManager(cache=mock_cache)

        with pytest.raises(ValueError, match="position is required"):
            manager.generate_position_opened_event(
                position=None,
                ts_event=1704153600000000000,
            )

    def test_synthetic_fill_requires_quantity(self, mock_cache):
        """Test that synthetic fill events require quantity."""
        from strategies.common.recovery.event_replay import EventReplayManager

        manager = EventReplayManager(cache=mock_cache)

        with pytest.raises(ValueError, match="quantity must be positive"):
            manager.generate_synthetic_fill_event(
                instrument_id="BTCUSDT-PERP.BINANCE",
                side="BUY",
                quantity=Decimal("0"),
                price=Decimal("42000.00"),
                ts_event=1704153600000000000,
            )


@pytest.mark.recovery
class TestGapFillingEvents:
    """Tests for gap filling event generation."""

    def test_detect_event_gaps(self, mock_cache):
        """Test detecting gaps in event sequence."""
        from strategies.common.recovery.event_replay import EventReplayManager

        event1 = MagicMock()
        event1.ts_event = 1704153600000000000
        event1.sequence = 1

        event2 = MagicMock()
        event2.ts_event = 1704157200000000000  # 1 hour gap
        event2.sequence = 5  # Gap in sequence

        mock_cache.position_events.return_value = [event1, event2]
        manager = EventReplayManager(cache=mock_cache)

        gaps = manager.detect_event_gaps(
            trader_id="TESTER-001",
            max_gap_secs=1800,  # 30 minutes
        )

        assert len(gaps) == 1
        assert gaps[0]["start_seq"] == 2
        assert gaps[0]["end_seq"] == 4

    def test_no_gaps_when_continuous(self, mock_cache):
        """Test that no gaps are detected when events are continuous."""
        from strategies.common.recovery.event_replay import EventReplayManager

        event1 = MagicMock()
        event1.ts_event = 1704153600000000000
        event1.sequence = 1

        event2 = MagicMock()
        event2.ts_event = 1704153900000000000  # 5 minute gap (ok)
        event2.sequence = 2

        mock_cache.position_events.return_value = [event1, event2]
        manager = EventReplayManager(cache=mock_cache)

        gaps = manager.detect_event_gaps(
            trader_id="TESTER-001",
            max_gap_secs=1800,
        )

        assert len(gaps) == 0

    def test_fill_gaps_with_synthetic_events(self, mock_cache, position_snapshot):
        """Test filling detected gaps with synthetic events."""
        from strategies.common.recovery.event_replay import EventReplayManager

        manager = EventReplayManager(cache=mock_cache)

        # Create a gap
        gap = {
            "start_seq": 2,
            "end_seq": 4,
            "start_ts": 1704153600000000000,
            "end_ts": 1704157200000000000,
        }

        filled = manager.fill_event_gap(
            gap=gap,
            position=position_snapshot,
        )

        assert len(filled) >= 1
        for event in filled:
            assert event.is_synthetic is True
            assert gap["start_ts"] <= event.ts_event <= gap["end_ts"]
