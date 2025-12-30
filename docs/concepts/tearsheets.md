# Tearsheets

Tearsheets are comprehensive HTML reports that analyze backtest performance, providing traders with visual and statistical summaries of strategy behavior.

## Overview

The tearsheet module (`strategies/common/tearsheet/`) provides custom extensions to NautilusTrader's native tearsheet system. It includes:

- **Wrapper function** with automatic edge case handling
- **Multi-strategy comparison** for side-by-side analysis
- **Custom themes** including `nautilus_dev` project branding
- **Custom charts** for strategy-specific metrics (extensible)
- **Edge case detection** for unusual data patterns

## Quick Start

### Basic Tearsheet Generation

```python
from strategies.common.tearsheet import generate_tearsheet

# Generate basic tearsheet
generate_tearsheet(engine, output_path="tearsheet.html")
```

### With Custom Theme

```python
from nautilus_trader.analysis import TearsheetConfig

config = TearsheetConfig(theme="nautilus_dev")
generate_tearsheet(engine, output_path="tearsheet.html", config=config)
```

### Multi-Strategy Comparison

```python
from strategies.common.tearsheet import create_comparison_tearsheet

create_comparison_tearsheet(
    engines=[engine1, engine2, engine3],
    strategy_names=["Momentum", "Mean Reversion", "Trend"],
    output_path="comparison.html",
)
```

## Available Themes

The tearsheet module supports 5 themes:

### Built-in Plotly Themes

- **plotly_white** - Clean light theme (default)
- **plotly_dark** - Dark background with light text
- **nautilus** - Light with NautilusTrader branding
- **nautilus_dark** - Dark with NautilusTrader branding

### Custom Theme

- **nautilus_dev** - Project-specific theme with navy blue primary color, green/red profit/loss indicators, and optimized typography

To use a theme:

```python
config = TearsheetConfig(theme="plotly_dark")
generate_tearsheet(engine, output_path="tearsheet.html", config=config)
```

## Edge Case Handling

The tearsheet module automatically detects and handles these edge cases:

### Zero Trades

**Problem**: Strategy never enters a position.

**Detection**: Checks trade count from portfolio analyzer.

**Handling**:
- Warning message logged
- Trade metrics display as N/A
- Other charts still render normally

```
[WARNING] No trades were executed during backtest
Recommendation: Check strategy logic, entry conditions, or data availability
```

### Open Positions at Backtest End

**Problem**: Strategy has unclosed positions when backtest ends (epoch timestamp bug).

**Detection**: Checks `engine.cache.positions_open()`.

**Handling**:
- Warning message with position count
- May show incorrect equity curve timestamps
- Workaround: Close all positions before generating tearsheet

```
[WARNING] {N} open positions at backtest end
Recommendation: Close all positions before generating tearsheet to avoid epoch bug
```

### Long Backtests (10+ Years)

**Problem**: Large datasets (>5,000 points) cause browser rendering lag.

**Detection**: Estimates backtest duration from return series.

**Handling**:
- Uses ScatterGL instead of Scatter for performance
- Renders smoothly even with 100K+ data points
- Trade-off: Lower visual precision at zoom levels

```
[INFO] Backtest spans ~15.2 years (3,840 data points)
Recommendation: Using ScatterGL for improved rendering performance
```

### High-Frequency Trading (1,000+ trades/day)

**Problem**: Too many discrete points to visualize clearly.

**Detection**: Calculates average trades per day.

**Handling**:
- Trade distribution aggregated for overview
- Drill-down data available in original resolution
- Improves chart readability without losing data

```
[INFO] High-frequency: 2,450 trades/day average
Recommendation: Trade data will be aggregated for overview; drill-down available
```

### All Losses (0% Win Rate)

**Problem**: No winning trades to highlight in analysis.

**Detection**: Checks win rate from performance stats.

**Handling**:
- Charts render normally (all red)
- Returns cumulative losses correctly
- Useful for strategy validation before refinement

```
[WARNING] All trades resulted in losses (0% win rate)
Recommendation: Review strategy logic and market conditions
```

### Missing OHLC Data

**Problem**: Cannot render bar charts with fills without OHLC data.

**Detection**: Checks data availability in engine.

**Handling**:
- Gracefully skips `bars_with_fills` chart
- All other charts still render
- Recommend using OHLC bars for better analysis

## Multi-Strategy Comparison

Compare multiple strategies side-by-side in a single report:

```python
from strategies.common.tearsheet import (
    create_comparison_tearsheet,
    ComparisonConfig,
)

# Simple comparison
create_comparison_tearsheet(
    engines=[engine1, engine2, engine3],
    strategy_names=["Momentum", "Mean Reversion", "Trend"],
    output_path="comparison.html",
)

# With custom configuration
config = ComparisonConfig(
    theme="nautilus_dev",
    benchmark_symbol="BTCUSDT",  # Optional
)
create_comparison_tearsheet(
    engines=[engine1, engine2, engine3],
    strategy_names=["S1", "S2", "S3"],
    output_path="comparison.html",
    config=config,
)
```

The comparison report includes:

- **Overlaid equity curves** - Compare cumulative returns visually
- **Overlaid drawdown charts** - Compare peak-to-trough metrics
- **Side-by-side statistics table** - Total return, Sharpe, max drawdown, etc.
- **Performance metrics ranking** - Quick comparison of key stats

