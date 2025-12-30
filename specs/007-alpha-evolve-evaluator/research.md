# Research: Alpha-Evolve Backtest Evaluator

**Feature Branch**: `007-alpha-evolve-evaluator`
**Researched**: 2025-12-27
**Status**: Complete

## Research Questions Resolved

### RQ1: Dynamic Strategy Loading in NautilusTrader

**Question**: How to load strategy code from string without permanent files?

**Decision**: Use `exec()` with `types.ModuleType`

**Rationale**:
- NautilusTrader's `ImportableStrategyConfig` requires file-based imports (`module:ClassName` format)
- For dynamic evaluation, we need to bypass this limitation
- Python's `exec()` with a custom module namespace allows:
  - Loading code without file I/O
  - Immediate cleanup after evaluation
  - Full access to NautilusTrader imports (already in `sys.modules`)

**Implementation Pattern**:
```python
import types
import sys

def load_strategy_from_string(code: str, class_name: str) -> type:
    module = types.ModuleType("evolved_strategy")
    module.__file__ = "<dynamic>"
    sys.modules["evolved_strategy"] = module
    exec(code, module.__dict__)
    return getattr(module, class_name)
```

**Alternatives Considered**:
1. Temporary file + importlib: Full import semantics but file I/O overhead
2. ast.parse + compile: Pre-validation but same execution behavior

---

### RQ2: BacktestNode vs BacktestEngine

**Question**: Which NautilusTrader API to use for evaluation?

**Decision**: Use `BacktestEngine` (low-level API)

**Rationale**:
- `BacktestNode` requires `ImportableStrategyConfig` (file-based)
- `BacktestEngine` allows direct strategy instance injection:
  ```python
  engine.add_strategy(strategy_instance)
  ```
- More control over venue/data configuration
- Better error handling access

**Implementation Pattern**:
```python
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.config import BacktestEngineConfig

engine = BacktestEngine(config=engine_config)
engine.add_venue(venue)
engine.add_instrument(instrument)
engine.add_data(bars)
engine.add_strategy(strategy)
engine.run()
```

**Alternatives Considered**:
1. BacktestNode: Simpler but requires file-based strategy imports
2. Custom executor: Over-engineering, reinventing the wheel

---

### RQ3: Metrics Extraction from PortfolioAnalyzer

**Question**: How to extract standardized fitness metrics from backtest results?

**Decision**: Use `engine.portfolio.analyzer` methods

**Rationale**:
- NautilusTrader's `PortfolioAnalyzer` provides all required metrics
- Three categories of stats available:
  - `get_performance_stats_pnls()`: PnL metrics
  - `get_performance_stats_returns()`: Sharpe, Sortino, MaxDD
  - `get_performance_stats_general()`: Win rate, profit factor

**Implementation Pattern**:
```python
def extract_metrics(engine: BacktestEngine) -> FitnessMetrics:
    analyzer = engine.portfolio.analyzer
    stats_returns = analyzer.get_performance_stats_returns()
    stats_general = analyzer.get_performance_stats_general()

    # Calculate CAGR from total return and period
    total_return = engine.portfolio.total_return()

    return FitnessMetrics(
        sharpe_ratio=stats_returns.get("Sharpe Ratio (252 days)", 0.0),
        calmar_ratio=calculate_calmar(cagr, max_dd),
        max_drawdown=stats_returns.get("Max Drawdown", 0.0),
        cagr=calculate_cagr(total_return, days),
        total_return=total_return,
        trade_count=len(engine.cache.positions_closed()),
        win_rate=stats_general.get("Win Rate", 0.0),
    )
```

**Key Metrics Mapping**:
| Spec Metric | NautilusTrader Source |
|------------|----------------------|
| sharpe_ratio | `stats_returns["Sharpe Ratio (252 days)"]` |
| max_drawdown | `stats_returns["Max Drawdown"]` |
| win_rate | `stats_general["Win Rate"]` |
| total_return | `portfolio.total_return()` |
| trade_count | `len(cache.positions_closed())` |
| calmar_ratio | Calculated: CAGR / abs(MaxDD) |
| cagr | Calculated: (1 + total_return)^(365/days) - 1 |

---

### RQ4: Concurrency Control for Memory Safety

**Question**: How to limit concurrent evaluations to prevent OOM?

**Decision**: Use `asyncio.Semaphore` with `asyncio.to_thread`

**Rationale**:
- BacktestEngine is CPU-bound and blocking
- Evolution controller (spec-009) will be async
- `asyncio.to_thread` runs blocking code in thread pool
- `asyncio.Semaphore` limits concurrent executions

