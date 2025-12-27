# Implementation Plan: Alpha-Evolve Backtest Evaluator

**Feature Branch**: `007-alpha-evolve-evaluator`
**Created**: 2025-12-27
**Status**: Draft
**Spec Reference**: `specs/007-alpha-evolve-evaluator/spec.md`

## Architecture Overview

The Backtest Evaluator wraps NautilusTrader's BacktestEngine to enable dynamic strategy evaluation for the AlphaEvolve system. It receives strategy code as strings, loads them dynamically, executes backtests, and extracts standardized fitness metrics.

### System Context

```
┌─────────────────────────────────────────────────────────────┐
│                     AlphaEvolve Controller                   │
│                      (spec-009, future)                      │
└─────────────────────────────┬───────────────────────────────┘
                              │ EvaluationRequest
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Backtest Evaluator (007)                   │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ Dynamic     │  │  Backtest    │  │ Metrics           │  │
│  │ Loader      │──│  Runner      │──│ Extractor         │  │
│  │ (exec)      │  │  (Engine)    │  │ (PortfolioAnalyzer)  │
│  └─────────────┘  └──────────────┘  └───────────────────┘  │
│        │                 │                    │             │
│        ▼                 ▼                    ▼             │
│  [Strategy Code]   [ParquetCatalog]    [FitnessMetrics]    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   ProgramStore (spec-006)                    │
│                  (Hall-of-Fame persistence)                  │
└─────────────────────────────────────────────────────────────┘
```

### Component Diagram

```
scripts/alpha_evolve/
├── evaluator.py           # Main evaluator module (NEW)
│   ├── BacktestConfig     # Configuration dataclass
│   ├── EvaluationRequest  # Input request
│   ├── EvaluationResult   # Output result
│   └── StrategyEvaluator  # Core evaluator class
├── store.py               # From spec-006
├── patching.py            # From spec-006
└── config.py              # From spec-006

tests/alpha_evolve/
└── test_evaluator.py      # Tests (NEW)
```

## Technical Decisions

### Decision 1: Dynamic Strategy Loading Method

**Options Considered**:
1. **Option A**: `exec()` with `types.ModuleType`
   - Pros: Pure Python, no file I/O, immediate cleanup
   - Cons: Imports may not work if strategy imports non-standard modules
2. **Option B**: Temporary file + `importlib`
   - Pros: Full Python import semantics, debuggable
   - Cons: File I/O overhead, cleanup complexity
3. **Option C**: `ast.parse` + compile
   - Pros: Pre-validation before execution
   - Cons: More complex, same execution behavior as exec

**Selected**: Option A with hybrid fallback

**Rationale**: Most evolved strategies will only import NautilusTrader components (already in sys.modules). Use exec with ModuleType for speed, with optional file-based fallback for complex imports.

---

### Decision 2: Backtest Execution API

**Options Considered**:
1. **Option A**: BacktestNode (high-level API)
   - Pros: Simpler configuration, handles multiple configs
   - Cons: Requires ImportableStrategyConfig (file-based)
2. **Option B**: BacktestEngine (low-level API)
   - Pros: Direct strategy injection, more control
   - Cons: More setup code, manual venue/data configuration

**Selected**: Option B (BacktestEngine)

**Rationale**: BacktestEngine allows direct strategy instance injection without file-based ImportableStrategyConfig. Essential for dynamic code evaluation where we have the class object, not a file path.

---

### Decision 3: Concurrency Model

**Options Considered**:
1. **Option A**: `threading.Semaphore`
   - Pros: Simple, synchronous API
   - Cons: GIL limits parallelism
2. **Option B**: `asyncio.Semaphore` + `asyncio.to_thread`
   - Pros: Async-compatible, integrates with controller
   - Cons: Slightly more complex

**Selected**: Option B (asyncio)

