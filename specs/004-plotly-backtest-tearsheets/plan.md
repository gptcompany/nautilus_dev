# Implementation Plan: Plotly Backtest Tearsheets

**Feature Branch**: `004-plotly-backtest-tearsheets`
**Created**: 2025-12-25
**Status**: Draft
**Spec Reference**: `specs/004-plotly-backtest-tearsheets/spec.md`

## Technical Context

### Existing NautilusTrader Visualization System (v1.221+)

**CRITICAL FINDING**: NautilusTrader already has a comprehensive tearsheet system on the `develop` branch:

```python
from nautilus_trader.analysis.tearsheet import create_tearsheet
from nautilus_trader.analysis import TearsheetConfig

# High-level API
create_tearsheet(engine=engine, output_path="tearsheet.html")

# Customizable
config = TearsheetConfig(
    charts=["equity", "drawdown", "monthly_returns"],
    theme="nautilus_dark",
    height=2000,
)
create_tearsheet(engine=engine, config=config)
```

### Available Built-in Charts

| Chart Name        | Type        | Description                                        |
|-------------------|-------------|----------------------------------------------------|
| `run_info`        | Table       | Run metadata and account balances                  |
| `stats_table`     | Table       | Performance statistics (PnL, returns, metrics)     |
| `equity`          | Line        | Cumulative returns with optional benchmark         |
| `drawdown`        | Area        | Drawdown percentage from peak                      |
| `monthly_returns` | Heatmap     | Monthly return percentages by year                 |
| `distribution`    | Histogram   | Distribution of individual returns                 |
| `rolling_sharpe`  | Line        | 60-day rolling Sharpe ratio                        |
| `yearly_returns`  | Bar         | Annual return percentages                          |
| `bars_with_fills` | Candlestick | OHLC prices with order fills overlaid              |

### Theme System

Four built-in themes: `plotly_white`, `plotly_dark`, `nautilus`, `nautilus_dark`

Custom theme registration:
```python
from nautilus_trader.analysis.themes import register_theme
register_theme(
    name="custom",
    template="plotly_white",
    colors={"primary": "#003366", "positive": "#2e8b57", ...}
)
```

### Extension Points

1. **Chart Registry**: `register_chart("name", chart_func)` for custom charts
2. **Low-level API**: `create_tearsheet_from_stats()` for precomputed data
3. **Individual Charts**: `create_equity_curve()`, `create_drawdown_chart()`, etc.

### Known Issues (Discord Research)

1. **Epoch timestamp bug** (2025-12-07): Open positions cause equity curve to start from 1970
2. **Visualization extra** only available on nightly (`pip install nautilus_trader[visualization]`)
3. **Equity tracking** tracks realized PnL, not unrealized (workaround: use cache for unrealized)

## Constitution Check

### Principle Compliance

| Principle | Status | Notes |
|-----------|--------|-------|
| Black Box Design | PASS | Chart registry = replaceable modules with clean APIs |
| KISS & YAGNI | PASS | Leverage existing NautilusTrader tearsheet system |
| Native First | PASS | Uses native PortfolioAnalyzer, not custom calculations |
| No df.iterrows() | PASS | All chart functions use vectorized operations |

### TDD Discipline

- RED: Write tests for custom chart extensions
- GREEN: Implement custom charts using registry
- REFACTOR: Optimize performance for large datasets

### Quality Gates (Pre-Commit)

- [ ] All tests pass (`uv run pytest tests/test_tearsheets.py`)
- [ ] Code formatted (`ruff format .`)
- [ ] Linting clean (`ruff check .`)
- [ ] Coverage > 80%

## Architecture Overview

### System Context

```
┌─────────────────────────────────────────────────────────────────┐
│                       NautilusTrader                            │
├─────────────────────────────────────────────────────────────────┤
│  BacktestEngine                                                 │
│    ├── Portfolio                                                │
│    │     └── PortfolioAnalyzer                                  │
│    │           ├── get_performance_stats_pnls()                 │
│    │           ├── get_performance_stats_returns()              │
│    │           ├── get_performance_stats_general()              │
│    │           └── returns() -> pd.Series                       │
│    └── Cache                                                    │
│          ├── orders()                                           │
│          ├── positions()                                        │
│          └── position_snapshots()                               │
├─────────────────────────────────────────────────────────────────┤
│  nautilus_trader.analysis                                       │
│    ├── TearsheetConfig         <- Configuration                 │
│    ├── create_tearsheet()      <- High-level API                │
│    ├── create_tearsheet_from_stats() <- Low-level API           │
│    ├── register_chart()        <- Extension point               │
│    └── themes.py               <- Theme system                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  This Feature (004): Custom Extensions                          │
├─────────────────────────────────────────────────────────────────┤
│  1. Multi-strategy comparison charts                            │
│  2. Custom metrics visualization                                │
│  3. Project-specific theme                                      │
│  4. CLI integration for batch processing                        │
└─────────────────────────────────────────────────────────────────┘
```

