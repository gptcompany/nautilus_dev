# Implementation Plan: Alpha-Evolve Strategy Templates

**Feature Branch**: `008-alpha-evolve-templates`
**Created**: 2025-12-27
**Status**: Ready for Implementation
**Spec Reference**: `specs/008-alpha-evolve-templates/spec.md`

## Architecture Overview

Strategy templates provide the evolvable foundation for the Alpha-Evolve system. They integrate with NautilusTrader's Strategy base class while adding equity tracking, order helpers, and EVOLVE-BLOCK markers for targeted mutations.

### System Context

```
┌─────────────────────────────────────────────────────────────┐
│                    Alpha-Evolve System                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Controller  │───>│  Evaluator   │───>│   Store      │  │
│  │  (spec-009)  │    │  (spec-007)  │    │  (spec-006)  │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                   │                               │
│         │                   ▼                               │
│         │           ┌──────────────┐                        │
│         └──────────>│  Templates   │  <── THIS SPEC         │
│                     │  (spec-008)  │                        │
│                     └──────────────┘                        │
│                            │                                │
│                            ▼                                │
│                     ┌──────────────┐                        │
│                     │ NautilusTrader│                       │
│                     │   Strategy   │                        │
│                     └──────────────┘                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Component Diagram

```
┌────────────────────────────────────────────────────────────┐
│                   BaseEvolveStrategy                        │
├────────────────────────────────────────────────────────────┤
│  Inherits: nautilus_trader.trading.strategy.Strategy       │
├────────────────────────────────────────────────────────────┤
│  Properties:                                                │
│    - instrument: Instrument                                 │
│    - _equity_curve: list[EquityPoint]                      │
├────────────────────────────────────────────────────────────┤
│  Lifecycle:                                                 │
│    + on_start() → subscribe bars, register indicators      │
│    + on_bar(bar) → call _on_bar_evolved, record equity     │
│    + on_stop() → cancel orders, close positions            │
│    + on_reset() → reset indicators, clear equity curve     │
├────────────────────────────────────────────────────────────┤
│  Abstract:                                                  │
│    # _on_bar_evolved(bar) → contains EVOLVE-BLOCK          │
├────────────────────────────────────────────────────────────┤
│  Order Helpers:                                             │
│    + _enter_long(quantity)                                 │
│    + _enter_short(quantity)                                │
│    + _close_position()                                     │
│    + _get_position_size() → Decimal                        │
│    + _get_equity() → float                                 │
├────────────────────────────────────────────────────────────┤
│  Equity Tracking:                                           │
│    + get_equity_curve() → list[EquityPoint]                │
└────────────────────────────────────────────────────────────┘
                            │
                            │ inherits
                            ▼