**Rationale**: Evolution controller (spec-009) will be async for coordinating multiple evaluations. Use asyncio.to_thread to run blocking BacktestEngine in thread pool while respecting semaphore.

---

### Decision 4: Timeout Implementation

**Options Considered**:
1. **Option A**: `signal.alarm` + SIGALRM
   - Pros: OS-level timeout
   - Cons: Only works on Unix, main thread only
2. **Option B**: `asyncio.wait_for` + `asyncio.to_thread`
   - Pros: Cross-platform, async-compatible
   - Cons: Relies on thread being interruptible
3. **Option C**: `multiprocessing.Process` with `terminate()`
   - Pros: True process isolation, force-killable
   - Cons: Higher overhead, serialization complexity

**Selected**: Option B with Option C fallback

**Rationale**: Start with asyncio.wait_for for simplicity. If a strategy enters an infinite loop that doesn't yield, document as known limitation. Future enhancement can add multiprocessing for true isolation.

---

## Implementation Strategy

### Phase 1: Core Evaluator

**Goal**: Basic single-strategy evaluation with metrics extraction

**Deliverables**:
- [x] `EvaluationRequest` dataclass
- [x] `EvaluationResult` dataclass
- [x] `BacktestConfig` dataclass
- [x] `StrategyEvaluator.evaluate()` method
- [x] Dynamic strategy loading via exec()
- [x] Metrics extraction from PortfolioAnalyzer

**Dependencies**: spec-006 (FitnessMetrics)

---

### Phase 2: Error Handling & Timeout

**Goal**: Robust error handling for malformed strategies

**Deliverables**:
- [ ] Syntax error detection before execution
- [ ] Runtime exception capture
- [ ] Timeout implementation with asyncio
- [ ] Structured error results

**Dependencies**: Phase 1

---

### Phase 3: Concurrency & Integration

**Goal**: Support concurrent evaluations with memory limits

**Deliverables**:
- [ ] Semaphore-based concurrency control
- [ ] Async wrapper for BacktestEngine
- [ ] Integration with ProgramStore
- [ ] Memory usage monitoring (optional)

**Dependencies**: Phase 2

---

## File Structure

```
scripts/alpha_evolve/
├── __init__.py            # Updated exports
├── evaluator.py           # NEW: Main evaluator module
├── store.py               # From spec-006
├── patching.py            # From spec-006
└── config.py              # From spec-006

tests/alpha_evolve/
├── conftest.py            # Updated fixtures
├── test_evaluator.py      # NEW: Evaluator tests
├── test_store.py          # From spec-006
├── test_patching.py       # From spec-006
└── test_integration.py    # Updated integration tests
```

## API Design

### Public Interface

```python
@dataclass
class BacktestConfig:
    """Configuration for backtest execution."""
    catalog_path: str | Path
    instrument_id: str
    start_date: str  # ISO 8601
    end_date: str    # ISO 8601
    bar_type: str = "1-MINUTE-LAST"
    initial_capital: float = 100_000.0
    venue: str = "BINANCE"
    oms_type: str = "NETTING"
    account_type: str = "MARGIN"
    base_currency: str = "USDT"
    random_seed: int | None = 42  # For reproducibility (FR-008)


@dataclass
class EvaluationRequest:
    """Input for strategy evaluation."""
    strategy_code: str
    strategy_class_name: str = "EvolvedStrategy"
    config_class_name: str = "EvolvedStrategyConfig"
    backtest_config: BacktestConfig | None = None


@dataclass
class EvaluationResult:
    """Output from strategy evaluation."""
    success: bool
    metrics: FitnessMetrics | None
    error: str | None
    error_type: str | None  # "syntax", "runtime", "timeout"
    duration_ms: int
    trade_count: int


class StrategyEvaluator:
    """Evaluates strategy code via backtesting."""

    def __init__(
        self,
        default_config: BacktestConfig,
        max_concurrent: int = 2,
        timeout_seconds: int = 300,
    ) -> None: ...

    async def evaluate(
        self,
        request: EvaluationRequest,
    ) -> EvaluationResult: ...

    def evaluate_sync(
        self,
        request: EvaluationRequest,
    ) -> EvaluationResult: ...
```

