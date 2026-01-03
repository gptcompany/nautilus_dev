"""Position sizing components for NautilusTrader strategies.

This module provides:
- GillerSizer: Sub-linear position sizing based on Graham Giller research
- IntegratedSizer: Unified position sizing combining all factors (Spec 026)
- IntegratedSizingConfig: Configuration for integrated sizing
- IntegratedSize: Result dataclass with factor breakdown
"""

from strategies.common.position_sizing.config import (
    GillerConfig,
    IntegratedSizingConfig,
)
from strategies.common.position_sizing.giller_sizing import GillerSizer
from strategies.common.position_sizing.integrated_sizing import (
    IntegratedSize,
    IntegratedSizer,
)

__all__ = [
    "GillerConfig",
    "GillerSizer",
    "IntegratedSize",
    "IntegratedSizer",
    "IntegratedSizingConfig",
]
