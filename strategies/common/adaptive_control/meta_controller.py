"""
Meta Controller - The Self-Regulating Trading System

This is the SYNTHESIS - the nervous system that observes and regulates itself.

Philosophy:
- Polyvagal: System has states (Ventral/Sympathetic/Dorsal)
- Musical: Strategies should be in "harmony" with market
- Adaptive: Everything learns and evolves
- Non-parametric: No fixed parameters where possible

The Meta Controller:
1. Monitors system health (infrastructure, PnL, latency)
2. Detects market regime (HMM + Spectral ensemble)
3. Selects/weights strategies based on regime
4. Adjusts risk dynamically (PID drawdown control)
5. LEARNS from outcomes (online adaptation)

This is NOT a strategy - it's the brain that manages strategies.
"""

from __future__ import annotations

# Python 3.10 compatibility
import datetime as _dt
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime

if hasattr(_dt, "UTC"):
    UTC = _dt.UTC
else:
    UTC = _dt.timezone.utc
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from strategies.common.audit.emitter import AuditEventEmitter


logger = logging.getLogger(__name__)


class SystemState(Enum):
    """
    Polyvagal-inspired system states.

    Like the autonomic nervous system:
    - VENTRAL: Social engagement, optimal functioning
    - SYMPATHETIC: Fight/flight, stress response
    - DORSAL: Freeze, conservation mode
    """

    VENTRAL = "ventral"  # Optimal - full trading
    SYMPATHETIC = "sympathetic"  # Stressed - reduce exposure
    DORSAL = "dorsal"  # Critical - minimal/no trading


class MarketHarmony(Enum):
    """
    Musical harmony between strategies and market.

    Like music theory:
    - CONSONANT: Strategies aligned with market regime
    - DISSONANT: Strategies conflicting with market
    - RESOLVING: Transitioning to new harmony
    """

    CONSONANT = "consonant"  # In tune
    DISSONANT = "dissonant"  # Out of tune
    RESOLVING = "resolving"  # Finding new key


@dataclass
class MetaState:
    """Current state of the meta-controller."""

    timestamp: datetime
    system_state: SystemState
    market_harmony: MarketHarmony

    # Health metrics
    health_score: float  # 0-100
    drawdown_pct: float

    # Regime metrics
    regime_confidence: float
    spectral_alpha: float

    # Risk multiplier (output)
    risk_multiplier: float

    # Strategy weights (output)
    strategy_weights: dict[str, float] = field(default_factory=dict)