### Component Diagram

```
┌────────────────────┐     ┌────────────────────┐
│  BacktestEngine    │────▶│  PortfolioAnalyzer │
└────────────────────┘     └─────────┬──────────┘
                                     │
                                     ▼
┌────────────────────┐     ┌────────────────────┐
│  TearsheetConfig   │────▶│  create_tearsheet  │
└────────────────────┘     └─────────┬──────────┘
                                     │
          ┌──────────────────────────┼──────────────────────────┐
          │                          │                          │
          ▼                          ▼                          ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Chart Registry │     │  Theme System   │     │  Grid Layout    │
│  (Built-in +    │     │  (4 built-in +  │     │  (Auto or       │
│   Custom)       │     │   custom)       │     │   custom)       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
          │
          ▼
┌──────────────────────────────────────────────────────────────────┐
│  Self-Contained HTML Output (Plotly.js embedded)                 │
└──────────────────────────────────────────────────────────────────┘
```

## Technical Decisions

### Decision 1: Use Native NautilusTrader Tearsheet System

**Options Considered**:
1. **Option A**: Use existing `nautilus_trader.analysis.tearsheet`
   - Pros: Battle-tested, maintained by NautilusTrader team, theme system, chart registry
   - Cons: Limited to nightly builds, some bugs (epoch timestamp)
2. **Option B**: Build custom tearsheet from scratch
   - Pros: Full control, can fix bugs immediately
   - Cons: Duplicates existing work, maintenance burden, constitution violation (not Native First)

**Selected**: Option A - Use Native NautilusTrader Tearsheet System

**Rationale**:
- Follows "Native First" constitution principle
- Existing system covers 100% of FR-001 through FR-012
- Chart registry allows custom extensions for project-specific needs
- Bug fixes should be contributed upstream

---

### Decision 2: Extension Strategy for Custom Features

**Options Considered**:
1. **Option A**: Register custom charts via `register_chart()`
   - Pros: Clean integration, no monkey-patching
   - Cons: Limited to chart API
2. **Option B**: Fork and modify tearsheet.py
   - Pros: Full flexibility
   - Cons: Maintenance burden, breaks on NautilusTrader updates

**Selected**: Option A - Use Chart Registry

**Rationale**:
- Black Box Design: Custom charts as replaceable modules
- Multi-strategy comparison can be a registered chart
- Custom metrics can use `_register_tearsheet_chart()`

---

### Decision 3: Multi-Strategy Comparison Implementation

**Options Considered**:
1. **Option A**: Single tearsheet with overlaid equity curves
   - Pros: Direct comparison, single file output
   - Cons: Requires multiple engine results aggregation
2. **Option B**: Separate tearsheets + summary comparison page
   - Pros: Modular, easier to implement
   - Cons: Multiple files to manage

**Selected**: Option A - Single Comparison Tearsheet

**Rationale**:
- User Story 6 requires side-by-side comparison in single view
- Use `create_tearsheet_from_stats()` with aggregated data
- Custom comparison chart registered via registry

---

## Implementation Strategy

### Phase 1: Foundation & Validation

**Goal**: Verify native tearsheet system works with our nightly environment

**Deliverables**:
- [ ] Test `create_tearsheet()` with sample backtest
- [ ] Document any bugs or gaps vs spec requirements
- [ ] Create base test fixtures for tearsheet testing

**Dependencies**: None

---

### Phase 2: Custom Extensions

**Goal**: Implement project-specific enhancements

**Deliverables**:
- [ ] Custom theme registration (`nautilus_dev` theme)
- [ ] Multi-strategy comparison chart (User Story 6)
- [ ] Custom metrics chart (User Story 5)
- [ ] Edge case handling (zero trades, all losses, etc.)

**Dependencies**: Phase 1

---

### Phase 3: Integration & Testing

**Goal**: Full integration with project workflow

**Deliverables**:
- [ ] Backtest wrapper that auto-generates tearsheet
- [ ] CLI integration for batch tearsheet generation
- [ ] Performance tests (1-year daily, 10K+ data points)
- [ ] Documentation with usage examples

**Dependencies**: Phase 2

---

## File Structure

```
strategies/                           # Existing
├── common/
│   └── tearsheet/                    # NEW: Custom extensions
│       ├── __init__.py
│       ├── comparison.py             # Multi-strategy comparison chart
│       ├── custom_metrics.py         # Custom metrics chart
│       └── themes.py                 # Project-specific themes

tests/
├── test_tearsheets.py                # NEW: Tearsheet tests
└── integration/
    └── test_tearsheet_integration.py # Integration tests
```

## API Design

### Public Interface

