"""Test fixtures for baseline validation tests.

Provides:
    - Sample WindowResult objects
    - Mock strategy configurations
    - Test data generators
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from scripts.alpha_evolve.walk_forward.models import (
        Window,
        WindowResult,
    )


@pytest.fixture
def sample_window() -> "Window":
    """Create a sample Window for testing."""
    from scripts.alpha_evolve.walk_forward.models import Window

    return Window(
        window_id=1,
        train_start=datetime(2023, 1, 1),
        train_end=datetime(2023, 6, 30),
        test_start=datetime(2023, 7, 5),
        test_end=datetime(2023, 7, 31),
    )


@pytest.fixture
def profitable_window_result() -> "WindowResult":
    """Create a profitable WindowResult for testing."""
    from scripts.alpha_evolve.walk_forward.models import (
        Window,
        WindowMetrics,
        WindowResult,
    )

    window = Window(
        window_id=1,
        train_start=datetime(2023, 1, 1),
        train_end=datetime(2023, 6, 30),
        test_start=datetime(2023, 7, 5),
        test_end=datetime(2023, 7, 31),
    )

    train_metrics = WindowMetrics(
        sharpe_ratio=1.5,
        calmar_ratio=2.0,
        max_drawdown=0.15,
        total_return=0.25,
        win_rate=0.55,
        trade_count=50,
    )

    test_metrics = WindowMetrics(
        sharpe_ratio=1.2,
        calmar_ratio=1.5,
        max_drawdown=0.18,
        total_return=0.12,
        win_rate=0.52,
        trade_count=25,
    )

    return WindowResult(
        window=window,
        train_metrics=train_metrics,
        test_metrics=test_metrics,
    )


@pytest.fixture
def unprofitable_window_result() -> "WindowResult":
    """Create an unprofitable WindowResult for testing."""
    from scripts.alpha_evolve.walk_forward.models import (
        Window,
        WindowMetrics,
        WindowResult,
    )

    window = Window(
        window_id=2,
        train_start=datetime(2023, 7, 1),
        train_end=datetime(2023, 12, 31),
        test_start=datetime(2024, 1, 5),
        test_end=datetime(2024, 1, 31),
    )

    train_metrics = WindowMetrics(
        sharpe_ratio=1.8,
        calmar_ratio=2.5,
        max_drawdown=0.12,
        total_return=0.30,
        win_rate=0.60,
        trade_count=45,
    )

    test_metrics = WindowMetrics(
        sharpe_ratio=-0.3,
        calmar_ratio=-0.5,
        max_drawdown=0.25,
        total_return=-0.08,
        win_rate=0.42,
        trade_count=20,
    )

    return WindowResult(
        window=window,
        train_metrics=train_metrics,
        test_metrics=test_metrics,
    )


@pytest.fixture
def sample_window_results(
    profitable_window_result: "WindowResult",
    unprofitable_window_result: "WindowResult",
) -> list["WindowResult"]:
    """Create a list of sample WindowResults."""
    return [profitable_window_result, unprofitable_window_result]


@pytest.fixture
def multiple_profitable_windows() -> list["WindowResult"]:
    """Create multiple profitable WindowResults for testing."""
    from scripts.alpha_evolve.walk_forward.models import (
        Window,
        WindowMetrics,
        WindowResult,
    )

    results = []
    base_date = datetime(2023, 1, 1)

    for i in range(12):
        window = Window(
            window_id=i + 1,
            train_start=base_date + timedelta(days=30 * i),
            train_end=base_date + timedelta(days=30 * i + 180),
            test_start=base_date + timedelta(days=30 * i + 185),
            test_end=base_date + timedelta(days=30 * i + 210),
        )

        # Simulate varying but mostly profitable results
        train_sharpe = 1.5 + (i % 3) * 0.2
        test_sharpe = train_sharpe * (0.7 + (i % 5) * 0.1)

        train_metrics = WindowMetrics(
            sharpe_ratio=train_sharpe,
            calmar_ratio=train_sharpe * 1.2,
            max_drawdown=0.10 + (i % 4) * 0.02,
            total_return=0.15 + (i % 5) * 0.03,
            win_rate=0.52 + (i % 3) * 0.02,
            trade_count=40 + i * 2,
        )

        test_metrics = WindowMetrics(
            sharpe_ratio=test_sharpe,
            calmar_ratio=test_sharpe * 1.1,
            max_drawdown=0.12 + (i % 4) * 0.03,
            total_return=0.08 + (i % 5) * 0.02,
            win_rate=0.50 + (i % 3) * 0.02,
            trade_count=20 + i,
        )

        results.append(
            WindowResult(
                window=window,
                train_metrics=train_metrics,
                test_metrics=test_metrics,
            )
        )

    return results


@pytest.fixture
def sample_returns() -> list[float]:
    """Generate sample return sequence for sizer testing."""
    import random

    random.seed(42)
    return [random.gauss(0.001, 0.02) for _ in range(100)]


@pytest.fixture
def sample_signals() -> list[float]:
    """Generate sample signal sequence for sizer testing."""
    import random

    random.seed(42)
    return [random.gauss(0, 1) for _ in range(100)]
