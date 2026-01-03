"""Orderflow Indicators Module (Spec 025).

This module provides orderflow indicators for detecting toxic flow
and predicting short-term price movements.

Components (in development):
- VPINIndicator: Volume-Synchronized Probability of Informed Trading
- HawkesOFI: Hawkes process-based Order Flow Imbalance
- OrderflowManager: Unified interface for strategy integration
- TradeClassifier variants: TickRule, BVC, CloseVsOpen
"""

# Configuration models (available)
from strategies.common.orderflow.config import (
    HawkesConfig,
    OrderflowConfig,
    VPINConfig,
)

__all__ = [
    # Config (available now)
    "VPINConfig",
    "HawkesConfig",
    "OrderflowConfig",
]

# Future exports (uncomment as implemented):
# from strategies.common.orderflow.trade_classifier import (
#     BVCClassifier,
#     CloseVsOpenClassifier,
#     TickRuleClassifier,
#     TradeClassification,
#     TradeSide,
#     create_classifier,
# )
# from strategies.common.orderflow.vpin import (
#     ToxicityLevel,
#     VPINBucket,
#     VPINIndicator,
# )
# from strategies.common.orderflow.hawkes_ofi import (
#     HawkesOFI,
#     HawkesState,
# )
# from strategies.common.orderflow.orderflow_manager import OrderflowManager
