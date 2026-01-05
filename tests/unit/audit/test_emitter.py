"""Unit tests for AuditEventEmitter (Spec 030).

Tests:
- Event emission with sequence tracking
- Convenience methods for different event types
- Callback integration
- Context manager usage
"""

import json
from unittest.mock import MagicMock


from strategies.common.audit.config import AuditConfig
from strategies.common.audit.emitter import AuditEventEmitter
from strategies.common.audit.events import (
    AuditEvent,
    AuditEventType,
    ParameterChangeEvent,
    SignalEvent,
    SystemEvent,
    TradeEvent,
)
from strategies.common.audit.writer import AppendOnlyWriter


class TestAuditEventEmitter:
    """Tests for AuditEventEmitter."""

    def test_emit_sets_sequence(self, tmp_path):
        """Test that emit sets monotonic sequence numbers."""
        config = AuditConfig(base_path=tmp_path)
        emitter = AuditEventEmitter(trader_id="TRADER-001", config=config)

        events = []
        for i in range(5):
            event = AuditEvent(
                event_type=AuditEventType.PARAM_STATE_CHANGE,
                source="test",
            )
            emitted = emitter.emit(event)
            events.append(emitted)

        emitter.close()

        # Check sequences are monotonic
        for i, event in enumerate(events):
            assert event.sequence == i

    def test_emit_sets_trader_id(self, tmp_path):
        """Test that emit sets trader_id from emitter."""
        config = AuditConfig(base_path=tmp_path)
        emitter = AuditEventEmitter(trader_id="TRADER-002", config=config)

        event = AuditEvent(
            event_type=AuditEventType.PARAM_STATE_CHANGE,
            source="test",
            trader_id="wrong",  # Should be overwritten
        )
        emitted = emitter.emit(event)
        emitter.close()

        assert emitted.trader_id == "TRADER-002"

    def test_emit_invokes_callback(self, tmp_path):
        """Test that emit invokes optional callback."""
        callback = MagicMock()
        config = AuditConfig(base_path=tmp_path)
        emitter = AuditEventEmitter(
            trader_id="TRADER-001",
            config=config,
            on_event=callback,
        )

        event = AuditEvent(
            event_type=AuditEventType.PARAM_STATE_CHANGE,
            source="test",
        )
        emitter.emit(event)
        emitter.close()

        callback.assert_called_once()
        called_event = callback.call_args[0][0]
        assert called_event.event_type == AuditEventType.PARAM_STATE_CHANGE

    def test_emit_param_change(self, tmp_path):
        """Test emit_param_change convenience method."""
        config = AuditConfig(base_path=tmp_path)
        emitter = AuditEventEmitter(trader_id="TRADER-001", config=config)

        event = emitter.emit_param_change(
            param_name="risk_multiplier",
            old_value=1.0,
            new_value=0.5,
            trigger_reason="drawdown > 10%",
            source="meta_controller",
        )
        emitter.close()

        assert isinstance(event, ParameterChangeEvent)
        assert event.param_name == "risk_multiplier"
        assert event.old_value == "1.0"  # Stringified
        assert event.new_value == "0.5"  # Stringified
        assert event.trigger_reason == "drawdown > 10%"
        assert event.source == "meta_controller"
        assert event.trader_id == "TRADER-001"
        assert event.sequence == 0

    def test_emit_param_change_with_event_type(self, tmp_path):
        """Test emit_param_change with custom event type."""
        config = AuditConfig(base_path=tmp_path)
        emitter = AuditEventEmitter(trader_id="TRADER-001", config=config)

        event = emitter.emit_param_change(
            param_name="adaptive_k",
            old_value=2.0,
            new_value=2.5,
            trigger_reason="vol=0.02",
            source="sops_sizer",
            event_type=AuditEventType.PARAM_K_CHANGE,
        )
        emitter.close()

        assert event.event_type == AuditEventType.PARAM_K_CHANGE

    def test_emit_trade(self, tmp_path):
        """Test emit_trade convenience method."""
        config = AuditConfig(base_path=tmp_path)
        emitter = AuditEventEmitter(trader_id="TRADER-001", config=config)

        event = emitter.emit_trade(
            order_id="O-001",
            instrument_id="BTCUSDT-PERP.BINANCE",
            side="BUY",
            size=0.5,
            price=42000.00,
            strategy_source="momentum_v1",
            slippage_bps=1.5,
            realized_pnl=100.50,
        )
        emitter.close()

        assert isinstance(event, TradeEvent)
        assert event.order_id == "O-001"
        assert event.instrument_id == "BTCUSDT-PERP.BINANCE"
        assert event.side == "BUY"
        assert event.size == "0.5"  # Stringified
        assert event.price == "42000.0"  # Stringified
        assert event.slippage_bps == 1.5
        assert event.realized_pnl == "100.5"  # Stringified

    def test_emit_signal(self, tmp_path):
        """Test emit_signal convenience method."""
        config = AuditConfig(base_path=tmp_path)
        emitter = AuditEventEmitter(trader_id="TRADER-001", config=config)

        event = emitter.emit_signal(
            signal_value=0.75,
            regime="TRENDING",
            confidence=0.85,
            strategy_source="ensemble_v1",
            source="particle_portfolio",
        )
        emitter.close()

        assert isinstance(event, SignalEvent)
        assert event.signal_value == 0.75
        assert event.regime == "TRENDING"
        assert event.confidence == 0.85
        assert event.strategy_source == "ensemble_v1"

    def test_emit_system(self, tmp_path):
        """Test emit_system convenience method."""
        config = AuditConfig(base_path=tmp_path)
        emitter = AuditEventEmitter(trader_id="TRADER-001", config=config)

        event = emitter.emit_system(
            event_type=AuditEventType.SYS_EVOLUTION_TRIGGER,
            source="alpha_evolve_bridge",
            payload={
                "trigger_reason": "DISSONANCE",
                "underperforming_strategy": "momentum_v1",
            },
        )
        emitter.close()

        assert isinstance(event, SystemEvent)
        assert event.event_type == AuditEventType.SYS_EVOLUTION_TRIGGER
        assert event.payload["trigger_reason"] == "DISSONANCE"

    def test_context_manager(self, tmp_path):
        """Test emitter as context manager."""
        config = AuditConfig(base_path=tmp_path)

        with AuditEventEmitter(trader_id="TRADER-001", config=config) as emitter:
            emitter.emit_param_change(
                param_name="test",
                old_value=1,
                new_value=2,
                trigger_reason="test",
                source="test",
            )

        # File should be written
        today_file = list(tmp_path.glob("audit_*.jsonl"))[0]
        assert today_file.exists()

    def test_custom_writer(self, tmp_path):
        """Test emitter with custom writer."""
        writer = AppendOnlyWriter(
            base_path=tmp_path,
            sync_writes=True,  # Custom setting
            rotate_daily=False,  # Custom setting
        )

        emitter = AuditEventEmitter(
            trader_id="TRADER-001",
            writer=writer,
        )

        emitter.emit_param_change(
            param_name="test",
            old_value=1,
            new_value=2,
            trigger_reason="test",
            source="test",
        )

        # Emitter should NOT close writer it doesn't own
        emitter.close()

        # Writer should still be usable
        writer.flush()
        writer.close()

    def test_events_written_to_file(self, tmp_path):
        """Test that events are actually written to file."""
        config = AuditConfig(base_path=tmp_path, rotate_daily=False)
        emitter = AuditEventEmitter(trader_id="TRADER-001", config=config)

        emitter.emit_param_change(
            param_name="risk",
            old_value=1.0,
            new_value=0.5,
            trigger_reason="test",
            source="test",
        )
        emitter.emit_trade(
            order_id="O-001",
            instrument_id="BTCUSDT-PERP.BINANCE",
            side="BUY",
            size="0.5",
            price="42000.00",
            strategy_source="test",
        )
        emitter.close()

        # Read file
        log_file = tmp_path / "audit.jsonl"
        with open(log_file) as f:
            lines = f.readlines()

        assert len(lines) == 2

        event1 = json.loads(lines[0])
        assert event1["event_type"] == "param.state_change"
        assert event1["sequence"] == 0

        event2 = json.loads(lines[1])
        assert event2["event_type"] == "trade.fill"
        assert event2["sequence"] == 1

    def test_sequence_property(self, tmp_path):
        """Test sequence property returns current sequence."""
        config = AuditConfig(base_path=tmp_path)
        emitter = AuditEventEmitter(trader_id="TRADER-001", config=config)

        assert emitter.sequence == 0

        emitter.emit_param_change(
            param_name="test",
            old_value=1,
            new_value=2,
            trigger_reason="test",
            source="test",
        )

        assert emitter.sequence == 1

        emitter.close()

    def test_writer_property(self, tmp_path):
        """Test writer property returns underlying writer."""
        config = AuditConfig(base_path=tmp_path)
        emitter = AuditEventEmitter(trader_id="TRADER-001", config=config)

        assert isinstance(emitter.writer, AppendOnlyWriter)
        assert emitter.writer.base_path == tmp_path

        emitter.close()

    def test_flush(self, tmp_path):
        """Test flush method."""
        config = AuditConfig(base_path=tmp_path)
        emitter = AuditEventEmitter(trader_id="TRADER-001", config=config)

        emitter.emit_param_change(
            param_name="test",
            old_value=1,
            new_value=2,
            trigger_reason="test",
            source="test",
        )

        # Flush should force sync
        emitter.flush()

        emitter.close()
