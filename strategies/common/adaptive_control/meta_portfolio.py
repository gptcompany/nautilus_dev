"""
Meta-Portfolio: Multi-Level Adaptive Portfolio System

Three levels of adaptation:
1. BACKTEST MATRIX: Test many configurations offline
2. PRODUCTION ENSEMBLE: Run top-K systems in parallel
3. LIVE ADAPTATION: Adjust weights based on real PnL

Uses Giller sizing at portfolio level for non-linear risk control.

Philosophy (I Cinque Pilastri):
1. Probabilistico - Thompson + Particle for selection
2. Non Lineare - Giller for portfolio sizing
3. Non Parametrico - Adapts to real PnL, no fixed weights
4. Scalare - Works with any number of systems/strategies
5. Leggi Naturali - Evolutionary selection (survival of fittest)

Usage:
    # 1. Create portfolio manager
    portfolio = MetaPortfolio(base_size=1000.0)

    # 2. Register systems (from backtest selection)
    portfolio.register_system("bayesian_5strat", initial_weight=0.4)
    portfolio.register_system("thompson_10strat", initial_weight=0.3)
    portfolio.register_system("particle_momentum", initial_weight=0.3)

    # 3. In production loop
    for bar in live_data:
        # Get signals from each system
        signals = {
            "bayesian_5strat": system_a.get_signal(bar),
            "thompson_10strat": system_b.get_signal(bar),
            "particle_momentum": system_c.get_signal(bar),
        }

        # Get portfolio signal and size
        portfolio_signal, position_size = portfolio.aggregate(signals)

        # Execute
        execute_trade(portfolio_signal, position_size)

        # After period, update with PnL
        pnls = {
            "bayesian_5strat": pnl_a,
            "thompson_10strat": pnl_b,
            "particle_momentum": pnl_c,
        }
        portfolio.update_pnl(pnls)
"""

from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from .particle_portfolio import BayesianEnsemble, ThompsonSelector

logger = logging.getLogger(__name__)


@dataclass
class SystemConfig:
    """Configuration for a trading system."""

    name: str
    selector_type: str  # "thompson", "particle", "bayesian"
    n_particles: int
    strategies: List[str]
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BacktestResult:
    """Result from a single backtest."""

    config: SystemConfig
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    total_return: float
    win_rate: float
    n_trades: int
    pnl_series: List[float] = field(default_factory=list)


@dataclass
class SystemState:
    """Current state of a production system."""

    name: str
    weight: float
    cumulative_pnl: float
    recent_pnl: List[float]
    n_updates: int
    is_active: bool


