"""Baseline strategy wrapper for fair contender comparison.

This module provides a generic strategy wrapper that:
    - Uses identical signal generation for all contenders (EMA crossover)
    - Plugs in different ContenderSizers for position sizing
    - Ensures the ONLY difference between contenders is position sizing

Signal Generation:
    Uses simple EMA crossover (fast EMA vs slow EMA).
    This is NOT the point of comparison - it's just a common signal.
    All contenders receive the same signal; only sizing differs.

Why EMA crossover?
    - Simple, well-understood signal
    - Uses NautilusTrader native Rust indicators
    - Not the focus of comparison (sizing is)
    - Works with update_raw() for Rust compatibility

Reference:
    API Note: Use ema.update_raw(price) for Rust/Cython compatibility
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scripts.baseline_validation.sizers import ContenderSizer


@dataclass
class StrategyState:
    """Current state of the baseline strategy."""

    fast_ema: float | None
    slow_ema: float | None
    signal: float
    is_warmed_up: bool
    price_count: int


class SimpleEMA:
    """Simple Exponential Moving Average.

    Uses the standard EMA formula:
        EMA_new = alpha * price + (1 - alpha) * EMA_old
        alpha = 2 / (period + 1)

    This is a Python fallback; prefer NautilusTrader's native Rust EMA
    when running in a full NautilusTrader context.
    """

    def __init__(self, period: int):
        """Initialize EMA.

        Args:
            period: EMA period (must be >= 1).
        """
        if period < 1:
            raise ValueError(f"period must be >= 1, got {period}")

        self.period = period
        self.alpha = 2.0 / (period + 1)
        self._value: float | None = None
        self._count: int = 0

    def update_raw(self, price: float) -> float | None:
        """Update EMA with new price.

        Uses update_raw naming for compatibility with NautilusTrader
        Rust indicators.

        Args:
            price: New price value.

        Returns:
            Current EMA value, or None if not enough data.
        """
        self._count += 1

        if self._value is None:
            self._value = price
        else:
            self._value = self.alpha * price + (1 - self.alpha) * self._value

        return self._value if self.is_initialized else None

    @property
    def value(self) -> float | None:
        """Current EMA value."""
        return self._value if self.is_initialized else None

    @property
    def is_initialized(self) -> bool:
        """Whether EMA has enough data points."""
        return self._count >= self.period

    def reset(self) -> None:
        """Reset EMA state."""
        self._value = None
        self._count = 0


class BaselineStrategy:
    """Generic strategy wrapper for contender comparison.

    Uses identical EMA crossover signal for all contenders.
    Only position sizing differs based on the plugged ContenderSizer.

    Attributes:
        sizer: The ContenderSizer for position calculation.
        fast_ema_period: Period for fast EMA (default 10).
        slow_ema_period: Period for slow EMA (default 20).

    Usage:
        >>> sizer = FixedFractionalSizer(risk_pct=0.02)
        >>> strategy = BaselineStrategy(sizer=sizer)
        >>> for bar in data:
        ...     strategy.update_price(bar.close)
        ...     if strategy.is_warmed_up:
        ...         position = strategy.calculate_position(
        ...             equity=account.equity,
        ...             entry_price=bar.close,
        ...             stop_loss_price=bar.close * 0.95,
        ...         )
    """

    def __init__(
        self,
        sizer: "ContenderSizer",
        fast_ema_period: int = 10,
        slow_ema_period: int = 20,
        signal_normalize_window: int = 20,
    ):
        """Initialize BaselineStrategy.

        Args:
            sizer: ContenderSizer for position calculation.
            fast_ema_period: Period for fast EMA.
            slow_ema_period: Period for slow EMA.
            signal_normalize_window: Window for signal normalization.
        """
        if fast_ema_period >= slow_ema_period:
            raise ValueError(
                f"fast_ema_period ({fast_ema_period}) must be < "
                f"slow_ema_period ({slow_ema_period})"
            )

        self._sizer = sizer
        self.fast_ema_period = fast_ema_period
        self.slow_ema_period = slow_ema_period
        self._signal_normalize_window = signal_normalize_window

        # Initialize EMAs
        self._fast_ema = SimpleEMA(period=fast_ema_period)
        self._slow_ema = SimpleEMA(period=slow_ema_period)

        # Signal normalization buffer
        self._signal_buffer: list[float] = []
        self._price_count = 0

    @property
    def sizer(self) -> "ContenderSizer":
        """The ContenderSizer for position calculation."""
        return self._sizer

    @property
    def is_warmed_up(self) -> bool:
        """Whether indicators are warmed up."""
        return self._fast_ema.is_initialized and self._slow_ema.is_initialized

    def update_price(self, price: float) -> None:
        """Update indicators with new price.

        Args:
            price: New price value.
        """
        self._price_count += 1

        # Update EMAs using update_raw for Rust compatibility
        self._fast_ema.update_raw(price)
        self._slow_ema.update_raw(price)

        # Update sizer state if it tracks volatility
        if self._price_count > 1:
            # Calculate simple return for volatility tracking
            # Note: In real use, should track previous price
            self._sizer.update(return_value=0.0, timestamp=float(self._price_count))

    def get_signal(self) -> float:
        """Get current trading signal.

        Returns:
            Signal in range [-1, 1]:
                - Positive: Fast EMA > Slow EMA (bullish)
                - Negative: Fast EMA < Slow EMA (bearish)
                - Zero: Not warmed up or EMAs equal
        """
        if not self.is_warmed_up:
            return 0.0

        fast_value = self._fast_ema.value
        slow_value = self._slow_ema.value

        if fast_value is None or slow_value is None:
            return 0.0

        if slow_value == 0:
            return 0.0

        # Calculate raw signal as percentage difference
        raw_signal = (fast_value - slow_value) / slow_value

        # Store for normalization
        self._signal_buffer.append(raw_signal)
        if len(self._signal_buffer) > self._signal_normalize_window:
            self._signal_buffer = self._signal_buffer[-self._signal_normalize_window :]

        # Normalize using tanh for bounded output
        # Scale by 10 to make typical signals more pronounced
        normalized = math.tanh(raw_signal * 10)

        return normalized

    def calculate_position(
        self,
        equity: float,
        entry_price: float,
        stop_loss_price: float,
    ) -> float:
        """Calculate position size using the sizer.

        Args:
            equity: Current account equity.
            entry_price: Expected entry price.
            stop_loss_price: Stop loss price.

        Returns:
            Position size in base units.
        """
        signal = self.get_signal()

        return self._sizer.calculate(
            signal=signal,
            equity=equity,
            entry_price=entry_price,
            stop_loss_price=stop_loss_price,
        )

    def get_state(self) -> StrategyState:
        """Get current strategy state.

        Returns:
            StrategyState with indicator values and signal.
        """
        return StrategyState(
            fast_ema=self._fast_ema.value,
            slow_ema=self._slow_ema.value,
            signal=self.get_signal() if self.is_warmed_up else 0.0,
            is_warmed_up=self.is_warmed_up,
            price_count=self._price_count,
        )

    def reset(self) -> None:
        """Reset strategy state.

        Clears indicator values and signal buffer.
        Also resets BuyAndHoldSizer if applicable.
        """
        self._fast_ema.reset()
        self._slow_ema.reset()
        self._signal_buffer.clear()
        self._price_count = 0

        # Reset BuyAndHoldSizer if applicable
        if hasattr(self._sizer, "reset"):
            self._sizer.reset()


def create_baseline_strategy(
    sizer: "ContenderSizer",
    fast_period: int = 10,
    slow_period: int = 20,
) -> BaselineStrategy:
    """Factory function to create BaselineStrategy.

    Args:
        sizer: ContenderSizer for position calculation.
        fast_period: Fast EMA period.
        slow_period: Slow EMA period.

    Returns:
        Configured BaselineStrategy.
    """
    return BaselineStrategy(
        sizer=sizer,
        fast_ema_period=fast_period,
        slow_ema_period=slow_period,
    )
