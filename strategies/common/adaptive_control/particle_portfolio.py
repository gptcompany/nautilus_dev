"""
Particle-Based Portfolio Selection

For selecting and weighting strategies/signals in a robust way.

Why Particle Filter + Thompson Sampling?
- GA: Overfits, not adaptive, fixed parameters
- PSO: Converges too fast, still has parameters
- Particle Filter: Adaptive, probabilistic, non-linear, NO FIXED PARAMS

This module provides:
1. ParticlePortfolio: Particle filter for strategy weights
2. ThompsonSelector: Thompson Sampling for strategy selection
3. BayesianEnsemble: Combines both for robust portfolio

Philosophy (I Quattro Pilastri):
1. Probabilistico - Distributions, not point estimates
2. Non Lineare - Non-linear weight updates
3. Non Parametrico - Adapts to data
4. Scalare - Works with any number of strategies

CSRC Integration (Spec 031):
- Correlation-aware allocation via covariance penalty
- Penalizes over-allocation to correlated strategies
- Optional: Pass correlation_tracker and lambda_penalty to enable

Reference:
- Doucet et al. (2001): Sequential Monte Carlo Methods
- Thompson (1933): On the Likelihood that One Unknown Probability Exceeds Another
- Arulampalam et al. (2002): A Tutorial on Particle Filters
- Varlashova & Bilokon (2025): Covariance-penalized portfolio optimization
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from strategies.common.adaptive_control.correlation_tracker import (
        CorrelationMetrics,
    )


@dataclass
class Particle:
    """A single particle representing a portfolio hypothesis."""

    weights: Dict[str, float]  # Strategy -> weight
    log_weight: float = 0.0  # Log-likelihood weight of this particle
    fitness: float = 0.0  # Recent performance

    def normalize_weights(self) -> None:
        """Normalize strategy weights to sum to 1."""
        total = sum(abs(w) for w in self.weights.values())
        if total > 0:
            for k in self.weights:
                self.weights[k] /= total


@dataclass
class PortfolioState:
    """Current state of the particle portfolio."""

    strategy_weights: Dict[str, float]  # Consensus weights
    weight_uncertainty: Dict[str, float]  # Uncertainty per strategy
    effective_particles: float  # Effective sample size
    resampled: bool  # Was resampling triggered?
    # CSRC (Spec 031): Correlation metrics for observability
    correlation_metrics: Optional["CorrelationMetrics"] = None


class ParticlePortfolio:
    """
    Particle Filter for Strategy Portfolio Weights.

    Each particle represents a hypothesis about optimal weights.
    Particles are updated based on observed performance.
    Poor particles die, good particles reproduce.

    This is ADAPTIVE, PROBABILISTIC, and NON-PARAMETRIC.

    Usage:
        portfolio = ParticlePortfolio(
            strategies=["momentum", "mean_rev", "trend"],
            n_particles=100,
        )

        # Each period, update with strategy returns
        for period in data:
            returns = {
                "momentum": momentum_return,
                "mean_rev": mean_rev_return,
                "trend": trend_return,
            }

            state = portfolio.update(returns)

            # Use consensus weights
            for strat, weight in state.strategy_weights.items():
                allocate(strat, weight)
    """

    def __init__(
        self,
        strategies: List[str],
        n_particles: int = 100,
        resampling_threshold: float = 0.5,
        mutation_std: float = 0.1,
        audit_emitter: "AuditEventEmitter | None" = None,
        # CSRC (Spec 031): Correlation-aware allocation parameters
        correlation_tracker: "OnlineCorrelationMatrix | None" = None,
        lambda_penalty: float = 1.0,
    ):
        """
        Args:
            strategies: List of strategy names
            n_particles: Number of particles (more = more accurate)
            resampling_threshold: ESS ratio below which to resample
            mutation_std: Standard deviation for weight mutations
            audit_emitter: Optional audit emitter for logging signals
            correlation_tracker: Optional OnlineCorrelationMatrix for CSRC (Spec 031).
                                 If provided, enables correlation-aware allocation.
            lambda_penalty: Covariance penalty strength (default: 1.0, range: [0.0, 5.0]).
                            Higher = stronger diversification pressure.
                            - 0.0: No penalty (baseline behavior)
                            - 0.5: Mild diversification
                            - 1.0: Balanced (default)
                            - 2.0: Strong diversification
                            - 5.0: Aggressive diversification
        """
        self.strategies = strategies
        self.n_particles = n_particles
        self.resampling_threshold = resampling_threshold
        self.mutation_std = mutation_std

        # Audit emitter for logging signals and resampling events (Spec 030)
        self._audit_emitter = audit_emitter

        # CSRC (Spec 031): Correlation tracking for covariance penalty
        self._correlation_tracker = correlation_tracker
        self._lambda_penalty = lambda_penalty

        # Strategy indices for penalty calculation
        self._strategy_indices: Dict[str, int] = {
            s: i for i, s in enumerate(strategies)
        }

        # Initialize particles with random weights
        self.particles: List[Particle] = []
        for _ in range(n_particles):
            weights = {s: random.random() for s in strategies}
            p = Particle(weights=weights)
            p.normalize_weights()
            self.particles.append(p)

    def update(self, strategy_returns: Dict[str, float]) -> PortfolioState:
        """
        Update particle weights based on observed returns.

        CSRC Integration (Spec 031):
        If correlation_tracker is configured, this method:
        1. Updates the correlation tracker with current returns
        2. Applies covariance penalty to each particle's fitness:
           adjusted_fitness = portfolio_return - lambda * covariance_penalty
        3. Includes correlation_metrics in returned PortfolioState

        Args:
            strategy_returns: Dict of strategy -> return this period

        Returns:
            PortfolioState with consensus weights, uncertainty, and correlation_metrics
        """
        # CSRC (Spec 031): Update correlation tracker with new returns
        correlation_metrics = None
        corr_matrix = None
        if self._correlation_tracker is not None:
            self._correlation_tracker.update(strategy_returns)
            corr_matrix = self._correlation_tracker.get_correlation_matrix()

        # 1. Update particle weights based on likelihood
        for particle in self.particles:
            # Calculate portfolio return for this particle
            portfolio_return = sum(
                particle.weights.get(s, 0) * strategy_returns.get(s, 0)
                for s in self.strategies
            )

            # Likelihood: higher return = higher weight
            # Using exponential likelihood (like softmax)
            particle.fitness = portfolio_return

            # CSRC (Spec 031): Apply covariance penalty to fitness
            # reward = sharpe - lambda * covariance_penalty
            if self._correlation_tracker is not None and self._lambda_penalty > 0:
                from strategies.common.adaptive_control.correlation_tracker import (
                    calculate_covariance_penalty,
                )

                penalty = calculate_covariance_penalty(
                    weights=particle.weights,
                    corr_matrix=corr_matrix,
                    strategy_indices=self._correlation_tracker.strategy_indices,
                )
                particle.fitness -= self._lambda_penalty * penalty

            particle.log_weight += particle.fitness  # Accumulate log-likelihood

        # 2. Normalize weights
        max_log_weight = max(p.log_weight for p in self.particles)
        for p in self.particles:
            p.log_weight -= max_log_weight  # Prevent overflow

        weights = [math.exp(p.log_weight) for p in self.particles]
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]

        # 3. Calculate effective sample size
        ess = 1.0 / sum(w * w for w in weights) if sum(weights) > 0 else 0
        ess_ratio = ess / self.n_particles

        # 4. Resample if ESS is too low (particles have degenerated)
        resampled = False
        if ess_ratio < self.resampling_threshold:
            self._resample(weights)
            resampled = True

            # Audit: Log resampling event
            if self._audit_emitter:
                from strategies.common.audit.events import AuditEventType

                self._audit_emitter.emit_system(
                    event_type=AuditEventType.SYS_RESAMPLING,
                    source="particle_portfolio",
                    payload={
                        "ess": ess,
                        "ess_ratio": ess_ratio,
                        "threshold": self.resampling_threshold,
                        "n_particles": self.n_particles,
                    },
                )

        # 5. Mutate particles (exploration)
        self._mutate()

        # 6. Calculate consensus weights (weighted average)
        consensus = {s: 0.0 for s in self.strategies}
        uncertainty = {s: 0.0 for s in self.strategies}

        for i, particle in enumerate(self.particles):
            w = weights[i] if not resampled else 1.0 / self.n_particles
            for s in self.strategies:
                consensus[s] += w * particle.weights.get(s, 0)

        # Calculate uncertainty (weighted std)
        for i, particle in enumerate(self.particles):
            w = weights[i] if not resampled else 1.0 / self.n_particles
            for s in self.strategies:
                diff = particle.weights.get(s, 0) - consensus[s]
                uncertainty[s] += w * diff * diff

        for s in self.strategies:
            uncertainty[s] = math.sqrt(uncertainty[s])

        # CSRC (Spec 031): Get correlation metrics for observability
        if self._correlation_tracker is not None:
            correlation_metrics = self._correlation_tracker.get_metrics(consensus)

        state = PortfolioState(
            strategy_weights=consensus,
            weight_uncertainty=uncertainty,
            effective_particles=ess,
            resampled=resampled,
            correlation_metrics=correlation_metrics,
        )

        # Audit: Log consensus signal
        if self._audit_emitter:
            # Calculate overall consensus confidence
            avg_uncertainty = (
                sum(uncertainty.values()) / len(uncertainty) if uncertainty else 0.5
            )
            confidence = max(0.0, 1.0 - avg_uncertainty)

            # Find dominant strategy for signal attribution
            dominant_strategy = (
                max(consensus, key=consensus.get) if consensus else "unknown"
            )
            signal_value = consensus.get(dominant_strategy, 0.0)

            self._audit_emitter.emit_signal(
                signal_value=signal_value,
                regime="ENSEMBLE",
                confidence=confidence,
                strategy_source=f"particle_portfolio:{dominant_strategy}",
                source="particle_portfolio",
            )

            # CSRC (Spec 031): Emit correlation metrics to audit trail
            if correlation_metrics is not None:
                from strategies.common.audit.events import AuditEventType

                self._audit_emitter.emit_system(
                    event_type=AuditEventType.SYS_CORRELATION_UPDATE,
                    source="particle_portfolio",
                    payload={
                        "herfindahl_index": correlation_metrics.herfindahl_index,
                        "effective_n_strategies": correlation_metrics.effective_n_strategies,
                        "max_pairwise_correlation": correlation_metrics.max_pairwise_correlation,
                        "avg_correlation": correlation_metrics.avg_correlation,
                        "lambda_penalty": self._lambda_penalty,
                    },
                )

        return state

    def _resample(self, weights: List[float]) -> None:
        """Resample particles using systematic resampling.

        Handles edge cases:
        - NaN/Inf weights: Falls back to uniform resampling
        - Zero total weight: Falls back to uniform resampling
        """
        import math

        n = self.n_particles

        # Validate weights - check for NaN, Inf, or zero total
        valid_weights = all(math.isfinite(w) for w in weights)
        total_weight = sum(weights) if valid_weights else 0.0

        if not valid_weights or total_weight <= 0:
            # Fallback: uniform resampling (copy each particle once)
            # This prevents infinite loop on NaN/Inf/zero weights
            new_particles = []
            for particle in self.particles:
                new_p = Particle(
                    weights=particle.weights.copy(),
                    log_weight=0.0,
                    fitness=particle.fitness,
                )
                new_particles.append(new_p)
            self.particles = new_particles
            return

        positions = [(random.random() + i) / n for i in range(n)]

        cumsum = []
        total = 0.0
        for w in weights:
            total += w
            cumsum.append(total)

        new_particles = []
        i, j = 0, 0

        while i < n:
            if positions[i] < cumsum[j]:
                # Copy particle j
                old = self.particles[j]
                new_p = Particle(
                    weights=old.weights.copy(),
                    log_weight=0.0,  # Reset weight after resampling
                    fitness=old.fitness,
                )
                new_particles.append(new_p)
                i += 1
            else:
                j += 1
                if j >= len(cumsum):
                    j = len(cumsum) - 1

        self.particles = new_particles

    def _mutate(self) -> None:
        """Apply random mutations to particle weights (exploration)."""
        for particle in self.particles:
            for s in self.strategies:
                # Small random perturbation
                noise = random.gauss(0, self.mutation_std)
                particle.weights[s] = max(0, particle.weights[s] + noise)
            particle.normalize_weights()

    def get_best_particle(self) -> Particle:
        """Get the particle with highest fitness."""
        return max(self.particles, key=lambda p: p.fitness)

    @property
    def audit_emitter(self) -> "AuditEventEmitter | None":
        """Audit emitter for logging signals."""
        return self._audit_emitter

    @audit_emitter.setter
    def audit_emitter(self, emitter: "AuditEventEmitter | None") -> None:
        """Set the audit emitter."""
        self._audit_emitter = emitter

    # CSRC (Spec 031): Correlation tracking properties
    @property
    def correlation_tracker(self) -> "OnlineCorrelationMatrix | None":
        """Correlation tracker for CSRC allocation."""
        return self._correlation_tracker

    @correlation_tracker.setter
    def correlation_tracker(self, tracker: "OnlineCorrelationMatrix | None") -> None:
        """Set the correlation tracker."""
        self._correlation_tracker = tracker

    @property
    def lambda_penalty(self) -> float:
        """Covariance penalty strength for CSRC."""
        return self._lambda_penalty

    @lambda_penalty.setter
    def lambda_penalty(self, value: float) -> None:
        """Set the covariance penalty strength."""
        self._lambda_penalty = value


@dataclass
class StrategyStats:
    """Statistics for Thompson Sampling."""

    successes: float = 1.0  # Prior: 1 success
    failures: float = 1.0  # Prior: 1 failure

    @property
    def mean(self) -> float:
        """Expected success rate."""
        return self.successes / (self.successes + self.failures)

    def sample(self) -> float:
        """Sample from Beta posterior."""
        # Beta distribution sampling
        return random.betavariate(self.successes, self.failures)


class ThompsonSelector:
    """
    Thompson Sampling for Strategy Selection.

    Each strategy has a Beta distribution over its success probability.
    We sample from each distribution and select the highest.

    This naturally balances EXPLORATION vs EXPLOITATION.

    Unlike GA/PSO, this has NO hyperparameters (except priors).

    Adaptive Discounting (Spec 032):
    When regime_detector is provided, decay factor adapts automatically
    based on market volatility:
    - Low volatility (variance_ratio < 0.7): decay = 0.99 (stable estimates)
    - High volatility (variance_ratio > 1.5): decay = 0.95 (faster adaptation)
    - Normal volatility: Interpolated linearly

    Academic Foundation:
    - Qi et al. (2023): Discounted Thompson Sampling for Non-Stationary Bandits
    - de Freitas Fonseca et al. (2024): RF-DSW TS

    Usage:
        # Basic usage (fixed decay)
        selector = ThompsonSelector(["strat_a", "strat_b", "strat_c"])

        # Adaptive decay with regime detector
        from strategies.common.adaptive_control.dsp_filters import IIRRegimeDetector
        detector = IIRRegimeDetector()
        selector = ThompsonSelector(
            strategies=["strat_a", "strat_b"],
            regime_detector=detector,
        )

        # Each period
        selected = selector.select()
        use_strategy(selected)

        # Update with outcome (uses adaptive decay if detector provided)
        if profit > 0:
            selector.update(selected, success=True)
        else:
            selector.update(selected, success=False)
    """

    def __init__(
        self,
        strategies: List[str],
        decay: float = 0.99,  # Base forgetting factor (used when no detector)
        regime_detector: "IIRRegimeDetector | None" = None,  # Spec 032: Adaptive decay
        audit_emitter: "AuditEventEmitter | None" = None,  # Spec 032: Decay audit
    ):
        """
        Args:
            strategies: List of strategy names
            decay: Base decay factor (used when regime_detector is None)
            regime_detector: Optional IIRRegimeDetector for adaptive decay (Spec 032)
            audit_emitter: Optional audit emitter for decay event logging (Spec 032)
        """
        self.strategies = strategies
        self._fixed_decay = decay  # Store base decay
        self._regime_detector = regime_detector
        self._audit_emitter = audit_emitter
        self.stats: Dict[str, StrategyStats] = {s: StrategyStats() for s in strategies}

        # Initialize adaptive decay calculator if detector provided
        if regime_detector is not None:
            from strategies.common.adaptive_control.adaptive_decay import (
                AdaptiveDecayCalculator,
            )

            self._decay_calculator = AdaptiveDecayCalculator()
        else:
            self._decay_calculator = None

    @property
    def current_decay(self) -> float:
        """Get current decay value (adaptive or fixed).

        Returns:
            Current decay factor in [0.95, 0.99] range.
        """
        return self._get_decay()

    def _get_decay(self) -> float:
        """Internal method to get current decay value.

        If regime_detector is configured, calculates adaptive decay.
        Otherwise returns fixed decay value.

        Returns:
            Current decay factor.
        """
        if self._decay_calculator is not None and self._regime_detector is not None:
            decay = self._decay_calculator.calculate_from_detector(
                self._regime_detector
            )
            self._emit_decay_event(decay)
            return decay
        return self._fixed_decay

    def _emit_decay_event(self, decay_value: float) -> None:
        """Emit decay update event to audit trail (Spec 032 - US3).

        Args:
            decay_value: Current adaptive decay value.
        """
        if self._audit_emitter is None:
            return

        from strategies.common.audit.events import AuditEventType

        self._audit_emitter.emit_system(
            event_type=AuditEventType.SYS_DECAY_UPDATE,
            source="thompson_selector",
            payload={
                "decay_value": decay_value,
                "variance_ratio": self._regime_detector.variance_ratio,
                "is_adaptive": True,
            },
        )

    def select(self) -> str:
        """
        Select a strategy using Thompson Sampling.

        Returns:
            Selected strategy name
        """
        samples = {s: self.stats[s].sample() for s in self.strategies}
        return max(samples, key=samples.get)

    def select_top_k(self, k: int) -> List[str]:
        """
        Select top k strategies.

        Args:
            k: Number of strategies to select

        Returns:
            List of selected strategy names
        """
        samples = {s: self.stats[s].sample() for s in self.strategies}
        sorted_strats = sorted(samples.keys(), key=lambda s: samples[s], reverse=True)
        return sorted_strats[:k]

    def update(self, strategy: str, success: bool) -> None:
        """
        Update strategy statistics.

        Uses adaptive decay if regime_detector is configured,
        otherwise uses fixed decay value.

        Args:
            strategy: Strategy name
            success: Whether the strategy was successful
        """
        if strategy not in self.stats:
            return

        # Get decay (adaptive or fixed)
        decay = self._get_decay()

        # Apply decay (forget old observations)
        for s in self.strategies:
            self.stats[s].successes *= decay
            self.stats[s].failures *= decay

        # Update selected strategy
        if success:
            self.stats[strategy].successes += 1
        else:
            self.stats[strategy].failures += 1

    def update_continuous(self, strategy: str, return_value: float) -> None:
        """
        Update with continuous return (not just success/failure).

        Uses adaptive decay if regime_detector is configured,
        otherwise uses fixed decay value.

        Args:
            strategy: Strategy name
            return_value: Strategy return (can be negative)
        """
        if strategy not in self.stats:
            return

        # Get decay (adaptive or fixed)
        decay = self._get_decay()

        # Apply decay FIRST (consistent with update() method)
        for s in self.strategies:
            self.stats[s].successes *= decay
            self.stats[s].failures *= decay

        # Convert continuous to pseudo-counts
        # Positive return = partial success
        if return_value >= 0:
            self.stats[strategy].successes += min(1.0, return_value * 10)
        else:
            self.stats[strategy].failures += min(1.0, abs(return_value) * 10)

    def get_probabilities(self) -> Dict[str, float]:
        """Get current success probability estimates."""
        return {s: self.stats[s].mean for s in self.strategies}


class BayesianEnsemble:
    """
    Combines Particle Filter + Thompson Sampling.

    - Particle Filter: For continuous weight optimization
    - Thompson Sampling: For discrete strategy selection

    This is the ROBUST solution for portfolio selection.

    Usage:
        ensemble = BayesianEnsemble(
            strategies=["momentum", "mean_rev", "breakout"],
            n_particles=50,
        )

        for period in data:
            # Get current weights
            weights, selected = ensemble.get_allocation()

            # Execute with weights
            returns = execute_strategies(weights)

            # Update
            ensemble.update(returns)
    """

    def __init__(
        self,
        strategies: List[str],
        n_particles: int = 50,
        selection_fraction: float = 0.5,
    ):
        """
        Args:
            strategies: List of strategy names
            n_particles: Particles for weight optimization
            selection_fraction: Fraction of strategies to activate
        """
        self.strategies = strategies
        self.selection_fraction = selection_fraction

        self.particle_portfolio = ParticlePortfolio(
            strategies=strategies,
            n_particles=n_particles,
        )
        self.thompson = ThompsonSelector(strategies=strategies)

        self._last_state: Optional[PortfolioState] = None

    def get_allocation(self) -> Tuple[Dict[str, float], List[str]]:
        """
        Get current allocation.

        Returns:
            (weights, selected_strategies)
        """
        # Use Thompson to select which strategies to activate
        k = max(1, int(len(self.strategies) * self.selection_fraction))
        selected = self.thompson.select_top_k(k)

        # Use Particle Filter weights for selected strategies
        if self._last_state:
            weights = self._last_state.strategy_weights.copy()
        else:
            # Equal weights initially
            weights = {s: 1.0 / len(self.strategies) for s in self.strategies}

        # Zero out non-selected strategies
        for s in self.strategies:
            if s not in selected:
                weights[s] = 0.0

        # Renormalize
        total = sum(weights.values())
        if total > 0:
            weights = {s: w / total for s, w in weights.items()}

        return weights, selected

    def update(self, strategy_returns: Dict[str, float]) -> PortfolioState:
        """
        Update with observed returns.

        Args:
            strategy_returns: Dict of strategy -> return

        Returns:
            Updated PortfolioState
        """
        # Update particle portfolio
        state = self.particle_portfolio.update(strategy_returns)
        self._last_state = state

        # Update Thompson selector
        for strat, ret in strategy_returns.items():
            self.thompson.update_continuous(strat, ret)

        return state

    def get_strategy_rankings(self) -> List[Tuple[str, float, float]]:
        """
        Get strategy rankings with uncertainty.

        Returns:
            List of (strategy, weight, uncertainty) sorted by weight
        """
        if not self._last_state:
            return [(s, 1.0 / len(self.strategies), 0.5) for s in self.strategies]

        rankings = []
        for s in self.strategies:
            weight = self._last_state.strategy_weights.get(s, 0)
            uncertainty = self._last_state.weight_uncertainty.get(s, 0.5)
            rankings.append((s, weight, uncertainty))

        return sorted(rankings, key=lambda x: x[1], reverse=True)