class BacktestMatrix:
    """
    Run and evaluate multiple system configurations.

    Creates a matrix of configurations and evaluates each.
    Selects top performers for production.
    """

    def __init__(
        self,
        backtest_runner: Optional[Callable[[SystemConfig], BacktestResult]] = None,
    ):
        """
        Args:
            backtest_runner: Function that runs backtest and returns result
        """
        self.backtest_runner = backtest_runner
        self.configs: List[SystemConfig] = []
        self.results: List[BacktestResult] = []

    def add_config(self, config: SystemConfig) -> None:
        """Add a configuration to test."""
        self.configs.append(config)

    def generate_configs(
        self,
        selector_types: List[str],
        particle_counts: List[int],
        strategy_sets: List[List[str]],
    ) -> None:
        """
        Generate configuration matrix.

        Args:
            selector_types: ["thompson", "particle", "bayesian"]
            particle_counts: [0, 20, 50, 100]
            strategy_sets: [["mom", "mr"], ["mom", "mr", "trend"], ...]
        """
        for selector in selector_types:
            for n_particles in particle_counts:
                # Skip invalid combinations
                if selector == "thompson" and n_particles > 0:
                    continue
                if selector in ["particle", "bayesian"] and n_particles == 0:
                    continue

                for strategies in strategy_sets:
                    config = SystemConfig(
                        name=f"{selector}_{n_particles}p_{len(strategies)}s",
                        selector_type=selector,
                        n_particles=n_particles,
                        strategies=strategies,
                    )
                    self.configs.append(config)

        logger.info(f"Generated {len(self.configs)} configurations")

    def run_all(self) -> List[BacktestResult]:
        """Run all backtests and return results."""
        if not self.backtest_runner:
            raise ValueError("No backtest_runner provided")

        self.results = []
        for i, config in enumerate(self.configs):
            logger.info(f"Running backtest {i + 1}/{len(self.configs)}: {config.name}")
            try:
                result = self.backtest_runner(config)
                self.results.append(result)
            except Exception as e:
                logger.error(f"Backtest failed for {config.name}: {e}")

        return self.results

    def select_top_k(
        self,
        k: int,
        metric: str = "sharpe_ratio",
        min_trades: int = 30,
    ) -> List[BacktestResult]:
        """
        Select top K configurations by metric.

        Args:
            k: Number of top systems to select
            metric: Metric to rank by ("sharpe_ratio", "sortino_ratio", "total_return")
            min_trades: Minimum trades required

        Returns:
            Top K BacktestResults
        """
        # Filter by minimum trades
        valid = [r for r in self.results if r.n_trades >= min_trades]

        # Sort by metric
        sorted_results = sorted(
            valid,
            key=lambda r: getattr(r, metric, 0),
            reverse=True,
        )

        return sorted_results[:k]

    def save_results(self, path: Path) -> None:
        """Save results to JSON."""
        data = []
        for r in self.results:
            data.append(
                {
                    "config": {
                        "name": r.config.name,
                        "selector_type": r.config.selector_type,
                        "n_particles": r.config.n_particles,
                        "strategies": r.config.strategies,
                    },
                    "sharpe_ratio": r.sharpe_ratio,
                    "sortino_ratio": r.sortino_ratio,
                    "max_drawdown": r.max_drawdown,
                    "total_return": r.total_return,
                    "win_rate": r.win_rate,
                    "n_trades": r.n_trades,
                }
            )

        with open(path, "w") as f:
            json.dump(data, f, indent=2)


