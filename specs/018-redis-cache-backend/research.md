# Research: Redis Cache Backend (Spec 018)

**Created**: 2025-12-30
**Status**: Complete

---

## Research Question 1: Redis Configuration Best Practices

### Decision
Use Redis 7.x with AOF persistence and msgpack serialization.

### Rationale
- **AOF (Append Only File)**: Durability without sacrificing performance
- **msgpack**: 30-50% smaller than JSON, faster serialization
- **Connection pooling**: Handled natively by NautilusTrader

### Configuration
```python
CacheConfig(
    database=DatabaseConfig(
        type="redis",
        host="localhost",
        port=6379,
        timeout=2,
    ),
    encoding="msgpack",
    buffer_interval_ms=100,  # Batch writes
)
```

### Alternatives Considered
1. **JSON encoding** - Human-readable but 50% larger
2. **RDB persistence** - Faster but potential data loss

---

## Research Question 2: Key Structure

### Decision
Use `trader-{type}:{identifier}` pattern with optional instance ID.

### Rationale
- **Namespacing**: Prevents collisions in multi-tenant setups
- **Scannable**: Can use `SCAN trader-position:*` for all positions
- **Native support**: Built into NautilusTrader CacheConfig

### Key Examples
```
trader-position:BTCUSDT-PERP.BINANCE-001
trader-order:O-20251230-001
trader-account:BINANCE-USDT_FUTURES-master
```

---

## Research Question 3: Performance Tuning

### Decision
Buffer writes at 100ms intervals, capacity-limit market data.

### Rationale
- **buffer_interval_ms=100**: Batches writes, reduces Redis round-trips
- **tick_capacity=10_000**: Limits memory for high-frequency data
- **bar_capacity=10_000**: Sufficient for most strategies

### Benchmarks (from Discord)
- Write latency: < 1ms (p95) with buffering
- Read latency: < 0.5ms (p95)
- Memory: ~100 bytes per position

---

## Research Question 4: High Availability

### Decision
Use Redis Sentinel for production HA.

### Rationale
- **Automatic failover**: Master failure handled transparently
- **NautilusTrader support**: Native Sentinel connection string
- **Simple setup**: 3 Sentinel nodes minimum

### Configuration
```python
DatabaseConfig(
    type="redis",
    host="sentinel://sentinel1:26379,sentinel2:26379,sentinel3:26379",
    password="secret",
)
```

### Alternatives Considered
1. **Redis Cluster** - Overkill for trading state
2. **Single instance** - No failover, acceptable for development

---

## Summary

| Topic | Decision |
|-------|----------|
| Persistence | AOF (appendonly yes) |
| Encoding | msgpack |
| Key pattern | trader-{type}:{identifier} |
| Buffering | 100ms batch writes |
| HA | Redis Sentinel for production |
