"""
Plotly Backtest Tearsheet Module for NautilusTrader.

This module provides custom extensions to NautilusTrader's native tearsheet system,
including multi-strategy comparison, custom themes, and edge case handling.

Quick Start
-----------
>>> from strategies.common.tearsheet import generate_tearsheet, NAUTILUS_DEV_THEME
>>> from nautilus_trader.analysis import TearsheetConfig
>>>
>>> # Generate basic tearsheet
>>> generate_tearsheet(engine, output_path="tearsheet.html")
>>>
>>> # With custom theme
>>> config = TearsheetConfig(theme="nautilus_dev")
>>> generate_tearsheet(engine, output_path="tearsheet.html", config=config)
>>>
>>> # Multi-strategy comparison
>>> from strategies.common.tearsheet import create_comparison_tearsheet
>>> create_comparison_tearsheet(
...     engines=[engine1, engine2, engine3],
...     strategy_names=["Momentum", "Mean Reversion", "Trend"],
...     output_path="comparison.html",
... )

Native API
----------
This module wraps NautilusTrader's native tearsheet API:
- `nautilus_trader.analysis.tearsheet.create_tearsheet`
- `nautilus_trader.analysis.TearsheetConfig`
- `nautilus_trader.analysis.themes.register_theme`

Custom Extensions
-----------------
- `generate_tearsheet`: Wrapper with edge case handling
- `create_comparison_tearsheet`: Multi-strategy comparison
- `register_custom_charts`: One-time setup for custom charts
- `NAUTILUS_DEV_THEME`: Project-specific theme name

Edge Case Handling
------------------
The wrapper automatically handles:
- Zero trades (displays warning)
- Open positions at backtest end (epoch bug workaround)
- Long backtests (10+ years) with ScatterGL
- High-frequency data (1000+ trades/day) with aggregation
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

# Lazy imports for performance
if TYPE_CHECKING:
    from nautilus_trader.analysis import TearsheetConfig
    from nautilus_trader.backtest.engine import BacktestEngine

__all__ = [
    # Core wrapper
    "generate_tearsheet",
    # Comparison
    "create_comparison_tearsheet",
    "StrategyMetrics",
    "ComparisonConfig",
    # Themes
    "NAUTILUS_DEV_THEME",
    "register_nautilus_dev_theme",
    # Custom charts
    "register_custom_charts",
    # Edge cases
    "check_edge_cases",
    "TearsheetWarning",
]

# Theme name constant
NAUTILUS_DEV_THEME = "nautilus_dev"

_logger = logging.getLogger(__name__)

# Lazy-loaded module references
_themes_module = None
_core_module = None
_comparison_module = None
_edge_cases_module = None
_custom_charts_module = None


def _get_themes():
    """Lazy load themes module."""
    global _themes_module
    if _themes_module is None:
        from strategies.common.tearsheet import themes as _themes_module
    return _themes_module


def _get_core():
    """Lazy load core module."""
    global _core_module
    if _core_module is None:
        from strategies.common.tearsheet import core as _core_module
    return _core_module


def _get_comparison():
    """Lazy load comparison module."""
    global _comparison_module
    if _comparison_module is None:
        from strategies.common.tearsheet import comparison as _comparison_module
    return _comparison_module


def _get_edge_cases():
    """Lazy load edge_cases module."""
    global _edge_cases_module
    if _edge_cases_module is None:
        from strategies.common.tearsheet import edge_cases as _edge_cases_module
    return _edge_cases_module


def _get_custom_charts():
    """Lazy load custom_charts module."""
    global _custom_charts_module
    if _custom_charts_module is None:
        from strategies.common.tearsheet import custom_charts as _custom_charts_module
    return _custom_charts_module


# Public API delegators
def generate_tearsheet(
    engine: BacktestEngine,
    output_path: str = "tearsheet.html",
    config: TearsheetConfig | None = None,
    **kwargs,
) -> str:
    """
    Generate tearsheet with edge case handling.

    This is a wrapper around NautilusTrader's native `create_tearsheet()`
    that adds edge case detection and handling.

    Parameters
    ----------
    engine : BacktestEngine
        Completed backtest engine.
    output_path : str, optional
        Output HTML file path. Default "tearsheet.html".
    config : TearsheetConfig, optional
        Tearsheet configuration. Uses defaults if None.
    **kwargs
        Additional arguments passed to native create_tearsheet().

    Returns
    -------
    str
        Path to generated HTML file.

    Raises
    ------
    TearsheetWarning
        If edge cases detected (zero trades, open positions, etc.)
    """
    result = _get_core().generate_tearsheet(engine, output_path, config, **kwargs)
    return str(result)


def create_comparison_tearsheet(
    engines: list[BacktestEngine],
    strategy_names: list[str] | None = None,
    output_path: str = "comparison.html",
    config: TearsheetConfig | None = None,
    normalize_equity: bool = True,
    colors: list[str] | None = None,
) -> str:
    """
    Generate comparison tearsheet for multiple strategies.

    Parameters
    ----------
    engines : list[BacktestEngine]
        List of completed backtest engines to compare.
    strategy_names : list[str] | None
        Display names for each strategy. If None, uses strategy IDs.
    output_path : str
        Output HTML file path.
    config : TearsheetConfig | None
        Custom configuration. Defaults to comparison-optimized layout.
    normalize_equity : bool
        If True, normalize all equity curves to start at 1.0.
    colors : list[str] | None
        Custom colors for each strategy.

    Returns
    -------
    str
        Path to generated HTML file.
    """
    result = _get_comparison().create_comparison_tearsheet(
        engines, strategy_names, output_path, config, normalize_equity, colors
    )
    return str(result)


def register_nautilus_dev_theme() -> None:
    """Register the nautilus_dev custom theme."""
    _get_themes().register_nautilus_dev_theme()


def register_custom_charts() -> None:
    """
    Register all custom charts (one-time setup).

    Call this once at application startup to register:
    - comparison_equity: Overlaid equity curves
    - comparison_drawdown: Overlaid drawdown charts
    - comparison_stats: Side-by-side metrics table
    - rolling_volatility: Example custom chart
    """
    _get_custom_charts().register_custom_charts()


def check_edge_cases(engine: BacktestEngine) -> list:
    """
    Check for edge cases in backtest results.

    Parameters
    ----------
    engine : BacktestEngine
        Completed backtest engine.

    Returns
    -------
    list[TearsheetWarning]
        List of detected edge case warnings.
    """
    result = _get_edge_cases().check_edge_cases(engine)
    return list(result)


# Re-export classes
def __getattr__(name: str):
    """Lazy attribute loading for classes."""
    if name == "StrategyMetrics":
        return _get_comparison().StrategyMetrics
    if name == "ComparisonConfig":
        return _get_comparison().ComparisonConfig
    if name == "TearsheetWarning":
        return _get_edge_cases().TearsheetWarning
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