## Custom Chart Registration

Extend tearsheets with strategy-specific metrics:

### One-time Setup

```python
from strategies.common.tearsheet import register_custom_charts

# Call once at application startup
register_custom_charts()
```

This registers:
- `rolling_volatility` - 30-day rolling annualized volatility with mean line
- `comparison_equity` - Multi-strategy equity comparison
- `comparison_drawdown` - Multi-strategy drawdown comparison
- `comparison_stats` - Multi-strategy statistics table

### Creating Custom Charts

```python
from nautilus_trader.analysis.charts import register_chart
import plotly.graph_objects as go

def my_custom_chart(returns, **kwargs):
    """Create a custom metric chart."""
    # Calculate your metric
    metric = returns.rolling(window=20).mean()

    # Build Plotly figure
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=metric.index, y=metric.values))
    fig.update_layout(title="My Metric", height=350)
    return fig

# Register the chart
register_chart(name="my_metric", chart_func=my_custom_chart)

# Use in tearsheet configuration
from nautilus_trader.analysis import TearsheetConfig
config = TearsheetConfig(charts=["my_metric"])
generate_tearsheet(engine, config=config)
```

### Chart Function Signature

Custom chart functions should:

```python
def my_chart(
    returns: pd.Series,  # Daily returns with DatetimeIndex
    **kwargs,           # Additional parameters (ignored)
) -> go.Figure:        # Plotly figure
    """Create a custom chart."""
    # ... implementation
    return fig
```

Parameters:
- `returns` - Series of daily returns from backtest
- `kwargs` - Additional arguments (for extensibility)

Return:
- Plotly `Figure` object

Best Practices:
- Set `height=350` for consistent spacing
- Use meaningful axis labels and titles
- Add legends only if multiple traces
- Use colors from theme (e.g., `#22c55e` for positive)

## API Reference

### Core Functions

**`generate_tearsheet(engine, output_path="tearsheet.html", config=None, **kwargs)`**

Generate tearsheet with edge case handling.

- `engine` - Completed BacktestEngine
- `output_path` - Output HTML file path
- `config` - TearsheetConfig object (optional)
- Returns: Path to generated HTML file

**`create_comparison_tearsheet(engines, strategy_names=None, output_path="comparison.html", config=None)`**

Generate comparison tearsheet for multiple strategies.

- `engines` - List of BacktestEngine objects
- `strategy_names` - Display names for each strategy (optional)
- `output_path` - Output HTML file path
- `config` - TearsheetConfig object (optional)
- Returns: Path to generated HTML file

**`register_custom_charts()`**

Register all custom chart templates (one-time setup).

**`check_edge_cases(engine)`**

Check for edge cases in backtest results.

- `engine` - Completed BacktestEngine
- Returns: List of TearsheetWarning objects

### Classes

**`TearsheetWarning`**

Edge case warning with severity level.

- `edge_case` - EdgeCaseType enum
- `severity` - EdgeCaseSeverity enum (INFO, WARNING, ERROR)
- `message` - Human-readable description
- `recommendation` - Suggested action

**`StrategyMetrics`**

Dataclass for a single strategy's performance metrics.

**`ComparisonConfig`**

Configuration for multi-strategy comparison reports.

## Performance Characteristics

- **1-year daily backtest** - < 5 seconds to generate
- **10K+ data points** - Uses ScatterGL for browser performance
- **File size** - < 2MB HTML with all charts (self-contained)
- **Charts rendered** - 8 built-in + custom charts

## Integration with Strategies

Typical workflow:

```python
# 1. Run backtest
from nautilus_trader.backtest.engine import BacktestEngine

engine = BacktestEngine(strategies=[...])
engine.run()

# 2. Check for issues
from strategies.common.tearsheet import check_edge_cases

warnings = check_edge_cases(engine)
for w in warnings:
    print(w)  # [WARNING] format

# 3. Generate report
from strategies.common.tearsheet import generate_tearsheet

output = generate_tearsheet(
    engine,
    output_path="results/my_strategy.html"
)
print(f"Tearsheet: {output}")
```

## Troubleshooting

**Charts not rendering?**
- Ensure NautilusTrader visualization extra is installed
- Check browser console for errors (opens tearsheet in browser)
- Verify data is available (some edge cases may skip charts)

**Theme not applying?**
- Call `register_nautilus_dev_theme()` at startup if using custom theme
- Built-in themes (plotly_white, etc.) should work out of the box
- Check theme name spelling in TearsheetConfig

**Slow rendering?**
- Long backtests automatically use ScatterGL
- If still slow, consider aggregating data (high-frequency edge case)
- Try narrowing backtest period for validation

**Comparison not comparing correctly?**
- Ensure strategy_names list matches engines list length
- All engines should use same instrument/symbol
- Different timeframes may show unexpected comparisons

## See Also

- **NautilusTrader Docs** - [Tearsheets](https://docs.nautilusunstable.io/tutorials/)
- **Plotly** - [Graph Objects Reference](https://plotly.com/python/graph-objects/)
- **Discord** - Search `tearsheet` in #dev-discussions for community solutions
