"""Comprehensive tests for SystemHealthMonitor.

Focus on:
- Health state transitions (HEALTHY -> DEGRADED -> CRITICAL)
- Metrics calculation (latency, rejection rate, slippage, drawdown)
- Risk multiplier based on health state
- Callback mechanism for state changes
- Edge cases: extreme drawdowns, many reconnections
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

from strategies.common.adaptive_control.system_health import (
    HealthMetrics,
    HealthState,
    SystemHealthMonitor,
)


class TestHealthState:
    """Test HealthState enum."""

    def test_health_states_exist(self):
        """Test all health states are defined."""
        assert HealthState.HEALTHY.value == "healthy"
        assert HealthState.DEGRADED.value == "degraded"
        assert HealthState.CRITICAL.value == "critical"


class TestHealthMetrics:
    """Test HealthMetrics dataclass."""

    def test_health_metrics_creation(self):
        """Test creating HealthMetrics instance."""
        now = datetime.now(UTC)
        metrics = HealthMetrics(
            timestamp=now,
            latency_mean_ms=45.0,
            latency_p99_ms=95.0,
            rejection_rate=0.02,
            slippage_bps=1.5,
            drawdown_pct=2.5,
            reconnects_1h=1,
            state=HealthState.HEALTHY,
            score=85.0,
        )

        assert metrics.timestamp == now
        assert metrics.latency_mean_ms == 45.0
        assert metrics.latency_p99_ms == 95.0
        assert metrics.rejection_rate == 0.02
        assert metrics.slippage_bps == 1.5
        assert metrics.drawdown_pct == 2.5
        assert metrics.reconnects_1h == 1
        assert metrics.state == HealthState.HEALTHY
        assert metrics.score == 85.0


class TestSystemHealthMonitorInitialization:
    """Test SystemHealthMonitor initialization."""

    def test_default_initialization(self):
        """Test default initialization."""
        health = SystemHealthMonitor()
        assert health.latency_threshold == 100.0
        assert health.rejection_threshold == 0.05
        assert health.drawdown_halt_pct == 10.0

    def test_custom_initialization(self):
        """Test custom initialization."""
        health = SystemHealthMonitor(
            latency_threshold_ms=50.0,
            rejection_threshold=0.03,
            drawdown_halt_pct=5.0,
        )
        assert health.latency_threshold == 50.0
        assert health.rejection_threshold == 0.03
        assert health.drawdown_halt_pct == 5.0

    def test_initial_state(self):
        """Test initial internal state."""
        health = SystemHealthMonitor()
        assert len(health._latencies) == 0
        assert len(health._fills) == 0
        assert len(health._rejections) == 0
        assert len(health._reconnects) == 0
        assert health._peak_equity == 0.0
        assert health._current_equity == 0.0


class TestRecordingEvents:
    """Test recording various events."""

    def test_record_latency(self):
        """Test recording latency."""
        health = SystemHealthMonitor()
        health.record_latency(45.5)

        assert len(health._latencies) == 1
        timestamp, latency = health._latencies[0]
        assert isinstance(timestamp, datetime)
        assert latency == 45.5

    def test_record_multiple_latencies(self):
        """Test recording multiple latencies."""
        health = SystemHealthMonitor()

        for i in range(10):
            health.record_latency(float(i))

        assert len(health._latencies) == 10

    def test_record_fill(self):
        """Test recording fill."""
        health = SystemHealthMonitor()
        health.record_fill(slippage_bps=2.5)

        assert len(health._fills) == 1
        timestamp, slippage = health._fills[0]
        assert isinstance(timestamp, datetime)
        assert slippage == 2.5

    def test_record_fill_no_slippage(self):
        """Test recording fill with no slippage."""
        health = SystemHealthMonitor()
        health.record_fill()

        timestamp, slippage = health._fills[0]
        assert slippage == 0.0

    def test_record_rejection(self):
        """Test recording order rejection."""
        health = SystemHealthMonitor()
        health.record_rejection()

        assert len(health._rejections) == 1
        assert isinstance(health._rejections[0], datetime)

    def test_record_reconnect(self):
        """Test recording reconnection."""
        health = SystemHealthMonitor()
        health.record_reconnect()

        assert len(health._reconnects) == 1
        assert isinstance(health._reconnects[0], datetime)

    def test_set_equity(self):
        """Test setting equity."""
        health = SystemHealthMonitor()
        health.set_equity(10000.0)

        assert health._current_equity == 10000.0
        assert health._peak_equity == 10000.0

    def test_set_equity_updates_peak(self):
        """Test that equity updates peak when higher."""
        health = SystemHealthMonitor()
        health.set_equity(10000.0)
        health.set_equity(12000.0)

        assert health._current_equity == 12000.0
        assert health._peak_equity == 12000.0

    def test_set_equity_does_not_lower_peak(self):
        """Test that lower equity doesn't reduce peak."""
        health = SystemHealthMonitor()
        health.set_equity(10000.0)
        health.set_equity(8000.0)

        assert health._current_equity == 8000.0
        assert health._peak_equity == 10000.0  # Peak stays at 10k


