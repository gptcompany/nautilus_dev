# Tasks: TradingNode Configuration

**Input**: Design documents from `/specs/014-tradingnode-configuration/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Included per Testing Strategy in plan.md (TDD Discipline from Constitution)

**Organization**: Tasks are grouped by functional requirement to enable independent implementation and testing.

## Format: `[ID] [Markers] [Story] Description`

### Task Markers
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US5)

---

## Phase 1: Setup (Project Structure)

**Purpose**: Create project structure and initialize configuration package

- [X] T001 Create config package structure per plan.md: `config/__init__.py`, `config/clients/__init__.py`
- [X] T002 Create .env.example template with all environment variables from spec.md FR-005
- [X] T003 [P] Create .env.production.example with production defaults
- [X] T004 [P] Add python-dotenv to project dependencies

**Checkpoint**: Project structure ready, environment templates available

---

## Phase 2: Foundational (Core Models)

**Purpose**: Base Pydantic models that ALL user stories depend on

**CRITICAL**: Complete this phase before ANY user story work

- [X] T005 Create ConfigEnvironment model in config/models.py (trader_id, environment)
- [X] T006 Create RedisConfig model in config/models.py (host, port, password, timeout)
- [X] T007 Create LoggingSettings model in config/models.py (log_level, log_directory, etc.)
- [X] T008 Create StreamingSettings model in config/models.py (catalog_path, flush_interval_ms, etc.)
- [X] T009 Create ExchangeCredentials base model in config/models.py (api_key, api_secret, testnet)
- [X] T010 Create test fixtures for configuration testing in tests/conftest.py

**Checkpoint**: Foundation ready - all core models implemented and testable

---

## Phase 3: User Story 1 - Base Configuration Factory (Priority: P1) 🎯 MVP

**Goal**: Implement TradingNodeSettings and TradingNodeConfigFactory core

**Independent Test**: `TradingNodeConfigFactory.from_settings(settings)` returns valid TradingNodeConfig

### Tests for User Story 1

- [X] T011 [P] [US1] Unit test for TradingNodeSettings validation in tests/test_config_models.py
- [X] T012 [P] [US1] Unit test for TradingNodeConfigFactory.from_settings() in tests/test_config_factory.py

### Implementation for User Story 1

- [X] T013 [US1] Create TradingNodeSettings composite model in config/models.py (combines all sub-configs)
- [X] T014 [US1] Create TradingNodeConfigFactory base class in config/factory.py
- [X] T015 [US1] Implement TradingNodeConfigFactory.from_settings() method in config/factory.py
- [X] T016 [US1] Implement TradingNodeSettings.from_env() classmethod in config/models.py

**Checkpoint**: User Story 1 complete - factory creates valid configs from settings

---

## Phase 4: User Story 2 - Cache Configuration with Redis (Priority: P2)

**Goal**: Implement Redis CacheConfig builder with msgpack encoding

**Independent Test**: CacheConfig validates and connects to Redis

### Tests for User Story 2

- [X] T017 [P] [US2] Unit test for CacheConfig builder in tests/test_config_cache.py
- [X] T018 [P] [US2] Integration test Redis connection in tests/integration/test_redis_connection.py

### Implementation for User Story 2

- [X] T019 [US2] Create CacheConfig builder function in config/cache.py
- [X] T020 [US2] Integrate CacheConfig builder into TradingNodeConfigFactory._build_cache_config() in config/factory.py

**Checkpoint**: User Story 2 complete - Redis cache configuration validated

---

## Phase 5: User Story 3 - Execution Engine Configuration (Priority: P3)

**Goal**: Implement LiveExecEngineConfig with reconciliation settings

**Independent Test**: LiveExecEngineConfig has valid reconciliation settings (lookback >= 60 min)

### Tests for User Story 3

- [X] T021 [P] [US3] Unit test for LiveExecEngineConfig builder in tests/test_config_execution.py
- [X] T022 [P] [US3] Unit test for reconciliation parameter validation in tests/test_config_execution.py

### Implementation for User Story 3

- [X] T023 [US3] Create LiveExecEngineConfig builder function in config/execution.py
- [X] T024 [US3] Integrate into TradingNodeConfigFactory._build_exec_engine_config() in config/factory.py
- [X] T025 [US3] Create LiveDataEngineConfig builder function in config/data.py
- [X] T026 [US3] Create LiveRiskEngineConfig builder function in config/risk.py

**Checkpoint**: User Story 3 complete - execution engine with reconciliation ready

---

## Phase 6: User Story 4 - Exchange Client Configurations (Priority: P4)

**Goal**: Implement Binance and Bybit client configuration builders

**Independent Test**: Client configs validate with testnet=true

### Tests for User Story 4

- [X] T027 [P] [US4] Unit test for BinanceCredentials model in tests/test_config_clients.py
- [X] T028 [P] [US4] Unit test for BybitCredentials model in tests/test_config_clients.py
- [X] T029 [P] [US4] Unit test for Binance client config builder in tests/test_config_clients.py
- [X] T030 [P] [US4] Unit test for Bybit client config builder in tests/test_config_clients.py

### Implementation for User Story 4

- [X] T031 [P] [US4] Create BinanceCredentials model in config/models.py (account_type, us)
- [X] T032 [P] [US4] Create BybitCredentials model in config/models.py (product_types, demo)
- [X] T033 [US4] Create Binance data/exec client config builder in config/clients/binance.py
- [X] T034 [US4] Create Bybit data/exec client config builder in config/clients/bybit.py
- [X] T035 [US4] Integrate client builders into TradingNodeConfigFactory._build_data_clients() in config/factory.py
- [X] T036 [US4] Integrate client builders into TradingNodeConfigFactory._build_exec_clients() in config/factory.py

**Checkpoint**: User Story 4 complete - exchange clients configured

---

## Phase 7: User Story 5 - Production & Testnet Factories (Priority: P5)

**Goal**: Implement create_production() and create_testnet() convenience methods

**Independent Test**: `TradingNodeConfigFactory.create_testnet()` returns config with testnet=True for all exchanges

### Tests for User Story 5

- [X] T037 [P] [US5] Unit test for create_production() in tests/test_config_factory.py
- [X] T038 [P] [US5] Unit test for create_testnet() in tests/test_config_factory.py
- [X] T039 [US5] Integration test TradingNode startup with factory config in tests/integration/test_trading_node_startup.py

### Implementation for User Story 5

- [X] T040 [US5] Implement TradingNodeConfigFactory.create_production() in config/factory.py
- [X] T041 [US5] Implement TradingNodeConfigFactory.create_testnet() in config/factory.py
- [X] T042 [US5] Create LoggingConfig builder in config/logging_config.py
- [X] T043 [US5] Create StreamingConfig builder in config/streaming.py
- [X] T044 [US5] Integrate logging and streaming builders into factory in config/factory.py

**Checkpoint**: User Story 5 complete - production and testnet factories ready

---

## Phase 8: Docker Integration

**Purpose**: Production deployment with Docker Compose

- [X] T045 Create Dockerfile for TradingNode container
- [X] T046 Create docker-compose.yml with Redis + TradingNode services
- [X] T047 [P] Create docker-compose.testnet.yml for testnet deployment
- [X] T048 [P] Update .gitignore with .env files and secrets

**Checkpoint**: Docker deployment ready

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and documentation

- [X] T049 [P] Export public API in config/__init__.py
- [X] T050 [P] Update quickstart.md with final usage examples
- [X] T051 Run ruff format and ruff check on config/
- [X] T052 Run alpha-debug verification on config/factory.py
- [X] T053 Verify all tests pass with coverage > 80% (use test-runner agent per constitution)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - US1 (Base Factory): Can proceed first - other stories depend on it
  - US2 (Cache): Depends on US1
  - US3 (Exec Engine): Depends on US1
  - US4 (Exchange Clients): Depends on US1
  - US5 (Prod/Testnet): Depends on US1-US4
- **Docker (Phase 8)**: Depends on Phase 7
- **Polish (Phase 9)**: Depends on all phases

### User Story Dependencies

```
US1 (Base Factory) ──┬──> US2 (Cache)
                     ├──> US3 (Exec Engine)
                     └──> US4 (Exchange Clients)
                              │
                              ▼
                          US5 (Prod/Testnet)
