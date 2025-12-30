# Research: Position Recovery (Spec 017)

**Date**: 2025-12-30
**Status**: Complete

## Executive Summary

Position recovery in NautilusTrader is achieved through a combination of Redis cache persistence and the execution reconciliation system. The framework provides built-in mechanisms for state recovery, but requires careful configuration and strategy-level patterns to ensure seamless resume after restarts.

---

## Research Questions

### Q1: How does TradingNode handle position recovery on startup?

**Decision**: Use native `LiveExecEngineConfig.reconciliation=True` with startup delay

**Rationale**: NautilusTrader's reconciliation system automatically:
1. Queries exchange for current positions via `generate_position_status_reports()`
2. Compares with cached state
3. Generates synthetic orders (tagged `EXTERNAL` + `RECONCILIATION`) to bridge gaps
4. Uses price hierarchy: calculated price → mid-price → avg price → MARKET

**Alternatives Considered**:
- Custom reconciliation logic: Rejected (duplicates native functionality)
- External state manager: Rejected (adds complexity without benefit)

**Configuration**:
```python
LiveExecEngineConfig(
    reconciliation=True,
    reconciliation_startup_delay_secs=10.0,  # Wait for connections
    generate_missing_orders=True,
)
```

---

### Q2: How to configure Redis cache for position persistence?

**Decision**: Use native CacheConfig with msgpack encoding

**Rationale**:
- `msgpack` is faster than JSON for production
- `flush_on_start=False` is **CRITICAL** to preserve state across restarts
- Buffer interval of 100ms balances writes and performance

**Alternatives Considered**:
- JSON encoding: Rejected (slower, only useful for debugging)
- No buffering: Rejected (too many write operations)

**Configuration**:
```python
CacheConfig(
    database=DatabaseConfig(type="redis", host="localhost", port=6379),
    encoding="msgpack",
    timestamps_as_iso8601=True,
    buffer_interval_ms=100,
    flush_on_start=False,  # CRITICAL
)
```

**Key Schema** (from Spec 018):
```
nautilus:{trader_id}:positions:{venue}:{instrument_id}
nautilus:{trader_id}:orders:{client_order_id}
nautilus:{trader_id}:account:{venue}
```

---

### Q3: How to restore strategy state (indicators, pending orders)?

**Decision**: Use warmup pattern + cache position detection

**Rationale**:
- Strategies must request historical data on `on_start()` for indicator warmup
- Check `self.cache.position()` for recovered positions
- Use `external_order_claims` in StrategyConfig for claiming positions

**Pattern**:
```python
class RecoverableStrategy(Strategy):
    def on_start(self) -> None:
        # 1. Check for recovered positions
        for position in self.cache.positions():
            if position.is_open:
                self._handle_recovered_position(position)

        # 2. Request historical data for warmup
        self.request_bars(
            bar_type=self.bar_type,
            start=self.clock.utc_now() - timedelta(days=2),
        )

    def on_historical_data(self, data) -> None:
        for bar in data.bars:
            self.indicator.handle_bar(bar)
```

---

### Q4: What are known issues and workarounds?

**Known Bugs**:

| Issue | Description | Workaround |
|-------|-------------|------------|
| #3104 | HEDGING mode reconciliation fails | Use one-way mode only |
| #3042 | Routing client venue mismatch | Ensure instrument venue matches execution venue |

**Community Issues** (from Discord):

1. **Duplicate Orders on Restart**
   - Cause: Redis persistence enabled on existing positions
   - Workaround: Clear Redis or start fresh

2. **Negative Quantity Errors**
   - Cause: Confusing LONG close with SHORT open
   - Workaround: Explicit position tracking in strategy

3. **External Positions Not Recognized**
   - Cause: Missing `external_order_claims` config
   - Solution: Configure per strategy

---

### Q5: What are the integration points with Spec 016 and 018?

**Spec 016 (Order Reconciliation) Dependencies**:
- Position recovery triggers **after** order reconciliation completes
- Uses same `LiveExecEngineConfig` parameters
- Reconciliation flow: Orders → Fills → Positions

**Spec 018 (Redis Cache) Dependencies**:
- Redis must be running before TradingNode start
- Uses same `DatabaseConfig` for cache
- Key schema already defined in Spec 018

**Integration Order**:
```
1. Redis available (Spec 018)
2. TradingNode starts
3. Order reconciliation (Spec 016)
4. Position recovery (Spec 017) ← This spec
5. Strategy warmup
6. Trading begins
```

---

## Technical Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Recovery mechanism | Native reconciliation | Built-in, battle-tested |
| Cache encoding | msgpack | Performance (faster than JSON) |
| Startup delay | 10 seconds | Allow connections to establish |
| Indicator warmup | Historical data request | Native pattern, reliable |
| Position detection | Cache query | Simple, no custom state needed |

---

## Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| HEDGING mode not supported | High | Medium | Document limitation, use one-way mode |
| Redis unavailable | High | Low | Health check before start, alerts |
| Indicator warmup incomplete | Medium | Low | Wait for warmup callback before trading |
| External positions missed | Medium | Medium | Configure `external_order_claims` |

---

## Implementation Checklist

- [x] Research NautilusTrader native recovery mechanisms
- [x] Understand Redis cache schema (Spec 018)
- [x] Review order reconciliation flow (Spec 016)
- [x] Document known issues and workarounds
- [x] Define integration points between specs
- [ ] Create data model for recovery entities
- [ ] Define recovery API contracts
- [ ] Create implementation plan
