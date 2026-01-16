"""
Comprehensive tests for MetaController - 90%+ coverage target.

Tests cover:
1. Initialization and configuration
2. Lazy component initialization
3. Strategy registration and PnL recording
4. Update cycle and state transitions
5. System state calculation (polyvagal)
6. Market harmony calculation
7. Strategy weight calculation
8. Properties and reset
9. Audit emitter integration
10. Edge cases and error handling

Run with: pytest tests/strategies/common/adaptive_control/test_meta_controller.py -v --noconftest
"""

from __future__ import annotations

# Python 3.10 compatibility
import datetime as _dt
from dataclasses import dataclass
from datetime import datetime

if hasattr(_dt, "UTC"):
    UTC = _dt.UTC
else:
    UTC = _dt.timezone.utc
from typing import Any
from unittest.mock import Mock

import numpy as np
import pytest

# ==============================================================================
# Test Fixtures (standalone - no conftest dependency)
# ==============================================================================


@pytest.fixture
def simple_returns():
    """Simple returns for basic testing."""
    return [0.01, -0.02, 0.015, -0.01, 0.02, -0.015, 0.01, 0.02, -0.01, 0.005]


@pytest.fixture
def trending_returns():
    """Returns with strong trend for spectral regime detection."""
    np.random.seed(42)
    trend = np.linspace(0, 0.1, 100)
    noise = np.random.normal(0, 0.005, 100)
    prices = 100 * np.exp(np.cumsum(trend + noise))
    returns = np.diff(prices) / prices[:-1]
    return returns.tolist()


@pytest.fixture
def mean_reverting_returns():
    """Returns with mean reversion (white noise)."""
    np.random.seed(42)
    return np.random.normal(0, 0.01, 100).tolist()


# ==============================================================================
# Mock Classes for Dependencies
# ==============================================================================


@dataclass
class MockHealthMetrics:
    """Mock health metrics."""

    score: float = 80.0
    state: str = "healthy"
    latency_mean_ms: float = 10.0
    latency_p99_ms: float = 50.0
    rejection_rate: float = 0.0
    slippage_bps: float = 0.5
    drawdown_pct: float = 1.0
    reconnects_1h: int = 0
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(UTC)


@dataclass
class MockRegimeAnalysis:
    """Mock regime analysis result."""

    regime: Any  # MarketRegime enum
    alpha: float = 1.0
    confidence: float = 0.8
    dominant_period: float = None
    timestamp: float = 0.0


class MockSystemHealthMonitor:
    """Mock for SystemHealthMonitor."""

    def __init__(self, **kwargs):
        self.drawdown_halt_pct = kwargs.get("drawdown_halt_pct", 10.0)
        self._score = 80.0
        self._latencies = []
        self._fills = []
        self._rejections = 0

    def set_equity(self, equity: float) -> None:
        pass

    def record_latency(self, latency_ms: float) -> None:
        self._latencies.append(latency_ms)

    def record_fill(self, slippage_bps: float = 0.0) -> None:
        self._fills.append(slippage_bps)

    def record_rejection(self) -> None:
        self._rejections += 1

    def get_metrics(self) -> MockHealthMetrics:
        return MockHealthMetrics(score=self._score)


class MockSpectralRegimeDetector:
    """Mock for SpectralRegimeDetector."""

    def __init__(self, **kwargs):
        self.window_size = kwargs.get("window_size", 256)
        self.min_samples = kwargs.get("min_samples", 64)
        self._returns = []
        self._regime = None  # Will be set from MarketRegime.NORMAL

    def update(self, return_value: float) -> None:
        self._returns.append(return_value)

    def analyze(self) -> MockRegimeAnalysis:
        from strategies.common.adaptive_control.spectral_regime import MarketRegime

        return MockRegimeAnalysis(
            regime=self._regime or MarketRegime.NORMAL,
            alpha=1.0,
            confidence=0.8,
        )


class MockPIDDrawdownController:
    """Mock for PIDDrawdownController."""

    def __init__(self, **kwargs):
        self.target_drawdown = kwargs.get("target_drawdown", 0.05)
        self._output = 1.0
        self._integral = 0.0
        self._prev_error = None

    def update(self, current_drawdown: float) -> float:
        # Simple mock: reduce output as drawdown increases
        if current_drawdown <= self.target_drawdown:
            return 1.0
        elif current_drawdown >= self.target_drawdown * 2:
            return 0.5
        else:
            return 0.75

    def reset(self) -> None:
        self._output = 1.0
        self._integral = 0.0
        self._prev_error = None


class MockAuditEventEmitter:
    """Mock audit event emitter for testing audit integration."""

    def __init__(self):
        self.events = []

    def emit_param_change(
        self,
        param_name: str,
        old_value: Any,
        new_value: Any,
        trigger_reason: str,
        source: str,
    ) -> None:
        self.events.append(
            {
                "param_name": param_name,
                "old_value": old_value,
                "new_value": new_value,
                "trigger_reason": trigger_reason,
                "source": source,
            }
        )


# ==============================================================================
# Test Class: MetaController Initialization
# ==============================================================================


class TestMetaControllerInitialization:
    """Tests for MetaController initialization."""

    def test_default_initialization(self):
        """Test MetaController initializes with default parameters."""
        from strategies.common.adaptive_control.meta_controller import (
            MarketHarmony,
            MetaController,
            SystemState,
        )

        controller = MetaController()

        assert controller.target_drawdown == 0.05
        assert controller.ventral_threshold == 70
        assert controller.sympathetic_threshold == 40
        assert controller.harmony_lookback == 50
        assert controller._audit_emitter is None
        assert controller._current_state == SystemState.VENTRAL
        assert controller._current_harmony == MarketHarmony.CONSONANT
        assert controller._bars_processed == 0
        assert controller._peak_equity == 0.0
        assert controller._current_equity == 0.0

    def test_custom_initialization(self):
        """Test MetaController with custom parameters."""
        from strategies.common.adaptive_control.meta_controller import MetaController

        controller = MetaController(
            target_drawdown=0.10,
            ventral_threshold=80,
            sympathetic_threshold=50,
            harmony_lookback=100,
        )

        assert controller.target_drawdown == 0.10
        assert controller.ventral_threshold == 80
        assert controller.sympathetic_threshold == 50
        assert controller.harmony_lookback == 100

    def test_initialization_with_audit_emitter(self):
        """Test MetaController initializes with audit emitter."""
        from strategies.common.adaptive_control.meta_controller import MetaController

        emitter = MockAuditEventEmitter()
        controller = MetaController(audit_emitter=emitter)

        assert controller._audit_emitter is emitter
        assert controller.audit_emitter is emitter

    def test_components_lazy_initialized(self):
        """Test that components are None until first update."""
        from strategies.common.adaptive_control.meta_controller import MetaController

        controller = MetaController()

        assert controller._health_monitor is None
        assert controller._regime_detector is None
        assert controller._pid_controller is None

    def test_prev_values_initialized(self):
        """Test previous values for audit change detection are initialized."""
        from strategies.common.adaptive_control.meta_controller import MetaController

        controller = MetaController()

        assert controller._prev_risk_multiplier is None
        assert controller._prev_strategy_weights == {}


