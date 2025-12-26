# monitoring.constants - Centralized constants for monitoring collectors
#
# Centralized validation constants to avoid duplication across collectors

from typing import Literal

# Valid exchange names (must match models literal types)
VALID_EXCHANGES = frozenset(("binance", "bybit", "okx", "dydx"))

# Valid data types for pipeline metrics
VALID_DATA_TYPES = frozenset(("oi", "funding", "liquidation"))

# Type aliases for convenience
Exchange = Literal["binance", "bybit", "okx", "dydx"]
DataType = Literal["oi", "funding", "liquidation"]
Environment = Literal["prod", "staging", "dev"]

__all__ = [
    "VALID_EXCHANGES",
    "VALID_DATA_TYPES",
    "Exchange",
    "DataType",
    "Environment",
]
