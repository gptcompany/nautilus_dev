"""
Information Theory for Trading

Shannon's Information Theory applied to financial markets:
- Entropy = Uncertainty = Risk
- Mutual Information = Signal vs Noise
- Optimal Sampling = Nyquist for markets
- Kalman = Optimal signal/noise separation

Key Insights:
- High entropy = many possibilities = uncertain = REDUCE RISK
- Low entropy = few possibilities = predictable = NORMAL RISK
- Mutual Information = how much does X tell us about Y?

This module helps you:
1. Measure market uncertainty (entropy)
2. Detect information arrival (entropy spikes)
3. Optimal filtering (Kalman, Wiener)
4. Risk scaling based on information content

Reference:
- Shannon (1948): A Mathematical Theory of Communication
- Kelly (1956): A New Interpretation of Information Rate
- Cover & Thomas: Elements of Information Theory
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class InformationState:
    """Current state of market information."""

    entropy: float  # Bits of uncertainty
    normalized_entropy: float  # 0-1 scale
    information_rate: float  # Bits per sample
    signal_to_noise: float  # Estimated SNR
    risk_multiplier: float  # Based on information


class EntropyEstimator:
    """
    Estimate entropy of price returns.

    Uses histogram-based estimation for simplicity.
    More sophisticated methods exist but add complexity.

    Shannon entropy: H(X) = -Σ p(x) * log2(p(x))

    High entropy = uncertain = reduce position
    Low entropy = predictable = normal position

    Usage:
        entropy = EntropyEstimator(n_bins=20)

        for ret in returns:
            entropy.update(ret)

        if entropy.normalized_entropy > 0.8:
            reduce_position()
    """

    def __init__(
        self,
        n_bins: int = 20,
        window_size: int = 100,
        smoothing: float = 0.1,  # Laplace smoothing
    ):
        """
        Args:
            n_bins: Number of histogram bins
            n_bins: Histogram bins for entropy estimation
            window_size: Rolling window for histogram
            smoothing: Laplace smoothing to avoid log(0)
        """
        self.n_bins = n_bins
        self.window_size = window_size
        self.smoothing = smoothing

        self._buffer: List[float] = []
        self._entropy: float = 0.0
        self._max_entropy = math.log2(n_bins)  # Maximum possible entropy

    def update(self, value: float) -> float:
        """
        Update with new value, return current entropy.

        Args:
            value: New observation (typically return)

        Returns:
            Current entropy estimate
        """
        self._buffer.append(value)
        if len(self._buffer) > self.window_size:
            self._buffer = self._buffer[-self.window_size :]

        if len(self._buffer) >= self.n_bins:
            self._entropy = self._calculate_entropy()

        return self._entropy

    def _calculate_entropy(self) -> float:
        """Calculate Shannon entropy from buffer."""
        if len(self._buffer) < 2:
            return 0.0

        # Find range
        min_val = min(self._buffer)
        max_val = max(self._buffer)

        if max_val == min_val:
            return 0.0  # No variation = no entropy

        # Create histogram
        bin_width = (max_val - min_val) / self.n_bins
        counts = [self.smoothing] * self.n_bins  # Laplace smoothing

        for v in self._buffer:
            bin_idx = int((v - min_val) / bin_width)
            bin_idx = min(bin_idx, self.n_bins - 1)  # Handle edge case
            counts[bin_idx] += 1

        # Calculate probabilities
        total = sum(counts)
        probs = [c / total for c in counts]

        # Shannon entropy
        entropy = -sum(p * math.log2(p) for p in probs if p > 0)

        return entropy

    @property
    def entropy(self) -> float:
        """Current entropy in bits."""
        return self._entropy

    @property
    def normalized_entropy(self) -> float:
        """Entropy normalized to 0-1 (relative to maximum)."""
        if self._max_entropy <= 0:
            return 0.0
        return self._entropy / self._max_entropy

    def get_risk_multiplier(
        self,
        high_entropy_threshold: float = 0.8,
        penalty: float = 0.5,
    ) -> float:
        """
        Get risk multiplier based on entropy.

        High entropy = uncertain = reduce risk.

        Args:
            high_entropy_threshold: Normalized entropy above this reduces risk
            penalty: How much to reduce risk when entropy is high

        Returns:
            Risk multiplier (0 to 1)
        """
        if self.normalized_entropy > high_entropy_threshold:
            # Linear reduction above threshold
            excess = (self.normalized_entropy - high_entropy_threshold) / (
                1 - high_entropy_threshold
            )
            return max(0.0, 1.0 - excess * penalty)
        return 1.0


class MutualInformationEstimator:
    """
    Estimate mutual information between two signals.

    I(X;Y) = H(X) + H(Y) - H(X,Y)

    This tells us how much knowing X reduces uncertainty about Y.

    Use case: Does indicator X actually tell us about future returns Y?

    If I(indicator; returns) is low, the indicator is noise.
    """

    def __init__(
        self,
        n_bins: int = 10,
        window_size: int = 100,
    ):
        self.n_bins = n_bins
        self.window_size = window_size

        self._x_buffer: List[float] = []
        self._y_buffer: List[float] = []

    def update(self, x: float, y: float) -> float:
        """
        Update with paired observations.

        Args:
            x: First signal (e.g., indicator)
            y: Second signal (e.g., future return)

        Returns:
            Current mutual information estimate
        """
        self._x_buffer.append(x)
        self._y_buffer.append(y)

        if len(self._x_buffer) > self.window_size:
            self._x_buffer = self._x_buffer[-self.window_size :]
            self._y_buffer = self._y_buffer[-self.window_size :]

        if len(self._x_buffer) >= self.n_bins * 2:
            return self._calculate_mi()
        return 0.0

    def _calculate_mi(self) -> float:
        """Calculate mutual information."""
        n = len(self._x_buffer)
        if n < self.n_bins:
            return 0.0

        # Create 2D histogram (joint distribution)
        x_min, x_max = min(self._x_buffer), max(self._x_buffer)
        y_min, y_max = min(self._y_buffer), max(self._y_buffer)

        if x_max == x_min or y_max == y_min:
            return 0.0

        x_width = (x_max - x_min) / self.n_bins
        y_width = (y_max - y_min) / self.n_bins

        # Joint histogram
        joint = [[0] * self.n_bins for _ in range(self.n_bins)]
        x_marginal = [0] * self.n_bins
        y_marginal = [0] * self.n_bins

        for x, y in zip(self._x_buffer, self._y_buffer):
            xi = min(int((x - x_min) / x_width), self.n_bins - 1)
            yi = min(int((y - y_min) / y_width), self.n_bins - 1)
            joint[xi][yi] += 1
            x_marginal[xi] += 1
            y_marginal[yi] += 1

        # Calculate MI
        mi = 0.0
        for i in range(self.n_bins):
            for j in range(self.n_bins):
                if joint[i][j] > 0 and x_marginal[i] > 0 and y_marginal[j] > 0:
                    p_xy = joint[i][j] / n
                    p_x = x_marginal[i] / n
                    p_y = y_marginal[j] / n
                    mi += p_xy * math.log2(p_xy / (p_x * p_y))

        return max(0.0, mi)  # MI is non-negative

    @property
    def mutual_information(self) -> float:
        """Current MI estimate."""
        if len(self._x_buffer) >= self.n_bins * 2:
            return self._calculate_mi()
        return 0.0


class OptimalSamplingAnalyzer:
    """
    Analyze optimal sampling frequency.

    Nyquist theorem: f_sample >= 2 * f_max

    If you sample too slow, you get aliasing (false patterns).
    If you sample too fast, you get noise.

    This analyzer helps find the optimal sampling rate
    for your trading strategy.
    """

    def __init__(self, max_samples: int = 1000):
        self.max_samples = max_samples
        self._buffer: List[float] = []

    def add_sample(self, value: float) -> None:
        """Add a sample."""
        self._buffer.append(value)
        if len(self._buffer) > self.max_samples:
            self._buffer = self._buffer[-self.max_samples :]

    def estimate_nyquist_frequency(self) -> Optional[float]:
        """
        Estimate the Nyquist frequency for this signal.

        Uses zero-crossing rate as a simple frequency estimator.

        Returns:
            Estimated Nyquist frequency (samples^-1), or None
        """
        if len(self._buffer) < 10:
            return None

        # Count zero crossings (around mean)
        mean = sum(self._buffer) / len(self._buffer)
        crossings = 0

        for i in range(1, len(self._buffer)):
            if (self._buffer[i - 1] - mean) * (self._buffer[i] - mean) < 0:
                crossings += 1

        # Frequency estimate (zero crossings per sample)
        freq = crossings / (2 * len(self._buffer))

        # Nyquist frequency = 2 * max_freq
        return 2 * freq

    def get_downsampling_factor(
        self,
        target_frequency: float,
    ) -> int:
        """
        Get optimal downsampling factor.

        Args:
            target_frequency: Desired signal frequency

        Returns:
            Downsampling factor (keep every N samples)
        """
        nyquist = self.estimate_nyquist_frequency()
        if nyquist is None or nyquist <= 0:
            return 1

        # Want: f_sample >= 2 * target_frequency
        # Current f_sample = 1 (normalized)
        # Downsampled f_sample = 1 / factor

        # 1 / factor >= 2 * target_frequency
        # factor <= 1 / (2 * target_frequency)

        max_factor = 1 / (2 * target_frequency) if target_frequency > 0 else 1
        return max(1, int(max_factor))


class WienerFilter:
    """
    Wiener filter for optimal noise reduction.

    The Wiener filter minimizes mean squared error between
    the filtered signal and the true signal.

    W(f) = S(f) / (S(f) + N(f))

    where S(f) = signal power, N(f) = noise power

    This is optimal in the MSE sense when signal and noise
    are stationary and uncorrelated.
    """

    def __init__(self, signal_to_noise: float = 2.0):
        """
        Args:
            signal_to_noise: Estimated SNR
        """
        self.snr = signal_to_noise
        self._filter_coeff = self.snr / (self.snr + 1)

        self._prev_output: float = 0.0
        self._initialized: bool = False

    def update(self, noisy_signal: float) -> float:
        """
        Apply Wiener filter to noisy signal.

        Args:
            noisy_signal: Input with noise

        Returns:
            Filtered signal
        """
        if not self._initialized:
            self._prev_output = noisy_signal
            self._initialized = True
            return noisy_signal

        # Simple Wiener-like filter (first-order IIR approximation)
        output = self._filter_coeff * noisy_signal + (1 - self._filter_coeff) * self._prev_output
        self._prev_output = output

        return output

    def update_snr(self, new_snr: float) -> None:
        """Update SNR estimate (adaptive)."""
        self.snr = new_snr
        self._filter_coeff = self.snr / (self.snr + 1)


class InformationBasedRiskManager:
    """
    Risk management based on information theory.

    Combines:
    - Entropy (uncertainty)
    - Mutual information (signal quality)
    - Optimal filtering (Kalman/Wiener)

    Usage:
        risk_mgr = InformationBasedRiskManager()

        for ret in returns:
            state = risk_mgr.update(ret)

            if state.risk_multiplier < 0.5:
                reduce_positions()
    """

    def __init__(
        self,
        entropy_window: int = 50,
        entropy_bins: int = 15,
        snr_estimate: float = 2.0,
    ):
        self._entropy = EntropyEstimator(
            n_bins=entropy_bins,
            window_size=entropy_window,
        )
        self._wiener = WienerFilter(signal_to_noise=snr_estimate)
        self._snr_estimate = snr_estimate

    def update(self, value: float) -> InformationState:
        """
        Update with new observation.

        Args:
            value: New observation (typically return)

        Returns:
            InformationState with entropy, SNR, risk multiplier
        """
        # Update entropy
        entropy = self._entropy.update(value)
        norm_entropy = self._entropy.normalized_entropy

        # Filter signal
        filtered = self._wiener.update(value)

        # Estimate SNR from filtered vs raw
        noise = value - filtered
        if abs(filtered) > 1e-10:
            instantaneous_snr = abs(filtered) / (abs(noise) + 1e-10)
        else:
            instantaneous_snr = 0.0

        # Update SNR estimate (exponential smoothing)
        alpha = 0.1
        self._snr_estimate = alpha * instantaneous_snr + (1 - alpha) * self._snr_estimate
        self._wiener.update_snr(self._snr_estimate)

        # Calculate risk multiplier
        # High entropy OR low SNR = reduce risk
        entropy_factor = self._entropy.get_risk_multiplier()
        snr_factor = min(1.0, self._snr_estimate / 2.0)  # SNR < 2 = noisy

        risk_multiplier = entropy_factor * snr_factor

        return InformationState(
            entropy=entropy,
            normalized_entropy=norm_entropy,
            information_rate=filtered,  # Approximation
            signal_to_noise=self._snr_estimate,
            risk_multiplier=risk_multiplier,
        )
