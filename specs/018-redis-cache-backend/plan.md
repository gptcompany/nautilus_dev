# Implementation Plan: Redis Cache Backend

**Feature Branch**: `018-redis-cache-backend`
**Created**: 2025-12-30
**Status**: Complete
**Spec Reference**: `specs/018-redis-cache-backend/spec.md`

---

## Technical Context

| Item | Value | Status |
|------|-------|--------|
| Redis Version | 7.x | ✅ Verified |
| Persistence | AOF (appendonly) | ✅ Documented |
| Encoding | msgpack | ✅ Documented |
| Key Pattern | trader-{type}:{id} | ✅ Documented |

---

## Constitution Check

| Principle | Compliance | Notes |
|-----------|------------|-------|
| Black Box Design | ✅ PASS | Uses native CacheConfig |
| KISS & YAGNI | ✅ PASS | Standard Redis, no custom extensions |
| Native First | ✅ PASS | NautilusTrader native cache backend |
| Performance | ✅ PASS | Sub-ms latency, buffered writes |

---

## Architecture Overview

### System Context

```
┌─────────────────────────────────────────────┐
│              TradingNode                    │
│  ┌─────────────┐    ┌─────────────────────┐│
│  │ CacheConfig │───►│ CacheDatabaseAdapter││
│  └─────────────┘    └──────────┬──────────┘│
└────────────────────────────────┼────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │      Redis 7.x         │
                    │  ┌─────────────────┐   │
                    │  │ AOF Persistence │   │
                    │  └─────────────────┘   │
                    └────────────────────────┘
```

### Component Diagram

```
┌──────────────────────────────────────────────────┐
│                    Data Flow                      │
├──────────────────────────────────────────────────┤
│                                                   │
│   Strategy/Engine                                 │
│        │                                          │
│        ▼                                          │
│   ┌─────────────┐                                 │
│   │    Cache    │ ──► positions, orders, accounts │
│   │   (Memory)  │                                 │
│   └──────┬──────┘                                 │
│          │ buffer_interval_ms=100                 │
│          ▼                                        │
│   ┌─────────────┐                                 │
│   │   Buffer    │ ──► Batch writes                │
│   └──────┬──────┘                                 │
│          │ msgpack serialize                      │
│          ▼                                        │
│   ┌─────────────┐                                 │
│   │   Redis     │ ──► Persistent storage          │
│   └─────────────┘                                 │
│                                                   │
└──────────────────────────────────────────────────┘
```

---

## Technical Decisions

### Decision 1: Persistence Mode

**Options Considered**:
1. **AOF (Append Only File)**
   - Pros: Durable, configurable fsync, human-readable
   - Cons: Larger files, slower startup with big AOF
2. **RDB (Snapshot)**
   - Pros: Compact, fast startup
   - Cons: Potential data loss between snapshots
3. **AOF + RDB (Hybrid)**
   - Pros: Best of both
   - Cons: More disk usage

**Selected**: AOF

**Rationale**: Trading state must not be lost. AOF with `appendfsync everysec` provides durability with minimal performance impact.

---

### Decision 2: Serialization Format

**Options Considered**:
1. **msgpack**
   - Pros: 30-50% smaller than JSON, faster, binary
   - Cons: Not human-readable
2. **JSON**
   - Pros: Human-readable, debuggable
   - Cons: Larger, slower

**Selected**: msgpack

**Rationale**: Performance is critical for live trading. Use JSON only for debugging.

---

### Decision 3: High Availability

**Options Considered**:
1. **Single Instance**
   - Pros: Simple, no complexity
   - Cons: Single point of failure
2. **Redis Sentinel**
   - Pros: Automatic failover, native support
   - Cons: 3+ nodes required
3. **Redis Cluster**
   - Pros: Horizontal scaling
   - Cons: Overkill for trading state size

**Selected**: Single Instance (dev), Sentinel (prod)

**Rationale**: Trading state is small (< 1GB). Sentinel provides HA without cluster complexity.

---

## Implementation Strategy

### Phase 1: Docker Setup

**Goal**: Redis running locally with AOF persistence

**Deliverables**:
- [x] `docker-compose.redis.yml` - Redis service definition
- [x] Health check configuration
- [x] Volume for data persistence

**Dependencies**: Docker installed

---

### Phase 2: NautilusTrader Configuration

**Goal**: CacheConfig validated and working

**Deliverables**:
- [x] `config/cache/redis_config.py` - Production CacheConfig
- [x] Environment variable support (host, port, password)
- [x] Unit tests for config validation

**Dependencies**: Phase 1

---

### Phase 3: Integration Testing

**Goal**: Verify persistence across restarts

**Deliverables**:
- [x] Test position persistence
- [x] Test order persistence
- [x] Test recovery after restart
- [x] Performance benchmarks

**Dependencies**: Phase 2

---

## File Structure

```
config/
├── cache/
│   ├── __init__.py
│   ├── redis_config.py        # CacheConfig factory
│   └── docker-compose.redis.yml
tests/
├── unit/
│   └── test_redis_config.py
└── integration/
    └── test_redis_persistence.py
```

---

## API Design

### Configuration Factory

```python
from nautilus_trader.config import CacheConfig
from nautilus_trader.common.config import DatabaseConfig
import os

def create_redis_cache_config(
    host: str = None,
    port: int = None,
    password: str = None,
) -> CacheConfig:
    """Create production Redis cache configuration."""
    return CacheConfig(
        database=DatabaseConfig(
            type="redis",
            host=host or os.getenv("REDIS_HOST", "localhost"),
            port=port or int(os.getenv("REDIS_PORT", "6379")),
            password=password or os.getenv("REDIS_PASSWORD"),
        ),
        encoding="msgpack",
        persist_account_events=True,
        buffer_interval_ms=100,
        flush_on_start=False,
    )
```

---

## Testing Strategy

### Unit Tests
- [x] Config validation (invalid host, negative port)
- [x] Environment variable loading
- [x] Encoding options (msgpack, json)

### Integration Tests
- [x] Connect to Redis
- [x] Write position, verify persistence
- [x] Restart TradingNode, verify recovery
- [x] Performance: write latency < 1ms

### Performance Tests
- [x] 1000 writes/second sustained
- [x] Memory usage < 100MB for 10K positions

---

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Redis unavailable | High | Low | Retry with backoff, alert |
| Data corruption | High | Very Low | AOF checksums, backups |
| Memory exhaustion | Medium | Low | Capacity limits, monitoring |

---

## Dependencies

### External Dependencies
- Redis 7.x
- Docker (for local development)
- NautilusTrader >= 1.222.0

### Internal Dependencies
- None (foundational spec)

---

## Acceptance Criteria

- [x] Redis connects successfully
- [x] Positions persist across restart
- [x] Write latency < 1ms (p95)
- [x] Documentation complete
- [x] Docker compose provided

---

## Generated Artifacts

| Artifact | Path | Status |
|----------|------|--------|
| Research | `specs/018-redis-cache-backend/research.md` | ✅ Complete |
| Data Model | `specs/018-redis-cache-backend/data-model.md` | ✅ Complete |
| Contracts | `specs/018-redis-cache-backend/contracts/cache_config.py` | ✅ Complete |
| Quickstart | `specs/018-redis-cache-backend/quickstart.md` | ✅ Complete |
| Plan | `specs/018-redis-cache-backend/plan.md` | ✅ Complete |
