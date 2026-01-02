"""Position sizing components for NautilusTrader strategies.

This module provides:
- GillerSizer: Sub-linear position sizing based on Graham Giller research
"""

from strategies.common.position_sizing.config import GillerConfig
from strategies.common.position_sizing.giller_sizing import GillerSizer

__all__ = [
    "GillerConfig",
    "GillerSizer",
]