class MetaController:
    """
    The self-regulating meta-system.

    Combines:
    - System health monitoring (polyvagal states)
    - Market regime detection (spectral + HMM)
    - Strategy ensemble management (harmony)
    - Dynamic risk control (PID)

    This is the synthesis - the brain that observes itself
    and adapts in real-time.

    Usage:
        meta = MetaController()

        # Register strategies
        meta.register_strategy("momentum", momentum_strategy)
        meta.register_strategy("mean_revert", mean_revert_strategy)

        # In your main loop
        def on_bar(bar):
            # Update meta state
            state = meta.update(
                bar=bar,
                current_pnl=portfolio.pnl,
                latency_ms=last_latency,
            )

            # Get strategy weights
            for name, weight in state.strategy_weights.items():
                strategies[name].set_weight(weight)

            # Apply risk multiplier
            position_size = base_size * state.risk_multiplier
    """

    def __init__(
        self,
        target_drawdown: float = 0.05,
        ventral_threshold: float = 70,
        sympathetic_threshold: float = 40,
        harmony_lookback: int = 50,
        audit_emitter: AuditEventEmitter | None = None,
    ):
        """
        Args:
            target_drawdown: Target max drawdown (decimal)
            ventral_threshold: Health score for Ventral state
            sympathetic_threshold: Health score for Sympathetic state
            harmony_lookback: Bars to calculate strategy-market harmony
            audit_emitter: Optional audit emitter for logging state changes
        """
        self.target_drawdown = target_drawdown
        self.ventral_threshold = ventral_threshold
        self.sympathetic_threshold = sympathetic_threshold
        self.harmony_lookback = harmony_lookback

        # Audit emitter for logging state changes (Spec 030)
        self._audit_emitter = audit_emitter

        # Components (lazy initialized)
        self._health_monitor = None
        self._regime_detector = None
        self._pid_controller = None

        # Strategy management
        self._strategies: dict[str, dict] = {}
        self._strategy_performance: dict[str, list[float]] = {}

        # State tracking
        self._current_state: SystemState = SystemState.VENTRAL
        self._current_harmony: MarketHarmony = MarketHarmony.CONSONANT
        self._returns_buffer: list[float] = []
        self._bars_processed: int = 0

        # Peak equity for drawdown
        self._peak_equity: float = 0.0
        self._current_equity: float = 0.0

        # Previous values for audit change detection
        self._prev_risk_multiplier: float | None = None
        self._prev_strategy_weights: dict[str, float] = {}

    def _ensure_components(self):
        """Lazy initialize components."""
        if self._health_monitor is None:
            from .system_health import SystemHealthMonitor

            self._health_monitor = SystemHealthMonitor(
                drawdown_halt_pct=self.target_drawdown * 100 * 2,  # Halt at 2x target
            )

        if self._regime_detector is None:
            from .spectral_regime import SpectralRegimeDetector

            self._regime_detector = SpectralRegimeDetector(
                window_size=256,
                min_samples=64,
            )

        if self._pid_controller is None:
            from .pid_drawdown import PIDDrawdownController

            self._pid_controller = PIDDrawdownController(
                target_drawdown=self.target_drawdown,
                Kp=2.0,
                Ki=0.1,
                Kd=0.5,
            )

    def register_strategy(
        self,
        name: str,
        regime_affinity: dict[str, float] | None = None,
        callback: Callable[[float], None] | None = None,
    ) -> None:
        """
        Register a strategy for management.

        Args:
            name: Strategy identifier
            regime_affinity: How well strategy performs in each regime
                            {"trending": 1.0, "normal": 0.7, "mean_reverting": 0.3}
            callback: Optional callback to set strategy weight
        """
        self._strategies[name] = {
            "affinity": regime_affinity or {"trending": 0.7, "normal": 0.7, "mean_reverting": 0.7},
            "callback": callback,
            "current_weight": 1.0,
        }
        self._strategy_performance[name] = []
        logger.info(f"MetaController: Registered strategy '{name}'")

    def record_strategy_pnl(self, name: str, pnl: float) -> None:
        """Record strategy PnL for harmony calculation."""
        if name in self._strategy_performance:
            self._strategy_performance[name].append(pnl)
            # Keep limited history
            if len(self._strategy_performance[name]) > self.harmony_lookback:
                self._strategy_performance[name] = self._strategy_performance[name][
                    -self.harmony_lookback :
                ]

    def update(
        self,
        current_return: float,
        current_equity: float,
        latency_ms: float = 0.0,
        order_filled: bool = True,
        slippage_bps: float = 0.0,
    ) -> MetaState:
        """
        Update meta-controller state.

        This is called on every bar/tick to:
        1. Update health monitoring
        2. Update regime detection
        3. Calculate system state
        4. Calculate strategy weights
        5. Calculate risk multiplier

        Args:
            current_return: Latest return
            current_equity: Current portfolio equity
            latency_ms: Order/message latency
            order_filled: Whether last order was filled
            slippage_bps: Slippage in basis points

        Returns:
            MetaState with all current information and outputs
        """
        self._ensure_components()
        self._bars_processed += 1

        # Track equity for drawdown
        self._current_equity = current_equity
        self._peak_equity = max(self._peak_equity, current_equity)
        drawdown = (
            (self._peak_equity - self._current_equity) / self._peak_equity
            if self._peak_equity > 0
            else 0
        )

        # Update health monitor
        if self._health_monitor is not None:
            self._health_monitor.set_equity(current_equity)
            if latency_ms > 0:
                self._health_monitor.record_latency(latency_ms)
            if order_filled:
                self._health_monitor.record_fill(slippage_bps)
            else:
                self._health_monitor.record_rejection()

            health_metrics = self._health_monitor.get_metrics()
        else:
            # Fallback if components not initialized
            from dataclasses import dataclass

            @dataclass
            class HealthMetrics:
                score: float = 50.0

            health_metrics = HealthMetrics()

        # Update regime detector
        if self._regime_detector is not None:
            self._regime_detector.update(current_return)
            self._returns_buffer.append(current_return)
            if len(self._returns_buffer) > 500:
                self._returns_buffer = self._returns_buffer[-500:]

            regime_analysis = self._regime_detector.analyze()
        else:
            # Fallback if components not initialized
            from dataclasses import dataclass

            @dataclass
            class RegimeAnalysis:
                regime: str = "unknown"
                confidence: float = 0.0
                alpha: float = 0.0

            regime_analysis = RegimeAnalysis()

        # Determine system state (polyvagal)
        prev_state = self._current_state
        self._current_state = self._calculate_system_state(
            health_metrics.score,
            drawdown,
        )

        # Audit: Log system state change
        if self._audit_emitter and self._current_state != prev_state:
            self._audit_emitter.emit_param_change(
                param_name="system_state",
                old_value=prev_state.value,
                new_value=self._current_state.value,
                trigger_reason=f"health_score={health_metrics.score:.1f}",
                source="meta_controller",
            )

        # Determine market harmony
        prev_harmony = self._current_harmony
        self._current_harmony = self._calculate_harmony(regime_analysis.regime)

        # Audit: Log market harmony change
        if self._audit_emitter and self._current_harmony != prev_harmony:
            self._audit_emitter.emit_param_change(
                param_name="market_harmony",
                old_value=prev_harmony.value,
                new_value=self._current_harmony.value,
                trigger_reason=f"regime={regime_analysis.regime}",
                source="meta_controller",
            )

        # Calculate strategy weights
        strategy_weights = self._calculate_strategy_weights(
            regime_analysis.regime,
            self._current_state,
            self._current_harmony,
        )

        # Calculate risk multiplier
        pid_multiplier = (
            self._pid_controller.update(drawdown) if self._pid_controller is not None else 1.0
        )
        state_multiplier = {
            SystemState.VENTRAL: 1.0,
            SystemState.SYMPATHETIC: 0.5,
            SystemState.DORSAL: 0.0,
        }[self._current_state]
        harmony_multiplier = {
            MarketHarmony.CONSONANT: 1.0,
            MarketHarmony.RESOLVING: 0.7,
            MarketHarmony.DISSONANT: 0.3,
        }[self._current_harmony]

        risk_multiplier = pid_multiplier * state_multiplier * harmony_multiplier

        # Audit: Log risk multiplier change (significant changes only)
        if self._audit_emitter and self._prev_risk_multiplier is not None:
            if abs(risk_multiplier - self._prev_risk_multiplier) > 0.01:
                self._audit_emitter.emit_param_change(
                    param_name="risk_multiplier",
                    old_value=f"{self._prev_risk_multiplier:.4f}",
                    new_value=f"{risk_multiplier:.4f}",
                    trigger_reason=f"drawdown={drawdown * 100:.2f}%",
                    source="meta_controller",
                )
        self._prev_risk_multiplier = risk_multiplier

        # Apply strategy weights via callbacks
        for name, info in self._strategies.items():
            weight = strategy_weights.get(name, 0.0)
            info["current_weight"] = weight
            if info["callback"]:
                info["callback"](weight)

        # Audit: Log strategy weight changes (significant changes only)
        if self._audit_emitter:
            for name, new_weight in strategy_weights.items():
                old_weight = self._prev_strategy_weights.get(name, 0.0)
                if abs(new_weight - old_weight) > 0.01:
                    self._audit_emitter.emit_param_change(
                        param_name=f"strategy_weight.{name}",
                        old_value=f"{old_weight:.4f}",
                        new_value=f"{new_weight:.4f}",
                        trigger_reason=f"state={self._current_state.value}",
                        source="meta_controller",
                    )
        self._prev_strategy_weights = strategy_weights.copy()

        return MetaState(
            timestamp=datetime.now(UTC),
            system_state=self._current_state,
            market_harmony=self._current_harmony,
            health_score=health_metrics.score,
            drawdown_pct=drawdown * 100,
            regime_confidence=regime_analysis.confidence,
            spectral_alpha=regime_analysis.alpha,
            risk_multiplier=risk_multiplier,
            strategy_weights=strategy_weights,
        )

    def _calculate_system_state(
        self,
        health_score: float,
        drawdown: float,
    ) -> SystemState:
        """Calculate polyvagal system state."""
        # Drawdown override
        if drawdown > self.target_drawdown * 2:
            return SystemState.DORSAL

        # Health-based
        if health_score >= self.ventral_threshold:
            return SystemState.VENTRAL
        elif health_score >= self.sympathetic_threshold:
            return SystemState.SYMPATHETIC
        else:
            return SystemState.DORSAL

    def _calculate_harmony(self, current_regime) -> MarketHarmony:
        """Calculate strategy-market harmony."""

        if not self._strategy_performance:
            return MarketHarmony.CONSONANT

        # Check if strategies are performing in current regime
        total_pnl = 0.0
        for _name, pnls in self._strategy_performance.items():
            if pnls:
                recent_pnl = sum(pnls[-10:])  # Last 10 observations
                total_pnl += recent_pnl

        # Positive PnL = consonant, negative = dissonant
        if total_pnl > 0:
            return MarketHarmony.CONSONANT
        elif total_pnl < -abs(self._current_equity * 0.001):  # More than 0.1% loss
            return MarketHarmony.DISSONANT
        else:
            return MarketHarmony.RESOLVING

    def _calculate_strategy_weights(
        self,
        regime,
        state: SystemState,
        harmony: MarketHarmony,
    ) -> dict[str, float]:
        """Calculate weights for each strategy."""
        from .spectral_regime import MarketRegime

        regime_key = {
            MarketRegime.TRENDING: "trending",
            MarketRegime.NORMAL: "normal",
            MarketRegime.MEAN_REVERTING: "mean_reverting",
            MarketRegime.UNKNOWN: "normal",
        }.get(regime, "normal")

        weights = {}
        for name, info in self._strategies.items():
            # Base weight from regime affinity
            base_weight = info["affinity"].get(regime_key, 0.5)

            # State adjustment
            state_mult = {
                SystemState.VENTRAL: 1.0,
                SystemState.SYMPATHETIC: 0.6,
                SystemState.DORSAL: 0.0,
            }[state]

            # Harmony adjustment
            harmony_mult = {
                MarketHarmony.CONSONANT: 1.0,
                MarketHarmony.RESOLVING: 0.8,
                MarketHarmony.DISSONANT: 0.4,
            }[harmony]

            weights[name] = base_weight * state_mult * harmony_mult

        # Normalize to sum to 1.0 if any weights
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}

        return weights

    @property
    def state(self) -> SystemState:
        """Current system state."""
        return self._current_state

    @property
    def harmony(self) -> MarketHarmony:
        """Current market harmony."""
        return self._current_harmony

    @property
    def audit_emitter(self) -> AuditEventEmitter | None:
        """Audit emitter for logging state changes."""
        return self._audit_emitter

    @audit_emitter.setter
    def audit_emitter(self, emitter: AuditEventEmitter | None) -> None:
        """Set the audit emitter."""
        self._audit_emitter = emitter

    def reset(self) -> None:
        """Reset controller state."""
        self._current_state = SystemState.VENTRAL
        self._current_harmony = MarketHarmony.CONSONANT
        self._returns_buffer = []
        self._bars_processed = 0
        self._peak_equity = 0.0
        self._current_equity = 0.0
        if self._pid_controller:
            self._pid_controller.reset()
        for name in self._strategy_performance:
            self._strategy_performance[name] = []
        logger.info("MetaController: Reset")
