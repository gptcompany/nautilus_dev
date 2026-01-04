"""
Spectral Regime Detector - DSP-based market regime detection

Uses Power Spectral Density (PSD) slope to detect market regimes.
Based on Mandelbrot's 1/f noise observations in financial markets.

References:
- Mandelbrot (1963): "The Variation of Certain Speculative Prices"
- Cont (2001): "Empirical properties of asset returns"
"""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Deque, Optional

import numpy as np
from scipy import signal

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """
    Market regime based on spectral slope (alpha).

    MEAN_REVERTING: alpha < 0.5 (white noise-like)
    NORMAL: 0.5 <= alpha < 1.5 (pink/1f noise)
    TRENDING: alpha >= 1.5 (brown noise-like)
    """

    MEAN_REVERTING = "mean_reverting"
    NORMAL = "normal"
    TRENDING = "trending"
    UNKNOWN = "unknown"


@dataclass
class RegimeAnalysis:
    """Result of spectral regime analysis."""

    regime: MarketRegime
    alpha: float  # Spectral slope
    confidence: float  # R-squared of linear fit
    dominant_period: Optional[float]  # Most significant cycle period
    timestamp: float


class SpectralRegimeDetector:
    """
    Detects market regime using Power Spectral Density analysis.

    Calculates the spectral slope (alpha) of returns:
    - alpha ~ 0: White noise (random walk, mean reversion dominates)
    - alpha ~ 1: Pink/1f noise (natural market state)
    - alpha ~ 2: Brown noise (strong trends)

    Usage:
        detector = SpectralRegimeDetector(window_size=256)

        # Feed returns
        for ret in returns:
            detector.update(ret)

        # Get current regime
        analysis = detector.analyze()
        if analysis.regime == MarketRegime.TRENDING:
            # Use trend-following strategy
            pass
    """

    def __init__(
        self,
        window_size: int = 256,
        min_samples: int = 64,
        update_interval: int = 10,
    ):
        """
        Args:
            window_size: Number of returns to analyze
            min_samples: Minimum samples before producing result
            update_interval: Recalculate every N updates
        """
        if window_size < 32:
            raise ValueError("window_size must be >= 32 for reliable spectral analysis")

        self.window_size = window_size
        self.min_samples = min_samples
        self.update_interval = update_interval

        self._returns: Deque[float] = deque(maxlen=window_size)
        self._update_count: int = 0
        self._cached_analysis: Optional[RegimeAnalysis] = None

    def update(self, return_value: float) -> None:
        """Add new return value."""
        self._returns.append(return_value)
        self._update_count += 1

        # Invalidate cache periodically
        if self._update_count >= self.update_interval:
            self._cached_analysis = None
            self._update_count = 0

    def update_batch(self, returns: list[float]) -> None:
        """Add multiple returns at once."""
        for r in returns:
            self._returns.append(r)
        self._cached_analysis = None
        self._update_count = 0

    def analyze(self) -> RegimeAnalysis:
        """
        Perform spectral analysis and determine regime.

        Returns:
            RegimeAnalysis with regime, alpha, and confidence
        """
        if self._cached_analysis is not None:
            return self._cached_analysis

        if len(self._returns) < self.min_samples:
            return RegimeAnalysis(
                regime=MarketRegime.UNKNOWN,
                alpha=0.0,
                confidence=0.0,
                dominant_period=None,
                timestamp=0.0,
            )

        returns_arr = np.array(self._returns)

        # Compute Power Spectral Density using Welch's method
        nperseg = min(len(returns_arr), 64)
        freqs, psd = signal.welch(
            returns_arr,
            fs=1.0,  # Normalized frequency
            nperseg=nperseg,
            noverlap=nperseg // 2,
        )

        # Fit log-log slope (exclude DC component)
        mask = freqs > 0
        if mask.sum() < 3:
            return RegimeAnalysis(
                regime=MarketRegime.UNKNOWN,
                alpha=0.0,
                confidence=0.0,
                dominant_period=None,
                timestamp=0.0,
            )

        log_freqs = np.log10(freqs[mask])
        log_psd = np.log10(psd[mask] + 1e-10)  # Avoid log(0)

        # Linear regression for slope
        coeffs = np.polyfit(log_freqs, log_psd, 1)
        slope = coeffs[0]
        alpha = -slope  # PSD ~ f^(-alpha)

        # Calculate R-squared for confidence
        fitted = np.polyval(coeffs, log_freqs)
        ss_res = np.sum((log_psd - fitted) ** 2)
        ss_tot = np.sum((log_psd - np.mean(log_psd)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        # Find dominant period (peak in PSD)
        peak_idx = np.argmax(psd[mask])
        peak_freq = freqs[mask][peak_idx]
        dominant_period = 1.0 / peak_freq if peak_freq > 0 else None

        # Determine regime
        if alpha < 0.5:
            regime = MarketRegime.MEAN_REVERTING
        elif alpha < 1.5:
            regime = MarketRegime.NORMAL
        else:
            regime = MarketRegime.TRENDING

        analysis = RegimeAnalysis(
            regime=regime,
            alpha=float(alpha),
            confidence=float(max(0, r_squared)),
            dominant_period=dominant_period,
            timestamp=float(len(self._returns)),
        )

        self._cached_analysis = analysis
        return analysis

    @property
    def regime(self) -> MarketRegime:
        """Get current regime."""
        return self.analyze().regime

    @property
    def alpha(self) -> float:
        """Get current spectral slope."""
        return self.analyze().alpha

    def get_strategy_recommendation(self) -> str:
        """
        Get strategy recommendation based on current regime.

        Returns:
            Strategy type recommendation
        """
        analysis = self.analyze()

        if analysis.regime == MarketRegime.UNKNOWN:
            return "WAIT - insufficient data"
        elif analysis.regime == MarketRegime.MEAN_REVERTING:
            return "MEAN_REVERSION - fade moves, buy dips"
        elif analysis.regime == MarketRegime.NORMAL:
            return "MIXED - use both trend and mean reversion"
        else:  # TRENDING
            return "TREND_FOLLOWING - ride momentum"

    def to_dict(self) -> dict:
        """Export current state as dictionary."""
        analysis = self.analyze()
        return {
            "regime": analysis.regime.value,
            "alpha": analysis.alpha,
            "confidence": analysis.confidence,
            "dominant_period": analysis.dominant_period,
            "samples": len(self._returns),
            "recommendation": self.get_strategy_recommendation(),
        }
