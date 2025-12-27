# Data Model: Alpha-Evolve Backtest Evaluator

**Feature Branch**: `007-alpha-evolve-evaluator`
**Created**: 2025-12-27

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    EvaluationRequest                         │
│─────────────────────────────────────────────────────────────│
│ + strategy_code: str              # Python source code       │
│ + strategy_class_name: str        # Class to instantiate     │
│ + config_class_name: str          # Config class name        │
│ + backtest_config: BacktestConfig # Optional override        │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ evaluates to
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    EvaluationResult                          │
│─────────────────────────────────────────────────────────────│
│ + success: bool                   # Evaluation completed     │
│ + metrics: FitnessMetrics | None  # Extracted metrics        │
│ + error: str | None               # Error message if failed  │
│ + error_type: str | None          # Error classification     │
│ + duration_ms: int                # Execution time           │
│ + trade_count: int                # Number of trades         │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ contains
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    FitnessMetrics (from spec-006)            │
│─────────────────────────────────────────────────────────────│
│ + sharpe_ratio: float             # Risk-adjusted return     │
│ + calmar_ratio: float             # CAGR / MaxDD             │
│ + max_drawdown: float             # Maximum peak-to-trough   │
│ + cagr: float                     # Compound annual growth   │
│ + total_return: float             # Total period return      │
│ + trade_count: int | None         # Number of trades         │
│ + win_rate: float | None          # Winning trade percentage │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    BacktestConfig                            │
│─────────────────────────────────────────────────────────────│
│ + catalog_path: str | Path        # ParquetDataCatalog path  │
│ + instrument_id: str              # Trading instrument       │
│ + start_date: str                 # Backtest start (ISO8601) │
│ + end_date: str                   # Backtest end (ISO8601)   │
│ + bar_type: str                   # Bar aggregation spec     │
│ + initial_capital: float          # Starting balance         │
│ + venue: str                      # Exchange name            │
│ + oms_type: str                   # NETTING or HEDGING       │
│ + account_type: str               # CASH, MARGIN, BETTING    │
│ + base_currency: str              # Account currency         │
│ + random_seed: int | None         # Reproducibility seed     │
└─────────────────────────────────────────────────────────────┘
```

## Entity Definitions

### EvaluationRequest

**Purpose**: Input container for strategy evaluation.

| Field | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| strategy_code | str | Yes | - | Non-empty, valid Python |
| strategy_class_name | str | No | "EvolvedStrategy" | Valid identifier |
| config_class_name | str | No | "EvolvedStrategyConfig" | Valid identifier |
| backtest_config | BacktestConfig | No | None | Uses evaluator default |

**Validation Rules**:
- `strategy_code` must pass `ast.parse()` (valid Python syntax)
- Class names must be valid Python identifiers (no spaces, starts with letter)

---

### EvaluationResult

**Purpose**: Output container with evaluation outcome.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| success | bool | Yes | - | True if backtest completed |
| metrics | FitnessMetrics | No | None | Extracted performance metrics |
| error | str | No | None | Error message if failed |
| error_type | str | No | None | Classification: syntax/import/runtime/timeout |
| duration_ms | int | Yes | - | Total execution time |
| trade_count | int | Yes | 0 | Number of trades executed |

**State Transitions**:
```
Initial → Loading → Running → Extracting → Complete
            │           │          │
            ▼           ▼          ▼
         [syntax]   [runtime]   [extraction]
            │           │          │
            └───────────┴──────────┘
                        │
                        ▼
                     Failed
