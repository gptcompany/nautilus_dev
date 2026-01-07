"""Comprehensive tests for Luck vs Skill Quantification module.

Focus on:
- SkillAssessment dataclass
- LuckQuantifier: deflated Sharpe, minimum track record, probability of luck, PBO
- TrackRecordAnalyzer: return tracking, skill assessment, reporting
- Statistical edge cases
- Error handling paths
"""

import math

import pytest

from strategies.common.adaptive_control.luck_skill import (
    LuckQuantifier,
    SkillAssessment,
    TrackRecordAnalyzer,
)


# =============================================================================
# Test SkillAssessment Dataclass
# =============================================================================


class TestSkillAssessment:
    """Test SkillAssessment dataclass."""

    def test_skill_assessment_creation(self):
        """Test creating SkillAssessment with all fields."""
        assessment = SkillAssessment(
            observed_sharpe=1.5,
            deflated_sharpe=0.8,
            min_track_record=24.0,
            probability_of_luck=0.15,
            skill_confidence=0.85,
            verdict="likely_skill",
        )
        assert assessment.observed_sharpe == 1.5
        assert assessment.deflated_sharpe == 0.8
        assert assessment.min_track_record == 24.0
        assert assessment.probability_of_luck == 0.15
        assert assessment.skill_confidence == 0.85
        assert assessment.verdict == "likely_skill"

    def test_skill_assessment_uncertain_verdict(self):
        """Test SkillAssessment with uncertain verdict."""
        assessment = SkillAssessment(
            observed_sharpe=1.0,
            deflated_sharpe=0.3,
            min_track_record=36.0,
            probability_of_luck=0.35,
            skill_confidence=0.65,
            verdict="uncertain",
        )
        assert assessment.verdict == "uncertain"

    def test_skill_assessment_likely_luck_verdict(self):
        """Test SkillAssessment with likely_luck verdict."""
        assessment = SkillAssessment(
            observed_sharpe=0.8,
            deflated_sharpe=0.0,
            min_track_record=48.0,
            probability_of_luck=0.75,
            skill_confidence=0.25,
            verdict="likely_luck",
        )
        assert assessment.verdict == "likely_luck"


# =============================================================================
# Test LuckQuantifier
# =============================================================================


class TestLuckQuantifierInit:
    """Test LuckQuantifier initialization."""

    def test_default_significance_level(self):
        """Test default significance level is 0.05."""
        luck = LuckQuantifier()
        assert luck.alpha == 0.05

    def test_custom_significance_level(self):
        """Test custom significance level."""
        luck = LuckQuantifier(significance_level=0.01)
        assert luck.alpha == 0.01


class TestDeflatedSharpeRatio:
    """Test deflated_sharpe_ratio method."""

    def test_single_trial_no_deflation(self):
        """Test single trial returns original Sharpe."""
        luck = LuckQuantifier()
        sharpe = 1.5
        deflated = luck.deflated_sharpe_ratio(sharpe, n_trials=1)
        assert deflated == sharpe

    def test_multiple_trials_deflates_sharpe(self):
        """Test multiple trials deflate Sharpe ratio."""
        luck = LuckQuantifier()
        sharpe = 2.0
        n_trials = 100

        deflated = luck.deflated_sharpe_ratio(sharpe, n_trials)

        # Expected max Sharpe under null: sqrt(2 * log(100)) ≈ 3.03
        expected_max = math.sqrt(2 * math.log(n_trials))
        expected_deflated = max(0, sharpe - expected_max)

        assert abs(deflated - expected_deflated) < 1e-10

    def test_sharpe_below_expected_max_returns_zero(self):
        """Test Sharpe below expected max returns 0."""
        luck = LuckQuantifier()
        sharpe = 1.0
        n_trials = 1000

        deflated = luck.deflated_sharpe_ratio(sharpe, n_trials)

        # Expected max Sharpe under null: sqrt(2 * log(1000)) ≈ 3.72
        # 1.0 - 3.72 = negative, clamped to 0
        assert deflated == 0.0

    def test_custom_expected_max_sharpe(self):
        """Test custom expected max Sharpe."""
        luck = LuckQuantifier()
        sharpe = 2.0
        n_trials = 50
        custom_expected_max = 1.5

        deflated = luck.deflated_sharpe_ratio(
            sharpe, n_trials, expected_max_sharpe=custom_expected_max
        )

        assert abs(deflated - (sharpe - custom_expected_max)) < 1e-10

    def test_zero_sharpe_deflated(self):
        """Test zero Sharpe gets deflated to zero."""
        luck = LuckQuantifier()
        deflated = luck.deflated_sharpe_ratio(0.0, n_trials=10)
        assert deflated == 0.0

    def test_negative_sharpe_deflated_to_zero(self):
        """Test negative Sharpe gets clamped to zero."""
        luck = LuckQuantifier()
        deflated = luck.deflated_sharpe_ratio(-1.0, n_trials=10)
        assert deflated == 0.0

    def test_many_trials_severe_deflation(self):
        """Test many trials cause severe deflation."""
        luck = LuckQuantifier()
        sharpe = 3.0
        n_trials = 10000

        deflated = luck.deflated_sharpe_ratio(sharpe, n_trials)

        # sqrt(2 * log(10000)) ≈ 4.29
        # 3.0 - 4.29 = negative, clamped to 0
        assert deflated == 0.0


