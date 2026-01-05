# Implementation Plan: Audit Trail System

**Feature Branch**: `030-audit-trail`
**Created**: 2026-01-05
**Status**: Draft
**Spec Reference**: `specs/030-audit-trail/spec.md`
**Research Reference**: `specs/030-audit-trail/research.md`

---

## Technical Context

| Item | Value | Status |
|------|-------|--------|
| NautilusTrader Version | Nightly (1.222.0+) | Verified |
| Storage Format (Hot) | JSON Lines (append-only) | Selected |
| Storage Format (Cold) | Parquet (partitioned by day) | Selected |
| Target Latency | <1ms p99 per event | Requirement |
| Existing Pattern | RecoveryEventEmitter | Reusable |

---

## Constitution Check

| Principle | Compliance | Notes |
|-----------|------------|-------|
| Black Box Design | PASS | AuditEmitter is self-contained module |
| KISS & YAGNI | PASS | JSON Lines for MVP, Parquet optional |
| Native First | PASS | Uses Python stdlib + Pydantic (existing) |
| Performance | PASS | Async writes, <1ms target |
| Adaptive Signals, Fixed Safety | N/A | Audit trail is observability layer |

---

## Architecture Overview

### System Context

```
┌─────────────────────────────────────────────────────────────┐
│                    Trading System                            │
│  ┌─────────────────┐  ┌──────────────────────────────────┐  │
│  │ MetaController  │  │        AuditTrail                 │  │
│  │ ParticlePortfolio├─►│  ┌─────────────┐  ┌───────────┐ │  │
│  │ SOPSGillerSizer │  │  │AuditEmitter │─►│JSONLWriter│ │  │
│  │ AlphaEvolveBridge│  │  └─────────────┘  └─────┬─────┘ │  │
│  └─────────────────┘  │                          │       │  │
│                       │                 hourly   │       │  │
│                       │                          ▼       │  │
│                       │            ┌───────────────────┐ │  │
│                       │            │ ParquetConverter  │ │  │
│                       │            └───────────────────┘ │  │
│                       └──────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Component Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                       Data Flow                               │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│   Component Event                                             │
│        │                                                      │
│        ▼                                                      │
│   ┌───────────────┐                                           │
│   │ AuditEmitter  │ ──► Validate + checksum                   │
│   └───────┬───────┘                                           │
│           │ event.model_dump_json()                           │
│           ▼                                                   │
│   ┌───────────────┐                                           │
│   │ JSONLWriter   │ ──► Append-only, O_APPEND flag            │
│   │ (async/sync)  │                                           │
│   └───────┬───────┘                                           │
│           │ daily rotation                                    │
│           ▼                                                   │
│   ┌───────────────┐      ┌─────────────────────┐              │
│   │ audit_YYYYMMDD│ ───► │ ParquetConverter    │              │
│   │ .jsonl        │      │ (hourly background) │              │
│   └───────────────┘      └──────────┬──────────┘              │
│                                     │                         │
│                                     ▼                         │
│                          ┌─────────────────────┐              │
│                          │ audit/year=YYYY/    │              │
│                          │   month=MM/day=DD/  │              │
│                          │   events.parquet    │              │
│                          └─────────────────────┘              │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## Technical Decisions

### Decision 1: Storage Format

**Options Considered**:
1. **JSON Lines (JSONL)**
   - Pros: <1ms append, human-readable, Python stdlib
   - Cons: Slow queries on large files
2. **Parquet Direct**
   - Pros: Fast queries, columnar compression
   - Cons: 5-10ms write latency (batching required)
3. **immudb**
   - Pros: Cryptographic verification built-in
   - Cons: External dependency, 10-13ms latency
4. **SQLite WAL**
   - Pros: SQL queries, single file
   - Cons: Write latency ~2-5ms

**Selected**: JSON Lines (hot) + Parquet (cold)

**Rationale**: JSONL provides <1ms writes for trading path. Parquet conversion in background provides fast queries for analysis. No external dependencies.

---

### Decision 2: Append-Only Enforcement

**Options Considered**:
1. **O_APPEND flag**
   - Pros: OS-level guarantee, simple
   - Cons: Can still delete file
2. **File permissions (immutable)**
   - Pros: Stronger protection
   - Cons: Complex rotation
3. **Cryptographic chaining**
   - Pros: Tamper detection
   - Cons: Performance overhead

**Selected**: O_APPEND + SHA-256 checksums

**Rationale**: O_APPEND prevents overwrites. SHA-256 per event detects tampering. Balance of security and performance.

---

### Decision 3: Sync vs Async Writes

**Options Considered**:
1. **Fully Async (no fsync)**
   - Pros: <1ms latency
   - Cons: May lose ~1s of data on crash
2. **Sync every N events**
   - Pros: Bounded data loss
   - Cons: Variable latency
3. **Sync every event**
   - Pros: Maximum durability
   - Cons: 5-10ms latency

**Selected**: Async default, configurable sync for trades

**Rationale**: Parameter changes and signals can tolerate ~1s loss. Trade executions sync every event for audit compliance.

---

### Decision 4: Query Interface

**Options Considered**:
1. **DuckDB on Parquet**
   - Pros: SQL, fast columnar queries
   - Cons: Requires DuckDB dependency
2. **Pandas on Parquet**
   - Pros: Familiar, existing dependency
   - Cons: Memory-bound for large files
3. **Custom iterator**
   - Pros: No dependencies
   - Cons: Limited query capabilities

**Selected**: DuckDB on Parquet

**Rationale**: DuckDB provides <5s queries on 1M+ events, SQL for forensics. Already compatible with ParquetDataCatalog pattern.

---

## Implementation Strategy

### Phase 1: Core Audit Trail (MVP)

**Goal**: Append-only JSON Lines logging with Pydantic schemas

**Deliverables**:
- [ ] `strategies/common/audit/events.py` - Pydantic event schemas
- [ ] `strategies/common/audit/emitter.py` - AuditEventEmitter class
- [ ] `strategies/common/audit/writer.py` - AppendOnlyWriter class
- [ ] Unit tests for all components

**Duration**: 4 hours

**Dependencies**: None (uses existing patterns)

---

### Phase 2: Component Integration

**Goal**: Integrate with meta_controller, particle_portfolio, sops_sizing, alpha_evolve_bridge

**Deliverables**:
- [ ] MetaController integration (state transitions, weights)
- [ ] ParticlePortfolio integration (resampling, consensus)
- [ ] SOPSGillerSizer integration (k changes, tape regime)
- [ ] AlphaEvolveBridge integration (evolution triggers)
- [ ] Integration tests

**Duration**: 4 hours

**Dependencies**: Phase 1

---

### Phase 3: Parquet Conversion

**Goal**: Background job to convert JSONL to partitioned Parquet

**Deliverables**:
- [ ] `strategies/common/audit/converter.py` - ParquetConverter class
- [ ] Hourly rotation script
- [ ] Retention policy (90 days default)

**Duration**: 2 hours

**Dependencies**: Phase 1

---

### Phase 4: Query Interface

**Goal**: Fast queries on audit trail for post-mortem analysis

**Deliverables**:
- [ ] `strategies/common/audit/query.py` - AuditQuery class
- [ ] Time-range queries
- [ ] Event-type filtering
- [ ] Source filtering
- [ ] Example forensics notebook

**Duration**: 2 hours

**Dependencies**: Phase 3

---

## File Structure

```
strategies/common/audit/
├── __init__.py
├── events.py            # Pydantic event schemas
├── emitter.py           # AuditEventEmitter
├── writer.py            # AppendOnlyWriter
├── converter.py         # JSONL → Parquet converter
├── query.py             # AuditQuery (DuckDB-based)
└── config.py            # AuditConfig dataclass