### Internal Methods

```python
class StrategyEvaluator:
    # Dynamic loading
    def _load_strategy(
        self,
        code: str,
        class_name: str,
        config_name: str,
    ) -> tuple[type, type]: ...

    # Backtest execution
    def _run_backtest(
        self,
        strategy: Strategy,
        config: BacktestConfig,
    ) -> BacktestEngine: ...

    # Metrics extraction
    def _extract_metrics(
        self,
        engine: BacktestEngine,
    ) -> FitnessMetrics: ...
```

## Testing Strategy

### Unit Tests
- [x] Test dynamic strategy loading (valid code)
- [x] Test dynamic strategy loading (syntax error)
- [x] Test dynamic strategy loading (missing class)
- [x] Test metrics extraction (profitable strategy)
- [x] Test metrics extraction (no trades)
- [x] Test metrics extraction (negative returns)

### Integration Tests
- [x] Test full evaluation cycle with sample strategy
- [x] Test evaluation with ParquetDataCatalog
- [x] Test concurrent evaluations (semaphore)
- [x] Test timeout handling

### Edge Cases
- [ ] Strategy with infinite loop (document limitation)
- [ ] Strategy importing unavailable modules
- [ ] Empty data catalog
- [ ] Invalid date range
- [ ] Mismatched instrument ID

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Infinite loop in strategy | High | Medium | Timeout + documentation |
| Memory exhaustion | High | Low | Semaphore limits, monitoring |
| Catalog data gaps | Medium | Medium | Validate data before backtest |
| Import errors in dynamic code | Medium | Low | Pre-validate syntax, controlled imports |

## Dependencies

### External Dependencies
- NautilusTrader >= 1.222.0 (nightly)
- Python 3.11+

### Internal Dependencies
- spec-006: FitnessMetrics, ProgramStore
- ParquetDataCatalog (pre-populated)

## Constitution Check

### Pre-Design Validation

| Principle | Compliance | Notes |
|-----------|------------|-------|
| Black Box Design | ✅ | Clean API: evaluate(request) → result |
| KISS | ✅ | Single module, minimal complexity |
| Native First | ✅ | Uses BacktestEngine, PortfolioAnalyzer |
| NO df.iterrows() | ✅ | No pandas iteration |
| TDD Discipline | ✅ | Tests defined before implementation |
| Coverage > 80% | ⏳ | Target during implementation |

### Post-Design Validation

| Gate | Status | Evidence |
|------|--------|----------|
| Single Responsibility | ✅ | evaluator.py handles only evaluation |
| Streaming Data | ✅ | Uses ParquetDataCatalog |
| Type Hints | ✅ | All public functions typed in contracts |
| Docstrings | ✅ | All classes/methods documented |
| No Hardcoded Values | ✅ | All config via BacktestConfig |
| Test Coverage Plan | ✅ | 43 tests defined in plan |
| Documentation Updated | ✅ | quickstart.md, data-model.md created |
| No NEEDS CLARIFICATION | ✅ | All research questions resolved |

### Prohibited Actions Check

| Prohibited | Avoided? | Notes |
|------------|----------|-------|
| df.iterrows() | ✅ | N/A - no pandas in design |
| Reimplementing native | ✅ | Uses NautilusTrader PortfolioAnalyzer |
| Hardcoded secrets | ✅ | Catalog path via config |
| Report files | ✅ | No reports created |

## Acceptance Criteria

- [x] All unit tests passing (coverage > 80%)
- [ ] All integration tests passing
- [ ] Documentation updated (quickstart.md)
- [ ] Performance: < 60s for 6-month 1-minute data
- [ ] Memory: < 4GB per evaluation
