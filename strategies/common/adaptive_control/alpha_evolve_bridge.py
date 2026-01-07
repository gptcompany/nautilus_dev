"""
Alpha-Evolve Bridge - The Connection Between MetaController and Strategy Evolution

When the MetaController detects DISSONANT state (system out of harmony with market),
it triggers Alpha-Evolve to generate new strategy variations.

This is NOT about predicting the market.
This is about ADAPTING when our current strategies no longer fit.

The market is a living organism made of living beings.
We are one small part of it. We observe. We adapt. We survive.

Philosophy:
- No fixed parameters (they become stale)
- No prediction (the future is unknowable)
- Only adaptation (respond to what IS)

Integration:
- MetaController monitors system/market harmony
- When DISSONANT: trigger Alpha-Evolve
- Alpha-Evolve generates variations (specs 006-010)
- Best variations replace underperformers
- Cycle continues

This is how we survive: by being water, not rock.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Callable, Dict, List, Optional

from .meta_controller import MarketHarmony, MetaController, MetaState

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class EvolutionTrigger(Enum):
    """Reasons why evolution was triggered."""

    DISSONANCE = "market_system_dissonance"
    DRAWDOWN = "excessive_drawdown"
    STAGNATION = "performance_stagnation"
    REGIME_SHIFT = "major_regime_shift"
    SCHEDULED = "scheduled_evolution"


@dataclass
class EvolutionRequest:
    """Request sent to Alpha-Evolve system."""

    trigger: EvolutionTrigger
    timestamp: datetime
    current_state: MetaState
    underperforming_strategies: List[str]
    market_conditions: Dict[str, float]
    priority: int  # 1-5, 5 = urgent


@dataclass
class EvolutionConfig:
    """Configuration for evolution triggers."""

    # When to trigger evolution
    dissonance_threshold: float = 0.3  # Harmony below this
    drawdown_threshold: float = 0.15  # 15% drawdown
    stagnation_periods: int = 50  # Bars without improvement

    # How often to allow evolution
    min_bars_between_evolution: int = 100  # Don't evolve too fast
    max_concurrent_evolutions: int = 2  # Don't overload

    # What to evolve
    min_strategies_to_evolve: int = 1
    max_strategies_to_evolve: int = 3


class AlphaEvolveBridge:
    """
    Bridge between MetaController and Alpha-Evolve system.

    This class doesn't implement the evolution itself
    (that's in scripts/alpha_evolve/), but provides the
    TRIGGER mechanism based on meta-controller state.

    The bridge observes the MetaController and decides
    WHEN evolution should be triggered, not HOW.

    Usage:
        meta = MetaController()
        bridge = AlphaEvolveBridge(meta)

        # Register callback for evolution requests
        bridge.on_evolution_request(my_handler)

        # In main loop
        state = meta.update(bar)
        bridge.check_and_trigger(state)
    """

    def __init__(
        self,
        meta_controller: MetaController,
        config: Optional[EvolutionConfig] = None,
        audit_emitter: "AuditEventEmitter | None" = None,
    ):
        """
        Args:
            meta_controller: The MetaController to observe
            config: Evolution trigger configuration
            audit_emitter: Optional audit emitter for logging evolution triggers
        """
        self.meta = meta_controller
        self.config = config or EvolutionConfig()

        # Audit emitter for logging evolution triggers (Spec 030)
        self._audit_emitter = audit_emitter

        self._callbacks: List[Callable[[EvolutionRequest], None]] = []
        self._last_evolution_bar: int = 0
        self._bars_since_improvement: int = 0
        self._best_sharpe: float = float("-inf")
        self._pending_requests: List[EvolutionRequest] = []

    def on_evolution_request(
        self,
        callback: Callable[[EvolutionRequest], None],
    ) -> None:
        """
        Register callback for evolution requests.

        Args:
            callback: Function to call when evolution is needed
        """
        self._callbacks.append(callback)

    def check_and_trigger(
        self,
        state: MetaState,
        current_bar: int = 0,
    ) -> Optional[EvolutionRequest]:
        """
        Check if evolution should be triggered based on current state.

        This is called after each MetaController update.
        It evaluates multiple conditions and may trigger evolution.

        Args:
            state: Current MetaState from MetaController
            current_bar: Current bar index (for timing)

        Returns:
            EvolutionRequest if triggered, None otherwise
        """
        # Check cooldown
        if current_bar - self._last_evolution_bar < self.config.min_bars_between_evolution:
            return None

        # Check pending requests limit
        if len(self._pending_requests) >= self.config.max_concurrent_evolutions:
            return None

        # Evaluate trigger conditions
        trigger = self._evaluate_triggers(state, current_bar)

        if trigger is None:
            return None

        # Find underperforming strategies
        underperformers = self._find_underperformers(state)

        if len(underperformers) < self.config.min_strategies_to_evolve:
            # Not enough underperformers to justify evolution
            return None

        # Create request
        request = EvolutionRequest(
            trigger=trigger,
            timestamp=datetime.utcnow(),
            current_state=state,
            underperforming_strategies=underperformers[: self.config.max_strategies_to_evolve],
            market_conditions=self._extract_market_conditions(state),
            priority=self._calculate_priority(trigger, state),
        )

        # Update state
        self._last_evolution_bar = current_bar
        self._pending_requests.append(request)

        # Audit: Log evolution trigger event
        if self._audit_emitter:
            from strategies.common.audit.events import AuditEventType

            self._audit_emitter.emit_system(
                event_type=AuditEventType.SYS_EVOLUTION_TRIGGER,
                source="alpha_evolve_bridge",
                payload={
                    "trigger_reason": trigger.value,
                    "underperforming_strategies": underperformers[
                        : self.config.max_strategies_to_evolve
                    ],
                    "priority": request.priority,
                    "harmony": state.market_harmony.value,
                    "risk_multiplier": state.risk_multiplier,
                    "current_bar": current_bar,
                },
            )

        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(request)
            except Exception as e:
                logger.error(f"Evolution callback error: {e}")

        logger.info(
            f"Evolution triggered: {trigger.value}, "
            f"strategies: {underperformers}, priority: {request.priority}"
        )

        return request

    def _evaluate_triggers(
        self,
        state: MetaState,
        current_bar: int,
    ) -> Optional[EvolutionTrigger]:
        """Evaluate which trigger condition is met (if any)."""
        # 1. Dissonance check (most important)
        if state.market_harmony == MarketHarmony.DISSONANT:
            # Check if it's severe enough
            harmony_score = self._estimate_harmony_score(state)
            if harmony_score < self.config.dissonance_threshold:
                return EvolutionTrigger.DISSONANCE

        # 2. Drawdown check
        if state.risk_multiplier < (1 - self.config.drawdown_threshold):
            return EvolutionTrigger.DRAWDOWN

        # 3. Stagnation check
        current_sharpe = self._estimate_sharpe(state)
        if current_sharpe > self._best_sharpe:
            self._best_sharpe = current_sharpe
            self._bars_since_improvement = 0
        else:
            self._bars_since_improvement += 1

        if self._bars_since_improvement >= self.config.stagnation_periods:
            self._bars_since_improvement = 0  # Reset
            return EvolutionTrigger.STAGNATION

        # 4. Major regime shift (implicit in dissonance, but explicit check)
        # This would require tracking regime history

        return None

    def _find_underperformers(self, state: MetaState) -> List[str]:
        """Find strategies that are underperforming."""
        if not state.strategy_weights:
            return []

        # Sort by weight (lower weight = worse performer)
        sorted_strategies = sorted(
            state.strategy_weights.items(),
            key=lambda x: x[1],
        )

        # Return bottom performers
        n_underperformers = max(
            self.config.min_strategies_to_evolve,
            len(sorted_strategies) // 4,  # Bottom 25%
        )

        return [name for name, _ in sorted_strategies[:n_underperformers]]

    def _estimate_harmony_score(self, state: MetaState) -> float:
        """Estimate harmony score from state (0-1, 1 = perfect harmony)."""
        # Simple heuristic based on risk multiplier and harmony state
        base_score = state.risk_multiplier

        if state.market_harmony == MarketHarmony.CONSONANT:
            return min(1.0, base_score * 1.2)
        elif state.market_harmony == MarketHarmony.RESOLVING:
            return base_score * 0.8
        else:  # DISSONANT
            return base_score * 0.5

    def _estimate_sharpe(self, state: MetaState) -> float:
        """Estimate current Sharpe-like metric from state."""
        # Use risk multiplier as proxy (higher = better recent performance)
        return state.risk_multiplier

    def _extract_market_conditions(self, state: MetaState) -> Dict[str, float]:
        """Extract market conditions for Alpha-Evolve context."""
        return {
            "risk_multiplier": state.risk_multiplier,
            "harmony": 1.0
            if state.market_harmony == MarketHarmony.CONSONANT
            else 0.5
            if state.market_harmony == MarketHarmony.RESOLVING
            else 0.0,
            "n_active_strategies": len(state.strategy_weights),
        }

    def _calculate_priority(
        self,
        trigger: EvolutionTrigger,
        state: MetaState,
    ) -> int:
        """Calculate priority (1-5) for the evolution request."""
        if trigger == EvolutionTrigger.DRAWDOWN:
            return 5  # Urgent - losing money
        elif trigger == EvolutionTrigger.DISSONANCE:
            if state.risk_multiplier < 0.5:
                return 4  # High - severe dissonance
            return 3  # Medium
        elif trigger == EvolutionTrigger.REGIME_SHIFT:
            return 3  # Medium - need to adapt
        elif trigger == EvolutionTrigger.STAGNATION:
            return 2  # Low - can wait
        else:
            return 1  # Scheduled - lowest

    def mark_evolution_complete(self, request: EvolutionRequest) -> None:
        """Mark an evolution request as complete."""
        if request in self._pending_requests:
            self._pending_requests.remove(request)
            logger.info(f"Evolution complete: {request.trigger.value}")

    def get_pending_evolutions(self) -> List[EvolutionRequest]:
        """Get list of pending evolution requests."""
        return self._pending_requests.copy()

    @property
    def audit_emitter(self) -> "AuditEventEmitter | None":
        """Audit emitter for logging evolution triggers."""
        return self._audit_emitter

    @audit_emitter.setter
    def audit_emitter(self, emitter: "AuditEventEmitter | None") -> None:
        """Set the audit emitter."""
        self._audit_emitter = emitter


class AdaptiveSurvivalSystem:
    """
    The complete adaptive survival system.

    This is the highest-level integration that combines:
    - MetaController (observation + response)
    - AlphaEvolveBridge (evolution trigger)
    - Your existing infrastructure

    It's designed to help you survive in markets
    made of living beings, by being alive yourself -
    adaptive, responsive, never rigid.

    Usage:
        system = AdaptiveSurvivalSystem()

        # Register your strategies
        system.register_strategy("momentum_1")
        system.register_strategy("mean_rev_1")

        # Connect to your trading system
        system.on_evolution_needed(trigger_alpha_evolve)
        system.on_risk_change(adjust_position_sizes)

        # Main loop
        for bar in market_data:
            actions = system.process(bar, drawdown, regime)
            execute(actions)
    """

    def __init__(
        self,
        meta_config: Optional[dict] = None,
        evolution_config: Optional[EvolutionConfig] = None,
    ):
        """Initialize the survival system."""
        from .meta_controller import MetaController

        self.meta = MetaController(**(meta_config or {}))
        self.bridge = AlphaEvolveBridge(self.meta, evolution_config)

        self._bar_count: int = 0
        self._risk_callbacks: List[Callable[[float], None]] = []

    def register_strategy(self, name: str) -> None:
        """Register a strategy with the meta system."""
        self.meta.register_strategy(name)

    def on_evolution_needed(
        self,
        callback: Callable[[EvolutionRequest], None],
    ) -> None:
        """Register callback for evolution needs."""
        self.bridge.on_evolution_request(callback)

    def on_risk_change(self, callback: Callable[[float], None]) -> None:
        """Register callback for risk multiplier changes."""
        self._risk_callbacks.append(callback)

    def update_strategy_performance(
        self,
        strategy_name: str,
        pnl: float,
    ) -> None:
        """Update performance for a strategy."""
        self.meta.record_strategy_pnl(strategy_name, pnl)

    def process(
        self,
        price: float,
        current_drawdown: float,
        regime: Optional[str] = None,
    ) -> Dict:
        """
        Process a new bar and return recommended actions.

        Args:
            price: Current price
            current_drawdown: Current drawdown (0-1)
            regime: Current market regime (optional)

        Returns:
            Dict with:
                - risk_multiplier: How much to scale positions
                - strategy_weights: Relative weights for each strategy
                - evolution_triggered: Whether evolution was triggered
                - system_state: Current system state
                - market_harmony: Current market harmony
        """
        self._bar_count += 1

        # Update meta controller
        state = self.meta.update(
            current_price=price,
            current_drawdown=current_drawdown,
            current_regime=regime,
        )

        # Check for evolution triggers
        evolution_request = self.bridge.check_and_trigger(state, self._bar_count)

        # Notify risk callbacks if risk changed significantly
        for callback in self._risk_callbacks:
            try:
                callback(state.risk_multiplier)
            except Exception as e:
                logger.error(f"Risk callback error: {e}")

        return {
            "risk_multiplier": state.risk_multiplier,
            "strategy_weights": state.strategy_weights,
            "evolution_triggered": evolution_request is not None,
            "evolution_request": evolution_request,
            "system_state": state.system_state.value,
            "market_harmony": state.market_harmony.value,
        }

    def get_status(self) -> Dict:
        """Get current system status."""
        return {
            "bar_count": self._bar_count,
            "pending_evolutions": len(self.bridge.get_pending_evolutions()),
            "registered_strategies": list(self.meta._strategy_performances.keys()),
        }
