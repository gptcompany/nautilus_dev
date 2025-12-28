# Implementation Plan: Binance Exec Client (Spec 015)

**Feature Branch**: `015-binance-exec-client`
**Created**: 2025-12-28
**Status**: Draft
**Spec Reference**: `specs/015-binance-exec-client/spec.md`

---

## Architecture Overview

### System Context

The Binance Exec Client integrates NautilusTrader with Binance USDT Futures for live order execution. It builds on Spec 014 (TradingNode Configuration) to provide a complete live trading setup.

```
┌─────────────────────────────────────────────────────────────┐
│                      TradingNode                            │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐ │
│  │  Strategy   │  │  ExecEngine  │  │   BinanceExecClient │ │
│  │  (User)     │──│  (Core)      │──│   (Adapter)         │ │
│  └─────────────┘  └──────────────┘  └─────────────────────┘ │
│        │                │                    │              │
│        ▼                ▼                    ▼              │
│   ┌─────────┐    ┌───────────┐      ┌──────────────────┐   │
│   │ Orders  │    │   Cache   │      │   Binance API    │   │
│   │ Events  │    │  (Redis)  │      │   HTTP + WS      │   │
│   └─────────┘    └───────────┘      └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Component Diagram

```
┌─────────────────────────────────────────────────────┐
│                 config/binance_exec.py              │
│  ┌───────────────────────────────────────────────┐  │
│  │  create_binance_exec_client()                 │  │
│  │    → BinanceExecClientConfig                  │  │
│  │    → InstrumentProviderConfig                 │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│           Integration with Spec 014                 │
│  ┌───────────────────────────────────────────────┐  │
│  │  create_tradingnode_config(                   │  │
│  │      exec_clients={"BINANCE": binance_exec},  │  │
│  │  )                                            │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## Technical Decisions

### Decision 1: Position Mode

**Options Considered**:
1. **ONE-WAY (NETTING)**
   - Pros: Works correctly, simple mental model
   - Cons: Can't have simultaneous long/short on same instrument