tests/
├── unit/
│   └── audit/
│       ├── test_events.py
│       ├── test_emitter.py
│       ├── test_writer.py
│       └── test_query.py
└── integration/
    └── test_audit_integration.py

data/
└── audit/               # Runtime data (not in git)
    ├── hot/             # JSON Lines (7 days)
    │   └── audit_20260105.jsonl
    └── cold/            # Parquet (90 days)
        └── year=2026/month=01/day=05/events.parquet
```

---

## API Design

### Event Schemas

```python
# strategies/common/audit/events.py
from enum import Enum
from pydantic import BaseModel, Field
import hashlib
import time

class AuditEventType(str, Enum):
    """Hierarchical event types."""
    # Parameter changes
    PARAM_STATE_CHANGE = "param.state_change"
    PARAM_WEIGHT_CHANGE = "param.weight_change"
    PARAM_K_CHANGE = "param.k_change"
    PARAM_RISK_CHANGE = "param.risk_change"
    
    # Trading events
    TRADE_SIGNAL = "trade.signal"
    TRADE_ORDER = "trade.order"
    TRADE_FILL = "trade.fill"
    
    # System events
    SYS_EVOLUTION_TRIGGER = "sys.evolution_trigger"
    SYS_REGIME_CHANGE = "sys.regime_change"
    SYS_RESAMPLING = "sys.resampling"

