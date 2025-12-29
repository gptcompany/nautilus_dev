"""Walk-forward validator implementation."""

import logging
import time
from datetime import timedelta
from typing import Protocol

from scripts.alpha_evolve.walk_forward.config import WalkForwardConfig
from scripts.alpha_evolve.walk_forward.metrics import (
    calculate_deflated_sharpe_ratio,
    calculate_robustness_score,
    estimate_probability_backtest_overfitting,
)
from scripts.alpha_evolve.walk_forward.models import (
    WalkForwardResult,
    Window,
    WindowMetrics,
    WindowResult,
)


logger = logging.getLogger(__name__)


class StrategyEvaluator(Protocol):
    """Protocol for strategy evaluation dependency."""

    async def evaluate(
        self,
        strategy_code: str,
        start_date: ...,
        end_date: ...,
        **kwargs,
    ) -> WindowMetrics:
        """Evaluate strategy on a date range and return metrics."""
        ...


class WalkForwardValidator:
    """Validates strategies using walk-forward analysis.

    Walk-forward validation tests strategies on out-of-sample data using
    rolling windows to prevent overfitting and ensure robustness.

    Attributes:
        config: Validation configuration.
        evaluator: Strategy evaluator dependency.

    Example:
        >>> config = WalkForwardConfig(
        ...     data_start=datetime(2023, 1, 1),
        ...     data_end=datetime(2024, 12, 1),
        ... )
        >>> validator = WalkForwardValidator(config, evaluator)
        >>> result = await validator.validate(strategy_code)
        >>> print(f"Passed: {result.passed}")
    """

    def __init__(self, config: WalkForwardConfig, evaluator: StrategyEvaluator) -> None:
        """Initialize validator with configuration and evaluator.

        Args:
            config: Walk-forward validation configuration.
            evaluator: Strategy evaluator for running backtests.
        """
        self.config = config
        self.evaluator = evaluator

    async def validate(self, strategy_code: str) -> WalkForwardResult:
        """Run walk-forward validation on strategy.

        Args:
            strategy_code: Strategy source code to validate.

        Returns:
            WalkForwardResult with all metrics and pass/fail status.
        """
        start_time = time.time()

        # Generate windows
        windows = self._generate_windows()
        logger.info(f"Generated {len(windows)} walk-forward windows")

        if len(windows) < self.config.min_windows:
            logger.warning(
                f"Insufficient windows: {len(windows)} < {self.config.min_windows}"
            )

        # Evaluate each window
        window_results: list[WindowResult] = []
        for window in windows:
            logger.debug(f"Evaluating window {window.window_id}")

            # Train period evaluation
            train_metrics = await self.evaluator.evaluate(
                strategy_code,
                start_date=window.train_start,
                end_date=window.train_end,
            )

            # Test period evaluation (out-of-sample)
            test_metrics = await self.evaluator.evaluate(
                strategy_code,
                start_date=window.test_start,
                end_date=window.test_end,
            )

            window_results.append(
                WindowResult(
                    window=window,
                    train_metrics=train_metrics,
                    test_metrics=test_metrics,
                )
            )

        # Calculate robustness score
        robustness_score = calculate_robustness_score(window_results)

        # Calculate advanced metrics
        avg_sharpe = (
            sum(w.test_metrics.sharpe_ratio for w in window_results)
            / len(window_results)
            if window_results
            else 0.0
        )
        deflated_sharpe = calculate_deflated_sharpe_ratio(
            sharpe=avg_sharpe,
            n_trials=len(window_results),
        )
        pbo = estimate_probability_backtest_overfitting(
            window_results, seed=self.config.seed
        )

        # Check pass/fail criteria
        passed = self._check_criteria(window_results, robustness_score)

        validation_time = time.time() - start_time

        return WalkForwardResult(
            config=self.config,
            windows=window_results,
            robustness_score=robustness_score,
            passed=passed,
            deflated_sharpe_ratio=deflated_sharpe,
            probability_backtest_overfitting=pbo,
            validation_time_seconds=validation_time,
        )

    def _generate_windows(self) -> list[Window]:
        """Generate walk-forward windows from config.

        Uses rolling (sliding) windows per plan.md Decision 1.
        Applies embargo periods per plan.md Decision 4.

        Embargo periods (Lopez de Prado PKCV):
            - embargo_before_days: Gap between train_end and test_start to prevent
              lagging indicators from leaking future test data into training.
            - embargo_after_days: Gap after test_end before next training window
              can start, preventing test period contamination of subsequent training.

        Returns:
            List of Window objects with train/test date ranges.
        """
        windows: list[Window] = []
        current_start = self.config.data_start
        window_id = 1  # 1-indexed for user-facing IDs

        # Calculate durations
        train_delta = timedelta(days=self.config.train_months * 30)
        test_delta = timedelta(days=self.config.test_months * 30)
        step_delta = timedelta(days=self.config.step_months * 30)
        embargo_before = timedelta(days=self.config.embargo_before_days)
        embargo_after = timedelta(days=self.config.embargo_after_days)

        while True:
            train_end = current_start + train_delta
            test_start = train_end + embargo_before
            test_end = test_start + test_delta

            # Check if window fits within data range
            if test_end > self.config.data_end:
                break

            windows.append(
                Window(
                    window_id=window_id,
                    train_start=current_start,
                    train_end=train_end,
                    test_start=test_start,
                    test_end=test_end,
                )
            )

            # Move to next window by step size
            # Note: embargo_after ensures gap between prev test_end and next train_start
            # This prevents training on data that was recently tested
            next_start = current_start + step_delta

            # If next training window would start before prev test_end + embargo,
            # delay the start to respect the embargo
            min_next_start = test_end + embargo_after
            if next_start < min_next_start:
                next_start = min_next_start

            current_start = next_start
            window_id += 1

        return windows

    def _check_criteria(
        self,
        window_results: list[WindowResult],
        robustness_score: float,
    ) -> bool:
        """Check if validation passed all criteria.

        Per spec.md FR-005:
        - Robustness Score >= min_robustness_score
        - At least min_profitable_windows_pct of windows profitable
        - Test Sharpe >= min_test_sharpe in majority of windows
        - No window with drawdown > max_drawdown_threshold

        Args:
            window_results: Results from all windows.
            robustness_score: Calculated robustness score.

        Returns:
            True if all criteria passed, False otherwise.
        """
        if not window_results:
            return False

        # Criterion 0: Minimum window count
        if len(window_results) < self.config.min_windows:
            logger.debug(
                f"Failed: insufficient windows {len(window_results)} < {self.config.min_windows}"
            )
            return False

        # Criterion 1: Robustness score threshold
        if robustness_score < self.config.min_robustness_score:
            logger.debug(
                f"Failed: robustness {robustness_score:.1f} < {self.config.min_robustness_score}"
            )
            return False

        # Criterion 2: Profitable windows percentage
        profitable = sum(1 for w in window_results if w.test_metrics.total_return > 0)
        profitable_pct = profitable / len(window_results)
        if profitable_pct < self.config.min_profitable_windows_pct:
            logger.debug(
                f"Failed: profitable {profitable_pct:.1%} < {self.config.min_profitable_windows_pct:.1%}"
            )
            return False

        # Criterion 3: Max drawdown threshold
        for w in window_results:
            if w.test_metrics.max_drawdown > self.config.max_drawdown_threshold:
                logger.debug(
                    f"Failed: window {w.window.window_id} drawdown "
                    f"{w.test_metrics.max_drawdown:.1%} > {self.config.max_drawdown_threshold:.1%}"
                )
                return False

        # Criterion 4: Majority with adequate Sharpe (more than 50%)
        sharpe_ok = sum(
            1
            for w in window_results
            if w.test_metrics.sharpe_ratio >= self.config.min_test_sharpe
        )
        # Use float division to correctly handle odd window counts
        if sharpe_ok <= len(window_results) / 2:
            logger.debug(
                f"Failed: only {sharpe_ok}/{len(window_results)} windows have "
                f"Sharpe >= {self.config.min_test_sharpe}"
            )
            return False

        return True