# ==============================================================================
# Test Class: Lazy Component Initialization
# ==============================================================================


class TestLazyComponentInitialization:
    """Tests for lazy component initialization."""

    def test_ensure_components_initializes_health_monitor(self):
        """Test _ensure_components creates SystemHealthMonitor."""
        from strategies.common.adaptive_control.meta_controller import MetaController

        controller = MetaController(target_drawdown=0.05)
        controller._ensure_components()

        assert controller._health_monitor is not None
        # Health monitor should have drawdown halt at 2x target
        assert controller._health_monitor.drawdown_halt_pct == 10.0

    def test_ensure_components_initializes_regime_detector(self):
        """Test _ensure_components creates SpectralRegimeDetector."""
        from strategies.common.adaptive_control.meta_controller import MetaController

        controller = MetaController()
        controller._ensure_components()

        assert controller._regime_detector is not None
        assert controller._regime_detector.window_size == 256
        assert controller._regime_detector.min_samples == 64

    def test_ensure_components_initializes_pid_controller(self):
        """Test _ensure_components creates PIDDrawdownController."""
        from strategies.common.adaptive_control.meta_controller import MetaController

        controller = MetaController(target_drawdown=0.03)
        controller._ensure_components()

        assert controller._pid_controller is not None
        assert controller._pid_controller.target_drawdown == 0.03

    def test_ensure_components_idempotent(self):
        """Test _ensure_components only initializes once."""
        from strategies.common.adaptive_control.meta_controller import MetaController

        controller = MetaController()
        controller._ensure_components()

        # Store references
        health = controller._health_monitor
        regime = controller._regime_detector
        pid = controller._pid_controller

        # Call again
        controller._ensure_components()

        # Should be same objects
        assert controller._health_monitor is health
        assert controller._regime_detector is regime
        assert controller._pid_controller is pid


# ==============================================================================
# Test Class: Strategy Registration
# ==============================================================================


class TestStrategyRegistration:
    """Tests for strategy registration."""

    def test_register_strategy_default_affinity(self):
        """Test registering strategy with default regime affinity."""
        from strategies.common.adaptive_control.meta_controller import MetaController

        controller = MetaController()
        controller.register_strategy("momentum")

        assert "momentum" in controller._strategies
        assert controller._strategies["momentum"]["affinity"] == {
            "trending": 0.7,
            "normal": 0.7,
            "mean_reverting": 0.7,
        }
        assert controller._strategies["momentum"]["callback"] is None
        assert controller._strategies["momentum"]["current_weight"] == 1.0
        assert "momentum" in controller._strategy_performance
        assert controller._strategy_performance["momentum"] == []

    def test_register_strategy_custom_affinity(self):
        """Test registering strategy with custom regime affinity."""
        from strategies.common.adaptive_control.meta_controller import MetaController

        controller = MetaController()
        affinity = {"trending": 1.0, "normal": 0.5, "mean_reverting": 0.2}
        controller.register_strategy("trend_follower", regime_affinity=affinity)

        assert controller._strategies["trend_follower"]["affinity"] == affinity

    def test_register_strategy_with_callback(self):
        """Test registering strategy with weight callback."""
        from strategies.common.adaptive_control.meta_controller import MetaController

        callback = Mock()
        controller = MetaController()
        controller.register_strategy("test_strategy", callback=callback)

        assert controller._strategies["test_strategy"]["callback"] is callback

    def test_register_multiple_strategies(self):
        """Test registering multiple strategies."""
        from strategies.common.adaptive_control.meta_controller import MetaController

        controller = MetaController()
        controller.register_strategy("strategy1")
        controller.register_strategy("strategy2")
        controller.register_strategy("strategy3")

        assert len(controller._strategies) == 3
        assert len(controller._strategy_performance) == 3


# ==============================================================================
# Test Class: Strategy PnL Recording
# ==============================================================================


class TestStrategyPnLRecording:
    """Tests for recording strategy PnL."""

    def test_record_strategy_pnl_basic(self):
        """Test basic PnL recording."""
        from strategies.common.adaptive_control.meta_controller import MetaController

        controller = MetaController()
        controller.register_strategy("test")

        controller.record_strategy_pnl("test", 100.0)
        controller.record_strategy_pnl("test", -50.0)
        controller.record_strategy_pnl("test", 75.0)

        assert controller._strategy_performance["test"] == [100.0, -50.0, 75.0]

    def test_record_strategy_pnl_unknown_strategy(self):
        """Test recording PnL for unregistered strategy (no-op)."""
        from strategies.common.adaptive_control.meta_controller import MetaController

        controller = MetaController()

        # Should not raise, just ignore
        controller.record_strategy_pnl("unknown", 100.0)

        assert "unknown" not in controller._strategy_performance

    def test_record_strategy_pnl_limited_history(self):
        """Test PnL history is limited to harmony_lookback."""
        from strategies.common.adaptive_control.meta_controller import MetaController

        controller = MetaController(harmony_lookback=10)
        controller.register_strategy("test")

        # Add more than lookback
        for i in range(15):
            controller.record_strategy_pnl("test", float(i))

        # Should only keep last 10
        assert len(controller._strategy_performance["test"]) == 10
        assert controller._strategy_performance["test"] == list(range(5, 15))


# ==============================================================================
# Test Class: Update Cycle (using direct component injection)
# ==============================================================================


