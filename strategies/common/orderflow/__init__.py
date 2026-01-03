"""Orderflow Indicators Module (Spec 025).

This module provides orderflow indicators for detecting toxic flow
and predicting short-term price movements.

Components:
- VPINIndicator: Volume-Synchronized Probability of Informed Trading
- HawkesOFI: Hawkes process-based Order Flow Imbalance
- OrderflowManager: Unified interface for strategy integration
- TradeClassifier variants: TickRule, BVC, CloseVsOpen
"""

from strategies.common.orderflow.config import (
    HawkesConfig,
    OrderflowConfig,
    VPINConfig,
)
from strategies.common.orderflow.trade_classifier import (
    BVCClassifier,
    CloseVsOpenClassifier,
    TickRuleClassifier,
    TradeClassification,
    TradeSide,
    create_classifier,
)
from strategies.common.orderflow.vpin import (
    ToxicityLevel,
    VPINBucket,
    VPINIndicator,
)
from strategies.common.orderflow.hawkes_ofi import (
    HawkesOFI,
    HawkesState,
)
from strategies.common.orderflow.orderflow_manager import OrderflowManager

__all__ = [
    # Config
    "VPINConfig",
    "HawkesConfig",
    "OrderflowConfig",
    # Trade Classification
    "TradeClassification",
    "TradeSide",
    "TickRuleClassifier",
    "BVCClassifier",
    "CloseVsOpenClassifier",
    "create_classifier",
    # VPIN
    "VPINIndicator",
    "VPINBucket",
    "ToxicityLevel",
    # Hawkes OFI
    "HawkesOFI",
    "HawkesState",
    # Manager
    "OrderflowManager",
]
