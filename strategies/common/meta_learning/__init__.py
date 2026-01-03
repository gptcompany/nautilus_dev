"""Meta-Learning Module (Spec 026).

This module provides meta-labeling and meta-model training for trading strategies,
implementing the secondary model approach from Advances in Financial Machine Learning.

Public API:
    - MetaModel: RandomForest-based meta-model
    - MetaModelConfig: Configuration for meta-model training
    - MetaLabelGenerator: Creates meta-labels from primary signals
    - WalkForwardSplitter: Walk-forward validation splits
    - WalkForwardConfig: Configuration for walk-forward validation
    - extract_meta_features: Feature engineering for meta-model
"""

from __future__ import annotations

__all__ = [
    "MetaModel",
    "MetaModelConfig",
    "MetaLabelGenerator",
    "WalkForwardSplitter",
    "WalkForwardConfig",
    "extract_meta_features",
]


def __getattr__(name: str):
    """Lazy import to avoid circular dependencies."""
    if name in ("MetaModelConfig", "WalkForwardConfig"):
        from strategies.common.meta_learning.config import (
            MetaModelConfig,
            WalkForwardConfig,
        )

        return MetaModelConfig if name == "MetaModelConfig" else WalkForwardConfig
    if name == "MetaModel":
        from strategies.common.meta_learning.meta_model import MetaModel

        return MetaModel
    if name == "MetaLabelGenerator":
        from strategies.common.meta_learning.meta_label import MetaLabelGenerator

        return MetaLabelGenerator
    if name == "WalkForwardSplitter":
        from strategies.common.meta_learning.walk_forward import WalkForwardSplitter

        return WalkForwardSplitter
    if name == "extract_meta_features":
        from strategies.common.meta_learning.feature_engineering import (
            extract_meta_features,
        )

        return extract_meta_features
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
