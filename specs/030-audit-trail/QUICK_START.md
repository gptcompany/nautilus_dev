# Quick Start Checklist for Implementation

## Pre-Implementation Verification (Do this FIRST)

```bash
# Verify Actor class is available
python3 -c "from nautilus_trader.common.actor import Actor; print('✓ Actor available')"

# Verify MessageBus pattern
python3 -c "from nautilus_trader.message_bus import MessageBus; print('✓ MessageBus available')"

# Verify events module
python3 -c "from nautilus_trader.model.events import OrderFilled, PositionOpened; print('✓ Events available')"
```

Expected output:
```
✓ Actor available
✓ MessageBus available
✓ Events available
```

---

## Phase 1: Setup (T001-T003)

- [ ] Create `/media/sam/1TB/nautilus_dev/strategies/common/audit/` directory
- [ ] Create `/media/sam/1TB/nautilus_dev/strategies/common/audit/__init__.py`
- [ ] Add DuckDB to `pyproject.toml` (optional, for queries)

**Status**: Can start immediately
**Duration**: < 30 minutes

---

## Phase 2: Foundational (T004-T010) - BLOCKS all user stories

**Critical**: Complete this phase before moving to user stories

### Sequential Tasks (must complete in order):
- [ ] T004: Create `AuditConfig` dataclass
- [ ] T005: Create `AuditEventType` enum
- [ ] T006: Create `AuditEvent` base model
- [ ] T007: Create `AppendOnlyWriter` class (test with O_APPEND)
- [ ] T008: Create `AuditEventEmitter` class (sequence tracking)

### Parallel Tasks (can run alongside):
- [ ] T009: Unit test for `AppendOnlyWriter` (test O_APPEND atomic writes)
- [ ] T010: Unit test for `AuditEvent` checksum

**Status**: Start after Phase 1
**Duration**: 3-4 hours
**Checkpoint**: Run all Phase 2 tests to verify foundation

```bash
pytest tests/unit/audit/test_writer.py tests/unit/audit/test_events.py -v
```

---

## Phase 3: User Story 1 - Parameter Logging (T011-T017)

**Parallelizable** with other user stories once Phase 2 is done

```
T011 → T012 → T013-T014 → T015-T016 → T017
```

Key tasks:
- [ ] T011: Create `ParameterChangeEvent` model
- [ ] T012: Add `emit_param_change()` to emitter
- [ ] T015: Integrate with `meta_controller.py` (add emitter, call on state change)
- [ ] T016: Integrate with `sops_sizing.py` (add emitter, call on k change)
- [ ] T017: Integration test (verify log contains old/new values)

**Status**: Can start after T010 completes
**Duration**: 2-3 hours
**Test**: Change a parameter and verify audit log captures it

---

## Phase 4: User Story 2 - Trade Logging (T018-T024)

**Parallelizable** with other user stories once Phase 2 is done

**Critical Task: T020-T022** (AuditObserver with Actor/MessageBus)

```
T018 → T019 → T020 → T021-T022 → T023-T024
                       ↑
                   KEY: Uses Actor + MessageBus
```

Key tasks:
- [ ] T020: Create `AuditObserver` class inheriting from `Actor`
  - Import: `from nautilus_trader.common.actor import Actor`
  - Import: `from nautilus_trader.config import ActorConfig`
  - Pattern: Use Discord #help OrderSpreadGuardActor as reference
  
- [ ] T021: Implement `_on_order_event()` handler
  - Subscribe to: `events.order.OrderFilled`, `events.order.OrderRejected`
  - Pattern: `self.msgbus.subscribe(topic="events.order.*", handler=self._on_order_event)`
  
- [ ] T022: Implement `_on_position_event()` handler
  - Subscribe to: `events.position.PositionOpened`, `events.position.PositionClosed`
  - Pattern: Same as T021
  
- [ ] T024: Integration test with mock NT events

**Status**: Can start after T010 completes
**Duration**: 3-4 hours (longest user story due to NT integration)
**Test**: Submit order, verify OrderFilled event is captured in audit log

**Reference Pattern**:
```python
from nautilus_trader.common.actor import Actor
from nautilus_trader.config import ActorConfig

class AuditObserver(Actor):
    def on_start(self) -> None:
        self.msgbus.subscribe(topic="events.order.*", handler=self._on_order_event)
        self.msgbus.subscribe(topic="events.position.*", handler=self._on_position_event)
    
    def _on_order_event(self, event) -> None:
        # Handle OrderFilled, OrderRejected
        pass
    
    def _on_position_event(self, event) -> None:
        # Handle PositionOpened, PositionClosed
        pass
```

---

## Phase 5: User Story 3 - Signal Logging (T025-T031)

**Parallelizable** with other user stories once Phase 2 is done

- [ ] T025: Create `SignalEvent` model
- [ ] T026: Add `emit_signal()` to emitter
- [ ] T027: Create `SystemEvent` model
- [ ] T028: Integrate with `particle_portfolio.py`
- [ ] T029: Integrate with `alpha_evolve_bridge.py`
- [ ] T030-T031: Signal event tests

**Status**: Can start after T010 completes
**Duration**: 2-3 hours
**Test**: Generate a signal, verify audit log captures value + regime + confidence

---

## Phase 6: User Story 4 - Query Infrastructure (T032-T041)

**Parallelizable** with other user stories once Phase 2 is done

