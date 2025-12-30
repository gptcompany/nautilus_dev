# Spec 018: Redis Cache Backend

## Overview

Configure Redis as the persistent cache backend for NautilusTrader TradingNode, enabling position recovery and state persistence across restarts.

## Problem Statement

Without a persistent cache backend, all trading state (positions, orders, account balances) is lost when TradingNode restarts. Redis provides fast, reliable state persistence.

## Goals

1. **State Persistence**: Persist positions, orders, accounts to Redis
2. **Fast Recovery**: Sub-second cache reads on startup
3. **Production Ready**: Battle-tested configuration for live trading

## Requirements

### Functional Requirements

#### FR-001: Redis Connection
- Connect to Redis server (local or remote)
- Support authentication (password, TLS)
- Handle connection failures gracefully

#### FR-002: Data Persistence
- Persist positions with msgpack serialization
- Persist orders with full event history
- Persist account balances and margins
- Persist instrument definitions

#### FR-003: Key Structure
- Use trader-prefixed keys for multi-tenant support
- Support instance ID for multiple nodes per trader
- Configurable TTL for cached data

### Non-Functional Requirements

#### NFR-001: Performance
- Write latency < 1ms (p95)
- Read latency < 1ms (p95)
- Support 10,000+ keys without degradation

#### NFR-002: Reliability
- Automatic reconnection on failure
- Buffered writes to handle burst traffic
- No data loss on graceful shutdown

## Technical Design

### CacheConfig

```python
from nautilus_trader.config import CacheConfig
from nautilus_trader.common.config import DatabaseConfig

cache_config = CacheConfig(
    database=DatabaseConfig(
        type="redis",
        host="localhost",
        port=6379,
        password=None,  # Optional
        ssl=False,      # Enable for production
        timeout=2,      # Connection timeout seconds
    ),
    encoding="msgpack",           # or "json" for debugging
    timestamps_as_iso8601=False,  # Use nanoseconds
    persist_account_events=True,  # CRITICAL for recovery
    buffer_interval_ms=100,       # Batch writes
    use_trader_prefix=True,       # Namespace by trader
    use_instance_id=False,        # Multi-instance support
    flush_on_start=False,         # Preserve state on restart
    tick_capacity=10_000,         # Market data buffer
    bar_capacity=10_000,          # Bar data buffer
)
```

### Redis Key Structure

```
trader-{type}:{identifier}

Examples:
  trader-position:BTCUSDT-PERP.BINANCE-001
  trader-order:O-20251230-001
  trader-account:BINANCE-USDT_FUTURES-master
  trader-instrument:BTCUSDT-PERP.BINANCE
```

### Docker Compose

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  redis_data:
```

## Dependencies

- Redis 7.x
- NautilusTrader >= 1.222.0

## Success Metrics

- Connection success rate: 99.9%
- Write latency < 1ms (p95)
- Zero data loss on restart
