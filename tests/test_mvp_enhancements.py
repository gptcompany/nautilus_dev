"""
Unit tests for MVP Enhancements (ROI > 5)

Tests for:
1. Overfitting Detection (ROI 10.0)
2. Probabilistic Sharpe Ratio (ROI 7.5)
3. Ensemble Selection (ROI 7.5)
4. Transaction Cost Modeling (ROI 5.0)

These are the highest-ROI enhancements aligned with all 4 pillars.
"""

import numpy as np
import pytest

from strategies.common.adaptive_control import (
    BacktestCostAdjuster,
    CostProfile,
    EnsembleSelector,
    Exchange,
    OverfittingDetector,
    TransactionCostModel,
    calculate_returns_correlation,
    probabilistic_sharpe_ratio,
    select_ensemble,
)

# =============================================================================
# Test: Probabilistic Sharpe Ratio (007-FE-003, ROI 7.5)
# =============================================================================


class TestProbabilisticSharpeRatio:
    """Tests for probabilistic_sharpe_ratio function."""

    def test_insufficient_data_returns_uncertain(self):
        """PSR should return 0.5 (uncertain) with insufficient data."""
        returns = [0.01, 0.02, 0.03]  # Only 3 points
        psr = probabilistic_sharpe_ratio(returns)
        assert psr == 0.5

    def test_flat_returns_gives_neutral_psr(self):
        """Flat returns should give PSR near 0.5."""
        returns = [0.0] * 100
        psr = probabilistic_sharpe_ratio(returns)
        assert psr == 0.5  # No variance = uncertain

    def test_positive_returns_high_psr(self):
        """Consistently positive returns should give high PSR."""
        np.random.seed(42)
        returns = list(np.random.normal(0.001, 0.01, 252))  # Positive drift
        psr = probabilistic_sharpe_ratio(returns, benchmark_sr=0.0)
        assert psr > 0.5  # Should be confident SR > 0

    def test_negative_returns_low_psr(self):
        """Consistently negative returns should give low PSR."""
        np.random.seed(42)
        returns = list(np.random.normal(-0.001, 0.01, 252))  # Negative drift
        psr = probabilistic_sharpe_ratio(returns, benchmark_sr=0.0)
        assert psr < 0.5  # Should be unlikely SR > 0

    def test_high_benchmark_lowers_psr(self):
        """Higher benchmark SR should lower PSR."""
        np.random.seed(42)
        returns = list(np.random.normal(0.001, 0.01, 252))
        psr_low = probabilistic_sharpe_ratio(returns, benchmark_sr=0.5)
        psr_high = probabilistic_sharpe_ratio(returns, benchmark_sr=2.0)
        assert psr_low > psr_high

    def test_psr_bounded_0_to_1(self):
        """PSR should always be between 0 and 1."""
        np.random.seed(42)
        for _ in range(10):
            returns = list(np.random.normal(0, 0.02, 100))
            psr = probabilistic_sharpe_ratio(returns)
            assert 0.0 <= psr <= 1.0


# =============================================================================
# Test: Overfitting Detection (010-FE-005, ROI 10.0)
# =============================================================================