- [ ] T032: Create `ParquetConverter` (JSONL → Parquet)
- [ ] T033-T034: Implement partitioning (year/month/day) + 90-day retention
- [ ] T035: Create `AuditQuery` class (DuckDB backend)
- [ ] T036-T038: Implement query methods (time_range, aggregation, incident reconstruction)
- [ ] T039-T041: Unit tests + performance benchmark

**Status**: Can start after T010 completes
**Duration**: 3-4 hours
**Test**: Convert 1M events JSONL → Parquet, query in < 5 seconds

**Note**: DuckDB is optional. JSON Lines can be queried with simple Python if DuckDB unavailable.

---

## Phase 7: Polish & Verification (T042-T047)

**After all user stories complete**

- [ ] T042: Handle disk full scenario (graceful degradation)
- [ ] T043: Implement batching/throttling for high event rate
- [ ] T044: Checksum verification + corruption detection
- [ ] T045: Create example forensics Jupyter notebook
- [ ] T046: Run alpha-debug verification on audit module
- [ ] T047: Performance benchmark (verify < 1ms write latency p99)

**Status**: Can start after T001-T041 complete
**Duration**: 2-3 hours
**Test**: Simulate disk full, high event rate, log corruption

---

## Quick Validation

After each phase, run:

```bash
# Phase 1-2: Verify core infrastructure
pytest tests/unit/audit/ -v

# Phase 3: Verify parameter logging
pytest tests/integration/test_audit_integration.py::test_parameter_logging -v

# Phase 4: Verify trade logging (needs mock NT events)
pytest tests/integration/test_audit_observer.py -v

# Phase 6: Verify query performance
pytest tests/performance/test_audit_query_performance.py -v
```

---

## Files to Create/Modify

### Core Audit Module
```
strategies/common/audit/
├── __init__.py                 (T002)
├── config.py                   (T004)
├── events.py                   (T005, T006, T011, T018, T025, T027)
├── writer.py                   (T007)
├── emitter.py                  (T008, T012, T019, T026)
├── observer.py                 (T020)
├── converter.py                (T032)
└── query.py                    (T035)
```

### Tests
```
tests/
├── unit/audit/
│   ├── test_writer.py          (T009)
│   ├── test_events.py          (T010, T013, T023, T030)
│   ├── test_emitter.py         (T014)
│   ├── test_converter.py       (T039)
│   └── test_query.py           (T040)
├── integration/
│   ├── test_audit_integration.py    (T017, T031)
│   └── test_audit_observer.py       (T024)
└── performance/
    └── test_audit_query_performance.py (T041)
```

### Integration Points
```
strategies/common/adaptive_control/
├── meta_controller.py          (T015 - add emitter call)
├── sops_sizing.py              (T016 - add emitter call)
└── particle_portfolio.py        (T028 - add emitter call)

strategies/common/alpha_evolve/
└── alpha_evolve_bridge.py      (T029 - add emitter call)
```

---

## Critical Imports

```python
# Actor + MessageBus (Tasks T020-T022)
from nautilus_trader.common.actor import Actor
from nautilus_trader.config import ActorConfig

# Events (Tasks T021-T022)
from nautilus_trader.model.events import (
    OrderFilled,
    OrderRejected,
    PositionOpened,
    PositionClosed,
)

# Data Models (All phases)
from pydantic import BaseModel, Field

# File I/O (Task T007)
import os

# Parquet/DuckDB (Phase 6)
import pyarrow.parquet as pq
import duckdb  # optional
```

---

## Known Discord Patterns

### OrderSpreadGuardActor (Reference)
Source: Discord #help, 2025-09-23
```python
from nautilus_trader.common.actor import Actor  
from nautilus_trader.config import ActorConfig  

class OrderSpreadGuardConfig(ActorConfig):  
    pass

class OrderSpreadGuardActor(Actor):  
    def __init__(self, config: OrderSpreadGuardConfig) -> None:
        super().__init__(config)
    
    # ... implementation
```

### MessageBus Subscription (Reference)
Source: Discord #help, 2025-09-23
```python
def on_start(self) -> None:
    self.msgbus.subscribe(topic="events.order.*", handler=self.on_order_event)  

def on_order_event(self, event: OrderEvent):  
    # Handle event
    pass
```

---

## Troubleshooting

### "AttributeError: module 'nautilus_trader' has no attribute 'Actor'"
- Verify nightly v1.222.0+: `python3 -c "import nautilus_trader; print(nautilus_trader.__version__)"`
- Use correct import: `from nautilus_trader.common.actor import Actor`

### "MessageBus handler not called"
- Remember: MessageBus executes handlers SYNCHRONOUSLY (not queued)
- Ensure topic pattern matches event type: `events.order.*` for OrderFilled

### "PositionOpened fired but I expected PositionClosed"
- This can happen with reconciliation (logged correctly by audit trail)
- Audit trail logs what actually happens - this is the point of auditing

### "O_APPEND write failed on Windows"
- Atomic appends may behave differently on Windows
- Target: Linux (as per project environment)

---

## Success Criteria Per Phase

**Phase 1**: Directories exist, __init__.py created
**Phase 2**: All unit tests pass, append-only enforced, checksums computed
**Phase 3**: Parameter changes logged with old/new values
**Phase 4**: Order fills logged, positions tracked, 0 lost events
**Phase 5**: Signals logged with value/regime/confidence
**Phase 6**: 1M event query completes in < 5 seconds
**Phase 7**: <1ms write latency p99, graceful degradation on disk full

---

**Start Date**: 2026-01-05
**Estimated Total Duration**: 14-18 hours
**Dependency Chain**: Phase 1 → Phase 2 → (Phases 3-6 in parallel) → Phase 7
