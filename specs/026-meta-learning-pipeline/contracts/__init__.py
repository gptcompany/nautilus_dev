"""API Contracts for Meta-Learning Pipeline (Spec 026).

This package defines the public interfaces for the meta-learning pipeline.
"""

from specs._026_meta_learning_pipeline.contracts.api import (
    BarrierEvent,
    BaseBOCD,
    BaseIntegratedSizer,
    BaseMetaModel,
    BaseTripleBarrierLabeler,
    BOCDProtocol,
    Changepoint,
    IntegratedSize,
    IntegratedSizerProtocol,
    MetaModelProtocol,
    TripleBarrierLabel,
    TripleBarrierLabelerProtocol,
)

__all__ = [
    # Enums
    "TripleBarrierLabel",
    # Data Classes
    "BarrierEvent",
    "Changepoint",
    "IntegratedSize",
    # Protocols
    "TripleBarrierLabelerProtocol",
    "MetaModelProtocol",
    "BOCDProtocol",
    "IntegratedSizerProtocol",
    # Abstract Base Classes
    "BaseTripleBarrierLabeler",
    "BaseMetaModel",
    "BaseBOCD",
    "BaseIntegratedSizer",
]
