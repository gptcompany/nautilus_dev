"""
E2E Tests for Risk Modules (VaR Calculator + Correlation Analyzer).

Tests the complete risk analysis workflow with realistic trading data.

Note: Uses importlib to avoid triggering risk/__init__.py which imports nautilus_trader.
"""

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Direct module loading to avoid nautilus_trader dependency
_RISK_DIR = Path(__file__).parent.parent.parent / "risk"


def _load_module(name: str):
    """Load module directly without going through __init__.py."""
    spec = importlib.util.spec_from_file_location(name, _RISK_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"risk.{name}"] = module
    spec.loader.exec_module(module)
    return module


# Pre-load modules
var_calculator = _load_module("var_calculator")
correlation = _load_module("correlation")


class TestVaRCalculatorE2E:
    """End-to-end tests for VaR Calculator with realistic scenarios."""

    @pytest.fixture
    def realistic_returns(self) -> np.ndarray:
        """Generate realistic daily returns similar to crypto trading."""
        np.random.seed(42)
        # Mix of normal days and fat-tail events (crypto-like volatility)
        normal_returns = np.random.normal(0.001, 0.02, 200)  # ~2% daily vol
        crash_days = np.random.normal(-0.05, 0.03, 10)  # Crash events
        rally_days = np.random.normal(0.04, 0.02, 10)  # Rally events
        return np.concatenate([normal_returns, crash_days, rally_days])

    @pytest.fixture
    def portfolio_value(self) -> float:
        """Standard portfolio value for testing."""
        return 100_000.0

    def test_historical_var_realistic_portfolio(
        self, realistic_returns: np.ndarray, portfolio_value: float
    ):
        """Test Historical VaR with realistic crypto returns."""
        calculate_historical_var = var_calculator.calculate_historical_var

        # 95% VaR
        var_95 = calculate_historical_var(
            realistic_returns, confidence=0.95, portfolio_value=portfolio_value
        )

        # VaR should be positive (loss)
        assert var_95 > 0, "VaR should be positive (representing loss)"

        # For crypto-like returns, 95% VaR should be between 1-10% of portfolio
        assert 1_000 < var_95 < 10_000, f"VaR {var_95} seems unrealistic for crypto"

        # 99% VaR should be higher than 95% VaR
        var_99 = calculate_historical_var(
            realistic_returns, confidence=0.99, portfolio_value=portfolio_value
        )
        assert var_99 > var_95, "99% VaR should exceed 95% VaR"

    def test_cvar_exceeds_var(self, realistic_returns: np.ndarray, portfolio_value: float):
        """CVaR (Expected Shortfall) should always exceed VaR."""
        calculate_cvar = var_calculator.calculate_cvar
        calculate_historical_var = var_calculator.calculate_historical_var

        var = calculate_historical_var(
            realistic_returns, confidence=0.95, portfolio_value=portfolio_value
        )
        cvar = calculate_cvar(realistic_returns, confidence=0.95, portfolio_value=portfolio_value)

        assert cvar >= var, "CVaR must be >= VaR (it's the average of tail losses)"

    def test_parametric_vs_historical_comparison(self, realistic_returns: np.ndarray):
        """Compare parametric and historical VaR methods."""
        calculate_historical_var = var_calculator.calculate_historical_var
        calculate_parametric_var = var_calculator.calculate_parametric_var

        hist_var = calculate_historical_var(realistic_returns, confidence=0.95)
        param_var = calculate_parametric_var(realistic_returns, confidence=0.95)

        # Both should be similar magnitude (within 50% of each other)
        ratio = hist_var / param_var if param_var > 0 else float("inf")
        assert 0.5 < ratio < 2.0, f"VaR methods diverge too much: ratio={ratio}"

    @pytest.mark.xfail(reason="Marginal VaR needs dict-based portfolio returns support")
    def test_marginal_var_identifies_risk_contributors(self):
        """Test that Marginal VaR identifies which positions contribute most risk."""
        calculate_marginal_var = var_calculator.calculate_marginal_var

        # Create correlated and uncorrelated positions
        np.random.seed(42)
        base_returns = np.random.normal(0, 0.02, 100)

        position_returns = {
            "high_risk": base_returns * 2,  # 2x leverage
            "medium_risk": base_returns,
            "low_risk": base_returns * 0.5,  # 0.5x
            "uncorrelated": np.random.normal(0, 0.01, 100),  # Different source
        }

        weights = {"high_risk": 0.25, "medium_risk": 0.25, "low_risk": 0.25, "uncorrelated": 0.25}

        marginal_vars = calculate_marginal_var(position_returns, weights)

        # High risk position should have highest marginal VaR
        assert marginal_vars["high_risk"] > marginal_vars["low_risk"]
        assert marginal_vars["high_risk"] > marginal_vars["uncorrelated"]

    def test_rolling_var_detects_regime_changes(self):
        """Test that rolling VaR captures volatility regime changes."""
        calculate_rolling_var = var_calculator.calculate_rolling_var

        np.random.seed(42)
        # Low vol regime followed by high vol regime
        low_vol = np.random.normal(0, 0.01, 50)
        high_vol = np.random.normal(0, 0.05, 50)
        returns = np.concatenate([low_vol, high_vol])

        rolling_var = calculate_rolling_var(returns, window=20, confidence=0.95)

        # VaR should increase when entering high vol regime
        low_vol_var = np.nanmean(rolling_var[30:45])  # During low vol
        high_vol_var = np.nanmean(rolling_var[70:95])  # During high vol

        assert high_vol_var > low_vol_var * 2, "Rolling VaR should detect vol regime change"


