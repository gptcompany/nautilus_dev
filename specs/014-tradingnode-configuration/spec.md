# Spec 014: TradingNode Configuration

## Overview

Create production-ready TradingNode configuration for live trading on Binance and Bybit.

## Problem Statement

Current system only has BacktestNode configuration. For live trading, we need properly configured TradingNode with all production settings.

## Goals

1. **Production Config**: Complete TradingNodeConfig for live trading
2. **Environment Separation**: Testnet vs Production configs
3. **Secret Management**: Secure API key handling

## Requirements

### Functional Requirements

#### FR-001: Base Configuration
```python
TradingNodeConfig(
    trader_id="NAUTILUS-PROD-001",
    instance_id=None,  # Auto-generated UUID
    environment=Environment.LIVE,
    cache=CacheConfig(...),
    data_engine=LiveDataEngineConfig(...),
    risk_engine=LiveRiskEngineConfig(...),
    exec_engine=LiveExecEngineConfig(...),
    streaming=StreamingConfig(...),
    data_clients={...},
    exec_clients={...},
)
```

#### FR-002: Cache Configuration (Redis)
```python
CacheConfig(
    database=DatabaseConfig(
        type="redis",
        host="${REDIS_HOST}",
        port=6379,
        username="${REDIS_USER}",
        password="${REDIS_PASSWORD}",
    ),
    encoding="msgpack",
    timestamps_as_iso8601=True,
    buffer_interval_ms=100,
    persist_account_events=True,
)
```

#### FR-003: Execution Engine Configuration
```python
LiveExecEngineConfig(
    reconciliation=True,
    reconciliation_startup_delay_secs=10.0,
    reconciliation_interval_secs=300,  # 5 min
    inflight_check_interval_secs=5.0,
    inflight_timeout_ms=5000,
    graceful_shutdown_on_exception=True,
)
```

#### FR-004: Logging Configuration
```python
LoggingConfig(
    log_level="INFO",
    log_level_file="DEBUG",
    log_directory="/var/log/nautilus",
    log_file_name="trading",
    log_file_format="json",
    log_component_levels={
        "ExecEngine": "DEBUG",
        "RiskEngine": "DEBUG",
        "DataEngine": "INFO",
    },
)
```

#### FR-005: Environment Variables
```bash
# .env.production
NAUTILUS_TRADER_ID=NAUTILUS-PROD-001
NAUTILUS_ENVIRONMENT=LIVE

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=secret

# Binance
BINANCE_API_KEY=xxx
BINANCE_API_SECRET=xxx
BINANCE_TESTNET=false

# Bybit
BYBIT_API_KEY=xxx
BYBIT_API_SECRET=xxx
BYBIT_TESTNET=false
```

### Non-Functional Requirements

#### NFR-001: Security
- API keys never in code or git
- Use environment variables or secret manager
- Separate testnet/production credentials

#### NFR-002: Reliability
- Auto-reconnect on connection loss (native to NautilusTrader adapters - no custom implementation needed)
- Graceful shutdown preserves state (positions/orders persisted via Redis cache per FR-002)

## Technical Design

### Configuration Factory

```python
class TradingNodeConfigFactory:
    """Factory for creating TradingNode configurations."""

    @classmethod
    def create_production(cls, strategies: list[StrategyConfig]) -> TradingNodeConfig:
        """Create production configuration."""
        return TradingNodeConfig(
            trader_id=os.environ["NAUTILUS_TRADER_ID"],
            environment=Environment.LIVE,
            cache=cls._cache_config(),
            exec_engine=cls._exec_engine_config(),
            data_clients=cls._data_clients(),
            exec_clients=cls._exec_clients(),
            strategies=strategies,
        )

    @classmethod
    def create_testnet(cls, strategies: list[StrategyConfig]) -> TradingNodeConfig:
        """Create testnet configuration."""
        # Similar but with testnet=True
```

### File Structure

```
config/
├── __init__.py           # Package exports
├── models.py             # Pydantic configuration models
├── factory.py            # TradingNodeConfigFactory
├── cache.py              # CacheConfig builder
├── execution.py          # LiveExecEngineConfig builder
├── data.py               # LiveDataEngineConfig builder
├── risk.py               # LiveRiskEngineConfig builder
├── logging_config.py     # LoggingConfig builder
├── streaming.py          # StreamingConfig builder
└── clients/
    ├── __init__.py
    ├── binance.py        # Binance client configs
    └── bybit.py          # Bybit client configs
```

## Environment Setup

### Production Checklist
- [ ] Redis running and accessible
- [ ] API keys configured in environment
- [ ] Logging directory exists and writable
- [ ] Network connectivity to exchanges verified
- [ ] Testnet validation completed

### Docker Compose (Optional)
```yaml
services:
  trading-node:
    build: .
    environment:
      - NAUTILUS_ENVIRONMENT=LIVE
    env_file:
      - .env.production
    volumes:
      - ./logs:/var/log/nautilus
    depends_on:
      - redis
    restart: unless-stopped
```

## Testing Strategy

1. **Config Validation**: Pydantic validation for all configs
2. **Testnet Integration**: Full cycle on testnet before production
3. **Connectivity Tests**: Exchange API reachability

## Dependencies

- Spec 015 (Binance Exec Client)
- Spec 018 (Redis Cache Backend)

## Success Metrics

- Configuration passes all Pydantic validation
- TradingNode starts successfully
- All data/exec clients connect
