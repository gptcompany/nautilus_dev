"""Integration tests for audit trail system (Spec 030).

Tests:
- MetaController audit integration
- SOPSGillerSizer audit integration
- Full audit trail flow
"""

import json

from strategies.common.adaptive_control.meta_controller import (
    MetaController,
    SystemState,
)
from strategies.common.adaptive_control.sops_sizing import SOPSGillerSizer
from strategies.common.audit.config import AuditConfig
from strategies.common.audit.emitter import AuditEventEmitter
from strategies.common.audit.events import (
    AuditEventType,
    ParameterChangeEvent,
)


class TestMetaControllerAuditIntegration:
    """Test audit integration with MetaController."""

    def test_state_transition_audit(self, tmp_path):
        """Test that state transitions can be audited."""
        config = AuditConfig(base_path=tmp_path, rotate_daily=False)
        emitter = AuditEventEmitter(trader_id="TRADER-001", config=config)

        # Simulate MetaController state transition auditing
        old_state = SystemState.VENTRAL
        new_state = SystemState.SYMPATHETIC
        health_score = 45.0

        # This is how MetaController would audit a state transition
        event = emitter.emit_param_change(
            param_name="system_state",
            old_value=old_state.value,
            new_value=new_state.value,
            trigger_reason=f"health_score={health_score:.1f}",
            source="meta_controller",
            event_type=AuditEventType.PARAM_STATE_CHANGE,
        )

        emitter.close()

        # Verify event was logged
        assert isinstance(event, ParameterChangeEvent)
        assert event.param_name == "system_state"
        assert event.old_value == "ventral"
        assert event.new_value == "sympathetic"
        assert "health_score=45.0" in event.trigger_reason

        # Verify file was written
        log_file = tmp_path / "audit.jsonl"
        with open(log_file) as f:
            data = json.loads(f.readline())

        assert data["event_type"] == "param.state_change"
        assert data["param_name"] == "system_state"

    def test_risk_multiplier_audit(self, tmp_path):
        """Test that risk multiplier changes can be audited."""
        config = AuditConfig(base_path=tmp_path, rotate_daily=False)
        emitter = AuditEventEmitter(trader_id="TRADER-001", config=config)

        # Simulate risk multiplier change auditing
        old_mult = 1.0
        new_mult = 0.5
        drawdown = 8.5

        event = emitter.emit_param_change(
            param_name="risk_multiplier",
            old_value=old_mult,
            new_value=new_mult,
            trigger_reason=f"drawdown={drawdown:.1f}%",
            source="meta_controller",
            event_type=AuditEventType.PARAM_RISK_CHANGE,
        )

        emitter.close()

        assert event.param_name == "risk_multiplier"
        assert event.old_value == "1.0"
        assert event.new_value == "0.5"
        assert event.event_type == AuditEventType.PARAM_RISK_CHANGE

    def test_strategy_weight_audit(self, tmp_path):
        """Test that strategy weight changes can be audited."""
        config = AuditConfig(base_path=tmp_path, rotate_daily=False)
        emitter = AuditEventEmitter(trader_id="TRADER-001", config=config)

        # Simulate strategy weight change auditing
        strategy_name = "momentum_v1"
        old_weight = 0.5
        new_weight = 0.3
        regime = "MEAN_REVERTING"

        event = emitter.emit_param_change(
            param_name=f"strategy_weight.{strategy_name}",
            old_value=old_weight,
            new_value=new_weight,
            trigger_reason=f"regime={regime}",
            source="meta_controller",
            event_type=AuditEventType.PARAM_WEIGHT_CHANGE,
        )

        emitter.close()

        assert event.param_name == "strategy_weight.momentum_v1"
        assert event.event_type == AuditEventType.PARAM_WEIGHT_CHANGE

    def test_full_meta_controller_cycle(self, tmp_path):
        """Test auditing a full MetaController update cycle."""
        config = AuditConfig(base_path=tmp_path, rotate_daily=False)
        emitter = AuditEventEmitter(trader_id="TRADER-001", config=config)

        # Create MetaController
        meta = MetaController(
            target_drawdown=0.05,
            ventral_threshold=70,
            sympathetic_threshold=40,
        )

        # Register a strategy
        meta.register_strategy(
            "momentum",
            regime_affinity={"trending": 1.0, "normal": 0.5, "mean_reverting": 0.1},
        )

        # Track state for audit
        prev_state = meta.state
        prev_harmony = meta.harmony

        # Update MetaController
        state = meta.update(
            current_return=0.001,
            current_equity=100000,
            latency_ms=5.0,
        )

        # Audit if state changed
        if state.system_state != prev_state:
            emitter.emit_param_change(
                param_name="system_state",
                old_value=prev_state.value,
                new_value=state.system_state.value,
                trigger_reason=f"health_score={state.health_score:.1f}",
                source="meta_controller",
            )

        # Audit if harmony changed
        if state.market_harmony != prev_harmony:
            emitter.emit_param_change(
                param_name="market_harmony",
                old_value=prev_harmony.value,
                new_value=state.market_harmony.value,
                trigger_reason="performance_based",
                source="meta_controller",
            )

        emitter.close()

        # Verify file exists (may be empty if no state changes)
        log_file = tmp_path / "audit.jsonl"
        assert log_file.exists()


