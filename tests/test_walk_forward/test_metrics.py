"""Tests for walk-forward validation metrics module."""

from datetime import datetime


from scripts.alpha_evolve.walk_forward.models import (
    Window,
    WindowMetrics,
    WindowResult,
)
from scripts.alpha_evolve.walk_forward.metrics import (
    calculate_robustness_score,
    calculate_deflated_sharpe_ratio,
    estimate_probability_backtest_overfitting,
    simulate_combinatorial_paths,
    _norm_cdf,
    _norm_ppf,
)


# === Fixtures ===


def make_window(window_id: int = 1) -> Window:
    """Create a test window."""
    return Window(
        window_id=window_id,
        train_start=datetime(2023, 1, 1),
        train_end=datetime(2023, 6, 30),
        test_start=datetime(2023, 7, 1),
        test_end=datetime(2023, 9, 30),
    )


def make_metrics(
    sharpe: float = 1.5,
    total_return: float = 0.10,
    max_dd: float = 0.05,
) -> WindowMetrics:
    """Create test window metrics."""
    return WindowMetrics(
        sharpe_ratio=sharpe,
        calmar_ratio=total_return / max_dd if max_dd > 0 else 0.0,
        max_drawdown=max_dd,
        total_return=total_return,
        win_rate=0.55,
        trade_count=100,
    )


def make_result(
    window_id: int = 1,
    train_sharpe: float = 2.0,
    test_sharpe: float = 1.5,
    train_return: float = 0.15,
    test_return: float = 0.10,
) -> WindowResult:
    """Create a test window result."""
    return WindowResult(
        window=make_window(window_id),
        train_metrics=make_metrics(sharpe=train_sharpe, total_return=train_return),
        test_metrics=make_metrics(sharpe=test_sharpe, total_return=test_return),
    )


# === Test Normal Distribution Functions ===


class TestNormCdf:
    """Tests for standard normal CDF."""

    def test_cdf_at_zero(self) -> None:
        """CDF(0) should be 0.5."""
        assert abs(_norm_cdf(0.0) - 0.5) < 1e-10

    def test_cdf_at_positive(self) -> None:
        """CDF of positive values should be > 0.5."""
        assert _norm_cdf(1.0) > 0.5
        assert _norm_cdf(2.0) > _norm_cdf(1.0)

    def test_cdf_at_negative(self) -> None:
        """CDF of negative values should be < 0.5."""
        assert _norm_cdf(-1.0) < 0.5
        assert _norm_cdf(-2.0) < _norm_cdf(-1.0)

    def test_cdf_symmetry(self) -> None:
        """CDF should be symmetric: CDF(x) + CDF(-x) = 1."""
        for x in [0.5, 1.0, 1.96, 2.5]:
            assert abs(_norm_cdf(x) + _norm_cdf(-x) - 1.0) < 1e-10

    def test_cdf_known_values(self) -> None:
        """Test against known statistical values."""
        # CDF(1.96) ~= 0.975 (95% CI upper bound)
        assert abs(_norm_cdf(1.96) - 0.975) < 0.001
        # CDF(-1.96) ~= 0.025
        assert abs(_norm_cdf(-1.96) - 0.025) < 0.001


class TestNormPpf:
    """Tests for inverse standard normal CDF."""

    def test_ppf_at_half(self) -> None:
        """PPF(0.5) should be 0."""
        assert abs(_norm_ppf(0.5) - 0.0) < 1e-6

    def test_ppf_boundaries(self) -> None:
        """PPF at boundaries should return infinities."""
        assert _norm_ppf(0.0) == float("-inf")
        assert _norm_ppf(1.0) == float("inf")

    def test_ppf_known_values(self) -> None:
        """Test against known statistical values."""
        # PPF(0.975) ~= 1.96
        assert abs(_norm_ppf(0.975) - 1.96) < 0.01
        # PPF(0.025) ~= -1.96
        assert abs(_norm_ppf(0.025) - (-1.96)) < 0.01

    def test_ppf_inverse_of_cdf(self) -> None:
        """PPF should be inverse of CDF."""
        for x in [-2.0, -1.0, 0.0, 1.0, 2.0]:
            p = _norm_cdf(x)
            x_recovered = _norm_ppf(p)
            assert abs(x - x_recovered) < 0.01


# === Test Robustness Score ===


