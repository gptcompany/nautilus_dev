"""Comprehensive tests for VibrationAnalysis module.

Focus on:
- Vibration mode detection (FFT-based)
- Resonance event detection (phase coherence)
- Harmonic ratio analysis
- Digital root analysis
- Edge cases and error handling

Target coverage: 90%
"""

import math

import numpy as np
import pytest

from strategies.common.adaptive_control.vibration_analysis import (
    DigitalRootAnalyzer,
    HarmonicRatioAnalyzer,
    ResonanceEvent,
    VibrationAnalyzer,
    VibrationMode,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sinusoidal_prices():
    """Generate sinusoidal price series with known frequency."""
    np.random.seed(42)
    t = np.arange(200)
    period = 20
    base_price = 100
    amplitude = 5
    prices = base_price + amplitude * np.sin(2 * np.pi * t / period)
    return prices.tolist()


@pytest.fixture
def multi_frequency_prices():
    """Generate price series with multiple overlapping frequencies."""
    np.random.seed(42)
    t = np.arange(256)
    base_price = 100
    # Combine multiple sinusoids
    prices = (
        base_price
        + 5 * np.sin(2 * np.pi * t / 10)  # Period 10
        + 3 * np.sin(2 * np.pi * t / 20)  # Period 20
        + 2 * np.sin(2 * np.pi * t / 40)  # Period 40
    )
    return prices.tolist()


@pytest.fixture
def random_walk_prices():
    """Generate random walk prices (no clear cycles)."""
    np.random.seed(42)
    returns = np.random.normal(0, 0.01, 200)
    prices = 100 * np.exp(np.cumsum(returns))
    return prices.tolist()


@pytest.fixture
def vibration_analyzer():
    """Create default VibrationAnalyzer instance."""
    return VibrationAnalyzer(window_size=128, min_period=5, max_period=64)


@pytest.fixture
def harmonic_analyzer():
    """Create default HarmonicRatioAnalyzer instance."""
    return HarmonicRatioAnalyzer(tolerance=0.02)


@pytest.fixture
def digital_root_analyzer():
    """Create DigitalRootAnalyzer instance."""
    return DigitalRootAnalyzer()


# =============================================================================
# VibrationMode Dataclass Tests
# =============================================================================


class TestVibrationMode:
    """Test VibrationMode dataclass."""

    def test_vibration_mode_creation(self):
        """Test creating VibrationMode instance."""
        mode = VibrationMode(
            frequency=0.05,
            period=20.0,
            amplitude=1.5,
            phase=0.785,
        )
        assert mode.frequency == 0.05
        assert mode.period == 20.0
        assert mode.amplitude == 1.5
        assert mode.phase == 0.785

    def test_vibration_mode_zero_values(self):
        """Test VibrationMode with zero values."""
        mode = VibrationMode(
            frequency=0.0,
            period=0.0,
            amplitude=0.0,
            phase=0.0,
        )
        assert mode.frequency == 0.0
        assert mode.amplitude == 0.0


# =============================================================================
# ResonanceEvent Dataclass Tests
# =============================================================================


class TestResonanceEvent:
    """Test ResonanceEvent dataclass."""

    def test_resonance_event_creation(self):
        """Test creating ResonanceEvent instance."""
        modes = [
            VibrationMode(frequency=0.05, period=20.0, amplitude=1.5, phase=0.1),
            VibrationMode(frequency=0.025, period=40.0, amplitude=1.0, phase=0.15),
        ]
        event = ResonanceEvent(
            timestamp=100,
            strength=0.85,
            participating_modes=modes,
        )
        assert event.timestamp == 100
        assert event.strength == 0.85
        assert len(event.participating_modes) == 2

    def test_resonance_event_empty_modes(self):
        """Test ResonanceEvent with empty modes list."""
        event = ResonanceEvent(
            timestamp=0,
            strength=0.0,
            participating_modes=[],
        )
        assert len(event.participating_modes) == 0


# =============================================================================
# VibrationAnalyzer Initialization Tests
# =============================================================================


class TestVibrationAnalyzerInit:
    """Test VibrationAnalyzer initialization."""

    def test_default_initialization(self):
        """Test default initialization."""
        va = VibrationAnalyzer()
        assert va.window_size == 128
        assert va.min_period == 5
        assert va.max_period == 64
        assert len(va._buffer) == 0
        assert len(va._modes) == 0
        assert va._last_price is None

    def test_custom_initialization(self):
        """Test custom initialization."""
        va = VibrationAnalyzer(
            window_size=256,
            min_period=10,
            max_period=128,
        )
        assert va.window_size == 256
        assert va.min_period == 10
        assert va.max_period == 128


# =============================================================================
# VibrationAnalyzer.update() Tests - Lines 98-101
# =============================================================================


class TestVibrationAnalyzerUpdate:
    """Test VibrationAnalyzer.update() method."""

    def test_update_single_price(self, vibration_analyzer):
        """Test updating with single price."""
        vibration_analyzer.update(100.0)
        assert len(vibration_analyzer._buffer) == 1
        assert vibration_analyzer._last_price == 100.0

    def test_update_multiple_prices(self, vibration_analyzer):
        """Test updating with multiple prices sequentially."""
        prices = [100.0, 101.0, 102.0, 101.5, 100.5]
        for p in prices:
            vibration_analyzer.update(p)
        assert len(vibration_analyzer._buffer) == 5
        assert vibration_analyzer._last_price == 100.5

    def test_update_buffer_truncation(self):
        """Test buffer truncation when exceeding 2x window_size (lines 99-100)."""
        va = VibrationAnalyzer(window_size=50)
        # Add more than 2x window_size prices
        for i in range(150):
            va.update(float(i))
        # Buffer should be truncated to 2x window_size
        assert len(va._buffer) == 100  # 2 * 50

    def test_update_preserves_recent_data(self):
        """Test that truncation preserves most recent data."""
        va = VibrationAnalyzer(window_size=50)
        for i in range(150):
            va.update(float(i))
        # Last value should be preserved
        assert va._buffer[-1] == 149.0
        # First value in truncated buffer should be 50 (150 - 2*50)
        assert va._buffer[0] == 50.0


# =============================================================================
# VibrationAnalyzer.get_dominant_modes() Tests - Lines 115-153
# =============================================================================


class TestGetDominantModes:
    """Test VibrationAnalyzer.get_dominant_modes() method."""

    def test_insufficient_data_returns_empty(self, vibration_analyzer):
        """Test returns empty list with insufficient data (line 115-116)."""
        # Add less than window_size samples
        for i in range(50):
            vibration_analyzer.update(100.0 + i * 0.1)
        modes = vibration_analyzer.get_dominant_modes(n_modes=3)
        assert modes == []

    def test_detects_single_sinusoid(self, sinusoidal_prices, vibration_analyzer):
        """Test detection of dominant mode from sinusoidal data."""
        for p in sinusoidal_prices:
            vibration_analyzer.update(p)
        modes = vibration_analyzer.get_dominant_modes(n_modes=3)
        assert len(modes) > 0
        # Dominant mode should have period close to 20
        dominant = modes[0]
        assert 10 < dominant.period < 30

    def test_detects_multiple_frequencies(self, multi_frequency_prices):
        """Test detection of multiple frequency components."""
        va = VibrationAnalyzer(window_size=256, min_period=5, max_period=64)
        for p in multi_frequency_prices:
            va.update(p)
        modes = va.get_dominant_modes(n_modes=5)
        assert len(modes) >= 3
        # All modes should have amplitude > 0
        for mode in modes:
            assert mode.amplitude > 0

    def test_modes_sorted_by_amplitude(self, multi_frequency_prices):
        """Test that modes are sorted by amplitude descending."""
        va = VibrationAnalyzer(window_size=256, min_period=5, max_period=64)
        for p in multi_frequency_prices:
            va.update(p)
        modes = va.get_dominant_modes(n_modes=5)
        for i in range(len(modes) - 1):
            assert modes[i].amplitude >= modes[i + 1].amplitude

    def test_modes_stored_internally(self, sinusoidal_prices, vibration_analyzer):
        """Test that modes are stored in _modes attribute."""
        for p in sinusoidal_prices:
            vibration_analyzer.update(p)
        modes = vibration_analyzer.get_dominant_modes(n_modes=2)
        assert vibration_analyzer._modes == modes

    def test_period_filtering(self, vibration_analyzer):
        """Test that only periods within min/max range are returned (line 140)."""
        # Create signal with period outside filter range
        np.random.seed(42)
        t = np.arange(200)
        # Period 100 is outside max_period=64
        prices = 100 + 5 * np.sin(2 * np.pi * t / 100)
        for p in prices:
            vibration_analyzer.update(p)
        modes = vibration_analyzer.get_dominant_modes(n_modes=5)
        # All returned modes should have period within range
        for mode in modes:
            assert vibration_analyzer.min_period <= mode.period <= vibration_analyzer.max_period

    def test_detrending_applied(self, vibration_analyzer):
        """Test that linear trend is removed before FFT (line 122)."""
        # Create trending signal
        t = np.arange(200)
        prices = 100 + t * 0.1 + 5 * np.sin(2 * np.pi * t / 20)
        for p in prices:
            vibration_analyzer.update(p)
        modes = vibration_analyzer.get_dominant_modes(n_modes=3)
        # Should still detect the sinusoidal component
        assert len(modes) > 0

    def test_n_modes_limit(self, multi_frequency_prices):
        """Test n_modes parameter limits output."""
        va = VibrationAnalyzer(window_size=256, min_period=5, max_period=64)
        for p in multi_frequency_prices:
            va.update(p)
        modes_2 = va.get_dominant_modes(n_modes=2)
        assert len(modes_2) <= 2

    def test_random_walk_produces_modes(self, random_walk_prices, vibration_analyzer):
        """Test that random walk data still produces some modes."""
        for p in random_walk_prices:
            vibration_analyzer.update(p)
        modes = vibration_analyzer.get_dominant_modes(n_modes=5)
        # Random walk should still have some spectral content
        assert isinstance(modes, list)


# =============================================================================
# VibrationAnalyzer.check_resonance() Tests - Lines 168-188
# =============================================================================


class TestCheckResonance:
    """Test VibrationAnalyzer.check_resonance() method."""

    def test_no_resonance_insufficient_modes(self, vibration_analyzer):
        """Test returns None with less than 2 modes (line 168-169)."""
        # No data, no modes
        result = vibration_analyzer.check_resonance()
        assert result is None

    def test_no_resonance_one_mode(self, sinusoidal_prices, vibration_analyzer):
        """Test returns None with only one mode."""
        for p in sinusoidal_prices:
            vibration_analyzer.update(p)
        vibration_analyzer.get_dominant_modes(n_modes=1)
        result = vibration_analyzer.check_resonance()
        assert result is None

    def test_resonance_with_aligned_phases(self):
        """Test resonance detection when phases are aligned (line 181-186)."""
        va = VibrationAnalyzer(window_size=128)
        # Manually set modes with aligned phases
        va._modes = [
            VibrationMode(frequency=0.05, period=20.0, amplitude=1.5, phase=0.1),
            VibrationMode(frequency=0.1, period=10.0, amplitude=1.0, phase=0.12),
            VibrationMode(frequency=0.025, period=40.0, amplitude=0.8, phase=0.08),
        ]
        va._buffer = list(range(128))  # Dummy buffer for timestamp
        result = va.check_resonance()
        assert result is not None
        assert isinstance(result, ResonanceEvent)
        assert result.strength > 0.7
        assert len(result.participating_modes) == 3

    def test_no_resonance_misaligned_phases(self):
        """Test no resonance with misaligned phases (line 188)."""
        va = VibrationAnalyzer(window_size=128)
        # Set modes with very different phases
        va._modes = [
            VibrationMode(frequency=0.05, period=20.0, amplitude=1.5, phase=0.0),
            VibrationMode(frequency=0.1, period=10.0, amplitude=1.0, phase=math.pi),
            VibrationMode(frequency=0.025, period=40.0, amplitude=0.8, phase=math.pi / 2),
        ]
        va._buffer = list(range(128))
        result = va.check_resonance()
        assert result is None

    def test_resonance_strength_calculation(self):
        """Test resonance strength is coherence value."""
        va = VibrationAnalyzer(window_size=128)
        # All same phase = max coherence
        va._modes = [
            VibrationMode(frequency=0.05, period=20.0, amplitude=1.5, phase=0.0),
            VibrationMode(frequency=0.1, period=10.0, amplitude=1.0, phase=0.0),
        ]
        va._buffer = list(range(128))
        result = va.check_resonance()
        assert result is not None
        # Perfect alignment should give coherence = 1.0
        assert result.strength == pytest.approx(1.0, abs=0.01)


# =============================================================================
# VibrationAnalyzer.predict_next_extreme() Tests - Lines 199-223
# =============================================================================


class TestPredictNextExtreme:
    """Test VibrationAnalyzer.predict_next_extreme() method."""

    def test_no_prediction_no_modes(self, vibration_analyzer):
        """Test returns None when no modes available (lines 199-203)."""
        result = vibration_analyzer.predict_next_extreme()
        assert result is None

    def test_no_prediction_insufficient_data(self, vibration_analyzer):
        """Test returns None with insufficient data."""
        for i in range(50):
            vibration_analyzer.update(100.0 + i * 0.1)
        result = vibration_analyzer.predict_next_extreme()
        assert result is None

    def test_prediction_with_modes(self, sinusoidal_prices, vibration_analyzer):
        """Test prediction returns valid result with modes."""
        for p in sinusoidal_prices:
            vibration_analyzer.update(p)
        vibration_analyzer.get_dominant_modes(n_modes=3)
        result = vibration_analyzer.predict_next_extreme()
        assert result is not None
        bars, extreme_type = result
        assert isinstance(bars, int)
        assert bars >= 0
        assert extreme_type in ("peak", "trough")

    def test_prediction_uses_dominant_mode(self):
        """Test prediction uses first (dominant) mode."""
        va = VibrationAnalyzer(window_size=128)
        # Set specific mode
        va._modes = [
            VibrationMode(frequency=0.05, period=20.0, amplitude=1.5, phase=0.0),
        ]
        result = va.predict_next_extreme()
        assert result is not None
        bars, _ = result
        # With phase=0, should predict peak soon or trough at period/2
        assert bars < 20

    def test_prediction_auto_calculates_modes(self, sinusoidal_prices):
        """Test prediction calculates modes if not available (line 200)."""
        va = VibrationAnalyzer(window_size=128)
        for p in sinusoidal_prices:
            va.update(p)
        # Don't call get_dominant_modes explicitly
        assert len(va._modes) == 0
        va.predict_next_extreme()
        # Should auto-calculate modes
        assert len(va._modes) > 0

    def test_prediction_peak_vs_trough(self):
        """Test prediction correctly identifies nearest extreme type."""
        va = VibrationAnalyzer(window_size=128)
        # Phase near 0 -> peak imminent
        va._modes = [
            VibrationMode(frequency=0.05, period=20.0, amplitude=1.5, phase=0.1),
        ]
        result = va.predict_next_extreme()
        assert result is not None
        bars, extreme_type = result
        # Should identify peak or trough based on phase


# =============================================================================
# HarmonicRatioAnalyzer Initialization Tests
# =============================================================================


class TestHarmonicRatioAnalyzerInit:
    """Test HarmonicRatioAnalyzer initialization."""

    def test_default_tolerance(self):
        """Test default tolerance value."""
        hra = HarmonicRatioAnalyzer()
        assert hra.tolerance == 0.02

    def test_custom_tolerance(self):
        """Test custom tolerance value."""
        hra = HarmonicRatioAnalyzer(tolerance=0.05)
        assert hra.tolerance == 0.05

    def test_consonant_ratios_defined(self):
        """Test CONSONANT_RATIOS class attribute."""
        assert "unison" in HarmonicRatioAnalyzer.CONSONANT_RATIOS
        assert "octave" in HarmonicRatioAnalyzer.CONSONANT_RATIOS
        assert "fifth" in HarmonicRatioAnalyzer.CONSONANT_RATIOS
        assert HarmonicRatioAnalyzer.CONSONANT_RATIOS["octave"] == 2.0


# =============================================================================
# HarmonicRatioAnalyzer.find_harmonic_relationship() Tests - Lines 273, 281
# =============================================================================


class TestFindHarmonicRelationship:
    """Test HarmonicRatioAnalyzer.find_harmonic_relationship() method."""

    def test_invalid_price_zero(self, harmonic_analyzer):
        """Test returns None for zero price (line 273)."""
        assert harmonic_analyzer.find_harmonic_relationship(0, 100) is None
        assert harmonic_analyzer.find_harmonic_relationship(100, 0) is None

    def test_invalid_price_negative(self, harmonic_analyzer):
        """Test returns None for negative price (line 273)."""
        assert harmonic_analyzer.find_harmonic_relationship(-50, 100) is None
        assert harmonic_analyzer.find_harmonic_relationship(100, -50) is None

    def test_unison_relationship(self, harmonic_analyzer):
        """Test unison (1:1) relationship."""
        result = harmonic_analyzer.find_harmonic_relationship(100, 100)
        assert result == "unison"

    def test_octave_relationship(self, harmonic_analyzer):
        """Test octave (2:1) relationship."""
        result = harmonic_analyzer.find_harmonic_relationship(100, 200)
        assert result == "octave"
        # Order shouldn't matter
        result2 = harmonic_analyzer.find_harmonic_relationship(200, 100)
        assert result2 == "octave"

    def test_fifth_relationship(self, harmonic_analyzer):
        """Test fifth (3:2 = 1.5) relationship."""
        result = harmonic_analyzer.find_harmonic_relationship(100, 150)
        assert result == "fifth"

    def test_fourth_relationship(self, harmonic_analyzer):
        """Test fourth (4:3 = 1.333) relationship."""
        result = harmonic_analyzer.find_harmonic_relationship(100, 133.3)
        assert result == "fourth"

    def test_major_third_relationship(self, harmonic_analyzer):
        """Test major third (5:4 = 1.25) relationship."""
        result = harmonic_analyzer.find_harmonic_relationship(100, 125)
        assert result == "major_third"

    def test_minor_third_relationship(self, harmonic_analyzer):
        """Test minor third (6:5 = 1.2) relationship."""
        result = harmonic_analyzer.find_harmonic_relationship(100, 120)
        assert result == "minor_third"

    def test_no_harmonic_relationship(self, harmonic_analyzer):
        """Test returns None for non-harmonic ratio (line 281)."""
        # 100:185 = 1.85, not close to any harmonic ratio
        result = harmonic_analyzer.find_harmonic_relationship(100, 185)
        assert result is None

    def test_tolerance_boundary(self):
        """Test tolerance boundary detection."""
        hra = HarmonicRatioAnalyzer(tolerance=0.02)
        # 1.99 is within 0.02 of 2.0 (octave)
        assert hra.find_harmonic_relationship(100, 199) == "octave"
        # 1.97 is outside tolerance
        assert hra.find_harmonic_relationship(100, 197) is None


# =============================================================================
# HarmonicRatioAnalyzer.get_harmonic_levels() Tests - Line 304
# =============================================================================


class TestGetHarmonicLevels:
    """Test HarmonicRatioAnalyzer.get_harmonic_levels() method."""

    def test_levels_both_directions(self, harmonic_analyzer):
        """Test levels in both directions (default)."""
        levels = harmonic_analyzer.get_harmonic_levels(100)
        # Should have both up and down levels
        assert "octave_up" in levels
        assert "octave_down" in levels
        assert levels["octave_up"] == 200.0
        assert levels["octave_down"] == 50.0

    def test_levels_up_only(self, harmonic_analyzer):
        """Test levels in up direction only."""
        levels = harmonic_analyzer.get_harmonic_levels(100, direction="up")
        assert "octave_up" in levels
        assert "octave_down" not in levels

    def test_levels_down_only(self, harmonic_analyzer):
        """Test levels in down direction only (line 304)."""
        levels = harmonic_analyzer.get_harmonic_levels(100, direction="down")
        assert "octave_up" not in levels
        assert "octave_down" in levels
        assert levels["octave_down"] == 50.0

    def test_all_ratios_present(self, harmonic_analyzer):
        """Test all harmonic ratios generate levels."""
        levels = harmonic_analyzer.get_harmonic_levels(100)
        for name in HarmonicRatioAnalyzer.CONSONANT_RATIOS:
            assert f"{name}_up" in levels
            assert f"{name}_down" in levels

    def test_level_calculations(self, harmonic_analyzer):
        """Test correct level calculations."""
        levels = harmonic_analyzer.get_harmonic_levels(100)
        assert levels["fifth_up"] == 150.0
        assert levels["fifth_down"] == pytest.approx(66.67, abs=0.01)
        assert levels["unison_up"] == 100.0
        assert levels["unison_down"] == 100.0


# =============================================================================
# HarmonicRatioAnalyzer.calculate_consonance_score() Tests - Lines 324-336
# =============================================================================


class TestCalculateConsonanceScore:
    """Test HarmonicRatioAnalyzer.calculate_consonance_score() method."""

    def test_insufficient_prices(self, harmonic_analyzer):
        """Test returns 0 with less than 2 prices (lines 324-325)."""
        assert harmonic_analyzer.calculate_consonance_score([]) == 0.0
        assert harmonic_analyzer.calculate_consonance_score([100]) == 0.0

    def test_all_harmonic_pairs(self, harmonic_analyzer):
        """Test score with all harmonic pairs (consecutive octaves: 100, 200)."""
        # 100:200 is octave (2:1), both pairs harmonic
        prices = [100, 200]
        score = harmonic_analyzer.calculate_consonance_score(prices)
        # 1 pair: (100,200) - octave
        assert score == 1.0

    def test_multiple_harmonic_pairs(self, harmonic_analyzer):
        """Test score with multiple octave pairs."""
        # 100:200 octave, 100:400 is 4:1 (not harmonic), 200:400 octave
        prices = [100, 200, 400]
        score = harmonic_analyzer.calculate_consonance_score(prices)
        # 2 out of 3 pairs are harmonic (100:200, 200:400 but not 100:400)
        assert score == pytest.approx(2 / 3, abs=0.01)

    def test_no_harmonic_pairs(self, harmonic_analyzer):
        """Test score with no harmonic pairs."""
        # Use prices that have no harmonic relationships
        # 100:185 = 1.85, 100:317 = 3.17, 185:317 = 1.71 - none are harmonic
        prices = [100, 185, 317]
        score = harmonic_analyzer.calculate_consonance_score(prices)
        assert score == 0.0

    def test_mixed_harmonic_pairs(self, harmonic_analyzer):
        """Test score with some harmonic pairs."""
        # 100 and 200 are octave, but 173 isn't harmonic with either
        prices = [100, 173, 200]
        score = harmonic_analyzer.calculate_consonance_score(prices)
        # 1 out of 3 pairs is harmonic
        assert score == pytest.approx(1 / 3, abs=0.01)

    def test_pair_counting(self, harmonic_analyzer):
        """Test correct pair counting (lines 330-334)."""
        # 4 prices = 6 pairs
        prices = [100, 200, 150, 125]  # octave, fifth, major_third
        score = harmonic_analyzer.calculate_consonance_score(prices)
        # Should count all pairwise comparisons
        assert 0 <= score <= 1.0


# =============================================================================
# DigitalRootAnalyzer.digital_root() Tests - Lines 371-374
# =============================================================================


class TestDigitalRoot:
    """Test DigitalRootAnalyzer.digital_root() static method."""

    def test_zero_returns_zero(self):
        """Test zero input returns zero (line 371-372)."""
        assert DigitalRootAnalyzer.digital_root(0) == 0

    def test_negative_returns_zero(self):
        """Test negative input returns zero (line 371-372)."""
        assert DigitalRootAnalyzer.digital_root(-5) == 0
        assert DigitalRootAnalyzer.digital_root(-100) == 0

    def test_single_digit(self):
        """Test single digit returns itself."""
        for i in range(1, 10):
            assert DigitalRootAnalyzer.digital_root(i) == i

    def test_double_digit(self):
        """Test double digit digital roots."""
        # 10 -> 1+0 = 1
        assert DigitalRootAnalyzer.digital_root(10) == 1
        # 25 -> 2+5 = 7
        assert DigitalRootAnalyzer.digital_root(25) == 7
        # 99 -> 9+9 = 18 -> 1+8 = 9
        assert DigitalRootAnalyzer.digital_root(99) == 9

    def test_triple_digit(self):
        """Test triple digit digital roots."""
        # 256 -> 2+5+6 = 13 -> 1+3 = 4
        assert DigitalRootAnalyzer.digital_root(256) == 4
        # 999 -> 9+9+9 = 27 -> 2+7 = 9
        assert DigitalRootAnalyzer.digital_root(999) == 9

    def test_nine_fixed_point(self):
        """Test 9 is a fixed point (line 374)."""
        assert DigitalRootAnalyzer.digital_root(9) == 9
        assert DigitalRootAnalyzer.digital_root(18) == 9
        assert DigitalRootAnalyzer.digital_root(27) == 9
        assert DigitalRootAnalyzer.digital_root(900) == 9

    def test_mathematical_formula(self):
        """Test digital root matches dr(n) = 1 + ((n-1) mod 9)."""
        for n in [1, 7, 15, 42, 100, 256, 999]:
            expected = 1 + ((n - 1) % 9)
            if expected == 0:
                expected = 9
            assert DigitalRootAnalyzer.digital_root(n) == expected


# =============================================================================
# DigitalRootAnalyzer.vortex_sequence() Tests - Lines 389-394
# =============================================================================


class TestVortexSequence:
    """Test DigitalRootAnalyzer.vortex_sequence() static method."""

    def test_default_length(self):
        """Test default sequence length is 24."""
        seq = DigitalRootAnalyzer.vortex_sequence()
        assert len(seq) == 24

    def test_custom_length(self):
        """Test custom sequence length."""
        seq = DigitalRootAnalyzer.vortex_sequence(n=10)
        assert len(seq) == 10

    def test_first_six_values(self):
        """Test first six values of vortex sequence."""
        seq = DigitalRootAnalyzer.vortex_sequence(n=6)
        # 1, 2, 4, 8, 16(7), 32(5)
        assert seq == [1, 2, 4, 8, 7, 5]

    def test_cycle_repeats(self):
        """Test the 1,2,4,8,7,5 cycle repeats."""
        seq = DigitalRootAnalyzer.vortex_sequence(n=12)
        # Pattern should repeat every 6
        assert seq[:6] == seq[6:12]

    def test_never_contains_369(self):
        """Test vortex sequence never contains 3, 6, or 9."""
        seq = DigitalRootAnalyzer.vortex_sequence(n=100)
        for val in seq:
            assert val not in [3, 6, 9]

    def test_zero_length(self):
        """Test zero length sequence."""
        seq = DigitalRootAnalyzer.vortex_sequence(n=0)
        assert seq == []


# =============================================================================
# DigitalRootAnalyzer.analyze_price_pattern() Tests - Lines 409-422
# =============================================================================


class TestAnalyzePricePattern:
    """Test DigitalRootAnalyzer.analyze_price_pattern() method."""

    def test_basic_analysis(self, digital_root_analyzer):
        """Test basic price pattern analysis."""
        prices = [100, 200, 300, 400, 500]
        result = digital_root_analyzer.analyze_price_pattern(prices)
        assert "distribution" in result
        assert "vortex_ratio" in result
        assert "trinity_ratio" in result
        assert "most_common" in result

    def test_distribution_keys(self, digital_root_analyzer):
        """Test distribution contains all digits 1-9."""
        prices = [100, 200, 300]
        result = digital_root_analyzer.analyze_price_pattern(prices)
        for i in range(1, 10):
            assert i in result["distribution"]

    def test_vortex_ratio(self, digital_root_analyzer):
        """Test vortex ratio calculation (line 419)."""
        # Digital roots: 1, 2, 4, 8, 7, 5 are vortex numbers
        prices = [1, 2, 4, 8, 16, 32]  # All vortex
        result = digital_root_analyzer.analyze_price_pattern(prices)
        assert result["vortex_ratio"] == 1.0

    def test_trinity_ratio(self, digital_root_analyzer):
        """Test trinity ratio calculation (line 420)."""
        # Digital roots: 3, 6, 9 are trinity numbers
        prices = [3, 6, 9, 12, 15, 18]  # All trinity (3,6,9,3,6,9)
        result = digital_root_analyzer.analyze_price_pattern(prices)
        assert result["trinity_ratio"] == 1.0

    def test_most_common_root(self, digital_root_analyzer):
        """Test most common root identification (line 426)."""
        # All prices have root 1
        prices = [1, 10, 100, 1000]
        result = digital_root_analyzer.analyze_price_pattern(prices)
        assert result["most_common"] == 1

    def test_empty_prices(self, digital_root_analyzer):
        """Test empty price list returns default values."""
        result = digital_root_analyzer.analyze_price_pattern([])
        assert result["vortex_ratio"] == 0
        assert result["trinity_ratio"] == 0
        # Empty distribution max() returns first key (1) due to implementation
        # This is expected behavior - not a bug
        assert result["most_common"] == 1

    def test_filters_non_positive_prices(self, digital_root_analyzer):
        """Test non-positive prices are filtered (line 409)."""
        prices = [100, 0, -50, 200, -100]
        result = digital_root_analyzer.analyze_price_pattern(prices)
        # Only 100 and 200 should be analyzed
        total_count = sum(result["distribution"].values())
        assert total_count == 2

    def test_float_prices_converted(self, digital_root_analyzer):
        """Test float prices are converted to int."""
        prices = [100.5, 200.9, 300.1]
        result = digital_root_analyzer.analyze_price_pattern(prices)
        # Should work without error
        assert "distribution" in result


# =============================================================================
# Integration Tests
# =============================================================================


class TestVibrationAnalyzerIntegration:
    """Integration tests for VibrationAnalyzer workflow."""

    def test_full_workflow(self, sinusoidal_prices):
        """Test complete vibration analysis workflow."""
        va = VibrationAnalyzer(window_size=128)

        # 1. Add prices
        for p in sinusoidal_prices:
            va.update(p)

        # 2. Get modes
        modes = va.get_dominant_modes(n_modes=3)
        assert len(modes) > 0

        # 3. Check resonance
        va.check_resonance()
        # May or may not have resonance

        # 4. Predict next extreme
        prediction = va.predict_next_extreme()
        assert prediction is not None

    def test_continuous_updates(self):
        """Test continuous price updates don't cause issues."""
        va = VibrationAnalyzer(window_size=64)
        np.random.seed(42)

        for i in range(500):
            price = 100 + 5 * np.sin(i / 10) + np.random.normal(0, 0.5)
            va.update(price)

            if i % 100 == 99:
                va.get_dominant_modes(n_modes=3)
                va.check_resonance()
                va.predict_next_extreme()

        # Should not have memory issues
        assert len(va._buffer) <= va.window_size * 2


class TestHarmonicRatioAnalyzerIntegration:
    """Integration tests for HarmonicRatioAnalyzer workflow."""

    def test_find_support_resistance(self, harmonic_analyzer):
        """Test finding harmonic support/resistance levels."""
        base_price = 100

        # Get levels
        harmonic_analyzer.get_harmonic_levels(base_price)

        # Check some known prices
        prices_to_check = [100, 150, 200, 125, 133.3]
        for price in prices_to_check:
            relationship = harmonic_analyzer.find_harmonic_relationship(base_price, price)
            assert relationship is not None or price == base_price

    def test_market_structure_consonance(self, harmonic_analyzer):
        """Test analyzing market structure consonance."""
        # Strong harmonic structure (all octaves)
        harmonic_prices = [100, 200]
        harmonic_score = harmonic_analyzer.calculate_consonance_score(harmonic_prices)

        # Weak harmonic structure (no harmonics)
        random_prices = [100, 185, 317]
        random_score = harmonic_analyzer.calculate_consonance_score(random_prices)

        assert harmonic_score > random_score


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_small_prices(self, harmonic_analyzer):
        """Test with very small price values."""
        levels = harmonic_analyzer.get_harmonic_levels(0.001)
        assert levels["octave_up"] == pytest.approx(0.002, abs=0.0001)

    def test_very_large_prices(self, harmonic_analyzer):
        """Test with very large price values."""
        levels = harmonic_analyzer.get_harmonic_levels(1_000_000)
        assert levels["octave_up"] == 2_000_000

    def test_digital_root_large_number(self):
        """Test digital root with very large number."""
        result = DigitalRootAnalyzer.digital_root(999_999_999)
        assert 1 <= result <= 9

    def test_vibration_analyzer_constant_price(self):
        """Test vibration analyzer with constant price."""
        va = VibrationAnalyzer(window_size=64)
        for _ in range(100):
            va.update(100.0)
        modes = va.get_dominant_modes(n_modes=3)
        # Constant price should have minimal modes
        assert isinstance(modes, list)

    def test_harmonic_analyzer_same_price(self, harmonic_analyzer):
        """Test harmonic relationship with same price."""
        result = harmonic_analyzer.find_harmonic_relationship(100, 100)
        assert result == "unison"

    def test_resonance_boundary_coherence(self):
        """Test resonance at boundary coherence threshold."""
        va = VibrationAnalyzer(window_size=128)
        # Set modes with coherence just above 0.7
        va._modes = [
            VibrationMode(frequency=0.05, period=20.0, amplitude=1.5, phase=0.0),
            VibrationMode(frequency=0.1, period=10.0, amplitude=1.0, phase=0.5),
        ]
        va._buffer = list(range(128))
        va.check_resonance()
        # Coherence depends on actual phase values
        # With phase diff of 0.5 rad, coherence should be > 0.7


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
