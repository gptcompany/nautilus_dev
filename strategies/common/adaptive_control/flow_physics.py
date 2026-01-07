"""
Flow Physics - Markets as Fluid/Wave Systems

The deep insight: Markets behave like physical flow systems.

Water Flow     → Liquidity Flow
Air Pressure   → Price Pressure
Sound Waves    → Price Waves
Turbulence     → Volatility

The same differential equations govern:
- Navier-Stokes (fluid dynamics)
- Wave equation (sound/light)
- Diffusion equation (heat, information)

Key concepts applied to markets:
- Resistance (spread, slippage)
- Pressure (buy/sell imbalance)
- Flow rate (volume, velocity)
- Turbulence (volatility clustering)
- Impedance matching (liquidity depth)

This module models markets as physical flow systems.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class FlowState:
    """Current state of the market flow."""

    pressure: float  # Buy vs sell imbalance
    flow_rate: float  # Volume/time
    resistance: float  # Spread + slippage
    turbulence: float  # Volatility
    reynolds_number: float  # Laminar vs turbulent indicator


class MarketFlowAnalyzer:
    """
    Analyzes market as a fluid flow system.

    Key analogy:
    - Price = Pressure
    - Volume = Flow rate
    - Spread = Resistance
    - Volatility = Turbulence

    Fluid dynamics equations adapted for markets:
    - Continuity: Flow in = Flow out (conservation)
    - Momentum: F = ma → Order impact
    - Bernoulli: Pressure + Kinetic = Constant

    Usage:
        flow = MarketFlowAnalyzer()

        # Update with market data
        state = flow.update(
            bid=100.0,
            ask=100.10,
            bid_size=1000,
            ask_size=800,
            last_price=100.05,
            volume=5000,
        )

        # Get flow characteristics
        if state.turbulence > 0.5:
            # High volatility regime
            reduce_position_size()
    """

    def __init__(
        self,
        pressure_window: int = 20,
        viscosity: float = 0.1,
    ):
        """
        Args:
            pressure_window: Bars for pressure calculation
            viscosity: Market "viscosity" (resistance to change)
        """
        self.pressure_window = pressure_window
        self.viscosity = viscosity

        self._price_buffer: list[float] = []
        self._volume_buffer: list[float] = []
        self._imbalance_buffer: list[float] = []
        self._last_state: FlowState | None = None

    def update(
        self,
        bid: float,
        ask: float,
        bid_size: float,
        ask_size: float,
        last_price: float,
        volume: float,
    ) -> FlowState:
        """
        Update flow analysis with new market data.

        Args:
            bid: Best bid price
            ask: Best ask price
            bid_size: Size at bid
            ask_size: Size at ask
            last_price: Last traded price
            volume: Recent volume

        Returns:
            Current FlowState
        """
        # Calculate spread (resistance)
        spread = ask - bid
        mid = (bid + ask) / 2
        relative_spread = spread / mid if mid > 0 else 0

        # Calculate order imbalance (pressure)
        total_size = bid_size + ask_size
        if total_size > 0:
            imbalance = (bid_size - ask_size) / total_size  # -1 to +1
        else:
            imbalance = 0

        self._imbalance_buffer.append(imbalance)
        if len(self._imbalance_buffer) > self.pressure_window:
            self._imbalance_buffer = self._imbalance_buffer[-self.pressure_window :]

        # Average pressure over window
        pressure = sum(self._imbalance_buffer) / len(self._imbalance_buffer)

        # Flow rate (normalized volume)
        self._volume_buffer.append(volume)
        if len(self._volume_buffer) > self.pressure_window:
            self._volume_buffer = self._volume_buffer[-self.pressure_window :]

        avg_volume = sum(self._volume_buffer) / len(self._volume_buffer)
        flow_rate = volume / avg_volume if avg_volume > 0 else 1.0

        # Price for volatility
        self._price_buffer.append(last_price)
        if len(self._price_buffer) > self.pressure_window:
            self._price_buffer = self._price_buffer[-self.pressure_window :]

        # Turbulence (volatility)
        if len(self._price_buffer) >= 2:
            returns = [
                (self._price_buffer[i] - self._price_buffer[i - 1]) / self._price_buffer[i - 1]
                for i in range(1, len(self._price_buffer))
            ]
            turbulence = self._calculate_std(returns)
        else:
            turbulence = 0.0

        # Reynolds number analog
        # High Re = turbulent, Low Re = laminar
        # Re = (flow_rate * characteristic_length) / viscosity
        reynolds = abs(flow_rate * pressure) / self.viscosity if self.viscosity > 0 else 0

        state = FlowState(
            pressure=pressure,
            flow_rate=flow_rate,
            resistance=relative_spread,
            turbulence=turbulence,
            reynolds_number=reynolds,
        )

        self._last_state = state
        return state

    def _calculate_std(self, values: list[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance)

    def get_flow_regime(self) -> str:
        """
        Determine flow regime (laminar vs turbulent).

        Like fluid dynamics:
        - Laminar: Smooth, predictable flow (low Re)
        - Transitional: Mixed behavior
        - Turbulent: Chaotic, volatile (high Re)

        Returns:
            "laminar", "transitional", or "turbulent"
        """
        if self._last_state is None:
            return "unknown"

        re = self._last_state.reynolds_number

        if re < 0.5:
            return "laminar"  # Smooth, mean-reverting
        elif re < 1.5:
            return "transitional"  # Mixed
        else:
            return "turbulent"  # Volatile, trending


class WaveEquationAnalyzer:
    """
    Models price as a wave phenomenon.

    The wave equation: ∂²u/∂t² = c² ∂²u/∂x²

    Applied to markets:
    - u = price deviation from equilibrium
    - c = speed of information propagation
    - x = "space" (market depth, time-to-delivery, etc.)

    This helps understand:
    - How information propagates through markets
    - Reflection at support/resistance (boundary conditions)
    - Standing waves (consolidation patterns)
    - Interference (when multiple trends collide)
    """

    def __init__(self, wave_speed: float = 1.0):
        """
        Args:
            wave_speed: How fast price changes propagate
        """
        self.wave_speed = wave_speed
        self._price_buffer: list[float] = []
        self._equilibrium: float | None = None

    def update(self, price: float) -> None:
        """Add new price observation."""
        self._price_buffer.append(price)
        if len(self._price_buffer) > 500:
            self._price_buffer = self._price_buffer[-500:]

        # Update equilibrium estimate (slow moving average)
        if self._equilibrium is None:
            self._equilibrium = price
        else:
            alpha = 0.01  # Very slow adaptation
            self._equilibrium = alpha * price + (1 - alpha) * self._equilibrium

    def get_displacement(self) -> float:
        """
        Get current displacement from equilibrium.

        Like a wave: how far from rest position.
        """
        if not self._price_buffer or self._equilibrium is None:
            return 0.0
        return self._price_buffer[-1] - self._equilibrium

    def get_velocity(self) -> float:
        """
        Get current price velocity (rate of change).

        In wave terms: ∂u/∂t
        """
        if len(self._price_buffer) < 2:
            return 0.0
        return self._price_buffer[-1] - self._price_buffer[-2]

    def get_acceleration(self) -> float:
        """
        Get current price acceleration.

        In wave terms: ∂²u/∂t²
        """
        if len(self._price_buffer) < 3:
            return 0.0
        v1 = self._price_buffer[-2] - self._price_buffer[-3]
        v2 = self._price_buffer[-1] - self._price_buffer[-2]
        return v2 - v1

    def detect_standing_wave(self, window: int = 50) -> float | None:
        """
        Detect standing wave pattern (consolidation).

        Standing waves occur when waves reflect at boundaries.
        In markets: price bouncing between support and resistance.

        Returns:
            Amplitude of standing wave, or None if not detected
        """
        if len(self._price_buffer) < window:
            return None

        recent = self._price_buffer[-window:]

        # Check for oscillation around equilibrium
        crossings = 0
        eq = self._equilibrium or sum(recent) / len(recent)

        for i in range(1, len(recent)):
            if (recent[i - 1] - eq) * (recent[i] - eq) < 0:
                crossings += 1

        # Standing wave: regular crossings
        expected_crossings = window / 10  # Rough expectation

        if crossings > expected_crossings * 0.7:
            # Calculate amplitude
            high = max(recent)
            low = min(recent)
            return (high - low) / 2

        return None

    def predict_wave_behavior(self) -> dict:
        """
        Predict near-term wave behavior.

        Using simple wave mechanics:
        - Displacement + velocity → momentum
        - Acceleration → changing momentum

        Returns:
            Prediction dict
        """
        d = self.get_displacement()
        v = self.get_velocity()
        a = self.get_acceleration()

        # Simple physics: F = ma, momentum = mv
        momentum = v  # Simplified

        # Energy (kinetic + potential)
        kinetic = 0.5 * v * v
        potential = 0.5 * d * d  # Like spring
        energy = kinetic + potential

        # Prediction
        if momentum > 0 and a > 0:
            direction = "accelerating_up"
        elif momentum > 0 and a < 0:
            direction = "decelerating_up"
        elif momentum < 0 and a < 0:
            direction = "accelerating_down"
        elif momentum < 0 and a > 0:
            direction = "decelerating_down"
        else:
            direction = "neutral"

        # Is this near an extreme? (potential energy high, kinetic low)
        if energy > 0:
            potential_ratio = potential / energy
        else:
            potential_ratio = 0.5

        near_extreme = potential_ratio > 0.7

        return {
            "displacement": d,
            "velocity": v,
            "acceleration": a,
            "momentum": momentum,
            "energy": energy,
            "direction": direction,
            "near_extreme": near_extreme,
            "expected_reversal": near_extreme and abs(v) < 0.01,
        }


class InformationDiffusion:
    """
    Models information spreading through markets.

    The diffusion equation: ∂u/∂t = D * ∂²u/∂x²

    Applied to markets:
    - u = "informed-ness" of market participants
    - D = diffusion coefficient (how fast info spreads)
    - x = participant type (from informed to noise traders)

    This helps understand:
    - How news/information propagates
    - Why some markets are more efficient
    - Time scales of price discovery
    """

    def __init__(self, diffusion_coefficient: float = 0.1):
        """
        Args:
            diffusion_coefficient: How fast information spreads
        """
        self.D = diffusion_coefficient
        self._information_level: float = 0.0
        self._decay_rate: float = 0.05

    def inject_information(self, magnitude: float) -> None:
        """
        Inject new information (like news event).

        Args:
            magnitude: Size of information shock
        """
        self._information_level += magnitude

    def update(self) -> float:
        """
        Update information diffusion (called each bar).

        Information dissipates over time as it becomes "priced in".

        Returns:
            Current information level
        """
        # Exponential decay (information gets absorbed)
        self._information_level *= 1 - self._decay_rate
        return self._information_level

    def get_information_halflife(self) -> float:
        """
        Get halflife of information (bars until half absorbed).

        Returns:
            Number of bars for info to halve
        """
        if self._decay_rate <= 0:
            return float("inf")
        return math.log(2) / self._decay_rate

    def is_informed_period(self, threshold: float = 0.1) -> bool:
        """
        Check if we're in a period of high information.

        During high-info periods:
        - Trends are more reliable
        - Mean reversion is less effective

        Args:
            threshold: Information level threshold

        Returns:
            True if information level is high
        """
        return self._information_level > threshold