class TestDrawdownCalculation:
    """Test drawdown calculation."""

    def test_drawdown_zero_with_no_equity(self):
        """Test drawdown is zero when no equity set."""
        health = SystemHealthMonitor()
        assert health.drawdown_pct == 0.0

    def test_drawdown_zero_at_peak(self):
        """Test drawdown is zero at peak."""
        health = SystemHealthMonitor()
        health.set_equity(10000.0)
        assert health.drawdown_pct == 0.0

    def test_drawdown_calculation(self):
        """Test drawdown percentage calculation."""
        health = SystemHealthMonitor()
        health.set_equity(10000.0)
        health.set_equity(9000.0)

        # 10% drawdown
        assert health.drawdown_pct == 10.0

    def test_drawdown_large(self):
        """Test large drawdown calculation."""
        health = SystemHealthMonitor()
        health.set_equity(10000.0)
        health.set_equity(5000.0)

        # 50% drawdown
        assert health.drawdown_pct == 50.0

    def test_drawdown_resets_with_new_peak(self):
        """Test drawdown resets when equity reaches new peak."""
        health = SystemHealthMonitor()
        health.set_equity(10000.0)
        health.set_equity(9000.0)
        assert health.drawdown_pct == 10.0

        health.set_equity(11000.0)
        assert health.drawdown_pct == 0.0


class TestMetricsCalculation:
    """Test health metrics calculation."""

    def test_get_metrics_empty(self):
        """Test metrics with no data."""
        health = SystemHealthMonitor()
        metrics = health.get_metrics()

        assert metrics.latency_mean_ms == 0.0
        assert metrics.latency_p99_ms == 0.0
        assert metrics.rejection_rate == 0.0
        assert metrics.slippage_bps == 0.0
        assert metrics.drawdown_pct == 0.0
        assert metrics.reconnects_1h == 0
        assert metrics.state == HealthState.HEALTHY
        assert metrics.score == 100.0

    def test_get_metrics_latency(self):
        """Test latency metrics calculation."""
        health = SystemHealthMonitor()

        latencies = [10, 20, 30, 40, 50, 100, 200]
        for lat in latencies:
            health.record_latency(float(lat))

        metrics = health.get_metrics()
        assert metrics.latency_mean_ms > 0
        assert metrics.latency_p99_ms >= metrics.latency_mean_ms

    def test_get_metrics_rejection_rate(self):
        """Test rejection rate calculation."""
        health = SystemHealthMonitor()

        # 2 rejections, 8 fills = 20% rejection rate
        for _ in range(2):
            health.record_rejection()
        for _ in range(8):
            health.record_fill()

        metrics = health.get_metrics()
        assert 0.19 < metrics.rejection_rate < 0.21  # ~20%

    def test_get_metrics_slippage(self):
        """Test average slippage calculation."""
        health = SystemHealthMonitor()

        slippages = [1.0, 2.0, 3.0, 4.0, 5.0]
        for slip in slippages:
            health.record_fill(slippage_bps=slip)

        metrics = health.get_metrics()
        assert 2.9 < metrics.slippage_bps < 3.1  # Average = 3.0

    def test_get_metrics_reconnects(self):
        """Test reconnects counting."""
        health = SystemHealthMonitor()

        for _ in range(3):
            health.record_reconnect()

        metrics = health.get_metrics()
        assert metrics.reconnects_1h == 3


