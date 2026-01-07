"""Tests for window generation in walk-forward validation."""

from datetime import datetime


from scripts.alpha_evolve.walk_forward.config import WalkForwardConfig
from scripts.alpha_evolve.walk_forward.validator import WalkForwardValidator


class MockEvaluator:
    """Mock evaluator for testing window generation only."""

    async def evaluate(self, *args, **kwargs):
        pass


class TestWindowGeneration:
    """Test window generation algorithm."""

    def test_24_month_data_window_count(self) -> None:
        """Test 24-month data with 6-month train, 3-month test.

        With embargo_after=0, windows can overlap in training periods,
        but next window starts after previous test ends (no data leakage).

        24 months with 9-month windows stepping after test_end yields ~2 windows.
        """
        config = WalkForwardConfig(
            data_start=datetime(2023, 1, 1),
            data_end=datetime(2024, 12, 1),
            train_months=6,
            test_months=3,
            step_months=3,
            embargo_before_days=0,
            embargo_after_days=0,
            min_windows=2,
        )
        validator = WalkForwardValidator(config, MockEvaluator())
        windows = validator._generate_windows()

        # With embargo_after preventing overlap of train with prev test,
        # we get fewer windows than with naive overlapping
        assert len(windows) >= 2, f"Expected at least 2 windows, got {len(windows)}"

    def test_window_ids_are_sequential(self) -> None:
        """Verify window IDs are sequential starting from 1."""
        config = WalkForwardConfig(
            data_start=datetime(2023, 1, 1),
            data_end=datetime(2024, 12, 1),
            train_months=6,
            test_months=3,
            step_months=3,
            embargo_before_days=0,
            embargo_after_days=0,
            min_windows=4,
        )
        validator = WalkForwardValidator(config, MockEvaluator())
        windows = validator._generate_windows()

        for i, window in enumerate(windows):
            assert window.window_id == i + 1, f"Expected window_id {i + 1}, got {window.window_id}"

    def test_embargo_period_applied(self) -> None:
        """Test embargo_before_days creates gap between train_end and test_start."""
        config = WalkForwardConfig(
            data_start=datetime(2023, 1, 1),
            data_end=datetime(2024, 12, 1),
            train_months=6,
            test_months=3,
            step_months=3,
            embargo_before_days=5,
            embargo_after_days=3,
            min_windows=4,
        )
        validator = WalkForwardValidator(config, MockEvaluator())
        windows = validator._generate_windows()

        for window in windows:
            gap_days = (window.test_start - window.train_end).days
            assert gap_days == 5, f"Expected 5-day gap, got {gap_days} days"

    def test_window_boundaries_dont_overlap_test_periods(self) -> None:
        """Verify test periods don't overlap between consecutive windows."""
        config = WalkForwardConfig(
            data_start=datetime(2023, 1, 1),
            data_end=datetime(2024, 12, 1),
            train_months=6,
            test_months=3,
            step_months=3,
            embargo_before_days=5,
            embargo_after_days=0,
            min_windows=4,
        )
        validator = WalkForwardValidator(config, MockEvaluator())
        windows = validator._generate_windows()

        for i in range(len(windows) - 1):
            current_test_end = windows[i].test_end
            next_test_start = windows[i + 1].test_start

            # Test periods should not overlap (next test can start same day current ends)
            assert next_test_start >= current_test_end, (
                f"Window {i + 1} test_end ({current_test_end}) overlaps with "
                f"Window {i + 2} test_start ({next_test_start})"
            )

    def test_insufficient_data_produces_fewer_windows(self) -> None:
        """Test that insufficient data produces fewer windows."""
        # Only enough for 2 windows
        config = WalkForwardConfig(
            data_start=datetime(2023, 1, 1),
            data_end=datetime(2023, 12, 31),
            train_months=3,
            test_months=2,
            step_months=2,
            embargo_before_days=0,
            embargo_after_days=0,
            min_windows=2,
        )
        validator = WalkForwardValidator(config, MockEvaluator())
        windows = validator._generate_windows()

        # Should still generate windows even if less than ideal
        assert len(windows) >= 2

    def test_train_end_before_test_start(self) -> None:
        """Verify train_end is always <= test_start."""
        config = WalkForwardConfig(
            data_start=datetime(2023, 1, 1),
            data_end=datetime(2024, 12, 1),
            train_months=6,
            test_months=3,
            step_months=3,
            embargo_before_days=5,
            embargo_after_days=3,
            min_windows=4,
        )
        validator = WalkForwardValidator(config, MockEvaluator())
        windows = validator._generate_windows()

        for window in windows:
            assert window.train_end <= window.test_start, (
                f"Window {window.window_id}: train_end ({window.train_end}) "
                f"should be <= test_start ({window.test_start})"
            )

    def test_all_windows_within_data_range(self) -> None:
        """Verify all windows are within the configured data range."""
        config = WalkForwardConfig(
            data_start=datetime(2023, 1, 1),
            data_end=datetime(2024, 12, 1),
            train_months=6,
            test_months=3,
            step_months=3,
            embargo_before_days=5,
            embargo_after_days=3,
            min_windows=4,
        )
        validator = WalkForwardValidator(config, MockEvaluator())
        windows = validator._generate_windows()

        for window in windows:
            assert window.train_start >= config.data_start, (
                f"Window {window.window_id} train_start before data_start"
            )
            assert window.test_end <= config.data_end, (
                f"Window {window.window_id} test_end after data_end"
            )


class TestWindowProperties:
    """Test Window dataclass properties."""

    def test_train_days_calculation(self) -> None:
        """Test train_days property."""
        config = WalkForwardConfig(
            data_start=datetime(2023, 1, 1),
            data_end=datetime(2024, 12, 1),
            train_months=6,
            test_months=3,
            step_months=3,
            embargo_before_days=0,
            embargo_after_days=0,
            min_windows=4,
        )
        validator = WalkForwardValidator(config, MockEvaluator())
        windows = validator._generate_windows()

        window = windows[0]
        expected_train_days = 6 * 30  # 180 days
        assert window.train_days == expected_train_days

    def test_test_days_calculation(self) -> None:
        """Test test_days property."""
        config = WalkForwardConfig(
            data_start=datetime(2023, 1, 1),
            data_end=datetime(2024, 12, 1),
            train_months=6,
            test_months=3,
            step_months=3,
            embargo_before_days=0,
            embargo_after_days=0,
            min_windows=4,
        )
        validator = WalkForwardValidator(config, MockEvaluator())
        windows = validator._generate_windows()

        window = windows[0]
        expected_test_days = 3 * 30  # 90 days
        assert window.test_days == expected_test_days

    def test_embargo_days_calculation(self) -> None:
        """Test embargo_days property."""
        config = WalkForwardConfig(
            data_start=datetime(2023, 1, 1),
            data_end=datetime(2024, 12, 1),
            train_months=6,
            test_months=3,
            step_months=3,
            embargo_before_days=5,
            embargo_after_days=3,
            min_windows=4,
        )
        validator = WalkForwardValidator(config, MockEvaluator())
        windows = validator._generate_windows()

        window = windows[0]
        assert window.embargo_days == 5
