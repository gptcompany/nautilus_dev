"""Contender sizers for baseline validation.

This module provides position sizing implementations for the three contenders:
    - Contender A: AdaptiveSizer (SOPS + Giller + Thompson)
    - Contender B: FixedFractionalSizer (Fixed 2%)
    - Contender C: BuyAndHoldSizer

All sizers follow the ContenderSizer protocol for consistent interface.

Philosophy (PMW - Prove Me Wrong):
    We compare complex (~60 params) vs simple (~3 params) to determine
    if complexity is justified by out-of-sample performance.

Reference:
    - DeMiguel 2009: "1/N beats 14 optimization models OOS"
    - Giller 2020: Sub-linear position sizing (signal^0.5)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from strategies.common.adaptive_control.sops_sizing import SOPSGillerSizer
    from strategies.common.adaptive_control.particle_portfolio import ThompsonSelector


@dataclass
class SizerState:
    """Current state of a sizer for analysis."""

    name: str
    position_size: float
    signal: float
    parameters: dict[str, float]


@runtime_checkable
class ContenderSizer(Protocol):
    """Protocol for contender position sizers.

    All contenders must implement this interface for fair comparison.
    The calculate method takes the same inputs across all sizers.
    """

    @property
    def name(self) -> str:
        """Contender name for reporting."""
        ...

    def calculate(
        self,
        signal: float,
        equity: float,
        entry_price: float,
        stop_loss_price: float,
    ) -> float:
        """Calculate position size.

        Args:
            signal: Trading signal (typically -1 to 1, or unbounded).
            equity: Current account equity.
            entry_price: Expected entry price.
            stop_loss_price: Stop loss price for risk calculation.

        Returns:
            Position size in base units (can be fractional).
        """
        ...

    def update(self, return_value: float, timestamp: float | None = None) -> None:
        """Update internal state with new market data.

        Args:
            return_value: Latest return for volatility estimation.
            timestamp: Current timestamp for tape speed (optional).
        """
        ...

    def get_state(self, signal: float) -> SizerState:
        """Get current state for analysis."""
        ...


class FixedFractionalSizer:
    """Contender B: Fixed 2% risk per trade.

    The simplest baseline - risk a fixed percentage on each trade.

    Parameters:
        - risk_pct: Percentage of equity to risk (default 2%)
        - max_positions: Maximum concurrent positions (default 10)

    This is the "1/N" strategy analog from DeMiguel 2009.
    If this beats the adaptive system, complexity is not justified.
    """

    def __init__(
        self,
        risk_pct: float = 0.02,
        max_positions: int = 10,
    ):
        """Initialize FixedFractionalSizer.

        Args:
            risk_pct: Fraction of equity to risk per trade (0.02 = 2%).
            max_positions: Maximum number of concurrent positions.
        """
        if not 0 < risk_pct <= 1:
            raise ValueError(f"risk_pct must be in (0, 1], got {risk_pct}")
        if max_positions < 1:
            raise ValueError(f"max_positions must be >= 1, got {max_positions}")

        self._risk_pct = risk_pct
        self._max_positions = max_positions
        self._name = f"Fixed {risk_pct * 100:.0f}%"

    @property
    def name(self) -> str:
        """Contender name."""
        return self._name

    def calculate(
        self,
        signal: float,
        equity: float,
        entry_price: float,
        stop_loss_price: float,
    ) -> float:
        """Calculate position size using fixed fractional sizing.

        Args:
            signal: Trading signal (determines direction).
            equity: Current account equity.
            entry_price: Expected entry price.
            stop_loss_price: Stop loss price for risk calculation.

        Returns:
            Position size in base units. Sign matches signal sign.
        """
        # No position if no signal
        if abs(signal) < 1e-10:
            return 0.0

        # Validate inputs
        if equity <= 0 or entry_price <= 0:
            return 0.0

        # Calculate risk amount
        risk_amount = equity * self._risk_pct

        # Calculate risk per unit (distance to stop loss)
        risk_per_unit = abs(entry_price - stop_loss_price)

        if risk_per_unit < 1e-10:
            # Stop loss at entry - use fixed fraction of equity
            return (risk_amount / entry_price) * (1 if signal > 0 else -1)

        # Position size = risk amount / risk per unit
        position_size = risk_amount / risk_per_unit

        # Apply direction from signal
        if signal < 0:
            position_size = -position_size

        return position_size

    def update(self, return_value: float, timestamp: float | None = None) -> None:
        """No-op for fixed sizer (no state to update)."""
        pass

    def get_state(self, signal: float) -> SizerState:
        """Get current state."""
        return SizerState(
            name=self._name,
            position_size=0.0,  # Requires calculate() with actual values
            signal=signal,
            parameters={
                "risk_pct": self._risk_pct,
                "max_positions": float(self._max_positions),
            },
        )


class BuyAndHoldSizer:
    """Contender C: Buy and Hold benchmark.

    Full allocation without rebalancing. This is the ultimate simple baseline.

    Parameters:
        - allocation_pct: Percentage of equity to allocate (default 100%)

    This represents the passive investing baseline.
    """

    def __init__(self, allocation_pct: float = 1.0):
        """Initialize BuyAndHoldSizer.

        Args:
            allocation_pct: Fraction of equity to allocate (1.0 = 100%).
        """
        if not 0 < allocation_pct <= 1:
            raise ValueError(f"allocation_pct must be in (0, 1], got {allocation_pct}")

        self._allocation_pct = allocation_pct
        self._name = "Buy & Hold"
        self._has_position = False

    @property
    def name(self) -> str:
        """Contender name."""
        return self._name

    def calculate(
        self,
        signal: float,
        equity: float,
        entry_price: float,
        stop_loss_price: float,
    ) -> float:
        """Calculate position size for buy and hold.

        Buy and hold always takes a full long position regardless of signal.
        Once positioned, returns 0 to avoid rebalancing.

        Args:
            signal: Trading signal (ignored for B&H).
            equity: Current account equity.
            entry_price: Expected entry price.
            stop_loss_price: Stop loss price (ignored for B&H).

        Returns:
            Position size in base units. Always positive (long only).
        """
        if equity <= 0 or entry_price <= 0:
            return 0.0

        # Buy and hold: allocate once, don't rebalance
        if self._has_position:
            return 0.0

        # Full allocation
        position_size = (equity * self._allocation_pct) / entry_price
        self._has_position = True

        return position_size

    def reset(self) -> None:
        """Reset position state for new validation window."""
        self._has_position = False

    def update(self, return_value: float, timestamp: float | None = None) -> None:
        """No-op for buy and hold (no state to update)."""
        pass

    def get_state(self, signal: float) -> SizerState:
        """Get current state."""
        return SizerState(
            name=self._name,
            position_size=0.0,
            signal=signal,
            parameters={
                "allocation_pct": self._allocation_pct,
                "has_position": float(self._has_position),
            },
        )


class AdaptiveSizer:
    """Contender A: SOPS + Giller + Thompson adaptive sizing.

    The complex adaptive system with ~60 parameters:
        - SOPS: Sigmoidal position sizing with adaptive k
        - Giller: Sub-linear power law scaling (signal^0.5)
        - Thompson: Bayesian strategy selection

    This is what we're trying to validate. If it doesn't beat
    Fixed 2% by Sharpe + 0.2, complexity is NOT justified.

    Philosophy:
        "La gabbia la creiamo noi, non il sistema"
        (The cage is created by us, not the system)

        Fixed parameters are prisons. Let the data speak.
    """

    def __init__(
        self,
        sops_k_base: float = 1.0,
        giller_exponent: float = 0.5,
        thompson_decay: float = 0.99,
        vol_alpha: float = 0.1,
        enable_tape_weight: bool = True,
        max_position_pct: float = 0.10,  # 10% max position
    ):
        """Initialize AdaptiveSizer.

        Args:
            sops_k_base: Base k for SOPS tanh transformation.
            giller_exponent: Power law exponent (0.5 = sqrt).
            thompson_decay: Decay factor for Thompson sampling.
            vol_alpha: EMA alpha for volatility estimation.
            enable_tape_weight: Whether to use tape speed weighting.
            max_position_pct: Maximum position as % of equity.
        """
        self._sops_k_base = sops_k_base
        self._giller_exponent = giller_exponent
        self._thompson_decay = thompson_decay
        self._vol_alpha = vol_alpha
        self._enable_tape_weight = enable_tape_weight
        self._max_position_pct = max_position_pct

        self._name = "SOPS+Giller+Thompson"

        # Lazy initialization to avoid import at module load
        self._sops_sizer: "SOPSGillerSizer | None" = None
        self._thompson: "ThompsonSelector | None" = None

    def _ensure_initialized(self) -> None:
        """Lazily initialize SOPS and Thompson components."""
        if self._sops_sizer is None:
            from strategies.common.adaptive_control.sops_sizing import SOPSGillerSizer
            from strategies.common.adaptive_control.particle_portfolio import (
                ThompsonSelector,
            )

            self._sops_sizer = SOPSGillerSizer(
                k_base=self._sops_k_base,
                vol_alpha=self._vol_alpha,
                giller_power=self._giller_exponent,
                max_position=1.0,
                enable_tape_weight=self._enable_tape_weight,
            )

            # Thompson selector for position sizing strategies
            self._thompson = ThompsonSelector(
                strategies=["aggressive", "moderate", "conservative"],
                decay=self._thompson_decay,
            )

    @property
    def name(self) -> str:
        """Contender name."""
        return self._name

    def calculate(
        self,
        signal: float,
        equity: float,
        entry_price: float,
        stop_loss_price: float,
    ) -> float:
        """Calculate position size using adaptive SOPS+Giller stack.

        Args:
            signal: Trading signal (unbounded, will be transformed).
            equity: Current account equity.
            entry_price: Expected entry price.
            stop_loss_price: Stop loss price for risk calculation.

        Returns:
            Position size in base units. Sign matches signal sign.
        """
        self._ensure_initialized()

        if abs(signal) < 1e-10 or equity <= 0 or entry_price <= 0:
            return 0.0

        assert self._sops_sizer is not None
        assert self._thompson is not None

        # Get SOPS+Giller position (normalized -1 to 1)
        normalized_position = self._sops_sizer.size(signal)

        # Thompson selects sizing strategy
        selected_strategy = self._thompson.select()

        # Apply strategy-specific multiplier
        strategy_multipliers = {
            "aggressive": 1.5,
            "moderate": 1.0,
            "conservative": 0.5,
        }
        multiplier = strategy_multipliers.get(selected_strategy, 1.0)

        # Calculate max position based on equity
        max_position_value = equity * self._max_position_pct
        max_position_units = max_position_value / entry_price

        # Scale normalized position to actual units
        position_size = normalized_position * max_position_units * multiplier

        # Clamp to max position
        position_size = max(-max_position_units, min(max_position_units, position_size))

        return position_size

    def update(self, return_value: float, timestamp: float | None = None) -> None:
        """Update internal state with market data.

        Args:
            return_value: Latest return for volatility estimation.
            timestamp: Current timestamp for tape speed.
        """
        self._ensure_initialized()

        assert self._sops_sizer is not None
        assert self._thompson is not None

        # Update SOPS volatility
        self._sops_sizer.update(
            return_value=return_value,
            timestamp=timestamp,
        )

        # Update Thompson with continuous return
        # Use moderate as default selection for updating
        self._thompson.update_continuous("moderate", return_value)

    def get_state(self, signal: float) -> SizerState:
        """Get current state for analysis."""
        self._ensure_initialized()

        assert self._sops_sizer is not None

        return SizerState(
            name=self._name,
            position_size=0.0,
            signal=signal,
            parameters={
                "sops_k": self._sops_sizer.k,
                "volatility": self._sops_sizer.volatility,
                "tape_regime": (
                    1.0
                    if self._sops_sizer.tape_regime == "fast"
                    else 0.5
                    if self._sops_sizer.tape_regime == "normal"
                    else 0.0
                ),
                "giller_exponent": self._giller_exponent,
            },
        )


def create_sizer(
    contender_type: str,
    config: dict | None = None,
) -> ContenderSizer:
    """Factory function to create sizers by type.

    Args:
        contender_type: One of "adaptive", "fixed", "buyhold".
        config: Optional configuration dict.

    Returns:
        Configured ContenderSizer instance.

    Raises:
        ValueError: If contender_type is unknown.
    """
    config = config or {}

    if contender_type == "adaptive":
        return AdaptiveSizer(
            sops_k_base=config.get("sops_k_base", 1.0),
            giller_exponent=config.get("giller_exponent", 0.5),
            thompson_decay=config.get("thompson_decay", 0.99),
            vol_alpha=config.get("vol_alpha", 0.1),
            enable_tape_weight=config.get("enable_tape_weight", True),
            max_position_pct=config.get("max_position_pct", 0.10),
        )
    elif contender_type == "fixed":
        return FixedFractionalSizer(
            risk_pct=config.get("risk_pct", 0.02),
            max_positions=config.get("max_positions", 10),
        )
    elif contender_type == "buyhold":
        return BuyAndHoldSizer(
            allocation_pct=config.get("allocation_pct", 1.0),
        )
    else:
        raise ValueError(
            f"Unknown contender_type: {contender_type}. Must be one of: adaptive, fixed, buyhold"
        )