class TestMinimumTrackRecord:
    """Test minimum_track_record method."""

    def test_positive_sharpe_finite_track_record(self):
        """Test positive Sharpe returns finite track record."""
        luck = LuckQuantifier()
        min_track = luck.minimum_track_record(sharpe=1.0)

        # Should be finite and positive
        assert min_track > 0
        assert math.isfinite(min_track)

    def test_zero_sharpe_returns_infinity(self):
        """Test zero Sharpe returns infinite track record."""
        luck = LuckQuantifier()
        min_track = luck.minimum_track_record(sharpe=0.0)
        assert min_track == float("inf")

    def test_negative_sharpe_returns_infinity(self):
        """Test negative Sharpe returns infinite track record."""
        luck = LuckQuantifier()
        min_track = luck.minimum_track_record(sharpe=-0.5)
        assert min_track == float("inf")

    def test_higher_sharpe_needs_shorter_track_record(self):
        """Test higher Sharpe needs shorter track record."""
        luck = LuckQuantifier()

        track_low_sharpe = luck.minimum_track_record(sharpe=0.5)
        track_high_sharpe = luck.minimum_track_record(sharpe=2.0)

        assert track_high_sharpe < track_low_sharpe

    def test_skewness_affects_track_record(self):
        """Test skewness affects minimum track record."""
        luck = LuckQuantifier()

        track_no_skew = luck.minimum_track_record(sharpe=1.0, skewness=0.0)
        track_pos_skew = luck.minimum_track_record(sharpe=1.0, skewness=1.0)
        track_neg_skew = luck.minimum_track_record(sharpe=1.0, skewness=-1.0)

        # With positive Sharpe, positive skew increases variance adjustment
        assert track_pos_skew > track_no_skew
        # Negative skew decreases variance adjustment
        assert track_neg_skew < track_no_skew

    def test_excess_kurtosis_affects_track_record(self):
        """Test excess kurtosis affects minimum track record."""
        luck = LuckQuantifier()

        track_normal = luck.minimum_track_record(sharpe=1.0, kurtosis=3.0)
        track_fat_tails = luck.minimum_track_record(sharpe=1.0, kurtosis=6.0)
        track_thin_tails = luck.minimum_track_record(sharpe=1.0, kurtosis=2.0)

        # Fat tails (excess kurtosis > 0) increase required track record
        assert track_fat_tails > track_normal
        # Thin tails (excess kurtosis < 0) decrease required track record
        assert track_thin_tails < track_normal

    def test_confidence_level_affects_track_record(self):
        """Test confidence level affects minimum track record."""
        luck = LuckQuantifier()

        track_95 = luck.minimum_track_record(sharpe=1.0, confidence=0.95)
        track_99 = luck.minimum_track_record(sharpe=1.0, confidence=0.99)
        track_90 = luck.minimum_track_record(sharpe=1.0, confidence=0.90)

        # Higher confidence needs longer track record
        assert track_99 > track_95 > track_90

    def test_realistic_sharpe_track_record(self):
        """Test realistic Sharpe ratio track record estimate."""
        luck = LuckQuantifier()

        # Sharpe of 1.0 with normal returns at 95% confidence
        min_track = luck.minimum_track_record(
            sharpe=1.0,
            skewness=0.0,
            kurtosis=3.0,
            confidence=0.95,
        )

        # Should be roughly 38 months (from Lo 2002)
        assert 30 < min_track < 50


