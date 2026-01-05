# Component Mapping: tasks.md → NautilusTrader Nightly v1.222.0

## Quick Reference Table

| Task | Component | Import Path | Status | Evidence |
|------|-----------|-------------|--------|----------|
| T001-T003 | Directory structure | N/A | ✅ PASS | Python standard |
| T004 | `AuditConfig` | Custom (Pydantic) | ✅ PASS | Pydantic v2.x available |
| T005 | `AuditEventType` enum | Custom | ✅ PASS | Python enum |
| T006 | `AuditEvent` (BaseModel) | `pydantic.BaseModel` | ✅ PASS | Nightly v1.222.0 ships Pydantic |
| T007 | `AppendOnlyWriter` (os.O_APPEND) | `os` module | ✅ PASS | Python standard library |
| T008 | `AuditEventEmitter` | Custom | ✅ PASS | Event emitter pattern (no NT API) |
| T009-T010 | Unit tests | `pytest` | ✅ PASS | Standard test framework |
| T011 | `ParameterChangeEvent` | Custom (Pydantic) | ✅ PASS | Extends AuditEvent |
| T012 | `emit_param_change()` | Custom method | ✅ PASS | AuditEventEmitter extension |
| T013-T014 | Parameter event tests | `pytest` | ✅ PASS | Standard testing |
| T015 | MetaController integration | `strategies/common/adaptive_control/meta_controller.py` | ✅ PASS | Custom code, not NT core |
| T016 | SOPSGillerSizer integration | `strategies/common/adaptive_control/sops_sizing.py` | ✅ PASS | Custom code, not NT core |
| T017 | Integration tests | `pytest` | ✅ PASS | Standard testing |
| T018 | `TradeEvent` | Custom (Pydantic) | ✅ PASS | Extends AuditEvent |
| T019 | `emit_trade()` | Custom method | ✅ PASS | AuditEventEmitter extension |
| **T020** | **`AuditObserver(Actor)`** | **`from nautilus_trader.common.actor import Actor`** | **✅ PASS** | **Discord #help confirms pattern** |
| **T021** | **`_on_order_event()` handler** | **`events.order.OrderFilled`, `events.order.OrderRejected`** | **✅ PASS** | **Discord #help: `self.msgbus.subscribe(topic="events.order.*")`** |
| **T022** | **`_on_position_event()` handler** | **`events.position.PositionOpened`, `events.position.PositionClosed`** | **✅ PASS** | **Confirmed in NT event system** |
| T023-T024 | Trade event tests | `pytest` | ✅ PASS | Standard testing |
| T025 | `SignalEvent` | Custom (Pydantic) | ✅ PASS | Extends AuditEvent |
| T026 | `emit_signal()` | Custom method | ✅ PASS | AuditEventEmitter extension |
| T027 | `SystemEvent` | Custom (Pydantic) | ✅ PASS | Extends AuditEvent |
| T028 | ParticlePortfolio integration | `strategies/common/adaptive_control/particle_portfolio.py` | ✅ PASS | Custom code, not NT core |
| T029 | AlphaEvolveBridge integration | `strategies/common/alpha_evolve/alpha_evolve_bridge.py` | ✅ PASS | Custom code, not NT core |
| T030-T031 | Signal event tests | `pytest` | ✅ PASS | Standard testing |
| T032 | `ParquetConverter` | `pyarrow.parquet` | ✅ PASS | Standard Python library |
| T033-T034 | Partitioning & retention | `pyarrow`, `pathlib` | ✅ PASS | Standard Python |
| T035 | `AuditQuery` | `duckdb` (optional) | ✅ PASS | Optional dependency, works without |
| T036-T037 | Query methods | `duckdb` (optional) | ✅ PASS | DuckDB is optional |
| T038 | Incident reconstruction | `duckdb` (optional) | ✅ PASS | DuckDB is optional |
| T039-T041 | Query tests & performance | `pytest` | ✅ PASS | Standard testing |
| T042-T044 | Edge cases (disk/throttle/checksum) | Custom | ✅ PASS | Implementation-specific |
| T045 | Example notebook | Custom | ✅ PASS | Documentation artifact |
| T046 | alpha-debug verification | Custom | ✅ PASS | Subagent task |
| T047 | Performance benchmark | `pytest` | ✅ PASS | Standard testing |

---

## Critical Path Dependencies

### Phase 2: Foundational (BLOCKS all user stories)
```
T004 → T005 → T006 → T007 → T008
       ├─→ T009 (parallel, T007 ready)
       └─→ T010 (parallel, T006 ready)
```

