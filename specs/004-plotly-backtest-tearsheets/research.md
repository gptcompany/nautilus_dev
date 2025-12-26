# Research: Plotly Backtest Tearsheets

**Feature**: 004-plotly-backtest-tearsheets
**Created**: 2025-12-25
**Status**: Complete

## Executive Summary

NautilusTrader v1.221+ already provides a comprehensive Plotly-based tearsheet system via `nautilus_trader.analysis.tearsheet`. This feature should **leverage the existing system** rather than build from scratch, adding only project-specific extensions (multi-strategy comparison, custom themes).

## Research Findings

### 1. NautilusTrader Native Tearsheet System

**Decision**: Use native NautilusTrader tearsheet system
**Rationale**: Follows "Native First" constitution principle; covers 100% of spec requirements
**Alternatives Considered**:
- Build custom tearsheet (rejected: violates constitution, maintenance burden)
- Use PyFolio (rejected: outdated, no NautilusTrader integration)
- Use QuantStats (rejected: limited customization, different data structures)

#### Key Findings

| Feature | NautilusTrader Native | Custom Build Required |
|---------|----------------------|-----------------------|
| Equity curve | YES (`equity` chart) | NO |
| Drawdown chart | YES (`drawdown` chart) | NO |
| Monthly returns heatmap | YES (`monthly_returns` chart) | NO |
| Yearly returns | YES (`yearly_returns` chart) | NO |
| Trade distribution | YES (`distribution` chart) | NO |
| Statistics table | YES (`stats_table` chart) | NO |
| OHLC with trades | YES (`bars_with_fills` chart) | NO |
| Dark/Light themes | YES (4 built-in) | NO |
| Self-contained HTML | YES (Plotly.js embedded) | NO |
| Custom chart registry | YES (`register_chart()`) | NO |
| Multi-strategy comparison | NO | **YES** |
| Custom project theme | NO | **YES** |

#### API Reference

```python
# High-level API
from nautilus_trader.analysis.tearsheet import create_tearsheet
create_tearsheet(engine=engine, output_path="tearsheet.html")

# Customizable
from nautilus_trader.analysis import TearsheetConfig
config = TearsheetConfig(
    charts=["equity", "drawdown", "monthly_returns"],
    theme="nautilus_dark",
    height=2000,
)
create_tearsheet(engine=engine, config=config)

# Extension point
from nautilus_trader.analysis.tearsheet import register_chart
register_chart("my_custom", my_custom_chart)

# Low-level API (for custom data sources)
from nautilus_trader.analysis.tearsheet import create_tearsheet_from_stats
create_tearsheet_from_stats(
    stats_pnls=stats_pnls,
    stats_returns=stats_returns,
    stats_general=stats_general,
    returns=returns,
)
```

### 2. Plotly Best Practices for Financial Visualization

**Decision**: Use Plotly Graph Objects for complex charts, Express for simple exploratory charts
**Rationale**: Graph Objects provides subplot control and consistent theming required for tearsheets
**Alternatives Considered**:
- Plotly Express only (rejected: limited subplot control)
- Matplotlib (rejected: no interactivity)
- Bokeh (rejected: larger file sizes, different ecosystem)

#### Performance Recommendations

| Data Points | Recommended Approach |
|-------------|---------------------|
| < 5,000 | Standard Scatter/Candlestick |
| 5,000 - 50,000 | ScatterGL (WebGL rendering) |
| > 50,000 | Data aggregation + ScatterGL |

#### Self-Contained HTML

```python
# Plotly automatically embeds Plotly.js in HTML
fig.write_html("output.html", include_plotlyjs=True)  # Default: ~3MB file
fig.write_html("output.html", include_plotlyjs="cdn")  # Smaller: requires internet
```

**Recommendation**: Use `include_plotlyjs=True` (default) for offline capability per FR-011.

### 3. Known Issues & Workarounds

#### Epoch Timestamp Bug (Discord: 2025-12-07)

**Issue**: Open positions at backtest end cause equity curve to start from 1970 (Unix epoch 0)
**Root Cause**: `position.ts_closed = 0` for open positions
**Workaround**: Ensure all positions are closed before tearsheet generation, or filter returns data
**Status**: Bug should be reported upstream to NautilusTrader

#### Visualization Extra Availability

**Issue**: `visualization` extra only available on nightly builds
**Workaround**: Use nightly environment (already configured in project)
```bash
source /media/sam/2TB-NVMe/prod/apps/nautilus_nightly/nautilus_nightly_env/bin/activate
uv pip install "nautilus_trader[visualization]"
```

