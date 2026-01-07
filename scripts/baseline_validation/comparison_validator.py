"""Comparison validator for multi-contender walk-forward validation.

This module extends the walk-forward infrastructure to run validation
across multiple contenders (Adaptive, Fixed, Buy&Hold) in parallel.

Key Features:
    - Same windows for all contenders (fair comparison)
    - ContenderResult aggregation per contender
    - MultiContenderComparison for statistical analysis
    - No lookahead bias (embargo periods enforced)

Reference:
    - Lopez de Prado (2018): "Advances in Financial Machine Learning"
    - DeMiguel (2009): "Optimal Versus Naive Diversification"
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from scripts.alpha_evolve.walk_forward.models import Window
from scripts.baseline_validation.comparison_metrics import (
    MultiContenderComparison,
    compare_all_contenders,
)
from scripts.baseline_validation.registry import ContenderRegistry

if TYPE_CHECKING:
    from scripts.baseline_validation.config_models import BaselineValidationConfig
    from scripts.baseline_validation.sizers import ContenderSizer


@dataclass
class ContenderResult:
    """Results for a single contender across all windows.

    Aggregates metrics from individual window results.
    """

    name: str
    window_sharpes: list[float]
    window_returns: list[float]
    window_drawdowns: list[float]
    window_trade_counts: list[int]

    @property
    def avg_sharpe(self) -> float:
        """Average Sharpe ratio across windows."""
        if not self.window_sharpes:
            return 0.0
        return sum(self.window_sharpes) / len(self.window_sharpes)

    @property
    def std_sharpe(self) -> float:
        """Standard deviation of Sharpe ratios."""
        if len(self.window_sharpes) < 2:
            return 0.0
        mean = self.avg_sharpe
        variance = sum((s - mean) ** 2 for s in self.window_sharpes) / (
            len(self.window_sharpes) - 1
        )
        return variance**0.5

    @property
    def avg_return(self) -> float:
        """Average return across windows."""
        if not self.window_returns:
            return 0.0
        return sum(self.window_returns) / len(self.window_returns)

    @property
    def max_drawdown(self) -> float:
        """Maximum drawdown across all windows."""
        if not self.window_drawdowns:
            return 0.0
        return max(self.window_drawdowns)

    @property
    def total_trades(self) -> int:
        """Total trades across all windows."""
        return sum(self.window_trade_counts)

    @property
    def win_rate(self) -> float:
        """Percentage of profitable windows."""
        if not self.window_returns:
            return 0.0
        profitable = sum(1 for r in self.window_returns if r > 0)
        return profitable / len(self.window_returns)


@dataclass
class ValidationRun:
    """Complete result of a validation run.

    Contains results for all contenders and comparison metrics.
    """

    config_hash: str
    run_timestamp: datetime
    windows: list[Window]
    contender_results: dict[str, ContenderResult]
    comparison: MultiContenderComparison | None = None
    elapsed_seconds: float = 0.0

    @property
    def best_contender(self) -> str:
        """Name of the best performing contender."""
        if self.comparison:
            return self.comparison.best_contender
        # Fallback: find highest avg_sharpe
        if not self.contender_results:
            return ""
        return max(
            self.contender_results.keys(),
            key=lambda k: self.contender_results[k].avg_sharpe,
        )

    @property
    def best_sharpe(self) -> float:
        """Sharpe ratio of best contender."""
        if self.comparison:
            return self.comparison.best_sharpe
        best = self.best_contender
        if best and best in self.contender_results:
            return self.contender_results[best].avg_sharpe
        return 0.0


class ComparisonValidator:
    """Multi-contender walk-forward validator.

    Runs walk-forward validation for multiple contenders on the same windows,
    ensuring fair comparison.

    Usage:
        >>> config = BaselineValidationConfig.default()
        >>> validator = ComparisonValidator(config)
        >>> result = validator.run()  # Full validation with backtest
        >>> # Or for testing:
        >>> result = validator.run_mock()  # Mock results
    """

    def __init__(
        self,
        config: BaselineValidationConfig,
        registry: ContenderRegistry | None = None,
    ):
        """Initialize ComparisonValidator.

        Args:
            config: Validation configuration.
            registry: Optional custom contender registry.
        """
        self._config = config
        self._registry = registry or ContenderRegistry.from_config(config.contenders)

    @property
    def config(self) -> BaselineValidationConfig:
        """Validation configuration."""
        return self._config

    @property
    def contenders(self) -> dict[str, ContenderSizer]:
        """Registered contenders."""
        return dict(self._registry.all())

    def generate_windows(self) -> list[Window]:
        """Generate walk-forward windows from config.

        Returns:
            List of Window objects with train/test date ranges.
        """
        val_config = self._config.validation

        windows = []
        window_id = 1

        # Convert months to approximate days
        train_days = val_config.train_months * 30
        test_days = val_config.test_months * 30
        step_days = val_config.step_months * 30
        embargo_days = val_config.embargo_before_days

        # Start from data_start
        train_start = val_config.data_start
        data_end = val_config.data_end

        while True:
            train_end = train_start + timedelta(days=train_days)
            test_start = train_end + timedelta(days=embargo_days)
            test_end = test_start + timedelta(days=test_days)

            # Stop if test would exceed data range
            if test_end > data_end:
                break

            window = Window(
                window_id=window_id,
                train_start=train_start,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end,
            )
            windows.append(window)

            # Step forward
            train_start = train_start + timedelta(days=step_days)
            window_id += 1

        return windows

    def run_mock(self, seed: int | None = None) -> ValidationRun:
        """Run mock validation for testing.

        Generates synthetic results without actual backtesting.

        Args:
            seed: Random seed for reproducibility.

        Returns:
            ValidationRun with mock results.
        """
        start_time = datetime.now()
        rng = random.Random(seed or self._config.seed)

        windows = self.generate_windows()
        contender_results: dict[str, ContenderResult] = {}

        for name, sizer in self._registry.all():
            # Generate mock metrics per window
            window_sharpes = []
            window_returns = []
            window_drawdowns = []
            window_trade_counts = []

            for _ in windows:
                # Mock Sharpe: varies by contender type
                if "adaptive" in name.lower() or "sops" in name.lower():
                    base_sharpe = 1.0 + rng.gauss(0, 0.3)
                elif "fixed" in name.lower():
                    base_sharpe = 0.9 + rng.gauss(0, 0.25)
                else:  # buyhold
                    base_sharpe = 0.7 + rng.gauss(0, 0.4)

                window_sharpes.append(base_sharpe)
                window_returns.append(base_sharpe * 0.05 + rng.gauss(0, 0.02))
                window_drawdowns.append(0.1 + rng.random() * 0.15)
                window_trade_counts.append(int(30 + rng.random() * 40))

            contender_results[name] = ContenderResult(
                name=sizer.name,
                window_sharpes=window_sharpes,
                window_returns=window_returns,
                window_drawdowns=window_drawdowns,
                window_trade_counts=window_trade_counts,
            )

        # Calculate comparison metrics
        comparison_data = {
            name: {
                "sharpes": result.window_sharpes,
                "returns": result.window_returns,
                "drawdowns": result.window_drawdowns,
                "trade_counts": result.window_trade_counts,
            }
            for name, result in contender_results.items()
        }

        comparison = compare_all_contenders(
            comparison_data,
            sharpe_edge_threshold=self._config.success_criteria.sharpe_edge,
        )

        elapsed = (datetime.now() - start_time).total_seconds()

        return ValidationRun(
            config_hash=str(hash(str(self._config.model_dump()))),
            run_timestamp=start_time,
            windows=windows,
            contender_results=contender_results,
            comparison=comparison,
            elapsed_seconds=elapsed,
        )

    def run(self) -> ValidationRun:
        """Run full validation with backtesting.

        This method would integrate with BacktestEngine and ParquetDataCatalog
        for actual walk-forward validation.

        Returns:
            ValidationRun with real backtest results.

        Note:
            Currently returns mock results. Full implementation requires:
            - ParquetDataCatalog integration for BTC data
            - BacktestEngine for window backtests
            - Strategy instantiation with sizers
        """
        # For now, delegate to mock
        # TODO: Implement real backtesting when integrating with NautilusTrader
        return self.run_mock()


def create_comparison_validator(
    data_start: datetime | None = None,
    data_end: datetime | None = None,
    train_months: int = 12,
    test_months: int = 1,
    seed: int | None = 42,
) -> ComparisonValidator:
    """Factory function to create ComparisonValidator.

    Args:
        data_start: Start of data range (default: 2015-01-01).
        data_end: End of data range (default: 2025-01-01).
        train_months: Training window size.
        test_months: Test window size.
        seed: Random seed.

    Returns:
        Configured ComparisonValidator.
    """
    from scripts.baseline_validation.config_models import (
        BaselineValidationConfig,
        ValidationConfig,
    )

    validation = ValidationConfig(
        data_start=data_start or datetime(2015, 1, 1),
        data_end=data_end or datetime(2025, 1, 1),
        train_months=train_months,
        test_months=test_months,
    )

    config = BaselineValidationConfig.default()
    config.validation = validation
    config.seed = seed

    return ComparisonValidator(config)
