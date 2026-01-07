"""
Comprehensive tests for AlphaEvolveBridge module.

Target: 90%+ coverage for alpha_evolve_bridge.py
Missing lines: 119-129, 141, 162-227, 236-261, 265-280, 285-292, 297, 301, 317-328, 332-334, 338, 343, 348, 387-393, 397, 404, 408, 416, 440-459, 470
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from unittest.mock import MagicMock, Mock, patch

import pytest

# ============================================================================
# Mock classes to avoid importing real dependencies
# ============================================================================


class MockSystemState(Enum):
    """Mock SystemState enum."""

    VENTRAL = "ventral"
    SYMPATHETIC = "sympathetic"
    DORSAL = "dorsal"


class MockMarketHarmony(Enum):
    """Mock MarketHarmony enum."""

    CONSONANT = "consonant"
    DISSONANT = "dissonant"
    RESOLVING = "resolving"


@dataclass
class MockMetaState:
    """Mock MetaState dataclass."""

    timestamp: datetime = field(default_factory=datetime.utcnow)
    system_state: MockSystemState = MockSystemState.VENTRAL
    market_harmony: MockMarketHarmony = MockMarketHarmony.CONSONANT
    health_score: float = 80.0
    drawdown_pct: float = 2.0
    regime_confidence: float = 0.8
    spectral_alpha: float = 1.5
    risk_multiplier: float = 1.0
    strategy_weights: dict[str, float] = field(default_factory=dict)


class MockMetaController:
    """Mock MetaController for testing."""

    def __init__(self, **kwargs):
        self._strategy_performances: dict[str, list[float]] = {}
        self._current_state = MockSystemState.VENTRAL
        self._current_harmony = MockMarketHarmony.CONSONANT

    def register_strategy(self, name: str, regime_affinity=None, callback=None):
        self._strategy_performances[name] = []

    def record_strategy_pnl(self, name: str, pnl: float):
        if name in self._strategy_performances:
            self._strategy_performances[name].append(pnl)

    def update(
        self,
        current_price=None,
        current_drawdown=None,
        current_regime=None,
        current_return=None,
        current_equity=None,
        **kwargs,
    ):
        return MockMetaState(
            strategy_weights={"strategy_1": 0.5, "strategy_2": 0.3, "strategy_3": 0.2},
            risk_multiplier=1.0,
        )


# ============================================================================
# Setup mocked meta_controller module before importing the module under test
# ============================================================================

# Save original module references for cleanup
_original_meta_module = sys.modules.get("strategies.common.adaptive_control.meta_controller")
_original_alpha_bridge = sys.modules.get("strategies.common.adaptive_control.alpha_evolve_bridge")

# Create mock module
_mock_meta_module = MagicMock()
_mock_meta_module.MetaController = MockMetaController
_mock_meta_module.MetaState = MockMetaState
_mock_meta_module.SystemState = MockSystemState
_mock_meta_module.MarketHarmony = MockMarketHarmony

# Patch before any imports
sys.modules["strategies.common.adaptive_control.meta_controller"] = _mock_meta_module

# Force reimport of alpha_evolve_bridge to ensure it uses our mock
if _original_alpha_bridge is not None:
    # Module was already imported, need to reload with our mock
    sys.modules.pop("strategies.common.adaptive_control.alpha_evolve_bridge", None)

# Now import the module under test (it will use our mock)
from strategies.common.adaptive_control.alpha_evolve_bridge import (
    AdaptiveSurvivalSystem,
    AlphaEvolveBridge,
    EvolutionConfig,
    EvolutionRequest,
    EvolutionTrigger,
)


@pytest.fixture(scope="module", autouse=True)
def _cleanup_sys_modules():
    """Restore original meta_controller module after all tests in this file."""
    yield
    # Cleanup: restore original modules
    if _original_meta_module is not None:
        sys.modules["strategies.common.adaptive_control.meta_controller"] = _original_meta_module
    else:
        sys.modules.pop("strategies.common.adaptive_control.meta_controller", None)

    # Also restore alpha_evolve_bridge to avoid affecting other tests
    if _original_alpha_bridge is not None:
        sys.modules["strategies.common.adaptive_control.alpha_evolve_bridge"] = (
            _original_alpha_bridge
        )
    else:
        sys.modules.pop("strategies.common.adaptive_control.alpha_evolve_bridge", None)


# ============================================================================
# Tests for EvolutionTrigger enum
# ============================================================================


class TestEvolutionTrigger:
    """Tests for EvolutionTrigger enum."""

    def test_all_trigger_values(self):
        """Test all trigger values exist."""
        assert EvolutionTrigger.DISSONANCE.value == "market_system_dissonance"
        assert EvolutionTrigger.DRAWDOWN.value == "excessive_drawdown"
        assert EvolutionTrigger.STAGNATION.value == "performance_stagnation"
        assert EvolutionTrigger.REGIME_SHIFT.value == "major_regime_shift"
        assert EvolutionTrigger.SCHEDULED.value == "scheduled_evolution"


# ============================================================================
# Tests for EvolutionConfig dataclass
# ============================================================================


class TestEvolutionConfig:
    """Tests for EvolutionConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = EvolutionConfig()
        assert config.dissonance_threshold == 0.3
        assert config.drawdown_threshold == 0.15
        assert config.stagnation_periods == 50
        assert config.min_bars_between_evolution == 100
        assert config.max_concurrent_evolutions == 2
        assert config.min_strategies_to_evolve == 1
        assert config.max_strategies_to_evolve == 3

    def test_custom_values(self):
        """Test custom configuration values."""
        config = EvolutionConfig(
            dissonance_threshold=0.5,
            drawdown_threshold=0.20,
            stagnation_periods=30,
            min_bars_between_evolution=50,
            max_concurrent_evolutions=5,
            min_strategies_to_evolve=2,
            max_strategies_to_evolve=5,
        )
        assert config.dissonance_threshold == 0.5
        assert config.drawdown_threshold == 0.20
        assert config.stagnation_periods == 30
        assert config.min_bars_between_evolution == 50


