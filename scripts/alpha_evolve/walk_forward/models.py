"""Data models for walk-forward validation."""

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scripts.alpha_evolve.walk_forward.config import WalkForwardConfig


@dataclass(frozen=True)
class Window:
    """A single train/test window in the walk-forward sequence.

    Attributes:
        window_id: Sequential window identifier (1-indexed).
        train_start: Training period start date.
        train_end: Training period end date.
        test_start: Test period start date (after embargo).
        test_end: Test period end date.

    Constraints:
        - train_start < train_end
        - train_end <= test_start (embargo period between)
        - test_start < test_end
    """

    window_id: int
    train_start: datetime
    train_end: datetime
    test_start: datetime
    test_end: datetime

    def __post_init__(self) -> None:
        """Validate window constraints."""
        if self.train_start >= self.train_end:
            raise ValueError(
                f"train_start ({self.train_start}) must be before train_end ({self.train_end})"
            )
        if self.train_end > self.test_start:
            raise ValueError(
                f"train_end ({self.train_end}) must be before or equal to test_start ({self.test_start})"
            )
        if self.test_start >= self.test_end:
            raise ValueError(
                f"test_start ({self.test_start}) must be before test_end ({self.test_end})"
            )

    @property
    def train_days(self) -> int:
        """Number of days in training period."""
        return (self.train_end - self.train_start).days

    @property
    def test_days(self) -> int:
        """Number of days in test period."""
        return (self.test_end - self.test_start).days

    @property
    def embargo_days(self) -> int:
        """Number of days between train_end and test_start."""
        return (self.test_start - self.train_end).days


@dataclass(frozen=True)
class WindowMetrics:
    """Performance metrics for a single window.

    Attributes:
        sharpe_ratio: Risk-adjusted return (annualized).
        calmar_ratio: Return / Max Drawdown.
        max_drawdown: Maximum peak-to-trough decline (0-1).
        total_return: Total percentage return (e.g., 0.15 = 15%).
        win_rate: Percentage of winning trades (0-1).
        trade_count: Number of trades executed.
    """

    sharpe_ratio: float
    calmar_ratio: float
    max_drawdown: float
    total_return: float
    win_rate: float
    trade_count: int


@dataclass(frozen=True)
class WindowResult:
    """Combined result for a window including train and test metrics.

    Attributes:
        window: Window definition with date ranges.
        train_metrics: Training period performance metrics.
        test_metrics: Test period performance metrics (out-of-sample).

    Properties:
        degradation_ratio: test_sharpe / train_sharpe (lower = more overfitting).
    """

    window: Window
    train_metrics: WindowMetrics
    test_metrics: WindowMetrics

    @property
    def degradation_ratio(self) -> float:
        """Calculate test/train sharpe ratio.

        Returns:
            Ratio of test to train Sharpe. Values < 1.0 indicate degradation.
            Returns 1.0 if train_sharpe is <= 0 to avoid division issues.
        """
        if self.train_metrics.sharpe_ratio <= 0:
            return 1.0
        return self.test_metrics.sharpe_ratio / self.train_metrics.sharpe_ratio


@dataclass
class WalkForwardResult:
    """Complete result of walk-forward validation.

    Attributes:
        config: Configuration used for validation.
        windows: Results for each window.
        robustness_score: Overall robustness score (0-100).
        passed: Whether validation passed all criteria.
        deflated_sharpe_ratio: Sharpe adjusted for multiple testing (Lopez de Prado Ch. 14).
        probability_backtest_overfitting: PBO estimate (Lopez de Prado Ch. 11).
        validation_time_seconds: Time taken to run validation.
    """

    config: "WalkForwardConfig"
    windows: list[WindowResult]
    robustness_score: float
    passed: bool
    deflated_sharpe_ratio: float | None = None
    probability_backtest_overfitting: float | None = None
    validation_time_seconds: float = 0.0

    @property
    def profitable_windows_pct(self) -> float:
        """Percentage of windows with positive test return."""
        if not self.windows:
            return 0.0
        profitable = sum(1 for w in self.windows if w.test_metrics.total_return > 0)
        return profitable / len(self.windows)

    @property
    def avg_test_sharpe(self) -> float:
        """Average Sharpe ratio across test periods."""
        if not self.windows:
            return 0.0
        return sum(w.test_metrics.sharpe_ratio for w in self.windows) / len(self.windows)

    @property
    def avg_test_return(self) -> float:
        """Average return across test periods."""
        if not self.windows:
            return 0.0
        return sum(w.test_metrics.total_return for w in self.windows) / len(self.windows)

    @property
    def worst_drawdown(self) -> float:
        """Worst drawdown across all test windows."""
        if not self.windows:
            return 0.0
        return max(w.test_metrics.max_drawdown for w in self.windows)

    @property
    def avg_degradation(self) -> float:
        """Average degradation ratio across windows."""
        if not self.windows:
            return 0.0
        return sum(w.degradation_ratio for w in self.windows) / len(self.windows)
