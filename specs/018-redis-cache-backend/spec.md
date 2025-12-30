# Spec 018: Redis Cache Backend

## Overview

Configure Redis as the cache backend for NautilusTrader, enabling state persistence across restarts.

## Problem Statement

Default in-memory cache loses all state on restart. For production, we need persistent cache that survives restarts and enables fast recovery.

## Goals

1. **State Persistence**: All trading state persisted to Redis
2. **Fast Recovery**: Sub-second state loading on restart
3. **Multi-Node Support**: Enable multiple TradingNode instances (future)

## Requirements

### Functional Requirements

#### FR-001: Redis Configuration
```python
DatabaseConfig(
    type="redis",
    host=os.environ.get("REDIS_HOST", "localhost"),
    port=int(os.environ.get("REDIS_PORT", 6379)),
    username=os.environ.get("REDIS_USER"),
    password=os.environ.get("REDIS_PASSWORD"),
    timeout=2.0,
    ssl=os.environ.get("REDIS_SSL", "false").lower() == "true",
)
```

#### FR-002: Cache Configuration
```python
CacheConfig(
    database=DatabaseConfig(...),
    encoding="msgpack",  # Faster than JSON
    timestamps_as_iso8601=True,
    buffer_interval_ms=100,  # Batch writes
    persist_account_events=True,
    persist_orders=True,
    persist_positions=True,
    persist_quotes=False,  # High volume, skip
    persist_trades=False,  # High volume, skip
)
```

#### FR-003: Data Retention
- Orders: 7 days (configurable)
- Positions: Until closed + 24h
- Account events: 30 days
- Quotes/trades: Not persisted (high volume)

#### FR-004: Redis Deployment
- Docker container for development
- Redis Cluster for production (optional)
- Sentinel for HA (optional)

### Non-Functional Requirements

#### NFR-001: Performance
- Write latency < 1ms (buffered)
- Read latency < 1ms
- Throughput > 10,000 ops/sec

#### NFR-002: Reliability
- Connection pooling with auto-reconnect
- Graceful handling of Redis unavailability

## Technical Design

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
    restart: unless-stopped

volumes:
  redis_data:
```

### Connection Management

```python
class RedisCacheManager:
    """Manages Redis connection for NautilusTrader cache."""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._pool: redis.ConnectionPool | None = None

    def get_connection(self) -> redis.Redis:
        if self._pool is None:
            self._pool = redis.ConnectionPool(
                host=self.config.host,
                port=self.config.port,
                password=self.config.password,
                socket_timeout=self.config.timeout,
                max_connections=20,
            )
        return redis.Redis(connection_pool=self._pool)

    def health_check(self) -> bool:
        try:
            return self.get_connection().ping()
        except redis.ConnectionError:
            return False
```

### Key Schema

```
# Namespace: nautilus:{trader_id}:

# Positions
nautilus:PROD-001:positions:{venue}:{instrument_id}

# Orders
nautilus:PROD-001:orders:{client_order_id}
nautilus:PROD-001:orders_open:{venue}:{instrument_id}

# Account
nautilus:PROD-001:account:{venue}

# Events (list)
nautilus:PROD-001:events:account:{venue}
nautilus:PROD-001:events:order:{client_order_id}
```

### Monitoring

```python
# Prometheus metrics for Redis
redis_operations_total = Counter("redis_operations_total", ["operation"])
redis_latency_seconds = Histogram("redis_latency_seconds", ["operation"])
redis_connection_pool_size = Gauge("redis_connection_pool_size")
```

## Testing Strategy

1. **Connection Tests**: Connect/disconnect/reconnect
2. **Persistence Tests**: Write -> restart -> read
3. **Performance Tests**: Latency and throughput benchmarks
4. **Failure Tests**: Redis unavailable during operation

## Dependencies

- Docker (for Redis container)
- Spec 014 (TradingNode Configuration)

## Success Metrics

- Write latency p99 < 5ms
- Read latency p99 < 2ms
- 100% state recovery after restart
- Zero data loss during Redis failover