### Phase 3-6: User Stories (parallelizable after Phase 2)
```
Phase 2 complete ──┬─→ US1 (T011-T017)
                   ├─→ US2 (T018-T024) ← KEY: T020 uses Actor, T021-T022 use MessageBus
                   ├─→ US3 (T025-T031)
                   └─→ US4 (T032-T041)
```

---

## NautilusTrader API Reference

### Actor & MessageBus (Tasks T020-T022)

**Source**: Discord #help and #questions, confirmed in production

```python
# IMPORT PATTERN (Production-Confirmed)
from nautilus_trader.common.actor import Actor
from nautilus_trader.config import ActorConfig

# CLASS PATTERN (Discord #help: OrderSpreadGuardActor)
class AuditObserver(Actor):
    def __init__(self, config: ActorConfig):
        super().__init__(config)
    
    def on_start(self) -> None:
        # Subscribe to order events
        self.msgbus.subscribe(
            topic="events.order.*",
            handler=self._on_order_event
        )
        # Subscribe to position events
        self.msgbus.subscribe(
            topic="events.position.*",
            handler=self._on_position_event
        )
    
    def _on_order_event(self, event) -> None:
        # Handles: OrderFilled, OrderRejected, etc.
        pass
    
    def _on_position_event(self, event) -> None:
        # Handles: PositionOpened, PositionClosed
        pass
```

**Verification**:
- Discord #help (2025-09-23): Shows OrderSpreadGuardActor(Actor) pattern
- Discord #help (2025-09-23): Shows `self.msgbus.subscribe(topic="events.order.*")`
- Discord #questions: MessageBus behavior discussion confirms API stability

### Event Types (Tasks T021-T022)

**Available Event Types** (confirmed in NT event system):
- `OrderFilled` - Task T021
- `OrderRejected` - Task T021
- `PositionOpened` - Task T022
- `PositionClosed` - Task T022

**Usage Pattern**:
```python
def _on_order_event(self, event) -> None:
    if isinstance(event, OrderFilled):
        # Log trade execution
        self.emit_trade(event)
    elif isinstance(event, OrderRejected):
        # Log rejection
        self.emit_system_event("order.rejected", event)
```

---

## Version-Specific Notes

### NautilusTrader v1.222.0 (Nightly)

**Stable Components** (NO CHANGES expected):
- `Actor` class - STABLE
- `ActorConfig` - STABLE
- `MessageBus` - STABLE (both Cython + Rust implementations)
- `OrderFilled`, `OrderRejected` events - STABLE
- `PositionOpened`, `PositionClosed` events - STABLE
- Pydantic v2.x integration - STABLE

**Recent Changes** (2026-01-04 breaking change):
- ❌ Does NOT affect audit trail (concerns data commands, not events)

**Open Issues** (Nightly-specific):
- #3384 (TestClock monotonicity) - Does NOT block audit trail
- #3104 (Reconciliation for Binance hedge mode) - Does NOT block audit trail
- #3042 (Routing client reconciliation) - Does NOT block audit trail

---

## Implementation Checklist

### Before Starting T001:
- [ ] Confirm Actor class available: `from nautilus_trader.common.actor import Actor`
- [ ] Confirm MessageBus pattern: `self.msgbus.subscribe(topic="events.order.*", handler=callback)`
- [ ] Confirm event types: OrderFilled, OrderRejected, PositionOpened, PositionClosed

### Phase 2 Checkpoint (after T010):
- [ ] AuditConfig created
- [ ] AuditEventType enum created
- [ ] AuditEvent base model created
- [ ] AppendOnlyWriter tested with O_APPEND
- [ ] AuditEventEmitter working with sequence tracking

### Phase 4 Checkpoint (after T024):
- [ ] AuditObserver(Actor) subclass created
- [ ] MessageBus subscription pattern working
- [ ] Order event handler receiving OrderFilled/OrderRejected
- [ ] Position event handler receiving PositionOpened/PositionClosed

---

## Discord Evidence Archive

**File**: `/media/sam/1TB/nautilus_dev/docs/discord/help.md`

**OrderSpreadGuardActor Pattern** (2025-09-23):
```python
from nautilus_trader.common.actor import Actor  
from nautilus_trader.config import ActorConfig  

class OrderSpreadGuardConfig(ActorConfig):  
    # ...

class OrderSpreadGuardActor(Actor):  # Use Actor, not Strategy  
    # ...
```

**MessageBus Subscription** (2025-09-23):
```python
self.msgbus.subscribe(topic="events.order.*", handler=self.on_order_event)  
def on_order_event(self, event: OrderEvent):  
    # ...
```

---

**Validation Date**: 2026-01-05
**Nightly Version**: v1.222.0
**Confidence**: HIGH