class AuditEvent(BaseModel):
    """Base audit event with common fields."""
    ts_event: int = Field(
        default_factory=lambda: int(time.time_ns()),
        description="Event timestamp in nanoseconds"
    )
    event_type: AuditEventType
    source: str = Field(description="Component source")
    trader_id: str = Field(default="TRADER-001")
    sequence: int = Field(default=0)
    
    # Computed checksum (Layer 1 integrity)
    @property
    def checksum(self) -> str:
        payload = self.model_dump_json(exclude={"checksum"})
        return hashlib.sha256(payload.encode()).hexdigest()[:16]

class ParameterChangeEvent(AuditEvent):
    """Parameter change event."""
    event_type: AuditEventType = AuditEventType.PARAM_STATE_CHANGE
    param_name: str
    old_value: str  # Serialized as string for consistency
    new_value: str
    trigger_reason: str

class TradeEvent(AuditEvent):
    """Trade execution event."""
    event_type: AuditEventType = AuditEventType.TRADE_FILL
    order_id: str
    instrument_id: str
    side: str  # BUY/SELL
    size: str  # String for precision
    price: str
    slippage_bps: float
    realized_pnl: str
    strategy_source: str

class SignalEvent(AuditEvent):
    """Signal generation event."""
    event_type: AuditEventType = AuditEventType.TRADE_SIGNAL
    signal_value: float
    regime: str
    confidence: float
    strategy_source: str
```

### Audit Emitter

```python
# strategies/common/audit/emitter.py
from typing import Callable, Optional
from pydantic import BaseModel
import logging

class AuditEventEmitter:
    """Emitter for audit events (extends RecoveryEventEmitter pattern)."""
    
    def __init__(
        self,
        trader_id: str,
        writer: "AppendOnlyWriter",
        logger: Optional[logging.Logger] = None,
        on_event: Optional[Callable[[BaseModel], None]] = None,
    ):
        self._trader_id = trader_id
        self._writer = writer
        self._log = logger or logging.getLogger(__name__)
        self._on_event = on_event
        self._sequence = 0
    
    def emit(self, event: AuditEvent) -> AuditEvent:
        """Emit an audit event."""
        event.trader_id = self._trader_id
        event.sequence = self._sequence
        self._sequence += 1
        
        # Write to append-only log
        self._writer.write(event)
        
        # Log for observability
        self._log.debug("Audit: %s", event.event_type.value)
        
        # Callback for testing/integration
        if self._on_event:
            self._on_event(event)
        
        return event
    
    def emit_param_change(
        self,
        param_name: str,
        old_value: any,
        new_value: any,
        trigger_reason: str,
        source: str,
    ) -> ParameterChangeEvent:
        """Convenience method for parameter changes."""
        event = ParameterChangeEvent(
            source=source,
            param_name=param_name,
            old_value=str(old_value),
            new_value=str(new_value),
            trigger_reason=trigger_reason,
        )
        return self.emit(event)
```

### Append-Only Writer

```python
# strategies/common/audit/writer.py
from pathlib import Path
from pydantic import BaseModel
import os
import threading
from datetime import datetime