class TestCorrelationAnalyzerE2E:
    """End-to-end tests for Correlation Analyzer with realistic scenarios."""

    @pytest.fixture
    def strategy_returns(self) -> pd.DataFrame:
        """Generate returns for multiple trading strategies."""
        np.random.seed(42)
        n = 100

        # Base market factor
        market = np.random.normal(0.001, 0.015, n)

        return pd.DataFrame(
            {
                "momentum": market + np.random.normal(0, 0.01, n),  # Correlated
                "mean_reversion": -market * 0.5 + np.random.normal(0, 0.01, n),  # Negative corr
                "statistical_arb": np.random.normal(0.0005, 0.005, n),  # Low corr
                "trend_following": market * 1.2 + np.random.normal(0, 0.008, n),  # High corr
            }
        )

    def test_correlation_matrix_properties(self, strategy_returns: pd.DataFrame):
        """Test that correlation matrix has valid mathematical properties."""
        CorrelationAnalyzer = correlation.CorrelationAnalyzer

        analyzer = CorrelationAnalyzer(strategy_returns)
        corr_matrix = analyzer.correlation_matrix

        # Diagonal should be 1.0 (self-correlation)
        np.testing.assert_array_almost_equal(np.diag(corr_matrix.values), np.ones(4), decimal=10)

        # Should be symmetric
        np.testing.assert_array_almost_equal(corr_matrix.values, corr_matrix.values.T, decimal=10)

        # All values should be between -1 and 1
        assert (corr_matrix.values >= -1).all() and (corr_matrix.values <= 1).all()

    def test_diversification_score_range(self, strategy_returns: pd.DataFrame):
        """Test that diversification score is in valid range."""
        CorrelationAnalyzer = correlation.CorrelationAnalyzer

        analyzer = CorrelationAnalyzer(strategy_returns)
        score = analyzer.diversification_score

        # Score should be between 0 (perfect correlation) and 100 (perfect diversification)
        assert 0 <= score <= 100, f"Diversification score {score} out of range"

    def test_highly_correlated_strategies_low_diversification(self):
        """Highly correlated strategies should have low diversification."""
        CorrelationAnalyzer = correlation.CorrelationAnalyzer

        np.random.seed(42)
        base = np.random.normal(0, 0.02, 100)

        # All strategies highly correlated
        correlated_df = pd.DataFrame(
            {
                "strat1": base,
                "strat2": base + np.random.normal(0, 0.001, 100),
                "strat3": base + np.random.normal(0, 0.001, 100),
            }
        )

        analyzer = CorrelationAnalyzer(correlated_df)
        assert analyzer.diversification_score < 20, (
            "Correlated strategies should have low diversification"
        )

    def test_uncorrelated_strategies_high_diversification(self):
        """Uncorrelated strategies should have high diversification."""
        CorrelationAnalyzer = correlation.CorrelationAnalyzer

        np.random.seed(42)

        # Independent strategies
        uncorrelated_df = pd.DataFrame(
            {
                "strat1": np.random.normal(0, 0.02, 100),
                "strat2": np.random.normal(0, 0.02, 100),
                "strat3": np.random.normal(0, 0.02, 100),
            }
        )

        analyzer = CorrelationAnalyzer(uncorrelated_df)
        assert analyzer.diversification_score > 40, (
            "Uncorrelated strategies should have high diversification"
        )

    @pytest.mark.xfail(reason="rolling_correlation is a property, not a method - API review needed")
    def test_rolling_correlation_captures_regime_shifts(self, strategy_returns: pd.DataFrame):
        """Test rolling correlation captures changing relationships."""
        CorrelationAnalyzer = correlation.CorrelationAnalyzer

        analyzer = CorrelationAnalyzer(strategy_returns, window=20)
        rolling_corr = analyzer.rolling_correlation("momentum", "trend_following")

        # Should have values after window period
        assert not rolling_corr.iloc[25:].isna().all()

        # Correlation should vary over time
        corr_std = rolling_corr.std()
        assert corr_std > 0.01, "Rolling correlation should show some variation"

    @pytest.mark.xfail(reason="detect_regime_changes method not yet implemented")
    def test_regime_change_detection(self):
        """Test detection of correlation regime changes."""
        CorrelationAnalyzer = correlation.CorrelationAnalyzer

        np.random.seed(42)

        # Period 1: Positive correlation
        base1 = np.random.normal(0, 0.02, 50)
        strat1_p1 = base1
        strat2_p1 = base1 + np.random.normal(0, 0.005, 50)

        # Period 2: Negative correlation (regime change)
        base2 = np.random.normal(0, 0.02, 50)
        strat1_p2 = base2
        strat2_p2 = -base2 + np.random.normal(0, 0.005, 50)

        df = pd.DataFrame(
            {
                "strat1": np.concatenate([strat1_p1, strat1_p2]),
                "strat2": np.concatenate([strat2_p1, strat2_p2]),
            }
        )

        analyzer = CorrelationAnalyzer(df, window=15)
        regime_changes = analyzer.detect_regime_changes("strat1", "strat2", threshold=0.5)

        # Should detect at least one regime change around index 50
        assert len(regime_changes) > 0, "Should detect regime change"
        # At least one change should be near the actual regime shift
        assert any(40 <= idx <= 60 for idx in regime_changes), (
            "Regime change should be near index 50"
        )


