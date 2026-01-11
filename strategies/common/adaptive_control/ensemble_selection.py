"""
Ensemble Strategy Selection (MVP - ROI 7.5)

Selects a portfolio of uncorrelated strategies instead of relying on a single best.

This reduces tail risk because:
- P1 (Probabilistic): Diversification reduces variance
- P2 (Non-linear): Protects against regime-specific tail events
- P4 (Scale-invariant): Ensemble is robust across timeframes

The key insight is that correlation-based selection is better than
fitness-based selection alone, because:
- Top 5 strategies by Sharpe may all be correlated (same edge, same risk)
- Uncorrelated strategies with lower Sharpe may provide better risk-adjusted portfolio

Reference:
- Lopez de Prado (2018): Ch. 16 "Combinatorial Purged Cross-Validation"
- Markowitz (1952): "Portfolio Selection"
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class SelectedStrategy:
    """A strategy selected for the ensemble."""

    name: str
    sharpe: float
    max_correlation: float  # Max correlation with other selected strategies
    weight: float


@dataclass
class EnsembleResult:
    """Result of ensemble selection."""

    strategies: list[SelectedStrategy]
    portfolio_sharpe: float  # Estimated portfolio Sharpe
    diversification_ratio: float  # Sum(individual Sharpe) / Portfolio Sharpe
    correlation_matrix: np.ndarray


def select_ensemble(
    strategy_names: list[str],
    strategy_sharpes: list[float],
    correlation_matrix: np.ndarray,
    n_select: int = 5,
    max_correlation: float = 0.3,
    min_sharpe: float = 0.0,
) -> EnsembleResult:
    """
    Select an ensemble of uncorrelated strategies.

    Algorithm:
    1. Sort strategies by Sharpe ratio (descending)
    2. Select the best strategy
    3. For each remaining strategy (by Sharpe):
       - Check max correlation with all selected strategies
       - If below threshold, add to ensemble
    4. Stop when n_select reached

    Args:
        strategy_names: List of strategy names
        strategy_sharpes: List of corresponding Sharpe ratios
        correlation_matrix: NxN correlation matrix of strategy returns
        n_select: Maximum strategies to select (default 5)
        max_correlation: Maximum pairwise correlation allowed (default 0.3)
        min_sharpe: Minimum Sharpe to consider (default 0.0)

    Returns:
        EnsembleResult with selected strategies and metrics

    Example:
        >>> names = ["strat_a", "strat_b", "strat_c", "strat_d"]
        >>> sharpes = [2.0, 1.8, 1.5, 1.2]
        >>> corr = np.array([
        ...     [1.0, 0.8, 0.1, 0.2],
        ...     [0.8, 1.0, 0.2, 0.1],
        ...     [0.1, 0.2, 1.0, 0.3],
        ...     [0.2, 0.1, 0.3, 1.0]
        ... ])
        >>> result = select_ensemble(names, sharpes, corr, n_select=3, max_correlation=0.3)
        >>> # Will select: strat_a (best), strat_c (low corr with a), strat_d (low corr with a,c)
        >>> # Will NOT select strat_b (high corr with strat_a)
    """
    if len(strategy_names) != len(strategy_sharpes):
        raise ValueError("strategy_names and strategy_sharpes must have same length")

    if correlation_matrix.shape[0] != len(strategy_names):
        raise ValueError("correlation_matrix dimensions must match strategy count")

    # Create indexed list sorted by Sharpe (descending)
    indexed = list(enumerate(zip(strategy_names, strategy_sharpes)))
    indexed.sort(key=lambda x: x[1][1], reverse=True)

    # Filter by minimum Sharpe
    indexed = [(i, (n, s)) for i, (n, s) in indexed if s >= min_sharpe]

    if not indexed:
        return EnsembleResult(
            strategies=[],
            portfolio_sharpe=0.0,
            diversification_ratio=0.0,
            correlation_matrix=correlation_matrix,
        )

    # Greedy selection
    selected_indices: list[int] = []
    selected_strategies: list[SelectedStrategy] = []

    for orig_idx, (name, sharpe) in indexed:
        if len(selected_strategies) >= n_select:
            break

        # Check correlation with all already selected
        if selected_indices:
            correlations = [
                abs(correlation_matrix[orig_idx, sel_idx]) for sel_idx in selected_indices
            ]
            max_corr = max(correlations)

            if max_corr > max_correlation:
                continue  # Skip this strategy, too correlated
        else:
            max_corr = 0.0

        # Add to ensemble
        selected_indices.append(orig_idx)
        selected_strategies.append(
            SelectedStrategy(
                name=name,
                sharpe=sharpe,
                max_correlation=max_corr,
                weight=1.0 / n_select,  # Equal weight initially
            )
        )

    if not selected_strategies:
        return EnsembleResult(
            strategies=[],
            portfolio_sharpe=0.0,
            diversification_ratio=0.0,
            correlation_matrix=correlation_matrix,
        )

    # Calculate portfolio metrics
    n = len(selected_strategies)

    # Equal weights
    weights = np.ones(n) / n

    # Update weights in results
    for i, strat in enumerate(selected_strategies):
        strat.weight = weights[i]

    # Extract sub-correlation matrix for selected strategies
    sub_corr = correlation_matrix[np.ix_(selected_indices, selected_indices)]

    # Estimate portfolio Sharpe (simplified: assuming equal volatility)
    # Portfolio variance = w'Cw where C is correlation matrix (assuming equal vol)
    portfolio_variance = weights @ sub_corr @ weights
    portfolio_vol = np.sqrt(portfolio_variance)

    # Portfolio Sharpe = weighted avg Sharpe / portfolio vol factor
    weighted_sharpe = sum(s.sharpe * s.weight for s in selected_strategies)
    portfolio_sharpe = weighted_sharpe / portfolio_vol if portfolio_vol > 0 else weighted_sharpe

    # Diversification ratio
    sum_individual = sum(s.sharpe for s in selected_strategies)
    diversification_ratio = sum_individual / portfolio_sharpe if portfolio_sharpe > 0 else 1.0

    return EnsembleResult(
        strategies=selected_strategies,
        portfolio_sharpe=portfolio_sharpe,
        diversification_ratio=diversification_ratio,
        correlation_matrix=sub_corr,
    )


def calculate_returns_correlation(
    returns_dict: dict[str, list[float]],
) -> tuple[list[str], np.ndarray]:
    """
    Calculate correlation matrix from strategy returns.

    Args:
        returns_dict: Dictionary mapping strategy name to list of returns

    Returns:
        Tuple of (strategy names, correlation matrix)

    Example:
        >>> returns = {
        ...     "strat_a": [0.01, -0.02, 0.03],
        ...     "strat_b": [0.02, -0.01, 0.02],
        ... }
        >>> names, corr = calculate_returns_correlation(returns)
    """
    names = list(returns_dict.keys())
    n = len(names)

    if n == 0:
        return [], np.array([])

    # Convert to numpy array
    min_len = min(len(r) for r in returns_dict.values())
    returns_matrix = np.array([returns_dict[name][:min_len] for name in names])

    # Calculate correlation matrix
    if min_len < 2:
        return names, np.eye(n)

    corr_matrix = np.corrcoef(returns_matrix)

    # Handle NaN (e.g., zero variance strategies)
    corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)

    return names, corr_matrix


class EnsembleSelector:
    """
    Stateful ensemble selector with history tracking.

    Tracks selected ensembles over time and provides stability metrics.

    Usage:
        selector = EnsembleSelector(max_correlation=0.3, n_select=5)

        # Register strategies
        selector.register("strat_a", sharpe=2.0, returns=[...])
        selector.register("strat_b", sharpe=1.5, returns=[...])

        # Select ensemble
        result = selector.select()
        print(f"Selected: {[s.name for s in result.strategies]}")

        # Check stability over time
        new_result = selector.select()  # After more data
        stability = selector.get_stability()
    """

    def __init__(
        self,
        n_select: int = 5,
        max_correlation: float = 0.3,
        min_sharpe: float = 0.0,
    ):
        self.n_select = n_select
        self.max_correlation = max_correlation
        self.min_sharpe = min_sharpe

        self._strategies: dict[str, dict] = {}  # name -> {sharpe, returns}
        self._selection_history: list[list[str]] = []

    def register(
        self,
        name: str,
        sharpe: float,
        returns: list[float],
    ) -> None:
        """Register or update a strategy."""
        self._strategies[name] = {"sharpe": sharpe, "returns": returns}

    def unregister(self, name: str) -> None:
        """Remove a strategy."""
        self._strategies.pop(name, None)

    def select(self) -> EnsembleResult:
        """Select ensemble from registered strategies."""
        if len(self._strategies) < 2:
            # Not enough strategies
            if self._strategies:
                name, data = next(iter(self._strategies.items()))
                return EnsembleResult(
                    strategies=[
                        SelectedStrategy(
                            name=name,
                            sharpe=data["sharpe"],
                            max_correlation=0.0,
                            weight=1.0,
                        )
                    ],
                    portfolio_sharpe=data["sharpe"],
                    diversification_ratio=1.0,
                    correlation_matrix=np.array([[1.0]]),
                )
            return EnsembleResult(
                strategies=[],
                portfolio_sharpe=0.0,
                diversification_ratio=0.0,
                correlation_matrix=np.array([]),
            )

        # Build inputs
        names = list(self._strategies.keys())
        sharpes = [self._strategies[n]["sharpe"] for n in names]
        returns_dict = {n: self._strategies[n]["returns"] for n in names}

        _, corr_matrix = calculate_returns_correlation(returns_dict)

        result = select_ensemble(
            strategy_names=names,
            strategy_sharpes=sharpes,
            correlation_matrix=corr_matrix,
            n_select=self.n_select,
            max_correlation=self.max_correlation,
            min_sharpe=self.min_sharpe,
        )

        # Track selection history
        selected_names = [s.name for s in result.strategies]
        self._selection_history.append(selected_names)

        return result

    def get_stability(self, window: int = 5) -> float:
        """
        Calculate selection stability over recent selections.

        Returns:
            Jaccard similarity between recent selections (0 to 1)
            1.0 = perfectly stable (same strategies selected each time)
            0.0 = completely unstable (different strategies each time)
        """
        if len(self._selection_history) < 2:
            return 1.0  # Not enough history

        recent = self._selection_history[-window:]
        if len(recent) < 2:
            return 1.0

        # Calculate average pairwise Jaccard similarity
        similarities = []
        for i in range(len(recent) - 1):
            set_a = set(recent[i])
            set_b = set(recent[i + 1])

            if not set_a and not set_b:
                similarities.append(1.0)
            elif not set_a or not set_b:
                similarities.append(0.0)
            else:
                jaccard = len(set_a & set_b) / len(set_a | set_b)
                similarities.append(jaccard)

        return sum(similarities) / len(similarities) if similarities else 1.0