class AppendOnlyWriter:
    """Thread-safe append-only JSON Lines writer."""
    
    def __init__(
        self,
        base_path: Path,
        sync_writes: bool = False,
        rotate_daily: bool = True,
    ):
        self._base_path = Path(base_path)
        self._base_path.mkdir(parents=True, exist_ok=True)
        self._sync_writes = sync_writes
        self._rotate_daily = rotate_daily
        self._lock = threading.Lock()
        self._fd: Optional[int] = None
        self._current_date: Optional[str] = None
    
    def _get_filename(self) -> Path:
        """Get current filename (rotates daily)."""
        if self._rotate_daily:
            date_str = datetime.utcnow().strftime("%Y%m%d")
            return self._base_path / f"audit_{date_str}.jsonl"
        return self._base_path / "audit.jsonl"
    
    def _ensure_file(self) -> int:
        """Ensure file is open, handle rotation."""
        today = datetime.utcnow().strftime("%Y%m%d")
        
        if self._fd is None or (self._rotate_daily and self._current_date != today):
            if self._fd is not None:
                os.close(self._fd)
            
            path = self._get_filename()
            # O_APPEND ensures atomic appends (kernel guarantees)
            self._fd = os.open(
                str(path),
                os.O_WRONLY | os.O_APPEND | os.O_CREAT,
                0o644
            )
            self._current_date = today
        
        return self._fd
    
    def write(self, event: BaseModel) -> None:
        """Write event to append-only log."""
        line = event.model_dump_json() + "\n"
        data = line.encode("utf-8")
        
        with self._lock:
            fd = self._ensure_file()
            os.write(fd, data)
            
            if self._sync_writes:
                os.fsync(fd)
    
    def close(self) -> None:
        """Close the file descriptor."""
        with self._lock:
            if self._fd is not None:
                os.close(self._fd)
                self._fd = None
```

### Query Interface

```python
# strategies/common/audit/query.py
from pathlib import Path
from datetime import datetime
from typing import Optional, List
import duckdb

class AuditQuery:
    """Query interface for audit trail (DuckDB on Parquet)."""
    
    def __init__(self, parquet_path: Path):
        self._path = Path(parquet_path)
        self._conn = duckdb.connect(":memory:")
    
    def query_time_range(
        self,
        start: datetime,
        end: datetime,
        event_type: Optional[str] = None,
        source: Optional[str] = None,
    ) -> List[dict]:
        """Query events in time range."""
        start_ns = int(start.timestamp() * 1e9)
        end_ns = int(end.timestamp() * 1e9)
        
        # Build query
        where_clauses = [
            f"ts_event >= {start_ns}",
            f"ts_event <= {end_ns}",
        ]
        if event_type:
            where_clauses.append(f"event_type = '{event_type}'")
        if source:
            where_clauses.append(f"source = '{source}'")
        
        where = " AND ".join(where_clauses)
        
        # Query partitioned Parquet
        query = f"""
            SELECT *
            FROM read_parquet('{self._path}/**/*.parquet')
            WHERE {where}
            ORDER BY ts_event ASC
        """
        
        result = self._conn.execute(query).fetchall()
        columns = [desc[0] for desc in self._conn.description]
        
        return [dict(zip(columns, row)) for row in result]
    
    def count_by_type(self, start: datetime, end: datetime) -> dict:
        """Count events by type in time range."""
        start_ns = int(start.timestamp() * 1e9)
        end_ns = int(end.timestamp() * 1e9)
        
        query = f"""
            SELECT event_type, COUNT(*) as count
            FROM read_parquet('{self._path}/**/*.parquet')
            WHERE ts_event >= {start_ns} AND ts_event <= {end_ns}
            GROUP BY event_type
            ORDER BY count DESC
        """
        
        result = self._conn.execute(query).fetchall()
        return {row[0]: row[1] for row in result}
```

---

## Integration Examples

### MetaController Integration

```python
# In meta_controller.py update() method

