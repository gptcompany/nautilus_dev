"""Hawkes OFI (Order Flow Imbalance) Indicator (Spec 025).

This module implements a Hawkes process-based Order Flow Imbalance indicator.
Hawkes processes are self-exciting point processes where past events increase
the probability of future events. This captures the clustering nature of order
flow in financial markets.

The implementation uses a pure Python exponential kernel since the `tick`
library is not available on Python 3.12.

References:
- Hawkes, A.G. (1971). Spectra of some self-exciting and mutually exciting
  point processes.
- Bacry et al. (2015). Hawkes Processes in Finance.

Math:
    Intensity: lambda(t) = mu + sum(alpha * exp(-beta * (t - t_i))) for t_i < t
    OFI = (lambda_buy - lambda_sell) / (lambda_buy + lambda_sell + eps)
    Branching ratio: eta = alpha/beta (must be < 1 for stationarity)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

from strategies.common.orderflow.config import HawkesConfig
from strategies.common.orderflow.trade_classifier import (
    TradeClassification,
    TradeSide,
    create_classifier,
)

if TYPE_CHECKING:
    from nautilus_trader.model.data import Bar


# Import HawkesResult from API contract
@dataclass
class HawkesResult:
    """Result from Hawkes OFI indicator."""

    ofi: float  # Order Flow Imbalance [-1.0, 1.0]
    buy_intensity: float  # Current lambda_buy
    sell_intensity: float  # Current lambda_sell
    branching_ratio: float  # eta = alpha/beta (stationarity indicator)
    is_fitted: bool  # True if model has been fitted


@dataclass
class HawkesState:
    """Current state of Hawkes process for OFI.

    Attributes:
        buy_intensity: Current buy-side intensity (lambda_buy)
        sell_intensity: Current sell-side intensity (lambda_sell)
        baseline: Baseline intensities (mu_buy, mu_sell)
        excitation: Excitation parameters (alpha_buy, alpha_sell)
        decay: Exponential decay rate (beta)
        branching_ratio: eta = alpha/beta (must be < 1 for stationarity)
        last_fit_time: Timestamp of last model fit (nanoseconds)
        ticks_since_fit: Number of ticks since last fit
    """

    buy_intensity: float = 0.0
    sell_intensity: float = 0.0
    baseline: tuple[float, float] = (0.1, 0.1)  # (mu_buy, mu_sell)
    excitation: tuple[float, float] = (0.5, 0.5)  # (alpha_buy, alpha_sell)
    decay: float = 1.0  # beta
    branching_ratio: float = 0.5  # eta = alpha/beta
    last_fit_time: int = 0
    ticks_since_fit: int = 0

    @property
    def ofi(self) -> float:
        """Order Flow Imbalance = normalized intensity difference.

        Returns:
            Normalized OFI in range [-1.0, 1.0]
        """
        total = self.buy_intensity + self.sell_intensity
        if total <= 1e-10:
            return 0.0
        return (self.buy_intensity - self.sell_intensity) / (total + 1e-10)


class HawkesOFI:
    """Hawkes process-based Order Flow Imbalance indicator.

    This indicator models order arrival times as a bivariate Hawkes process
    where buy and sell events can excite future events. The intensity
    difference between buy and sell processes provides the OFI signal.

    The implementation uses a pure Python exponential kernel:
        lambda(t) = mu + sum(alpha * exp(-beta * (t - t_i))) for t_i < t

    Since the `tick` library is not available on Python 3.12, we use fixed
    parameters rather than online MLE fitting.

    Attributes:
        config: HawkesConfig with decay_rate, lookback_ticks, etc.
        ofi: Current Order Flow Imbalance [-1.0, 1.0]
        buy_intensity: Current buy-side intensity
        sell_intensity: Current sell-side intensity
        is_fitted: True if model has been fitted

    Example:
        >>> config = HawkesConfig(decay_rate=1.0, use_fixed_params=True)
        >>> hawkes = HawkesOFI(config)
        >>> hawkes.handle_bar(bar)
        >>> print(f"OFI: {hawkes.ofi:.4f}")
    """

    def __init__(self, config: HawkesConfig) -> None:
        """Initialize Hawkes OFI indicator.

        Args:
            config: HawkesConfig with model parameters
        """
        self._config = config

        # Event time buffers (seconds since first event)
        self._buy_times: list[float] = []
        self._sell_times: list[float] = []

        # Initialize state with config parameters
        self._state = HawkesState(
            buy_intensity=0.0,
            sell_intensity=0.0,
            baseline=(config.fixed_baseline, config.fixed_baseline),
            excitation=(config.fixed_excitation, config.fixed_excitation),
            decay=config.decay_rate,
            branching_ratio=config.fixed_excitation / config.decay_rate,
            last_fit_time=0,
            ticks_since_fit=0,
        )

        self._is_fitted: bool = False

        # Trade classifier (tick rule for bar data)
        self._classifier = create_classifier("tick_rule")

        # Track last price for tick rule classification
        self._last_price: float | None = None

        # Track first timestamp for relative time conversion
        self._first_timestamp: int | None = None

    @property
    def config(self) -> HawkesConfig:
        """Get configuration."""
        return self._config

    @property
    def ofi(self) -> float:
        """Current Order Flow Imbalance [-1.0, 1.0].

        Returns:
            Normalized OFI value. Positive = buy pressure, negative = sell pressure.
            Returns 0.0 if not fitted.
        """
        if not self._is_fitted:
            return 0.0

        # Calculate normalized imbalance
        buy = self._state.buy_intensity
        sell = self._state.sell_intensity
        total = buy + sell + 1e-10

        ofi = (buy - sell) / total

        # Clamp to [-1.0, 1.0]
        return max(-1.0, min(1.0, ofi))

    @property
    def buy_intensity(self) -> float:
        """Current buy-side intensity (lambda_buy)."""
        return self._state.buy_intensity

    @property
    def sell_intensity(self) -> float:
        """Current sell-side intensity (lambda_sell)."""
        return self._state.sell_intensity

    @property
    def is_fitted(self) -> bool:
        """True if Hawkes model has been fitted."""
        return self._is_fitted

    def update(self, classification: TradeClassification) -> None:
        """Update Hawkes model with a new trade classification.

        Adds the event to the appropriate time buffer, updates intensities
        using the exponential kernel, and checks if refit is needed.

        Args:
            classification: Classified trade with side and timestamp
        """
        # Initialize first timestamp if needed
        if self._first_timestamp is None:
            self._first_timestamp = classification.timestamp_ns

        # Convert timestamp to relative seconds since first event
        relative_time_s = (classification.timestamp_ns - self._first_timestamp) / 1_000_000_000.0

        # Add to appropriate time buffer based on side
        if classification.side == TradeSide.BUY:
            self._buy_times.append(relative_time_s)
        elif classification.side == TradeSide.SELL:
            self._sell_times.append(relative_time_s)
        # UNKNOWN trades are ignored

        # Trim buffers to lookback_ticks (ring buffer logic)
        max_size = self._config.lookback_ticks
        if len(self._buy_times) > max_size:
            self._buy_times = self._buy_times[-max_size:]
        if len(self._sell_times) > max_size:
            self._sell_times = self._sell_times[-max_size:]

        # Increment ticks counter
        self._state.ticks_since_fit += 1

        # Update intensities using exponential kernel
        self._state.buy_intensity = self._calculate_intensity(self._buy_times, relative_time_s)
        self._state.sell_intensity = self._calculate_intensity(self._sell_times, relative_time_s)

        # Check if refit is needed (based on interval)
        if self._state.ticks_since_fit >= self._config.refit_interval:
            self.refit()

    def _calculate_intensity(self, times: list[float], current_time: float) -> float:
        """Calculate Hawkes intensity at current time.

        Uses the exponential kernel:
            lambda(t) = mu + sum(alpha * exp(-beta * (t - t_i))) for t_i < t

        Args:
            times: List of event times in seconds
            current_time: Current time in seconds

        Returns:
            Intensity value at current time
        """
        if not times:
            return self._config.fixed_baseline

        mu = self._config.fixed_baseline
        alpha = self._config.fixed_excitation
        beta = self._config.decay_rate

        # Sum over all past events
        excitation_sum = 0.0
        for t_i in times:
            if t_i < current_time:
                dt = current_time - t_i
                excitation_sum += alpha * math.exp(-beta * dt)

        return mu + excitation_sum

    def refit(self) -> None:
        """Refit the Hawkes model on accumulated data.

        Since the `tick` library is not available on Python 3.12,
        we always use fixed parameters. This method updates the
        intensities and marks the model as fitted.

        For online MLE fitting, scipy.optimize could be used with
        the Hawkes log-likelihood, but this is complex and the fixed
        parameter approach works well for most trading applications.
        """
        # Always use fixed params (tick library unavailable on Python 3.12)
        # Just update state and mark as fitted

        # Update state with config parameters (in case they changed)
        self._state.baseline = (
            self._config.fixed_baseline,
            self._config.fixed_baseline,
        )
        self._state.excitation = (
            self._config.fixed_excitation,
            self._config.fixed_excitation,
        )
        self._state.decay = self._config.decay_rate
        self._state.branching_ratio = self._config.fixed_excitation / self._config.decay_rate

        # Calculate current intensities
        if self._buy_times or self._sell_times:
            # Use the most recent timestamp
            latest_time = 0.0
            if self._buy_times:
                latest_time = max(latest_time, self._buy_times[-1])
            if self._sell_times:
                latest_time = max(latest_time, self._sell_times[-1])

            self._state.buy_intensity = self._calculate_intensity(self._buy_times, latest_time)
            self._state.sell_intensity = self._calculate_intensity(self._sell_times, latest_time)

        # Mark as fitted
        self._is_fitted = True
        self._state.ticks_since_fit = 0
        if self._first_timestamp is not None:
            self._state.last_fit_time = self._first_timestamp

    def handle_bar(self, bar: Bar) -> None:
        """Process a NautilusTrader Bar.

        Extracts price, volume, and timestamp from the bar, classifies
        the trade using the tick rule, and updates the Hawkes model.

        Args:
            bar: NautilusTrader Bar object
        """
        # Extract bar data
        price = float(bar.close)
        volume = float(bar.volume)
        timestamp_ns = bar.ts_event
        open_price = float(bar.open)
        high = float(bar.high)
        low = float(bar.low)

        # Classify trade direction
        classification = self._classifier.classify(
            price=price,
            volume=volume,
            timestamp_ns=timestamp_ns,
            prev_price=self._last_price,
            open_price=open_price,
            high=high,
            low=low,
        )

        # Update Hawkes model
        self.update(classification)

        # Update last price for next classification
        self._last_price = price

    def reset(self) -> None:
        """Reset indicator state.

        Clears all event buffers and resets the model to initial state.
        """
        self._buy_times.clear()
        self._sell_times.clear()

        # Reset state
        self._state = HawkesState(
            buy_intensity=0.0,
            sell_intensity=0.0,
            baseline=(self._config.fixed_baseline, self._config.fixed_baseline),
            excitation=(self._config.fixed_excitation, self._config.fixed_excitation),
            decay=self._config.decay_rate,
            branching_ratio=self._config.fixed_excitation / self._config.decay_rate,
            last_fit_time=0,
            ticks_since_fit=0,
        )

        self._is_fitted = False
        self._first_timestamp = None
        self._last_price = None

        # Reset classifier state
        self._classifier.reset()

    def get_result(self) -> HawkesResult:
        """Get full Hawkes result with metadata.

        Returns:
            HawkesResult with OFI, intensities, branching ratio, and fitted status
        """
        return HawkesResult(
            ofi=self.ofi,
            buy_intensity=self._state.buy_intensity,
            sell_intensity=self._state.sell_intensity,
            branching_ratio=self._state.branching_ratio,
            is_fitted=self._is_fitted,
        )
