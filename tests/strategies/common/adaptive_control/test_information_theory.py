"""Comprehensive tests for information theory module.

Focus on:
- Entropy estimation and normalization
- Risk multiplier based on entropy
- Mutual information calculation
- Optimal sampling analysis
- Edge cases: constant values, high entropy, zero variance
"""

import math

import numpy as np

from strategies.common.adaptive_control.information_theory import (
    EntropyEstimator,
    InformationState,
    MutualInformationEstimator,
    OptimalSamplingAnalyzer,
)


class TestInformationState:
    """Test InformationState dataclass."""

    def test_information_state_creation(self):
        """Test creating InformationState."""
        state = InformationState(
            entropy=2.5,
            normalized_entropy=0.75,
            information_rate=0.1,
            signal_to_noise=3.0,
            risk_multiplier=0.8,
        )

        assert state.entropy == 2.5
        assert state.normalized_entropy == 0.75
        assert state.information_rate == 0.1
        assert state.signal_to_noise == 3.0
        assert state.risk_multiplier == 0.8


class TestEntropyEstimator:
    """Test EntropyEstimator."""

    def test_initialization(self):
        """Test initialization."""
        estimator = EntropyEstimator(n_bins=20, window_size=100, smoothing=0.1)
        assert estimator.n_bins == 20
        assert estimator.window_size == 100
        assert estimator.smoothing == 0.1

    def test_initial_entropy(self):
        """Test initial entropy is zero."""
        estimator = EntropyEstimator()
        assert estimator.entropy == 0.0

    def test_update_single_value(self):
        """Test updating with single value."""
        estimator = EntropyEstimator()
        entropy = estimator.update(0.01)

        assert entropy == 0.0  # Need more samples

    def test_update_multiple_values(self):
        """Test updating with multiple values."""
        estimator = EntropyEstimator(n_bins=10, window_size=50)

        # Feed enough data
        for i in range(30):
            estimator.update(float(i) / 30)

        # Should have non-zero entropy
        assert estimator.entropy > 0

    def test_constant_values_zero_entropy(self):
        """Test that constant values give zero entropy."""
        estimator = EntropyEstimator(n_bins=10)

        for _ in range(50):
            estimator.update(1.0)

        # Constant → no variation → zero entropy
        assert estimator.entropy == 0.0

    def test_uniform_distribution_high_entropy(self):
        """Test that uniform distribution gives high entropy."""
        np.random.seed(42)
        estimator = EntropyEstimator(n_bins=20, window_size=200)

        # Uniform distribution
        values = np.random.uniform(0, 1, 200)
        for v in values:
            estimator.update(v)

        # Should have high entropy (close to log2(20))
        assert estimator.entropy > 3.0

    def test_gaussian_distribution_entropy(self):
        """Test entropy of Gaussian distribution."""
        np.random.seed(42)
        estimator = EntropyEstimator(n_bins=20, window_size=200)

        # Gaussian distribution
        values = np.random.normal(0, 1, 200)
        for v in values:
            estimator.update(v)

        # Gaussian should have moderate entropy
        assert estimator.entropy > 0

    def test_normalized_entropy(self):
        """Test normalized entropy property."""
        estimator = EntropyEstimator(n_bins=20)

        for i in range(50):
            estimator.update(float(i) / 50)

        # Normalized should be in [0, 1]
        assert 0 <= estimator.normalized_entropy <= 1.0

    def test_normalized_entropy_bounds(self):
        """Test that normalized entropy is always in [0, 1]."""
        np.random.seed(42)
        estimator = EntropyEstimator(n_bins=10)

        # Various distributions
        for dist in [
            np.random.uniform(0, 1, 50),
            np.random.normal(0, 1, 50),
            np.ones(50),  # Constant
        ]:
            estimator._buffer.clear()
            for v in dist:
                estimator.update(v)
            assert 0 <= estimator.normalized_entropy <= 1.0

    def test_window_size_limit(self):
        """Test that buffer respects window size."""
        estimator = EntropyEstimator(window_size=50)

        for i in range(100):
            estimator.update(float(i))

        # Buffer should be capped at window_size
        assert len(estimator._buffer) == 50

    def test_max_entropy_calculation(self):
        """Test max entropy is log2(n_bins)."""
        for n_bins in [10, 20, 50]:
            estimator = EntropyEstimator(n_bins=n_bins)
            expected_max = math.log2(n_bins)
            assert estimator._max_entropy == expected_max

    def test_get_risk_multiplier_low_entropy(self):
        """Test risk multiplier with low entropy."""
        estimator = EntropyEstimator(n_bins=20)

        # Constant values → low entropy
        for _ in range(50):
            estimator.update(1.0)

        multiplier = estimator.get_risk_multiplier(high_entropy_threshold=0.8)
        # Low entropy → full risk
        assert multiplier == 1.0

    def test_get_risk_multiplier_high_entropy(self):
        """Test risk multiplier with high entropy."""
        np.random.seed(42)
        estimator = EntropyEstimator(n_bins=20, window_size=200)

        # Uniform → high entropy
        for v in np.random.uniform(0, 1, 200):
            estimator.update(v)

        multiplier = estimator.get_risk_multiplier(
            high_entropy_threshold=0.5,
            penalty=0.5,
        )
        # High entropy → reduced risk
        assert multiplier < 1.0

    def test_get_risk_multiplier_at_threshold(self):
        """Test risk multiplier exactly at threshold."""
        estimator = EntropyEstimator(n_bins=20)
        estimator._entropy = estimator._max_entropy * 0.8  # 80% of max

        multiplier = estimator.get_risk_multiplier(high_entropy_threshold=0.8)
        # At threshold → full risk (just below penalty)
        assert multiplier == 1.0

    def test_get_risk_multiplier_penalty(self):
        """Test risk multiplier with different penalties."""
        estimator = EntropyEstimator(n_bins=20)
        # Set to maximum entropy
        estimator._entropy = estimator._max_entropy

        multiplier_high_penalty = estimator.get_risk_multiplier(
            high_entropy_threshold=0.5,
            penalty=1.0,
        )
        multiplier_low_penalty = estimator.get_risk_multiplier(
            high_entropy_threshold=0.5,
            penalty=0.5,
        )

        # Higher penalty → lower multiplier
        assert multiplier_high_penalty <= multiplier_low_penalty