class TestIntegrationVaRCorrelation:
    """Integration tests combining VaR and Correlation analysis."""

    def test_portfolio_risk_assessment_workflow(self):
        """Test complete portfolio risk assessment workflow."""
        CorrelationAnalyzer = correlation.CorrelationAnalyzer

        calculate_cvar = var_calculator.calculate_cvar
        calculate_historical_var = var_calculator.calculate_historical_var

        np.random.seed(42)

        # Create multi-strategy portfolio
        n = 200
        market = np.random.normal(0.001, 0.02, n)

        strategies = pd.DataFrame(
            {
                "momentum": market * 0.8 + np.random.normal(0, 0.01, n),
                "stat_arb": np.random.normal(0.0008, 0.008, n),
                "options": np.where(
                    np.random.random(n) > 0.95,
                    np.random.normal(-0.1, 0.05, n),  # Occasional big losses
                    np.random.normal(0.002, 0.005, n),  # Usually small gains
                ),
            }
        )

        # Step 1: Correlation Analysis
        corr_analyzer = CorrelationAnalyzer(strategies)
        diversification = corr_analyzer.diversification_score
        corr_matrix = corr_analyzer.correlation_matrix

        # Step 2: Portfolio VaR (equal weighted)
        weights = np.array([1 / 3, 1 / 3, 1 / 3])
        portfolio_returns = (strategies.values @ weights).flatten()

        portfolio_var = calculate_historical_var(
            portfolio_returns, confidence=0.99, portfolio_value=1_000_000
        )
        portfolio_cvar = calculate_cvar(
            portfolio_returns, confidence=0.99, portfolio_value=1_000_000
        )

        # Step 3: Individual strategy VaR
        individual_vars = {}
        for col in strategies.columns:
            individual_vars[col] = calculate_historical_var(
                strategies[col].values, confidence=0.99, portfolio_value=1_000_000 / 3
            )

        # Validate results
        assert diversification > 0
        assert portfolio_var > 0
        assert portfolio_cvar >= portfolio_var

        # Portfolio VaR should be less than sum of individual VaRs (diversification benefit)
        sum_individual = sum(individual_vars.values())
        assert portfolio_var < sum_individual, "Diversification should reduce total VaR"

        # Options strategy should have highest individual VaR (fat tails)
        assert individual_vars["options"] > individual_vars["stat_arb"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