def update(self, ...) -> MetaState:
    # ... existing code ...
    
    # Audit: State transition
    if new_state != self._current_state:
        self._audit.emit_param_change(
            param_name="system_state",
            old_value=self._current_state.value,
            new_value=new_state.value,
            trigger_reason=f"health_score={health_metrics.score:.1f}",
            source="meta_controller",
        )
        self._current_state = new_state
    
    # Audit: Risk multiplier change (only if significant)
    if abs(risk_multiplier - self._last_risk_mult) > 0.01:
        self._audit.emit_param_change(
            param_name="risk_multiplier",
            old_value=self._last_risk_mult,
            new_value=risk_multiplier,
            trigger_reason=f"drawdown={drawdown*100:.1f}%",
            source="meta_controller",
        )
        self._last_risk_mult = risk_multiplier
    
    return state
```

### SOPSGillerSizer Integration

```python
# In sops_sizing.py

def update(self, return_value: float, timestamp: float = None, ...) -> None:
    old_k = self._sops.k
    self._sops.update_volatility(return_value)
    new_k = self._sops.k
    
    # Audit: k parameter change (only if significant)
    if abs(new_k - old_k) > 0.01:
        self._audit.emit_param_change(
            param_name="adaptive_k",
            old_value=old_k,
            new_value=new_k,
            trigger_reason=f"vol={self._sops.volatility:.4f}",
            source="sops_sizer",
        )
```

---

## Testing Strategy

### Unit Tests

- [ ] Event schema validation (required fields, types)
- [ ] Checksum computation consistency
- [ ] AppendOnlyWriter: verify O_APPEND behavior
- [ ] AppendOnlyWriter: daily rotation
- [ ] Query time-range filtering
- [ ] Query event-type filtering

### Integration Tests

- [ ] Full flow: emit → write → convert → query
- [ ] Concurrent writes from multiple threads
- [ ] Large file handling (1M events)
- [ ] Recovery after crash (partial writes)

### Performance Tests

- [ ] Write latency < 1ms (p99, async mode)
- [ ] Write latency < 5ms (p99, sync mode)
- [ ] Query 1M events in < 5 seconds
- [ ] Memory usage < 100MB for emitter

---

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Disk full | High | Low | Monitor disk space, retention policy |
| Corrupt file | Medium | Very Low | Checksum validation, daily rotation |
| High event rate | Medium | Medium | Batching, async writes |
| Late integration | Low | Medium | Phase 2 separate from Phase 1 |

---

## Dependencies

### External Dependencies
- `pydantic` (existing)
- `duckdb` (new, optional for queries)

### Internal Dependencies
- `strategies/common/recovery/events.py` (pattern reference)
- Integration points: meta_controller, particle_portfolio, sops_sizing, alpha_evolve_bridge

---

## Acceptance Criteria

### Phase 1 (MVP)
- [ ] AuditEvent schemas validated
- [ ] AppendOnlyWriter verified (O_APPEND)
- [ ] Write latency < 1ms (async mode)
- [ ] Daily rotation working
- [ ] Unit tests pass

### Phase 2 (Integration)
- [ ] MetaController emits state changes
- [ ] SOPSGillerSizer emits k changes
- [ ] AlphaEvolveBridge emits triggers
- [ ] Integration tests pass

### Phase 3 (Analysis)
- [ ] Parquet conversion working
- [ ] Query returns results < 5 seconds
- [ ] 90-day retention enforced

---

## Generated Artifacts

| Artifact | Path | Status |
|----------|------|--------|
| Specification | `specs/030-audit-trail/spec.md` | Complete |
| Research | `specs/030-audit-trail/research.md` | Complete |
| Plan | `specs/030-audit-trail/plan.md` | Complete |
| Events Schema | `strategies/common/audit/events.py` | Pending |
| Emitter | `strategies/common/audit/emitter.py` | Pending |
| Writer | `strategies/common/audit/writer.py` | Pending |
| Tests | `tests/unit/audit/` | Pending |

---

## Estimated Effort

| Phase | Duration | Complexity |
|-------|----------|------------|
| Phase 1: Core | 4 hours | Medium |
| Phase 2: Integration | 4 hours | Medium |
| Phase 3: Parquet | 2 hours | Low |
| Phase 4: Query | 2 hours | Low |
| **Total** | **12 hours** | Medium |