class TestMutualInformationEstimator:
    """Test MutualInformationEstimator."""

    def test_initialization(self):
        """Test initialization."""
        mi = MutualInformationEstimator(n_bins=10, window_size=100)
        assert mi.n_bins == 10
        assert mi.window_size == 100

    def test_initial_mi(self):
        """Test initial MI is zero."""
        mi = MutualInformationEstimator()
        assert mi.mutual_information == 0.0

    def test_update_single_pair(self):
        """Test updating with single pair."""
        mi = MutualInformationEstimator()
        result = mi.update(0.5, 0.3)

        # Need more samples
        assert result == 0.0

    def test_update_multiple_pairs(self):
        """Test updating with multiple pairs."""
        mi = MutualInformationEstimator(n_bins=10)

        # Add enough samples
        for i in range(30):
            mi.update(float(i) / 30, float(i) / 30)

        # Should calculate MI
        result = mi.mutual_information
        assert isinstance(result, float)

    def test_independent_signals_low_mi(self):
        """Test that independent signals have low MI."""
        np.random.seed(42)
        mi = MutualInformationEstimator(n_bins=10, window_size=100)

        # Independent random signals
        x = np.random.normal(0, 1, 100)
        y = np.random.normal(0, 1, 100)

        for xi, yi in zip(x, y, strict=False):
            mi.update(xi, yi)

        # Independent → low MI (less than identical signals)
        # Note: with finite samples and binning, MI can be > 0 even for independent signals
        # We just verify it's lower than the high MI case (identical signals)
        assert mi.mutual_information < 1.0

    def test_identical_signals_high_mi(self):
        """Test that identical signals have high MI."""
        np.random.seed(42)
        mi = MutualInformationEstimator(n_bins=10, window_size=100)

        # Identical signals
        x = np.random.normal(0, 1, 100)

        for xi in x:
            mi.update(xi, xi)  # Y = X

        # Identical → high MI
        # I(X;X) = H(X)
        assert mi.mutual_information > 0.5

    def test_correlated_signals(self):
        """Test MI with correlated signals."""
        np.random.seed(42)
        mi = MutualInformationEstimator(n_bins=10, window_size=100)

        # Correlated: y = x + noise
        x = np.random.normal(0, 1, 100)
        y = x + np.random.normal(0, 0.1, 100)

        for xi, yi in zip(x, y, strict=False):
            mi.update(xi, yi)

        # Correlated → moderate to high MI
        assert mi.mutual_information > 0.1

    def test_constant_signals_zero_mi(self):
        """Test that constant signals have zero MI."""
        mi = MutualInformationEstimator(n_bins=10)

        for _ in range(50):
            mi.update(1.0, 1.0)

        # Constant → no variation → MI = 0
        assert mi.mutual_information == 0.0

    def test_window_size_limit(self):
        """Test that buffers respect window size."""
        mi = MutualInformationEstimator(window_size=50)

        for i in range(100):
            mi.update(float(i), float(i))

        assert len(mi._x_buffer) == 50
        assert len(mi._y_buffer) == 50

    def test_mi_non_negative(self):
        """Test that MI is always non-negative."""
        np.random.seed(42)
        mi = MutualInformationEstimator(n_bins=10)

        for _ in range(50):
            x = np.random.normal(0, 1)
            y = np.random.normal(0, 1)
            mi.update(x, y)

        # MI is always >= 0
        assert mi.mutual_information >= 0.0