class TestOverfittingDetector:
    """Tests for OverfittingDetector class."""

    def test_no_overfit_healthy_ratio(self):
        """Healthy IS/OOS ratio should not trigger alert."""
        detector = OverfittingDetector()
        alert = detector.check(train_sharpe=1.5, test_sharpe=1.2)
        assert not alert.is_overfit
        assert alert.severity == "none"
        assert alert.ratio == pytest.approx(1.25, rel=0.01)

    def test_warning_threshold(self):
        """Ratio > 1.5 should trigger warning."""
        detector = OverfittingDetector(warning_threshold=1.5, critical_threshold=2.0)
        alert = detector.check(train_sharpe=2.4, test_sharpe=1.5)
        assert alert.is_overfit
        assert alert.severity == "warning"
        assert alert.ratio == pytest.approx(1.6, rel=0.01)

    def test_critical_threshold(self):
        """Ratio > 2.0 should trigger critical alert."""
        detector = OverfittingDetector(warning_threshold=1.5, critical_threshold=2.0)
        alert = detector.check(train_sharpe=3.0, test_sharpe=1.2)
        assert alert.is_overfit
        assert alert.severity == "critical"
        assert alert.ratio == pytest.approx(2.5, rel=0.01)

    def test_negative_oos_sharpe_critical(self):
        """Negative OOS Sharpe should always be critical overfit."""
        detector = OverfittingDetector()
        alert = detector.check(train_sharpe=2.0, test_sharpe=-0.5)
        assert alert.is_overfit
        assert alert.severity == "critical"

    def test_zero_oos_sharpe_critical(self):
        """Zero OOS Sharpe should be critical overfit."""
        detector = OverfittingDetector()
        alert = detector.check(train_sharpe=2.0, test_sharpe=0.0)
        assert alert.is_overfit
        assert alert.severity == "critical"

    def test_history_tracking(self):
        """Detector should track history for trend analysis."""
        detector = OverfittingDetector()
        for i in range(10):
            detector.check(train_sharpe=2.0, test_sharpe=1.5 - i * 0.1)
        assert len(detector._history) == 10

    def test_trend_detection_deteriorating(self):
        """Should detect deteriorating trend."""
        detector = OverfittingDetector()
        # Improving ratios first
        for _ in range(5):
            detector.check(train_sharpe=2.0, test_sharpe=1.8)
        # Then deteriorating
        for _ in range(5):
            detector.check(train_sharpe=2.0, test_sharpe=0.8)
        trend = detector.get_trend()
        assert trend == "deteriorating"

    def test_reset_clears_history(self):
        """Reset should clear history."""
        detector = OverfittingDetector()
        detector.check(train_sharpe=2.0, test_sharpe=1.5)
        detector.reset()
        assert len(detector._history) == 0


# =============================================================================
# Test: Ensemble Selection (009-FE-003, ROI 7.5)
# =============================================================================


class TestEnsembleSelection:
    """Tests for ensemble selection functions."""

    @pytest.fixture
    def sample_data(self):
        """Sample strategy data for testing."""
        names = ["strat_a", "strat_b", "strat_c", "strat_d"]
        sharpes = [2.0, 1.8, 1.5, 1.2]
        corr = np.array(
            [
                [1.0, 0.8, 0.1, 0.2],
                [0.8, 1.0, 0.2, 0.1],
                [0.1, 0.2, 1.0, 0.3],
                [0.2, 0.1, 0.3, 1.0],
            ]
        )
        return names, sharpes, corr

    def test_selects_best_first(self, sample_data):
        """Should select best Sharpe strategy first."""
        names, sharpes, corr = sample_data
        result = select_ensemble(names, sharpes, corr, n_select=1)
        assert len(result.strategies) == 1
        assert result.strategies[0].name == "strat_a"

    def test_skips_correlated_strategies(self, sample_data):
        """Should skip strategies highly correlated with selected ones."""
        names, sharpes, corr = sample_data
        result = select_ensemble(names, sharpes, corr, n_select=3, max_correlation=0.3)
        selected_names = [s.name for s in result.strategies]
        # strat_b should be skipped (0.8 corr with strat_a)
        assert "strat_b" not in selected_names
        assert "strat_a" in selected_names
        assert "strat_c" in selected_names

    def test_respects_n_select_limit(self, sample_data):
        """Should not select more than n_select strategies."""
        names, sharpes, corr = sample_data
        result = select_ensemble(names, sharpes, corr, n_select=2, max_correlation=1.0)
        assert len(result.strategies) <= 2

    def test_respects_min_sharpe(self, sample_data):
        """Should respect minimum Sharpe threshold."""
        names, sharpes, corr = sample_data
        result = select_ensemble(
            names, sharpes, corr, n_select=5, max_correlation=1.0, min_sharpe=1.6
        )
        for s in result.strategies:
            assert s.sharpe >= 1.6

    def test_portfolio_sharpe_calculation(self, sample_data):
        """Portfolio Sharpe should be calculated."""
        names, sharpes, corr = sample_data
        result = select_ensemble(names, sharpes, corr, n_select=3, max_correlation=0.5)
        assert result.portfolio_sharpe > 0

    def test_empty_input(self):
        """Should handle empty input gracefully."""
        result = select_ensemble([], [], np.array([]), n_select=5)
        assert len(result.strategies) == 0
        assert result.portfolio_sharpe == 0.0