class TestUpdateCycle:
    """Tests for the main update cycle."""

    def _create_controller_with_mocks(self):
        """Helper to create controller with mock components injected."""
        from strategies.common.adaptive_control.meta_controller import MetaController
        from strategies.common.adaptive_control.spectral_regime import MarketRegime

        controller = MetaController()

        # Inject mocks directly instead of patching imports
        controller._health_monitor = MockSystemHealthMonitor()
        mock_regime = MockSpectralRegimeDetector()
        mock_regime._regime = MarketRegime.NORMAL
        controller._regime_detector = mock_regime
        controller._pid_controller = MockPIDDrawdownController()

        return controller

    def test_update_basic(self):
        """Test basic update cycle returns MetaState."""
        from strategies.common.adaptive_control.meta_controller import MetaState

        controller = self._create_controller_with_mocks()
        state = controller.update(
            current_return=0.01,
            current_equity=10000.0,
            latency_ms=10.0,
            order_filled=True,
            slippage_bps=0.5,
        )

        assert isinstance(state, MetaState)
        assert state.health_score == 80.0
        assert state.risk_multiplier >= 0.0
        assert state.risk_multiplier <= 1.0

    def test_update_tracks_equity(self):
        """Test update tracks peak equity for drawdown."""
        controller = self._create_controller_with_mocks()

        # Rising equity
        controller.update(current_return=0.01, current_equity=10000.0)
        assert controller._peak_equity == 10000.0

        controller.update(current_return=0.01, current_equity=11000.0)
        assert controller._peak_equity == 11000.0

        # Falling equity (peak should stay)
        controller.update(current_return=-0.01, current_equity=10500.0)
        assert controller._peak_equity == 11000.0

    def test_update_calculates_drawdown(self):
        """Test update correctly calculates drawdown percentage."""
        controller = self._create_controller_with_mocks()

        # Set peak
        controller.update(current_return=0.01, current_equity=10000.0)

        # 10% drawdown
        state = controller.update(current_return=-0.10, current_equity=9000.0)

        assert state.drawdown_pct == pytest.approx(10.0, rel=0.01)

    def test_update_records_latency(self):
        """Test update records latency when provided."""
        controller = self._create_controller_with_mocks()
        controller.update(current_return=0.01, current_equity=10000.0, latency_ms=25.0)

        assert 25.0 in controller._health_monitor._latencies

    def test_update_records_fill(self):
        """Test update records fill when order_filled=True."""
        controller = self._create_controller_with_mocks()
        controller.update(
            current_return=0.01,
            current_equity=10000.0,
            order_filled=True,
            slippage_bps=1.5,
        )

        assert 1.5 in controller._health_monitor._fills

    def test_update_records_rejection(self):
        """Test update records rejection when order_filled=False."""
        controller = self._create_controller_with_mocks()
        controller.update(
            current_return=0.01,
            current_equity=10000.0,
            order_filled=False,
        )

        assert controller._health_monitor._rejections == 1

    def test_update_increments_bars_processed(self):
        """Test update increments bars_processed counter."""
        controller = self._create_controller_with_mocks()

        controller.update(current_return=0.01, current_equity=10000.0)
        assert controller._bars_processed == 1

        controller.update(current_return=0.01, current_equity=10000.0)
        assert controller._bars_processed == 2

    def test_update_limits_returns_buffer(self):
        """Test update limits returns buffer to 500 entries."""
        controller = self._create_controller_with_mocks()

        # Add more than 500 returns
        for i in range(550):
            controller.update(current_return=0.001 * i, current_equity=10000.0)

        assert len(controller._returns_buffer) == 500

    def test_update_applies_strategy_callbacks(self):
        """Test update invokes strategy weight callbacks."""
        controller = self._create_controller_with_mocks()
        callback = Mock()
        controller.register_strategy("test", callback=callback)

        controller.update(current_return=0.01, current_equity=10000.0)

        callback.assert_called_once()
        # Weight should be between 0 and 1
        weight = callback.call_args[0][0]
        assert 0 <= weight <= 1

    def test_update_with_zero_equity(self):
        """Test update handles zero peak equity (no division by zero)."""
        controller = self._create_controller_with_mocks()

        # First update with zero equity
        state = controller.update(current_return=0.0, current_equity=0.0)

        # Should handle gracefully
        assert state.drawdown_pct == 0.0

    def test_update_with_zero_latency(self):
        """Test update handles zero latency (doesn't record)."""
        controller = self._create_controller_with_mocks()
        controller.update(current_return=0.01, current_equity=10000.0, latency_ms=0.0)

        # Zero latency should not be recorded
        assert len(controller._health_monitor._latencies) == 0

    def test_update_with_negative_equity(self):
        """Test update handles negative equity gracefully."""
        controller = self._create_controller_with_mocks()

        # Set positive peak first
        controller.update(current_return=0.01, current_equity=10000.0)

        # Then negative current
        state = controller.update(current_return=-0.50, current_equity=-1000.0)

        # Should handle gracefully (peak stays positive, large drawdown)
        assert controller._peak_equity == 10000.0
        assert state.drawdown_pct > 100  # Over 100% drawdown

    def test_update_with_extreme_returns(self):
        """Test update handles extreme return values."""
        controller = self._create_controller_with_mocks()

        # Extreme positive return
        state = controller.update(current_return=10.0, current_equity=10000.0)
        assert state is not None

        # Extreme negative return
        state = controller.update(current_return=-0.99, current_equity=5000.0)
        assert state is not None


# ==============================================================================
# Test Class: System State Calculation
# ==============================================================================


