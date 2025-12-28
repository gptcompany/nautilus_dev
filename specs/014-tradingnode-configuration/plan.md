# Implementation Plan: TradingNode Configuration

**Feature Branch**: `014-tradingnode-configuration`
**Created**: 2025-12-28
**Status**: Draft
**Spec Reference**: `specs/014-tradingnode-configuration/spec.md`

## Architecture Overview

Production-ready TradingNode configuration system for live trading on Binance and Bybit exchanges. Provides factory pattern for creating testnet and production configurations with proper secret management, Redis caching, and reconciliation settings.

### System Context

```
┌─────────────────────────────────────────────────────────────────────┐
│                         NautilusTrader Node                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    TradingNodeConfigFactory                   │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐  │  │
│  │  │  create_prod()  │  │ create_testnet()│  │ from_env()   │  │  │
│  │  └────────┬────────┘  └────────┬────────┘  └──────┬───────┘  │  │
│  └───────────┼────────────────────┼──────────────────┼──────────┘  │
│              ▼                    ▼                  ▼             │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                      TradingNodeConfig                        │  │
│  │  ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌───────────────────┐  │  │
│  │  │ Cache   │ │ Exec    │ │ Data     │ │ Risk Engine       │  │  │
│  │  │ (Redis) │ │ Engine  │ │ Engine   │ │ (Rate Limits)     │  │  │
│  │  └────┬────┘ └────┬────┘ └────┬─────┘ └─────────┬─────────┘  │  │
│  └───────┼───────────┼───────────┼─────────────────┼────────────┘  │
│          ▼           ▼           ▼                 ▼               │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌─────────────────┐  │
│  │   Redis    │ │  Binance   │ │  Bybit     │ │  Data Catalog   │  │
│  │   Cache    │ │  Adapters  │ │  Adapters  │ │  (Streaming)    │  │
│  └────────────┘ └────────────┘ └────────────┘ └─────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Diagram

```
config/
├── __init__.py           # Package exports
├── factory.py            # TradingNodeConfigFactory
├── cache.py              # CacheConfig helpers
├── execution.py          # ExecEngine config
├── data.py               # DataEngine config
├── risk.py               # RiskEngine config
├── logging_config.py     # LoggingConfig helpers
├── secrets.py            # Environment variable loading
└── clients/
    ├── __init__.py
    ├── binance.py        # Binance client configs
    └── bybit.py          # Bybit client configs
```

## Technical Decisions

### Decision 1: Configuration Factory Pattern

**Options Considered**:
1. **Factory Pattern**: Single factory class with methods for each environment
   - Pros: Clean API, centralized logic, easy testing
   - Cons: Slightly more code
2. **Direct Configuration**: Build config directly in main.py
   - Pros: Simple, transparent
   - Cons: Code duplication, error-prone

**Selected**: Option 1 - Factory Pattern

**Rationale**: Centralizes configuration logic, makes it easy to switch between testnet and production, and allows for proper testing of configuration generation.

---

### Decision 2: Secret Management

**Options Considered**:
1. **Environment Variables**: Load from `os.environ`
   - Pros: Standard practice, works with Docker, 12-factor app
   - Cons: Need to manage .env files
2. **HashiCorp Vault**: External secret manager
   - Pros: Enterprise-grade, rotation support
   - Cons: Overkill for single-node, adds complexity
3. **AWS Secrets Manager / GCP Secret Manager**
   - Pros: Cloud-native, auto-rotation
   - Cons: Cloud lock-in, costs

**Selected**: Option 1 - Environment Variables

**Rationale**: Simplest solution that works with Docker, shell scripts, and local development. Can be upgraded to secret manager later if needed.

---

### Decision 3: Cache Backend

**Options Considered**:
1. **Redis**: Full-featured cache with persistence
   - Pros: Production-proven, supports persistence, required for position recovery
   - Cons: External dependency
2. **In-Memory Cache**: No persistence
   - Pros: No dependencies
   - Cons: No crash recovery, positions lost on restart

**Selected**: Option 1 - Redis

**Rationale**: Production trading requires position persistence and crash recovery. Redis is the standard choice for NautilusTrader production deployments.

---

### Decision 4: Logging Strategy

**Options Considered**:
1. **JSON Logs**: Structured logging to files
   - Pros: Machine-parseable, works with ELK/Loki
   - Cons: Less human-readable
2. **Plain Text Logs**: Traditional text logging
   - Pros: Human-readable
   - Cons: Hard to parse, aggregate

**Selected**: Option 1 - JSON Logs

**Rationale**: Production systems need machine-parseable logs for monitoring and alerting. JSON format integrates with Grafana Loki, ELK, and other log aggregation systems.

---

## Implementation Strategy

### Phase 1: Foundation (config/ package)

**Goal**: Create base configuration infrastructure and secret loading.

**Deliverables**:
- [x] `config/__init__.py` - Package exports
- [x] `config/secrets.py` - Environment variable loading with validation
- [x] `.env.example` - Template for environment variables
- [x] `tests/test_config_secrets.py` - Unit tests for secret loading

**Dependencies**: None

---

### Phase 2: Core Configuration Classes

**Goal**: Implement individual configuration helpers for each engine.

**Deliverables**:
- [ ] `config/cache.py` - Redis CacheConfig builder
- [ ] `config/execution.py` - LiveExecEngineConfig builder
- [ ] `config/data.py` - LiveDataEngineConfig builder
- [ ] `config/risk.py` - LiveRiskEngineConfig builder
- [ ] `config/logging_config.py` - LoggingConfig builder
- [ ] `config/streaming.py` - StreamingConfig builder

**Dependencies**: Phase 1

---

### Phase 3: Exchange Client Configurations

**Goal**: Implement Binance and Bybit client configuration builders.

**Deliverables**:
- [ ] `config/clients/binance.py` - Binance data/exec client configs
- [ ] `config/clients/bybit.py` - Bybit data/exec client configs
- [ ] Unit tests for client configurations

**Dependencies**: Phase 2

---

### Phase 4: Factory Implementation

**Goal**: Create unified TradingNodeConfigFactory.

**Deliverables**:
- [ ] `config/factory.py` - Main factory implementation
- [ ] `create_production()` - Production config generator
- [ ] `create_testnet()` - Testnet config generator
- [ ] Integration tests

**Dependencies**: Phase 3

---

### Phase 5: Docker Integration

**Goal**: Add Docker Compose for production deployment.

**Deliverables**:
- [ ] `docker-compose.yml` - Redis + TradingNode
- [ ] `Dockerfile` - TradingNode container
- [ ] `.env.production.example` - Production env template
- [ ] Deployment documentation

**Dependencies**: Phase 4

---

## Constitution Check

### Verified Compliance:
- [x] **Black Box Design**: Factory pattern provides clean interface, hidden implementation
- [x] **KISS & YAGNI**: Environment variables (simple), no secret manager (overkill)
- [x] **Native First**: Uses NautilusTrader native config classes
- [x] **Performance Constraints**: Redis for caching, msgpack encoding
- [x] **TDD Discipline**: Tests required for each phase

### Prohibited Actions Verified:
- [x] No `--no-verify` hook bypass
- [x] No hardcoded secrets (environment variables only)
- [x] No `df.iterrows()` usage
- [x] No reimplementation of native components

---

## File Structure

```
config/
├── __init__.py
├── factory.py             # TradingNodeConfigFactory
├── secrets.py             # Environment variable loading
├── cache.py               # CacheConfig helpers
├── execution.py           # LiveExecEngineConfig helpers
├── data.py                # LiveDataEngineConfig helpers
├── risk.py                # LiveRiskEngineConfig helpers
├── logging_config.py      # LoggingConfig helpers
├── streaming.py           # StreamingConfig helpers
└── clients/
    ├── __init__.py
    ├── binance.py         # BinanceLive[Data|Exec]ClientConfig
    └── bybit.py           # BybitLive[Data|Exec]ClientConfig

