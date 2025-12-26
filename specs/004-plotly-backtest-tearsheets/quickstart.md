# Quickstart: Plotly Backtest Tearsheets

## Prerequisites

1. NautilusTrader nightly environment activated:
   ```bash
   source /media/sam/2TB-NVMe/prod/apps/nautilus_nightly/nautilus_nightly_env/bin/activate
   ```

2. Visualization extras installed:
   ```bash
   uv pip install "nautilus_trader[visualization]"
   ```

## Basic Tearsheet Generation

### 1. Run a Backtest

```python
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.config import BacktestEngineConfig

# Configure and run backtest
config = BacktestEngineConfig(...)
engine = BacktestEngine(config=config)
engine.run()
```

### 2. Generate Default Tearsheet

```python
from nautilus_trader.analysis.tearsheet import create_tearsheet

# Generate with all default charts
create_tearsheet(
    engine=engine,
    output_path="tearsheet.html",
)
# Output: tearsheet.html (open in browser)
```

### 3. Custom Tearsheet Configuration

```python
from nautilus_trader.analysis import TearsheetConfig

config = TearsheetConfig(
    charts=["run_info", "stats_table", "equity", "drawdown", "monthly_returns"],
    theme="nautilus_dark",
    height=2000,
    title="My Strategy - Q4 2024",
)

create_tearsheet(
    engine=engine,
    output_path="custom_tearsheet.html",
    config=config,
)
```

### 4. Add Benchmark Comparison

```python
import pandas as pd

# Load benchmark returns (e.g., S&P 500)
benchmark_returns = pd.read_csv("sp500_returns.csv", index_col=0, parse_dates=True)["return"]

create_tearsheet(
    engine=engine,
    output_path="with_benchmark.html",
    benchmark_returns=benchmark_returns,
    benchmark_name="S&P 500",
)
```

## Multi-Strategy Comparison

```python
from strategies.common.tearsheet import (
    register_custom_charts,
    create_comparison_tearsheet,
)

# One-time setup (call at application startup)
register_custom_charts()

# Run multiple backtests
engines = [engine1, engine2, engine3]
strategy_names = ["Momentum", "Mean Reversion", "Trend Following"]

# Generate comparison tearsheet
create_comparison_tearsheet(
    engines=engines,
    strategy_names=strategy_names,
    output_path="comparison.html",
)
```

## Available Charts

| Chart Name | Description | Default Included |
|------------|-------------|------------------|
| `run_info` | Run metadata and account balances | YES |
| `stats_table` | Performance statistics | YES |
| `equity` | Equity curve with optional benchmark | YES |
| `drawdown` | Drawdown from peak | YES |
| `monthly_returns` | Monthly returns heatmap | YES |
| `distribution` | Returns distribution histogram | YES |
| `rolling_sharpe` | 60-day rolling Sharpe ratio | YES |
| `yearly_returns` | Annual returns bar chart | YES |
| `bars_with_fills` | OHLC with trade markers | YES |

## Themes

| Theme | Description |
|-------|-------------|
| `plotly_white` | Clean light theme (default) |
| `plotly_dark` | Dark background |
| `nautilus` | Light with NautilusTrader branding |
| `nautilus_dark` | Dark with NautilusTrader branding |
| `nautilus_dev` | Project-specific theme (after registration) |

## Custom Theme Registration

```python
from nautilus_trader.analysis.themes import register_theme

register_theme(
    name="my_theme",
    template="plotly_white",
    colors={
        "primary": "#003366",
        "positive": "#22c55e",
        "negative": "#ef4444",
        "neutral": "#6b7280",
        "background": "#ffffff",
        "grid": "#e5e7eb",
    }
)

# Use custom theme
config = TearsheetConfig(theme="my_theme")
```

## Individual Chart Functions

For standalone charts without full tearsheet:

```python
from nautilus_trader.analysis.tearsheet import (
    create_equity_curve,
    create_drawdown_chart,
    create_monthly_returns_heatmap,
)

returns = engine.portfolio.analyzer.returns()

# Create individual charts
fig_equity = create_equity_curve(returns, title="Equity Curve")
fig_equity.show()  # Display in browser

fig_drawdown = create_drawdown_chart(returns, title="Drawdown")
fig_drawdown.write_html("drawdown.html")
```

## Performance Tips

1. **Large datasets (> 5,000 points)**: Use ScatterGL for better performance
2. **Very long backtests**: Consider generating separate tearsheets by period
3. **File size**: Default HTML is ~1.5 MB; with Plotly.js embedded ~4.5 MB

## Troubleshooting

### Epoch Timestamp Bug

If equity curve starts from 1970, ensure all positions are closed before generating tearsheet:

```python
# Close all open positions before tearsheet
for position in engine.cache.positions_open():
    # Force close at last known price
    ...

# Then generate tearsheet
create_tearsheet(engine=engine, ...)
```

### Missing Visualization Extra

```bash
# Error: ModuleNotFoundError: No module named 'plotly'
# Fix:
uv pip install "nautilus_trader[visualization]"
```

### Import Error for TearsheetConfig

```python
# Use nightly builds only
# Stable releases do not include visualization module
source /media/sam/2TB-NVMe/prod/apps/nautilus_nightly/nautilus_nightly_env/bin/activate
```

## Next Steps

- See `research.md` for detailed API documentation
- See `plan.md` for implementation roadmap
- See `data-model.md` for entity relationships
