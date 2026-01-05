# Research Summary: Audit Trail for Algorithmic Trading

**Feature**: 030-audit-trail
**Date**: 2026-01-05
**Status**: Complete

---

## Executive Summary

This research analyzed state-of-the-art audit trail systems for algorithmic trading, with focus on:
- Immutable logging architectures (append-only)
- Low-latency logging (<1ms per event)
- Post-mortem forensics and analysis
- Industry standards and regulatory requirements

**Key Finding**: The trading industry is converging on cryptographically-verifiable, append-only audit trails as the standard. The VeritasChain Protocol (VCP) v1.1 represents the emerging industry standard with three-layer integrity (Event, Collection, External).

---

## Industry Context: Why This Matters

### Recent Trading Disasters (2025)

Three major algorithmic trading incidents in 2025 shared a common root cause: **audit logs that could be modified by the systems they were supposed to audit**.

| Incident | Impact | Root Cause |
|----------|--------|------------|
| Two Sigma Fraud | $165M | Parameter manipulation undetected for 2 years |
| Knight Capital | $440M in 45 min | No audit trail for debugging |
| Jane Street/SEBI | Months to investigate | Logs not correlated across markets |

### Regulatory Pressure

- **MiFID III**: Requires microsecond-precise audit trails
- **EU AI Act (Article 12)**: Mandates automatic logging for high-risk AI systems by August 2026
- **CAT (Consolidated Audit Trail)**: US requirement for cross-market event correlation

---

## Architecture Patterns

### 1. Write-Ahead Log (WAL) Pattern

The foundational pattern for immutable audit trails. Used by Kafka, PostgreSQL, and most financial systems.

**Core Principle**: Before applying any changes, write to append-only log first.

```
Signal → Log Entry → State Change → Confirmation
        │
        └── (immutable record)
```

**Performance Characteristics**:
- Sequential writes: 100-1000x faster than random writes
- WAL leverages sequential I/O for sub-millisecond latency
- Checkpointing amortizes cost over many writes