tests/
├── test_config_secrets.py
├── test_config_cache.py
├── test_config_execution.py
├── test_config_factory.py
└── integration/
    └── test_trading_node_startup.py

# Root files
.env.example
.env.production.example
docker-compose.yml
Dockerfile
```

## API Design

### Public Interface

```python
from config import TradingNodeConfigFactory

# Production
config = TradingNodeConfigFactory.create_production(
    strategies=[my_strategy_config],
    exchanges=["BINANCE", "BYBIT"],
)

# Testnet
config = TradingNodeConfigFactory.create_testnet(
    strategies=[my_strategy_config],
    exchanges=["BINANCE"],
)

# From environment
config = TradingNodeConfigFactory.from_env(
    strategies=[my_strategy_config],
)
```

### Configuration

```python
from pydantic import BaseModel
from typing import Literal

class ExchangeCredentials(BaseModel):
    api_key: str
    api_secret: str
    testnet: bool = False

class ConfigEnvironment(BaseModel):
    trader_id: str
    environment: Literal["LIVE", "SANDBOX"]
    redis_host: str = "localhost"
    redis_port: int = 6379
    log_directory: str = "/var/log/nautilus"
    catalog_path: str = "/data/nautilus/catalog"
```

## Testing Strategy

### Unit Tests
- [x] Test secret loading from environment
- [ ] Test cache configuration generation
- [ ] Test execution engine configuration
- [ ] Test data engine configuration
- [ ] Test risk engine configuration
- [ ] Test logging configuration
- [ ] Test streaming configuration
- [ ] Test Binance client configuration
- [ ] Test Bybit client configuration
- [ ] Test factory methods

### Integration Tests
- [ ] Test TradingNode initialization (no strategies)
- [ ] Test Binance testnet connection
- [ ] Test Bybit testnet connection
- [ ] Test Redis connection and persistence

### Validation Tests
- [ ] Test missing environment variables error handling
- [ ] Test invalid configuration combinations
- [ ] Test credential validation

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| API key exposure | High | Low | Environment variables, `.gitignore` |
| Redis connection failure | High | Medium | Retry logic, graceful degradation |
| Bybit hedge mode incompatibility | Medium | High | Document limitation, use netting mode |
| Rate limit violations | Medium | Medium | Configure rate limits in RiskEngine |
| Reconciliation failure on restart | High | Low | 60+ minute lookback, external_order_claims |

## Dependencies

### External Dependencies
- NautilusTrader >= 1.222.0 (nightly)
- Redis >= 6.0
- python-dotenv >= 1.0.0

### Internal Dependencies
- Spec 015 (Binance Exec Client) - uses BinanceLiveExecClientConfig
- Spec 018 (Redis Cache Backend) - uses CacheConfig with Redis

## Acceptance Criteria

- [ ] All unit tests passing (coverage > 80%)
- [ ] All integration tests passing
- [ ] TradingNode starts successfully with factory-generated config
- [ ] Binance testnet connection verified
- [ ] Bybit testnet connection verified
- [ ] Redis persistence verified
- [ ] Documentation updated
- [ ] Code review approved