┌────────────────────────────────────────────────────────────┐
│                 MomentumEvolveStrategy                      │
├────────────────────────────────────────────────────────────┤
│  Config:                                                    │
│    - fast_period: int = 10                                 │
│    - slow_period: int = 30                                 │
├────────────────────────────────────────────────────────────┤
│  Indicators (Native Rust):                                  │
│    - fast_ema: ExponentialMovingAverage                    │
│    - slow_ema: ExponentialMovingAverage                    │
├────────────────────────────────────────────────────────────┤
│  _on_bar_evolved(bar):                                      │
│    # === EVOLVE-BLOCK: decision_logic ===                  │
│    # Entry: fast_ema > slow_ema → enter long               │
│    # Exit: fast_ema < slow_ema → close position            │
│    # === END EVOLVE-BLOCK ===                              │
└────────────────────────────────────────────────────────────┘
```

## Technical Decisions

### Decision 1: Equity Tracking Location

**Options Considered**:
1. **Option A**: Track in parent `on_bar()` after calling `_on_bar_evolved()`
   - Pros: Automatic, consistent, can't be accidentally removed
   - Cons: None significant
2. **Option B**: Track inside `_on_bar_evolved()` via helper call
   - Pros: More explicit
   - Cons: Could be removed by mutation, adds boilerplate

**Selected**: Option A

**Rationale**: Equity tracking is infrastructure, not trading logic. It should be protected from mutations.

---

### Decision 2: Order Helper Design

**Options Considered**:
1. **Option A**: Simple wrappers around order_factory.market()
   - Pros: Minimal abstraction, clear what happens
   - Cons: More code in EVOLVE-BLOCK
2. **Option B**: Smart helpers that handle position flipping
   - Pros: Simpler EVOLVE-BLOCK code, handles edge cases
   - Cons: More complex implementation

**Selected**: Option B

**Rationale**: Simpler EVOLVE-BLOCK means LLM can write better mutations. Complexity is hidden in tested infrastructure.

---

### Decision 3: EVOLVE-BLOCK Scope

**Options Considered**:
1. **Option A**: Single block for all decision logic
   - Pros: Simple, one target for mutations
   - Cons: Large blocks harder to mutate precisely
2. **Option B**: Multiple blocks (entry, exit, filters)
   - Pros: More granular mutations
   - Cons: More complex, coordination needed

**Selected**: Option A (for MVP)

**Rationale**: Start simple. Multiple blocks can be added in future iteration if needed.

---

## Implementation Strategy

### Phase 1: Base Strategy Class

**Goal**: Implement BaseEvolveStrategy with lifecycle and order helpers

**Deliverables**:
- [x] `EquityPoint` dataclass
- [x] `BaseEvolveConfig` Pydantic model
- [ ] `BaseEvolveStrategy` abstract class
  - [ ] `on_start()` with instrument lookup
  - [ ] `on_bar()` with equity recording
  - [ ] `on_stop()` with cleanup
  - [ ] `on_reset()` with state reset
  - [ ] `_enter_long()` helper
  - [ ] `_enter_short()` helper
  - [ ] `_close_position()` helper
  - [ ] `_get_position_size()` helper
  - [ ] `_get_equity()` helper
  - [ ] `get_equity_curve()` getter

**Dependencies**: NautilusTrader Strategy base class

---

### Phase 2: Seed Strategy

**Goal**: Implement working MomentumEvolveStrategy as seed

**Deliverables**:
- [ ] `MomentumEvolveConfig` with period validation
- [ ] `MomentumEvolveStrategy` with EMA crossover logic
- [ ] EVOLVE-BLOCK markers in `_on_bar_evolved()`
- [ ] Unit tests for strategy initialization
- [ ] Integration test with BacktestEngine

**Dependencies**: Phase 1

---

### Phase 3: Integration Testing

**Goal**: Verify templates work with evaluator and patching system

**Deliverables**:
- [ ] Test strategy evaluation returns metrics
- [ ] Test EVOLVE-BLOCK extraction works
- [ ] Test patched strategy executes correctly
- [ ] Test equity curve contains expected points
- [ ] Performance benchmark (< 5% overhead)

**Dependencies**: Phase 2, spec-006 (patching), spec-007 (evaluator)

---

## File Structure

```
scripts/
├── alpha_evolve/
│   ├── __init__.py           # Export templates
│   ├── templates/
│   │   ├── __init__.py       # Export BaseEvolveStrategy, MomentumEvolveStrategy
│   │   ├── base.py           # BaseEvolveStrategy, BaseEvolveConfig, EquityPoint
│   │   └── momentum.py       # MomentumEvolveStrategy, MomentumEvolveConfig
tests/
├── alpha_evolve/
│   ├── templates/
│   │   ├── __init__.py
│   │   ├── test_base.py      # BaseEvolveStrategy tests
│   │   └── test_momentum.py  # MomentumEvolveStrategy tests
│   └── test_templates_integration.py  # Integration with evaluator
```

## API Design

### Public Interface

```python
from scripts.alpha_evolve.templates import (
    # Base class and config
    BaseEvolveStrategy,
    BaseEvolveConfig,
    EquityPoint,
    # Seed strategy
    MomentumEvolveStrategy,
    MomentumEvolveConfig,
)
```

### Configuration

```python
class BaseEvolveConfig(StrategyConfig, frozen=True):
    instrument_id: InstrumentId
    bar_type: BarType
    trade_size: Decimal


class MomentumEvolveConfig(BaseEvolveConfig, frozen=True):
    fast_period: int = 10
    slow_period: int = 30
```

## Testing Strategy

### Unit Tests

- [x] Test EquityPoint creation
- [ ] Test BaseEvolveConfig validation
- [ ] Test MomentumEvolveConfig period validation
- [ ] Test order helper methods (mock portfolio)
- [ ] Test equity curve recording
- [ ] Test indicator registration

### Integration Tests

- [ ] Test with BacktestEngine (real data)
- [ ] Test produces trades on sample period
- [ ] Test equity curve populated after backtest
- [ ] Test EVOLVE-BLOCK can be extracted
- [ ] Test patched strategy runs without errors

### Performance Tests

- [ ] Benchmark equity tracking overhead
- [ ] Verify < 5% impact on backtest time

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| NautilusTrader API changes | High | Low | Pin to nightly v1.222.0 |
| Equity calculation errors | Medium | Low | Test against known backtest results |
| Order helper edge cases | Medium | Medium | Extensive unit tests |
| EVOLVE-BLOCK format mismatch | High | Low | Use same regex as spec-006 |

## Dependencies

### External Dependencies

- NautilusTrader nightly >= 1.222.0
- Python 3.11+

### Internal Dependencies

- spec-006: EVOLVE-BLOCK marker format
- spec-007: BacktestEvaluator for integration tests

## Acceptance Criteria

- [x] All research questions answered (research.md)
- [x] Data model documented (data-model.md)
- [x] API contracts defined (contracts/)
- [ ] All unit tests passing (coverage > 80%)
- [ ] All integration tests passing
- [ ] Seed strategy produces trades on 6-month BTC data
- [ ] EVOLVE-BLOCK extractable by spec-006 patching
- [ ] Performance overhead < 5%

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| Black Box Design | ✅ | BaseEvolveStrategy hides order mechanics |
| KISS & YAGNI | ✅ | Single symbol, market orders only |
| Native First | ✅ | Uses nautilus_trader.indicators |
| Performance | ✅ | No df.iterrows(), native Rust indicators |
| TDD | ⏳ | Tests to be written before implementation |