class TestHealthStates:
    """Test health state determination."""

    def test_healthy_state(self):
        """Test HEALTHY state conditions."""
        health = SystemHealthMonitor()

        # Good metrics
        health.set_equity(10000.0)
        health.record_latency(50.0)
        health.record_fill(slippage_bps=1.0)

        metrics = health.get_metrics()
        assert metrics.state == HealthState.HEALTHY
        assert metrics.score >= 70

    def test_degraded_state_high_latency(self):
        """Test DEGRADED state due to high latency."""
        health = SystemHealthMonitor(latency_threshold_ms=50.0)

        # Very high latency to bring score below 70
        # Score penalty: min(20, (200-50)/5) = 20, plus rejections
        for _ in range(20):
            health.record_latency(200.0)  # Much higher latency
        # Add rejections to push score below 70: 20% rejection = 10 point penalty
        # Total: 100 - 20 (latency) - 10 (rejections) = 70, need one more
        for _ in range(21):
            health.record_rejection()
        for _ in range(79):
            health.record_fill()

        # Check state via property (which calls get_metrics internally)
        assert health.state == HealthState.DEGRADED

        # Get metrics to verify score
        metrics = health.get_metrics()
        assert 40 <= metrics.score < 70

    def test_degraded_state_high_rejections(self):
        """Test DEGRADED state due to high rejection rate."""
        health = SystemHealthMonitor()

        # High rejection rate (45%) - penalty = 0.45 * 50 = 22.5
        for _ in range(45):
            health.record_rejection()
        for _ in range(55):
            health.record_fill()
        # Add latency to push score below 70: default threshold is 100ms
        # penalty = min(20, (200-100)/5) = 20
        for _ in range(20):
            health.record_latency(200.0)

        # Check state via property (which calls get_metrics internally)
        assert health.state == HealthState.DEGRADED

    def test_critical_state_drawdown(self):
        """Test CRITICAL state due to drawdown."""
        health = SystemHealthMonitor(drawdown_halt_pct=10.0)

        # Exceed drawdown threshold
        health.set_equity(10000.0)
        health.set_equity(8900.0)  # 11% drawdown
        health.record_fill()

        metrics = health.get_metrics()
        assert metrics.state == HealthState.CRITICAL

    def test_critical_state_low_score(self):
        """Test CRITICAL state due to low score."""
        health = SystemHealthMonitor()

        # Terrible metrics
        for _ in range(50):
            health.record_latency(500.0)
            health.record_rejection()
        for _ in range(50):
            health.record_fill(slippage_bps=50.0)

        metrics = health.get_metrics()
        assert metrics.state == HealthState.CRITICAL
        assert metrics.score < 40

    def test_critical_state_multiple_reconnects(self):
        """Test CRITICAL state with many reconnections."""
        health = SystemHealthMonitor()

        # Many reconnects
        for _ in range(10):
            health.record_reconnect()
        health.record_fill()

        metrics = health.get_metrics()
        # Score penalty: 10 reconnects * 5 = 50 points off
        assert metrics.score <= 50