# ============================================================================
# Tests for EvolutionRequest dataclass
# ============================================================================


class TestEvolutionRequest:
    """Tests for EvolutionRequest dataclass."""

    def test_creation(self):
        """Test creating an EvolutionRequest."""
        now = datetime.now(UTC)
        state = MockMetaState()

        request = EvolutionRequest(
            trigger=EvolutionTrigger.DISSONANCE,
            timestamp=now,
            current_state=state,
            underperforming_strategies=["strat1", "strat2"],
            market_conditions={"risk": 0.5, "volatility": 0.2},
            priority=3,
        )

        assert request.trigger == EvolutionTrigger.DISSONANCE
        assert request.timestamp == now
        assert request.current_state == state
        assert request.underperforming_strategies == ["strat1", "strat2"]
        assert request.market_conditions == {"risk": 0.5, "volatility": 0.2}
        assert request.priority == 3


# ============================================================================
# Tests for AlphaEvolveBridge class
# ============================================================================


class TestAlphaEvolveBridgeInit:
    """Tests for AlphaEvolveBridge initialization (lines 119-129)."""

    def test_init_with_defaults(self):
        """Test initialization with default config."""
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta)

        assert bridge.meta is meta
        assert bridge.config is not None
        assert bridge._audit_emitter is None
        assert bridge._callbacks == []
        assert bridge._last_evolution_bar == 0
        assert bridge._bars_since_improvement == 0
        assert bridge._best_sharpe == float("-inf")
        assert bridge._pending_requests == []

    def test_init_with_custom_config(self):
        """Test initialization with custom config."""
        meta = MockMetaController()
        config = EvolutionConfig(dissonance_threshold=0.5)
        bridge = AlphaEvolveBridge(meta, config=config)

        assert bridge.config.dissonance_threshold == 0.5

    def test_init_with_audit_emitter(self):
        """Test initialization with audit emitter."""
        meta = MockMetaController()
        audit_emitter = Mock()
        bridge = AlphaEvolveBridge(meta, audit_emitter=audit_emitter)

        assert bridge._audit_emitter is audit_emitter


class TestAlphaEvolveBridgeOnEvolutionRequest:
    """Tests for on_evolution_request method (line 141)."""

    def test_register_callback(self):
        """Test registering a callback."""
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta)

        callback = Mock()
        bridge.on_evolution_request(callback)

        assert callback in bridge._callbacks

    def test_register_multiple_callbacks(self):
        """Test registering multiple callbacks."""
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta)

        callback1 = Mock()
        callback2 = Mock()
        bridge.on_evolution_request(callback1)
        bridge.on_evolution_request(callback2)

        assert len(bridge._callbacks) == 2
        assert callback1 in bridge._callbacks
        assert callback2 in bridge._callbacks