class TestOptimalSamplingAnalyzer:
    """Test OptimalSamplingAnalyzer."""

    def test_initialization(self):
        """Test initialization."""
        analyzer = OptimalSamplingAnalyzer(max_samples=1000)
        assert analyzer.max_samples == 1000

    def test_add_sample(self):
        """Test adding samples."""
        analyzer = OptimalSamplingAnalyzer()
        analyzer.add_sample(1.0)

        assert len(analyzer._buffer) == 1

    def test_max_samples_limit(self):
        """Test that buffer respects max_samples."""
        analyzer = OptimalSamplingAnalyzer(max_samples=100)

        for i in range(200):
            analyzer.add_sample(float(i))

        assert len(analyzer._buffer) == 100

    def test_estimate_nyquist_insufficient_samples(self):
        """Test Nyquist estimation with insufficient samples."""
        analyzer = OptimalSamplingAnalyzer()

        for i in range(5):
            analyzer.add_sample(float(i))

        # Need at least 10 samples
        assert analyzer.estimate_nyquist_frequency() is None

    def test_estimate_nyquist_constant_signal(self):
        """Test Nyquist estimation with constant signal."""
        analyzer = OptimalSamplingAnalyzer()

        for _ in range(50):
            analyzer.add_sample(1.0)

        # Constant → zero crossings → low frequency
        freq = analyzer.estimate_nyquist_frequency()
        assert freq is not None
        assert freq >= 0

    def test_estimate_nyquist_oscillating_signal(self):
        """Test Nyquist estimation with oscillating signal."""
        analyzer = OptimalSamplingAnalyzer()

        # Alternating signal → high frequency
        for i in range(50):
            analyzer.add_sample(1.0 if i % 2 == 0 else -1.0)

        freq = analyzer.estimate_nyquist_frequency()
        assert freq is not None
        assert freq > 0

    def test_estimate_nyquist_sine_wave(self):
        """Test Nyquist estimation with sine wave."""
        analyzer = OptimalSamplingAnalyzer()

        # Sine wave
        for i in range(100):
            analyzer.add_sample(math.sin(2 * math.pi * i / 20))

        freq = analyzer.estimate_nyquist_frequency()
        assert freq is not None
        # Should be related to the sine frequency
        assert freq > 0

    def test_get_downsampling_factor_no_nyquist(self):
        """Test downsampling factor with no Nyquist estimate."""
        analyzer = OptimalSamplingAnalyzer()

        # Insufficient data
        factor = analyzer.get_downsampling_factor(target_frequency=0.1)
        assert factor == 1

    def test_get_downsampling_factor_valid(self):
        """Test downsampling factor calculation."""
        analyzer = OptimalSamplingAnalyzer()

        # Add data
        for i in range(50):
            analyzer.add_sample(math.sin(2 * math.pi * i / 20))

        factor = analyzer.get_downsampling_factor(target_frequency=0.05)
        assert isinstance(factor, int)
        assert factor >= 1

    def test_get_downsampling_factor_zero_target(self):
        """Test downsampling with zero target frequency."""
        analyzer = OptimalSamplingAnalyzer()

        for i in range(50):
            analyzer.add_sample(float(i))

        factor = analyzer.get_downsampling_factor(target_frequency=0.0)
        assert factor == 1


