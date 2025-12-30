# Redis Monitoring Guide (Spec 018)

## Quick Health Check

```bash
# Ping test
redis-cli ping
# Expected: PONG

# Server info
redis-cli info server

# Memory usage
redis-cli info memory
```

## Key Metrics to Monitor

### Memory

```bash
# Current memory usage
redis-cli info memory | grep used_memory_human

# Peak memory
redis-cli info memory | grep used_memory_peak_human
```

**Alerts**:
- Warning: > 80% of maxmemory
- Critical: > 95% of maxmemory

### Connections

```bash
# Connected clients
redis-cli info clients | grep connected_clients

# Blocked clients
redis-cli info clients | grep blocked_clients
```

**Alerts**:
- Warning: blocked_clients > 0
- Critical: connected_clients > 90% of maxclients

### Persistence

```bash
# Last save status
redis-cli info persistence | grep rdb_last_bgsave_status
redis-cli info persistence | grep aof_last_bgrewrite_status
```

**Alerts**:
- Critical: rdb_last_bgsave_status != ok
- Critical: aof_last_bgrewrite_status != ok

## Real-Time Monitoring

```bash
# Watch all commands
redis-cli monitor

# Filter for trading data
redis-cli monitor | grep "trader-"

# Stats every second
redis-cli --stat
```

## Trading-Specific Queries

```bash
# Count positions
redis-cli keys "trader-position:*" | wc -l

# Count open orders
redis-cli keys "trader-order:*" | wc -l

# List all accounts
redis-cli keys "trader-account:*"

# Get specific position
redis-cli get "trader-position:BTCUSDT-PERP.BINANCE-001"
```

## Grafana Dashboard

For production monitoring, see Spec 005 Grafana integration.

Key panels:
- Redis memory usage
- Operations per second
- Connection count
- Persistence status
- Trading key counts

## Alerting Rules

### Prometheus Alerts (if using)

```yaml
groups:
  - name: redis
    rules:
      - alert: RedisDown
        expr: redis_up == 0
        for: 1m
        labels:
          severity: critical

      - alert: RedisMemoryHigh
        expr: redis_memory_used_bytes / redis_memory_max_bytes > 0.9
        for: 5m
        labels:
          severity: warning

      - alert: RedisPersistenceFailed
        expr: redis_rdb_last_bgsave_status != 1
        for: 1m
        labels:
          severity: critical
```

## Backup

```bash
# Trigger manual backup
redis-cli bgsave

# Check backup status
redis-cli lastsave

# Copy backup file
cp /var/lib/redis/dump.rdb /backup/redis-$(date +%Y%m%d).rdb
```

## Recovery

```bash
# Stop Redis
docker-compose -f config/cache/docker-compose.redis.yml down

# Restore backup
cp /backup/redis-backup.rdb /var/lib/redis/dump.rdb

# Start Redis
docker-compose -f config/cache/docker-compose.redis.yml up -d
```