class TestAlphaEvolveBridgeCheckAndTrigger:
    """Tests for check_and_trigger method (lines 162-227)."""

    def test_cooldown_prevents_trigger(self):
        """Test cooldown period prevents evolution."""
        config = EvolutionConfig(min_bars_between_evolution=100)
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta, config=config)
        bridge._last_evolution_bar = 50

        state = MockMetaState()
        result = bridge.check_and_trigger(state, current_bar=100)

        # 100 - 50 = 50, which is < 100, so should return None
        assert result is None

    def test_max_concurrent_evolutions(self):
        """Test max concurrent evolutions limit."""
        config = EvolutionConfig(max_concurrent_evolutions=2)
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta, config=config)

        # Add pending requests to hit the limit
        mock_request = EvolutionRequest(
            trigger=EvolutionTrigger.DISSONANCE,
            timestamp=datetime.now(UTC),
            current_state=MockMetaState(),
            underperforming_strategies=["s1"],
            market_conditions={},
            priority=3,
        )
        bridge._pending_requests = [mock_request, mock_request]

        state = MockMetaState()
        result = bridge.check_and_trigger(state, current_bar=200)

        assert result is None

    def test_no_trigger_without_conditions(self):
        """Test no evolution triggered when conditions not met."""
        config = EvolutionConfig()
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta, config=config)

        # CONSONANT state = no trigger
        state = MockMetaState(
            market_harmony=MockMarketHarmony.CONSONANT,
            risk_multiplier=1.0,
        )

        result = bridge.check_and_trigger(state, current_bar=200)

        assert result is None

    def test_trigger_on_dissonance(self):
        """Test evolution triggered on dissonance."""
        config = EvolutionConfig(
            min_bars_between_evolution=10,
            dissonance_threshold=0.5,
            min_strategies_to_evolve=1,
        )
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta, config=config)

        # Create DISSONANT state with low risk multiplier
        state = MockMetaState(
            market_harmony=MockMarketHarmony.DISSONANT,
            risk_multiplier=0.3,  # Low risk multiplier gives harmony score < 0.3
            strategy_weights={"strat1": 0.3, "strat2": 0.7},
        )

        result = bridge.check_and_trigger(state, current_bar=200)

        assert result is not None
        assert result.trigger == EvolutionTrigger.DISSONANCE
        assert "strat1" in result.underperforming_strategies

    def test_trigger_on_drawdown(self):
        """Test evolution triggered on excessive drawdown."""
        config = EvolutionConfig(
            min_bars_between_evolution=10,
            drawdown_threshold=0.15,
            min_strategies_to_evolve=1,
        )
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta, config=config)

        # Create state with drawdown (risk_multiplier < 1 - drawdown_threshold)
        state = MockMetaState(
            market_harmony=MockMarketHarmony.CONSONANT,
            risk_multiplier=0.80,  # < 1 - 0.15 = 0.85
            strategy_weights={"strat1": 0.3, "strat2": 0.7},
        )

        result = bridge.check_and_trigger(state, current_bar=200)

        assert result is not None
        assert result.trigger == EvolutionTrigger.DRAWDOWN

    def test_trigger_on_stagnation(self):
        """Test evolution triggered on performance stagnation."""
        config = EvolutionConfig(
            min_bars_between_evolution=1,
            stagnation_periods=5,
            min_strategies_to_evolve=1,
        )
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta, config=config)
        bridge._best_sharpe = 1.0  # Set a higher best sharpe
        bridge._bars_since_improvement = 4  # Almost at threshold

        # Create normal state that doesn't trigger other conditions
        state = MockMetaState(
            market_harmony=MockMarketHarmony.CONSONANT,
            risk_multiplier=0.9,  # Enough to not trigger drawdown
            strategy_weights={"strat1": 0.3, "strat2": 0.7},
        )

        result = bridge.check_and_trigger(state, current_bar=200)

        assert result is not None
        assert result.trigger == EvolutionTrigger.STAGNATION

    def test_not_enough_underperformers(self):
        """Test no trigger when not enough underperforming strategies."""
        config = EvolutionConfig(
            min_bars_between_evolution=1,
            min_strategies_to_evolve=5,  # Require more than we have
        )
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta, config=config)

        state = MockMetaState(
            market_harmony=MockMarketHarmony.DISSONANT,
            risk_multiplier=0.2,
            strategy_weights={"strat1": 0.5, "strat2": 0.5},  # Only 2 strategies
        )

        result = bridge.check_and_trigger(state, current_bar=200)

        assert result is None

    def test_callback_error_handling(self):
        """Test error handling in callbacks (lines 217-220)."""
        config = EvolutionConfig(
            min_bars_between_evolution=1,
            min_strategies_to_evolve=1,
        )
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta, config=config)

        # Register a callback that raises an exception
        failing_callback = Mock(side_effect=Exception("Callback error"))
        success_callback = Mock()
        bridge.on_evolution_request(failing_callback)
        bridge.on_evolution_request(success_callback)

        state = MockMetaState(
            market_harmony=MockMarketHarmony.DISSONANT,
            risk_multiplier=0.2,
            strategy_weights={"strat1": 0.3, "strat2": 0.7},
        )

        # Should not raise, should continue to next callback
        result = bridge.check_and_trigger(state, current_bar=200)

        assert result is not None
        failing_callback.assert_called_once()
        success_callback.assert_called_once()

    def test_audit_emitter_called(self):
        """Test audit emitter is called when evolution triggers."""
        config = EvolutionConfig(
            min_bars_between_evolution=1,
            min_strategies_to_evolve=1,
        )
        meta = MockMetaController()
        audit_emitter = Mock()
        bridge = AlphaEvolveBridge(meta, config=config, audit_emitter=audit_emitter)

        state = MockMetaState(
            market_harmony=MockMarketHarmony.DISSONANT,
            risk_multiplier=0.2,
            strategy_weights={"strat1": 0.3, "strat2": 0.7},
        )

        # Mock the audit events module
        mock_audit_events = MagicMock()
        mock_audit_events.AuditEventType.SYS_EVOLUTION_TRIGGER = "SYS_EVOLUTION_TRIGGER"

        with patch.dict(sys.modules, {"strategies.common.audit.events": mock_audit_events}):
            result = bridge.check_and_trigger(state, current_bar=200)

        assert result is not None
        audit_emitter.emit_system.assert_called_once()