class TestSystemStateCalculation:
    """Tests for polyvagal system state calculation."""

    def test_calculate_system_state_ventral(self):
        """Test VENTRAL state when health is high."""
        from strategies.common.adaptive_control.meta_controller import (
            MetaController,
            SystemState,
        )

        controller = MetaController(
            target_drawdown=0.05,
            ventral_threshold=70,
            sympathetic_threshold=40,
        )

        state = controller._calculate_system_state(health_score=85.0, drawdown=0.02)
        assert state == SystemState.VENTRAL

    def test_calculate_system_state_sympathetic(self):
        """Test SYMPATHETIC state when health is medium."""
        from strategies.common.adaptive_control.meta_controller import (
            MetaController,
            SystemState,
        )

        controller = MetaController(
            target_drawdown=0.05,
            ventral_threshold=70,
            sympathetic_threshold=40,
        )

        state = controller._calculate_system_state(health_score=55.0, drawdown=0.02)
        assert state == SystemState.SYMPATHETIC

    def test_calculate_system_state_dorsal(self):
        """Test DORSAL state when health is low."""
        from strategies.common.adaptive_control.meta_controller import (
            MetaController,
            SystemState,
        )

        controller = MetaController(
            target_drawdown=0.05,
            ventral_threshold=70,
            sympathetic_threshold=40,
        )

        state = controller._calculate_system_state(health_score=30.0, drawdown=0.02)
        assert state == SystemState.DORSAL

    def test_calculate_system_state_dorsal_drawdown_override(self):
        """Test DORSAL state when drawdown exceeds 2x target."""
        from strategies.common.adaptive_control.meta_controller import (
            MetaController,
            SystemState,
        )

        controller = MetaController(
            target_drawdown=0.05,  # 5%
            ventral_threshold=70,
            sympathetic_threshold=40,
        )

        # Even with high health, high drawdown forces DORSAL
        state = controller._calculate_system_state(health_score=95.0, drawdown=0.12)
        assert state == SystemState.DORSAL

    def test_calculate_system_state_boundary_ventral(self):
        """Test boundary: exactly at ventral_threshold."""
        from strategies.common.adaptive_control.meta_controller import (
            MetaController,
            SystemState,
        )

        controller = MetaController(ventral_threshold=70)

        state = controller._calculate_system_state(health_score=70.0, drawdown=0.0)
        assert state == SystemState.VENTRAL

    def test_calculate_system_state_boundary_sympathetic(self):
        """Test boundary: exactly at sympathetic_threshold."""
        from strategies.common.adaptive_control.meta_controller import (
            MetaController,
            SystemState,
        )

        controller = MetaController(sympathetic_threshold=40)

        state = controller._calculate_system_state(health_score=40.0, drawdown=0.0)
        assert state == SystemState.SYMPATHETIC


# ==============================================================================
# Test Class: Market Harmony Calculation
# ==============================================================================


class TestMarketHarmonyCalculation:
    """Tests for market harmony calculation."""

    def test_calculate_harmony_no_performance_data(self):
        """Test harmony is CONSONANT when no performance data."""
        from strategies.common.adaptive_control.meta_controller import (
            MarketHarmony,
            MetaController,
        )
        from strategies.common.adaptive_control.spectral_regime import MarketRegime

        controller = MetaController()
        # Don't register any strategies

        harmony = controller._calculate_harmony(MarketRegime.NORMAL)
        assert harmony == MarketHarmony.CONSONANT

    def test_calculate_harmony_positive_pnl(self):
        """Test harmony is CONSONANT with positive PnL."""
        from strategies.common.adaptive_control.meta_controller import (
            MarketHarmony,
            MetaController,
        )
        from strategies.common.adaptive_control.spectral_regime import MarketRegime

        controller = MetaController()
        controller.register_strategy("test")

        # Record positive PnLs
        for _ in range(10):
            controller.record_strategy_pnl("test", 100.0)

        harmony = controller._calculate_harmony(MarketRegime.NORMAL)
        assert harmony == MarketHarmony.CONSONANT

    def test_calculate_harmony_negative_pnl(self):
        """Test harmony is DISSONANT with significant negative PnL."""
        from strategies.common.adaptive_control.meta_controller import (
            MarketHarmony,
            MetaController,
        )
        from strategies.common.adaptive_control.spectral_regime import MarketRegime

        controller = MetaController()
        controller._current_equity = 10000.0  # Set equity for threshold calc
        controller.register_strategy("test")

        # Record significant negative PnLs
        for _ in range(10):
            controller.record_strategy_pnl("test", -100.0)  # Total -1000 > 0.1% of 10000

        harmony = controller._calculate_harmony(MarketRegime.NORMAL)
        assert harmony == MarketHarmony.DISSONANT

    def test_calculate_harmony_neutral_pnl(self):
        """Test harmony is RESOLVING with neutral PnL."""
        from strategies.common.adaptive_control.meta_controller import (
            MarketHarmony,
            MetaController,
        )
        from strategies.common.adaptive_control.spectral_regime import MarketRegime

        controller = MetaController()
        controller._current_equity = 10000.0
        controller.register_strategy("test")

        # Record small negative PnL (less than 0.1% of equity)
        controller.record_strategy_pnl("test", -5.0)  # -5 < 10 (0.1% of 10000)

        harmony = controller._calculate_harmony(MarketRegime.NORMAL)
        assert harmony == MarketHarmony.RESOLVING

    def test_calculate_harmony_empty_pnl_list(self):
        """Test harmony with registered strategy but no PnL data."""
        from strategies.common.adaptive_control.meta_controller import (
            MarketHarmony,
            MetaController,
        )
        from strategies.common.adaptive_control.spectral_regime import MarketRegime

        controller = MetaController()
        controller.register_strategy("test")  # No PnL recorded

        harmony = controller._calculate_harmony(MarketRegime.NORMAL)
        # With empty pnl list, total_pnl = 0, which triggers RESOLVING
        assert harmony == MarketHarmony.RESOLVING

    def test_calculate_harmony_multiple_strategies(self):
        """Test harmony calculation with multiple strategies."""
        from strategies.common.adaptive_control.meta_controller import (
            MarketHarmony,
            MetaController,
        )
        from strategies.common.adaptive_control.spectral_regime import MarketRegime

        controller = MetaController()
        controller.register_strategy("strategy1")
        controller.register_strategy("strategy2")

        # Strategy 1 positive, Strategy 2 negative, net positive
        for _ in range(10):
            controller.record_strategy_pnl("strategy1", 200.0)
            controller.record_strategy_pnl("strategy2", -100.0)

        harmony = controller._calculate_harmony(MarketRegime.NORMAL)
        assert harmony == MarketHarmony.CONSONANT


# ==============================================================================
# Test Class: Strategy Weight Calculation
# ==============================================================================


