"""
DSP Filters - Computationally Efficient Signal Processing

From electrical engineering / DSP:
- IIR filters: O(1) per sample, no window needed
- Kalman filter: Optimal state estimation, O(1)
- LMS adaptive filter: Self-tuning, O(1)

These replace expensive batch operations (FFT, windowed mean) with
single-sample recursive updates.

Computational Cost Comparison:
- FFT regime detection: O(N log N) per update
- IIR regime detection: O(1) per update
- Windowed volatility: O(N) per update
- Kalman volatility: O(1) per update

For 256-sample window: 256x to 2000x speedup!
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class IIRState:
    """State of IIR filter."""

    y: float  # Output
    initialized: bool = False


class IIRLowPass:
    """
    First-order IIR low-pass filter.

    Transfer function: H(z) = (1-alpha) / (1 - alpha*z^-1)

    This is the "EMA" from trading, but properly named.
    Single sample update, O(1) cost.

    Usage:
        lpf = IIRLowPass(cutoff_period=20)  # Like EMA(20)
        for value in stream:
            filtered = lpf.update(value)
    """

    def __init__(self, cutoff_period: int):
        """
        Args:
            cutoff_period: Equivalent to EMA period
        """
        # Alpha from EMA convention: alpha = 2 / (period + 1)
        self.alpha = 2.0 / (cutoff_period + 1)
        self._y: float = 0.0
        self._initialized: bool = False

    def update(self, x: float) -> float:
        """Process single sample, O(1)."""
        if not self._initialized:
            self._y = x
            self._initialized = True
        else:
            self._y = self.alpha * x + (1 - self.alpha) * self._y
        return self._y

    @property
    def value(self) -> float:
        """Current output."""
        return self._y

    def reset(self) -> None:
        """Reset filter state."""
        self._y = 0.0
        self._initialized = False


class IIRHighPass:
    """
    First-order IIR high-pass filter.

    H(z) = alpha * (1 - z^-1) / (1 - alpha*z^-1)

    Extracts "fast" component, removes trend.
    O(1) per sample.
    """

    def __init__(self, cutoff_period: int):
        self.alpha = 2.0 / (cutoff_period + 1)
        self._x_prev: float = 0.0
        self._y: float = 0.0
        self._initialized: bool = False

    def update(self, x: float) -> float:
        """Process single sample, O(1)."""
        if not self._initialized:
            self._x_prev = x
            self._y = 0.0
            self._initialized = True
        else:
            self._y = self.alpha * (self._y + x - self._x_prev)
            self._x_prev = x
        return self._y

    @property
    def value(self) -> float:
        return self._y


class RecursiveVariance:
    """
    Welford's online algorithm for variance.

    O(1) per sample, numerically stable.
    No window needed - exponentially weighted.
    """

    def __init__(self, alpha: float = 0.05):
        """
        Args:
            alpha: Smoothing factor (0.05 = ~40 sample effective window)
        """
        self.alpha = alpha
        self._mean: float = 0.0
        self._var: float = 0.0
        self._initialized: bool = False

    def update(self, x: float) -> float:
        """Process single sample, return current variance."""
        if not self._initialized:
            self._mean = x
            self._var = 0.0
            self._initialized = True
        else:
            delta = x - self._mean
            self._mean += self.alpha * delta
            self._var = (1 - self.alpha) * (self._var + self.alpha * delta * delta)
        return self._var

    @property
    def variance(self) -> float:
        return self._var

    @property
    def std(self) -> float:
        return math.sqrt(max(0, self._var))

    @property
    def mean(self) -> float:
        return self._mean


@dataclass
class KalmanState:
    """State of Kalman filter."""

    x: float  # State estimate
    P: float  # Estimate covariance
    initialized: bool = False


class KalmanFilter1D:
    """
    1D Kalman filter for state estimation.

    Optimal linear estimator for noisy signals.
    O(1) per sample.

    Models: x[k] = x[k-1] + w (random walk)
            z[k] = x[k] + v (noisy observation)

    Usage:
        kf = KalmanFilter1D(process_noise=0.01, measurement_noise=0.1)
        for price in stream:
            estimated_value = kf.update(price)
    """

    def __init__(
        self,
        process_noise: float = 0.01,
        measurement_noise: float = 0.1,
    ):
        """
        Args:
            process_noise: Q - how much state changes between samples
            measurement_noise: R - how noisy are observations
        """
        self.Q = process_noise
        self.R = measurement_noise
        self._x: float = 0.0  # State estimate
        self._P: float = 1.0  # Estimate covariance
        self._initialized: bool = False

    def update(self, z: float) -> float:
        """
        Update with new observation, O(1).

        Args:
            z: New observation

        Returns:
            Filtered state estimate
        """
        if not self._initialized:
            self._x = z
            self._P = 1.0
            self._initialized = True
            return self._x

        # Predict
        x_pred = self._x  # Random walk model
        P_pred = self._P + self.Q

        # Update
        K = P_pred / (P_pred + self.R)  # Kalman gain
        self._x = x_pred + K * (z - x_pred)  # State update
        self._P = (1 - K) * P_pred  # Covariance update

        return self._x

    @property
    def value(self) -> float:
        return self._x

    @property
    def uncertainty(self) -> float:
        return math.sqrt(self._P)

    def reset(self) -> None:
        self._x = 0.0
        self._P = 1.0
        self._initialized = False


class LMSAdaptiveFilter:
    """
    Least Mean Squares adaptive filter.

    Self-tuning FIR filter that learns optimal weights.
    O(N) per sample where N = filter length.

    For short filters (N < 10), very fast.

    Usage:
        lms = LMSAdaptiveFilter(length=5, mu=0.1)
        for x, target in zip(inputs, targets):
            prediction = lms.update(x, target)
    """

    def __init__(
        self,
        length: int = 5,
        mu: float = 0.1,
    ):
        """
        Args:
            length: Number of taps (weights)
            mu: Learning rate (step size)
        """
        self.length = length
        self.mu = mu
        self._weights = [0.0] * length
        self._buffer = [0.0] * length
        self._buffer_idx = 0

    def update(self, x: float, target: float) -> float:
        """
        Update filter with new sample and target.

        Args:
            x: New input sample
            target: Desired output (for adaptation)

        Returns:
            Filter prediction
        """
        # Add to circular buffer
        self._buffer[self._buffer_idx] = x
        self._buffer_idx = (self._buffer_idx + 1) % self.length

        # Compute prediction
        prediction = 0.0
        for i in range(self.length):
            idx = (self._buffer_idx - 1 - i) % self.length
            prediction += self._weights[i] * self._buffer[idx]

        # Compute error
        error = target - prediction

        # Update weights (LMS rule)
        for i in range(self.length):
            idx = (self._buffer_idx - 1 - i) % self.length
            self._weights[i] += self.mu * error * self._buffer[idx]

        return prediction

    @property
    def weights(self) -> list[float]:
        return self._weights.copy()


class IIRRegimeDetector:
    """
    IIR-based regime detection - MUCH faster than spectral.

    Uses ratio of fast/slow variance to detect regime:
    - Fast variance >> slow: Volatile/trending
    - Fast variance << slow: Mean reverting
    - Fast variance ~ slow: Normal

    O(1) per sample vs O(N log N) for FFT.
    """

    def __init__(
        self,
        fast_period: int = 10,
        slow_period: int = 50,
        trend_threshold: float = 1.5,
        revert_threshold: float = 0.7,
    ):
        """
        Args:
            fast_period: Fast variance period
            slow_period: Slow variance period
            trend_threshold: Ratio above which = trending
            revert_threshold: Ratio below which = mean reverting
        """
        self.trend_threshold = trend_threshold
        self.revert_threshold = revert_threshold

        # Fast and slow variance trackers
        self._fast_var = RecursiveVariance(alpha=2.0 / (fast_period + 1))
        self._slow_var = RecursiveVariance(alpha=2.0 / (slow_period + 1))

    def update(self, return_value: float) -> str:
        """
        Update with new return, get regime.

        Args:
            return_value: Latest return

        Returns:
            Regime: "trending", "normal", or "mean_reverting"
        """
        fast = self._fast_var.update(return_value)
        slow = self._slow_var.update(return_value)

        if slow < 1e-10:
            return "unknown"

        ratio = fast / slow

        if ratio > self.trend_threshold:
            return "trending"
        elif ratio < self.revert_threshold:
            return "mean_reverting"
        else:
            return "normal"

    @property
    def variance_ratio(self) -> float:
        """Fast/slow variance ratio."""
        slow = self._slow_var.variance
        if slow < 1e-10:
            return 1.0
        return self._fast_var.variance / slow


class DSPRegimeDetector:
    """
    Complete DSP-based regime detector.

    Combines multiple efficient IIR components:
    - Fast/slow variance ratio for regime
    - Kalman filtered momentum for trend direction
    - Recursive volatility for position sizing

    Total cost: O(1) per sample.
    """

    def __init__(
        self,
        fast_period: int = 10,
        slow_period: int = 50,
        momentum_period: int = 20,
    ):
        self._iir_regime = IIRRegimeDetector(
            fast_period=fast_period,
            slow_period=slow_period,
        )
        self._momentum_filter = IIRLowPass(cutoff_period=momentum_period)
        self._volatility = RecursiveVariance(alpha=2.0 / (slow_period + 1))

    def update(self, price: float, prev_price: float | None = None) -> dict:
        """
        Update with new price.

        Args:
            price: Current price
            prev_price: Previous price (for return calculation)

        Returns:
            Dict with regime, momentum, volatility
        """
        # Calculate return if we have previous price
        if prev_price is not None and prev_price > 0:
            ret = (price - prev_price) / prev_price
        else:
            ret = 0.0

        # Update components
        regime = self._iir_regime.update(ret)
        momentum = self._momentum_filter.update(ret)
        vol = self._volatility.update(ret)

        return {
            "regime": regime,
            "momentum": momentum,
            "volatility": math.sqrt(max(0, vol)),
            "variance_ratio": self._iir_regime.variance_ratio,
        }