class TestAlphaEvolveBridgeEvaluateTriggers:
    """Tests for _evaluate_triggers method (lines 236-261)."""

    def test_dissonance_severe_enough(self):
        """Test dissonance trigger when severe enough."""
        config = EvolutionConfig(dissonance_threshold=0.3)
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta, config=config)

        state = MockMetaState(
            market_harmony=MockMarketHarmony.DISSONANT,
            risk_multiplier=0.3,  # harmony_score = 0.3 * 0.5 = 0.15 < 0.3
        )

        result = bridge._evaluate_triggers(state, 100)

        assert result == EvolutionTrigger.DISSONANCE

    def test_dissonance_not_severe_enough(self):
        """Test dissonance not triggered when not severe."""
        config = EvolutionConfig(dissonance_threshold=0.3)
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta, config=config)

        state = MockMetaState(
            market_harmony=MockMarketHarmony.DISSONANT,
            risk_multiplier=0.8,  # harmony_score = 0.8 * 0.5 = 0.4 > 0.3
        )

        result = bridge._evaluate_triggers(state, 100)

        # Should continue to check other conditions
        assert result is None or result != EvolutionTrigger.DISSONANCE

    def test_drawdown_trigger(self):
        """Test drawdown trigger."""
        config = EvolutionConfig(drawdown_threshold=0.15)
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta, config=config)

        state = MockMetaState(
            market_harmony=MockMarketHarmony.CONSONANT,
            risk_multiplier=0.80,  # < 1 - 0.15 = 0.85
        )

        result = bridge._evaluate_triggers(state, 100)

        assert result == EvolutionTrigger.DRAWDOWN

    def test_stagnation_increments_counter(self):
        """Test stagnation counter increments."""
        config = EvolutionConfig(stagnation_periods=10)
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta, config=config)
        bridge._best_sharpe = 1.0
        bridge._bars_since_improvement = 0

        state = MockMetaState(
            market_harmony=MockMarketHarmony.CONSONANT,
            risk_multiplier=0.9,  # This becomes sharpe = 0.9 < 1.0
        )

        bridge._evaluate_triggers(state, 100)

        assert bridge._bars_since_improvement == 1

    def test_stagnation_resets_on_improvement(self):
        """Test stagnation counter resets on improvement."""
        config = EvolutionConfig(stagnation_periods=10)
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta, config=config)
        bridge._best_sharpe = 0.5
        bridge._bars_since_improvement = 5

        state = MockMetaState(
            market_harmony=MockMarketHarmony.CONSONANT,
            risk_multiplier=1.0,  # sharpe = 1.0 > 0.5
        )

        bridge._evaluate_triggers(state, 100)

        assert bridge._best_sharpe == 1.0
        assert bridge._bars_since_improvement == 0

    def test_stagnation_triggers_at_threshold(self):
        """Test stagnation triggers at threshold."""
        config = EvolutionConfig(stagnation_periods=5)
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta, config=config)
        bridge._best_sharpe = 1.0
        bridge._bars_since_improvement = 4  # Will become 5

        state = MockMetaState(
            market_harmony=MockMarketHarmony.CONSONANT,
            risk_multiplier=0.9,  # < best_sharpe
        )

        result = bridge._evaluate_triggers(state, 100)

        assert result == EvolutionTrigger.STAGNATION
        assert bridge._bars_since_improvement == 0  # Reset after trigger


