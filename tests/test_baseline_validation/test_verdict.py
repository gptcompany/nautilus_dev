"""Unit tests for verdict logic.

Tests for:
    - GO/WAIT/STOP verdict determination
    - Confidence level calculation
    - Recommendation generation

TDD: Tests written first to define expected behavior.
"""

from __future__ import annotations


class TestVerdictDetermination:
    """Tests for GO/WAIT/STOP verdict determination."""

    def test_go_when_adaptive_beats_fixed_with_edge(self) -> None:
        """Test GO verdict when adaptive beats fixed by sharpe_edge threshold."""
        from scripts.baseline_validation.verdict import determine_verdict, Verdict

        # Adaptive Sharpe = 1.5, Fixed Sharpe = 1.2
        # Edge = 1.5 - 1.2 = 0.3 > 0.2 threshold
        verdict = determine_verdict(
            adaptive_sharpe=1.5,
            fixed_sharpe=1.2,
            adaptive_max_dd=0.15,
            fixed_max_dd=0.18,
            sharpe_edge_threshold=0.2,
        )

        assert verdict == Verdict.GO

    def test_stop_when_fixed_wins(self) -> None:
        """Test STOP verdict when fixed beats adaptive."""
        from scripts.baseline_validation.verdict import determine_verdict, Verdict

        # Fixed Sharpe = 1.3, Adaptive Sharpe = 1.0
        verdict = determine_verdict(
            adaptive_sharpe=1.0,
            fixed_sharpe=1.3,
            adaptive_max_dd=0.20,
            fixed_max_dd=0.15,
            sharpe_edge_threshold=0.2,
        )

        assert verdict == Verdict.STOP

    def test_wait_when_edge_insufficient(self) -> None:
        """Test WAIT verdict when edge is below threshold."""
        from scripts.baseline_validation.verdict import determine_verdict, Verdict

        # Adaptive Sharpe = 1.3, Fixed Sharpe = 1.2
        # Edge = 0.1 < 0.2 threshold
        verdict = determine_verdict(
            adaptive_sharpe=1.3,
            fixed_sharpe=1.2,
            adaptive_max_dd=0.15,
            fixed_max_dd=0.15,
            sharpe_edge_threshold=0.2,
        )

        assert verdict == Verdict.WAIT

    def test_wait_when_adaptive_has_worse_drawdown(self) -> None:
        """Test WAIT verdict when adaptive has worse drawdown despite better Sharpe."""
        from scripts.baseline_validation.verdict import determine_verdict, Verdict

        # Adaptive wins Sharpe but has much worse drawdown
        verdict = determine_verdict(
            adaptive_sharpe=1.5,
            fixed_sharpe=1.2,
            adaptive_max_dd=0.30,  # Much worse
            fixed_max_dd=0.15,
            sharpe_edge_threshold=0.2,
        )

        assert verdict == Verdict.WAIT


class TestConfidenceLevelCalculation:
    """Tests for confidence level calculation."""

    def test_high_confidence_with_many_windows(self) -> None:
        """Test high confidence with many consistent windows."""
        from scripts.baseline_validation.verdict import calculate_confidence

        # 20 windows with consistent positive results
        window_sharpes = [1.2, 1.3, 1.1, 1.4, 1.2] * 4  # 20 windows

        confidence = calculate_confidence(
            window_sharpes=window_sharpes,
            p_value=0.01,  # Highly significant
        )

        assert confidence >= 0.8  # High confidence

    def test_low_confidence_with_few_windows(self) -> None:
        """Test low confidence with few windows."""
        from scripts.baseline_validation.verdict import calculate_confidence

        window_sharpes = [1.2, 1.3]  # Only 2 windows

        confidence = calculate_confidence(
            window_sharpes=window_sharpes,
            p_value=0.10,  # Not significant
        )

        # With only 2 windows and p=0.10, confidence should be moderate but not high
        assert confidence <= 0.6  # Moderate-low confidence

    def test_medium_confidence_with_mixed_results(self) -> None:
        """Test medium confidence with mixed window results."""
        from scripts.baseline_validation.verdict import calculate_confidence

        # Mixed results - some positive, some negative
        window_sharpes = [1.2, -0.5, 1.1, 0.3, -0.2, 1.0]

        confidence = calculate_confidence(
            window_sharpes=window_sharpes,
            p_value=0.05,
        )

        assert 0.3 <= confidence <= 0.7  # Medium confidence


class TestRecommendationGeneration:
    """Tests for recommendation text generation."""

    def test_go_recommendation_includes_deploy(self) -> None:
        """Test GO recommendation mentions deployment."""
        from scripts.baseline_validation.verdict import generate_recommendation, Verdict

        recommendation = generate_recommendation(
            verdict=Verdict.GO,
            adaptive_sharpe=1.5,
            fixed_sharpe=1.2,
            sharpe_edge=0.3,
        )

        assert "deploy" in recommendation.lower() or "adaptive" in recommendation.lower()

    def test_stop_recommendation_mentions_fixed(self) -> None:
        """Test STOP recommendation mentions using fixed sizing."""
        from scripts.baseline_validation.verdict import generate_recommendation, Verdict

        recommendation = generate_recommendation(
            verdict=Verdict.STOP,
            adaptive_sharpe=1.0,
            fixed_sharpe=1.3,
            sharpe_edge=-0.3,
        )

        assert "fixed" in recommendation.lower()

    def test_wait_recommendation_suggests_investigation(self) -> None:
        """Test WAIT recommendation suggests further investigation."""
        from scripts.baseline_validation.verdict import generate_recommendation, Verdict

        recommendation = generate_recommendation(
            verdict=Verdict.WAIT,
            adaptive_sharpe=1.2,
            fixed_sharpe=1.1,
            sharpe_edge=0.1,
        )

        assert any(
            word in recommendation.lower()
            for word in ["investigate", "more", "insufficient", "further"]
        )


class TestVerdictEdgeCases:
    """Tests for verdict edge cases."""

    def test_identical_sharpes(self) -> None:
        """Test verdict when Sharpes are identical."""
        from scripts.baseline_validation.verdict import determine_verdict, Verdict

        verdict = determine_verdict(
            adaptive_sharpe=1.2,
            fixed_sharpe=1.2,
            adaptive_max_dd=0.15,
            fixed_max_dd=0.15,
            sharpe_edge_threshold=0.2,
        )

        # Identical = no edge, so WAIT
        assert verdict == Verdict.WAIT

    def test_negative_sharpes(self) -> None:
        """Test verdict with negative Sharpe ratios."""
        from scripts.baseline_validation.verdict import determine_verdict, Verdict

        # Both losing, but fixed loses less
        verdict = determine_verdict(
            adaptive_sharpe=-0.5,
            fixed_sharpe=-0.2,
            adaptive_max_dd=0.25,
            fixed_max_dd=0.20,
            sharpe_edge_threshold=0.2,
        )

        assert verdict == Verdict.STOP

    def test_zero_sharpes(self) -> None:
        """Test verdict with zero Sharpe ratios."""
        from scripts.baseline_validation.verdict import determine_verdict, Verdict

        verdict = determine_verdict(
            adaptive_sharpe=0.0,
            fixed_sharpe=0.0,
            adaptive_max_dd=0.15,
            fixed_max_dd=0.15,
            sharpe_edge_threshold=0.2,
        )

        assert verdict == Verdict.WAIT