#### Equity Curve Tracks Realized PnL Only

**Issue**: Equity curve shows realized PnL, not unrealized
**Workaround**: For unrealized tracking, use cache to store `position.unrealized_pnl(price)` during backtest
**Future**: Feature request submitted for native unrealized equity tracking

### 4. Multi-Strategy Comparison (Custom Extension)

**Decision**: Implement comparison using `create_tearsheet_from_stats()` with aggregated data
**Rationale**: Leverages existing infrastructure while adding comparison capability

#### Implementation Approach

```python
def create_comparison_tearsheet(engines: list[BacktestEngine], ...):
    """Aggregate stats from multiple engines and create comparison view."""

    # Collect returns from all strategies
    all_returns = {}
    for engine, name in zip(engines, strategy_names):
        all_returns[name] = engine.portfolio.analyzer.returns()

    # Create overlaid equity curves using custom chart
    # Register comparison chart before tearsheet generation
    register_chart("comparison_equity", _render_comparison_equity)

    # Use low-level API with aggregated data
    create_tearsheet_from_stats(...)
```

### 5. Custom Theme Implementation

**Decision**: Register custom theme using native `register_theme()` function
**Rationale**: Follows extension pattern, no monkey-patching required

```python
from nautilus_trader.analysis.themes import register_theme

register_theme(
    name="nautilus_dev",
    template="plotly_white",
    colors={
        "primary": "#1a365d",      # Navy blue (project branding)
        "positive": "#22c55e",     # Green
        "negative": "#ef4444",     # Red
        "neutral": "#6b7280",      # Gray
        "background": "#ffffff",
        "grid": "#e5e7eb",
        "table_section": "#f3f4f6",
        "table_row_odd": "#f9fafb",
        "table_row_even": "#ffffff",
        "table_text": "#111827",
    }
)
```

### 6. Edge Case Handling

| Edge Case | Built-in Handling | Custom Handling Required |
|-----------|-------------------|-------------------------|
| Zero trades | Empty stats table | Add informative message |
| All losses | Charts render correctly | No change needed |
| 10+ years data | Supported | Consider ScatterGL |
| 1000+ trades/day | Supported with ScatterGL | Aggregate for overview |
| Missing OHLC data | `bars_with_fills` gracefully skips | Log warning, continue |
| Open positions at end | Bug (epoch timestamp) | Close all positions first |

### 7. Performance Benchmarks

Based on Plotly documentation and community benchmarks:

| Scenario | Expected Performance | Target |
|----------|---------------------|--------|
| 1-year daily (252 points) | < 1 second | PASS |
| 5-year daily (1,260 points) | < 2 seconds | PASS |
| 10-year daily (2,520 points) | < 3 seconds | PASS |
| 1-year hourly (6,552 points) | < 5 seconds | PASS |
| 1-year minute (525,600 points) | 10-30 seconds | Aggregate to hourly |

**HTML File Size**:
- Standard tearsheet (8 charts): ~1.5 MB
- With embedded Plotly.js: ~4.5 MB
- Target: < 2 MB (excluding Plotly.js) - ACHIEVABLE

## Dependencies Verified

| Dependency | Version | Availability | Notes |
|------------|---------|--------------|-------|
| NautilusTrader | >= 1.221.0 | Nightly only | `[visualization]` extra required |
| Plotly | >= 6.3.1 | PyPI | Installed via extra |
| Pandas | Any | Standard | Already in environment |

## NEEDS CLARIFICATION Resolution

All items from Technical Context have been resolved:

| Item | Resolution |
|------|------------|
| Tearsheet API | Fully documented in NautilusTrader develop branch |
| Available charts | 9 built-in charts covering all spec requirements |
| Theme system | 4 built-in + custom registration |
| Extension points | Chart registry and low-level API |
| Known bugs | Epoch timestamp bug documented with workaround |

## Recommendations

1. **Use native tearsheet system** - Do not reinvent the wheel
2. **Extend via chart registry** - Register custom comparison chart
3. **Custom theme only** - Single theme registration for project branding
4. **Pin nightly version** - Avoid API changes during development
5. **Close all positions** - Before tearsheet generation to avoid epoch bug
6. **Use ScatterGL** - For datasets > 5,000 points

## Sources

- NautilusTrader Discord: `docs/discord/feedback.md`, `docs/discord/help.md`
- NautilusTrader Documentation: `docs/concepts/visualization.md`, `docs/concepts/reports.md`
- NautilusTrader GitHub: `develop` branch analysis module
- Plotly Documentation: Performance optimization guides
