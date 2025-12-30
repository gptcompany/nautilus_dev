"""
Alpha-Evolve Strategy Templates.

Provides evolvable strategy templates for NautilusTrader:
- BaseEvolveStrategy: Abstract base with EVOLVE-BLOCK markers
- MomentumEvolveStrategy: Seed strategy using EMA crossover
"""

from scripts.alpha_evolve.templates.base import (
    BaseEvolveConfig,
    BaseEvolveStrategy,
    EquityPoint,
)
from scripts.alpha_evolve.templates.momentum import (
    MomentumEvolveConfig,
    MomentumEvolveStrategy,
)

__all__ = [
    # Base
    "BaseEvolveConfig",
    "BaseEvolveStrategy",
    "EquityPoint",
    # Momentum seed
    "MomentumEvolveConfig",
    "MomentumEvolveStrategy",
]