class MetaPortfolio:
    """
    Production portfolio manager with live adaptation.

    Combines multiple trading systems with:
    - Bayesian weight updates based on PnL
    - Giller sizing at portfolio level
    - Automatic deactivation of failing systems
    """

    def __init__(
        self,
        base_size: float = 1000.0,
        giller_exponent: float = 0.5,
        adaptation_rate: float = 0.1,
        min_weight: float = 0.05,
        max_weight: float = 0.5,
        deactivation_threshold: float = -0.20,  # -20% cumulative PnL
    ):
        """
        Args:
            base_size: Base position size
            giller_exponent: Giller sizing exponent (0.5 = sqrt)
            adaptation_rate: How fast to adapt weights (0.1 = 10% per update)
            min_weight: Minimum weight per system
            max_weight: Maximum weight per system
            deactivation_threshold: Cumulative PnL below which to deactivate
        """
        self.base_size = base_size
        self.giller_exponent = giller_exponent
        self.adaptation_rate = adaptation_rate
        self.min_weight = min_weight
        self.max_weight = max_weight
        self.deactivation_threshold = deactivation_threshold

        self._systems: Dict[str, SystemState] = {}
        self._ensemble: Optional[BayesianEnsemble] = None
        self._thompson: Optional[ThompsonSelector] = None

        self._total_pnl: float = 0.0
        self._peak_equity: float = 0.0
        self._history: List[Dict] = []

    def register_system(
        self,
        name: str,
        initial_weight: float = None,
    ) -> None:
        """
        Register a trading system.

        Args:
            name: System identifier
            initial_weight: Initial weight (if None, equal weight)
        """
        n_systems = len(self._systems) + 1
        weight = initial_weight or (1.0 / n_systems)

        self._systems[name] = SystemState(
            name=name,
            weight=weight,
            cumulative_pnl=0.0,
            recent_pnl=[],
            n_updates=0,
            is_active=True,
        )

        # Rebuild ensemble
        self._rebuild_ensemble()
        logger.info(f"Registered system '{name}' with weight {weight:.2%}")

    def _rebuild_ensemble(self) -> None:
        """Rebuild the Bayesian ensemble with current systems."""
        active_systems = [s.name for s in self._systems.values() if s.is_active]

        if len(active_systems) >= 2:
            self._ensemble = BayesianEnsemble(
                strategies=active_systems,
                n_particles=30,
                selection_fraction=1.0,  # Use all
            )
        else:
            self._ensemble = None

        self._thompson = ThompsonSelector(
            strategies=active_systems,
            decay=0.99,
        )

    def aggregate(
        self,
        signals: Dict[str, float],
    ) -> Tuple[float, float]:
        """
        Aggregate signals from all systems into portfolio signal and size.

        Args:
            signals: Dict of system_name -> signal (-1 to +1)

        Returns:
            (portfolio_signal, position_size)
        """
        # Get current weights
        weights = self._get_current_weights()

        # Weighted sum of signals
        portfolio_signal = 0.0
        total_weight = 0.0

        for name, signal in signals.items():
            if name in self._systems and self._systems[name].is_active:
                w = weights.get(name, 0)
                portfolio_signal += w * signal
                total_weight += w

        # Normalize
        if total_weight > 0:
            portfolio_signal /= total_weight

        # Giller sizing at portfolio level
        # size = |signal|^exponent * base_size
        if abs(portfolio_signal) < 1e-10:
            position_size = 0.0
        else:
            magnitude = abs(portfolio_signal)
            position_size = (magnitude**self.giller_exponent) * self.base_size

            # Preserve sign
            if portfolio_signal < 0:
                position_size = -position_size

        return portfolio_signal, position_size

    def _get_current_weights(self) -> Dict[str, float]:
        """Get current system weights."""
        weights = {}
        total = 0.0

        for name, state in self._systems.items():
            if state.is_active:
                weights[name] = state.weight
                total += state.weight

        # Normalize
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}

        return weights

    def update_pnl(self, pnls: Dict[str, float]) -> Dict[str, float]:
        """
        Update system weights based on observed PnL.

        Args:
            pnls: Dict of system_name -> PnL this period

        Returns:
            New weights after update
        """
        for name, pnl in pnls.items():
            if name not in self._systems:
                continue

            state = self._systems[name]
            state.cumulative_pnl += pnl
            state.recent_pnl.append(pnl)
            state.n_updates += 1

            # Keep limited history
            if len(state.recent_pnl) > 50:
                state.recent_pnl = state.recent_pnl[-50:]

            # Update Thompson selector
            if self._thompson:
                self._thompson.update_continuous(name, pnl)

            # Check deactivation
            if state.cumulative_pnl < self.deactivation_threshold * self.base_size:
                if state.is_active:
                    state.is_active = False
                    logger.warning(
                        f"Deactivated system '{name}' due to poor performance "
                        f"(cumulative PnL: {state.cumulative_pnl:.2f})"
                    )
                    self._rebuild_ensemble()

        # Update ensemble
        if self._ensemble:
            self._ensemble.update(pnls)

        # Update weights using Thompson probabilities
        if self._thompson:
            probs = self._thompson.get_probabilities()
            self._update_weights_from_probs(probs)

        # Track total
        self._total_pnl += sum(pnls.values())
        self._peak_equity = max(self._peak_equity, self._total_pnl)

        # Record history
        self._history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "pnls": pnls.copy(),
                "weights": self._get_current_weights(),
                "total_pnl": self._total_pnl,
            }
        )

        return self._get_current_weights()

    def _update_weights_from_probs(self, probs: Dict[str, float]) -> None:
        """Update system weights from Thompson probabilities."""
        for name, prob in probs.items():
            if name not in self._systems:
                continue

            state = self._systems[name]
            if not state.is_active:
                continue

            # Blend current weight with Thompson probability
            target = prob
            state.weight = (1 - self.adaptation_rate) * state.weight + self.adaptation_rate * target

            # Enforce bounds
            state.weight = max(self.min_weight, min(self.max_weight, state.weight))

    def reactivate_system(self, name: str) -> None:
        """Manually reactivate a deactivated system."""
        if name in self._systems:
            self._systems[name].is_active = True
            self._systems[name].cumulative_pnl = 0.0  # Reset
            self._rebuild_ensemble()
            logger.info(f"Reactivated system '{name}'")

    def get_status(self) -> Dict:
        """Get current portfolio status."""
        active = [s for s in self._systems.values() if s.is_active]
        inactive = [s for s in self._systems.values() if not s.is_active]

        return {
            "total_pnl": self._total_pnl,
            "peak_equity": self._peak_equity,
            "drawdown": (self._peak_equity - self._total_pnl) / max(1, self._peak_equity),
            "active_systems": len(active),
            "inactive_systems": len(inactive),
            "weights": self._get_current_weights(),
            "system_details": {
                name: {
                    "weight": state.weight,
                    "cumulative_pnl": state.cumulative_pnl,
                    "n_updates": state.n_updates,
                    "is_active": state.is_active,
                    "recent_sharpe": self._calculate_sharpe(state.recent_pnl),
                }
                for name, state in self._systems.items()
            },
        }

    def _calculate_sharpe(self, pnls: List[float], risk_free: float = 0.0) -> float:
        """Calculate Sharpe ratio from PnL series."""
        if len(pnls) < 2:
            return 0.0

        mean = sum(pnls) / len(pnls)
        variance = sum((p - mean) ** 2 for p in pnls) / len(pnls)

        # Return 0 if variance is 0 (undefined Sharpe - neutral value)
        if variance == 0:
            return 0.0

        std = math.sqrt(variance)
        return (mean - risk_free) / std

    def save_state(self, path: Path) -> None:
        """Save portfolio state to file."""
        state = {
            "total_pnl": self._total_pnl,
            "peak_equity": self._peak_equity,
            "systems": {
                name: {
                    "weight": s.weight,
                    "cumulative_pnl": s.cumulative_pnl,
                    "n_updates": s.n_updates,
                    "is_active": s.is_active,
                }
                for name, s in self._systems.items()
            },
        }

        with open(path, "w") as f:
            json.dump(state, f, indent=2)

    def load_state(self, path: Path) -> None:
        """Load portfolio state from file."""
        with open(path) as f:
            state = json.load(f)

        self._total_pnl = state["total_pnl"]
        self._peak_equity = state["peak_equity"]

        for name, data in state["systems"].items():
            if name in self._systems:
                self._systems[name].weight = data["weight"]
                self._systems[name].cumulative_pnl = data["cumulative_pnl"]
                self._systems[name].n_updates = data["n_updates"]
                self._systems[name].is_active = data["is_active"]

        self._rebuild_ensemble()


def create_meta_portfolio_from_backtest(
    backtest_results: List[BacktestResult],
    top_k: int = 3,
    base_size: float = 1000.0,
) -> MetaPortfolio:
    """
    Create a MetaPortfolio from backtest results.

    Args:
        backtest_results: List of BacktestResult from BacktestMatrix
        top_k: Number of top systems to include
        base_size: Base position size

    Returns:
        Configured MetaPortfolio
    """
    # Sort by Sharpe
    sorted_results = sorted(
        backtest_results,
        key=lambda r: r.sharpe_ratio,
        reverse=True,
    )

    # Take top K
    selected = sorted_results[:top_k]

    # Create portfolio
    portfolio = MetaPortfolio(base_size=base_size)

    # Calculate initial weights based on Sharpe
    total_sharpe = sum(r.sharpe_ratio for r in selected if r.sharpe_ratio > 0)

    for result in selected:
        if total_sharpe > 0:
            weight = max(0.1, result.sharpe_ratio / total_sharpe)
        else:
            weight = 1.0 / len(selected)

        portfolio.register_system(result.config.name, initial_weight=weight)

    return portfolio
