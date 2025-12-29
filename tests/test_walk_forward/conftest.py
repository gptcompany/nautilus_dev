"""Pytest fixtures for walk-forward validation tests."""

from datetime import datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock

import pytest

from scripts.alpha_evolve.walk_forward.config import WalkForwardConfig
from scripts.alpha_evolve.walk_forward.models import (
    Window,
    WindowMetrics,
    WindowResult,
)


@pytest.fixture
def sample_config() -> WalkForwardConfig:
    """Sample WalkForwardConfig for testing."""
    return WalkForwardConfig(
        data_start=datetime(2023, 1, 1),
        data_end=datetime(2024, 12, 1),
        train_months=6,
        test_months=3,
        step_months=3,
        embargo_before_days=5,
        embargo_after_days=3,
        min_windows=4,
        min_profitable_windows_pct=0.75,
        min_test_sharpe=0.5,
        max_drawdown_threshold=0.30,
        min_robustness_score=60.0,
        seed=42,
    )


@pytest.fixture
def minimal_config() -> WalkForwardConfig:
    """Minimal WalkForwardConfig for quick tests."""
    return WalkForwardConfig(
        data_start=datetime(2023, 1, 1),
        data_end=datetime(2023, 12, 31),
        train_months=3,
        test_months=2,
        step_months=2,
        min_windows=2,
    )


@pytest.fixture
def sample_window() -> Window:
    """Sample Window for testing."""
    return Window(
        window_id=1,
        train_start=datetime(2023, 1, 1),
        train_end=datetime(2023, 6, 30),
        test_start=datetime(2023, 7, 5),  # 5-day embargo
        test_end=datetime(2023, 9, 30),
    )


@pytest.fixture
def profitable_metrics() -> WindowMetrics:
    """WindowMetrics representing profitable performance."""
    return WindowMetrics(
        sharpe_ratio=1.2,
        calmar_ratio=2.5,
        max_drawdown=0.08,
        total_return=0.15,
        win_rate=0.58,
        trade_count=45,
    )


@pytest.fixture
def losing_metrics() -> WindowMetrics:
    """WindowMetrics representing losing performance."""
    return WindowMetrics(
        sharpe_ratio=-0.3,
        calmar_ratio=-0.5,
        max_drawdown=0.25,
        total_return=-0.10,
        win_rate=0.38,
        trade_count=42,
    )


@pytest.fixture
def degraded_metrics() -> WindowMetrics:
    """WindowMetrics with moderate degradation from train."""
    return WindowMetrics(
        sharpe_ratio=0.65,
        calmar_ratio=1.2,
        max_drawdown=0.12,
        total_return=0.05,
        win_rate=0.52,
        trade_count=38,
    )


@pytest.fixture
def sample_window_result(
    sample_window: Window,
    profitable_metrics: WindowMetrics,
    degraded_metrics: WindowMetrics,
) -> WindowResult:
    """Sample WindowResult with typical train/test degradation."""
    return WindowResult(
        window=sample_window,
        train_metrics=profitable_metrics,
        test_metrics=degraded_metrics,
    )


@pytest.fixture
def multiple_windows() -> list[Window]:
    """Generate 5 windows for testing."""
    windows = []
    for i in range(5):
        base = datetime(2023, 1, 1) + timedelta(days=90 * i)
        windows.append(
            Window(
                window_id=i + 1,
                train_start=base,
                train_end=base + timedelta(days=180),
                test_start=base + timedelta(days=185),  # 5-day gap
                test_end=base + timedelta(days=275),
            )
        )
    return windows


@pytest.fixture
def mock_evaluator() -> AsyncMock:
    """Mock StrategyEvaluator for testing."""
    evaluator = AsyncMock()

    # Define predictable returns based on date range
    async def mock_evaluate(
        strategy_code: str,
        start_date: datetime,
        end_date: datetime,
        **kwargs: Any,
    ) -> WindowMetrics:
        """Return predictable metrics based on period."""
        # Training periods get higher metrics
        is_train = (end_date - start_date).days > 150

        if is_train:
            return WindowMetrics(
                sharpe_ratio=1.3,
                calmar_ratio=2.2,
                max_drawdown=0.10,
                total_return=0.12,
                win_rate=0.55,
                trade_count=50,
            )
        else:
            # Test periods show typical degradation
            return WindowMetrics(
                sharpe_ratio=0.75,
                calmar_ratio=1.5,
                max_drawdown=0.15,
                total_return=0.06,
                win_rate=0.51,
                trade_count=35,
            )

    evaluator.evaluate = mock_evaluate
    return evaluator


@pytest.fixture
def failing_evaluator() -> AsyncMock:
    """Mock evaluator that returns poor metrics."""
    evaluator = AsyncMock()

    async def mock_evaluate(
        strategy_code: str,
        start_date: datetime,
        end_date: datetime,
        **kwargs: Any,
    ) -> WindowMetrics:
        """Return poor metrics indicating overfitting."""
        is_train = (end_date - start_date).days > 150

        if is_train:
            return WindowMetrics(
                sharpe_ratio=2.5,  # Unrealistically high train
                calmar_ratio=5.0,
                max_drawdown=0.05,
                total_return=0.30,
                win_rate=0.70,
                trade_count=60,
            )
        else:
            return WindowMetrics(
                sharpe_ratio=0.2,  # Severe degradation
                calmar_ratio=0.3,
                max_drawdown=0.35,  # Exceeds threshold
                total_return=-0.05,  # Loss
                win_rate=0.40,
                trade_count=25,
            )

    evaluator.evaluate = mock_evaluate
    return evaluator