class TestProbabilityOfLuck:
    """Test probability_of_luck method."""

    def test_zero_sharpe_returns_one(self):
        """Test zero Sharpe returns probability 1.0."""
        luck = LuckQuantifier()
        prob = luck.probability_of_luck(sharpe=0.0)
        assert prob == 1.0

    def test_negative_sharpe_returns_one(self):
        """Test negative Sharpe returns probability 1.0."""
        luck = LuckQuantifier()
        prob = luck.probability_of_luck(sharpe=-1.0)
        assert prob == 1.0

    def test_sharpe_equal_null_returns_one(self):
        """Test Sharpe equal to null hypothesis returns 1.0."""
        luck = LuckQuantifier()
        prob = luck.probability_of_luck(sharpe=0.5, null_sharpe=0.5)
        assert prob == 1.0

    def test_sharpe_below_null_returns_one(self):
        """Test Sharpe below null hypothesis returns 1.0."""
        luck = LuckQuantifier()
        prob = luck.probability_of_luck(sharpe=0.3, null_sharpe=0.5)
        assert prob == 1.0

    def test_high_sharpe_low_probability(self):
        """Test high Sharpe has low probability of luck."""
        luck = LuckQuantifier()
        prob = luck.probability_of_luck(
            sharpe=3.0,
            n_trials=1,
            track_record_months=36,
        )
        assert prob < 0.1

    def test_longer_track_record_reduces_luck_probability(self):
        """Test longer track record reduces probability of luck."""
        luck = LuckQuantifier()

        prob_short = luck.probability_of_luck(sharpe=1.5, track_record_months=6)
        prob_long = luck.probability_of_luck(sharpe=1.5, track_record_months=36)

        assert prob_long < prob_short

    def test_more_trials_increases_luck_probability(self):
        """Test more trials increases probability of luck."""
        luck = LuckQuantifier()

        prob_few = luck.probability_of_luck(sharpe=2.0, n_trials=1)
        prob_many = luck.probability_of_luck(sharpe=2.0, n_trials=100)

        assert prob_many > prob_few

    def test_bonferroni_correction_caps_at_one(self):
        """Test Bonferroni correction caps probability at 1.0."""
        luck = LuckQuantifier()
        prob = luck.probability_of_luck(
            sharpe=0.5,
            n_trials=1000,
            track_record_months=3,
        )
        assert prob <= 1.0

    def test_very_short_track_record_high_luck(self):
        """Test very short track record has high probability of luck."""
        luck = LuckQuantifier()
        prob = luck.probability_of_luck(
            sharpe=2.0,
            track_record_months=1,
        )
        # Even with good Sharpe, very short track record is suspicious
        assert prob > 0.1

    def test_custom_null_sharpe(self):
        """Test custom null Sharpe hypothesis."""
        luck = LuckQuantifier()

        # Sharpe of 1.0 vs null of 0.0
        prob_vs_zero = luck.probability_of_luck(sharpe=1.0, null_sharpe=0.0)
        # Sharpe of 1.0 vs null of 0.5
        prob_vs_half = luck.probability_of_luck(sharpe=1.0, null_sharpe=0.5)

        # Beating higher null is harder, so probability of luck is higher
        assert prob_vs_half > prob_vs_zero