2. **HEDGE mode**
   - Pros: Flexible position management
   - Cons: Known reconciliation bug (#3104)

**Selected**: Option 1 (ONE-WAY/NETTING)

**Rationale**: HEDGE mode has unresolved reconciliation bug. ONE-WAY mode is reliable and meets requirements.

---

### Decision 2: Order Types Implementation

**Options Considered**:
1. **MARKET + LIMIT only**
   - Pros: Simple, well-tested
   - Cons: No stop-loss automation
2. **Include STOP_MARKET and STOP_LIMIT**
   - Pros: Full trading capability
   - Cons: Requires nightly >= 2025-12-10 (Algo Order API fix)

**Selected**: Option 2 (MVP scope)

**Rationale**: STOP orders essential for risk management. Algo API fix is already merged.

**MVP Scope**: MARKET, LIMIT, STOP_MARKET, STOP_LIMIT
**Deferred to v2**: TAKE_PROFIT_MARKET, TRAILING_STOP_MARKET (same Algo API, minimal changes)

---

### Decision 3: Error Handling Strategy

**Options Considered**:
1. **Fail fast on all errors**
   - Pros: Simple, predictable
   - Cons: Transient errors crash system
2. **Retry with exponential backoff**
   - Pros: Handles rate limits, network issues
   - Cons: More complex, potential delays

**Selected**: Option 2 with limits

**Rationale**: Production systems need resilience. Max 3 retries prevents account bans.

---

## Implementation Strategy

### Phase 1: Client Factory Module

**Goal**: Create factory function for BinanceExecClientConfig

**Deliverables**:
- [ ] `config/binance_exec.py` with `create_binance_exec_client()`
- [ ] Environment variable validation
- [ ] Default configuration for testnet vs production
- [ ] Unit tests for factory function

**Dependencies**: Spec 014 (TradingNodeConfigFactory)

---

### Phase 2: Order Submission Utilities

**Goal**: Helper functions for common order types

**Deliverables**:
- [ ] Market order helper
- [ ] Limit order helper
- [ ] Stop market order helper (Algo API)
- [ ] Stop limit order helper
- [ ] Order validation utilities

**Dependencies**: Phase 1

---

### Phase 3: Error Handling & Logging

**Goal**: Robust error handling for Binance-specific errors

**Deliverables**:
- [ ] Rate limit handling with backoff
- [ ] Insufficient balance handling
- [ ] Invalid symbol/order validation
- [ ] Network error retry logic
- [ ] Comprehensive logging

**Dependencies**: Phase 2

---

### Phase 4: Integration Testing

**Goal**: Validate complete order lifecycle on testnet

**Deliverables**:
- [ ] Testnet connection test
- [ ] Market order round-trip test
- [ ] Limit order lifecycle test
- [ ] Stop order (Algo API) test
- [ ] Error scenario tests

**Dependencies**: Phase 3

---

## File Structure

```
config/
├── binance_exec.py           # BinanceExecClient factory
├── tradingnode_factory.py    # From Spec 014 (updated)
└── __init__.py

tests/
├── test_binance_exec.py      # Unit tests
└── integration/
    └── test_binance_testnet.py  # Testnet integration
```

---

## API Design

### Public Interface

```python
def create_binance_exec_client(
    account_type: BinanceAccountType = BinanceAccountType.USDT_FUTURES,
    testnet: bool = False,
    max_retries: int = 3,
    leverages: dict[str, int] | None = None,
    margin_types: dict[str, str] | None = None,
) -> dict[str, BinanceExecClientConfig]:
    """
    Factory for Binance execution client configuration.

    Args:
        account_type: SPOT, USDT_FUTURES, or COIN_FUTURES
        testnet: Use Binance testnet
        max_retries: Max retry attempts for orders
        leverages: Symbol to leverage mapping
        margin_types: Symbol to margin type (CROSS/ISOLATED)

    Returns:
        Dict mapping venue name to client config
    """
```

### Configuration Model

```python
# Uses native BinanceExecClientConfig from NautilusTrader
# No custom wrapper needed - follow KISS principle
```

---

## Testing Strategy

### Unit Tests
- [ ] Factory creates valid config
- [ ] Environment variables sourced correctly
- [ ] Testnet vs production URLs
- [ ] Leverage and margin type mapping

### Integration Tests (Testnet)
- [ ] Connect to Binance testnet
- [ ] Submit and fill MARKET order
- [ ] Submit, modify, cancel LIMIT order
- [ ] Submit STOP_MARKET (Algo API)
- [ ] Handle rate limit gracefully
- [ ] Recover from WebSocket disconnect

### Performance Tests
- [ ] Order submission latency < 100ms
- [ ] Fill notification latency < 50ms

---

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Rate limit bans | High | Medium | Max 3 retries, exponential backoff |
| Algo API changes | Medium | Low | Monitor GitHub issues, nightly updates |
| HEDGE mode bugs | Medium | High | Use ONE-WAY mode only |
| Testnet differences | Low | Medium | Document testnet limitations |

---

## Dependencies

### External Dependencies
- NautilusTrader Nightly (>= 2025-12-10)
- Binance API credentials

### Internal Dependencies
- Spec 014 (TradingNode Configuration) - **COMPLETED**
- Spec 016 (Order Reconciliation) - downstream consumer

---

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| Black Box Design | PASS | Factory provides clean interface |
| KISS & YAGNI | PASS | Uses native BinanceExecClientConfig, no wrappers |
| Native First | PASS | Uses NautilusTrader adapter directly |
| Performance | PASS | No df.iterrows(), async operations |
| TDD Discipline | PENDING | Tests to be written in implementation |
| No Hardcoded Values | PASS | All config via parameters/env vars |

---

## Acceptance Criteria

- [ ] All unit tests passing (coverage > 80%)
- [ ] Testnet integration tests passing
- [ ] Market, Limit, Stop orders work correctly
- [ ] Error handling verified
- [ ] Documentation updated (this plan + quickstart)
- [ ] Code review approved
- [ ] alpha-debug verification complete

---

## Generated Artifacts

| Artifact | Path | Status |
|----------|------|--------|
| spec.md | `specs/015-binance-exec-client/spec.md` | EXISTS |
| plan.md | `specs/015-binance-exec-client/plan.md` | CREATED |
| research.md | `specs/015-binance-exec-client/research.md` | CREATED |
| data-model.md | `specs/015-binance-exec-client/data-model.md` | CREATED |
| contracts/ | `specs/015-binance-exec-client/contracts/` | CREATED |
| quickstart.md | `specs/015-binance-exec-client/quickstart.md` | CREATED |
