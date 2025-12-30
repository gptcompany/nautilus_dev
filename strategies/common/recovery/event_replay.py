"""Event Replay Manager (Spec 017, FR-004).

This module implements the EventReplayManager for replaying cached events
and generating synthetic events during position recovery.

This is a P3 optional feature for advanced recovery scenarios where
event history needs to be reconstructed.

Key Responsibilities:
- Replay position events from cache
- Generate synthetic events for gap filling
- Maintain event sequence numbers
- Detect and fill event gaps
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from strategies.common.recovery.models import PositionSnapshot


# Module logger
_log = logging.getLogger(__name__)


@dataclass
class SyntheticEvent:
    """Synthetic event for recovery gap filling.

    Synthetic events are generated when actual events are missing
    from the cache, allowing the system to reconstruct position state.

    Attributes:
        event_type: Type of event (position.opened, position.changed, order.filled)
        instrument_id: Instrument identifier
        ts_event: Event timestamp in nanoseconds
        is_synthetic: Always True for synthetic events
        side: Position/order side (LONG, SHORT, BUY, SELL)
        quantity: Event quantity
        price: Event price (if applicable)
        previous_quantity: Previous quantity for change events
        sequence: Event sequence number
    """

    event_type: str
    instrument_id: str
    ts_event: int
    is_synthetic: bool = True
    side: str | None = None
    quantity: Decimal | None = None
    price: Decimal | None = None
    previous_quantity: Decimal | None = None
    sequence: int | None = None


@dataclass
class EventGap:
    """Represents a gap in the event sequence.

    Attributes:
        start_seq: First missing sequence number
        end_seq: Last missing sequence number
        start_ts: Timestamp before the gap
        end_ts: Timestamp after the gap
    """

    start_seq: int
    end_seq: int
    start_ts: int
    end_ts: int


class EventReplayManager:
    """Manager for event replay and synthetic event generation.

    Implements FR-004 from Spec 017. Handles:
    - Replaying missed events from cache
    - Generating synthetic events for gap filling
    - Maintaining event sequence numbers

    This is a P3 optional feature - implementation is kept simple.

    Attributes:
        cache: NautilusTrader cache instance for event access.
        logger: Optional custom logger instance.

    Example:
        >>> manager = EventReplayManager(cache=node.cache)
        >>> events = manager.replay_events(trader_id="TRADER-001")
        >>> for event in events:
        ...     strategy.on_event(event)
    """

    def __init__(
        self,
        cache: Any,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize the EventReplayManager.

        Args:
            cache: NautilusTrader cache instance.
            logger: Optional custom logger. If None, uses module logger.
        """
        self._cache = cache
        self._log = logger or _log
        self._sequence_number: int = 0
        self._replay_count: int = 0

    @property
    def sequence_number(self) -> int:
        """Current sequence number."""
        return self._sequence_number

    @property
    def replay_count(self) -> int:
        """Number of replay operations performed."""
        return self._replay_count

    def replay_events(
        self,
        trader_id: str,
        instrument_id: str | None = None,
        start_ns: int | None = None,
        end_ns: int | None = None,
    ) -> list[Any]:
        """Replay position events from cache.

        Retrieves and orders position events from cache, optionally
        filtering by instrument and time range.

        Args:
            trader_id: The trader identifier.
            instrument_id: Optional instrument filter.
            start_ns: Optional start timestamp (nanoseconds).
            end_ns: Optional end timestamp (nanoseconds).

        Returns:
            List of position events ordered by timestamp (ascending).
        """
        self._log.info(
            "Replaying events for trader_id=%s instrument=%s",
            trader_id,
            instrument_id or "all",
        )

        # Get events from cache
        try:
            events = list(self._cache.position_events())
        except AttributeError:
            # Cache may not have position_events method
            self._log.warning("Cache does not support position_events()")
            events = []

        # Filter by instrument if specified
        if instrument_id:
            events = [
                e
                for e in events
                if hasattr(e, "instrument_id")
                and e.instrument_id.value == instrument_id
            ]

        # Filter by time range
        if start_ns:
            events = [e for e in events if e.ts_event >= start_ns]
        if end_ns:
            events = [e for e in events if e.ts_event <= end_ns]

        # Sort by timestamp (ascending)
        events = sorted(events, key=lambda e: e.ts_event)

        self._replay_count += 1
        self._log.info(
            "Replayed %d events for trader_id=%s (replay #%d)",
            len(events),
            trader_id,
            self._replay_count,
        )

        return events

    def get_next_sequence_number(self, trader_id: str) -> int:
        """Get the next sequence number for events.

        Increments and returns the next sequence number.

        Args:
            trader_id: The trader identifier (for logging).

        Returns:
            The next sequence number.
        """
        self._sequence_number += 1
        return self._sequence_number

    def reset_sequence(self, sequence: int = 0) -> None:
        """Reset sequence number to a specific value.

        Args:
            sequence: The sequence number to reset to.
        """
        self._sequence_number = sequence
        self._log.debug("Sequence number reset to %d", sequence)

    def generate_position_opened_event(
        self,
        position: PositionSnapshot | None,
        ts_event: int | None,
    ) -> SyntheticEvent:
        """Generate a synthetic position opened event.

        Creates a synthetic event representing a position opening
        for recovery purposes.

        Args:
            position: The position snapshot.
            ts_event: Event timestamp in nanoseconds.

        Returns:
            SyntheticEvent representing position opened.

        Raises:
            ValueError: If position or ts_event is None.
        """
        if position is None:
            raise ValueError("position is required")
        if ts_event is None:
            raise ValueError("ts_event is required")

        return SyntheticEvent(
            event_type="position.opened",
            instrument_id=position.instrument_id,
            ts_event=ts_event,
            side=position.side,
            quantity=position.quantity,
            price=position.avg_entry_price,
            sequence=self.get_next_sequence_number(trader_id="synthetic"),
        )

    def generate_position_changed_event(
        self,
        position: PositionSnapshot | None,
        previous_quantity: Decimal,
        ts_event: int | None,
    ) -> SyntheticEvent:
        """Generate a synthetic position changed event.

        Creates a synthetic event representing a position size change.

        Args:
            position: The position snapshot (current state).
            previous_quantity: The previous position quantity.
            ts_event: Event timestamp in nanoseconds.

        Returns:
            SyntheticEvent representing position changed.

        Raises:
            ValueError: If position or ts_event is None.
        """
        if position is None:
            raise ValueError("position is required")
        if ts_event is None:
            raise ValueError("ts_event is required")

        return SyntheticEvent(
            event_type="position.changed",
            instrument_id=position.instrument_id,
            ts_event=ts_event,
            side=position.side,
            quantity=position.quantity,
            previous_quantity=previous_quantity,
            sequence=self.get_next_sequence_number(trader_id="synthetic"),
        )

    def generate_synthetic_fill_event(
        self,
        instrument_id: str,
        side: str,
        quantity: Decimal,
        price: Decimal,
        ts_event: int | None,
    ) -> SyntheticEvent:
        """Generate a synthetic fill event for gap filling.

        Creates a synthetic order filled event to reconstruct
        position state when actual events are missing.

        Args:
            instrument_id: The instrument identifier.
            side: Order side (BUY or SELL).
            quantity: Fill quantity.
            price: Fill price.
            ts_event: Event timestamp in nanoseconds.

        Returns:
            SyntheticEvent representing order filled.

        Raises:
            ValueError: If quantity <= 0 or ts_event is None.
        """
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        if ts_event is None:
            raise ValueError("ts_event is required")

        return SyntheticEvent(
            event_type="order.filled",
            instrument_id=instrument_id,
            ts_event=ts_event,
            side=side,
            quantity=quantity,
            price=price,
            sequence=self.get_next_sequence_number(trader_id="synthetic"),
        )

    def generate_synthetic_events(
        self,
        position: PositionSnapshot,
        ts_recovery: int,
    ) -> list[SyntheticEvent]:
        """Generate all synthetic events for a position.

        Creates the minimal set of synthetic events needed to
        reconstruct position state during recovery.

        For a simple position, this generates:
        - One position.opened event

        Args:
            position: The position snapshot to generate events for.
            ts_recovery: Recovery timestamp in nanoseconds.

        Returns:
            List of synthetic events for the position.
        """
        events: list[SyntheticEvent] = []

        # Generate position opened event
        opened_event = self.generate_position_opened_event(
            position=position,
            ts_event=position.ts_opened,
        )
        events.append(opened_event)

        self._log.info(
            "Generated %d synthetic events for position %s",
            len(events),
            position.instrument_id,
        )

        return events

    def detect_event_gaps(
        self,
        trader_id: str,
        max_gap_secs: float = 1800.0,
    ) -> list[dict[str, Any]]:
        """Detect gaps in the event sequence.

        Identifies gaps based on:
        - Missing sequence numbers
        - Large time gaps between events

        Args:
            trader_id: The trader identifier.
            max_gap_secs: Maximum allowed gap in seconds before flagging.

        Returns:
            List of gap dictionaries with start/end sequence and timestamps.
        """
        self._log.info(
            "Detecting event gaps for trader_id=%s (max_gap=%ss)",
            trader_id,
            max_gap_secs,
        )

        # Get events from cache
        try:
            events = list(self._cache.position_events())
        except AttributeError:
            self._log.warning("Cache does not support position_events()")
            return []

        if len(events) < 2:
            return []

        # Sort by timestamp
        events = sorted(events, key=lambda e: e.ts_event)

        gaps: list[dict[str, Any]] = []
        max_gap_ns = int(max_gap_secs * 1_000_000_000)

        for i in range(1, len(events)):
            prev_event = events[i - 1]
            curr_event = events[i]

            # Check for sequence gap
            if hasattr(prev_event, "sequence") and hasattr(curr_event, "sequence"):
                seq_diff = curr_event.sequence - prev_event.sequence
                if seq_diff > 1:
                    gap = {
                        "start_seq": prev_event.sequence + 1,
                        "end_seq": curr_event.sequence - 1,
                        "start_ts": prev_event.ts_event,
                        "end_ts": curr_event.ts_event,
                    }
                    gaps.append(gap)
                    self._log.warning(
                        "Detected sequence gap: seq %d-%d",
                        gap["start_seq"],
                        gap["end_seq"],
                    )

            # Check for time gap
            time_diff = curr_event.ts_event - prev_event.ts_event
            if time_diff > max_gap_ns and not gaps:
                # Only flag time gaps if no sequence gap detected
                self._log.warning(
                    "Large time gap detected: %d seconds",
                    time_diff // 1_000_000_000,
                )

        self._log.info("Detected %d event gaps for trader_id=%s", len(gaps), trader_id)

        return gaps

    def fill_event_gap(
        self,
        gap: dict[str, Any],
        position: PositionSnapshot,
    ) -> list[SyntheticEvent]:
        """Fill a detected event gap with synthetic events.

        Generates synthetic events to bridge the gap between
        the start and end timestamps.

        Args:
            gap: Gap dictionary with start/end sequence and timestamps.
            position: Position snapshot for context.

        Returns:
            List of synthetic events to fill the gap.
        """
        self._log.info(
            "Filling event gap seq %d-%d for position %s",
            gap.get("start_seq", 0),
            gap.get("end_seq", 0),
            position.instrument_id,
        )

        events: list[SyntheticEvent] = []

        # Calculate midpoint timestamp for synthetic event
        mid_ts = (gap["start_ts"] + gap["end_ts"]) // 2

        # Generate a position update event at midpoint
        event = SyntheticEvent(
            event_type="position.snapshot",
            instrument_id=position.instrument_id,
            ts_event=mid_ts,
            side=position.side,
            quantity=position.quantity,
            price=position.avg_entry_price,
            sequence=gap["start_seq"],
        )
        events.append(event)

        self._log.info(
            "Generated %d synthetic events to fill gap",
            len(events),
        )

        return events
