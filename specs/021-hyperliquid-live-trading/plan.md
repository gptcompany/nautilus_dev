# Implementation Plan: Hyperliquid Live Trading (Spec 021)

**Feature Branch**: `021-hyperliquid-live-trading`
**Created**: 2025-12-28
**Status**: Draft
**Spec Reference**: `specs/021-hyperliquid-live-trading/spec.md`

---

## Architecture Overview

### System Context

Hyperliquid integration provides live trading capability for a decentralized perpetual futures exchange. This is our **primary target exchange** for live trading due to low fees and self-custody.

```
┌─────────────────────────────────────────────────────────────┐
│                      TradingNode                            │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐ │
│  │  Strategy   │  │  ExecEngine  │  │ HyperliquidExecClient│ │
│  │  (User)     │──│  (Core)      │──│   (Rust Adapter)    │ │
│  └─────────────┘  └──────────────┘  └─────────────────────┘ │
│        │                │                    │              │
│        ▼                ▼                    ▼              │
│   ┌─────────┐    ┌───────────┐      ┌──────────────────┐   │
│   │ Orders  │    │   Cache   │      │   Hyperliquid    │   │
│   │ Events  │    │  (Redis)  │      │   L1 Chain       │   │
│   └─────────┘    └───────────┘      └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Component Diagram

```
┌─────────────────────────────────────────────────────┐
│              configs/hyperliquid/                   │
│  ┌───────────────────────────────────────────────┐  │
│  │  trading_node.py                              │  │
│  │    → HyperliquidDataClientConfig              │  │
│  │    → HyperliquidExecClientConfig              │  │
│  │    → TradingNodeConfig                        │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│           strategies/hyperliquid/                   │
│  ┌───────────────────────────────────────────────┐  │
│  │  base_strategy.py                             │  │
│  │    → RiskManager integration (Spec 011)       │  │
│  │    → Stop-loss on position open               │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## Technical Decisions

### Decision 1: Adapter Status Mitigation

**Options Considered**:
1. **Wait for stable release**
   - Pros: More reliable
   - Cons: Unknown timeline, blocks progress
2. **Use current nightly with monitoring**
   - Pros: Start now, track issues
   - Cons: May encounter bugs

**Selected**: Option 2

**Rationale**: Data client is stable. Execution client is functional for basic orders. We'll use testnet extensively and monitor GitHub #3152.

---

### Decision 2: Data Persistence Strategy

**Options Considered**:
1. **Native NautilusTrader PersistenceConfig**
   - Pros: Integrated, real-time
   - Cons: Requires TradingNode running
2. **CCXT Pipeline (Spec 001)**
   - Pros: Already exists, historical backfill
   - Cons: Not integrated with live trading

**Selected**: Both (Hybrid)

**Rationale**: Use Option 1 for live data during trading. Use Option 2 for historical backfill and when TradingNode is offline.

---

### Decision 3: Risk Manager Integration

**Options Considered**:
1. **Standalone risk checks**
   - Pros: Simple
   - Cons: Duplicates Spec 011 work
2. **Integrate with Spec 011 RiskManager**
   - Pros: Unified risk management
   - Cons: Dependency on Spec 011

**Selected**: Option 2

**Rationale**: Spec 011 RiskManager is designed for this. Reuse existing code.

---

## Implementation Strategy

### Phase 1: Data Feed Configuration

**Goal**: Stream live market data from Hyperliquid

**Deliverables**:
- [ ] `configs/hyperliquid/data_client.py` with HyperliquidDataClientConfig
- [ ] Subscribe to BTC-USD-PERP, ETH-USD-PERP
- [ ] Verify QuoteTick, TradeTick, OrderBookDelta types
- [ ] Unit tests for config

**Dependencies**: None (DataClient is stable)

---

### Phase 2: Data Persistence Integration

**Goal**: Record live data to ParquetDataCatalog

**Deliverables**:
- [ ] `configs/hyperliquid/persistence.py` with PersistenceConfig
- [ ] Catalog at `./catalog/hyperliquid/`
- [ ] Verify BacktestNode compatibility
- [ ] Integration test with recorded data

**Dependencies**: Phase 1

---

### Phase 3: Testnet Execution

**Goal**: Submit and manage orders on Hyperliquid testnet

**Deliverables**:
- [ ] `configs/hyperliquid/testnet.py` with testnet configuration
- [ ] Environment variable setup (HYPERLIQUID_TESTNET_PK)
- [ ] Test MARKET order submission
- [ ] Test LIMIT order lifecycle
- [ ] Test STOP_MARKET order
- [ ] Verify fill events received

**Dependencies**: Phase 1, testnet credentials

---

### Phase 4: Risk Manager Integration

**Goal**: Integrate with Spec 011 RiskManager

