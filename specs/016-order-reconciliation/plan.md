# Implementation Plan: Order Reconciliation System

**Feature Branch**: `016-order-reconciliation`
**Created**: 2025-12-30
**Status**: Phase 1 Complete
**Spec Reference**: `specs/016-order-reconciliation/spec.md`

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| Black Box Design | PASS | Reconciler as independent module with clean API |
| KISS & YAGNI | PASS | Using existing NautilusTrader reconciliation - no reinventing |
| Native First | PASS | Leveraging native `LiveExecEngineConfig` parameters |
| Performance Constraints | PASS | Async polling, no blocking operations |
| TDD Discipline | PLANNED | Integration tests with mocked venue responses |

## Architecture Overview

This feature configures and extends NautilusTrader's built-in reconciliation capabilities rather than building a custom reconciliation system. NautilusTrader already provides:

1. **Startup Reconciliation** - via `generate_order_status_reports`, `generate_fill_reports`, `generate_position_status_reports`
2. **In-Flight Monitoring** - via `inflight_check_*` parameters
3. **Continuous Polling** - via `open_check_*` parameters
4. **External Order Claims** - via `StrategyConfig.external_order_claims`

### System Context

```
                    TradingNode
                         │
    ┌────────────────────┼────────────────────┐
    │                    │                    │
    ▼                    ▼                    ▼
┌─────────┐      ┌──────────────┐      ┌─────────┐
│  Cache  │◄────►│ ExecEngine   │◄────►│ Venue   │
│ (Redis) │      │              │      │  API    │
└─────────┘      │ Reconciler   │      └─────────┘
                 │ - startup    │
                 │ - in-flight  │
                 │ - continuous │
                 └──────────────┘
```

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        TradingNode                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                LiveExecEngineConfig                       │   │
│  ├───────────────┬────────────────┬─────────────────────────┤   │
│  │ Startup       │ In-Flight      │ Continuous              │   │
│  │ Reconciliation│ Monitoring     │ Polling                 │   │
│  │               │                │                         │   │
│  │ - delay: 10s  │ - interval: 2s │ - interval: 5s          │   │
│  │ - lookback:   │ - threshold: 5s│ - lookback: 60min       │   │
│  │   unlimited   │ - retries: 5   │ - threshold: 5s         │   │
│  └───────────────┴────────────────┴─────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    CacheConfig                            │   │
│  │  database: Redis (localhost:6379)                         │   │
│  │  persist_account_events: True  <- CRITICAL for recovery   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Technical Decisions

### Decision 1: Position Mode

**Options Considered**:
1. **NETTING Mode**: Single position per instrument
   - Pros: Fully supported, no known bugs, simpler state management
   - Cons: Cannot hold simultaneous long/short
2. **HEDGING Mode**: Separate long/short positions
   - Pros: More flexible trading strategies
   - Cons: Bug #3104 (long-lived positions fail), Bybit not supported

**Selected**: NETTING Mode

**Rationale**: HEDGING mode has critical open bug #3104 affecting positions >10 days. Bybit doesn't support hedge mode at all. NETTING mode is stable and fully tested.

---

### Decision 2: Reconciliation Strategy

**Options Considered**:
1. **Native NautilusTrader Reconciliation**: Use existing `LiveExecEngineConfig`
   - Pros: Battle-tested, maintained by core team, comprehensive
   - Cons: Limited customization
2. **Custom Reconciliation Module**: Build separate reconciler
   - Pros: Full control, custom logic
   - Cons: Reinventing wheel, maintenance burden, more bugs

**Selected**: Native NautilusTrader Reconciliation

**Rationale**: NautilusTrader's reconciliation is mature with three standardized methods. Custom implementation would violate KISS/YAGNI principles and introduce new bugs.

---

### Decision 3: Cache Backend

**Options Considered**:
1. **Redis**: Persistent, fast, battle-tested
   - Pros: Fast recovery, distributed support, persistence
   - Cons: External dependency
2. **SQLite/File-based**: Local, no external deps
   - Pros: Simple setup
   - Cons: Slower, no distributed support

**Selected**: Redis

**Rationale**: Required for production recovery. Discord community strongly recommends Redis for `persist_account_events=True`.

---

## Implementation Strategy

### Phase 1: Foundation (Configuration Layer)

**Goal**: Create production-ready TradingNode configuration with reconciliation enabled.

**Deliverables**:
- [x] `config/reconciliation_config.py` - Pydantic model for reconciliation settings
- [x] `config/trading_node_config.py` - Production TradingNode configuration
- [ ] Unit tests for configuration validation

**Dependencies**: Spec 014 (TradingNode Configuration)

---

### Phase 2: Integration & Monitoring

**Goal**: Integrate reconciliation with monitoring and alerting.

**Deliverables**:
- [ ] Reconciliation event handlers (log discrepancies)
- [ ] Grafana dashboard panel for reconciliation status
- [ ] Alert rules for position discrepancies

**Dependencies**: Phase 1, Spec 005 (Grafana Monitoring)

---

### Phase 3: External Order Handling

**Goal**: Configure external order claims for web/app-placed orders.

**Deliverables**:
- [ ] Strategy configuration with `external_order_claims`
- [ ] Documentation for claiming external positions
- [ ] Integration tests with mock external orders

**Dependencies**: Phase 2

---

### Phase 4: Testing & Validation