class TestScoreCalculation:
    """Test health score calculation."""

    def test_score_starts_at_100(self):
        """Test score starts at 100 with no issues."""
        health = SystemHealthMonitor()
        health.record_fill()  # Need at least one event

        metrics = health.get_metrics()
        assert metrics.score == 100.0

    def test_score_penalty_latency(self):
        """Test score penalty for high latency."""
        health = SystemHealthMonitor(latency_threshold_ms=100.0)

        # Latency way above threshold
        for _ in range(20):
            health.record_latency(200.0)  # 100ms over threshold
        health.record_fill()

        metrics = health.get_metrics()
        assert metrics.score < 100.0

    def test_score_penalty_rejections(self):
        """Test score penalty for rejections."""
        health = SystemHealthMonitor()

        for _ in range(20):
            health.record_rejection()
        for _ in range(80):
            health.record_fill()

        metrics = health.get_metrics()
        # 20% rejection rate → 50 * 0.2 = 10 point penalty
        assert metrics.score < 95.0

    def test_score_bounds(self):
        """Test score is bounded [0, 100]."""
        health = SystemHealthMonitor()

        # Catastrophic metrics
        for _ in range(100):
            health.record_latency(1000.0)
            health.record_rejection()
            health.record_reconnect()
        health.set_equity(10000.0)
        health.set_equity(1000.0)  # 90% drawdown

        metrics = health.get_metrics()
        assert 0 <= metrics.score <= 100


class TestStateChangeCallbacks:
    """Test state change callback mechanism."""

    def test_register_callback(self):
        """Test registering callback."""
        health = SystemHealthMonitor()
        callback = Mock()

        health.on_state_change(callback)
        assert callback in health._on_state_change

    def test_callback_triggered_on_state_change(self):
        """Test callback is triggered when state changes."""
        health = SystemHealthMonitor()
        callback = Mock()
        health.on_state_change(callback)

        # Start in HEALTHY state
        health.record_fill()
        health.get_metrics()

        # Trigger CRITICAL state
        health.set_equity(10000.0)
        health.set_equity(8000.0)  # 20% drawdown
        health.get_metrics()

        # Callback should be called
        callback.assert_called_once()
        old_state, new_state = callback.call_args[0]
        assert old_state == HealthState.HEALTHY
        assert new_state == HealthState.CRITICAL

    def test_callback_not_triggered_same_state(self):
        """Test callback not triggered when state doesn't change."""
        health = SystemHealthMonitor()
        callback = Mock()
        health.on_state_change(callback)

        # Stay in HEALTHY state
        health.record_fill()
        health.get_metrics()
        health.record_fill()
        health.get_metrics()

        # Callback should not be called
        callback.assert_not_called()

    def test_multiple_callbacks(self):
        """Test multiple callbacks registered."""
        health = SystemHealthMonitor()
        callback1 = Mock()
        callback2 = Mock()

        health.on_state_change(callback1)
        health.on_state_change(callback2)

        # Trigger state change
        health.record_fill()
        health.get_metrics()

        health.set_equity(10000.0)
        health.set_equity(5000.0)
        health.get_metrics()

        # Both callbacks should be called
        callback1.assert_called_once()
        callback2.assert_called_once()


class TestRiskMultiplier:
    """Test risk multiplier based on health state."""

    def test_risk_multiplier_healthy(self):
        """Test risk multiplier for HEALTHY state."""
        health = SystemHealthMonitor()
        health.record_fill()

        assert health.risk_multiplier == 1.0

    def test_risk_multiplier_degraded(self):
        """Test risk multiplier for DEGRADED state."""
        health = SystemHealthMonitor()

        # Trigger DEGRADED - 45% rejection rate plus high latency
        for _ in range(45):
            health.record_rejection()
        for _ in range(55):
            health.record_fill()
        for _ in range(20):
            health.record_latency(200.0)

        # risk_multiplier property calls get_metrics() internally
        assert health.risk_multiplier == 0.5

    def test_risk_multiplier_critical(self):
        """Test risk multiplier for CRITICAL state."""
        health = SystemHealthMonitor()

        # Trigger CRITICAL
        health.set_equity(10000.0)
        health.set_equity(8000.0)
        health.record_fill()

        assert health.risk_multiplier == 0.0


