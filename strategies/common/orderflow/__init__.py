"""Orderflow Indicators Module (Spec 025).

This module provides orderflow indicators for detecting toxic flow
and predicting short-term price movements.

Components:
- VPINIndicator: Volume-Synchronized Probability of Informed Trading
- HawkesOFI: Hawkes process-based Order Flow Imbalance
- OrderflowManager: Unified interface for strategy integration
- TradeClassifier variants: TickRule, BVC, CloseVsOpen

Example:
    >>> from strategies.common.orderflow import (
    ...     OrderflowConfig, OrderflowManager, ToxicityLevel
    ... )
    >>> config = OrderflowConfig(enable_vpin=True, enable_hawkes=True)
    >>> manager = OrderflowManager(config)
    >>> for bar in bars:
    ...     manager.handle_bar(bar)
    ...     if manager.toxicity == ToxicityLevel.HIGH:
    ...         print("High toxicity detected!")
"""

# Configuration models
from strategies.common.orderflow.config import (
    HawkesConfig,
    OrderflowConfig,
    VPINConfig,
)

# Trade classification
from strategies.common.orderflow.trade_classifier import (
    BVCClassifier,
    CloseVsOpenClassifier,
    TickRuleClassifier,
    TradeClassification,
    TradeSide,
    create_classifier,
)

# VPIN indicator
from strategies.common.orderflow.vpin import (
    ToxicityLevel,
    VPINBucket,
    VPINIndicator,
    VPINResult,
)

# Hawkes OFI indicator
from strategies.common.orderflow.hawkes_ofi import (
    HawkesOFI,
    HawkesResult,
    HawkesState,
)

# Unified manager
from strategies.common.orderflow.orderflow_manager import (
    OrderflowManager,
    OrderflowResult,
)

__all__ = [
    # Config
    "VPINConfig",
    "HawkesConfig",
    "OrderflowConfig",
    # Trade classification
    "TradeSide",
    "TradeClassification",
    "TickRuleClassifier",
    "BVCClassifier",
    "CloseVsOpenClassifier",
    "create_classifier",
    # VPIN
    "ToxicityLevel",
    "VPINBucket",
    "VPINIndicator",
    "VPINResult",
    # Hawkes OFI
    "HawkesState",
    "HawkesOFI",
    "HawkesResult",
    # Unified manager
    "OrderflowManager",
    "OrderflowResult",
]