**Goal**: Comprehensive testing of reconciliation scenarios.

**Deliverables**:
- [ ] Restart recovery tests
- [ ] Disconnection simulation tests
- [ ] Position discrepancy detection tests
- [ ] Performance benchmarks (< 30s startup, < 5s periodic)

**Dependencies**: Phase 3

---

## File Structure

```
config/
├── reconciliation/
│   ├── __init__.py
│   ├── config.py              # ReconciliationConfig Pydantic model
│   └── presets.py             # Conservative/Aggressive presets
├── trading_node/
│   ├── __init__.py
│   └── live_config.py         # LiveTradingNodeConfig
tests/
├── integration/
│   └── test_reconciliation.py # Integration tests
└── unit/
    └── test_reconciliation_config.py
docs/
└── guides/
    └── reconciliation.md      # User documentation
```

## API Design

### Configuration Interface

```python
from pydantic import BaseModel, Field
from typing import Optional, List

class ReconciliationConfig(BaseModel):
    """Reconciliation configuration with production defaults."""

    # Startup
    enabled: bool = True
    startup_delay_secs: float = Field(default=10.0, ge=10.0)
    lookback_mins: Optional[int] = None  # None = max history

    # In-Flight
    inflight_check_interval_ms: int = Field(default=2000, ge=1000)
    inflight_check_threshold_ms: int = Field(default=5000, ge=1000)
    inflight_check_retries: int = Field(default=5, ge=1)

    # Continuous Polling
    open_check_interval_secs: Optional[float] = Field(default=5.0, ge=1.0)
    open_check_lookback_mins: int = Field(default=60, ge=60)
    open_check_threshold_ms: int = Field(default=5000, ge=1000)

    # Memory Management
    purge_closed_orders_interval_mins: int = 10
    purge_closed_orders_buffer_mins: int = 60

    def to_live_exec_engine_config(self) -> dict:
        """Convert to LiveExecEngineConfig kwargs."""
        return {
            "reconciliation": self.enabled,
            "reconciliation_startup_delay_secs": self.startup_delay_secs,
            "reconciliation_lookback_mins": self.lookback_mins,
            "inflight_check_interval_ms": self.inflight_check_interval_ms,
            "inflight_check_threshold_ms": self.inflight_check_threshold_ms,
            "inflight_check_retries": self.inflight_check_retries,
            "open_check_interval_secs": self.open_check_interval_secs,
            "open_check_lookback_mins": self.open_check_lookback_mins,
            "open_check_threshold_ms": self.open_check_threshold_ms,
            "purge_closed_orders_interval_mins": self.purge_closed_orders_interval_mins,
            "purge_closed_orders_buffer_mins": self.purge_closed_orders_buffer_mins,
        }
```

### Strategy Configuration (External Claims)

```python
from nautilus_trader.config import StrategyConfig

class MyStrategyConfig(StrategyConfig):
    """Strategy with external order claims."""

    instrument_ids: List[str]

    @property
    def external_order_claims(self) -> List[str]:
        """Claim all configured instruments."""
        return self.instrument_ids
```

## Testing Strategy

### Unit Tests
- [ ] ReconciliationConfig validation (min values, types)
- [ ] Config conversion to LiveExecEngineConfig
- [ ] Preset configurations (conservative, aggressive)

### Integration Tests
- [ ] TradingNode startup with reconciliation
- [ ] Mock venue returning discrepancies
- [ ] External order detection and claiming
- [ ] In-flight order timeout handling

### Performance Tests
- [ ] Startup reconciliation < 30 seconds
- [ ] Periodic reconciliation < 5 seconds
- [ ] Memory usage during purge cycles

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Bug #3104 (HEDGING) | High | N/A | Use NETTING mode only |
| Bug #3042 (IB routing) | Medium | Low | Monitor for fix, not using IB initially |
| Redis unavailable | High | Low | Health checks, graceful degradation |
| Long reconciliation time | Medium | Medium | Optimize lookback window, parallel queries |
| False discrepancy alerts | Low | Medium | Use threshold delays, retry logic |

## Dependencies

### External Dependencies
- NautilusTrader >= 1.222.0 (nightly)
- Redis >= 6.0

### Internal Dependencies
- Spec 014 (TradingNode Configuration) - REQUIRED
- Spec 015 (Binance Exec Client) - REQUIRED
- Spec 005 (Grafana Monitoring) - OPTIONAL
- Spec 018 (Redis Cache) - REQUIRED

## Known Issues & Workarounds

### Issue: Binance HEDGING Mode (Bug #3104)
**Workaround**: Use NETTING mode only. Do not enable `dualSidePosition=true`.

### Issue: Bybit Hedge Mode
**Workaround**: Not supported. Use NETTING mode.

### Issue: IB Venue Routing (Bug #3042)
**Workaround**: Not using Interactive Brokers initially. Monitor for fix.

### Issue: INTERNAL-DIFF Positions
**Workaround**: Use develop branch for latest fixes. Set appropriate lookback window.

## Acceptance Criteria

- [x] Research complete (research.md)
- [ ] All unit tests passing (coverage > 80%)
- [ ] All integration tests passing
- [ ] Startup reconciliation < 30 seconds
- [ ] Periodic check < 5 seconds
- [ ] Documentation updated
- [ ] Code review approved
- [ ] Grafana dashboard shows reconciliation status