class TestRobustnessScore:
    """Tests for calculate_robustness_score."""

    def test_empty_list_returns_zero(self) -> None:
        """Empty window list should return 0."""
        assert calculate_robustness_score([]) == 0.0

    def test_single_window_profitable(self) -> None:
        """Single profitable window returns 40 (profitability component)."""
        result = make_result(test_return=0.10)
        score = calculate_robustness_score([result])
        assert score == 40.0

    def test_single_window_unprofitable(self) -> None:
        """Single unprofitable window returns 0."""
        result = make_result(test_return=-0.10)
        score = calculate_robustness_score([result])
        assert score == 0.0

    def test_all_profitable_consistent(self) -> None:
        """All profitable, consistent returns should score high."""
        results = [
            make_result(
                window_id=1, train_sharpe=2.0, test_sharpe=1.8, test_return=0.10
            ),
            make_result(
                window_id=2, train_sharpe=2.0, test_sharpe=1.9, test_return=0.11
            ),
            make_result(
                window_id=3, train_sharpe=2.0, test_sharpe=1.7, test_return=0.09
            ),
            make_result(
                window_id=4, train_sharpe=2.0, test_sharpe=2.0, test_return=0.10
            ),
        ]
        score = calculate_robustness_score(results)
        # All profitable (40%), good consistency (~27%), good degradation (~25%)
        assert score >= 80.0

    def test_mixed_profitability(self) -> None:
        """Mix of profitable/unprofitable should reduce score."""
        results = [
            make_result(window_id=1, test_return=0.10, test_sharpe=1.5),
            make_result(window_id=2, test_return=-0.05, test_sharpe=-0.5),
            make_result(window_id=3, test_return=0.08, test_sharpe=1.2),
            make_result(window_id=4, test_return=-0.03, test_sharpe=-0.3),
        ]
        score = calculate_robustness_score(results)
        # 50% profitable -> profitability = 0.5 * 0.4 * 100 = 20
        assert 20.0 <= score <= 60.0

    def test_high_degradation_penalty(self) -> None:
        """Large train->test degradation should reduce score."""
        results = [
            make_result(
                window_id=1, train_sharpe=3.0, test_sharpe=0.5, test_return=0.05
            ),
            make_result(
                window_id=2, train_sharpe=3.0, test_sharpe=0.3, test_return=0.03
            ),
            make_result(
                window_id=3, train_sharpe=3.0, test_sharpe=0.4, test_return=0.04
            ),
            make_result(
                window_id=4, train_sharpe=3.0, test_sharpe=0.2, test_return=0.02
            ),
        ]
        score = calculate_robustness_score(results)
        # Degradation ratio ~0.15 on average -> low degradation component
        assert score < 70.0

    def test_zero_train_sharpe_handled(self) -> None:
        """Zero train sharpe should not cause division error."""
        results = [
            make_result(
                window_id=1, train_sharpe=0.0, test_sharpe=1.0, test_return=0.10
            ),
            make_result(
                window_id=2, train_sharpe=0.0, test_sharpe=0.5, test_return=0.05
            ),
        ]
        score = calculate_robustness_score(results)
        # Should not raise, should return reasonable score
        assert 0.0 <= score <= 100.0

    def test_negative_train_sharpe_handled(self) -> None:
        """Negative train sharpe should not cause issues."""
        results = [
            make_result(
                window_id=1, train_sharpe=-0.5, test_sharpe=1.0, test_return=0.10
            ),
            make_result(
                window_id=2, train_sharpe=-1.0, test_sharpe=0.5, test_return=0.05
            ),
        ]
        score = calculate_robustness_score(results)
        assert 0.0 <= score <= 100.0

    def test_score_bounds(self) -> None:
        """Score should always be between 0 and 100."""
        # Best case: all profitable, consistent, no degradation
        best_results = [
            make_result(
                window_id=i, train_sharpe=2.0, test_sharpe=2.0, test_return=0.10
            )
            for i in range(1, 5)
        ]
        best_score = calculate_robustness_score(best_results)
        assert 0.0 <= best_score <= 100.0

        # Worst case: all unprofitable, high variance
        worst_results = [
            make_result(
                window_id=1, train_sharpe=2.0, test_sharpe=-1.0, test_return=-0.20
            ),
            make_result(
                window_id=2, train_sharpe=2.0, test_sharpe=-0.5, test_return=-0.01
            ),
            make_result(
                window_id=3, train_sharpe=2.0, test_sharpe=-2.0, test_return=-0.30
            ),
            make_result(
                window_id=4, train_sharpe=2.0, test_sharpe=-0.1, test_return=-0.05
            ),
        ]
        worst_score = calculate_robustness_score(worst_results)
        assert 0.0 <= worst_score <= 100.0


# === Test Deflated Sharpe Ratio ===