class TestAlphaEvolveBridgeFindUnderperformers:
    """Tests for _find_underperformers method (lines 265-280)."""

    def test_empty_strategy_weights(self):
        """Test empty strategy weights returns empty list."""
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta)

        state = MockMetaState(strategy_weights={})

        result = bridge._find_underperformers(state)

        assert result == []

    def test_finds_bottom_performers(self):
        """Test finds bottom 25% performers."""
        config = EvolutionConfig(min_strategies_to_evolve=1)
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta, config=config)

        state = MockMetaState(strategy_weights={"s1": 0.1, "s2": 0.2, "s3": 0.3, "s4": 0.4})

        result = bridge._find_underperformers(state)

        # Bottom 25% of 4 = 1, but min is also 1
        assert "s1" in result

    def test_min_strategies_to_evolve(self):
        """Test respects min_strategies_to_evolve."""
        config = EvolutionConfig(min_strategies_to_evolve=2)
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta, config=config)

        state = MockMetaState(strategy_weights={"s1": 0.1, "s2": 0.2, "s3": 0.3, "s4": 0.4})

        result = bridge._find_underperformers(state)

        assert len(result) >= 2
        assert "s1" in result
        assert "s2" in result


class TestAlphaEvolveBridgeEstimateHarmonyScore:
    """Tests for _estimate_harmony_score method (lines 285-292)."""

    def test_consonant_harmony(self):
        """Test harmony score for CONSONANT state."""
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta)

        state = MockMetaState(
            market_harmony=MockMarketHarmony.CONSONANT,
            risk_multiplier=0.9,
        )

        result = bridge._estimate_harmony_score(state)

        # CONSONANT: min(1.0, 0.9 * 1.2) = min(1.0, 1.08) = 1.0
        assert result == 1.0

    def test_resolving_harmony(self):
        """Test harmony score for RESOLVING state."""
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta)

        state = MockMetaState(
            market_harmony=MockMarketHarmony.RESOLVING,
            risk_multiplier=0.9,
        )

        result = bridge._estimate_harmony_score(state)

        # RESOLVING: 0.9 * 0.8 = 0.72
        assert result == pytest.approx(0.72)

    def test_dissonant_harmony(self):
        """Test harmony score for DISSONANT state."""
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta)

        state = MockMetaState(
            market_harmony=MockMarketHarmony.DISSONANT,
            risk_multiplier=0.8,
        )

        result = bridge._estimate_harmony_score(state)

        # DISSONANT: 0.8 * 0.5 = 0.4
        assert result == pytest.approx(0.4)


class TestAlphaEvolveBridgeEstimateSharpe:
    """Tests for _estimate_sharpe method (line 297)."""

    def test_uses_risk_multiplier_as_proxy(self):
        """Test sharpe estimation uses risk multiplier."""
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta)

        state = MockMetaState(risk_multiplier=0.75)

        result = bridge._estimate_sharpe(state)

        assert result == 0.75


class TestAlphaEvolveBridgeExtractMarketConditions:
    """Tests for _extract_market_conditions method (line 301)."""

    def test_extract_consonant_conditions(self):
        """Test market conditions extraction for CONSONANT."""
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta)

        state = MockMetaState(
            market_harmony=MockMarketHarmony.CONSONANT,
            risk_multiplier=0.9,
            strategy_weights={"s1": 0.5, "s2": 0.5},
        )

        result = bridge._extract_market_conditions(state)

        assert result["risk_multiplier"] == 0.9
        assert result["harmony"] == 1.0
        assert result["n_active_strategies"] == 2

    def test_extract_resolving_conditions(self):
        """Test market conditions extraction for RESOLVING."""
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta)

        state = MockMetaState(
            market_harmony=MockMarketHarmony.RESOLVING,
            risk_multiplier=0.7,
            strategy_weights={"s1": 0.5, "s2": 0.3, "s3": 0.2},
        )

        result = bridge._extract_market_conditions(state)

        assert result["harmony"] == 0.5
        assert result["n_active_strategies"] == 3

    def test_extract_dissonant_conditions(self):
        """Test market conditions extraction for DISSONANT."""
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta)

        state = MockMetaState(
            market_harmony=MockMarketHarmony.DISSONANT,
            risk_multiplier=0.5,
            strategy_weights={},
        )

        result = bridge._extract_market_conditions(state)

        assert result["harmony"] == 0.0
        assert result["n_active_strategies"] == 0