**Source**: [Martin Fowler - Write-Ahead Log](https://martinfowler.com/articles/patterns-of-distributed-systems/write-ahead-log.html)

### 2. Three-Layer Integrity Model (VCP v1.1)

The VeritasChain Protocol v1.1 structures integrity into three layers:

| Layer | Purpose | Mechanism |
|-------|---------|-----------|
| Layer 1 (Event) | Individual event immutability | EventHash (SHA-256) |
| Layer 2 (Collection) | Batch completeness | RFC 6962 Merkle Trees |
| Layer 3 (External) | Third-party verification | Digital signatures + timestamps |

**Key Innovation**: Layer 2 provides **completeness guarantees** - verifies no events were selectively omitted.

**Source**: [VCP v1.1 Architecture](https://dev.to/veritaschain/noahs-ark-for-algorithmic-trading-why-vcp-v11-requires-a-three-layer-architecture-2dhk)

### 3. Append-Only Storage Options

| Technology | Write Latency | Query Speed | Use Case |
|------------|---------------|-------------|----------|
| **JSON Lines** | <1ms | Slow (sequential) | Human-readable, debugging |
| **Parquet** | 5-10ms (batched) | 10-100x faster | Analytics, long-term storage |
| **immudb** | 10-13ms | 5-10ms | Cryptographic verification |
| **Kafka** | <1ms | N/A (streaming) | Real-time distribution |

**Recommendation**: JSON Lines for hot path (sub-ms), batch convert to Parquet for analysis.

**Source**: [Comparing Data Formats for Log Analytics](https://joshua-robinson.medium.com/comparing-data-formats-for-log-analytics-2202c146c0cc)

---

## Performance Benchmarks

### immudb (Append-Only Database)

| Operation | Latency | Notes |
|-----------|---------|-------|
| ExecAll (batch write) | 10-13ms | Default sync mode |
| GetAll (batch read) | 5-10ms | With index |
| Async write (noWait) | <1ms | Best for trading |
| Connection + session | 50-62ms | One-time cost |

**Key Insight**: Use `noWait` mode for trading path, sync mode for critical events.

**Source**: [immudb Performance Guide](https://docs.immudb.io/master/production/performance-guide.html)

### JSON Lines vs Parquet

| Metric | JSON Lines | Parquet |
|--------|------------|---------|
| Storage size | 1x | 0.25x (4x smaller) |
| Write latency | <1ms (append) | 5-10ms (batch) |
| Query (1M rows) | 10+ seconds | <1 second |
| Human readable | Yes | No |

**Recommendation**: Hot path uses JSON Lines; cold path (hourly) converts to Parquet.

**Source**: [Pure Storage - Comparing Data Formats](https://blog.purestorage.com/purely-technical/comparing-data-formats-for-log-analytics/)

---

## Existing Codebase Patterns

Our codebase already has event-driven patterns in `strategies/common/recovery/`:

### RecoveryEventEmitter Pattern

```python
# From strategies/common/recovery/event_emitter.py
class RecoveryEventEmitter:
    def _emit(self, event: BaseModel) -> None:
        # Log the event as JSON for structured logging
        self._log.info("Recovery event: %s", event.model_dump_json())
        
        # Invoke callback if registered
        if self._on_event is not None:
            self._on_event(event)
```

**Reusable**: This pattern extends directly to AuditEventEmitter.

### Pydantic Event Schemas

```python
# From strategies/common/recovery/events.py
class PositionLoadedEvent(BaseModel):
    event_type: str = RecoveryEventType.POSITION_LOADED
    trader_id: str = Field(description="Trader identifier")
    ts_event: int = Field(description="Event timestamp (nanoseconds)")
    instrument_id: str = Field(description="Position instrument")
    # ...
```

**Reusable**: Pydantic models provide validation + JSON serialization.

---

## Integration Points Analysis

### 1. meta_controller.py - State Transitions

**Events to Log**:
- `SystemState` changes (VENTRAL, SYMPATHETIC, DORSAL)
- `MarketHarmony` changes (CONSONANT, DISSONANT, RESOLVING)
- `risk_multiplier` updates
- `strategy_weights` changes

**Integration Point**: `MetaController.update()` method (line ~223)

### 2. particle_portfolio.py - Weight Changes

**Events to Log**:
- Particle resampling events
- Strategy weight consensus updates
- ESS (Effective Sample Size) drops

**Integration Point**: `ParticlePortfolio.update()` method (line ~121)

### 3. sops_sizing.py - Size Calculations

**Events to Log**:
- Adaptive k parameter changes
- Tape speed regime changes (fast/normal/slow)
- Final position size calculations

**Integration Point**: `SOPSGillerSizer.size()` and `.update()` methods

### 4. alpha_evolve_bridge.py - Evolution Triggers

**Events to Log**:
- `EvolutionRequest` creation
- Trigger reasons (DISSONANCE, DRAWDOWN, STAGNATION)
- Underperforming strategy identification

**Integration Point**: `AlphaEvolveBridge.check_and_trigger()` method (line ~135)

---

## Recommended Architecture

### Two-Tier Storage

```
┌─────────────────────────────────────────────────┐
│              Trading System                      │
│  ┌─────────────┐    ┌──────────────────────────┐│
│  │ AuditEmitter│───►│ JSON Lines (append-only) ││
│  └─────────────┘    └───────────┬──────────────┘│
│                                 │ hourly        │
│                                 ▼               │
│                    ┌──────────────────────────┐ │
│                    │ Parquet (partitioned)   │ │
│                    └──────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

### Event Schema (Unified)

```python
class AuditEvent(BaseModel):
    """Base audit event with common fields."""
    ts_event: int           # Nanoseconds (matches NautilusTrader)
    event_type: str         # Hierarchical: "param.change", "trade.exec"
    source: str             # Component: "meta_controller", "sops_sizer"
    trader_id: str          # For multi-trader systems
    sequence: int           # Monotonic sequence number
    checksum: str           # SHA-256 of payload (Layer 1 integrity)
    
    # Polymorphic payload based on event_type
    payload: dict           # Type-specific data
```

### Append-Only Enforcement

```python
class AppendOnlyWriter:
    """Enforces append-only semantics."""
    
    def __init__(self, path: Path):
        self._fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT)
        self._sequence = 0
    
    def write(self, event: AuditEvent) -> None:
        event.sequence = self._sequence
        self._sequence += 1
        line = event.model_dump_json() + "\n"
        os.write(self._fd, line.encode())
        # Note: No fsync by default for <1ms latency
```

---

## Key Decisions Required

### 1. Sync vs Async Writes

| Mode | Latency | Durability | Use Case |
|------|---------|------------|----------|
| **Async (no fsync)** | <1ms | May lose last ~1s on crash | Signal/weight changes |
| **Sync (fsync every N)** | 1-5ms | N events buffer | Trade executions |
| **Sync (fsync every)** | 5-10ms | Full durability | Critical events |

**Recommendation**: Async by default, sync for trade executions.

### 2. Checksum Strategy

| Option | Performance | Security |
|--------|-------------|----------|
| **None** | Best | None |
| **SHA-256 per event** | Good (<100us) | Tamper detection |
| **Merkle tree batches** | Medium | Completeness proof |

**Recommendation**: SHA-256 per event (Layer 1), Merkle tree optional (Layer 2).

### 3. Retention Policy

| Tier | Retention | Format | Query Speed |
|------|-----------|--------|-------------|
| Hot | 7 days | JSON Lines | Real-time |
| Warm | 90 days | Parquet | Seconds |
| Cold | 1 year | Parquet (compressed) | Minutes |

**Recommendation**: 90-day warm tier matches spec assumption.

---

## Sources

1. [VCP v1.1 - Three-Layer Architecture](https://dev.to/veritaschain/noahs-ark-for-algorithmic-trading-why-vcp-v11-requires-a-three-layer-architecture-2dhk)
2. [VCP - Cryptographic Audit Protocol](https://aijourn.com/vso-unveils-vcp-v1-0-a-first-of-its-kind-cryptographic-audit-protocol-to-restore-trust-in-ai-driven-markets/)
3. [Martin Fowler - Write-Ahead Log](https://martinfowler.com/articles/patterns-of-distributed-systems/write-ahead-log.html)
4. [LinkedIn - The Log: Unifying Abstraction](https://engineering.linkedin.com/distributed-systems/log-what-every-software-engineer-should-know-about-real-time-datas-unifying)
5. [immudb Performance Guide](https://docs.immudb.io/master/production/performance-guide.html)
6. [Comparing Data Formats for Log Analytics](https://joshua-robinson.medium.com/comparing-data-formats-for-log-analytics-2202c146c0cc)
7. [QuestDB - Append-Only Log](https://questdb.com/glossary/append-only-log/)
8. [Log Forensics Best Practices](https://www.salvationdata.com/work-tips/log-forensics-5-tips-for-investigators/)

---

## Conclusion

The audit trail implementation should:

1. **Use JSON Lines for hot path** (<1ms writes)
2. **Batch convert to Parquet** for analysis
3. **Implement SHA-256 checksums** per event (Layer 1)
4. **Extend existing Pydantic event pattern** from recovery module
5. **Target <1ms p99 latency** using async writes
6. **Provide time-range queries** via Parquet partitioning