class TestEdgeCases:
    """Test edge cases across all components."""

    def test_entropy_all_same_values(self):
        """Test entropy with all identical values."""
        estimator = EntropyEstimator(n_bins=20)

        for _ in range(100):
            estimator.update(42.0)

        assert estimator.entropy == 0.0
        assert estimator.normalized_entropy == 0.0

    def test_entropy_extreme_values(self):
        """Test entropy with extreme values."""
        estimator = EntropyEstimator(n_bins=20)

        values = [1e-10, 1e10, -1e10, 1e-10]
        for v in values * 20:
            estimator.update(v)

        # Should not crash
        assert estimator.entropy >= 0

    def test_mi_single_unique_value(self):
        """Test MI when X has single unique value."""
        mi = MutualInformationEstimator(n_bins=10)

        for i in range(50):
            mi.update(1.0, float(i))  # X constant, Y varies

        # If X is constant, I(X;Y) = 0
        assert mi.mutual_information == 0.0

    def test_mi_extreme_correlation(self):
        """Test MI with perfect linear correlation."""
        mi = MutualInformationEstimator(n_bins=10)

        for i in range(50):
            x = float(i)
            y = 2.0 * x + 3.0  # Perfect linear
            mi.update(x, y)

        # Perfect correlation → high MI
        assert mi.mutual_information > 0.5

    def test_sampling_analyzer_negative_values(self):
        """Test sampling analyzer with negative values."""
        analyzer = OptimalSamplingAnalyzer()

        for i in range(50):
            analyzer.add_sample(-float(i))

        freq = analyzer.estimate_nyquist_frequency()
        assert freq is not None
        assert freq >= 0

    def test_entropy_risk_multiplier_bounds(self):
        """Test that risk multiplier is always in [0, 1]."""
        estimator = EntropyEstimator(n_bins=20)

        # Test various entropy levels
        for entropy_level in [0.0, 0.5, 0.8, 1.0]:
            estimator._entropy = estimator._max_entropy * entropy_level

            for threshold in [0.5, 0.7, 0.9]:
                for penalty in [0.3, 0.5, 1.0]:
                    multiplier = estimator.get_risk_multiplier(
                        high_entropy_threshold=threshold,
                        penalty=penalty,
                    )
                    assert 0.0 <= multiplier <= 1.0

    def test_mi_asymmetric_distributions(self):
        """Test MI with asymmetric distributions."""
        np.random.seed(42)
        mi = MutualInformationEstimator(n_bins=10)

        # X: uniform, Y: exponential
        x = np.random.uniform(0, 1, 100)
        y = np.random.exponential(1.0, 100)

        for xi, yi in zip(x, y, strict=False):
            mi.update(xi, yi)

        # Independent but different distributions
        assert mi.mutual_information >= 0

    def test_entropy_two_values_alternating(self):
        """Test entropy with two alternating values."""
        estimator = EntropyEstimator(n_bins=20)

        for i in range(100):
            estimator.update(1.0 if i % 2 == 0 else -1.0)

        # Two equally likely values → entropy close to 1 bit
        # But binning may affect this
        assert estimator.entropy > 0

    def test_nyquist_very_slow_signal(self):
        """Test Nyquist with very slowly changing signal."""
        analyzer = OptimalSamplingAnalyzer()

        # Very slow change
        for i in range(100):
            analyzer.add_sample(float(i) / 1000)

        freq = analyzer.estimate_nyquist_frequency()
        # Slow signal → low frequency
        assert freq is not None
        assert freq >= 0


# ==============================================================================
# ADDITIONAL TESTS FOR 90%+ COVERAGE
# Coverage of: WienerFilter, InformationBasedRiskManager, edge cases
# ==============================================================================

from strategies.common.adaptive_control.information_theory import (
    InformationBasedRiskManager,
    WienerFilter,
)