class TestAlphaEvolveBridgeCalculatePriority:
    """Tests for _calculate_priority method (lines 317-328)."""

    def test_drawdown_priority(self):
        """Test DRAWDOWN gives highest priority."""
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta)

        state = MockMetaState()

        result = bridge._calculate_priority(EvolutionTrigger.DRAWDOWN, state)

        assert result == 5

    def test_dissonance_severe_priority(self):
        """Test severe DISSONANCE gives priority 4."""
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta)

        state = MockMetaState(risk_multiplier=0.4)

        result = bridge._calculate_priority(EvolutionTrigger.DISSONANCE, state)

        assert result == 4

    def test_dissonance_moderate_priority(self):
        """Test moderate DISSONANCE gives priority 3."""
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta)

        state = MockMetaState(risk_multiplier=0.6)

        result = bridge._calculate_priority(EvolutionTrigger.DISSONANCE, state)

        assert result == 3

    def test_regime_shift_priority(self):
        """Test REGIME_SHIFT gives priority 3."""
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta)

        state = MockMetaState()

        result = bridge._calculate_priority(EvolutionTrigger.REGIME_SHIFT, state)

        assert result == 3

    def test_stagnation_priority(self):
        """Test STAGNATION gives priority 2."""
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta)

        state = MockMetaState()

        result = bridge._calculate_priority(EvolutionTrigger.STAGNATION, state)

        assert result == 2

    def test_scheduled_priority(self):
        """Test SCHEDULED gives priority 1."""
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta)

        state = MockMetaState()

        result = bridge._calculate_priority(EvolutionTrigger.SCHEDULED, state)

        assert result == 1


class TestAlphaEvolveBridgeMarkEvolutionComplete:
    """Tests for mark_evolution_complete method (lines 332-334)."""

    def test_removes_completed_request(self):
        """Test removes request from pending list."""
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta)

        request = EvolutionRequest(
            trigger=EvolutionTrigger.DISSONANCE,
            timestamp=datetime.now(UTC),
            current_state=MockMetaState(),
            underperforming_strategies=["s1"],
            market_conditions={},
            priority=3,
        )
        bridge._pending_requests.append(request)

        bridge.mark_evolution_complete(request)

        assert request not in bridge._pending_requests

    def test_does_not_fail_on_missing_request(self):
        """Test doesn't fail when request not in list."""
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta)

        request = EvolutionRequest(
            trigger=EvolutionTrigger.DISSONANCE,
            timestamp=datetime.now(UTC),
            current_state=MockMetaState(),
            underperforming_strategies=["s1"],
            market_conditions={},
            priority=3,
        )

        # Should not raise
        bridge.mark_evolution_complete(request)


class TestAlphaEvolveBridgeGetPendingEvolutions:
    """Tests for get_pending_evolutions method (line 338)."""

    def test_returns_copy(self):
        """Test returns a copy of pending requests."""
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta)

        request = EvolutionRequest(
            trigger=EvolutionTrigger.DISSONANCE,
            timestamp=datetime.now(UTC),
            current_state=MockMetaState(),
            underperforming_strategies=["s1"],
            market_conditions={},
            priority=3,
        )
        bridge._pending_requests.append(request)

        result = bridge.get_pending_evolutions()

        assert result is not bridge._pending_requests
        assert result == bridge._pending_requests

    def test_empty_list(self):
        """Test returns empty list when no pending."""
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta)

        result = bridge.get_pending_evolutions()

        assert result == []


class TestAlphaEvolveBridgeAuditEmitterProperty:
    """Tests for audit_emitter property (lines 343, 348)."""

    def test_getter(self):
        """Test audit_emitter getter."""
        meta = MockMetaController()
        emitter = Mock()
        bridge = AlphaEvolveBridge(meta, audit_emitter=emitter)

        assert bridge.audit_emitter is emitter

    def test_setter(self):
        """Test audit_emitter setter."""
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta)

        emitter = Mock()
        bridge.audit_emitter = emitter

        assert bridge._audit_emitter is emitter


