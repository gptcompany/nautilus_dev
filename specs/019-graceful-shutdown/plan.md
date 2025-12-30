# Implementation Plan: Graceful Shutdown

**Feature Branch**: `019-graceful-shutdown`
**Created**: 2025-12-30
**Status**: Planning
**Spec Reference**: `specs/019-graceful-shutdown/spec.md`

## Architecture Overview

Graceful shutdown ensures TradingNode stops safely without losing state or leaving orphan orders. Integrates with NautilusTrader's existing `LiveExecEngineConfig` and Redis cache from Spec 018.

### System Context

```
┌─────────────────────────────────────────────────────────────┐
│                      TradingNode                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Strategies │  │ ExecEngine  │  │  GracefulShutdown   │  │
│  │  (halted)   │◄─┤ (cancel)    │◄─┤  Handler            │  │
│  └─────────────┘  └──────┬──────┘  └──────────┬──────────┘  │
│                          │                     │             │
│                    ┌─────▼─────┐         ┌─────▼─────┐       │
│                    │   Cache   │◄────────┤  Signals  │       │
│                    │  (flush)  │         │ SIGTERM/  │       │
│                    └─────┬─────┘         │ SIGINT    │       │
│                          │               └───────────┘       │
└──────────────────────────┼───────────────────────────────────┘
                           ▼
                    ┌─────────────┐
                    │    Redis    │
                    │  (persisted)│
                    └─────────────┘
```

### Component Diagram

```
GracefulShutdownHandler
├── setup_signal_handlers()     # Register SIGTERM/SIGINT
├── shutdown()                  # Main shutdown sequence
│   ├── halt_trading()          # TradingState.HALTED
│   ├── cancel_all_orders()     # Cancel pending orders
│   ├── verify_stop_losses()    # Check position protection
│   ├── flush_cache()           # Persist to Redis
│   └── close_connections()     # Disconnect exchanges
└── force_exit()                # Timeout handler
```

## Technical Decisions

### Decision 1: Signal Handling Strategy

**Options Considered**:
1. **Option A**: Python signal module
   - Pros: Standard library, no dependencies
   - Cons: Limited async support
2. **Option B**: asyncio signal handlers
   - Pros: Native async integration, cleaner code
   - Cons: Requires event loop

**Selected**: Option B (asyncio signal handlers)

**Rationale**: TradingNode runs an event loop; asyncio.get_event_loop().add_signal_handler() integrates naturally with existing async code.

---

### Decision 2: Shutdown Sequence Order

**Options Considered**:
1. **Option A**: Cancel orders → Flush cache → Close connections
2. **Option B**: Halt trading → Cancel orders → Verify stops → Flush → Close

**Selected**: Option B

**Rationale**: Halting trading first prevents new orders during shutdown. Verifying stop-losses ensures positions are protected before exiting.

---

### Decision 3: Timeout Implementation

**Options Considered**:
1. **Option A**: asyncio.wait_for with timeout
2. **Option B**: Background timer thread with force exit

**Selected**: Option A (asyncio.wait_for)

**Rationale**: Stays within async model, no threading complexity. If timeout exceeded, raises TimeoutError which triggers force exit.

---

## Implementation Strategy

### Phase 1: Core Handler

**Goal**: Implement GracefulShutdownHandler class

**Deliverables**:
- [ ] config/shutdown/shutdown_handler.py - Main handler class
- [ ] config/shutdown/shutdown_config.py - Configuration dataclass
- [ ] config/shutdown/__init__.py - Module exports

**Dependencies**: Spec 018 (Redis Cache) - COMPLETED

---

### Phase 2: Integration

**Goal**: Integrate with TradingNode lifecycle

**Deliverables**:
- [ ] config/examples/trading_node_graceful.py - Example usage
- [ ] scripts/test_graceful_shutdown.py - Manual test script
- [ ] docs/019-graceful-shutdown-guide.md - User guide

**Dependencies**: Phase 1

---

### Phase 3: Monitoring & Polish

**Goal**: Add metrics and documentation

**Deliverables**:
- [ ] Prometheus metrics (shutdown_total, shutdown_duration)
- [ ] Alert recommendations in docs
- [ ] Update CLAUDE.md with shutdown section

**Dependencies**: Phase 2

---

## File Structure

```
config/
├── shutdown/
│   ├── __init__.py              # Module exports
│   ├── shutdown_config.py       # ShutdownConfig dataclass
│   └── shutdown_handler.py      # GracefulShutdownHandler
├── examples/
│   └── trading_node_graceful.py # Example with graceful shutdown
scripts/
├── test_graceful_shutdown.py    # Manual shutdown test
docs/
├── 019-graceful-shutdown-guide.md  # User guide
specs/019-graceful-shutdown/
├── spec.md                      # Requirements (exists)
├── plan.md                      # This file
├── research.md                  # Research findings
├── data-model.md                # Data structures
├── quickstart.md                # Quick start guide
└── contracts/
    └── shutdown_handler.py      # API contract
```

## API Design

### Public Interface

```python
class GracefulShutdownHandler:
    def __init__(self, node: TradingNode, config: ShutdownConfig) -> None: ...
    def setup_signal_handlers(self) -> None: ...
    async def shutdown(self, reason: str = "signal") -> None: ...
    def is_shutdown_requested(self) -> bool: ...
```

### Configuration

```python
@dataclass
class ShutdownConfig:
    timeout_secs: float = 30.0
    cancel_orders: bool = True
    verify_stop_losses: bool = True
    flush_cache: bool = True
    log_level: str = "INFO"
```

## Testing Strategy

### Unit Tests
- [ ] Test signal handler registration
- [ ] Test shutdown sequence order
- [ ] Test timeout handling
- [ ] Test config validation

### Integration Tests
- [ ] Test with mock TradingNode
- [ ] Test SIGTERM handling
- [ ] Test order cancellation flow
- [ ] Test cache flush to Redis

### Manual Tests
- [ ] Docker stop with grace period
- [ ] Ctrl+C during backtest
- [ ] Kill -TERM to running node

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Orders not cancelled | High | Medium | Retry loop, timeout fallback |
| Redis flush fails | High | Low | Graceful degradation, log warning |
| Signal not received | Medium | Low | Docker stop_signal config |
| Timeout too short | Medium | Medium | Configurable, sensible default |

## Dependencies

### External Dependencies
- NautilusTrader >= 1.220.0 (LiveExecEngineConfig)
- Redis (Spec 018) - for state persistence

### Internal Dependencies
- Spec 018: Redis Cache Backend (COMPLETED)
- Spec 011: Stop-Loss Position Limits (for verification)

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| Black Box Design | ✅ | Clean API, hidden implementation |
| KISS | ✅ | Simple signal handlers, no complex threading |
| Native First | ✅ | Uses NautilusTrader TradingState, LiveExecEngineConfig |
| NO df.iterrows() | ✅ | No DataFrame operations |
| TDD Discipline | 🔄 | Tests will be written first |

## Acceptance Criteria

- [ ] All unit tests passing (coverage > 80%)
- [ ] SIGTERM/SIGINT properly handled
- [ ] All open orders cancelled on shutdown
- [ ] State persisted to Redis before exit
- [ ] Configurable timeout works
- [ ] Documentation complete
