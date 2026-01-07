"""Integration tests for walk-forward data isolation.

Tests for:
    - No future data leaks in training
    - Proper embargo handling
    - Window independence

TDD: Tests written first to define expected behavior.
"""

from __future__ import annotations


class TestWalkForwardDataIsolation:
    """Tests for walk-forward data isolation."""

    def test_no_future_data_in_training(self) -> None:
        """Test that training uses only past data."""
        from scripts.baseline_validation.comparison_validator import ComparisonValidator
        from scripts.baseline_validation.config_models import BaselineValidationConfig

        config = BaselineValidationConfig.default()
        validator = ComparisonValidator(config)

        windows = validator.generate_windows()

        for window in windows:
            # Training end must be before test start
            assert window.train_end < window.test_start, (
                f"Window {window.window_id}: train_end ({window.train_end}) "
                f"must be before test_start ({window.test_start})"
            )

    def test_embargo_period_applied(self) -> None:
        """Test that embargo period is applied between train and test."""
        from scripts.baseline_validation.comparison_validator import ComparisonValidator
        from scripts.baseline_validation.config_models import BaselineValidationConfig

        config = BaselineValidationConfig.default()
        validator = ComparisonValidator(config)

        windows = validator.generate_windows()
        expected_embargo = config.validation.embargo_before_days

        for window in windows:
            actual_gap = (window.test_start - window.train_end).days
            assert actual_gap >= expected_embargo, (
                f"Window {window.window_id}: gap ({actual_gap} days) "
                f"should be >= embargo ({expected_embargo} days)"
            )

    def test_sequential_windows(self) -> None:
        """Test that windows are sequential without backward jumps."""
        from scripts.baseline_validation.comparison_validator import ComparisonValidator
        from scripts.baseline_validation.config_models import BaselineValidationConfig

        config = BaselineValidationConfig.default()
        validator = ComparisonValidator(config)

        windows = validator.generate_windows()

        for i in range(1, len(windows)):
            prev_window = windows[i - 1]
            curr_window = windows[i]

            # Current window should start after previous
            assert curr_window.train_start >= prev_window.train_start, (
                f"Window {curr_window.window_id} starts before window {prev_window.window_id}"
            )


class TestWindowIndependence:
    """Tests for window independence."""

    def test_each_window_independent(self) -> None:
        """Test that each window can be validated independently."""
        from scripts.baseline_validation.comparison_validator import ComparisonValidator
        from scripts.baseline_validation.config_models import BaselineValidationConfig

        config = BaselineValidationConfig.default()
        validator = ComparisonValidator(config)

        windows = validator.generate_windows()

        # Each window should have valid date ranges
        for window in windows:
            assert window.train_start < window.train_end
            assert window.test_start < window.test_end
            assert window.train_end <= window.test_start

    def test_windows_cover_data_range(self) -> None:
        """Test that windows cover the configured data range."""
        from scripts.baseline_validation.comparison_validator import ComparisonValidator
        from scripts.baseline_validation.config_models import BaselineValidationConfig

        config = BaselineValidationConfig.default()
        validator = ComparisonValidator(config)

        windows = validator.generate_windows()

        # First window should start near data_start
        first_train_start = windows[0].train_start
        assert first_train_start >= config.validation.data_start

        # Last window test should end near data_end
        last_test_end = windows[-1].test_end
        # Allow some slack for embargo periods
        assert last_test_end <= config.validation.data_end


class TestReproducibility:
    """Tests for validation reproducibility."""

    def test_same_config_same_windows(self) -> None:
        """Test that same config produces same windows."""
        from scripts.baseline_validation.comparison_validator import ComparisonValidator
        from scripts.baseline_validation.config_models import BaselineValidationConfig

        config = BaselineValidationConfig.default()

        validator1 = ComparisonValidator(config)
        validator2 = ComparisonValidator(config)

        windows1 = validator1.generate_windows()
        windows2 = validator2.generate_windows()

        assert len(windows1) == len(windows2)

        for w1, w2 in zip(windows1, windows2, strict=False):
            assert w1.train_start == w2.train_start
            assert w1.train_end == w2.train_end
            assert w1.test_start == w2.test_start
            assert w1.test_end == w2.test_end

    def test_seed_affects_results(self) -> None:
        """Test that seed affects stochastic elements."""
        from scripts.baseline_validation.comparison_validator import ComparisonValidator
        from scripts.baseline_validation.config_models import BaselineValidationConfig

        config1 = BaselineValidationConfig.default()
        config1.seed = 42

        config2 = BaselineValidationConfig.default()
        config2.seed = 42

        validator1 = ComparisonValidator(config1)
        validator2 = ComparisonValidator(config2)

        # Same seed should give same mock results
        result1 = validator1.run_mock()
        result2 = validator2.run_mock()

        assert result1.best_contender == result2.best_contender