# ============================================================================
# Tests for AdaptiveSurvivalSystem class
# ============================================================================


class TestAdaptiveSurvivalSystemInit:
    """Tests for AdaptiveSurvivalSystem initialization (lines 387-393)."""

    def test_init_defaults(self):
        """Test default initialization."""
        system = AdaptiveSurvivalSystem()

        assert system._bar_count == 0
        assert system._risk_callbacks == []

    def test_init_with_configs(self):
        """Test initialization with custom configs."""
        meta_config = {"target_drawdown": 0.10}
        evolution_config = EvolutionConfig(dissonance_threshold=0.5)

        system = AdaptiveSurvivalSystem(
            meta_config=meta_config,
            evolution_config=evolution_config,
        )

        assert system.bridge.config.dissonance_threshold == 0.5


class TestAdaptiveSurvivalSystemRegisterStrategy:
    """Tests for register_strategy method (line 397)."""

    def test_registers_strategy(self):
        """Test strategy registration."""
        system = AdaptiveSurvivalSystem()
        system.register_strategy("test_strategy")

        assert "test_strategy" in system.meta._strategy_performances


class TestAdaptiveSurvivalSystemOnEvolutionNeeded:
    """Tests for on_evolution_needed method (line 404)."""

    def test_registers_callback(self):
        """Test callback registration."""
        system = AdaptiveSurvivalSystem()
        callback = Mock()
        system.on_evolution_needed(callback)

        assert callback in system.bridge._callbacks


class TestAdaptiveSurvivalSystemOnRiskChange:
    """Tests for on_risk_change method (line 408)."""

    def test_registers_risk_callback(self):
        """Test risk callback registration."""
        system = AdaptiveSurvivalSystem()
        callback = Mock()
        system.on_risk_change(callback)

        assert callback in system._risk_callbacks


class TestAdaptiveSurvivalSystemUpdateStrategyPerformance:
    """Tests for update_strategy_performance method (line 416)."""

    def test_updates_performance(self):
        """Test performance update."""
        system = AdaptiveSurvivalSystem()
        system.register_strategy("test_strategy")
        system.update_strategy_performance("test_strategy", 100.0)

        assert 100.0 in system.meta._strategy_performances["test_strategy"]


class TestAdaptiveSurvivalSystemProcess:
    """Tests for process method (lines 440-459)."""

    def test_increments_bar_count(self):
        """Test bar count increments."""
        system = AdaptiveSurvivalSystem()
        system.register_strategy("test")

        system.process(price=100.0, current_drawdown=0.02)

        assert system._bar_count == 1

    def test_returns_expected_structure(self):
        """Test return value structure."""
        system = AdaptiveSurvivalSystem()
        system.register_strategy("test")

        result = system.process(price=100.0, current_drawdown=0.02)

        assert "risk_multiplier" in result
        assert "strategy_weights" in result
        assert "evolution_triggered" in result
        assert "evolution_request" in result
        assert "system_state" in result
        assert "market_harmony" in result

    def test_calls_risk_callbacks(self):
        """Test risk callbacks are called."""
        system = AdaptiveSurvivalSystem()
        callback = Mock()
        system.on_risk_change(callback)
        system.register_strategy("test")

        system.process(price=100.0, current_drawdown=0.02)

        callback.assert_called_once()

    def test_risk_callback_error_handling(self):
        """Test risk callback error handling (lines 456-457)."""
        system = AdaptiveSurvivalSystem()
        failing_callback = Mock(side_effect=Exception("Callback error"))
        success_callback = Mock()
        system.on_risk_change(failing_callback)
        system.on_risk_change(success_callback)
        system.register_strategy("test")

        # Should not raise
        system.process(price=100.0, current_drawdown=0.02)

        failing_callback.assert_called_once()
        success_callback.assert_called_once()

    def test_with_regime(self):
        """Test process with regime parameter."""
        system = AdaptiveSurvivalSystem()
        system.register_strategy("test")

        result = system.process(price=100.0, current_drawdown=0.02, regime="trending")

        assert result is not None


