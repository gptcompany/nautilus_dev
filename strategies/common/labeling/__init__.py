"""Triple Barrier Labeling Module (Spec 026).

This module provides triple barrier labeling for trading strategies,
implementing the methodology from Advances in Financial Machine Learning (AFML).

Public API:
    - TripleBarrierLabeler: Main labeler class
    - TripleBarrierConfig: Configuration for labeling parameters
    - TripleBarrierLabel: Enum for label values (-1, 0, +1)
    - BarrierEvent: Detailed event data for analysis
    - get_vertical_barriers: Timeout index calculation
    - get_horizontal_barriers: TP/SL price level calculation
"""

from __future__ import annotations

# Imports will be added as modules are implemented
__all__ = [
    "TripleBarrierLabeler",
    "TripleBarrierConfig",
    "TripleBarrierLabel",
    "BarrierEvent",
    "get_vertical_barriers",
    "get_horizontal_barriers",
]


def __getattr__(name: str):
    """Lazy import to avoid circular dependencies."""
    if name == "TripleBarrierLabel":
        from specs._026_meta_learning_pipeline.contracts.api import TripleBarrierLabel

        return TripleBarrierLabel
    if name == "BarrierEvent":
        from specs._026_meta_learning_pipeline.contracts.api import BarrierEvent

        return BarrierEvent
    if name == "TripleBarrierConfig":
        from strategies.common.labeling.config import TripleBarrierConfig

        return TripleBarrierConfig
    if name == "TripleBarrierLabeler":
        from strategies.common.labeling.triple_barrier import TripleBarrierLabeler

        return TripleBarrierLabeler
    if name in ("get_vertical_barriers", "get_horizontal_barriers"):
        from strategies.common.labeling import label_utils

        return getattr(label_utils, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