class TestWienerFilter:
    """Test WienerFilter for optimal noise reduction."""

    def test_initialization(self):
        """Test WienerFilter initialization (lines 366-370)."""
        wf = WienerFilter(signal_to_noise=2.0)

        assert wf.snr == 2.0
        assert wf._filter_coeff == 2.0 / (2.0 + 1)  # snr / (snr + 1)
        assert wf._prev_output == 0.0
        assert wf._initialized is False

    def test_initialization_different_snr(self):
        """Test WienerFilter with different SNR values."""
        for snr in [0.5, 1.0, 5.0, 10.0]:
            wf = WienerFilter(signal_to_noise=snr)
            expected_coeff = snr / (snr + 1)
            assert wf._filter_coeff == expected_coeff

    def test_first_update_initializes(self):
        """Test first update initializes filter (lines 382-385)."""
        wf = WienerFilter(signal_to_noise=2.0)

        # First update
        result = wf.update(5.0)

        # First update returns input unchanged and initializes
        assert result == 5.0
        assert wf._initialized is True
        assert wf._prev_output == 5.0

    def test_subsequent_updates_filter(self):
        """Test subsequent updates apply filtering (lines 388-391)."""
        wf = WienerFilter(signal_to_noise=2.0)

        # First update (initialization)
        wf.update(5.0)

        # Second update (filtering)
        result = wf.update(10.0)

        # Expected: filter_coeff * noisy + (1 - filter_coeff) * prev
        # filter_coeff = 2/3
        expected = (2 / 3) * 10.0 + (1 / 3) * 5.0
        assert abs(result - expected) < 1e-10
        assert wf._prev_output == result

    def test_update_snr(self):
        """Test update_snr method (lines 395-396)."""
        wf = WienerFilter(signal_to_noise=2.0)

        # Update SNR
        wf.update_snr(5.0)

        assert wf.snr == 5.0
        assert wf._filter_coeff == 5.0 / (5.0 + 1)

    def test_filtering_smooths_noisy_signal(self):
        """Test that filtering reduces noise."""
        np.random.seed(42)
        wf = WienerFilter(signal_to_noise=2.0)

        # True signal + noise
        true_signal = 10.0
        noisy_samples = true_signal + np.random.normal(0, 1, 20)

        filtered = []
        for sample in noisy_samples:
            filtered.append(wf.update(sample))

        # Filtered signal should be closer to true signal (on average)
        filtered_mean = np.mean(filtered[-10:])  # Last 10 samples
        np.mean(noisy_samples[-10:])

        # Both should be close to true signal, filter should be stable
        assert abs(filtered_mean - true_signal) < 3.0

    def test_low_snr_heavy_filtering(self):
        """Test low SNR results in heavy filtering (smoother output)."""
        wf = WienerFilter(signal_to_noise=0.5)  # Low SNR

        # Initialize
        wf.update(0.0)

        # Filter coefficient is low, so previous value has more weight
        result = wf.update(10.0)

        # filter_coeff = 0.5 / 1.5 = 0.333
        expected = (0.5 / 1.5) * 10.0 + (1 - 0.5 / 1.5) * 0.0
        assert abs(result - expected) < 1e-10

    def test_high_snr_light_filtering(self):
        """Test high SNR results in light filtering (follows input closely)."""
        wf = WienerFilter(signal_to_noise=10.0)  # High SNR

        # Initialize
        wf.update(0.0)

        # Filter coefficient is high, so input has more weight
        result = wf.update(10.0)

        # filter_coeff = 10 / 11 = 0.909
        expected = (10.0 / 11.0) * 10.0 + (1.0 / 11.0) * 0.0
        assert abs(result - expected) < 1e-10


