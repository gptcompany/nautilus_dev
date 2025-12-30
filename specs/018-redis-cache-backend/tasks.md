# Tasks: Redis Cache Backend (Spec 018)

**Input**: Design documents from `/specs/018-redis-cache-backend/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

---

## Phase 1: Setup (Docker & Infrastructure)

**Purpose**: Redis running locally with AOF persistence

- [X] T001 Create Docker Compose file for Redis in config/cache/docker-compose.redis.yml
- [X] T002 [P] Create config/cache/__init__.py with module exports
- [X] T003 [P] Create .env.example with REDIS_HOST, REDIS_PORT, REDIS_PASSWORD

---

## Phase 2: Foundational (CacheConfig Factory)

**Purpose**: Production-ready CacheConfig that MUST be complete before integration

- [X] T004 Create CacheConfig factory with env var loading in config/cache/redis_config.py
- [X] T005 Add config validation (host format, port 1-65535, encoding msgpack/json) in config/cache/redis_config.py
- [X] T006 [P] Create debug config variant (JSON encoding) in config/cache/redis_config.py

**Checkpoint**: CacheConfig factory ready - integration can now begin

**Note**: TTL configuration marked YAGNI - NautilusTrader handles capacity limits via tick_capacity/bar_capacity

---

## Phase 3: User Story 1 - Redis Connection (Priority: P1) 🎯 MVP

**Goal**: TradingNode connects to Redis successfully with graceful error handling

**Independent Test**: `redis-cli ping` returns PONG, TradingNode starts without error

### Implementation for US1

- [X] T007 [US1] Create connection test script in scripts/test_redis_connection.py
- [X] T008 [US1] Add retry logic (max 5 retries, exponential backoff 1-32s) with graceful error handling in config/cache/redis_config.py
- [X] T009 [US1] Add health check function in config/cache/redis_config.py

**Checkpoint**: Redis connection verified - data persistence can now begin

---

## Phase 4: User Story 2 - Data Persistence (Priority: P2)

**Goal**: Positions, orders, accounts, instruments persist to Redis

**Independent Test**: Write position, restart TradingNode, position still exists

### Implementation for US2

- [X] T010 [US2] Create example TradingNode config (positions, orders, accounts, instruments) in config/examples/trading_node_redis.py
- [X] T011 [US2] Document key structure (trader-position, trader-order, trader-account, trader-instrument) in docs/018-redis-keys.md
- [X] T012 [US2] Create position persistence test script in scripts/test_position_persistence.py

**Checkpoint**: Data persistence verified - recovery can now be tested

---

## Phase 5: User Story 3 - Recovery Validation (Priority: P3)

**Goal**: State recovers correctly after TradingNode restart

**Independent Test**: Open position, kill TradingNode, restart, position recovered

### Implementation for US3

- [X] T013 [US3] Create recovery test script in scripts/test_recovery.py
- [X] T014 [US3] Add performance benchmark (read/write latency <1ms, 10K+ keys stress test) in scripts/benchmark_redis.py
- [X] T015 [US3] Document recovery workflow in docs/018-recovery-guide.md

**Checkpoint**: Full recovery workflow validated

---

## Phase 6: Polish & Documentation

**Purpose**: Production hardening and documentation

- [X] T016 [P] Update CLAUDE.md with Redis configuration section
- [X] T017 [P] Create monitoring guide in docs/018-redis-monitoring.md
- [ ] T018 Run alpha-debug verification on all config code

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Phase 1
- **US1 Connection (Phase 3)**: Depends on Phase 2
- **US2 Persistence (Phase 4)**: Depends on US1
- **US3 Recovery (Phase 5)**: Depends on US2
- **Polish (Phase 6)**: Depends on US3

### Parallel Opportunities

```bash
# Phase 1 - T002/T003 parallel:
T002 [P] Create __init__.py
T003 [P] Create .env.example

# Phase 2 - T006 parallel after T004-T005:
T006 [P] Create debug config

# Phase 6 - T016/T017 parallel:
T016 [P] Update CLAUDE.md
T017 [P] Create monitoring guide
```

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1: Docker setup
2. Complete Phase 2: CacheConfig factory
3. Complete Phase 3: US1 - Connection verified
4. **STOP and VALIDATE**: TradingNode connects to Redis
5. Ship MVP if needed

### Incremental Delivery

1. Setup + Foundational → CacheConfig ready
2. Add US1 → Connection works → Ship
3. Add US2 → Persistence works → Ship
4. Add US3 → Recovery validated → Ship

---

## Summary

| Metric | Value |
|--------|-------|
| Total Tasks | 18 |
| Phase 1 (Setup) | 3 |
| Phase 2 (Foundation) | 3 |
| Phase 3 (US1) | 3 |
| Phase 4 (US2) | 3 |
| Phase 5 (US3) | 3 |
| Phase 6 (Polish) | 3 |
| Parallel Opportunities | 5 |
| MVP Scope | T001-T009 (9 tasks) |

---

## Implementation Status

**Completed**: 17/18 tasks (94%)
**Remaining**: T018 (alpha-debug verification)