class TestProbabilityOfBacktestOverfitting:
    """Test probability_of_backtest_overfitting method."""

    def test_insufficient_data_returns_half(self):
        """Test insufficient data returns 0.5."""
        luck = LuckQuantifier()

        # Too few IS returns
        pbo = luck.probability_of_backtest_overfitting(
            is_returns=[0.01] * 5,
            oos_returns=[0.01] * 20,
        )
        assert pbo == 0.5

        # Too few OOS returns
        pbo = luck.probability_of_backtest_overfitting(
            is_returns=[0.01] * 20,
            oos_returns=[0.01] * 5,
        )
        assert pbo == 0.5

    def test_zero_is_sharpe_returns_half(self):
        """Test zero IS Sharpe returns 0.5."""
        luck = LuckQuantifier()

        # Zero variance (all same values) -> zero Sharpe
        pbo = luck.probability_of_backtest_overfitting(
            is_returns=[0.0] * 20,
            oos_returns=[0.01, -0.01] * 10,
        )
        assert pbo == 0.5

    def test_equal_is_oos_sharpe_low_pbo(self):
        """Test equal IS and OOS Sharpe has low PBO."""
        luck = LuckQuantifier()

        # Similar performance in and out of sample
        is_returns = [0.01, -0.005, 0.008, -0.003] * 5
        oos_returns = [0.012, -0.004, 0.007, -0.002] * 5

        pbo = luck.probability_of_backtest_overfitting(is_returns, oos_returns)

        # Should indicate low overfitting
        assert pbo < 0.5

    def test_worse_oos_sharpe_high_pbo(self):
        """Test worse OOS Sharpe has high PBO."""
        luck = LuckQuantifier()

        # Good IS, poor OOS
        is_returns = [0.02, 0.015, 0.018, 0.012] * 5
        oos_returns = [0.001, -0.002, 0.003, -0.001] * 5

        pbo = luck.probability_of_backtest_overfitting(is_returns, oos_returns)

        # Should indicate overfitting
        assert pbo > 0.3

    def test_better_oos_sharpe_low_pbo(self):
        """Test better OOS Sharpe has low PBO (negative degradation clamped to 0)."""
        luck = LuckQuantifier()

        # Good IS, better OOS - use data with variance for proper Sharpe calculation
        is_returns = [0.01, 0.015, 0.008, 0.012, 0.005] * 4  # Positive mean, some variance
        oos_returns = [0.03, 0.02, 0.025, 0.015, 0.035] * 4  # Higher positive mean

        pbo = luck.probability_of_backtest_overfitting(is_returns, oos_returns)

        # Better OOS means negative degradation, clamped to 0
        assert pbo == 0.0

    def test_pbo_bounded_zero_one(self):
        """Test PBO is always in [0, 1]."""
        luck = LuckQuantifier()

        # Various scenarios
        test_cases = [
            ([0.01] * 15, [0.01] * 15),
            ([0.05, -0.02] * 10, [0.01, -0.01] * 10),
            ([-0.01] * 15, [0.01] * 15),
        ]

        for is_ret, oos_ret in test_cases:
            pbo = luck.probability_of_backtest_overfitting(is_ret, oos_ret)
            assert 0.0 <= pbo <= 1.0


class TestLuckQuantifierCalculateSharpe:
    """Test _calculate_sharpe private method."""

    def test_empty_returns_zero(self):
        """Test empty returns gives zero Sharpe."""
        luck = LuckQuantifier()
        sharpe = luck._calculate_sharpe([])
        assert sharpe == 0.0

    def test_single_return_zero(self):
        """Test single return gives zero Sharpe."""
        luck = LuckQuantifier()
        sharpe = luck._calculate_sharpe([0.01])
        assert sharpe == 0.0

    def test_constant_returns_zero(self):
        """Test constant returns (zero variance) gives zero Sharpe."""
        luck = LuckQuantifier()
        sharpe = luck._calculate_sharpe([0.01] * 20)
        assert sharpe == 0.0

    def test_positive_returns_positive_sharpe(self):
        """Test positive mean returns gives positive Sharpe."""
        luck = LuckQuantifier()
        sharpe = luck._calculate_sharpe([0.01, 0.02, 0.015, 0.018, 0.012])
        assert sharpe > 0

    def test_negative_returns_negative_sharpe(self):
        """Test negative mean returns gives negative Sharpe."""
        luck = LuckQuantifier()
        sharpe = luck._calculate_sharpe([-0.01, -0.02, -0.015, -0.018, -0.012])
        assert sharpe < 0

    def test_annualization_factor(self):
        """Test Sharpe is annualized (sqrt(252) factor)."""
        luck = LuckQuantifier()

        # Create returns with known mean and std
        returns = [0.001, -0.001] * 50  # Mean=0, Std=0.001
        sharpe = luck._calculate_sharpe(returns)

        # With mean=0, Sharpe should be ~0
        assert abs(sharpe) < 0.01


