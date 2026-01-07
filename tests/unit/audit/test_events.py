"""Unit tests for audit events (Spec 030).

Tests:
- AuditEvent checksum computation
- Event schema validation
- Serialization/deserialization
"""

import json
import time

from strategies.common.audit.events import (
    AuditEvent,
    AuditEventType,
    ParameterChangeEvent,
    SignalEvent,
    SystemEvent,
    TradeEvent,
)


class TestAuditEvent:
    """Tests for AuditEvent base model."""

    def test_checksum_computation(self):
        """Test that checksum is computed correctly."""
        event = AuditEvent(
            event_type=AuditEventType.PARAM_STATE_CHANGE,
            source="test",
            ts_event=1704067200000000000,  # Fixed timestamp
        )
        checksum = event.checksum

        # Checksum should be 16 hex characters
        assert len(checksum) == 16
        assert all(c in "0123456789abcdef" for c in checksum)

    def test_checksum_deterministic(self):
        """Test that checksum is deterministic for same event."""
        event1 = AuditEvent(
            event_type=AuditEventType.PARAM_STATE_CHANGE,
            source="test",
            ts_event=1704067200000000000,
            trader_id="TRADER-001",
            sequence=0,
        )
        event2 = AuditEvent(
            event_type=AuditEventType.PARAM_STATE_CHANGE,
            source="test",
            ts_event=1704067200000000000,
            trader_id="TRADER-001",
            sequence=0,
        )

        assert event1.checksum == event2.checksum

    def test_checksum_changes_with_data(self):
        """Test that checksum changes when event data changes."""
        event1 = AuditEvent(
            event_type=AuditEventType.PARAM_STATE_CHANGE,
            source="test",
            ts_event=1704067200000000000,
        )
        event2 = AuditEvent(
            event_type=AuditEventType.PARAM_STATE_CHANGE,
            source="different_source",  # Changed
            ts_event=1704067200000000000,
        )

        assert event1.checksum != event2.checksum

    def test_default_timestamp_is_nanoseconds(self):
        """Test that default timestamp is in nanoseconds."""
        before = time.time_ns()
        event = AuditEvent(
            event_type=AuditEventType.PARAM_STATE_CHANGE,
            source="test",
        )
        after = time.time_ns()

        # Timestamp should be between before and after
        assert before <= event.ts_event <= after
        # And should be in nanoseconds (> 1e18 for year 2020+)
        assert event.ts_event > 1_500_000_000_000_000_000

    def test_serialization(self):
        """Test event serialization to JSON."""
        event = AuditEvent(
            event_type=AuditEventType.PARAM_STATE_CHANGE,
            source="test",
            ts_event=1704067200000000000,
            trader_id="TRADER-001",
            sequence=42,
        )

        json_str = event.model_dump_json()
        data = json.loads(json_str)

        assert data["event_type"] == "param.state_change"
        assert data["source"] == "test"
        assert data["ts_event"] == 1704067200000000000
        assert data["trader_id"] == "TRADER-001"
        assert data["sequence"] == 42
        assert "checksum" in data


class TestParameterChangeEvent:
    """Tests for ParameterChangeEvent."""

    def test_default_event_type(self):
        """Test default event type is PARAM_STATE_CHANGE."""
        event = ParameterChangeEvent(
            source="test",
            param_name="risk_multiplier",
            old_value="1.0",
            new_value="0.5",
            trigger_reason="drawdown > 10%",
        )

        assert event.event_type == AuditEventType.PARAM_STATE_CHANGE

    def test_serialization(self):
        """Test parameter change event serialization."""
        event = ParameterChangeEvent(
            source="meta_controller",
            param_name="system_state",
            old_value="VENTRAL",
            new_value="SYMPATHETIC",
            trigger_reason="health_score=65.3",
            ts_event=1704067200000000000,
        )

        json_str = event.model_dump_json()
        data = json.loads(json_str)

        assert data["event_type"] == "param.state_change"
        assert data["param_name"] == "system_state"
        assert data["old_value"] == "VENTRAL"
        assert data["new_value"] == "SYMPATHETIC"
        assert data["trigger_reason"] == "health_score=65.3"
        assert data["source"] == "meta_controller"

    def test_checksum_includes_all_fields(self):
        """Test that checksum includes param change fields."""
        event1 = ParameterChangeEvent(
            source="test",
            param_name="k",
            old_value="1.0",
            new_value="1.5",
            trigger_reason="reason",
            ts_event=1704067200000000000,
        )
        event2 = ParameterChangeEvent(
            source="test",
            param_name="k",
            old_value="1.0",
            new_value="2.0",  # Different new_value
            trigger_reason="reason",
            ts_event=1704067200000000000,
        )

        assert event1.checksum != event2.checksum


