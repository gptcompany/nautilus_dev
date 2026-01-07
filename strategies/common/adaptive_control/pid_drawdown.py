"""
PID Drawdown Controller - Control theory for risk management

Uses a PID controller to dynamically adjust position sizing based on drawdown.
When drawdown increases, position sizes decrease proportionally.

References:
- Standard PID control theory (Åström & Murray, 2008)
- Applied to trading by institutional quant desks
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PIDState:
    """Current PID controller state."""

    error: float  # Current error (drawdown - target)
    integral: float  # Accumulated error
    derivative: float  # Rate of change
    output: float  # Control output (risk multiplier)
    timestamp: float


class PIDDrawdownController:
    """
    PID controller for drawdown-based risk adjustment.

    Automatically reduces position sizes as drawdown increases.
    Uses control theory to smooth the response and avoid oscillation.

    Usage:
        pid = PIDDrawdownController(
            target_drawdown=0.02,  # 2% target max drawdown
            Kp=2.0,   # Proportional gain
            Ki=0.1,   # Integral gain
            Kd=0.5,   # Derivative gain
        )

        # Update with current drawdown
        multiplier = pid.update(current_drawdown=0.03)  # 3% drawdown
        # multiplier will be < 1.0, reducing position sizes

        # Use in strategy
        position_size = base_size * multiplier
    """

    def __init__(
        self,
        target_drawdown: float = 0.02,  # 2% target
        Kp: float = 2.0,  # Proportional gain
        Ki: float = 0.1,  # Integral gain
        Kd: float = 0.5,  # Derivative gain
        min_output: float = 0.0,  # Minimum multiplier (0 = full stop)
        max_output: float = 1.0,  # Maximum multiplier (1 = full size)
        integral_limit: float = 0.5,  # Anti-windup limit
    ):
        """
        Args:
            target_drawdown: Desired maximum drawdown (as decimal)
            Kp: Proportional gain - how strongly to react to current error
            Ki: Integral gain - how strongly to react to accumulated error
            Kd: Derivative gain - how strongly to react to error change rate
            min_output: Minimum risk multiplier
            max_output: Maximum risk multiplier
            integral_limit: Max absolute integral to prevent windup
        """
        self.target_drawdown = target_drawdown
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.min_output = min_output
        self.max_output = max_output
        self.integral_limit = integral_limit

        self._integral: float = 0.0
        self._prev_error: float | None = None
        self._step_count: int = 0

    def update(self, current_drawdown: float, dt: float = 1.0) -> float:
        """
        Update PID controller with current drawdown.

        Args:
            current_drawdown: Current drawdown as decimal (e.g., 0.03 for 3%)
            dt: Time step (default 1.0 for discrete steps)

        Returns:
            Risk multiplier between min_output and max_output
        """
        # Calculate error (positive when above target)
        error = current_drawdown - self.target_drawdown

        # Proportional term
        P = self.Kp * error

        # Integral term with anti-windup
        self._integral += error * dt
        self._integral = max(-self.integral_limit, min(self.integral_limit, self._integral))
        I = self.Ki * self._integral

        # Derivative term
        if self._prev_error is not None:
            derivative = (error - self._prev_error) / dt
        else:
            derivative = 0.0
        D = self.Kd * derivative

        self._prev_error = error
        self._step_count += 1

        # PID output (inverted: higher error = lower output)
        pid_output = P + I + D

        # Convert to multiplier: 0 error = 1.0 output, high error = low output
        # Sigmoid-like mapping for smooth response
        multiplier = 1.0 / (1.0 + pid_output)

        # Clamp to limits
        multiplier = max(self.min_output, min(self.max_output, multiplier))

        logger.debug(
            f"PID: dd={current_drawdown:.3f}, err={error:.3f}, "
            f"P={P:.3f}, I={I:.3f}, D={D:.3f}, mult={multiplier:.3f}"
        )

        return multiplier

    def reset(self) -> None:
        """Reset controller state."""
        self._integral = 0.0
        self._prev_error = None
        self._step_count = 0

    def get_state(self) -> PIDState:
        """Get current controller state."""
        return PIDState(
            error=self._prev_error or 0.0,
            integral=self._integral,
            derivative=0.0,  # Would need to track
            output=1.0 / (1.0 + (self._prev_error or 0.0)),
            timestamp=float(self._step_count),
        )


class SimpleDrawdownScaler:
    """
    Simple linear drawdown-based risk scaling.

    For when PID is overkill. Just linearly scales down as drawdown increases.
    """

    def __init__(
        self,
        start_reduction: float = 0.02,  # Start reducing at 2% drawdown
        full_stop: float = 0.10,  # Stop trading at 10% drawdown
    ):
        """
        Args:
            start_reduction: Drawdown at which to start reducing (decimal)
            full_stop: Drawdown at which to stop completely (decimal)
        """
        if start_reduction >= full_stop:
            raise ValueError("start_reduction must be less than full_stop")

        self.start_reduction = start_reduction
        self.full_stop = full_stop

    def get_multiplier(self, current_drawdown: float) -> float:
        """
        Get risk multiplier based on current drawdown.

        Args:
            current_drawdown: Current drawdown as decimal

        Returns:
            Multiplier between 0.0 and 1.0
        """
        if current_drawdown <= self.start_reduction:
            return 1.0
        elif current_drawdown >= self.full_stop:
            return 0.0
        else:
            # Linear interpolation
            range_pct = (current_drawdown - self.start_reduction) / (
                self.full_stop - self.start_reduction
            )
            return 1.0 - range_pct