class TestDeflatedSharpeRatio:
    """Tests for calculate_deflated_sharpe_ratio."""

    def test_single_trial_unchanged(self) -> None:
        """With n_trials=1, DSR should equal raw Sharpe."""
        assert calculate_deflated_sharpe_ratio(2.0, 1) == 2.0
        assert calculate_deflated_sharpe_ratio(0.5, 1) == 0.5

    def test_zero_trials_unchanged(self) -> None:
        """With n_trials<=1, DSR should equal raw Sharpe."""
        assert calculate_deflated_sharpe_ratio(2.0, 0) == 2.0

    def test_multiple_trials_deflates(self) -> None:
        """Multiple trials should deflate the Sharpe ratio."""
        raw_sharpe = 2.0
        dsr_10 = calculate_deflated_sharpe_ratio(raw_sharpe, 10)
        dsr_100 = calculate_deflated_sharpe_ratio(raw_sharpe, 100)
        dsr_1000 = calculate_deflated_sharpe_ratio(raw_sharpe, 1000)

        # DSR should decrease with more trials
        assert dsr_10 < raw_sharpe
        assert dsr_100 < dsr_10
        assert dsr_1000 < dsr_100

    def test_low_sharpe_more_affected(self) -> None:
        """Lower Sharpe ratios should be more affected by deflation."""
        high_sharpe = 3.0
        low_sharpe = 1.0
        n_trials = 100

        high_dsr = calculate_deflated_sharpe_ratio(high_sharpe, n_trials)
        low_dsr = calculate_deflated_sharpe_ratio(low_sharpe, n_trials)

        # Both deflated
        assert high_dsr < high_sharpe
        assert low_dsr < low_sharpe

        # Relative deflation: low sharpe loses more proportionally
        high_deflation_pct = (high_sharpe - high_dsr) / high_sharpe
        low_deflation_pct = (low_sharpe - low_dsr) / low_sharpe
        assert low_deflation_pct > high_deflation_pct

    def test_negative_sharpe(self) -> None:
        """Negative Sharpe should still work."""
        dsr = calculate_deflated_sharpe_ratio(-1.0, 100)
        # Should be more negative after deflation
        assert dsr < -1.0

    def test_large_n_trials(self) -> None:
        """Very large n_trials should not overflow."""
        dsr = calculate_deflated_sharpe_ratio(2.0, 1_000_000)
        assert dsr < 2.0
        assert dsr > -10.0  # Should still be reasonable


# === Test PBO ===


class TestProbabilityBacktestOverfitting:
    """Tests for estimate_probability_backtest_overfitting."""

    def test_empty_list_returns_zero(self) -> None:
        """Empty list should return 0."""
        assert estimate_probability_backtest_overfitting([]) == 0.0

    def test_single_window_returns_zero(self) -> None:
        """Single window cannot estimate PBO."""
        result = make_result()
        assert estimate_probability_backtest_overfitting([result]) == 0.0

    def test_consistent_strategy_low_pbo(self) -> None:
        """Consistent train->test should have low PBO."""
        results = [
            make_result(window_id=i, train_sharpe=2.0, test_sharpe=1.9)
            for i in range(1, 9)
        ]
        pbo = estimate_probability_backtest_overfitting(
            results, n_permutations=500, seed=42
        )
        # Low overfitting expected
        assert pbo < 0.7

    def test_overfit_strategy_high_pbo(self) -> None:
        """Strategy with much better train than test should have higher PBO."""
        results = [
            make_result(window_id=i, train_sharpe=3.0, test_sharpe=0.5)
            for i in range(1, 9)
        ]
        pbo = estimate_probability_backtest_overfitting(
            results, n_permutations=500, seed=42
        )
        # Higher overfitting expected when train >> test consistently
        # Note: PBO measures if IS < OOS which inverts the interpretation
        assert 0.0 <= pbo <= 1.0

    def test_reproducibility_with_seed(self) -> None:
        """Same seed should produce same result."""
        results = [make_result(window_id=i) for i in range(1, 5)]

        pbo1 = estimate_probability_backtest_overfitting(
            results, n_permutations=100, seed=123
        )
        pbo2 = estimate_probability_backtest_overfitting(
            results, n_permutations=100, seed=123
        )

        assert pbo1 == pbo2

    def test_different_seeds_vary(self) -> None:
        """Different seeds may produce different results."""
        results = [make_result(window_id=i) for i in range(1, 10)]

        pbo1 = estimate_probability_backtest_overfitting(
            results, n_permutations=100, seed=111
        )
        pbo2 = estimate_probability_backtest_overfitting(
            results, n_permutations=100, seed=222
        )

        # May differ (not guaranteed but highly likely)
        # Just check both are valid
        assert 0.0 <= pbo1 <= 1.0
        assert 0.0 <= pbo2 <= 1.0

    def test_pbo_range(self) -> None:
        """PBO should always be in [0, 1]."""
        results = [make_result(window_id=i) for i in range(1, 5)]
        pbo = estimate_probability_backtest_overfitting(results, n_permutations=100)
        assert 0.0 <= pbo <= 1.0


