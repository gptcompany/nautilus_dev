"""
Edge case detection and handling for tearsheet generation.

This module provides utilities to detect and handle edge cases that may
cause issues with tearsheet generation:

1. Zero trades (no fills) - Display warning, show N/A for trade metrics
2. Open positions at backtest end - Epoch timestamp bug workaround
3. Long backtests (10+ years) - Use ScatterGL for performance
4. High-frequency trading (1000+ trades/day) - Aggregate for overview
5. All losses (no positive trades) - Charts render normally
6. Missing OHLC data - Skip bars_with_fills gracefully
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nautilus_trader.backtest.engine import BacktestEngine

_logger = logging.getLogger(__name__)


class EdgeCaseType(Enum):
    """Types of edge cases detected."""

    ZERO_TRADES = "zero_trades"
    OPEN_POSITIONS = "open_positions"
    LONG_BACKTEST = "long_backtest"
    HIGH_FREQUENCY = "high_frequency"
    ALL_LOSSES = "all_losses"
    MISSING_OHLC = "missing_ohlc"


class EdgeCaseSeverity(Enum):
    """Severity levels for edge cases."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class TearsheetWarning:
    """
    Warning about an edge case detected in backtest results.

    Attributes
    ----------
    edge_case : EdgeCaseType
        Type of edge case detected.
    severity : EdgeCaseSeverity
        Severity level.
    message : str
        Human-readable warning message.
    recommendation : str
        Suggested action or workaround.
    """

    edge_case: EdgeCaseType
    severity: EdgeCaseSeverity
    message: str
    recommendation: str

    def __str__(self) -> str:
        return f"[{self.severity.value.upper()}] {self.message}"


def check_edge_cases(engine: BacktestEngine) -> list[TearsheetWarning]:
    """
    Check for all edge cases in backtest results.

    Parameters
    ----------
    engine : BacktestEngine
        Completed backtest engine.

    Returns
    -------
    list[TearsheetWarning]
        List of detected edge case warnings.
    """
    warnings = []

    # Check zero trades
    warning = check_zero_trades(engine)
    if warning:
        warnings.append(warning)

    # Check open positions
    warning = check_open_positions(engine)
    if warning:
        warnings.append(warning)

    # Check long backtest
    warning = check_long_backtest(engine)
    if warning:
        warnings.append(warning)

    # Check high frequency
    warning = check_high_frequency(engine)
    if warning:
        warnings.append(warning)

    # Check all losses
    warning = check_all_losses(engine)
    if warning:
        warnings.append(warning)

    return warnings


def check_zero_trades(engine: BacktestEngine) -> TearsheetWarning | None:
    """
    Check for zero trades edge case.

    Parameters
    ----------
    engine : BacktestEngine
        Completed backtest engine.

    Returns
    -------
    TearsheetWarning | None
        Warning if zero trades detected, None otherwise.
    """
    try:
        stats = engine.portfolio.analyzer.get_performance_stats_general()
        total_trades = stats.get("Total Trades", 0)

        if total_trades == 0:
            _logger.warning("Zero trades detected in backtest")
            return TearsheetWarning(
                edge_case=EdgeCaseType.ZERO_TRADES,
                severity=EdgeCaseSeverity.WARNING,
                message="No trades were executed during backtest",
                recommendation="Check strategy logic, entry conditions, or data availability",
            )
    except Exception as e:
        _logger.debug(f"Could not check trade count: {e}")

    return None


def check_open_positions(engine: BacktestEngine) -> TearsheetWarning | None:
    """
    Check for open positions at backtest end (epoch bug).

    Parameters
    ----------
    engine : BacktestEngine
        Completed backtest engine.

    Returns
    -------
    TearsheetWarning | None
        Warning if open positions detected, None otherwise.
    """
    try:
        open_positions = engine.cache.positions_open()

        if open_positions:
            _logger.warning(
                f"Found {len(open_positions)} open positions - "
                "may cause epoch timestamp bug in equity curve"
            )
            return TearsheetWarning(
                edge_case=EdgeCaseType.OPEN_POSITIONS,
                severity=EdgeCaseSeverity.WARNING,
                message=f"{len(open_positions)} open positions at backtest end",
                recommendation="Close all positions before generating tearsheet to avoid epoch bug",
            )
    except Exception as e:
        _logger.debug(f"Could not check open positions: {e}")

    return None


