# Implementation Plan: Binance Exec Client

**Feature Branch**: `015-binance-exec-client`
**Created**: 2025-12-31
**Status**: Planning
**Spec Reference**: `specs/015-binance-exec-client/spec.md`

## Architecture Overview

Binance execution client integration enables live order submission for USDT Futures trading. Builds on existing TradingNodeConfigFactory (Spec 014) and integrates with Redis cache (Spec 018) and graceful shutdown (Spec 019).

### System Context

```
┌─────────────────────────────────────────────────────────────────┐
│                        TradingNode                               │
│  ┌─────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │
│  │  Strategies │  │ LiveExecEngine  │  │ BinanceExecClient   │  │
│  │  (order     │──│ (reconciliation)│──│ (order submission)  │  │
│  │  submission)│  │                 │  │                     │  │
│  └─────────────┘  └────────┬────────┘  └──────────┬──────────┘  │
│                            │                       │             │
│                    ┌───────▼───────┐        ┌──────▼──────┐      │
│                    │ Redis Cache   │        │   Binance   │      │
│                    │ (order state) │        │   REST/WS   │      │
│                    └───────────────┘        └─────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

### Component Diagram

```
config/
├── clients/
│   └── binance.py           # Existing: build_binance_exec_client_config()
├── order_helpers.py         # NEW: Order submission helpers
├── binance_errors.py        # NEW: Error code handling
└── factory.py               # Existing: TradingNodeConfigFactory

Key Integration:
- TradingNodeConfigFactory._build_exec_clients() → BinanceExecClientConfig
- Strategy.submit_order() → LiveExecEngine → BinanceExecClient → Binance API
```

## Technical Decisions

### Decision 1: Enum Values (USDT_FUTURE vs USDT_FUTURES)

**Options Considered**:
1. **Option A**: Use `USDT_FUTURES` (plural)
   - Pros: Matches existing code
   - Cons: Breaks on nightly (AttributeError)
2. **Option B**: Use `USDT_FUTURE` (singular)
   - Pros: Works on nightly v1.222.0+
   - Cons: Requires updating existing code

**Selected**: Option B

**Rationale**: NautilusTrader nightly changed enum names from plural to singular. Our code must match.

---

### Decision 2: Position Mode

**Options Considered**:
1. **Option A**: Support HEDGE mode
   - Pros: More flexibility for hedging strategies
   - Cons: Known reconciliation bug #3104
2. **Option B**: ONE-WAY (NETTING) mode only
   - Pros: Works correctly, no known issues
   - Cons: Can't simultaneously hold long/short positions

**Selected**: Option B (ONE-WAY mode)

**Rationale**: HEDGE mode has unresolved reconciliation issues. ONE-WAY is safer for production.

---

### Decision 3: Order Type Scope

**Options Considered**:
1. **Option A**: Support all Binance order types
2. **Option B**: MVP with MARKET, LIMIT, STOP_MARKET, STOP_LIMIT only

**Selected**: Option B (MVP scope)

**Rationale**: Cover 95% of use cases. TRAILING_STOP and TAKE_PROFIT can be added in v2.

---

## Implementation Strategy

### Phase 1: Fix Existing Code

**Goal**: Update enum values to work with nightly

**Deliverables**:
- [ ] Fix `config/clients/binance.py` - Change `USDT_FUTURES` → `USDT_FUTURE`
- [ ] Fix `config/factory.py` - Change enum mapping
- [ ] Verify nightly compatibility

**Dependencies**: None

---

### Phase 2: Order Helpers

**Goal**: Create helper functions for order submission

**Deliverables**:
- [ ] `config/order_helpers.py` - Order creation utilities
- [ ] Unit tests for all order types
- [ ] Documentation in docstrings

**Dependencies**: Phase 1

---

### Phase 3: Error Handling

**Goal**: Robust handling of Binance-specific errors

**Deliverables**:
- [ ] `config/binance_errors.py` - Error code definitions
- [ ] Retry logic with exponential backoff
- [ ] Unit tests for error scenarios

**Dependencies**: Phase 1

---

### Phase 4: Integration Testing

**Goal**: Validate on Binance testnet

**Deliverables**:
- [ ] `tests/integration/test_binance_testnet.py`
- [ ] Order round-trip tests
- [ ] Reconnection tests

**Dependencies**: Phase 2, Phase 3

---

## File Structure

```
config/
├── clients/
│   └── binance.py           # EXISTING - needs enum fix
├── factory.py               # EXISTING - needs enum fix
├── order_helpers.py         # NEW - order submission utilities
├── binance_errors.py        # NEW - error code handling
└── __init__.py              # Update exports
tests/
├── test_binance_exec.py     # Unit tests for config
├── test_order_helpers.py    # Unit tests for order helpers
├── test_binance_errors.py   # Unit tests for error handling
└── integration/
    └── test_binance_testnet.py  # Testnet integration tests