class TestEnsembleSelector:
    """Tests for stateful EnsembleSelector class."""

    def test_register_and_select(self):
        """Should register strategies and select ensemble."""
        selector = EnsembleSelector(n_select=2, max_correlation=0.5)
        selector.register("strat_a", sharpe=2.0, returns=[0.01, -0.02, 0.03])
        selector.register("strat_b", sharpe=1.5, returns=[0.02, -0.01, 0.02])
        result = selector.select()
        assert len(result.strategies) <= 2

    def test_stability_tracking(self):
        """Should track selection stability over time."""
        selector = EnsembleSelector(n_select=2, max_correlation=1.0)
        selector.register("strat_a", sharpe=2.0, returns=[0.01] * 10)
        selector.register("strat_b", sharpe=1.5, returns=[0.02] * 10)

        # Select multiple times
        for _ in range(5):
            selector.select()

        stability = selector.get_stability()
        assert stability == 1.0  # Same selection each time


class TestCalculateReturnsCorrelation:
    """Tests for calculate_returns_correlation function."""

    def test_identical_returns_correlation_one(self):
        """Identical returns should have correlation 1.0."""
        returns_dict = {
            "strat_a": [0.01, 0.02, 0.03],
            "strat_b": [0.01, 0.02, 0.03],
        }
        names, corr = calculate_returns_correlation(returns_dict)
        assert corr[0, 1] == pytest.approx(1.0, rel=0.01)

    def test_opposite_returns_correlation_negative(self):
        """Opposite returns should have negative correlation."""
        returns_dict = {
            "strat_a": [0.01, 0.02, 0.03],
            "strat_b": [-0.01, -0.02, -0.03],
        }
        names, corr = calculate_returns_correlation(returns_dict)
        assert corr[0, 1] == pytest.approx(-1.0, rel=0.01)


# =============================================================================
# Test: Transaction Cost Modeling (007-FE-004, ROI 5.0)
# =============================================================================


class TestTransactionCostModel:
    """Tests for TransactionCostModel class."""

    def test_zero_notional_zero_cost(self):
        """Zero notional should have zero cost."""
        model = TransactionCostModel()
        cost = model.calculate(notional=0)
        assert cost.total == 0.0

    def test_cost_increases_with_size(self):
        """Cost should increase with trade size."""
        model = TransactionCostModel()
        cost_small = model.calculate(notional=1000)
        cost_large = model.calculate(notional=100000)
        assert cost_large.total > cost_small.total

    def test_slippage_scales_nonlinearly(self):
        """Slippage should scale with notional^1.5 (notional * sqrt(size)) - P2 power law."""
        model = TransactionCostModel()
        cost_1x = model.calculate(notional=10000)
        cost_4x = model.calculate(notional=40000)
        # Formula: notional * base_bps * (notional/ref)^0.5 = notional^1.5 scaling
        # So 4x notional = 4^1.5 = 8x slippage
        # This is correct P2 behavior: larger trades have disproportionately more impact
        expected_ratio = 4**1.5  # = 8
        actual_ratio = cost_4x.slippage / cost_1x.slippage
        assert actual_ratio == pytest.approx(expected_ratio, rel=0.01)

    def test_cost_increases_with_volatility(self):
        """Cost should increase with volatility."""
        model = TransactionCostModel()
        cost_low_vol = model.calculate(notional=10000, volatility=0.01)
        cost_high_vol = model.calculate(notional=10000, volatility=0.05)
        assert cost_high_vol.total > cost_low_vol.total

    def test_exchange_profiles_differ(self):
        """Different exchanges should have different costs."""
        binance = TransactionCostModel(exchange=Exchange.BINANCE_FUTURES)
        generic = TransactionCostModel(exchange=Exchange.GENERIC)
        cost_binance = binance.calculate(notional=10000)
        cost_generic = generic.calculate(notional=10000)
        # Generic is more conservative
        assert cost_generic.total > cost_binance.total

    def test_adjust_sharpe_reduces_gross(self):
        """Adjusted Sharpe should be less than gross Sharpe."""
        model = TransactionCostModel()
        net_sharpe = model.adjust_sharpe(gross_sharpe=2.0, avg_notional=10000, trades_per_year=500)
        assert net_sharpe < 2.0

    def test_more_trades_more_drag(self):
        """More trades per year should reduce net Sharpe more."""
        model = TransactionCostModel()
        net_100 = model.adjust_sharpe(gross_sharpe=2.0, avg_notional=10000, trades_per_year=100)
        net_1000 = model.adjust_sharpe(gross_sharpe=2.0, avg_notional=10000, trades_per_year=1000)
        assert net_1000 < net_100

    def test_breakeven_sharpe_positive(self):
        """Breakeven Sharpe should be positive."""
        model = TransactionCostModel()
        breakeven = model.get_breakeven_sharpe(avg_notional=10000, trades_per_year=500)
        assert breakeven > 0