def check_long_backtest(
    engine: BacktestEngine,
    year_threshold: int = 10,
) -> TearsheetWarning | None:
    """
    Check for long backtest (10+ years).

    Parameters
    ----------
    engine : BacktestEngine
        Completed backtest engine.
    year_threshold : int
        Number of years to consider "long".

    Returns
    -------
    TearsheetWarning | None
        Warning if long backtest detected, None otherwise.
    """
    try:
        returns = engine.portfolio.analyzer.returns()
        if len(returns) == 0:
            return None

        days = len(returns)
        years = days / 252  # Approximate trading days per year

        if years >= year_threshold:
            _logger.info(f"Long backtest detected: ~{years:.1f} years")
            return TearsheetWarning(
                edge_case=EdgeCaseType.LONG_BACKTEST,
                severity=EdgeCaseSeverity.INFO,
                message=f"Backtest spans ~{years:.1f} years ({days} data points)",
                recommendation="Using ScatterGL for improved rendering performance",
            )
    except Exception as e:
        _logger.debug(f"Could not check backtest length: {e}")

    return None


def check_high_frequency(
    engine: BacktestEngine,
    trades_per_day_threshold: int = 1000,
) -> TearsheetWarning | None:
    """
    Check for high-frequency trading data.

    Parameters
    ----------
    engine : BacktestEngine
        Completed backtest engine.
    trades_per_day_threshold : int
        Trades per day threshold.

    Returns
    -------
    TearsheetWarning | None
        Warning if high frequency detected, None otherwise.
    """
    try:
        stats = engine.portfolio.analyzer.get_performance_stats_general()
        total_trades = stats.get("Total Trades", 0)

        if total_trades == 0:
            return None

        returns = engine.portfolio.analyzer.returns()
        if len(returns) == 0:
            return None

        days = len(returns)
        trades_per_day = total_trades / max(days, 1)

        if trades_per_day >= trades_per_day_threshold:
            _logger.info(f"High-frequency trading detected: {trades_per_day:.0f} trades/day")
            return TearsheetWarning(
                edge_case=EdgeCaseType.HIGH_FREQUENCY,
                severity=EdgeCaseSeverity.INFO,
                message=f"High-frequency: {trades_per_day:.0f} trades/day average",
                recommendation="Trade data will be aggregated for overview; drill-down available",
            )
    except Exception as e:
        _logger.debug(f"Could not check trade frequency: {e}")

    return None


def check_all_losses(engine: BacktestEngine) -> TearsheetWarning | None:
    """
    Check for all-losses scenario.

    Parameters
    ----------
    engine : BacktestEngine
        Completed backtest engine.

    Returns
    -------
    TearsheetWarning | None
        Warning if all trades are losses, None otherwise.
    """
    try:
        stats = engine.portfolio.analyzer.get_performance_stats_general()
        win_rate = stats.get("Win Rate", 0.0)
        total_trades = stats.get("Total Trades", 0)

        if total_trades > 0 and win_rate == 0.0:
            _logger.warning("All trades are losses")
            return TearsheetWarning(
                edge_case=EdgeCaseType.ALL_LOSSES,
                severity=EdgeCaseSeverity.WARNING,
                message="All trades resulted in losses (0% win rate)",
                recommendation="Review strategy logic and market conditions",
            )
    except Exception as e:
        _logger.debug(f"Could not check win rate: {e}")

    return None


def should_use_scattergl(engine: BacktestEngine, threshold: int = 5000) -> bool:
    """
    Determine if ScatterGL should be used for performance.

    Parameters
    ----------
    engine : BacktestEngine
        Completed backtest engine.
    threshold : int
        Number of data points above which to use ScatterGL.

    Returns
    -------
    bool
        True if ScatterGL should be used.
    """
    try:
        returns = engine.portfolio.analyzer.returns()
        return len(returns) > threshold
    except Exception:
        return False


def should_aggregate_trades(engine: BacktestEngine, threshold: int = 50000) -> bool:
    """
    Determine if trades should be aggregated for display.

    Parameters
    ----------
    engine : BacktestEngine
        Completed backtest engine.
    threshold : int
        Number of data points above which to aggregate.

    Returns
    -------
    bool
        True if aggregation should be used.
    """
    try:
        returns = engine.portfolio.analyzer.returns()
        return len(returns) > threshold
    except Exception:
        return False


def get_aggregation_frequency(data_points: int) -> str:
    """
    Get recommended aggregation frequency based on data size.

    Parameters
    ----------
    data_points : int
        Number of data points.

    Returns
    -------
    str
        Pandas resampling frequency string.
    """
    if data_points > 100000:
        return "W"  # Weekly
    elif data_points > 50000:
        return "D"  # Daily
    elif data_points > 10000:
        return "4h"  # 4-hourly
    else:
        return "h"  # Hourly