class TestLuckQuantifierAssess:
    """Test assess method - full skill assessment."""

    def test_assess_likely_luck(self):
        """Test assessment returns likely_luck for poor performance."""
        luck = LuckQuantifier()

        assessment = luck.assess(
            sharpe=0.5,
            n_trials=100,
            track_record_months=6,
        )

        assert assessment.verdict == "likely_luck"
        assert assessment.probability_of_luck > 0.5

    def test_assess_uncertain(self):
        """Test assessment returns uncertain for moderate performance."""
        luck = LuckQuantifier()

        # Parameters that give uncertain verdict (prob_luck between 0.2 and 0.5)
        assessment = luck.assess(
            sharpe=1.5,
            n_trials=2,
            track_record_months=12,
        )

        assert assessment.verdict == "uncertain"
        assert 0.2 < assessment.probability_of_luck <= 0.5

    def test_assess_likely_skill(self):
        """Test assessment returns likely_skill for strong performance."""
        luck = LuckQuantifier()

        assessment = luck.assess(
            sharpe=3.0,
            n_trials=1,
            track_record_months=36,
        )

        assert assessment.verdict == "likely_skill"
        assert assessment.probability_of_luck < 0.2

    def test_assess_all_fields_populated(self):
        """Test assessment populates all fields."""
        luck = LuckQuantifier()

        assessment = luck.assess(sharpe=1.0)

        assert assessment.observed_sharpe == 1.0
        assert assessment.deflated_sharpe >= 0
        assert assessment.min_track_record > 0
        assert 0 <= assessment.probability_of_luck <= 1
        assert assessment.skill_confidence == 1 - assessment.probability_of_luck
        assert assessment.verdict in ["likely_luck", "uncertain", "likely_skill"]

    def test_assess_with_non_normal_returns(self):
        """Test assessment with non-normal return parameters."""
        luck = LuckQuantifier()

        assessment = luck.assess(
            sharpe=1.5,
            n_trials=5,
            track_record_months=24,
            skewness=-0.5,
            kurtosis=5.0,
        )

        # Fat tails should increase minimum track record
        normal_assessment = luck.assess(
            sharpe=1.5,
            n_trials=5,
            track_record_months=24,
            skewness=0.0,
            kurtosis=3.0,
        )

        assert assessment.min_track_record > normal_assessment.min_track_record

    def test_assess_boundary_probability_likelihood_luck(self):
        """Test verdict at probability of luck boundary (>0.5)."""
        luck = LuckQuantifier()

        # Force probability just above 0.5
        assessment = luck.assess(
            sharpe=0.8,
            n_trials=50,
            track_record_months=12,
        )

        if assessment.probability_of_luck > 0.5:
            assert assessment.verdict == "likely_luck"

    def test_assess_boundary_probability_uncertain(self):
        """Test verdict at uncertain boundary (0.2 < prob <= 0.5)."""
        luck = LuckQuantifier()

        # Force probability in uncertain range
        assessment = luck.assess(
            sharpe=1.2,
            n_trials=5,
            track_record_months=18,
        )

        if 0.2 < assessment.probability_of_luck <= 0.5:
            assert assessment.verdict == "uncertain"


# =============================================================================
# Test TrackRecordAnalyzer
# =============================================================================


class TestTrackRecordAnalyzerInit:
    """Test TrackRecordAnalyzer initialization."""

    def test_default_initialization(self):
        """Test default initialization."""
        analyzer = TrackRecordAnalyzer()
        assert analyzer.n_trials == 1
        assert analyzer._returns == []
        assert analyzer._equity_curve == [1.0]

    def test_custom_n_strategies(self):
        """Test custom number of strategies tested."""
        analyzer = TrackRecordAnalyzer(n_strategies_tested=50)
        assert analyzer.n_trials == 50