```python
# Use native NautilusTrader API
from nautilus_trader.analysis.tearsheet import create_tearsheet
from nautilus_trader.analysis import TearsheetConfig

# Custom extensions
from strategies.common.tearsheet import (
    register_custom_charts,       # One-time setup
    create_comparison_tearsheet,  # Multi-strategy comparison
    NAUTILUS_DEV_THEME,           # Project theme
)
```

### Custom Comparison API

```python
def create_comparison_tearsheet(
    engines: list[BacktestEngine],
    strategy_names: list[str] | None = None,
    output_path: str = "comparison.html",
    config: TearsheetConfig | None = None,
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

    Returns
    -------
    str
        Path to generated HTML file.
    """
```

### Configuration

```python
# No custom config class needed - use TearsheetConfig
from nautilus_trader.analysis import TearsheetConfig

config = TearsheetConfig(
    charts=["run_info", "stats_table", "equity", "drawdown", "monthly_returns"],
    theme="nautilus_dev",  # Our custom theme
    height=2000,
)
```

## Testing Strategy

### Unit Tests
- [ ] Test custom theme registration
- [ ] Test comparison chart with mock data
- [ ] Test edge cases (empty trades, all losses)
- [ ] Test custom metrics chart

### Integration Tests
- [ ] Test with real BacktestEngine output
- [ ] Test self-contained HTML generation (no external deps)
- [ ] Test with Binance historical data (Spec 002)
- [ ] Test performance with 10K+ data points

### Performance Tests
- [ ] Benchmark tearsheet generation time (< 5 seconds for 1-year daily)
- [ ] Verify HTML file size (< 2MB)
- [ ] Test browser rendering performance

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Epoch timestamp bug in equity chart | Medium | High (confirmed) | Test with closed positions only; report bug upstream |
| Nightly API changes | Low | Medium | Pin nightly version; test before upgrade |
| Performance with large datasets | Medium | Low | Use ScatterGL for 10K+ points; chunk large datasets |
| Missing OHLC data for trade overlay | Low | Medium | Graceful degradation to equity-only chart |

## Dependencies

### External Dependencies
- NautilusTrader >= 1.221.0 (nightly with visualization extra)
- Plotly >= 6.3.1
- Pandas (for data manipulation)

### Internal Dependencies
- Spec 002: Binance historical data for integration tests

## Acceptance Criteria

- [ ] All unit tests passing (coverage > 80%)
- [ ] All integration tests passing
- [ ] Tearsheet generates in < 5 seconds for 1-year daily
- [ ] HTML file size < 2MB
- [ ] All 8 built-in charts render without JS errors
- [ ] Documentation updated in `docs/concepts/`
- [ ] alpha-debug verification passed

---

## Post-Design Constitution Check

### Principle Compliance (Final)

| Principle | Status | Evidence |
|-----------|--------|----------|
| **Black Box Design** | PASS | Uses NautilusTrader chart registry; custom charts are replaceable modules |
| **Everything Replaceable** | PASS | Custom comparison chart can be swapped without affecting native system |
| **KISS & YAGNI** | PASS | Leverages existing tearsheet system; only adds 3 custom files |
| **Native First** | PASS | Uses `create_tearsheet()`, `TearsheetConfig`, `register_chart()` |
| **No df.iterrows()** | PASS | All chart functions use vectorized Pandas/NumPy operations |
| **TDD Discipline** | PLANNED | Test fixtures in Phase 1; RED-GREEN-REFACTOR in Phase 2 |

### Quality Gate Compliance

| Gate | Status | Notes |
|------|--------|-------|
| Type hints | PLANNED | All custom functions will have type hints |
| Docstrings | PLANNED | NumPy-style docstrings on public API |
| Coverage > 80% | PLANNED | Test plan includes all custom code |
| No hardcoded values | PASS | Uses TearsheetConfig for all settings |
| No NEEDS CLARIFICATION | PASS | All unknowns resolved in research.md |

### Prohibited Actions Check

| Prohibited | Avoided? | Notes |
|------------|----------|-------|
| df.iterrows() | YES | Uses vectorized operations |
| Reimplement native | YES | Uses native tearsheet system |
| Create report files | YES | Only creates user-requested HTML tearsheets |
| Hardcode secrets | N/A | No secrets in visualization |

### Gate Violations

**None identified.** Design follows all constitution principles.

---

## Appendix: Generated Artifacts

| Artifact | Path | Status |
|----------|------|--------|
| Feature Spec | `specs/004-plotly-backtest-tearsheets/spec.md` | Complete |
| Implementation Plan | `specs/004-plotly-backtest-tearsheets/plan.md` | Complete |
| Research | `specs/004-plotly-backtest-tearsheets/research.md` | Complete |
| Data Model | `specs/004-plotly-backtest-tearsheets/data-model.md` | Complete |
| API Contract | `specs/004-plotly-backtest-tearsheets/contracts/tearsheet-api.yaml` | Complete |
| Quickstart | `specs/004-plotly-backtest-tearsheets/quickstart.md` | Complete |
