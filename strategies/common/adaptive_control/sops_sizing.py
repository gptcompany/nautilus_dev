"""
SOPS (Sigmoidal Optimal Position Sizing) + TapeSpeed

I Cinque Pilastri (The Five Pillars):
1. Probabilistico - Not predictions, but probability distributions
2. Non Lineare - Power laws, not linear scaling (Giller, Mandelbrot)
3. Non Parametrico - Adaptive to data, not fixed parameters
4. Scalare - Works at any frequency, any asset, any market condition
5. Leggi Naturali - Fibonacci, fractals, wave physics, flow dynamics

This module implements:
- SOPS: Sigmoidal position sizing with adaptive k parameter
- TapeSpeed: Poisson arrival rate estimation (lambda)
- Combined: SOPS → Giller power law → tape weighting → final size

Philosophy:
    "La gabbia la creiamo noi, non il sistema"
    (The cage is created by us, not the system)

    Fixed parameters are prisons. Let the data speak.

TapeSpeed (Pace of Tape):
    In orderflow analysis, "tape speed" refers to how quickly orders arrive.
    High tape speed (many orders/second) = high activity = potential momentum
    Low tape speed (few orders/second) = quiet market = mean reversion

    We model this as a Poisson process with rate parameter lambda (λ).
    λ is estimated using exponential smoothing for real-time adaptation.

Reference:
- Giller (2020): Sub-linear position sizing (signal^0.5)
- Mandelbrot: Power laws in financial markets
- Kelly (1956): Optimal bet sizing
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    pass


@dataclass
class SOPSState:
    """Current state of SOPS sizing."""

    raw_signal: float  # Input signal
    sops_position: float  # After tanh transformation
    giller_position: float  # After power law scaling
    tape_weight: float  # Tape speed multiplier
    final_position: float  # Output position size
    adaptive_k: float  # Current k parameter


@dataclass
class TapeSpeedState:
    """State of tape speed estimation."""

    lambda_rate: float  # Estimated arrival rate
    normalized_speed: float  # 0-1 normalized
    regime: str  # "fast", "normal", "slow"
    weight: float  # Position weight based on speed


class AdaptiveKEstimator:
    """
    Estimate adaptive k for SOPS tanh transformation.

    k controls the "steepness" of the sigmoid:
    - High k = aggressive response to signals (low vol)
    - Low k = dampened response (high vol)

    The key insight: k should be INVERSE to volatility.
    When markets are volatile, dampen the response.
    When markets are calm, amplify the response.

    Formula: k = k_base / (1 + volatility_ratio)

    This makes k non-parametric - it adapts to the data.
    """

    def __init__(
        self,
        k_base: float = 1.0,
        vol_alpha: float = 0.1,  # Volatility EMA smoothing
        lookback: int = 20,  # For rolling baseline
    ):
        """
        Args:
            k_base: Base k value (starting point, not fixed)
            vol_alpha: EMA alpha for volatility estimation
            lookback: Lookback for baseline volatility
        """
        self.k_base = k_base
        self.vol_alpha = vol_alpha
        self.lookback = lookback

        self._vol_ema: Optional[float] = None
        self._vol_baseline: Optional[float] = None
        self._returns_buffer: list[float] = []

    def update(self, return_value: float) -> float:
        """
        Update volatility estimate and return adaptive k.

        Args:
            return_value: Latest return (or proxy for volatility)

        Returns:
            Adaptive k value
        """
        # Update returns buffer for baseline
        self._returns_buffer.append(return_value)
        if len(self._returns_buffer) > self.lookback:
            self._returns_buffer = self._returns_buffer[-self.lookback :]

        # Update volatility EMA (using absolute return as proxy)
        abs_return = abs(return_value)
        if self._vol_ema is None:
            self._vol_ema = abs_return
        else:
            self._vol_ema = (
                self.vol_alpha * abs_return + (1 - self.vol_alpha) * self._vol_ema
            )

        # Calculate baseline volatility (median absolute return)
        if len(self._returns_buffer) >= 10:
            sorted_abs = sorted(abs(r) for r in self._returns_buffer)
            self._vol_baseline = sorted_abs[len(sorted_abs) // 2]
        else:
            self._vol_baseline = self._vol_ema

        return self.k

    @property
    def k(self) -> float:
        """Current adaptive k value."""
        if self._vol_ema is None or self._vol_baseline is None:
            return self.k_base

        if self._vol_baseline <= 1e-10:
            return self.k_base

        # Volatility ratio: current vol / baseline vol
        vol_ratio = self._vol_ema / self._vol_baseline

        # Adaptive k: inversely proportional to vol ratio
        # High vol (ratio > 1) → lower k → dampened response
        # Low vol (ratio < 1) → higher k → amplified response
        adaptive_k = self.k_base / (1 + vol_ratio)

        # Clamp to reasonable range [0.1, 5.0]
        return max(0.1, min(5.0, adaptive_k))

    @property
    def volatility(self) -> float:
        """Current volatility estimate."""
        return self._vol_ema if self._vol_ema is not None else 0.0


class SOPS:
    """
    Sigmoidal Optimal Position Sizing.

    Uses tanh to map signals to position sizes [-1, 1].

    position = tanh(k * signal)

    Why tanh?
    - Bounded output: position is always in [-1, 1]
    - Non-linear: small signals → small positions (proportional)
                 large signals → saturated positions (protection)
    - Symmetric: treats long and short equally
    - Smooth: no discontinuities

    The k parameter controls sensitivity:
    - k = 1: moderate response
    - k > 1: aggressive (saturates quickly)
    - k < 1: conservative (linear-like for small signals)

    In this implementation, k is ADAPTIVE to volatility.
    """

    def __init__(
        self,
        k_base: float = 1.0,
        vol_alpha: float = 0.1,
        max_position: float = 1.0,
    ):
        """
        Args:
            k_base: Base k for tanh (adapts to volatility)
            vol_alpha: EMA alpha for volatility estimation
            max_position: Maximum position size (scaling factor)
        """
        self.max_position = max_position
        self._k_estimator = AdaptiveKEstimator(
            k_base=k_base,
            vol_alpha=vol_alpha,
        )

    def update_volatility(self, return_value: float) -> float:
        """
        Update volatility estimate.

        Call this with each new return to adapt k.

        Args:
            return_value: Latest return

        Returns:
            Updated adaptive k
        """
        return self._k_estimator.update(return_value)

    def size(self, signal: float) -> float:
        """
        Calculate position size from signal.

        Args:
            signal: Trading signal (unbounded)

        Returns:
            Position size in [-max_position, max_position]
        """
        k = self._k_estimator.k
        raw_position = math.tanh(k * signal)
        return raw_position * self.max_position

    @property
    def k(self) -> float:
        """Current adaptive k."""
        return self._k_estimator.k

    @property
    def volatility(self) -> float:
        """Current volatility estimate."""
        return self._k_estimator.volatility


class TapeSpeed:
    """
    Tape Speed Estimator (Poisson Lambda).

    In orderflow analysis, the "tape" is the stream of trades.
    Tape speed = how fast trades are arriving.

    We model this as a Poisson process:
    P(k events in time t) = (λt)^k * e^(-λt) / k!

    where λ (lambda) is the arrival rate.

    Interpretation:
    - High λ (fast tape): Many trades arriving
      → High activity, potential momentum, trend following
    - Low λ (slow tape): Few trades arriving
      → Low activity, mean reversion, fade extremes

    Estimation:
    We use exponential smoothing on inter-arrival times:
    λ_new = α * (1/dt) + (1-α) * λ_old

    This adapts in real-time as market activity changes.
    """

    def __init__(
        self,
        alpha: float = 0.1,  # EMA smoothing
        baseline_lambda: float = 1.0,  # Baseline rate
        fast_threshold: float = 1.5,  # λ/baseline for "fast"
        slow_threshold: float = 0.5,  # λ/baseline for "slow"
    ):
        """
        Args:
            alpha: EMA smoothing factor
            baseline_lambda: Expected baseline arrival rate
            fast_threshold: Ratio above this = fast tape
            slow_threshold: Ratio below this = slow tape
        """
        self.alpha = alpha
        self.baseline_lambda = baseline_lambda
        self.fast_threshold = fast_threshold
        self.slow_threshold = slow_threshold

        self._lambda: Optional[float] = None
        self._last_timestamp: Optional[float] = None
        self._lambda_baseline: Optional[float] = None
        self._lambda_buffer: list[float] = []

    def update(self, timestamp: float, count: int = 1) -> TapeSpeedState:
        """
        Update with new event arrival.

        Args:
            timestamp: Current timestamp (any unit)
            count: Number of events (default 1)

        Returns:
            TapeSpeedState with current estimates
        """
        if self._last_timestamp is not None:
            dt = timestamp - self._last_timestamp
            if dt > 1e-10:
                # Instantaneous rate = count / time
                instant_lambda = count / dt

                if self._lambda is None:
                    self._lambda = instant_lambda
                else:
                    # EMA smoothing
                    self._lambda = (
                        self.alpha * instant_lambda + (1 - self.alpha) * self._lambda
                    )

                # Update baseline buffer
                self._lambda_buffer.append(self._lambda)
                if len(self._lambda_buffer) > 100:
                    self._lambda_buffer = self._lambda_buffer[-100:]

                # Adaptive baseline (median of recent lambdas)
                if len(self._lambda_buffer) >= 20:
                    sorted_lambdas = sorted(self._lambda_buffer)
                    self._lambda_baseline = sorted_lambdas[len(sorted_lambdas) // 2]

        self._last_timestamp = timestamp

        return self.state

    @property
    def state(self) -> TapeSpeedState:
        """Get current tape speed state."""
        lam = self._lambda if self._lambda is not None else self.baseline_lambda
        baseline = (
            self._lambda_baseline
            if self._lambda_baseline is not None
            else self.baseline_lambda
        )

        # Normalized speed (ratio to baseline)
        ratio = lam / baseline if baseline > 1e-10 else 1.0

        # Clamp normalized speed to [0, 2] for weight calculation
        normalized = min(2.0, max(0.0, ratio))

        # Determine regime
        if ratio > self.fast_threshold:
            regime = "fast"
        elif ratio < self.slow_threshold:
            regime = "slow"
        else:
            regime = "normal"

        # Weight: how much to trust momentum signals
        # Fast tape → higher weight for momentum
        # Slow tape → lower weight (mean reversion)
        # Using sqrt for sub-linear scaling (Giller philosophy)
        weight = math.sqrt(normalized)

        return TapeSpeedState(
            lambda_rate=lam,
            normalized_speed=normalized,
            regime=regime,
            weight=weight,
        )

    @property
    def lambda_rate(self) -> float:
        """Current arrival rate estimate."""
        return self._lambda if self._lambda is not None else self.baseline_lambda

    @property
    def regime(self) -> str:
        """Current tape regime."""
        return self.state.regime


class GillerScaler:
    """
    Giller power law position scaling.

    From Giller (2020): Position size should scale SUB-LINEARLY with signal.

    scaled_position = sign(position) * |position|^power

    Default power = 0.5 (square root)

    Why?
    - Protects against large signals (which may be noise)
    - Matches natural scaling laws (Mandelbrot)
    - Kelly-like: don't bet too much even on "sure things"

    Example:
        signal = 1.0 → position = 1.0
        signal = 4.0 → position = 2.0 (not 4.0!)
        signal = 9.0 → position = 3.0 (not 9.0!)
    """

    def __init__(self, power: float = 0.5):
        """
        Args:
            power: Scaling exponent (default 0.5 = square root)
        """
        if power <= 0 or power > 1:
            raise ValueError(f"Power must be in (0, 1], got {power}")
        self.power = power

    def scale(self, position: float) -> float:
        """
        Apply Giller scaling to position.

        Args:
            position: Input position (any value)

        Returns:
            Scaled position (preserves sign, dampens magnitude)
        """
        if position == 0:
            return 0.0

        sign = 1 if position > 0 else -1
        magnitude = abs(position) ** self.power

        return sign * magnitude


class SOPSGillerSizer:
    """
    Combined SOPS + Giller + TapeSpeed position sizer.

    Pipeline:
        signal → SOPS(adaptive k) → Giller(^0.5) → tape_weight → final_size

    This combines:
    1. SOPS: Bounded, sigmoid transformation with adaptive k
    2. Giller: Sub-linear power law scaling
    3. TapeSpeed: Market activity weighting

    All parameters are ADAPTIVE:
    - k adapts to volatility
    - tape baseline adapts to activity
    - No fixed thresholds (all relative to baselines)

    Usage:
        sizer = SOPSGillerSizer()

        for trade in trades:
            # Update internal state
            sizer.update(
                return_value=trade.return_pct,
                timestamp=trade.timestamp,
            )

            # Get position size
            position = sizer.size(signal=trade.signal)

            # Or get full state
            state = sizer.get_state(signal=trade.signal)
    """

    def __init__(
        self,
        k_base: float = 1.0,
        vol_alpha: float = 0.1,
        giller_power: float = 0.5,
        tape_alpha: float = 0.1,
        max_position: float = 1.0,
        enable_tape_weight: bool = True,
        audit_emitter: "AuditEventEmitter | None" = None,
    ):
        """
        Args:
            k_base: Base k for SOPS (adapts to volatility)
            vol_alpha: EMA alpha for volatility
            giller_power: Power law exponent (0.5 = sqrt)
            tape_alpha: EMA alpha for tape speed
            max_position: Maximum final position
            enable_tape_weight: Whether to apply tape weighting
            audit_emitter: Optional audit emitter for logging k changes
        """
        self._sops = SOPS(
            k_base=k_base,
            vol_alpha=vol_alpha,
            max_position=1.0,  # Normalize to 1.0, scale at end
        )
        self._giller = GillerScaler(power=giller_power)
        self._tape = TapeSpeed(alpha=tape_alpha)

        self.max_position = max_position
        self.enable_tape_weight = enable_tape_weight

        # Audit emitter for logging k parameter changes (Spec 030)
        self._audit_emitter = audit_emitter
        self._prev_k: float | None = None
        self._prev_tape_regime: str | None = None

    def update(
        self,
        return_value: float,
        timestamp: Optional[float] = None,
        trade_count: int = 1,
    ) -> None:
        """
        Update internal state with new market data.

        Args:
            return_value: Latest return for volatility estimation
            timestamp: Current timestamp for tape speed
            trade_count: Number of trades in this update
        """
        # Update volatility for SOPS k
        prev_k = self._sops.k
        self._sops.update_volatility(return_value)
        new_k = self._sops.k

        # Audit: Log adaptive k parameter change (significant changes only)
        if self._audit_emitter and self._prev_k is not None:
            if abs(new_k - self._prev_k) > 0.05:  # 5% change threshold
                from strategies.common.audit.events import AuditEventType

                self._audit_emitter.emit_param_change(
                    param_name="adaptive_k",
                    old_value=f"{self._prev_k:.4f}",
                    new_value=f"{new_k:.4f}",
                    trigger_reason=f"volatility={self._sops.volatility:.6f}",
                    source="sops_giller_sizer",
                    event_type=AuditEventType.PARAM_K_CHANGE,
                )
        self._prev_k = new_k

        # Update tape speed if timestamp provided
        if timestamp is not None:
            prev_regime = self._tape.regime
            self._tape.update(timestamp, trade_count)
            new_regime = self._tape.regime

            # Audit: Log tape regime change
            if self._audit_emitter and self._prev_tape_regime is not None:
                if new_regime != self._prev_tape_regime:
                    from strategies.common.audit.events import AuditEventType

                    self._audit_emitter.emit_param_change(
                        param_name="tape_regime",
                        old_value=self._prev_tape_regime,
                        new_value=new_regime,
                        trigger_reason=f"lambda={self._tape.lambda_rate:.4f}",
                        source="sops_giller_sizer",
                        event_type=AuditEventType.PARAM_STATE_CHANGE,
                    )
            self._prev_tape_regime = new_regime

    def size(self, signal: float) -> float:
        """
        Calculate final position size.

        Args:
            signal: Trading signal (unbounded)

        Returns:
            Final position size in [-max_position, max_position]
        """
        # Step 1: SOPS with adaptive k
        sops_position = self._sops.size(signal)

        # Step 2: Giller power law scaling
        giller_position = self._giller.scale(sops_position)

        # Step 3: Tape speed weighting
        if self.enable_tape_weight:
            tape_weight = self._tape.state.weight
        else:
            tape_weight = 1.0

        # Final position
        final = giller_position * tape_weight * self.max_position

        # Clamp to max_position
        return max(-self.max_position, min(self.max_position, final))

    def get_state(self, signal: float) -> SOPSState:
        """
        Get full state information for analysis.

        Args:
            signal: Trading signal

        Returns:
            SOPSState with all intermediate values
        """
        sops_position = self._sops.size(signal)
        giller_position = self._giller.scale(sops_position)

        if self.enable_tape_weight:
            tape_weight = self._tape.state.weight
        else:
            tape_weight = 1.0

        final = giller_position * tape_weight * self.max_position
        final = max(-self.max_position, min(self.max_position, final))

        return SOPSState(
            raw_signal=signal,
            sops_position=sops_position,
            giller_position=giller_position,
            tape_weight=tape_weight,
            final_position=final,
            adaptive_k=self._sops.k,
        )

    @property
    def k(self) -> float:
        """Current adaptive k from SOPS."""
        return self._sops.k

    @property
    def volatility(self) -> float:
        """Current volatility estimate."""
        return self._sops.volatility

    @property
    def tape_regime(self) -> str:
        """Current tape speed regime."""
        return self._tape.regime

    @property
    def tape_lambda(self) -> float:
        """Current tape arrival rate."""
        return self._tape.lambda_rate

    @property
    def audit_emitter(self) -> "AuditEventEmitter | None":
        """Audit emitter for logging k parameter changes."""
        return self._audit_emitter

    @audit_emitter.setter
    def audit_emitter(self, emitter: "AuditEventEmitter | None") -> None:
        """Set the audit emitter."""
        self._audit_emitter = emitter


# Convenience factory function
def create_sops_sizer(
    aggressive: bool = False,
    max_position: float = 1.0,
    use_tape_speed: bool = True,
) -> SOPSGillerSizer:
    """
    Factory function for common configurations.

    Args:
        aggressive: If True, use higher k_base for faster response
        max_position: Maximum position size
        use_tape_speed: Whether to incorporate tape speed

    Returns:
        Configured SOPSGillerSizer
    """
    if aggressive:
        return SOPSGillerSizer(
            k_base=2.0,  # Higher k = faster saturation
            vol_alpha=0.2,  # Faster volatility adaptation
            giller_power=0.6,  # Less dampening
            max_position=max_position,
            enable_tape_weight=use_tape_speed,
        )
    else:
        return SOPSGillerSizer(
            k_base=1.0,  # Conservative
            vol_alpha=0.1,  # Slower adaptation
            giller_power=0.5,  # Standard sqrt
            max_position=max_position,
            enable_tape_weight=use_tape_speed,
        )