class TestAdaptiveSurvivalSystemGetStatus:
    """Tests for get_status method (line 470)."""

    def test_returns_status(self):
        """Test status return value."""
        system = AdaptiveSurvivalSystem()
        system.register_strategy("test_strategy")

        status = system.get_status()

        assert "bar_count" in status
        assert "pending_evolutions" in status
        assert "registered_strategies" in status
        assert status["bar_count"] == 0
        assert "test_strategy" in status["registered_strategies"]


# ============================================================================
# Integration tests
# ============================================================================


class TestIntegration:
    """Integration tests for the complete workflow."""

    def test_full_evolution_workflow(self):
        """Test complete evolution workflow."""
        config = EvolutionConfig(
            min_bars_between_evolution=1,
            dissonance_threshold=0.5,
            min_strategies_to_evolve=1,
        )
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta, config=config)

        # Register callback
        received_requests = []
        bridge.on_evolution_request(lambda r: received_requests.append(r))

        # Trigger evolution
        state = MockMetaState(
            market_harmony=MockMarketHarmony.DISSONANT,
            risk_multiplier=0.2,
            strategy_weights={"s1": 0.3, "s2": 0.7},
        )

        request = bridge.check_and_trigger(state, current_bar=200)

        assert request is not None
        assert len(received_requests) == 1
        assert len(bridge.get_pending_evolutions()) == 1

        # Complete evolution
        bridge.mark_evolution_complete(request)

        assert len(bridge.get_pending_evolutions()) == 0

    def test_survival_system_full_cycle(self):
        """Test AdaptiveSurvivalSystem full cycle."""
        system = AdaptiveSurvivalSystem()

        # Register strategies
        system.register_strategy("momentum_1")
        system.register_strategy("mean_rev_1")

        # Register callbacks
        evolution_requests = []
        risk_changes = []
        system.on_evolution_needed(lambda r: evolution_requests.append(r))
        system.on_risk_change(lambda r: risk_changes.append(r))

        # Process bars
        for i in range(10):
            system.process(
                price=100 + i,
                current_drawdown=0.01 * i,
            )
            system.update_strategy_performance("momentum_1", 10 - i)
            system.update_strategy_performance("mean_rev_1", i)

        # Check status
        status = system.get_status()
        assert status["bar_count"] == 10
        assert len(risk_changes) == 10


# ============================================================================
# Edge cases
# ============================================================================


class TestEdgeCases:
    """Edge case tests."""

    def test_very_high_risk_multiplier(self):
        """Test with very high risk multiplier."""
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta)

        state = MockMetaState(
            market_harmony=MockMarketHarmony.CONSONANT,
            risk_multiplier=10.0,  # Very high
        )

        harmony_score = bridge._estimate_harmony_score(state)
        # CONSONANT: min(1.0, 10.0 * 1.2) = 1.0
        assert harmony_score == 1.0

    def test_zero_risk_multiplier(self):
        """Test with zero risk multiplier."""
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta)

        state = MockMetaState(
            market_harmony=MockMarketHarmony.DISSONANT,
            risk_multiplier=0.0,
        )

        harmony_score = bridge._estimate_harmony_score(state)
        # DISSONANT: 0.0 * 0.5 = 0.0
        assert harmony_score == 0.0

    def test_negative_risk_multiplier(self):
        """Test with negative risk multiplier."""
        config = EvolutionConfig(drawdown_threshold=0.15)
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta, config=config)

        state = MockMetaState(
            market_harmony=MockMarketHarmony.CONSONANT,
            risk_multiplier=-0.5,  # Negative
        )

        # Should trigger drawdown since -0.5 < 0.85
        result = bridge._evaluate_triggers(state, 100)
        assert result == EvolutionTrigger.DRAWDOWN

    def test_single_strategy(self):
        """Test with single strategy."""
        config = EvolutionConfig(min_strategies_to_evolve=1)
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta, config=config)

        state = MockMetaState(strategy_weights={"only_one": 1.0})

        result = bridge._find_underperformers(state)

        assert result == ["only_one"]

    def test_many_strategies(self):
        """Test with many strategies."""
        config = EvolutionConfig(min_strategies_to_evolve=1, max_strategies_to_evolve=3)
        meta = MockMetaController()
        bridge = AlphaEvolveBridge(meta, config=config)

        # Create 20 strategies
        weights = {f"s{i}": i / 20.0 for i in range(20)}
        state = MockMetaState(strategy_weights=weights)

        result = bridge._find_underperformers(state)

        # 20 strategies, 25% = 5, but min is 1, so should get max(1, 5) = 5
        assert len(result) == 5
        assert "s0" in result  # Lowest weight


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