```

**Error Types**:
| Type | Cause | Example |
|------|-------|---------|
| syntax | Invalid Python | `def foo(` (unclosed paren) |
| import | Missing module | `import nonexistent_lib` |
| runtime | Backtest crash | Division by zero in on_bar |
| timeout | Exceeded limit | Infinite loop |
| data | Missing data | Invalid instrument_id |

---

### BacktestConfig

**Purpose**: Configuration for backtest execution.

| Field | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| catalog_path | str \| Path | Yes | - | Path must exist |
| instrument_id | str | Yes | - | Format: SYMBOL.VENUE |
| start_date | str | Yes | - | ISO 8601 date |
| end_date | str | Yes | - | ISO 8601, > start_date |
| bar_type | str | No | "1-MINUTE-LAST" | Valid bar spec |
| initial_capital | float | No | 100_000.0 | > 0 |
| venue | str | No | "BINANCE" | Supported venue |
| oms_type | str | No | "NETTING" | NETTING or HEDGING |
| account_type | str | No | "MARGIN" | CASH/MARGIN/BETTING |
| base_currency | str | No | "USDT" | Valid currency |
| random_seed | int \| None | No | 42 | Seed for reproducibility |

**Validation Rules**:
- `catalog_path` must exist and contain data for `instrument_id`
- `end_date` must be after `start_date`
- Date range must have data in catalog
- `bar_type` format: `{period}-{spec}-{price}` (e.g., "1-MINUTE-LAST")

---

### FitnessMetrics (from spec-006)

**Purpose**: Standardized performance metrics for strategy comparison.

| Field | Type | Range | Formula |
|-------|------|-------|---------|
| sharpe_ratio | float | -∞ to +∞ | (Rp - Rf) / σp (annualized) |
| calmar_ratio | float | -∞ to +∞ | CAGR / abs(MaxDD) |
| max_drawdown | float | 0 to 1 | Peak-to-trough % |
| cagr | float | -1 to +∞ | (1 + R)^(365/days) - 1 |
| total_return | float | -1 to +∞ | (End - Start) / Start |
| trade_count | int \| None | 0 to +∞ | Count of closed positions |
| win_rate | float \| None | 0 to 1 | Wins / Total trades |

**Special Cases**:
| Scenario | Metrics Behavior |
|----------|-----------------|
| No trades | All metrics = 0, trade_count = 0 |
| All losses | Negative sharpe/calmar, max_drawdown > 0 |
| Division by zero | Return 0 for that metric |

---

## Data Flow

```
┌──────────────────┐
│ EvaluationRequest│
│ (strategy_code)  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Syntax Validation│──── error ──→ EvaluationResult(error_type="syntax")
└────────┬─────────┘
         │ valid
         ▼
┌──────────────────┐
│ Dynamic Loading  │──── error ──→ EvaluationResult(error_type="import")
│ (exec + module)  │
└────────┬─────────┘
         │ loaded
         ▼
┌──────────────────┐
│ Strategy Instance│
│ + Config Instance│
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ BacktestEngine   │──── error ──→ EvaluationResult(error_type="runtime")
│ Execution        │──── timeout ─→ EvaluationResult(error_type="timeout")
└────────┬─────────┘
         │ complete
         ▼
┌──────────────────┐
│ PortfolioAnalyzer│
│ Metrics Extract  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ EvaluationResult │
│ (success=True)   │
└──────────────────┘
```

## Integration with spec-006

The `FitnessMetrics` dataclass is imported from `scripts/alpha_evolve/store.py`:

```python
from scripts.alpha_evolve.store import FitnessMetrics

# In evaluator.py
def _extract_metrics(self, engine: BacktestEngine) -> FitnessMetrics:
    # Extract from PortfolioAnalyzer
    stats_returns = engine.portfolio.analyzer.get_performance_stats_returns()
    stats_general = engine.portfolio.analyzer.get_performance_stats_general()

    return FitnessMetrics(
        sharpe_ratio=stats_returns.get("Sharpe Ratio (252 days)", 0.0),
        calmar_ratio=self._calculate_calmar(cagr, max_dd),
        max_drawdown=abs(stats_returns.get("Max Drawdown", 0.0)),
        cagr=self._calculate_cagr(total_return, days),
        total_return=engine.portfolio.total_return(),
        trade_count=len(engine.cache.positions_closed()),
        win_rate=stats_general.get("Win Rate", 0.0),
    )
```

## Persistence Notes

- **EvaluationRequest**: Not persisted (ephemeral input)
- **EvaluationResult**: Not persisted directly (metrics saved via ProgramStore)
- **BacktestConfig**: May be persisted as part of experiment configuration
- **FitnessMetrics**: Persisted in ProgramStore (spec-006)

The evaluator is stateless - it receives requests, runs evaluations, and returns results. Persistence of results is handled by the evolution controller (spec-009) using the ProgramStore (spec-006).