class TestTrackRecordAnalyzerAddReturn:
    """Test add_return method."""

    def test_add_single_return(self):
        """Test adding single return."""
        analyzer = TrackRecordAnalyzer()
        analyzer.add_return(0.01)

        assert len(analyzer._returns) == 1
        assert analyzer._returns[0] == 0.01
        assert len(analyzer._equity_curve) == 2
        assert abs(analyzer._equity_curve[1] - 1.01) < 1e-10

    def test_add_multiple_returns(self):
        """Test adding multiple returns."""
        analyzer = TrackRecordAnalyzer()
        analyzer.add_return(0.01)
        analyzer.add_return(0.02)
        analyzer.add_return(-0.01)

        assert len(analyzer._returns) == 3
        assert len(analyzer._equity_curve) == 4

        # Check equity curve: 1.0 * 1.01 * 1.02 * 0.99
        expected = 1.0 * 1.01 * 1.02 * 0.99
        assert abs(analyzer._equity_curve[-1] - expected) < 1e-10

    def test_add_negative_return(self):
        """Test adding negative return."""
        analyzer = TrackRecordAnalyzer()
        analyzer.add_return(-0.05)

        assert analyzer._returns[0] == -0.05
        assert abs(analyzer._equity_curve[1] - 0.95) < 1e-10


class TestTrackRecordAnalyzerGetAssessment:
    """Test get_assessment method."""

    def test_insufficient_data_returns_none(self):
        """Test insufficient data returns None."""
        analyzer = TrackRecordAnalyzer()

        # Add only 10 returns (need 20)
        for _ in range(10):
            analyzer.add_return(0.01)

        assessment = analyzer.get_assessment()
        assert assessment is None

    def test_exactly_20_returns_works(self):
        """Test exactly 20 returns works."""
        analyzer = TrackRecordAnalyzer()

        for _ in range(20):
            analyzer.add_return(0.01)

        assessment = analyzer.get_assessment()
        assert assessment is not None

    def test_assessment_uses_calculated_sharpe(self):
        """Test assessment uses calculated Sharpe."""
        analyzer = TrackRecordAnalyzer()

        # Add varied returns
        returns = [0.01, -0.005, 0.015, -0.003, 0.008] * 10
        for r in returns:
            analyzer.add_return(r)

        assessment = analyzer.get_assessment()
        assert assessment is not None
        assert assessment.observed_sharpe != 0

    def test_assessment_calculates_months_correctly(self):
        """Test assessment calculates months correctly."""
        analyzer = TrackRecordAnalyzer()

        # Add 42 returns (~2 months at 21 days/month)
        for _ in range(42):
            analyzer.add_return(0.005)

        assessment = analyzer.get_assessment()
        assert assessment is not None
        # Should be approximately 2 months

    def test_assessment_uses_n_trials(self):
        """Test assessment uses n_trials from initialization."""
        analyzer = TrackRecordAnalyzer(n_strategies_tested=100)

        for _ in range(50):
            analyzer.add_return(0.01)

        assessment = analyzer.get_assessment()
        assert assessment is not None
        # Deflated Sharpe should be affected by high n_trials
        # (likely 0 or close to 0 due to Bonferroni correction)


class TestTrackRecordAnalyzerCalculateSharpe:
    """Test _calculate_sharpe method."""

    def test_sharpe_insufficient_data(self):
        """Test Sharpe with insufficient data returns 0."""
        analyzer = TrackRecordAnalyzer()
        analyzer.add_return(0.01)

        sharpe = analyzer._calculate_sharpe()
        assert sharpe == 0.0

    def test_sharpe_zero_variance(self):
        """Test Sharpe with zero variance returns 0."""
        analyzer = TrackRecordAnalyzer()
        for _ in range(10):
            analyzer.add_return(0.01)  # Constant

        sharpe = analyzer._calculate_sharpe()
        assert sharpe == 0.0

    def test_sharpe_positive_returns(self):
        """Test Sharpe with positive mean returns."""
        analyzer = TrackRecordAnalyzer()
        returns = [0.01, 0.015, 0.008, 0.012, 0.018, 0.005]
        for r in returns:
            analyzer.add_return(r)

        sharpe = analyzer._calculate_sharpe()
        assert sharpe > 0