**Implementation Pattern**:
```python
class StrategyEvaluator:
    def __init__(self, max_concurrent: int = 2):
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def evaluate(self, request: EvaluationRequest) -> EvaluationResult:
        async with self._semaphore:
            return await asyncio.to_thread(
                self.evaluate_sync, request
            )
```

**Memory Considerations**:
- BacktestEngine uses ~2-4GB RAM per evaluation (6mo 1-min bars)
- With max_concurrent=2, peak memory ~8GB
- Recommendation: max_concurrent <= (available_ram - 4GB) / 4

---

### RQ5: Timeout Implementation

**Question**: How to timeout long-running evaluations?

**Decision**: Use `asyncio.wait_for` with documented limitations

**Rationale**:
- `asyncio.wait_for` provides clean async timeout
- Works with `asyncio.to_thread` wrapped functions
- Limitation: Cannot interrupt infinite loops in C extensions

**Implementation Pattern**:
```python
async def evaluate(self, request: EvaluationRequest) -> EvaluationResult:
    try:
        async with self._semaphore:
            result = await asyncio.wait_for(
                asyncio.to_thread(self.evaluate_sync, request),
                timeout=self._timeout_seconds,
            )
        return result
    except asyncio.TimeoutError:
        return EvaluationResult(
            success=False,
            metrics=None,
            error="Evaluation timeout exceeded",
            error_type="timeout",
            duration_ms=self._timeout_seconds * 1000,
            trade_count=0,
        )
```

**Known Limitations**:
- Infinite loops in pure Python: Timeout works
- Infinite loops in NautilusTrader Rust: May not interrupt
- Future enhancement: multiprocessing.Process for true isolation

---

### RQ6: Error Handling Strategy

**Question**: How to handle different error types gracefully?

**Decision**: Structured error results with error classification

**Error Types**:
| Type | Detection | Response |
|------|-----------|----------|
| `syntax` | ast.parse() before exec | Error with line number |
| `import` | Exception during exec | Error with missing module |
| `runtime` | Exception during backtest | Error with traceback |
| `timeout` | asyncio.TimeoutError | Error with configured limit |
| `data` | Empty catalog / missing instrument | Error with data path |

**Implementation Pattern**:
```python
def _validate_syntax(self, code: str) -> str | None:
    """Return error message or None if valid."""
    try:
        ast.parse(code)
        return None
    except SyntaxError as e:
        return f"Syntax error at line {e.lineno}: {e.msg}"

def evaluate_sync(self, request: EvaluationRequest) -> EvaluationResult:
    # 1. Validate syntax first
    if error := self._validate_syntax(request.strategy_code):
        return EvaluationResult(
            success=False,
            error=error,
            error_type="syntax",
            ...
        )

    # 2. Try loading
    try:
        StrategyClass, ConfigClass = self._load_strategy(...)
    except Exception as e:
        return EvaluationResult(error=str(e), error_type="import", ...)

    # 3. Try running
    try:
        engine = self._run_backtest(...)
    except Exception as e:
        return EvaluationResult(error=str(e), error_type="runtime", ...)
```

---

## Technology Best Practices

### NautilusTrader Backtest Best Practices

1. **Use V1 Wranglers**: V2 (PyO3) incompatible with BacktestEngine
2. **Use 128-bit precision**: Linux nightly default
3. **Bar timestamps**: Must be on close, not open
4. **Chunk size**: 100k-250k for streaming data
5. **Venue config**: `bar_adaptive_high_low_ordering=True` for OHLC accuracy

### Dynamic Code Execution Best Practices

1. **Validate syntax first**: Use `ast.parse()` before `exec()`
2. **Isolate namespace**: Use fresh `types.ModuleType` per evaluation
3. **Clean up**: Remove from `sys.modules` after evaluation
4. **Controlled imports**: Only allow NautilusTrader imports in evolved code

---

## Discord Community Insights

### Relevant Discussions

1. **BacktestNode vs BacktestEngine** (docs/discord/help.md:1689):
   - Community prefers BacktestEngine for programmatic control
   - BacktestNode issues with logger initialization

2. **Memory optimization** (docs/discord/questions.md:1595):
   - Chunk size 50k-250k doesn't significantly affect RAM
   - Major memory usage from engine state, not data loading

3. **Instrument precision mismatch** (docs/discord/help.md:84):
   - Common error: `fill_price.precision did not match instrument price_prec`
   - Solution: Use instruments from catalog, not manual creation

---

## Implementation Recommendations

1. **Start simple**: Phase 1 with synchronous evaluate_sync()
2. **Add async later**: Phase 3 for evolution controller integration
3. **Test with sample data**: Use existing catalog fixtures
4. **Document limitations**: Infinite loop handling, memory requirements