class TestBacktestCostAdjuster:
    """Tests for BacktestCostAdjuster class."""

    def test_adjust_return_reduces_gross(self):
        """Adjusted return should be less than gross return."""
        adjuster = BacktestCostAdjuster()
        adjusted = adjuster.adjust_return(gross_return=0.02, notional=10000)
        assert adjusted < 0.02

    def test_batch_adjustment(self):
        """Batch adjustment should work correctly."""
        adjuster = BacktestCostAdjuster()
        gross = [0.02, -0.01, 0.03]
        notionals = [10000, 15000, 8000]
        adjusted = adjuster.adjust_returns_batch(gross, notionals)
        assert len(adjusted) == 3
        # All returns should be reduced by costs
        for g, a in zip(gross, adjusted, strict=True):
            assert a < g

    def test_annual_drag_positive(self):
        """Annual drag should be positive."""
        adjuster = BacktestCostAdjuster()
        drag = adjuster.estimate_annual_drag(avg_notional=10000, trades_per_year=500)
        assert drag > 0


class TestCostProfile:
    """Tests for CostProfile dataclass."""

    def test_invalid_size_exponent_raises(self):
        """Size exponent must be positive."""
        with pytest.raises(ValueError):
            CostProfile(
                name="invalid",
                commission_rate=0.001,
                spread_bps=1.0,
                slippage_base_bps=1.0,
                slippage_vol_sensitivity=1.0,
                slippage_size_exponent=0,  # Invalid
            )


# =============================================================================
# Integration Tests
# =============================================================================


class TestMVPIntegration:
    """Integration tests combining multiple MVPs."""

    def test_full_strategy_evaluation_pipeline(self):
        """Test full pipeline: returns -> PSR -> overfit check -> cost adjust."""
        # 1. Generate returns
        np.random.seed(42)
        is_returns = list(np.random.normal(0.002, 0.02, 252))
        oos_returns = list(np.random.normal(0.001, 0.02, 252))

        # 2. Calculate PSR
        is_psr = probabilistic_sharpe_ratio(is_returns, benchmark_sr=1.0)
        oos_psr = probabilistic_sharpe_ratio(oos_returns, benchmark_sr=1.0)
        assert 0 <= is_psr <= 1
        assert 0 <= oos_psr <= 1

        # 3. Check overfitting
        detector = OverfittingDetector()
        # Calculate Sharpes manually
        is_sharpe = (np.mean(is_returns) / np.std(is_returns)) * np.sqrt(252)
        oos_sharpe = (np.mean(oos_returns) / np.std(oos_returns)) * np.sqrt(252)
        alert = detector.check(train_sharpe=is_sharpe, test_sharpe=oos_sharpe)

        # 4. Adjust for costs
        model = TransactionCostModel(exchange=Exchange.BINANCE_FUTURES)
        net_sharpe = model.adjust_sharpe(
            gross_sharpe=oos_sharpe,
            avg_notional=10000,
            trades_per_year=500,
        )
        assert net_sharpe < oos_sharpe

    def test_ensemble_with_cost_adjustment(self):
        """Test ensemble selection with cost-adjusted Sharpes."""
        # Create strategies with different characteristics
        np.random.seed(42)
        strategies = {}
        for i, name in enumerate(["high_freq", "med_freq", "low_freq"]):
            returns = list(np.random.normal(0.001 * (3 - i), 0.02, 100))
            sharpe = (np.mean(returns) / np.std(returns)) * np.sqrt(252)
            strategies[name] = {"returns": returns, "sharpe": sharpe}

        # Cost-adjust Sharpes based on trading frequency
        model = TransactionCostModel(exchange=Exchange.BINANCE_FUTURES)
        trades_per_year = [1000, 500, 100]  # High, med, low freq
        adjusted_sharpes = []
        for (name, data), tpy in zip(strategies.items(), trades_per_year, strict=True):
            net = model.adjust_sharpe(
                gross_sharpe=data["sharpe"], avg_notional=10000, trades_per_year=tpy
            )
            adjusted_sharpes.append(net)

        # Select ensemble based on adjusted Sharpes
        names = list(strategies.keys())
        returns_dict = {n: strategies[n]["returns"] for n in names}
        _, corr = calculate_returns_correlation(returns_dict)

        result = select_ensemble(
            strategy_names=names,
            strategy_sharpes=adjusted_sharpes,
            correlation_matrix=corr,
            n_select=2,
        )
        assert len(result.strategies) <= 2