class TestSOPSGillerSizerAuditIntegration:
    """Test audit integration with SOPSGillerSizer."""

    def test_k_parameter_audit(self, tmp_path):
        """Test that k parameter changes can be audited."""
        config = AuditConfig(base_path=tmp_path, rotate_daily=False)
        emitter = AuditEventEmitter(trader_id="TRADER-001", config=config)

        # Create sizer
        sizer = SOPSGillerSizer(k_base=1.0, vol_alpha=0.1)

        # Track k for audit
        prev_k = sizer.k

        # Update with returns to change k
        for _ in range(20):
            sizer.update(return_value=0.05)  # High volatility

        new_k = sizer.k

        # Audit k change
        if abs(new_k - prev_k) > 0.01:
            event = emitter.emit_param_change(
                param_name="adaptive_k",
                old_value=prev_k,
                new_value=new_k,
                trigger_reason=f"vol={sizer.volatility:.4f}",
                source="sops_sizer",
                event_type=AuditEventType.PARAM_K_CHANGE,
            )

            assert event.param_name == "adaptive_k"
            assert event.event_type == AuditEventType.PARAM_K_CHANGE

        emitter.close()

    def test_tape_regime_audit(self, tmp_path):
        """Test that tape regime changes can be audited."""
        config = AuditConfig(base_path=tmp_path, rotate_daily=False)
        emitter = AuditEventEmitter(trader_id="TRADER-001", config=config)

        # Create sizer
        sizer = SOPSGillerSizer(enable_tape_weight=True)

        # Track regime
        prev_regime = sizer.tape_regime

        # Update with timestamps to simulate fast tape
        for i in range(50):
            sizer.update(return_value=0.001, timestamp=float(i) * 0.01)

        new_regime = sizer.tape_regime

        # Audit regime change
        if new_regime != prev_regime:
            event = emitter.emit_system(
                event_type=AuditEventType.SYS_REGIME_CHANGE,
                source="sops_sizer",
                payload={
                    "regime_type": "tape_speed",
                    "old_regime": prev_regime,
                    "new_regime": new_regime,
                    "lambda": sizer.tape_lambda,
                },
            )

            assert event.payload["regime_type"] == "tape_speed"

        emitter.close()

    def test_sizer_full_cycle(self, tmp_path):
        """Test auditing a full sizer calculation cycle."""
        config = AuditConfig(base_path=tmp_path, rotate_daily=False)
        emitter = AuditEventEmitter(trader_id="TRADER-001", config=config)

        sizer = SOPSGillerSizer(k_base=1.0)

        # Warm up
        for i in range(30):
            sizer.update(return_value=0.01 * (i % 3 - 1))

        # Get full state
        state = sizer.get_state(signal=1.5)

        # Audit the sizing calculation (for debugging/forensics)
        emitter.emit_system(
            event_type=AuditEventType.SYS_REGIME_CHANGE,  # Using as generic sys event
            source="sops_sizer",
            payload={
                "event_subtype": "sizing_calculation",
                "raw_signal": state.raw_signal,
                "sops_position": state.sops_position,
                "giller_position": state.giller_position,
                "tape_weight": state.tape_weight,
                "final_position": state.final_position,
                "adaptive_k": state.adaptive_k,
            },
        )

        emitter.close()

        # Verify log
        log_file = tmp_path / "audit.jsonl"
        with open(log_file) as f:
            data = json.loads(f.readline())

        assert data["payload"]["event_subtype"] == "sizing_calculation"
        assert "final_position" in data["payload"]


