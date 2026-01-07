"""
Custom chart registration for NautilusTrader tearsheets.

This module provides utilities to register custom charts that extend
NautilusTrader's native tearsheet system.

Example
-------
>>> from strategies.common.tearsheet import register_custom_charts
>>> register_custom_charts()  # One-time setup
>>>
>>> # Custom charts are now available in tearsheets
>>> config = TearsheetConfig(charts=["rolling_volatility"])
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    import plotly.graph_objects as go

_logger = logging.getLogger(__name__)

# Track registration state
_charts_registered = False


def register_custom_charts() -> None:
    """
    Register all custom charts (one-time setup).

    This function registers project-specific charts that extend
    NautilusTrader's native tearsheet system:

    - rolling_volatility: 30-day rolling standard deviation

    Call this once at application startup. Subsequent calls are no-ops.
    """
    global _charts_registered

    if _charts_registered:
        _logger.debug("Custom charts already registered")
        return

    try:
        _register_rolling_volatility()
        _charts_registered = True
        _logger.info("Registered custom tearsheet charts")
    except ImportError as e:
        _logger.warning(f"Could not register custom charts: {e}")
    except Exception as e:
        _logger.error(f"Failed to register custom charts: {e}")


def _register_chart(name: str, chart_func: Callable[..., Any]) -> None:
    """
    Register a custom chart with NautilusTrader.

    Parameters
    ----------
    name : str
        Chart name for configuration.
    chart_func : callable
        Function that creates the chart figure.
    """
    try:
        from nautilus_trader.analysis.charts import register_chart

        register_chart(name=name, chart_func=chart_func)
        _logger.debug(f"Registered custom chart: {name}")
    except ImportError:
        _logger.warning(
            "Could not import chart registration - "
            "ensure NautilusTrader visualization extra is installed"
        )
    except Exception as e:
        _logger.error(f"Failed to register chart {name}: {e}")


def _register_rolling_volatility() -> None:
    """Register the rolling volatility chart."""
    _register_chart("rolling_volatility", create_rolling_volatility_chart)


def create_rolling_volatility_chart(
    returns: pd.Series,
    window: int = 30,
    annualize: bool = True,
    **kwargs,
) -> go.Figure:
    """
    Create a rolling volatility chart.

    Parameters
    ----------
    returns : pd.Series
        Returns series with DatetimeIndex.
    window : int
        Rolling window size in periods.
    annualize : bool
        Whether to annualize volatility.
    **kwargs
        Additional keyword arguments (ignored).

    Returns
    -------
    go.Figure
        Plotly figure with rolling volatility.
    """
    import plotly.graph_objects as go

    # Calculate rolling volatility
    rolling_vol = returns.rolling(window=window).std()

    # Annualize if requested (assuming daily data)
    if annualize:
        rolling_vol = rolling_vol * (252**0.5)

    # Create figure
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=rolling_vol.index,
            y=rolling_vol.values,
            mode="lines",
            name=f"{window}-Day Rolling Volatility",
            line={"color": "#6366f1", "width": 2},
            fill="tozeroy",
            fillcolor="rgba(99, 102, 241, 0.1)",
        )
    )

    # Add mean line (skip if all NaN)
    mean_vol = rolling_vol.mean()
    if pd.notna(mean_vol):
        fig.add_hline(
            y=mean_vol,
            line_dash="dash",
            line_color="#94a3b8",
            annotation_text=f"Mean: {mean_vol:.2%}",
            annotation_position="bottom right",
        )

    fig.update_layout(
        title=f"Rolling Volatility ({window}-Day Window)",
        xaxis_title="Date",
        yaxis_title="Volatility (Annualized)" if annualize else "Volatility",
        yaxis_tickformat=".1%",
        showlegend=False,
        height=350,
    )

    return fig


def is_charts_registered() -> bool:
    """Check if custom charts have been registered."""
    return _charts_registered