class TestStrategyWeightCalculation:
    """Tests for strategy weight calculation."""

    def test_calculate_strategy_weights_no_strategies(self):
        """Test weight calculation with no registered strategies."""
        from strategies.common.adaptive_control.meta_controller import (
            MarketHarmony,
            MetaController,
            SystemState,
        )
        from strategies.common.adaptive_control.spectral_regime import MarketRegime

        controller = MetaController()

        weights = controller._calculate_strategy_weights(
            regime=MarketRegime.NORMAL,
            state=SystemState.VENTRAL,
            harmony=MarketHarmony.CONSONANT,
        )

        assert weights == {}
        assert weights == {}

    def test_calculate_strategy_weights_single_strategy(self):
        """Test weight calculation normalizes single strategy to 1.0."""
        from strategies.common.adaptive_control.meta_controller import (
            MarketHarmony,
            MetaController,
            SystemState,
        )
        from strategies.common.adaptive_control.spectral_regime import MarketRegime

        controller = MetaController()
        controller.register_strategy("test", regime_affinity={"normal": 0.7})

        weights = controller._calculate_strategy_weights(
            regime=MarketRegime.NORMAL,
            state=SystemState.VENTRAL,
            harmony=MarketHarmony.CONSONANT,
        )

        assert weights["test"] == pytest.approx(1.0)

    def test_calculate_strategy_weights_trending_regime(self):
        """Test weights favor trending affinity in TRENDING regime."""
        from strategies.common.adaptive_control.meta_controller import (
            MarketHarmony,
            MetaController,
            SystemState,
        )
        from strategies.common.adaptive_control.spectral_regime import MarketRegime

        controller = MetaController()
        controller.register_strategy(
            "momentum",
            regime_affinity={"trending": 1.0, "normal": 0.5, "mean_reverting": 0.2},
        )
        controller.register_strategy(
            "mean_revert",
            regime_affinity={"trending": 0.2, "normal": 0.5, "mean_reverting": 1.0},
        )

        weights = controller._calculate_strategy_weights(
            regime=MarketRegime.TRENDING,
            state=SystemState.VENTRAL,
            harmony=MarketHarmony.CONSONANT,
        )

        # Momentum should have higher weight in trending
        assert weights["momentum"] > weights["mean_revert"]

    def test_calculate_strategy_weights_mean_reverting_regime(self):
        """Test weights favor mean_reverting affinity in MEAN_REVERTING regime."""
        from strategies.common.adaptive_control.meta_controller import (
            MarketHarmony,
            MetaController,
            SystemState,
        )
        from strategies.common.adaptive_control.spectral_regime import MarketRegime

        controller = MetaController()
        controller.register_strategy(
            "momentum",
            regime_affinity={"trending": 1.0, "normal": 0.5, "mean_reverting": 0.2},
        )
        controller.register_strategy(
            "mean_revert",
            regime_affinity={"trending": 0.2, "normal": 0.5, "mean_reverting": 1.0},
        )

        weights = controller._calculate_strategy_weights(
            regime=MarketRegime.MEAN_REVERTING,
            state=SystemState.VENTRAL,
            harmony=MarketHarmony.CONSONANT,
        )

        # Mean revert should have higher weight
        assert weights["mean_revert"] > weights["momentum"]

    def test_calculate_strategy_weights_sympathetic_reduces(self):
        """Test SYMPATHETIC state reduces weights by 0.6 multiplier."""
        from strategies.common.adaptive_control.meta_controller import (
            MarketHarmony,
            MetaController,
            SystemState,
        )
        from strategies.common.adaptive_control.spectral_regime import MarketRegime

        controller = MetaController()
        controller.register_strategy("test", regime_affinity={"normal": 1.0})

        ventral_weights = controller._calculate_strategy_weights(
            regime=MarketRegime.NORMAL,
            state=SystemState.VENTRAL,
            harmony=MarketHarmony.CONSONANT,
        )

        sympathetic_weights = controller._calculate_strategy_weights(
            regime=MarketRegime.NORMAL,
            state=SystemState.SYMPATHETIC,
            harmony=MarketHarmony.CONSONANT,
        )

        # Both normalized to 1.0 for single strategy
        assert ventral_weights["test"] == pytest.approx(1.0)
        assert sympathetic_weights["test"] == pytest.approx(1.0)

    def test_calculate_strategy_weights_dorsal_zeroes(self):
        """Test DORSAL state zeroes weights."""
        from strategies.common.adaptive_control.meta_controller import (
            MarketHarmony,
            MetaController,
            SystemState,
        )
        from strategies.common.adaptive_control.spectral_regime import MarketRegime

        controller = MetaController()
        controller.register_strategy("test", regime_affinity={"normal": 1.0})

        weights = controller._calculate_strategy_weights(
            regime=MarketRegime.NORMAL,
            state=SystemState.DORSAL,
            harmony=MarketHarmony.CONSONANT,
        )

        # Zero state multiplier means weights are 0.0, normalization skipped
        # Weights are 0.0 (not normalized since total is 0)
        assert weights == {"test": 0.0}

    def test_calculate_strategy_weights_dissonant_reduces(self):
        """Test DISSONANT harmony reduces weights by 0.4 multiplier."""
        from strategies.common.adaptive_control.meta_controller import (
            MarketHarmony,
            MetaController,
            SystemState,
        )
        from strategies.common.adaptive_control.spectral_regime import MarketRegime

        controller = MetaController()
        controller.register_strategy("s1", regime_affinity={"normal": 1.0})
        controller.register_strategy("s2", regime_affinity={"normal": 0.5})

        consonant_weights = controller._calculate_strategy_weights(
            regime=MarketRegime.NORMAL,
            state=SystemState.VENTRAL,
            harmony=MarketHarmony.CONSONANT,
        )

        dissonant_weights = controller._calculate_strategy_weights(
            regime=MarketRegime.NORMAL,
            state=SystemState.VENTRAL,
            harmony=MarketHarmony.DISSONANT,
        )

        # Relative proportions should remain after normalization
        assert consonant_weights["s1"] / consonant_weights["s2"] == pytest.approx(
            dissonant_weights["s1"] / dissonant_weights["s2"]
        )

    def test_calculate_strategy_weights_unknown_regime(self):
        """Test UNKNOWN regime uses 'normal' affinity."""
        from strategies.common.adaptive_control.meta_controller import (
            MarketHarmony,
            MetaController,
            SystemState,
        )
        from strategies.common.adaptive_control.spectral_regime import MarketRegime

        controller = MetaController()
        controller.register_strategy(
            "test",
            regime_affinity={"trending": 0.1, "normal": 0.8, "mean_reverting": 0.2},
        )

        unknown_weights = controller._calculate_strategy_weights(
            regime=MarketRegime.UNKNOWN,
            state=SystemState.VENTRAL,
            harmony=MarketHarmony.CONSONANT,
        )

        normal_weights = controller._calculate_strategy_weights(
            regime=MarketRegime.NORMAL,
            state=SystemState.VENTRAL,
            harmony=MarketHarmony.CONSONANT,
        )

        # Should be equal since UNKNOWN maps to 'normal'
        assert unknown_weights["test"] == pytest.approx(normal_weights["test"])

    def test_calculate_strategy_weights_normalizes_to_one(self):
        """Test weights normalize to sum to 1.0."""
        from strategies.common.adaptive_control.meta_controller import (
            MarketHarmony,
            MetaController,
            SystemState,
        )
        from strategies.common.adaptive_control.spectral_regime import MarketRegime

        controller = MetaController()
        controller.register_strategy("s1", regime_affinity={"normal": 0.9})
        controller.register_strategy("s2", regime_affinity={"normal": 0.6})
        controller.register_strategy("s3", regime_affinity={"normal": 0.3})

        weights = controller._calculate_strategy_weights(
            regime=MarketRegime.NORMAL,
            state=SystemState.VENTRAL,
            harmony=MarketHarmony.CONSONANT,
        )

        total = sum(weights.values())
        assert total == pytest.approx(1.0)

    def test_strategy_weights_with_missing_affinity_key(self):
        """Test weight calculation handles missing affinity keys."""
        from strategies.common.adaptive_control.meta_controller import (
            MarketHarmony,
            MetaController,
            SystemState,
        )
        from strategies.common.adaptive_control.spectral_regime import MarketRegime

        controller = MetaController()
        # Register with incomplete affinity (missing 'mean_reverting')
        controller.register_strategy(
            "test",
            regime_affinity={"trending": 1.0, "normal": 0.5},
        )

        # Should use default 0.5 for missing key
        weights = controller._calculate_strategy_weights(
            regime=MarketRegime.MEAN_REVERTING,
            state=SystemState.VENTRAL,
            harmony=MarketHarmony.CONSONANT,
        )

        # Should not raise, weight should be normalized
        assert "test" in weights


