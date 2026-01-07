"""
API Contract: Hall-of-Fame Store

This module defines the public interface for the strategy persistence layer.
Implementation should match these signatures exactly.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class FitnessMetrics:
    """Strategy performance measurements."""

    sharpe_ratio: float
    calmar_ratio: float
    max_drawdown: float
    cagr: float
    total_return: float
    trade_count: int | None = None
    win_rate: float | None = None


@dataclass
class Program:
    """Evolved strategy with code, metrics, and lineage."""

    id: str
    code: str
    parent_id: str | None
    generation: int
    experiment: str | None
    metrics: FitnessMetrics | None
    created_at: float


class ProgramStore:
    """
    Persistence layer for evolved strategies.

    Stores strategies with their fitness metrics and lineage information.
    Supports parent selection algorithms and population management.
    """

    def __init__(
        self,
        db_path: Path | str,
        *,
        population_size: int = 500,
        archive_size: int = 50,
    ) -> None:
        """
        Initialize store.

        Args:
            db_path: Path to SQLite database file
            population_size: Maximum population size (triggers pruning)
            archive_size: Number of top performers protected from pruning
        """
        ...

    def insert(
        self,
        code: str,
        metrics: FitnessMetrics | None = None,
        parent_id: str | None = None,
        experiment: str | None = None,
    ) -> str:
        """
        Insert a new strategy.

        Args:
            code: Strategy Python code
            metrics: Performance metrics (None if not yet evaluated)
            parent_id: ID of parent strategy (None for seeds)
            experiment: Experiment name for grouping

        Returns:
            Generated UUID for the strategy

        Note:
            Automatically triggers pruning if population exceeds limit.
        """
        ...

    def update_metrics(self, prog_id: str, metrics: FitnessMetrics) -> None:
        """
        Update metrics for an existing strategy.

        Args:
            prog_id: Strategy ID
            metrics: Performance metrics from evaluation

        Raises:
            KeyError: If strategy not found
        """
        ...

    def get(self, prog_id: str) -> Program | None:
        """
        Get strategy by ID.

        Args:
            prog_id: Strategy ID

        Returns:
            Program if found, None otherwise
        """
        ...

    def top_k(
        self,
        k: int = 10,
        metric: str = "calmar",
        experiment: str | None = None,
    ) -> list[Program]:
        """
        Get top k strategies by fitness metric.

        Args:
            k: Number of strategies to return
            metric: Metric to sort by (calmar, sharpe, cagr)
            experiment: Filter by experiment name (None for all)

        Returns:
            List of top k programs, sorted descending by metric
        """
        ...

    def sample(
        self,
        strategy: str = "exploit",
        experiment: str | None = None,
    ) -> Program | None:
        """
        Sample a parent strategy for mutation.

        Args:
            strategy: Selection strategy
                - "elite": Random from top 10%
                - "exploit": Fitness-weighted random
                - "explore": Uniform random
            experiment: Filter by experiment name

        Returns:
            Selected program, or None if store is empty
        """
        ...

    def get_lineage(self, prog_id: str) -> list[Program]:
        """
        Get full lineage chain from strategy to seed.

        Args:
            prog_id: Strategy ID

        Returns:
            List of programs from given ID to root seed
        """
        ...

    def count(self, experiment: str | None = None) -> int:
        """
        Count strategies in store.

        Args:
            experiment: Filter by experiment name

        Returns:
            Number of strategies
        """
        ...

    def prune(self) -> int:
        """
        Remove excess strategies to maintain population limit.

        Protects top archive_size performers from deletion.

        Returns:
            Number of strategies deleted
        """
        ...
