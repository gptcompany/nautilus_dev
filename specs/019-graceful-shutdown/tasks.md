# Tasks: Graceful Shutdown (Spec 019)

**Input**: Design documents from `/specs/019-graceful-shutdown/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

---

## Phase 1: Setup (Module Structure)

**Purpose**: Create config/shutdown module structure

- [X] T001 Create config/shutdown/__init__.py with module exports
- [X] T002 [P] Create config/shutdown/shutdown_config.py with ShutdownConfig dataclass

---

## Phase 2: Foundational (CacheConfig Factory)

**Purpose**: ShutdownConfig with validation MUST be complete before handler implementation

- [X] T003 Add ShutdownConfig validation (timeout 5-300s, log_level validation) in config/shutdown/shutdown_config.py
- [X] T004 [P] Add ShutdownReason enum in config/shutdown/shutdown_config.py

**Checkpoint**: ShutdownConfig ready - handler implementation can now begin

---

## Phase 3: User Story 1 - Signal Handling (Priority: P1) 🎯 MVP

**Goal**: TradingNode responds to SIGTERM/SIGINT with graceful shutdown sequence

**Independent Test**: `kill -TERM <pid>` triggers orderly shutdown with logs

### Implementation for US1

- [X] T005 [US1] Create GracefulShutdownHandler class skeleton in config/shutdown/shutdown_handler.py
- [X] T006 [US1] Implement setup_signal_handlers() with asyncio signal handlers in config/shutdown/shutdown_handler.py
- [X] T007 [US1] Implement halt_trading() method (TradingState.HALTED) in config/shutdown/shutdown_handler.py
- [X] T008 [US1] Implement cancel_all_orders() method in config/shutdown/shutdown_handler.py
- [X] T009 [US1] Implement verify_stop_losses() method (warning logs) in config/shutdown/shutdown_handler.py
- [X] T010 [US1] Implement shutdown() main sequence with timeout in config/shutdown/shutdown_handler.py

**Checkpoint**: Signal handling works - SIGTERM triggers full shutdown sequence

---

## Phase 4: User Story 2 - Exception Handling (Priority: P2)

**Goal**: Unhandled exceptions trigger graceful shutdown instead of crash

**Independent Test**: Raise exception in strategy, node shuts down gracefully

### Implementation for US2

- [X] T011 [US2] Add exception_handler() method for unhandled exceptions in config/shutdown/shutdown_handler.py
- [X] T012 [US2] Add is_shutdown_requested() state method in config/shutdown/shutdown_handler.py
- [X] T013 [US2] Export all public classes from config/shutdown/__init__.py

**Checkpoint**: Exception handling triggers graceful shutdown

---

## Phase 5: User Story 3 - Integration Example (Priority: P2)

**Goal**: Users have working example of TradingNode with graceful shutdown

**Independent Test**: Run example script, send SIGTERM, verify clean exit

### Implementation for US3

- [X] T014 [US3] Create example TradingNode with shutdown handler in config/examples/trading_node_graceful.py
- [X] T015 [US3] Create manual test script in scripts/test_graceful_shutdown.py
- [X] T016 [US3] Document shutdown workflow in docs/019-graceful-shutdown-guide.md

**Checkpoint**: Full integration example working

---

## Phase 6: Polish & Documentation

**Purpose**: Production hardening and documentation

- [X] T017 [P] Update CLAUDE.md with graceful shutdown section
- [X] T018 Run alpha-debug verification on all shutdown code

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Phase 1
- **US1 Signal Handling (Phase 3)**: Depends on Phase 2
- **US2 Exception Handling (Phase 4)**: Depends on US1
- **US3 Integration (Phase 5)**: Depends on US2
- **Polish (Phase 6)**: Depends on US3

### Parallel Opportunities

```bash
# Phase 1 - T001/T002 parallel:
T001 [P] Create __init__.py
T002 [P] Create shutdown_config.py

# Phase 2 - T003/T004 parallel:
T003 Add validation
T004 [P] Add ShutdownReason enum

# Phase 6 - T017/T018 parallel:
T017 [P] Update CLAUDE.md
T018 Run alpha-debug
```

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: US1 - Signal Handling
4. **STOP and VALIDATE**: SIGTERM triggers graceful shutdown
5. Ship MVP if needed

### Incremental Delivery

1. Setup + Foundational → ShutdownConfig ready
2. Add US1 → Signal handling works → Ship
3. Add US2 → Exception handling works → Ship
4. Add US3 → Full example available → Ship

---

## Summary

| Metric | Value |
|--------|-------|
| Total Tasks | 18 |
| Phase 1 (Setup) | 2 |
| Phase 2 (Foundation) | 2 |
| Phase 3 (US1) | 6 |
| Phase 4 (US2) | 3 |
| Phase 5 (US3) | 3 |
| Phase 6 (Polish) | 2 |
| Parallel Opportunities | 5 |
| MVP Scope | T001-T010 (10 tasks) |

---

## Implementation Status

**Completed**: 18/18 tasks (100%) ✅

**Alpha-Debug Fixes Applied**:
- B2: Added None check for `_shutdown_started_at` before elapsed calculation
- B4: Added try/except with fallback for unknown shutdown reasons
- B5: Added `asyncio.Lock` to prevent TOCTOU race condition
- B9: Added defensive `or []` for cache method returns
- B10: Added callback for fire-and-forget task exception handling