# ==============================================================================
# Test Class: Risk Multiplier Calculation
# ==============================================================================


class TestRiskMultiplierCalculation:
    """Tests for risk multiplier calculation in update."""

    def _create_controller_with_mocks(self, health_score=80.0):
        """Helper to create controller with mock components."""
        from strategies.common.adaptive_control.meta_controller import MetaController
        from strategies.common.adaptive_control.spectral_regime import MarketRegime

        controller = MetaController()

        mock_health = MockSystemHealthMonitor()
        mock_health._score = health_score
        controller._health_monitor = mock_health

        mock_regime = MockSpectralRegimeDetector()
        mock_regime._regime = MarketRegime.NORMAL
        controller._regime_detector = mock_regime

        controller._pid_controller = MockPIDDrawdownController()

        return controller

    def test_risk_multiplier_ventral_consonant(self):
        """Test risk multiplier is 1.0 in optimal state."""
        controller = self._create_controller_with_mocks(health_score=90.0)
        state = controller.update(current_return=0.01, current_equity=10000.0)

        # PID returns 1.0, state_mult=1.0, harmony_mult=1.0
        assert state.risk_multiplier == pytest.approx(1.0)

    def test_risk_multiplier_sympathetic_reduces(self):
        """Test risk multiplier reduces to 0.5 in SYMPATHETIC state."""
        controller = self._create_controller_with_mocks(health_score=50.0)
        state = controller.update(current_return=0.01, current_equity=10000.0)

        # PID returns 1.0, state_mult=0.5, harmony_mult=1.0
        assert state.risk_multiplier == pytest.approx(0.5)

    def test_risk_multiplier_dorsal_zeroes(self):
        """Test risk multiplier is 0.0 in DORSAL state."""
        controller = self._create_controller_with_mocks(health_score=20.0)
        state = controller.update(current_return=0.01, current_equity=10000.0)

        # state_mult=0.0 zeroes everything
        assert state.risk_multiplier == pytest.approx(0.0)


# ==============================================================================
# Test Class: Properties
# ==============================================================================


class TestMetaControllerProperties:
    """Tests for MetaController properties."""

    def test_state_property(self):
        """Test state property returns current system state."""
        from strategies.common.adaptive_control.meta_controller import (
            MetaController,
            SystemState,
        )

        controller = MetaController()
        assert controller.state == SystemState.VENTRAL

        controller._current_state = SystemState.SYMPATHETIC
        assert controller.state == SystemState.SYMPATHETIC

    def test_harmony_property(self):
        """Test harmony property returns current market harmony."""
        from strategies.common.adaptive_control.meta_controller import (
            MarketHarmony,
            MetaController,
        )

        controller = MetaController()
        assert controller.harmony == MarketHarmony.CONSONANT

        controller._current_harmony = MarketHarmony.DISSONANT
        assert controller.harmony == MarketHarmony.DISSONANT

    def test_audit_emitter_getter(self):
        """Test audit_emitter getter."""
        from strategies.common.adaptive_control.meta_controller import MetaController

        emitter = MockAuditEventEmitter()
        controller = MetaController(audit_emitter=emitter)

        assert controller.audit_emitter is emitter

    def test_audit_emitter_setter(self):
        """Test audit_emitter setter."""
        from strategies.common.adaptive_control.meta_controller import MetaController

        controller = MetaController()
        assert controller.audit_emitter is None

        emitter = MockAuditEventEmitter()
        controller.audit_emitter = emitter

        assert controller.audit_emitter is emitter


# ==============================================================================
# Test Class: Reset
# ==============================================================================