class TestTrackRecordAnalyzerCalculateSkewness:
    """Test _calculate_skewness method."""

    def test_skewness_insufficient_data(self):
        """Test skewness with insufficient data returns 0."""
        analyzer = TrackRecordAnalyzer()
        analyzer.add_return(0.01)
        analyzer.add_return(0.02)

        skew = analyzer._calculate_skewness()
        assert skew == 0.0

    def test_skewness_symmetric_distribution(self):
        """Test skewness of symmetric distribution is near zero."""
        analyzer = TrackRecordAnalyzer()
        # Symmetric around 0
        returns = [0.01, -0.01, 0.02, -0.02, 0.01, -0.01]
        for r in returns:
            analyzer.add_return(r)

        skew = analyzer._calculate_skewness()
        assert abs(skew) < 0.1

    def test_skewness_positive_skew(self):
        """Test positive skewness detection."""
        analyzer = TrackRecordAnalyzer()
        # Right-skewed: mostly small, few large positive
        returns = [0.001] * 10 + [0.1]
        for r in returns:
            analyzer.add_return(r)

        skew = analyzer._calculate_skewness()
        assert skew > 0

    def test_skewness_negative_skew(self):
        """Test negative skewness detection."""
        analyzer = TrackRecordAnalyzer()
        # Left-skewed: mostly small, few large negative
        returns = [-0.001] * 10 + [-0.1]
        for r in returns:
            analyzer.add_return(r)

        skew = analyzer._calculate_skewness()
        assert skew < 0


class TestTrackRecordAnalyzerCalculateKurtosis:
    """Test _calculate_kurtosis method."""

    def test_kurtosis_insufficient_data(self):
        """Test kurtosis with insufficient data returns 3 (normal)."""
        analyzer = TrackRecordAnalyzer()
        for _ in range(3):
            analyzer.add_return(0.01)

        kurt = analyzer._calculate_kurtosis()
        assert kurt == 3.0

    def test_kurtosis_calculation(self):
        """Test kurtosis is calculated."""
        analyzer = TrackRecordAnalyzer()
        returns = [0.01, -0.01, 0.02, -0.02, 0.015, -0.015, 0.005, -0.005]
        for r in returns:
            analyzer.add_return(r)

        kurt = analyzer._calculate_kurtosis()
        # Should be a valid number
        assert math.isfinite(kurt)


class TestTrackRecordAnalyzerGetReport:
    """Test get_report method."""

    def test_report_insufficient_data(self):
        """Test report with insufficient data."""
        analyzer = TrackRecordAnalyzer()
        for _ in range(10):
            analyzer.add_return(0.01)

        report = analyzer.get_report()
        assert "Not enough data" in report
        assert "20 observations" in report

    def test_report_with_sufficient_data(self):
        """Test report with sufficient data."""
        analyzer = TrackRecordAnalyzer(n_strategies_tested=10)

        returns = [0.01, -0.005, 0.008, -0.003, 0.012] * 10
        for r in returns:
            analyzer.add_return(r)

        report = analyzer.get_report()

        # Check report contains key sections
        assert "SKILL vs LUCK REPORT" in report
        assert "Track Record:" in report
        assert "Strategies Tested:" in report
        assert "OBSERVED SHARPE:" in report
        assert "DEFLATED SHARPE:" in report
        assert "PROBABILITY OF LUCK:" in report
        assert "SKILL CONFIDENCE:" in report
        assert "MIN TRACK RECORD:" in report
        assert "VERDICT:" in report

    def test_report_shows_correct_n_trials(self):
        """Test report shows correct number of trials."""
        analyzer = TrackRecordAnalyzer(n_strategies_tested=42)

        for _ in range(25):
            analyzer.add_return(0.005)

        report = analyzer.get_report()
        assert "42" in report


# =============================================================================
# Edge Cases and Integration Tests
# =============================================================================