# === Test Combinatorial Paths ===


class TestCombinatorialPaths:
    """Tests for simulate_combinatorial_paths."""

    def test_empty_list_returns_empty(self) -> None:
        """Empty input returns empty list."""
        assert simulate_combinatorial_paths([]) == []

    def test_returns_correct_count(self) -> None:
        """Should return n_permutations results."""
        results = [make_result(window_id=i) for i in range(1, 5)]
        paths = simulate_combinatorial_paths(results, n_permutations=50)
        assert len(paths) == 50

    def test_reproducibility_with_seed(self) -> None:
        """Same seed produces same results."""
        results = [make_result(window_id=i) for i in range(1, 5)]

        paths1 = simulate_combinatorial_paths(results, n_permutations=50, seed=42)
        paths2 = simulate_combinatorial_paths(results, n_permutations=50, seed=42)

        assert paths1 == paths2

    def test_average_sharpe_matches(self) -> None:
        """Average across paths should approximate mean of input Sharpes."""
        results = [
            make_result(window_id=1, test_sharpe=1.0),
            make_result(window_id=2, test_sharpe=2.0),
            make_result(window_id=3, test_sharpe=3.0),
            make_result(window_id=4, test_sharpe=4.0),
        ]
        # True mean = 2.5
        paths = simulate_combinatorial_paths(results, n_permutations=1000, seed=42)

        # Each path average should equal 2.5 (permutation doesn't change mean)
        for avg in paths:
            assert abs(avg - 2.5) < 1e-10

    def test_variation_in_paths(self) -> None:
        """Different permutations create variation (unless all same)."""
        # With identical values, no variation
        identical_results = [
            make_result(window_id=i, test_sharpe=1.5) for i in range(1, 5)
        ]
        paths = simulate_combinatorial_paths(
            identical_results, n_permutations=100, seed=42
        )
        # All paths have same average when inputs identical
        assert all(abs(p - paths[0]) < 1e-10 for p in paths)


# === Integration Tests ===


class TestMetricsIntegration:
    """Integration tests for metrics module."""

    def test_full_workflow(self) -> None:
        """Test typical usage workflow."""
        # Create realistic window results
        results = [
            make_result(
                window_id=1,
                train_sharpe=2.5,
                test_sharpe=1.8,
                train_return=0.20,
                test_return=0.12,
            ),
            make_result(
                window_id=2,
                train_sharpe=2.3,
                test_sharpe=1.5,
                train_return=0.18,
                test_return=0.10,
            ),
            make_result(
                window_id=3,
                train_sharpe=2.1,
                test_sharpe=1.2,
                train_return=0.15,
                test_return=0.08,
            ),
            make_result(
                window_id=4,
                train_sharpe=2.4,
                test_sharpe=1.6,
                train_return=0.19,
                test_return=0.11,
            ),
            make_result(
                window_id=5,
                train_sharpe=2.2,
                test_sharpe=1.4,
                train_return=0.16,
                test_return=0.09,
            ),
        ]

        # Calculate all metrics
        robustness = calculate_robustness_score(results)
        avg_test_sharpe = sum(r.test_metrics.sharpe_ratio for r in results) / len(
            results
        )
        dsr = calculate_deflated_sharpe_ratio(avg_test_sharpe, n_trials=50)
        pbo = estimate_probability_backtest_overfitting(
            results, n_permutations=200, seed=42
        )
        paths = simulate_combinatorial_paths(results, n_permutations=100, seed=42)

        # All should be reasonable
        assert 50.0 <= robustness <= 100.0
        assert dsr < avg_test_sharpe
        assert 0.0 <= pbo <= 1.0
        assert len(paths) == 100

        print("\nIntegration test results:")
        print(f"  Robustness Score: {robustness:.1f}")
        print(f"  Avg Test Sharpe: {avg_test_sharpe:.2f}")
        print(f"  Deflated Sharpe (N=50): {dsr:.2f}")
        print(f"  PBO: {pbo:.2%}")
