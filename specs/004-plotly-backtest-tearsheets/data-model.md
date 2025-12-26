# Data Model: Plotly Backtest Tearsheets

**Feature**: 004-plotly-backtest-tearsheets
**Created**: 2025-12-25
**Status**: Draft

## Overview

This feature primarily uses **native NautilusTrader data structures**. Custom entities are minimal, focused only on project-specific extensions.

## Native NautilusTrader Entities (Read-Only)

These entities are provided by NautilusTrader and should NOT be modified:

### BacktestEngine

Source: `nautilus_trader.backtest.engine.BacktestEngine`

```python
class BacktestEngine:
    """Engine for running backtests."""

    @property
    def portfolio(self) -> Portfolio: ...

    @property
    def cache(self) -> Cache: ...

    @property
    def trader(self) -> Trader: ...

    def run(self, start: datetime | None = None, end: datetime | None = None) -> None: ...
```

### PortfolioAnalyzer

Source: `nautilus_trader.analysis.analyzer.PortfolioAnalyzer`

```python
class PortfolioAnalyzer:
    """Analyzes portfolio performance."""

    def returns(self) -> pd.Series: ...

    def get_performance_stats_pnls(self) -> dict[str, dict[str, Any]]: ...

    def get_performance_stats_returns(self) -> dict[str, Any]: ...

    def get_performance_stats_general(self) -> dict[str, Any]: ...
```

### TearsheetConfig

Source: `nautilus_trader.analysis.config.TearsheetConfig`

```python
@dataclass
class TearsheetConfig:
    """Configuration for tearsheet generation."""

    charts: list[str] | None = None  # Default: all built-in
    theme: str = "plotly_white"
    layout: GridLayout | None = None
    title: str | None = None
    include_benchmark: bool = True
    benchmark_name: str = "Benchmark"
    height: int = 1500
    show_logo: bool = True
    chart_args: dict[str, dict[str, Any]] | None = None
```

### GridLayout

Source: `nautilus_trader.analysis.config.GridLayout`

```python
@dataclass
class GridLayout:
    """Layout configuration for tearsheet grid."""

    rows: int
    cols: int
    heights: list[float] | None = None
    vertical_spacing: float = 0.05
    horizontal_spacing: float = 0.10
```

## Custom Entities (Project-Specific)

### ComparisonConfig

Extension config for multi-strategy comparison tearsheets.

```python
from dataclasses import dataclass
from nautilus_trader.analysis import TearsheetConfig

@dataclass
class ComparisonConfig:
    """Configuration for multi-strategy comparison tearsheet."""

    strategy_names: list[str]
    """Display names for each strategy."""

    base_config: TearsheetConfig | None = None
    """Base tearsheet configuration. Defaults to comparison-optimized layout."""

    show_individual_stats: bool = True
    """Show individual strategy stats tables."""

    show_comparison_table: bool = True
    """Show side-by-side metrics comparison table."""

    colors: list[str] | None = None
    """Custom colors for each strategy. Defaults to Plotly color sequence."""

    def __post_init__(self):
        if self.base_config is None:
            self.base_config = TearsheetConfig(
                charts=["comparison_equity", "comparison_drawdown", "comparison_stats"],
                theme="nautilus_dev",
                height=2000,
            )
```

**Validation Rules**:
- `strategy_names` must have 2-10 entries
- Length must match number of engines passed to `create_comparison_tearsheet()`
- `colors` if provided must match length of `strategy_names`

### StrategyMetrics

Aggregated metrics for comparison display.

```python
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

@dataclass
class StrategyMetrics:
    """Aggregated metrics for a single strategy in comparison view."""

    name: str
    """Strategy display name."""

    total_pnl: Decimal
    """Total profit/loss in base currency."""

    sharpe_ratio: float
    """Sharpe ratio (252-day annualized)."""

    sortino_ratio: float
    """Sortino ratio (252-day annualized)."""

    max_drawdown: float
    """Maximum drawdown percentage (negative)."""

    win_rate: float
    """Percentage of winning trades (0-1)."""

    profit_factor: float
    """Ratio of gross profits to gross losses."""

    total_trades: int
    """Total number of closed trades."""

    avg_trade_duration: str
    """Average trade duration as formatted string."""

    returns_series: "pd.Series"
    """Daily returns time series for charting."""

    raw_stats: dict[str, Any]
    """Original stats dict from PortfolioAnalyzer."""

    @classmethod
    def from_engine(cls, engine: "BacktestEngine", name: str) -> "StrategyMetrics":
        """Extract metrics from a completed backtest engine."""
        analyzer = engine.portfolio.analyzer

        stats_pnls = analyzer.get_performance_stats_pnls()
        stats_returns = analyzer.get_performance_stats_returns()
        stats_general = analyzer.get_performance_stats_general()

        # Aggregate PnL across currencies
        total_pnl = sum(
            Decimal(str(currency_stats.get("PnL (total)", 0)))
            for currency_stats in stats_pnls.values()
        )

        return cls(
            name=name,
            total_pnl=total_pnl,
            sharpe_ratio=stats_returns.get("Sharpe Ratio (252 days)", 0.0),
            sortino_ratio=stats_returns.get("Sortino Ratio (252 days)", 0.0),
            max_drawdown=stats_returns.get("Max Drawdown", 0.0),
            win_rate=stats_general.get("Win Rate", 0.0),
            profit_factor=stats_general.get("Profit Factor", 0.0),
            total_trades=stats_general.get("Total Trades", 0),
            avg_trade_duration=stats_general.get("Avg Trade Duration", "N/A"),
            returns_series=analyzer.returns(),
            raw_stats={
                "pnls": stats_pnls,
                "returns": stats_returns,
                "general": stats_general,
            },
        )
```

**State Transitions**: N/A (immutable data class)

## Relationships

```
┌─────────────────────┐     ┌─────────────────────┐
│  BacktestEngine     │────▶│  PortfolioAnalyzer  │
│  (NautilusTrader)   │     │  (NautilusTrader)   │
└──────────┬──────────┘     └──────────┬──────────┘
           │                           │
           ▼                           ▼
┌─────────────────────┐     ┌─────────────────────┐
│  StrategyMetrics    │◀────│  stats_pnls,        │
│  (Custom)           │     │  stats_returns,     │
└──────────┬──────────┘     │  stats_general      │
           │                └─────────────────────┘
           ▼
┌─────────────────────┐     ┌─────────────────────┐
│  ComparisonConfig   │────▶│  TearsheetConfig    │
│  (Custom)           │     │  (NautilusTrader)   │
└─────────────────────┘     └─────────────────────┘
```

## Data Flow

1. **BacktestEngine.run()** populates portfolio with trading results
2. **PortfolioAnalyzer** computes statistics from portfolio data
3. **StrategyMetrics.from_engine()** extracts metrics for comparison
4. **ComparisonConfig** configures multi-strategy tearsheet
5. **create_comparison_tearsheet()** generates HTML output

## Validation Rules Summary

| Entity | Field | Rule |
|--------|-------|------|
| ComparisonConfig | strategy_names | 2-10 entries |
| ComparisonConfig | colors | Length matches strategy_names if provided |
| StrategyMetrics | win_rate | 0.0 - 1.0 |
| StrategyMetrics | max_drawdown | Negative (e.g., -0.15 = -15%) |
| StrategyMetrics | profit_factor | > 0 for profitable, < 1 for losing |