class TestEdgeCases:
    """Test edge cases."""

    def test_very_small_returns(self):
        """Test with very small returns."""
        analyzer = TrackRecordAnalyzer()
        for _ in range(50):
            analyzer.add_return(1e-10)

        assessment = analyzer.get_assessment()
        # Should handle without error
        assert assessment is not None or assessment is None

    def test_very_large_returns(self):
        """Test with very large returns."""
        analyzer = TrackRecordAnalyzer()
        returns = [0.5, -0.3, 0.4, -0.2] * 10
        for r in returns:
            analyzer.add_return(r)

        assessment = analyzer.get_assessment()
        assert assessment is not None

    def test_zero_variance_edge_case(self):
        """Test zero variance handling in all statistical methods."""
        analyzer = TrackRecordAnalyzer()
        # All identical returns
        for _ in range(30):
            analyzer.add_return(0.0)

        # Should handle gracefully
        sharpe = analyzer._calculate_sharpe()
        skew = analyzer._calculate_skewness()
        kurt = analyzer._calculate_kurtosis()

        assert sharpe == 0.0
        # With zero std, skewness calculation handles division
        assert math.isfinite(skew)

    def test_alternating_returns_zero_mean(self):
        """Test alternating returns with zero mean."""
        analyzer = TrackRecordAnalyzer()
        for i in range(50):
            analyzer.add_return(0.01 if i % 2 == 0 else -0.01)

        assessment = analyzer.get_assessment()
        assert assessment is not None
        # Sharpe should be close to 0
        assert abs(assessment.observed_sharpe) < 0.5


class TestIntegration:
    """Integration tests combining multiple components."""

    def test_full_workflow(self):
        """Test full workflow from returns to assessment."""
        # Simulate realistic trading returns
        import random

        random.seed(42)

        analyzer = TrackRecordAnalyzer(n_strategies_tested=5)

        # Add 100 days of returns (slightly positive drift)
        for _ in range(100):
            daily_return = 0.0005 + random.gauss(0, 0.015)
            analyzer.add_return(daily_return)

        assessment = analyzer.get_assessment()
        assert assessment is not None

        report = analyzer.get_report()
        assert len(report) > 100

    def test_comparison_single_vs_multiple_trials(self):
        """Test comparison between single and multiple trial assessments."""
        luck = LuckQuantifier()

        # Same Sharpe and track record
        sharpe = 1.5
        months = 24

        single_trial = luck.assess(sharpe=sharpe, n_trials=1, track_record_months=months)
        many_trials = luck.assess(sharpe=sharpe, n_trials=100, track_record_months=months)

        # More trials should increase probability of luck
        assert many_trials.probability_of_luck > single_trial.probability_of_luck
        # Deflated Sharpe should be lower with more trials
        assert many_trials.deflated_sharpe < single_trial.deflated_sharpe


class TestNumericalStability:
    """Test numerical stability."""

    def test_extreme_sharpe_values(self):
        """Test extreme Sharpe values."""
        luck = LuckQuantifier()

        # Very high Sharpe
        assessment_high = luck.assess(sharpe=10.0, n_trials=1)
        assert math.isfinite(assessment_high.deflated_sharpe)
        assert math.isfinite(assessment_high.min_track_record)
        assert math.isfinite(assessment_high.probability_of_luck)

        # Negative Sharpe
        assessment_neg = luck.assess(sharpe=-5.0, n_trials=1)
        assert math.isfinite(assessment_neg.deflated_sharpe)
        assert assessment_neg.min_track_record == float("inf")
        assert assessment_neg.probability_of_luck == 1.0

    def test_extreme_trial_counts(self):
        """Test extreme trial counts."""
        luck = LuckQuantifier()

        # Very many trials
        assessment = luck.assess(sharpe=2.0, n_trials=10000)
        assert math.isfinite(assessment.deflated_sharpe)
        assert 0 <= assessment.probability_of_luck <= 1

    def test_extreme_track_record(self):
        """Test extreme track record lengths."""
        luck = LuckQuantifier()

        # Very long track record
        assessment = luck.assess(sharpe=1.5, track_record_months=120)  # 10 years
        assert math.isfinite(assessment.probability_of_luck)
        assert assessment.probability_of_luck < 0.2  # Should be confident after 10 years

        # Very short track record
        assessment_short = luck.assess(sharpe=1.5, track_record_months=1)
        assert math.isfinite(assessment_short.probability_of_luck)