class TestTradeEvent:
    """Tests for TradeEvent."""

    def test_default_event_type(self):
        """Test default event type is TRADE_FILL."""
        event = TradeEvent(
            source="nautilus_trader",
            order_id="O-001",
            instrument_id="BTCUSDT-PERP.BINANCE",
            side="BUY",
            size="0.5",
            price="42000.00",
            strategy_source="momentum_v1",
        )

        assert event.event_type == AuditEventType.TRADE_FILL

    def test_serialization(self):
        """Test trade event serialization."""
        event = TradeEvent(
            source="nautilus_trader",
            order_id="O-001",
            instrument_id="BTCUSDT-PERP.BINANCE",
            side="BUY",
            size="0.5",
            price="42000.00",
            slippage_bps=1.5,
            realized_pnl="100.50",
            strategy_source="momentum_v1",
            ts_event=1704067200000000000,
        )

        json_str = event.model_dump_json()
        data = json.loads(json_str)

        assert data["event_type"] == "trade.fill"
        assert data["order_id"] == "O-001"
        assert data["instrument_id"] == "BTCUSDT-PERP.BINANCE"
        assert data["side"] == "BUY"
        assert data["size"] == "0.5"
        assert data["price"] == "42000.00"
        assert data["slippage_bps"] == 1.5
        assert data["realized_pnl"] == "100.50"


class TestSignalEvent:
    """Tests for SignalEvent."""

    def test_default_event_type(self):
        """Test default event type is TRADE_SIGNAL."""
        event = SignalEvent(
            source="particle_portfolio",
            signal_value=0.75,
            regime="TRENDING",
            confidence=0.85,
            strategy_source="ensemble_v1",
        )

        assert event.event_type == AuditEventType.TRADE_SIGNAL

    def test_serialization(self):
        """Test signal event serialization."""
        event = SignalEvent(
            source="particle_portfolio",
            signal_value=0.75,
            regime="TRENDING",
            confidence=0.85,
            strategy_source="ensemble_v1",
            ts_event=1704067200000000000,
        )

        json_str = event.model_dump_json()
        data = json.loads(json_str)

        assert data["event_type"] == "trade.signal"
        assert data["signal_value"] == 0.75
        assert data["regime"] == "TRENDING"
        assert data["confidence"] == 0.85
        assert data["strategy_source"] == "ensemble_v1"


class TestSystemEvent:
    """Tests for SystemEvent."""

    def test_payload_serialization(self):
        """Test system event with complex payload."""
        event = SystemEvent(
            event_type=AuditEventType.SYS_EVOLUTION_TRIGGER,
            source="alpha_evolve_bridge",
            payload={
                "trigger_reason": "DISSONANCE",
                "underperforming_strategy": "momentum_v1",
                "dissonance_score": 0.75,
            },
            ts_event=1704067200000000000,
        )

        json_str = event.model_dump_json()
        data = json.loads(json_str)

        assert data["event_type"] == "sys.evolution_trigger"
        assert data["payload"]["trigger_reason"] == "DISSONANCE"
        assert data["payload"]["dissonance_score"] == 0.75
