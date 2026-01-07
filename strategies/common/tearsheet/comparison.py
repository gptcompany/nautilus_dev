"""
Multi-Strategy Comparison Module for NautilusTrader Tearsheets.

This module provides classes and functions for comparing multiple strategy
backtests side-by-side with overlaid equity curves, drawdown charts, and
statistics tables.

Alpha-Evolve Decision:
    Selected Approach B (Pydantic-Style Validation) for:
    - Better error messages for invalid configurations
    - Helper methods for chart rendering (get_colors, normalized_equity)
    - ClassVar constants for clear defaults
    - Proper validation without over-engineering

    Fitness Scores:
    | Approach | Tests | Performance | Quality | Edge Cases | Total |
    |----------|-------|-------------|---------|------------|-------|
    | A - Minimal | 10/10 | 9/10 | 7/10 | 6/10 | 39/50 |
    | B - Pydantic-Style | 10/10 | 8/10 | 9/10 | 9/10 | 45/50 |
    | C - Factory | 10/10 | 7/10 | 8/10 | 8/10 | 41/50 |

Example
-------
>>> from strategies.common.tearsheet.comparison import (
...     StrategyMetrics,
...     ComparisonConfig,
...     create_comparison_tearsheet,
... )
>>>
>>> # Extract metrics from engines
>>> metrics = [
...     StrategyMetrics.from_engine(engine1, "Momentum"),
...     StrategyMetrics.from_engine(engine2, "Mean Reversion"),
...     StrategyMetrics.from_engine(engine3, "Trend"),
... ]
>>>
>>> # Create comparison tearsheet
>>> create_comparison_tearsheet(
...     engines=[engine1, engine2, engine3],
...     strategy_names=["Momentum", "Mean Reversion", "Trend"],
...     output_path="comparison.html",
... )
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

import pandas as pd

if TYPE_CHECKING:
    from nautilus_trader.analysis import TearsheetConfig
    from nautilus_trader.backtest.engine import BacktestEngine

    import plotly.graph_objects as go

__all__ = [
    "StrategyMetrics",
    "ComparisonConfig",
    "create_comparison_tearsheet",
    "render_comparison_equity",
    "render_comparison_drawdown",
    "render_comparison_stats_table",
]

_logger = logging.getLogger(__name__)


# =============================================================================
# T051: StrategyMetrics Dataclass
# =============================================================================


@dataclass
class StrategyMetrics:
    """
    Aggregated metrics for a single strategy in comparison view.

    This dataclass holds all performance metrics extracted from a completed
    backtest engine, formatted for comparison with other strategies.

    Attributes
    ----------
    name : str
        Display name for the strategy.
    total_pnl : Decimal
        Total profit/loss in base currency.
    sharpe_ratio : float
        Sharpe ratio (252-day annualized).
    sortino_ratio : float
        Sortino ratio (252-day annualized).
    max_drawdown : float
        Maximum drawdown percentage (negative).
    win_rate : float
        Percentage of winning trades (0-1).
    profit_factor : float
        Ratio of gross profits to gross losses.
    total_trades : int
        Total number of closed trades.
    avg_trade_duration : str
        Average trade duration as formatted string.
    returns_series : pd.Series
        Daily returns time series for charting.
    raw_stats : dict[str, Any]
        Original stats dict from PortfolioAnalyzer.

    Example
    -------
    >>> metrics = StrategyMetrics.from_engine(engine, "My Strategy")
    >>> print(f"Sharpe: {metrics.sharpe_ratio:.2f}")
    >>> print(f"Win Rate: {metrics.win_rate:.1%}")
    """

    name: str
    total_pnl: Decimal
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    total_trades: int
    avg_trade_duration: str
    returns_series: pd.Series
    raw_stats: dict[str, Any]

    # Default values for missing statistics
    _STAT_DEFAULTS: ClassVar[dict[str, Any]] = {
        "Sharpe Ratio (252 days)": 0.0,
        "Sortino Ratio (252 days)": 0.0,
        "Max Drawdown": 0.0,
        "Win Rate": 0.0,
        "Profit Factor": 0.0,
        "Total Trades": 0,
        "Avg Trade Duration": "N/A",
    }

    @classmethod
    def from_engine(cls, engine: "BacktestEngine", name: str) -> "StrategyMetrics":
        """
        Extract metrics from a completed backtest engine.

        Parameters
        ----------
        engine : BacktestEngine
            Completed backtest engine with portfolio data.
        name : str
            Display name for this strategy.

        Returns
        -------
        StrategyMetrics
            Extracted metrics ready for comparison.

        Example
        -------
        >>> metrics = StrategyMetrics.from_engine(engine, "Momentum Strategy")
        >>> assert metrics.name == "Momentum Strategy"
        """
        analyzer = engine.portfolio.analyzer

        stats_pnls = analyzer.get_performance_stats_pnls()
        stats_returns = analyzer.get_performance_stats_returns()
        stats_general = analyzer.get_performance_stats_general()

        # Helper to get stat with default fallback (handles None values)
        def get_stat(stats: dict, key: str) -> Any:
            value = stats.get(key)
            if value is None:
                return cls._STAT_DEFAULTS.get(key)
            return value

        # Aggregate PnL across all currencies (handles None values)
        total_pnl = Decimal(0)
        for currency_stats in stats_pnls.values():
            pnl_value = currency_stats.get("PnL (total)")
            if pnl_value is not None:
                total_pnl += Decimal(str(pnl_value))

        return cls(
            name=name,
            total_pnl=total_pnl,
            sharpe_ratio=get_stat(stats_returns, "Sharpe Ratio (252 days)"),
            sortino_ratio=get_stat(stats_returns, "Sortino Ratio (252 days)"),
            max_drawdown=get_stat(stats_returns, "Max Drawdown"),
            win_rate=get_stat(stats_general, "Win Rate"),
            profit_factor=get_stat(stats_general, "Profit Factor"),
            total_trades=get_stat(stats_general, "Total Trades"),
            avg_trade_duration=get_stat(stats_general, "Avg Trade Duration"),
            returns_series=analyzer.returns(),
            raw_stats={
                "pnls": stats_pnls,
                "returns": stats_returns,
                "general": stats_general,
            },
        )

    @property
    def cumulative_returns(self) -> pd.Series:
        """
        Calculate cumulative returns from returns series.

        Returns
        -------
        pd.Series
            Cumulative returns starting from 1.0.
        """
        if self.returns_series.empty:
            return pd.Series(dtype=float)
        return (1 + self.returns_series).cumprod()

    @property
    def normalized_equity(self) -> pd.Series:
        """
        Get equity curve normalized to start at 1.0.

        This is useful for comparing strategies with different starting capital.

        Returns
        -------
        pd.Series
            Normalized equity curve.
        """
        cumulative = self.cumulative_returns
        if cumulative.empty:
            return cumulative
        first_value = cumulative.iloc[0]
        if first_value == 0:
            # Avoid division by zero - return cumulative as-is
            _logger.warning("Cumulative returns starts at 0, cannot normalize")
            return cumulative
        return cumulative / first_value

    @property
    def drawdown_series(self) -> pd.Series:
        """
        Calculate drawdown series from returns.

        Returns
        -------
        pd.Series
            Drawdown values (negative percentages from peak).
        """
        cumulative = self.cumulative_returns
        if cumulative.empty:
            return pd.Series(dtype=float)
        running_max = cumulative.cummax()
        # Avoid division by zero when running_max is 0
        # Replace 0 with NaN before division, then fill back with 0
        safe_max = running_max.replace(0, float("nan"))
        drawdown = (cumulative - running_max) / safe_max
        # Replace inf/-inf/NaN with 0
        drawdown = drawdown.replace([float("inf"), float("-inf")], float("nan"))
        drawdown = drawdown.fillna(0)
        return drawdown


# =============================================================================
# T052: ComparisonConfig Dataclass
# =============================================================================


@dataclass
class ComparisonConfig:
    """
    Configuration for multi-strategy comparison tearsheet.

    This config controls how multiple strategies are displayed in comparison
    charts, including color schemes and normalization options.

    Attributes
    ----------
    strategy_names : list[str]
        Display names for each strategy (must have 2-10 entries).
    normalize_equity : bool
        If True, normalize all equity curves to start at 1.0.
    show_individual_stats : bool
        If True, show individual strategy stats tables.
    show_comparison_table : bool
        If True, show side-by-side metrics comparison table.
    colors : list[str] | None
        Custom colors for each strategy. Uses Plotly defaults if None.

    Raises
    ------
    ValueError
        If fewer than 2 or more than 10 strategies provided.
        If colors length doesn't match strategy_names length.

    Example
    -------
    >>> config = ComparisonConfig(
    ...     strategy_names=["Momentum", "Mean Reversion", "Trend"],
    ...     normalize_equity=True,
    ...     colors=["#1f77b4", "#ff7f0e", "#2ca02c"],
    ... )
    >>> assert len(config.strategy_names) == 3
    """

    strategy_names: list[str]
    normalize_equity: bool = True
    show_individual_stats: bool = True
    show_comparison_table: bool = True
    colors: list[str] | None = None

    # Plotly's default qualitative color sequence
    DEFAULT_COLORS: ClassVar[list[str]] = [
        "#636EFA",  # Blue
        "#EF553B",  # Red
        "#00CC96",  # Green
        "#AB63FA",  # Purple
        "#FFA15A",  # Orange
        "#19D3F3",  # Cyan
        "#FF6692",  # Pink
        "#B6E880",  # Light Green
        "#FF97FF",  # Magenta
        "#FECB52",  # Yellow
    ]

    MIN_STRATEGIES: ClassVar[int] = 2
    MAX_STRATEGIES: ClassVar[int] = 10

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        self._validate_strategy_names()
        self._validate_colors()

    def _validate_strategy_names(self) -> None:
        """Validate strategy_names has correct length."""
        count = len(self.strategy_names)
        if count < self.MIN_STRATEGIES:
            raise ValueError(
                f"ComparisonConfig requires at least {self.MIN_STRATEGIES} strategies, got {count}"
            )
        if count > self.MAX_STRATEGIES:
            raise ValueError(
                f"ComparisonConfig supports at most {self.MAX_STRATEGIES} strategies, got {count}"
            )

    def _validate_colors(self) -> None:
        """Validate colors length matches strategy_names if provided."""
        if self.colors is not None:
            if len(self.colors) != len(self.strategy_names):
                raise ValueError(
                    f"colors length ({len(self.colors)}) must match "
                    f"strategy_names length ({len(self.strategy_names)})"
                )

    def get_colors(self) -> list[str]:
        """
        Get colors for each strategy, using defaults if not specified.

        Returns
        -------
        list[str]
            Hex color codes for each strategy.
        """
        if self.colors is not None:
            return self.colors
        return self.DEFAULT_COLORS[: len(self.strategy_names)]


# =============================================================================
# T053: Comparison Equity Chart Renderer [E]
# =============================================================================


def render_comparison_equity(
    metrics_list: list[StrategyMetrics],
    config: ComparisonConfig | None = None,
    title: str = "Equity Curve Comparison",
) -> "go.Figure":
    """
    Render overlaid equity curves for multiple strategies.

    This function creates a Plotly figure with multiple equity curves
    overlaid for visual comparison. Supports normalization to start all
    curves at 1.0 for fair comparison.

    Parameters
    ----------
    metrics_list : list[StrategyMetrics]
        List of strategy metrics to compare.
    config : ComparisonConfig | None
        Comparison configuration. If None, creates default config.
    title : str
        Chart title.

    Returns
    -------
    go.Figure
        Plotly figure with overlaid equity curves.

    Example
    -------
    >>> fig = render_comparison_equity(
    ...     [metrics1, metrics2, metrics3],
    ...     config=ComparisonConfig(
    ...         strategy_names=["A", "B", "C"],
    ...         normalize_equity=True,
    ...     ),
    ... )
    >>> fig.write_html("equity_comparison.html")
    """
    import plotly.graph_objects as go

    # Create default config if not provided
    if config is None:
        config = ComparisonConfig(
            strategy_names=[m.name for m in metrics_list],
            normalize_equity=True,
        )

    colors = config.get_colors()
    fig = go.Figure()

    for i, metrics in enumerate(metrics_list):
        # Get equity curve based on normalization setting
        if config.normalize_equity:
            equity = metrics.normalized_equity
            y_label = "Normalized Equity"
        else:
            equity = metrics.cumulative_returns
            y_label = "Cumulative Returns"

        if equity.empty:
            _logger.warning(f"Strategy '{metrics.name}' has no returns data")
            continue

        fig.add_trace(
            go.Scatter(
                x=equity.index,
                y=equity.values,
                mode="lines",
                name=metrics.name,
                line={"color": colors[i % len(colors)], "width": 2},
                hovertemplate=(
                    f"<b>{metrics.name}</b><br>Date: %{{x}}<br>Value: %{{y:.4f}}<br><extra></extra>"
                ),
            )
        )

    fig.update_layout(
        title={
            "text": title,
            "x": 0.5,
            "xanchor": "center",
        },
        xaxis_title="Date",
        yaxis_title=y_label if config.normalize_equity else "Cumulative Returns",
        hovermode="x unified",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
        },
        template="plotly_white",
    )

    return fig


# =============================================================================
# T054: Comparison Drawdown Chart Renderer
# =============================================================================


def render_comparison_drawdown(
    metrics_list: list[StrategyMetrics],
    config: ComparisonConfig | None = None,
    title: str = "Drawdown Comparison",
) -> "go.Figure":
    """
    Render overlaid drawdown charts for multiple strategies.

    Parameters
    ----------
    metrics_list : list[StrategyMetrics]
        List of strategy metrics to compare.
    config : ComparisonConfig | None
        Comparison configuration. If None, creates default config.
    title : str
        Chart title.

    Returns
    -------
    go.Figure
        Plotly figure with overlaid drawdown charts.
    """
    import plotly.graph_objects as go

    # Create default config if not provided
    if config is None:
        config = ComparisonConfig(
            strategy_names=[m.name for m in metrics_list],
        )

    colors = config.get_colors()
    fig = go.Figure()

    for i, metrics in enumerate(metrics_list):
        drawdown = metrics.drawdown_series

        if drawdown.empty:
            _logger.warning(f"Strategy '{metrics.name}' has no drawdown data")
            continue

        # Create fill color with transparency
        color = colors[i % len(colors)]
        if color.startswith("#"):
            fill_color = color + "4D"  # Add 30% alpha for hex colors
        else:
            fill_color = color

        fig.add_trace(
            go.Scatter(
                x=drawdown.index,
                y=drawdown.values * 100,  # Convert to percentage
                mode="lines",
                name=metrics.name,
                fill="tozeroy",
                line={"color": color, "width": 1},
                fillcolor=fill_color,
                hovertemplate=(
                    f"<b>{metrics.name}</b><br>"
                    "Date: %{x}<br>"
                    "Drawdown: %{y:.2f}%<br>"
                    "<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        title={
            "text": title,
            "x": 0.5,
            "xanchor": "center",
        },
        xaxis_title="Date",
        yaxis_title="Drawdown (%)",
        hovermode="x unified",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
        },
        template="plotly_white",
        yaxis={"ticksuffix": "%"},
    )

    return fig


# =============================================================================
# T055: Comparison Stats Table Renderer
# =============================================================================


def render_comparison_stats_table(
    metrics_list: list[StrategyMetrics],
    config: ComparisonConfig | None = None,
    title: str = "Strategy Comparison",
) -> "go.Figure":
    """
    Render side-by-side metrics comparison table.

    Parameters
    ----------
    metrics_list : list[StrategyMetrics]
        List of strategy metrics to compare.
    config : ComparisonConfig | None
        Comparison configuration. If None, creates default config.
    title : str
        Table title.

    Returns
    -------
    go.Figure
        Plotly figure with comparison table.
    """
    import plotly.graph_objects as go

    # Create default config if not provided
    if config is None:
        config = ComparisonConfig(
            strategy_names=[m.name for m in metrics_list],
        )

    colors = config.get_colors()

    # Define metrics to display
    metric_labels = [
        "Total PnL",
        "Sharpe Ratio",
        "Sortino Ratio",
        "Max Drawdown",
        "Win Rate",
        "Profit Factor",
        "Total Trades",
        "Avg Duration",
    ]

    # Build table data (columns = strategies)
    header_values = ["Metric"] + [m.name for m in metrics_list]
    cell_values = [metric_labels]  # First column is metric names

    for metrics in metrics_list:
        cell_values.append(
            [
                f"${float(metrics.total_pnl):,.2f}",
                f"{metrics.sharpe_ratio:.2f}",
                f"{metrics.sortino_ratio:.2f}",
                f"{metrics.max_drawdown:.1%}",
                f"{metrics.win_rate:.1%}",
                f"{metrics.profit_factor:.2f}",
                str(metrics.total_trades),
                metrics.avg_trade_duration,
            ]
        )

    # Create header colors with strategy colors
    header_fill_colors = ["#374151"] + colors[: len(metrics_list)]

    fig = go.Figure(
        data=[
            go.Table(
                header={
                    "values": header_values,
                    "fill_color": [header_fill_colors],
                    "align": "center",
                    "font": {"size": 12, "color": "white"},
                    "height": 30,
                },
                cells={
                    "values": cell_values,
                    # Alternating row colors based on actual number of metrics
                    "fill_color": [["#f9fafb", "#ffffff"] * ((len(metric_labels) + 1) // 2)][
                        : len(metric_labels)
                    ],
                    "align": ["left"] + ["center"] * len(metrics_list),
                    "font": {"size": 11},
                    "height": 25,
                },
            )
        ]
    )

    fig.update_layout(
        title={
            "text": title,
            "x": 0.5,
            "xanchor": "center",
        },
        margin={"l": 20, "r": 20, "t": 50, "b": 20},
    )

    return fig


# =============================================================================
# T056: Main Comparison Tearsheet Function
# =============================================================================


def create_comparison_tearsheet(
    engines: list["BacktestEngine"],
    strategy_names: list[str] | None = None,
    output_path: str = "comparison.html",
    config: "TearsheetConfig | None" = None,
    normalize_equity: bool = True,
    colors: list[str] | None = None,
) -> str:
    """
    Generate comparison tearsheet for multiple strategies.

    This function creates a comprehensive HTML report comparing multiple
    strategy backtests with overlaid equity curves, drawdown charts,
    and side-by-side statistics tables.

    Parameters
    ----------
    engines : list[BacktestEngine]
        List of completed backtest engines to compare (2-10).
    strategy_names : list[str] | None
        Display names for each strategy. If None, uses default names
        like "Strategy 1", "Strategy 2", etc.
    output_path : str
        Output HTML file path.
    config : TearsheetConfig | None
        Base tearsheet configuration for styling.
    normalize_equity : bool
        If True, normalize all equity curves to start at 1.0.
    colors : list[str] | None
        Custom colors for each strategy.

    Returns
    -------
    str
        Path to generated HTML file.

    Raises
    ------
    ValueError
        If fewer than 2 or more than 10 engines provided.

    Example
    -------
    >>> path = create_comparison_tearsheet(
    ...     engines=[engine1, engine2, engine3],
    ...     strategy_names=["Momentum", "Mean Reversion", "Trend"],
    ...     output_path="comparison.html",
    ... )
    >>> print(f"Comparison saved to: {path}")
    """
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    # Validate engine count
    if len(engines) < 2:
        raise ValueError(
            f"create_comparison_tearsheet requires at least 2 engines, got {len(engines)}"
        )
    if len(engines) > 10:
        raise ValueError(
            f"create_comparison_tearsheet supports at most 10 engines, got {len(engines)}"
        )

    # Generate default strategy names if not provided
    if strategy_names is None:
        strategy_names = [f"Strategy {i + 1}" for i in range(len(engines))]
    elif len(strategy_names) != len(engines):
        raise ValueError(
            f"strategy_names length ({len(strategy_names)}) must match "
            f"engines length ({len(engines)})"
        )

    # Create comparison config
    comparison_config = ComparisonConfig(
        strategy_names=strategy_names,
        normalize_equity=normalize_equity,
        colors=colors,
    )

    _logger.info(f"Creating comparison tearsheet for {len(engines)} strategies")

    # Extract metrics from all engines
    metrics_list = [
        StrategyMetrics.from_engine(engine, name) for engine, name in zip(engines, strategy_names)
    ]

    # Create subplots layout
    fig = make_subplots(
        rows=3,
        cols=1,
        row_heights=[0.45, 0.35, 0.20],
        vertical_spacing=0.08,
        subplot_titles=("Equity Curve Comparison", "Drawdown Comparison", ""),
        specs=[
            [{"type": "scatter"}],
            [{"type": "scatter"}],
            [{"type": "table"}],
        ],
    )

    colors_list = comparison_config.get_colors()

    # Add equity curves
    for i, metrics in enumerate(metrics_list):
        equity = metrics.normalized_equity if normalize_equity else metrics.cumulative_returns
        if not equity.empty:
            fig.add_trace(
                go.Scatter(
                    x=equity.index,
                    y=equity.values,
                    mode="lines",
                    name=metrics.name,
                    line={"color": colors_list[i], "width": 2},
                    legendgroup=metrics.name,
                    hovertemplate=(
                        f"<b>{metrics.name}</b><br>"
                        "Date: %{x}<br>"
                        "Value: %{y:.4f}<br>"
                        "<extra></extra>"
                    ),
                ),
                row=1,
                col=1,
            )

    # Add drawdown curves
    for i, metrics in enumerate(metrics_list):
        drawdown = metrics.drawdown_series
        if not drawdown.empty:
            fig.add_trace(
                go.Scatter(
                    x=drawdown.index,
                    y=drawdown.values * 100,
                    mode="lines",
                    name=metrics.name,
                    fill="tozeroy",
                    line={"color": colors_list[i], "width": 1},
                    legendgroup=metrics.name,
                    showlegend=False,
                    hovertemplate=(
                        f"<b>{metrics.name}</b><br>"
                        "Date: %{x}<br>"
                        "Drawdown: %{y:.2f}%<br>"
                        "<extra></extra>"
                    ),
                ),
                row=2,
                col=1,
            )

    # Build stats table data
    metric_labels = [
        "Total PnL",
        "Sharpe",
        "Sortino",
        "Max DD",
        "Win Rate",
        "PF",
        "Trades",
    ]
    header_values = ["Metric"] + strategy_names
    cell_values = [metric_labels]

    for metrics in metrics_list:
        cell_values.append(
            [
                f"${float(metrics.total_pnl):,.0f}",
                f"{metrics.sharpe_ratio:.2f}",
                f"{metrics.sortino_ratio:.2f}",
                f"{metrics.max_drawdown:.1%}",
                f"{metrics.win_rate:.1%}",
                f"{metrics.profit_factor:.2f}",
                str(metrics.total_trades),
            ]
        )

    # Add stats table
    fig.add_trace(
        go.Table(
            header={
                "values": header_values,
                "fill_color": ["#374151"] + colors_list,
                "align": "center",
                "font": {"size": 11, "color": "white"},
                "height": 28,
            },
            cells={
                "values": cell_values,
                "fill_color": "#f9fafb",
                "align": ["left"] + ["center"] * len(metrics_list),
                "font": {"size": 10},
                "height": 24,
            },
        ),
        row=3,
        col=1,
    )

    # Update layout
    fig.update_layout(
        title={
            "text": f"Strategy Comparison ({len(engines)} strategies)",
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 20},
        },
        height=1000,
        showlegend=True,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "center",
            "x": 0.5,
        },
        template="plotly_white",
        hovermode="x unified",
    )

    # Update y-axis labels
    fig.update_yaxes(
        title_text="Normalized Equity" if normalize_equity else "Cumulative Returns",
        row=1,
        col=1,
    )
    fig.update_yaxes(title_text="Drawdown (%)", ticksuffix="%", row=2, col=1)

    # Write HTML file
    output_path_obj = Path(output_path)
    fig.write_html(
        str(output_path_obj),
        include_plotlyjs=True,
        full_html=True,
    )

    _logger.info(f"Comparison tearsheet saved to: {output_path}")

    return str(output_path_obj)