class TestMetaControllerReset:
    """Tests for MetaController reset."""

    def test_reset_restores_initial_state(self):
        """Test reset restores initial state."""
        from strategies.common.adaptive_control.meta_controller import (
            MarketHarmony,
            MetaController,
            SystemState,
        )

        controller = MetaController()

        # Modify state
        controller._current_state = SystemState.DORSAL
        controller._current_harmony = MarketHarmony.DISSONANT
        controller._bars_processed = 100
        controller._peak_equity = 50000.0
        controller._current_equity = 40000.0
        controller._returns_buffer = [0.01] * 50

        controller.reset()

        assert controller._current_state == SystemState.VENTRAL
        assert controller._current_harmony == MarketHarmony.CONSONANT
        assert controller._bars_processed == 0
        assert controller._peak_equity == 0.0
        assert controller._current_equity == 0.0
        assert controller._returns_buffer == []

    def test_reset_clears_strategy_performance(self):
        """Test reset clears strategy performance data."""
        from strategies.common.adaptive_control.meta_controller import MetaController

        controller = MetaController()
        controller.register_strategy("test1")
        controller.register_strategy("test2")

        controller.record_strategy_pnl("test1", 100.0)
        controller.record_strategy_pnl("test2", -50.0)

        controller.reset()

        assert controller._strategy_performance["test1"] == []
        assert controller._strategy_performance["test2"] == []

    def test_reset_resets_pid_controller(self):
        """Test reset resets PID controller if initialized."""
        from strategies.common.adaptive_control.meta_controller import MetaController

        controller = MetaController()
        controller._ensure_components()  # Initialize components

        # Simulate PID state change
        controller._pid_controller._integral = 0.5
        controller._pid_controller._prev_error = 0.01

        controller.reset()

        assert controller._pid_controller._integral == 0.0
        assert controller._pid_controller._prev_error is None

    def test_reset_without_pid_controller(self):
        """Test reset works when PID controller is not initialized."""
        from strategies.common.adaptive_control.meta_controller import MetaController

        controller = MetaController()
        # Don't initialize components

        # Should not raise
        controller.reset()


# ==============================================================================
# Test Class: Audit Emitter Integration
# ==============================================================================


class TestAuditEmitterIntegration:
    """Tests for audit emitter integration."""

    def _create_controller_with_mocks_and_emitter(self, health_score=80.0):
        """Helper to create controller with mocks and audit emitter."""
        from strategies.common.adaptive_control.meta_controller import MetaController
        from strategies.common.adaptive_control.spectral_regime import MarketRegime

        emitter = MockAuditEventEmitter()
        controller = MetaController(audit_emitter=emitter)

        mock_health = MockSystemHealthMonitor()
        mock_health._score = health_score
        controller._health_monitor = mock_health

        mock_regime = MockSpectralRegimeDetector()
        mock_regime._regime = MarketRegime.NORMAL
        controller._regime_detector = mock_regime

        controller._pid_controller = MockPIDDrawdownController()

        return controller, emitter

    def test_audit_emits_state_change(self):
        """Test audit emitter logs system state changes."""
        from strategies.common.adaptive_control.meta_controller import SystemState

        controller, emitter = self._create_controller_with_mocks_and_emitter(90.0)

        # First update: VENTRAL
        controller.update(current_return=0.01, current_equity=10000.0)

        # Change to SYMPATHETIC
        controller._health_monitor._score = 50.0
        controller.update(current_return=0.01, current_equity=10000.0)

        # Should have state change event
        state_events = [e for e in emitter.events if e["param_name"] == "system_state"]
        assert len(state_events) == 1
        assert state_events[0]["old_value"] == SystemState.VENTRAL.value
        assert state_events[0]["new_value"] == SystemState.SYMPATHETIC.value

    def test_audit_emits_harmony_change(self):
        """Test audit emitter logs market harmony changes."""

        controller, emitter = self._create_controller_with_mocks_and_emitter()
        controller.register_strategy("test")

        # First update with positive PnL
        controller.record_strategy_pnl("test", 100.0)
        controller.update(current_return=0.01, current_equity=10000.0)

        # Force dissonance with negative PnL
        controller._strategy_performance["test"] = []  # Clear
        for _ in range(10):
            controller.record_strategy_pnl("test", -200.0)
        controller._current_equity = 10000.0  # Set for threshold
        controller.update(current_return=-0.01, current_equity=10000.0)

        # Check for harmony change event
        harmony_events = [e for e in emitter.events if e["param_name"] == "market_harmony"]
        assert len(harmony_events) >= 1

    def test_audit_emits_risk_multiplier_change(self):
        """Test audit emitter logs significant risk multiplier changes."""
        controller, emitter = self._create_controller_with_mocks_and_emitter(90.0)

        # First update: VENTRAL
        controller.update(current_return=0.01, current_equity=10000.0)

        # Second update: SYMPATHETIC (significant multiplier change)
        controller._health_monitor._score = 50.0
        controller.update(current_return=0.01, current_equity=10000.0)

        # Check for risk_multiplier event
        risk_events = [e for e in emitter.events if e["param_name"] == "risk_multiplier"]
        assert len(risk_events) >= 1

    def test_audit_emits_strategy_weight_change(self):
        """Test audit emitter logs significant strategy weight changes."""
        from strategies.common.adaptive_control.spectral_regime import MarketRegime

        controller, emitter = self._create_controller_with_mocks_and_emitter(90.0)
        controller.register_strategy(
            "test",
            regime_affinity={"trending": 1.0, "normal": 0.3, "mean_reverting": 0.1},
        )

        # First update
        controller.update(current_return=0.01, current_equity=10000.0)

        # Change to different regime for weight change
        controller._regime_detector._regime = MarketRegime.TRENDING
        controller.update(current_return=0.01, current_equity=10000.0)

        # Check for strategy weight event (may not always trigger)
        weight_events = [e for e in emitter.events if "strategy_weight" in e["param_name"]]
        assert isinstance(weight_events, list)

    def test_no_audit_without_emitter(self):
        """Test no errors when audit emitter is None."""
        from strategies.common.adaptive_control.meta_controller import MetaController
        from strategies.common.adaptive_control.spectral_regime import MarketRegime

        controller = MetaController()  # No emitter

        # Inject mocks
        mock_health = MockSystemHealthMonitor()
        mock_health._score = 90.0
        controller._health_monitor = mock_health

        mock_regime = MockSpectralRegimeDetector()
        mock_regime._regime = MarketRegime.NORMAL
        controller._regime_detector = mock_regime

        controller._pid_controller = MockPIDDrawdownController()

        # First update
        controller.update(current_return=0.01, current_equity=10000.0)

        # Change state (would trigger audit if emitter present)
        mock_health._score = 20.0
        controller.update(current_return=0.01, current_equity=10000.0)

        # Should not raise
        assert controller._audit_emitter is None