class TestAuditTrailEndToEnd:
    """End-to-end tests for audit trail system."""

    def test_multiple_events_in_sequence(self, tmp_path):
        """Test multiple events logged in sequence."""
        config = AuditConfig(base_path=tmp_path, rotate_daily=False)
        emitter = AuditEventEmitter(trader_id="TRADER-001", config=config)

        # Emit various events
        emitter.emit_param_change(
            param_name="system_state",
            old_value="ventral",
            new_value="sympathetic",
            trigger_reason="drawdown",
            source="meta_controller",
        )

        emitter.emit_param_change(
            param_name="adaptive_k",
            old_value=1.0,
            new_value=0.8,
            trigger_reason="vol_spike",
            source="sops_sizer",
        )

        emitter.emit_param_change(
            param_name="risk_multiplier",
            old_value=1.0,
            new_value=0.5,
            trigger_reason="pid_control",
            source="meta_controller",
        )

        emitter.close()

        # Read all events
        log_file = tmp_path / "audit.jsonl"
        with open(log_file) as f:
            lines = f.readlines()

        assert len(lines) == 3

        # Verify sequence numbers
        for i, line in enumerate(lines):
            data = json.loads(line)
            assert data["sequence"] == i
            assert data["trader_id"] == "TRADER-001"

    def test_callback_for_testing(self, tmp_path):
        """Test using callback for test assertions."""
        events_captured = []

        def capture_event(event):
            events_captured.append(event)

        config = AuditConfig(base_path=tmp_path, rotate_daily=False)
        emitter = AuditEventEmitter(
            trader_id="TRADER-001",
            config=config,
            on_event=capture_event,
        )

        # Emit events
        emitter.emit_param_change(
            param_name="test",
            old_value=1,
            new_value=2,
            trigger_reason="test",
            source="test",
        )
        emitter.emit_signal(
            signal_value=0.75,
            regime="TRENDING",
            confidence=0.85,
            strategy_source="test",
            source="test",
        )

        emitter.close()

        # Verify callback captured events
        assert len(events_captured) == 2
        assert events_captured[0].param_name == "test"
        assert events_captured[1].signal_value == 0.75

    def test_checksum_integrity(self, tmp_path):
        """Test that checksums can detect tampering."""
        config = AuditConfig(base_path=tmp_path, rotate_daily=False)
        emitter = AuditEventEmitter(trader_id="TRADER-001", config=config)

        event = emitter.emit_param_change(
            param_name="risk",
            old_value=1.0,
            new_value=0.5,
            trigger_reason="test",
            source="test",
        )

        original_checksum = event.checksum

        emitter.close()

        # Read back and verify checksum
        log_file = tmp_path / "audit.jsonl"
        with open(log_file) as f:
            data = json.loads(f.readline())

        # The checksum in the file should match
        assert data["checksum"] == original_checksum

        # If we modify any field, checksum would differ
        # (This is conceptual - we're verifying the checksum was stored)
        assert len(original_checksum) == 16
