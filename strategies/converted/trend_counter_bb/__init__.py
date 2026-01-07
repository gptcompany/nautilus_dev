# Trend Counter [BigBeluga Style] - Converted from Pine Script
# This is a test conversion to validate the /pinescript skill

from .indicator import Trend, TrendCounterIndicator
from .trend_counter_strategy import TrendCounterBBConfig, TrendCounterBBStrategy

__all__ = [
    "TrendCounterBBStrategy",
    "TrendCounterBBConfig",
    "TrendCounterIndicator",
    "Trend",
]