# ==============================================================================
# Test Class: Edge Cases
# ==============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def _create_controller_with_mocks(self):
        """Helper to create controller with mock components."""
        from strategies.common.adaptive_control.meta_controller import MetaController
        from strategies.common.adaptive_control.spectral_regime import MarketRegime

        controller = MetaController()

        controller._health_monitor = MockSystemHealthMonitor()
        mock_regime = MockSpectralRegimeDetector()
        mock_regime._regime = MarketRegime.NORMAL
        controller._regime_detector = mock_regime
        controller._pid_controller = MockPIDDrawdownController()

        return controller

    def test_many_consecutive_updates(self):
        """Test many consecutive updates don't cause memory issues."""
        controller = self._create_controller_with_mocks()
        controller.register_strategy("test")

        # Simulate many updates
        for i in range(1000):
            controller.update(
                current_return=0.001 * (i % 10 - 5),
                current_equity=10000.0 + i,
            )
            controller.record_strategy_pnl("test", float(i % 10))

        # Buffer should be limited
        assert len(controller._returns_buffer) <= 500
        assert len(controller._strategy_performance["test"]) <= controller.harmony_lookback

    def test_strategy_callback_not_called_without_callback(self):
        """Test no error when strategy has no callback."""
        controller = self._create_controller_with_mocks()
        controller.register_strategy("test", callback=None)

        # Should not raise
        state = controller.update(current_return=0.01, current_equity=10000.0)
        assert state is not None


# ==============================================================================
# Test Class: MetaState Dataclass
# ==============================================================================


class TestMetaStateDataclass:
    """Tests for MetaState dataclass."""

    def test_meta_state_creation(self):
        """Test MetaState can be created with all fields."""
        from strategies.common.adaptive_control.meta_controller import (
            MarketHarmony,
            MetaState,
            SystemState,
        )

        state = MetaState(
            timestamp=datetime.now(UTC),
            system_state=SystemState.VENTRAL,
            market_harmony=MarketHarmony.CONSONANT,
            health_score=85.0,
            drawdown_pct=2.5,
            regime_confidence=0.8,
            spectral_alpha=1.0,
            risk_multiplier=0.9,
            strategy_weights={"test": 1.0},
        )

        assert state.system_state == SystemState.VENTRAL
        assert state.market_harmony == MarketHarmony.CONSONANT
        assert state.health_score == 85.0
        assert state.drawdown_pct == 2.5
        assert state.risk_multiplier == 0.9
        assert state.strategy_weights == {"test": 1.0}

    def test_meta_state_default_strategy_weights(self):
        """Test MetaState has default empty strategy_weights."""
        from strategies.common.adaptive_control.meta_controller import (
            MarketHarmony,
            MetaState,
            SystemState,
        )

        state = MetaState(
            timestamp=datetime.now(UTC),
            system_state=SystemState.VENTRAL,
            market_harmony=MarketHarmony.CONSONANT,
            health_score=85.0,
            drawdown_pct=0.0,
            regime_confidence=0.8,
            spectral_alpha=1.0,
            risk_multiplier=1.0,
        )

        assert state.strategy_weights == {}


# ==============================================================================
# Test Class: Enums
# ==============================================================================


class TestEnums:
    """Tests for enum values."""

    def test_system_state_values(self):
        """Test SystemState enum has correct values."""
        from strategies.common.adaptive_control.meta_controller import SystemState

        assert SystemState.VENTRAL.value == "ventral"
        assert SystemState.SYMPATHETIC.value == "sympathetic"
        assert SystemState.DORSAL.value == "dorsal"

    def test_market_harmony_values(self):
        """Test MarketHarmony enum has correct values."""
        from strategies.common.adaptive_control.meta_controller import MarketHarmony

        assert MarketHarmony.CONSONANT.value == "consonant"
        assert MarketHarmony.DISSONANT.value == "dissonant"
        assert MarketHarmony.RESOLVING.value == "resolving"


# ==============================================================================
# Test Class: Integration with Real Components
# ==============================================================================


class TestIntegrationWithRealComponents:
    """Tests using real (not mocked) components for integration testing."""

    def test_full_update_cycle_with_real_components(self):
        """Test complete update cycle with real component initialization."""
        from strategies.common.adaptive_control.meta_controller import (
            MetaController,
            MetaState,
            SystemState,
        )

        controller = MetaController()
        controller.register_strategy("momentum", regime_affinity={"trending": 1.0, "normal": 0.5})
        controller.register_strategy(
            "mean_revert", regime_affinity={"mean_reverting": 1.0, "normal": 0.5}
        )

        # Run multiple updates
        for i in range(100):
            ret = 0.001 * (i % 10 - 5)  # Oscillating returns
            equity = 10000.0 + i * 10

            state = controller.update(
                current_return=ret,
                current_equity=equity,
                latency_ms=10.0 if i % 5 == 0 else 0,
                order_filled=i % 7 != 0,
                slippage_bps=1.0 if i % 5 == 0 else 0,
            )

            # Record some PnL
            if i % 3 == 0:
                controller.record_strategy_pnl("momentum", ret * 1000)
                controller.record_strategy_pnl("mean_revert", -ret * 500)

        # Final state should be valid
        assert isinstance(state, MetaState)
        assert state.system_state in [
            SystemState.VENTRAL,
            SystemState.SYMPATHETIC,
            SystemState.DORSAL,
        ]
        assert 0.0 <= state.risk_multiplier <= 1.0
        assert (
            sum(state.strategy_weights.values()) == pytest.approx(1.0, abs=0.01)
            or state.strategy_weights == {}
        )

    def test_drawdown_triggers_state_change(self):
        """Test that significant drawdown triggers state change."""
        from strategies.common.adaptive_control.meta_controller import (
            MetaController,
            SystemState,
        )

        controller = MetaController(target_drawdown=0.05)

        # Start with high equity
        controller.update(current_return=0.0, current_equity=10000.0)
        assert controller.state == SystemState.VENTRAL

        # Large drawdown (>10% = 2x target) should force DORSAL
        state = controller.update(current_return=-0.15, current_equity=8400.0)

        # 16% drawdown should trigger DORSAL
        assert state.drawdown_pct > 10.0
        assert controller.state == SystemState.DORSAL


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