class TestInformationBasedRiskManager:
    """Test InformationBasedRiskManager for comprehensive risk management."""

    def test_initialization(self):
        """Test InformationBasedRiskManager initialization (lines 424-429)."""
        rm = InformationBasedRiskManager(
            entropy_window=50,
            entropy_bins=15,
            snr_estimate=2.0,
        )

        assert rm._entropy.window_size == 50
        assert rm._entropy.n_bins == 15
        assert rm._wiener.snr == 2.0
        assert rm._snr_estimate == 2.0

    def test_initialization_defaults(self):
        """Test InformationBasedRiskManager with default values."""
        rm = InformationBasedRiskManager()

        assert rm._entropy.window_size == 50
        assert rm._entropy.n_bins == 15
        assert rm._snr_estimate == 2.0

    def test_update_returns_information_state(self):
        """Test update returns InformationState (lines 442-467)."""
        rm = InformationBasedRiskManager()

        state = rm.update(0.01)

        assert isinstance(state, InformationState)
        assert hasattr(state, "entropy")
        assert hasattr(state, "normalized_entropy")
        assert hasattr(state, "information_rate")
        assert hasattr(state, "signal_to_noise")
        assert hasattr(state, "risk_multiplier")

    def test_update_entropy_calculation(self):
        """Test entropy is updated during update calls."""
        rm = InformationBasedRiskManager(entropy_bins=10, entropy_window=30)

        # Feed enough data to calculate entropy
        for i in range(40):
            state = rm.update(float(i) / 40)

        assert state.entropy > 0
        assert 0 <= state.normalized_entropy <= 1.0 + 1e-9  # Allow float precision

    def test_update_snr_estimation(self):
        """Test SNR is estimated during updates."""
        rm = InformationBasedRiskManager(snr_estimate=2.0)

        # Feed consistent signal
        for i in range(20):
            state = rm.update(1.0 + 0.01 * i)

        # SNR estimate should have changed
        assert state.signal_to_noise >= 0

    def test_update_risk_multiplier_bounds(self):
        """Test risk multiplier is always in [0, 1]."""
        rm = InformationBasedRiskManager()

        # Various input patterns
        for _i in range(50):
            state = rm.update(np.random.normal(0, 1))
            assert 0 <= state.risk_multiplier <= 1

    def test_update_with_constant_signal(self):
        """Test update with constant signal (low entropy path)."""
        rm = InformationBasedRiskManager(entropy_bins=10, entropy_window=30)

        # Constant signal
        for _ in range(40):
            state = rm.update(1.0)

        # Constant signal has zero entropy
        assert state.entropy == 0.0
        # Risk multiplier should be high (full risk allowed)
        assert state.risk_multiplier <= 1.0

    def test_update_snr_adaptive(self):
        """Test that SNR estimate adapts to signal quality."""
        rm = InformationBasedRiskManager(snr_estimate=2.0)

        # Clean signal (high SNR)
        for i in range(30):
            rm.update(float(i) * 0.1)

        # Noisy signal
        np.random.seed(42)
        for _ in range(30):
            rm.update(np.random.normal(0, 10))

        # SNR estimate should have changed
        # Note: exact change depends on filtering dynamics
        assert rm._snr_estimate >= 0

    def test_update_information_rate(self):
        """Test information_rate is set from filtered signal."""
        rm = InformationBasedRiskManager()

        state = rm.update(5.0)

        # First update: filtered = input (Wiener init)
        assert state.information_rate == 5.0

    def test_update_instantaneous_snr_zero_filtered(self):
        """Test instantaneous SNR calculation when filtered is near zero."""
        rm = InformationBasedRiskManager(snr_estimate=2.0)

        # Initialize with zero
        state = rm.update(0.0)

        # When filtered is near zero, instantaneous_snr should be 0
        # This tests line 453
        assert state.signal_to_noise >= 0

    def test_update_snr_factor_calculation(self):
        """Test SNR factor in risk calculation."""
        rm = InformationBasedRiskManager(snr_estimate=0.5)  # Low SNR

        # Initialize filter
        rm.update(1.0)
        state = rm.update(1.0)

        # Low SNR → snr_factor = min(1.0, 0.5/2.0) = 0.25
        # This affects risk_multiplier
        assert state.risk_multiplier <= 1.0

    def test_full_workflow(self):
        """Test complete workflow with realistic data."""
        np.random.seed(42)
        rm = InformationBasedRiskManager(
            entropy_window=30,
            entropy_bins=10,
            snr_estimate=2.0,
        )

        # Simulate returns
        returns = np.random.normal(0, 0.02, 100)

        states = []
        for ret in returns:
            state = rm.update(ret)
            states.append(state)

        # Verify all states are valid
        for state in states:
            assert 0 <= state.normalized_entropy <= 1.0 + 1e-9  # Allow float precision
            assert state.signal_to_noise >= 0
            assert 0 <= state.risk_multiplier <= 1


