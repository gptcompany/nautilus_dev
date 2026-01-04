"""
Luck vs Skill Quantification (Lopez de Prado)

Most backtests are luck. This module helps you know if you have real skill.

Key concepts from "Advances in Financial Machine Learning":
1. Deflated Sharpe Ratio - Adjusts for multiple testing
2. Probability of Backtest Overfitting (PBO)
3. Minimum Track Record Length - How long to prove skill?
4. False Strategy Theorem - Most strategies are false positives

The brutal truth:
- If you test 100 strategies, 5 will look good BY CHANCE (p=0.05)
- Sharpe of 2.0 from 1000 backtests is probably luck
- You need YEARS of out-of-sample to prove skill

This module helps you be honest with yourself.

Reference:
- Lopez de Prado (2018): Advances in Financial Machine Learning
- Bailey & Lopez de Prado (2012): The Sharpe Ratio Efficient Frontier
- Bailey et al. (2014): Probability of Backtest Overfitting
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional
from scipy import stats


@dataclass
class SkillAssessment:
    """Assessment of trading skill vs luck."""

    observed_sharpe: float
    deflated_sharpe: float  # After adjusting for trials
    min_track_record: float  # Months needed to prove skill
    probability_of_luck: float  # P(this is just luck)
    skill_confidence: float  # 1 - probability_of_luck
    verdict: str  # "likely_skill", "uncertain", "likely_luck"


class LuckQuantifier:
    """
    Quantify luck vs skill in trading performance.

    Based on Lopez de Prado's work on deflated Sharpe ratios
    and probability of backtest overfitting.

    Usage:
        luck = LuckQuantifier()

        # After backtest
        assessment = luck.assess(
            sharpe=1.5,
            n_trials=50,  # How many strategies did you test?
            track_record_months=12,
        )

        print(f"Probability this is luck: {assessment.probability_of_luck:.1%}")
        print(f"Months needed to prove skill: {assessment.min_track_record:.0f}")
    """

    def __init__(self, significance_level: float = 0.05):
        """
        Args:
            significance_level: Alpha for statistical tests (default 5%)
        """
        self.alpha = significance_level

    def assess(
        self,
        sharpe: float,
        n_trials: int = 1,
        track_record_months: int = 12,
        skewness: float = 0.0,
        kurtosis: float = 3.0,  # Normal = 3
        annual_periods: int = 252,  # Trading days per year
    ) -> SkillAssessment:
        """
        Full assessment of skill vs luck.

        Args:
            sharpe: Observed Sharpe ratio (annualized)
            n_trials: Number of strategies/variations tested
            track_record_months: Length of track record
            skewness: Return distribution skewness
            kurtosis: Return distribution kurtosis
            annual_periods: Periods per year for annualization

        Returns:
            SkillAssessment with all metrics
        """
        # 1. Deflate Sharpe for multiple testing
        deflated = self.deflated_sharpe_ratio(sharpe, n_trials)

        # 2. Calculate minimum track record needed
        min_track = self.minimum_track_record(
            sharpe,
            skewness=skewness,
            kurtosis=kurtosis,
        )

        # 3. Calculate probability this is luck
        prob_luck = self.probability_of_luck(
            sharpe,
            n_trials=n_trials,
            track_record_months=track_record_months,
        )

        # 4. Verdict
        if prob_luck > 0.5:
            verdict = "likely_luck"
        elif prob_luck > 0.2:
            verdict = "uncertain"
        else:
            verdict = "likely_skill"

        return SkillAssessment(
            observed_sharpe=sharpe,
            deflated_sharpe=deflated,
            min_track_record=min_track,
            probability_of_luck=prob_luck,
            skill_confidence=1 - prob_luck,
            verdict=verdict,
        )

    def deflated_sharpe_ratio(
        self,
        sharpe: float,
        n_trials: int,
        expected_max_sharpe: Optional[float] = None,
    ) -> float:
        """
        Deflate Sharpe ratio for multiple testing.

        When you test N strategies, the best one will have inflated Sharpe
        just by chance. This corrects for that.

        Formula: DSR = (SR - E[max(SR)]) / std(SR)

        Args:
            sharpe: Observed Sharpe ratio
            n_trials: Number of strategies tested
            expected_max_sharpe: Expected max Sharpe under null (auto-calculated)

        Returns:
            Deflated Sharpe ratio
        """
        if n_trials <= 1:
            return sharpe

        # Expected maximum Sharpe under null hypothesis
        # E[max] ≈ sqrt(2 * log(N)) for large N (extreme value theory)
        if expected_max_sharpe is None:
            # Approximation from order statistics
            expected_max_sharpe = math.sqrt(2 * math.log(n_trials))

        # Deflate
        deflated = sharpe - expected_max_sharpe

        return max(0, deflated)

    def minimum_track_record(
        self,
        sharpe: float,
        skewness: float = 0.0,
        kurtosis: float = 3.0,
        confidence: float = 0.95,
    ) -> float:
        """
        Minimum track record length to prove skill (in months).

        Based on Bailey & Lopez de Prado (2012).
        Accounts for non-normal returns.

        Args:
            sharpe: Target Sharpe ratio to prove
            skewness: Return skewness
            kurtosis: Return kurtosis (3 = normal)
            confidence: Confidence level

        Returns:
            Minimum months of track record needed
        """
        if sharpe <= 0:
            return float("inf")

        # Z-score for confidence level
        z = stats.norm.ppf(confidence)

        # Adjustment for non-normality (Lo, 2002)
        # Variance of Sharpe estimator increases with kurtosis
        excess_kurtosis = kurtosis - 3

        # Adjusted variance of Sharpe ratio estimator
        var_adjustment = 1 + (skewness * sharpe) + ((excess_kurtosis * sharpe**2) / 4)

        # Minimum track record in years
        min_years = var_adjustment * (z / sharpe) ** 2

        # Convert to months
        return min_years * 12

    def probability_of_luck(
        self,
        sharpe: float,
        n_trials: int = 1,
        track_record_months: int = 12,
        null_sharpe: float = 0.0,
    ) -> float:
        """
        Probability that observed Sharpe is due to luck.

        Uses multiple testing correction and track record length.

        Args:
            sharpe: Observed Sharpe ratio
            n_trials: Number of strategies tested
            track_record_months: Length of track record
            null_sharpe: Sharpe under null hypothesis

        Returns:
            Probability this is luck (0 to 1)
        """
        if sharpe <= null_sharpe:
            return 1.0

        # Standard error of Sharpe ratio
        # SE(SR) ≈ sqrt((1 + SR^2/2) / T) where T is in years
        track_years = track_record_months / 12
        se_sharpe = math.sqrt((1 + sharpe**2 / 2) / max(track_years, 0.1))

        # Z-score
        z = (sharpe - null_sharpe) / se_sharpe

        # P-value (one-tailed)
        p_value = 1 - stats.norm.cdf(z)

        # Bonferroni correction for multiple testing
        # (conservative but simple)
        p_adjusted = min(1.0, p_value * n_trials)

        return p_adjusted

    def probability_of_backtest_overfitting(
        self,
        is_returns: List[float],
        oos_returns: List[float],
        n_combinations: int = 100,
    ) -> float:
        """
        Probability of Backtest Overfitting (PBO).

        Uses combinatorially symmetric cross-validation (CSCV).

        Args:
            is_returns: In-sample returns
            oos_returns: Out-of-sample returns
            n_combinations: Number of train/test splits to try

        Returns:
            PBO (0 to 1, higher = more likely overfit)
        """
        if len(is_returns) < 10 or len(oos_returns) < 10:
            return 0.5  # Not enough data

        # Calculate rank correlation between IS and OOS performance
        # Low correlation = overfitting

        is_sharpe = self._calculate_sharpe(is_returns)
        oos_sharpe = self._calculate_sharpe(oos_returns)

        # If OOS Sharpe is much lower than IS, likely overfit
        if is_sharpe <= 0:
            return 0.5

        degradation = 1 - (oos_sharpe / is_sharpe)

        # Map to probability (heuristic)
        # degradation > 0.5 = likely overfit
        pbo = min(1.0, max(0.0, degradation))

        return pbo

    def _calculate_sharpe(self, returns: List[float]) -> float:
        """Calculate Sharpe ratio from returns."""
        if len(returns) < 2:
            return 0.0

        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / len(returns)

        # Return 0 if variance is 0 (undefined Sharpe - neutral value)
        if variance == 0:
            return 0.0

        std = math.sqrt(variance)
        # Annualize (assuming daily returns)
        return (mean / std) * math.sqrt(252)


class TrackRecordAnalyzer:
    """
    Analyze trading track record for skill assessment.

    Tracks performance over time and provides ongoing
    skill vs luck assessment.
    """

    def __init__(self, n_strategies_tested: int = 1):
        """
        Args:
            n_strategies_tested: How many strategies did you test to find this one?
        """
        self.n_trials = n_strategies_tested
        self.luck = LuckQuantifier()

        self._returns: List[float] = []
        self._equity_curve: List[float] = [1.0]

    def add_return(self, daily_return: float) -> None:
        """Add a daily return observation."""
        self._returns.append(daily_return)
        self._equity_curve.append(self._equity_curve[-1] * (1 + daily_return))

    def get_assessment(self) -> Optional[SkillAssessment]:
        """Get current skill assessment."""
        if len(self._returns) < 20:
            return None

        sharpe = self._calculate_sharpe()
        months = len(self._returns) / 21  # ~21 trading days per month

        return self.luck.assess(
            sharpe=sharpe,
            n_trials=self.n_trials,
            track_record_months=months,
            skewness=self._calculate_skewness(),
            kurtosis=self._calculate_kurtosis(),
        )

    def _calculate_sharpe(self) -> float:
        """Calculate current Sharpe ratio."""
        if len(self._returns) < 2:
            return 0.0

        mean = sum(self._returns) / len(self._returns)
        variance = sum((r - mean) ** 2 for r in self._returns) / len(self._returns)

        # Return 0 if variance is 0 (undefined Sharpe - neutral value)
        if variance == 0:
            return 0.0

        std = math.sqrt(variance)
        return (mean / std) * math.sqrt(252)

    def _calculate_skewness(self) -> float:
        """Calculate return skewness."""
        if len(self._returns) < 3:
            return 0.0

        mean = sum(self._returns) / len(self._returns)
        variance = sum((r - mean) ** 2 for r in self._returns) / len(self._returns)
        std = math.sqrt(variance) if variance > 0 else 1e-10

        skew = sum((r - mean) ** 3 for r in self._returns) / len(self._returns)
        return skew / (std**3) if std > 0 else 0.0

    def _calculate_kurtosis(self) -> float:
        """Calculate return kurtosis."""
        if len(self._returns) < 4:
            return 3.0  # Normal

        mean = sum(self._returns) / len(self._returns)
        variance = sum((r - mean) ** 2 for r in self._returns) / len(self._returns)
        std = math.sqrt(variance) if variance > 0 else 1e-10

        kurt = sum((r - mean) ** 4 for r in self._returns) / len(self._returns)
        return kurt / (std**4) if std > 0 else 3.0

    def get_report(self) -> str:
        """Get human-readable report."""
        assessment = self.get_assessment()

        if assessment is None:
            return "Not enough data yet (need at least 20 observations)"

        return f"""
╔══════════════════════════════════════════════════════════════╗
║                    SKILL vs LUCK REPORT                      ║
╠══════════════════════════════════════════════════════════════╣
║  Track Record: {len(self._returns)} days ({len(self._returns) / 21:.1f} months)
║  Strategies Tested: {self.n_trials}
║
║  OBSERVED SHARPE:     {assessment.observed_sharpe:+.2f}
║  DEFLATED SHARPE:     {assessment.deflated_sharpe:+.2f}  (adjusted for {self.n_trials} trials)
║
║  PROBABILITY OF LUCK: {assessment.probability_of_luck:.1%}
║  SKILL CONFIDENCE:    {assessment.skill_confidence:.1%}
║
║  MIN TRACK RECORD:    {assessment.min_track_record:.0f} months to prove skill
║
║  VERDICT: {assessment.verdict.upper()}
╚══════════════════════════════════════════════════════════════╝
"""