```

### Within Each User Story

- Tests MUST be written and FAIL before implementation (TDD)
- Model classes before builder functions
- Builders before factory integration
- Story complete before moving to next priority

### Parallel Opportunities

**Phase 1 (Setup)**:
- T003 + T004 can run in parallel

**Phase 2 (Foundational)**:
- Models can be added to same file sequentially (NOT parallel)

**Phase 4-7 (User Stories)**:
- Test tasks within same story marked [P] can run in parallel
- US2, US3, US4 can run in parallel after US1 completes (different files)

---

## Parallel Example: User Story 4 (Exchange Clients)

```bash
# Launch all tests for User Story 4 together:
Task: "Unit test for BinanceCredentials model in tests/test_config_clients.py"
Task: "Unit test for BybitCredentials model in tests/test_config_clients.py"
Task: "Unit test for Binance client config builder in tests/test_config_clients.py"
Task: "Unit test for Bybit client config builder in tests/test_config_clients.py"

# After tests fail, implement in parallel (different files):
Task: "Create Binance data/exec client config builder in config/clients/binance.py"
Task: "Create Bybit data/exec client config builder in config/clients/bybit.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: User Story 1 (Base Factory)
4. **STOP and VALIDATE**: Test factory creates valid TradingNodeConfig
5. Can use factory for basic configuration

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Basic factory working (MVP!)
3. Add User Story 2 → Redis cache configured
4. Add User Story 3 → Execution engine with reconciliation
5. Add User Story 4 → Exchange clients configured
6. Add User Story 5 → Production/testnet convenience methods
7. Add Docker → Deployment ready
8. Polish → Production ready

---

## Notes

- [P] tasks = different files, no dependencies
- Tests follow TDD: write FAILING test first, then implement
- Each user story should be independently testable
- Contracts (config_models.py, factory.py) already exist - move to config/ and refine
- Verify tests fail before implementing
- Commit after each task or logical group
- Constitution requires coverage > 80%