class TestShouldTrade:
    """Test should_trade decision logic."""

    def test_should_trade_healthy(self):
        """Test should trade in HEALTHY state."""
        health = SystemHealthMonitor()
        health.record_fill()

        should_trade, reason = health.should_trade()
        assert should_trade is True
        assert "healthy" in reason.lower()

    def test_should_trade_degraded(self):
        """Test should trade in DEGRADED state."""
        health = SystemHealthMonitor()

        # Trigger DEGRADED - 45% rejection rate plus high latency
        for _ in range(45):
            health.record_rejection()
        for _ in range(55):
            health.record_fill()
        for _ in range(20):
            health.record_latency(200.0)

        # should_trade() calls get_metrics() internally
        should_trade, reason = health.should_trade()
        assert should_trade is True
        assert "degraded" in reason.lower()

    def test_should_not_trade_critical(self):
        """Test should NOT trade in CRITICAL state."""
        health = SystemHealthMonitor()

        # Trigger CRITICAL
        health.set_equity(10000.0)
        health.set_equity(8000.0)
        health.record_fill()

        should_trade, reason = health.should_trade()
        assert should_trade is False
        assert "CRITICAL" in reason


class TestStateProperty:
    """Test state property accessor."""

    def test_state_property(self):
        """Test state property returns current state."""
        health = SystemHealthMonitor()
        health.record_fill()

        assert health.state == HealthState.HEALTHY

    def test_state_property_reflects_changes(self):
        """Test state property reflects state changes."""
        health = SystemHealthMonitor()
        health.record_fill()
        assert health.state == HealthState.HEALTHY

        # Trigger CRITICAL
        health.set_equity(10000.0)
        health.set_equity(5000.0)
        assert health.state == HealthState.CRITICAL


class TestEdgeCases:
    """Test edge cases and extreme conditions."""

    def test_extreme_drawdown(self):
        """Test extreme drawdown (99%)."""
        health = SystemHealthMonitor()
        health.set_equity(10000.0)
        health.set_equity(100.0)
        health.record_fill()

        metrics = health.get_metrics()
        assert metrics.drawdown_pct == 99.0
        assert metrics.state == HealthState.CRITICAL

    def test_zero_to_positive_equity(self):
        """Test equity going from 0 to positive."""
        health = SystemHealthMonitor()
        health.set_equity(0.0)
        health.set_equity(10000.0)

        assert health.drawdown_pct == 0.0

    def test_many_reconnections(self):
        """Test many reconnections."""
        health = SystemHealthMonitor()

        for _ in range(20):
            health.record_reconnect()
        health.record_fill()

        metrics = health.get_metrics()
        assert metrics.reconnects_1h == 20
        assert metrics.state == HealthState.CRITICAL

    def test_extreme_latency(self):
        """Test extreme latency values."""
        health = SystemHealthMonitor()

        for _ in range(10):
            health.record_latency(10000.0)  # 10 seconds!
        # Add rejections and reconnects to push into CRITICAL (score < 40)
        # Latency penalty: 20, Rejection (50%): 25, Reconnects (5): 25
        # Score = 100 - 20 - 25 - 25 = 30 (CRITICAL)
        for _ in range(50):
            health.record_rejection()
        for _ in range(50):
            health.record_fill()
        for _ in range(5):
            health.record_reconnect()

        # Check state via property first
        assert health.state == HealthState.CRITICAL

        # Get metrics to verify latency calculation
        metrics = health.get_metrics()
        assert metrics.latency_mean_ms == 10000.0

    def test_negative_slippage(self):
        """Test negative slippage (price improvement)."""
        health = SystemHealthMonitor()

        for _ in range(10):
            health.record_fill(slippage_bps=-1.0)

        metrics = health.get_metrics()
        assert metrics.slippage_bps == -1.0  # Negative = good

    def test_time_window_filtering(self):
        """Test that old events are filtered out (>1 hour)."""
        health = SystemHealthMonitor()

        # Manually add old event (>1 hour ago)
        old_time = datetime.now(UTC) - timedelta(hours=2)
        health._latencies.append((old_time, 1000.0))

        # Add recent event
        health.record_latency(50.0)
        health.record_fill()

        metrics = health.get_metrics()
        # Should only count recent latency
        assert metrics.latency_mean_ms < 100.0