```

## API Design

### Public Interface

```python
# Order helpers (config/order_helpers.py)
def create_market_order(
    order_factory: OrderFactory,
    instrument_id: InstrumentId,
    side: OrderSide,
    quantity: Quantity,
) -> MarketOrder: ...

def create_limit_order(
    order_factory: OrderFactory,
    instrument_id: InstrumentId,
    side: OrderSide,
    quantity: Quantity,
    price: Price,
    post_only: bool = False,
) -> LimitOrder: ...

def create_stop_market_order(
    order_factory: OrderFactory,
    instrument_id: InstrumentId,
    side: OrderSide,
    quantity: Quantity,
    trigger_price: Price,
) -> StopMarketOrder: ...
```

### Configuration

```python
# Existing config/clients/binance.py (with fixes)
def build_binance_exec_client_config(
    credentials: BinanceCredentials,
) -> BinanceExecClientConfig:
    account_type = {
        "SPOT": BinanceAccountType.SPOT,
        "USDT_FUTURES": BinanceAccountType.USDT_FUTURE,  # Fixed
        "COIN_FUTURES": BinanceAccountType.COIN_FUTURE,  # Fixed
    }[credentials.account_type]
    ...
```

## Testing Strategy

### Unit Tests
- [ ] Test config creation with all parameters
- [ ] Test order helper functions
- [ ] Test error code classification
- [ ] Test backoff delay calculation

### Integration Tests
- [ ] Connect to Binance testnet
- [ ] Submit MARKET order and verify fill
- [ ] Submit LIMIT order and cancel
- [ ] Submit STOP_MARKET order (Algo API)
- [ ] Test WebSocket reconnection

### Performance Tests
- [ ] Order submission latency < 100ms
- [ ] Fill notification < 50ms after exchange fill

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Enum name changes again | High | Low | Pin NautilusTrader version, monitor changelog |
| HEDGE mode needed | Medium | Low | Document limitation, can add in v2 |
| Rate limit ban | High | Medium | Conservative retry limits (max 3) |
| Testnet unreliable | Low | Medium | Retry tests, manual validation |

## Dependencies

### External Dependencies
- NautilusTrader Nightly >= 2025-12-10 (Algo Order API fix)
- Binance API credentials (testnet and/or production)

### Internal Dependencies
- Spec 014: TradingNode Configuration (COMPLETED)
- Spec 018: Redis Cache Backend (COMPLETED)
- Spec 019: Graceful Shutdown (COMPLETED)

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| Black Box Design | ✅ | Clean helper functions, hidden implementation |
| KISS | ✅ | Use native BinanceExecClientConfig, no custom wrappers |
| Native First | ✅ | All order types via NautilusTrader native API |
| NO df.iterrows() | ✅ | No DataFrame operations |
| TDD Discipline | 🔄 | Tests in tasks.md |

## Acceptance Criteria

- [ ] All unit tests passing (coverage > 80%)
- [ ] Enum values work with nightly v1.222.0+
- [ ] All 4 order types work on testnet (MARKET, LIMIT, STOP_MARKET, STOP_LIMIT)
- [ ] Order latency < 100ms
- [ ] Reconnection handling works
- [ ] Documentation updated