**Deliverables**:
- [ ] `strategies/hyperliquid/base_strategy.py` with RiskManager
- [ ] Auto stop-loss on PositionOpened
- [ ] Position limits enforcement
- [ ] End-to-end test on testnet

**Dependencies**: Phase 3, Spec 011 ✅ (COMPLETE)

---

### Phase 5: Production Configuration

**Goal**: Ready for mainnet trading

**Deliverables**:
- [ ] `configs/hyperliquid/trading_node.py` for production
- [ ] `scripts/hyperliquid/run_live.py` launcher
- [ ] Monitoring and alerting setup
- [ ] Documentation updates

**Dependencies**: Phase 4, mainnet credentials

---

## File Structure

```
nautilus_dev/
├── configs/
│   └── hyperliquid/
│       ├── __init__.py
│       ├── data_client.py       # Data-only config
│       ├── testnet.py           # Testnet config
│       ├── persistence.py       # Data recording config
│       └── trading_node.py      # Full production config
├── strategies/
│   └── hyperliquid/
│       ├── __init__.py
│       ├── config.py            # Strategy config
│       └── base_strategy.py     # Base with RiskManager
├── scripts/
│   └── hyperliquid/
│       ├── record_data.py       # Data recording script
│       └── run_live.py          # Live trading launcher
└── tests/
    └── hyperliquid/
        ├── test_data_client.py
        ├── test_exec_client.py
        └── integration/
            └── test_live_cycle.py
```

---

## API Design

### Public Interface

```python
def create_hyperliquid_data_client(
    testnet: bool = False,
    instruments: list[str] | None = None,
) -> dict:
    """Factory for Hyperliquid data client configuration."""

def create_hyperliquid_exec_client(
    testnet: bool = False,
    max_retries: int = 3,
) -> dict:
    """Factory for Hyperliquid execution client configuration."""

def create_hyperliquid_trading_node(
    trader_id: str,
    testnet: bool = False,
    redis_enabled: bool = True,
) -> TradingNodeConfig:
    """Factory for complete Hyperliquid TradingNode."""
```

---

## Testing Strategy

### Unit Tests
- [ ] Data client config validation
- [ ] Exec client config validation
- [ ] TradingNode config assembly
- [ ] Strategy config validation

### Integration Tests (Testnet)
- [ ] Connect to Hyperliquid testnet
- [ ] Subscribe to market data
- [ ] Submit MARKET order
- [ ] Submit LIMIT order
- [ ] Submit STOP_MARKET order
- [ ] Verify fill events
- [ ] Test RiskManager stop-loss

### Performance Tests
- [ ] Data feed latency < 50ms
- [ ] Order submission latency < 200ms

---

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Adapter bugs | High | Medium | Use testnet extensively, monitor #3152 |
| Chain congestion | Medium | Low | Implement retry logic, alert on delays |
| Private key exposure | Critical | Low | Environment variables only, never in code |
| Liquidity gaps | Medium | Medium | Small position sizes, limit orders |

---

## Dependencies

### External Dependencies
- NautilusTrader Nightly >= 1.222.0
- Hyperliquid testnet/mainnet account
- EVM wallet with private key
- USDC for trading

### Internal Dependencies
- Spec 011 (Stop-Loss & Position Limits) - ✅ **COMPLETE** - RiskManager ready
- Spec 014 (TradingNode Configuration) - for TradingNode patterns

---

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| Black Box Design | PASS | Factory functions with clean interfaces |
| KISS & YAGNI | PASS | Uses native adapter, no custom wrappers |
| Native First | PASS | Rust adapter via Python bindings |
| Performance | PASS | Native Rust, no df.iterrows() |
| TDD Discipline | PENDING | Tests in implementation |
| No Hardcoded Values | PASS | All config via params/env vars |

---

## Acceptance Criteria

- [ ] Live data feed operational (US1)
- [ ] Data persisted to catalog (US2)
- [ ] Testnet orders execute successfully (US3, US5)
- [ ] RiskManager integration working (US4)
- [ ] All tests passing (coverage > 80%)
- [ ] Documentation complete
- [ ] alpha-debug verification

---

## Generated Artifacts

| Artifact | Path | Status |
|----------|------|--------|
| spec.md | `specs/021-hyperliquid-live-trading/spec.md` | EXISTS |
| research.md | `specs/021-hyperliquid-live-trading/research.md` | EXISTS |
| plan.md | `specs/021-hyperliquid-live-trading/plan.md` | CREATED |
| data-model.md | `specs/021-hyperliquid-live-trading/data-model.md` | EXISTS |
| contracts/ | `specs/021-hyperliquid-live-trading/contracts/` | EXISTS |
| quickstart.md | `specs/021-hyperliquid-live-trading/quickstart.md` | EXISTS |