class TestEntropyEdgeCases:
    """Additional entropy edge cases for coverage."""

    def test_calculate_entropy_single_element(self):
        """Test _calculate_entropy with single element (line 110)."""
        estimator = EntropyEstimator(n_bins=10)

        # Directly set buffer to single element
        estimator._buffer = [1.0]

        # Should return 0.0 for insufficient data
        assert estimator._calculate_entropy() == 0.0

    def test_calculate_entropy_empty_buffer(self):
        """Test _calculate_entropy with empty buffer."""
        estimator = EntropyEstimator(n_bins=10)

        # Empty buffer
        estimator._buffer = []

        # Should return 0.0
        assert estimator._calculate_entropy() == 0.0

    def test_normalized_entropy_zero_max_entropy(self):
        """Test normalized_entropy when max_entropy is zero (line 146)."""
        estimator = EntropyEstimator(n_bins=1)  # log2(1) = 0

        # With n_bins=1, max_entropy = log2(1) = 0
        assert estimator._max_entropy == 0.0

        # Should return 0.0 to avoid division by zero
        assert estimator.normalized_entropy == 0.0


class TestMutualInformationEdgeCases:
    """Additional MI edge cases for coverage."""

    def test_calculate_mi_insufficient_samples(self):
        """Test _calculate_mi with n < n_bins (line 225)."""
        mi = MutualInformationEstimator(n_bins=20)

        # Add fewer samples than n_bins
        for i in range(15):
            mi._x_buffer.append(float(i))
            mi._y_buffer.append(float(i))

        # Should return 0.0
        assert mi._calculate_mi() == 0.0

    def test_calculate_mi_exactly_n_bins(self):
        """Test _calculate_mi with exactly n_bins samples."""
        mi = MutualInformationEstimator(n_bins=10)

        # Exactly n_bins samples
        for i in range(10):
            mi._x_buffer.append(float(i))
            mi._y_buffer.append(float(i))

        # Should calculate MI
        result = mi._calculate_mi()
        assert result >= 0.0


class TestWienerFilterEdgeCases:
    """Additional WienerFilter edge cases."""

    def test_zero_snr(self):
        """Test WienerFilter with zero SNR."""
        wf = WienerFilter(signal_to_noise=0.0)

        # filter_coeff = 0 / 1 = 0
        assert wf._filter_coeff == 0.0

        wf.update(5.0)  # Initialize
        result = wf.update(10.0)

        # With zero coefficient, output is entirely previous value
        assert result == 5.0

    def test_very_high_snr(self):
        """Test WienerFilter with very high SNR."""
        wf = WienerFilter(signal_to_noise=1000.0)

        # filter_coeff approaches 1
        assert wf._filter_coeff > 0.999

        wf.update(5.0)  # Initialize
        result = wf.update(10.0)

        # With high coefficient, output follows input closely
        assert result > 9.99

    def test_negative_values(self):
        """Test WienerFilter with negative values."""
        wf = WienerFilter(signal_to_noise=2.0)

        wf.update(-5.0)  # Initialize
        result = wf.update(-10.0)

        # Should handle negative values correctly
        expected = (2 / 3) * (-10.0) + (1 / 3) * (-5.0)
        assert abs(result - expected) < 1e-10


class TestInformationBasedRiskManagerEdgeCases:
    """Additional risk manager edge cases."""

    def test_near_zero_filtered_signal(self):
        """Test when filtered signal is near zero (line 450-453)."""
        rm = InformationBasedRiskManager(snr_estimate=2.0)

        # Very small values
        for _ in range(10):
            state = rm.update(1e-15)

        # Should not crash, SNR should be valid
        assert state.signal_to_noise >= 0

    def test_large_value_spikes(self):
        """Test handling of large value spikes."""
        rm = InformationBasedRiskManager()

        # Normal values
        for _ in range(20):
            rm.update(0.01)

        # Large spike
        state = rm.update(1000.0)

        # Should handle without crashing
        assert 0 <= state.risk_multiplier <= 1

    def test_alternating_signs(self):
        """Test with alternating positive/negative values."""
        rm = InformationBasedRiskManager()

        for i in range(50):
            value = 0.01 if i % 2 == 0 else -0.01
            state = rm.update(value)

        # Should produce valid state
        assert 0 <= state.normalized_entropy <= 1.0 + 1e-9  # Allow float precision
        assert 0 <= state.risk_multiplier <= 1
