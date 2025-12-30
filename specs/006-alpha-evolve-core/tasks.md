# Tasks: Alpha-Evolve Core Infrastructure

**Input**: Design documents from `/specs/006-alpha-evolve-core/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Included (TDD approach per project constitution)

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [Markers] [Story] Description`

### Task Markers
- **[P]**: Can run in parallel (different files, no dependencies)
- **[E]**: Alpha-Evolve trigger - use for complex algorithmic tasks
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create project structure and package setup

- [x] T001 Create package directory at scripts/alpha_evolve/
- [x] T002 Create package __init__.py with exports at scripts/alpha_evolve/__init__.py
- [x] T003 [P] Create test package at tests/alpha_evolve/__init__.py
- [x] T004 [P] Create test fixtures at tests/alpha_evolve/conftest.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared fixtures and utilities needed by all user stories

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Create sample strategy code fixture with EVOLVE-BLOCK markers in tests/alpha_evolve/conftest.py
- [x] T006 Create temp database fixture for store tests in tests/alpha_evolve/conftest.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - EVOLVE-BLOCK Patching System (Priority: P1) 🎯 MVP

**Goal**: Surgically replace code within EVOLVE-BLOCK markers while preserving strategy structure

**Independent Test**: Provide sample strategy code with markers and verify correct replacement with indentation preservation

### Tests for User Story 1

**NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T007 [P] [US1] Write test_apply_patch_full_replace in tests/alpha_evolve/test_patching.py
- [x] T008 [P] [US1] Write test_apply_patch_block_replace in tests/alpha_evolve/test_patching.py
- [x] T009 [P] [US1] Write test_apply_patch_preserves_indentation in tests/alpha_evolve/test_patching.py
- [x] T010 [P] [US1] Write test_apply_patch_multiple_blocks in tests/alpha_evolve/test_patching.py
- [x] T011 [P] [US1] Write test_extract_blocks in tests/alpha_evolve/test_patching.py
- [x] T012 [P] [US1] Write test_validate_syntax_valid in tests/alpha_evolve/test_patching.py
- [x] T013 [P] [US1] Write test_validate_syntax_invalid in tests/alpha_evolve/test_patching.py
- [x] T013a [P] [US1] Write test_apply_patch_malformed_markers in tests/alpha_evolve/test_patching.py

### Implementation for User Story 1

- [x] T014 [US1] Implement BLOCK_RE regex pattern in scripts/alpha_evolve/patching.py
- [x] T015 [US1] Implement apply_patch() function in scripts/alpha_evolve/patching.py
- [x] T016 [US1] Implement extract_blocks() function in scripts/alpha_evolve/patching.py
- [x] T017 [US1] Implement validate_syntax() function in scripts/alpha_evolve/patching.py
- [x] T018 [US1] Export patching functions in scripts/alpha_evolve/__init__.py

**Checkpoint**: User Story 1 should be fully functional - run `uv run pytest tests/alpha_evolve/test_patching.py -v`

---

## Phase 4: User Story 2 - SQLite Hall-of-Fame Store (Priority: P1)

**Goal**: Persist evolved strategies with fitness metrics, support parent selection and population management

**Independent Test**: Insert strategies, query top_k, sample for parent selection, verify pruning

### Tests for User Story 2

**NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T019 [P] [US2] Write test_program_store_insert_and_get in tests/alpha_evolve/test_store.py
- [x] T020 [P] [US2] Write test_program_store_update_metrics in tests/alpha_evolve/test_store.py
- [x] T021 [P] [US2] Write test_program_store_top_k in tests/alpha_evolve/test_store.py
- [x] T022 [P] [US2] Write test_program_store_sample_elite in tests/alpha_evolve/test_store.py
- [x] T023 [P] [US2] Write test_program_store_sample_exploit in tests/alpha_evolve/test_store.py
- [x] T024 [P] [US2] Write test_program_store_sample_explore in tests/alpha_evolve/test_store.py
- [x] T025 [P] [US2] Write test_program_store_prune in tests/alpha_evolve/test_store.py
- [x] T025a [P] [US2] Write test_program_store_atomic_insert_prune in tests/alpha_evolve/test_store.py
- [x] T026 [P] [US2] Write test_program_store_get_lineage in tests/alpha_evolve/test_store.py
- [x] T027 [P] [US2] Write test_program_store_count in tests/alpha_evolve/test_store.py

### Implementation for User Story 2

- [x] T028 [US2] Implement FitnessMetrics dataclass in scripts/alpha_evolve/store.py
- [x] T029 [US2] Implement Program dataclass in scripts/alpha_evolve/store.py
- [x] T030 [US2] Implement ProgramStore.__init__() with schema creation in scripts/alpha_evolve/store.py
- [x] T031 [US2] Implement ProgramStore.insert() in scripts/alpha_evolve/store.py
- [x] T032 [US2] Implement ProgramStore.update_metrics() in scripts/alpha_evolve/store.py
- [x] T033 [US2] Implement ProgramStore.get() in scripts/alpha_evolve/store.py
- [x] T034 [US2] Implement ProgramStore.top_k() in scripts/alpha_evolve/store.py
- [x] T035 [E] [US2] Implement ProgramStore.sample() with elite/exploit/explore strategies in scripts/alpha_evolve/store.py
- [x] T036 [US2] Implement ProgramStore.prune() in scripts/alpha_evolve/store.py
- [x] T037 [US2] Implement ProgramStore.get_lineage() in scripts/alpha_evolve/store.py
- [x] T038 [US2] Implement ProgramStore.count() in scripts/alpha_evolve/store.py
- [x] T039 [US2] Export store classes in scripts/alpha_evolve/__init__.py

**Checkpoint**: User Story 2 should be fully functional - run `uv run pytest tests/alpha_evolve/test_store.py -v`

---

## Phase 5: User Story 3 - Evolution Configuration (Priority: P2)

**Goal**: YAML configuration for evolution parameters with validation and defaults

**Independent Test**: Load config, verify parameters accessible with correct types and defaults

### Tests for User Story 3

**NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T040 [P] [US3] Write test_config_load_defaults in tests/alpha_evolve/test_config.py
- [x] T041 [P] [US3] Write test_config_load_from_yaml in tests/alpha_evolve/test_config.py
- [x] T042 [P] [US3] Write test_config_partial_override in tests/alpha_evolve/test_config.py
- [x] T043 [P] [US3] Write test_config_validation_error in tests/alpha_evolve/test_config.py
- [x] T044 [P] [US3] Write test_config_env_override in tests/alpha_evolve/test_config.py

### Implementation for User Story 3

- [x] T045 [US3] Create default config.yaml at scripts/alpha_evolve/config.yaml
- [x] T046 [US3] Implement EvolutionConfig class with Pydantic BaseSettings in scripts/alpha_evolve/config.py
- [x] T047 [US3] Implement EvolutionConfig.load() class method in scripts/alpha_evolve/config.py
- [x] T048 [US3] Implement validation rules in EvolutionConfig in scripts/alpha_evolve/config.py
- [x] T049 [US3] Export config class in scripts/alpha_evolve/__init__.py

**Checkpoint**: User Story 3 should be fully functional - run `uv run pytest tests/alpha_evolve/test_config.py -v`

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Integration testing and final cleanup

- [x] T050 [P] Write integration test patch->insert->sample cycle in tests/alpha_evolve/test_integration.py
- [x] T051 [P] Write integration test insert->update_metrics->top_k in tests/alpha_evolve/test_integration.py
- [x] T052 Verify all exports in scripts/alpha_evolve/__init__.py
- [x] T053 Run full test suite with coverage in tests/alpha_evolve/
- [x] T054 Run alpha-debug verification on scripts/alpha_evolve/

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Stories (Phases 3-5)**: All depend on Foundational completion
  - US1 and US3 can run in parallel (no cross-dependencies)
  - US2 can also run in parallel with US1 and US3
- **Polish (Phase 6)**: Depends on all user stories complete

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies on other stories - FULLY INDEPENDENT
- **User Story 2 (P1)**: No dependencies on other stories - FULLY INDEPENDENT
- **User Story 3 (P2)**: No dependencies on other stories - FULLY INDEPENDENT

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Implementation follows test order (data classes → methods → exports)
- Story complete before marking checkpoint

### Parallel Opportunities

**Setup Phase:**
```bash
# These can run in parallel (different files):
Task T003: tests/alpha_evolve/__init__.py
Task T004: tests/alpha_evolve/conftest.py
```

**User Story 1 Tests (all parallel - different test functions):**
```bash
# Launch all tests for US1 together:
Tasks T007-T013: All in tests/alpha_evolve/test_patching.py
# NOTE: Same file, but write in single session
```

**User Story 2 Tests (all parallel - different test functions):**
```bash
# Launch all tests for US2 together:
Tasks T019-T027: All in tests/alpha_evolve/test_store.py
```

**User Story 3 Tests (all parallel - different test functions):**
```bash
# Launch all tests for US3 together:
Tasks T040-T044: All in tests/alpha_evolve/test_config.py
```

**Cross-Story Parallelism:**
```bash
# With multiple developers:
Developer A: User Story 1 (patching.py + test_patching.py)
Developer B: User Story 2 (store.py + test_store.py)
Developer C: User Story 3 (config.py + test_config.py)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T006)
3. Complete Phase 3: User Story 1 (T007-T018)
4. **STOP and VALIDATE**: Run `uv run pytest tests/alpha_evolve/test_patching.py -v`
5. Patching system is now usable independently

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Patching works → Can test mutations
3. Add User Story 2 → Store works → Can persist strategies
4. Add User Story 3 → Config works → Can tune parameters
5. Polish → Integration tested → Production ready

### Recommended Order

Given all stories are P1 priority, implement in this order:
1. **US1 (Patching)**: Core dependency for evolution system
2. **US2 (Store)**: Needed for population persistence
3. **US3 (Config)**: Tuning parameters (can be hardcoded initially)

---

## Notes

- [P] tasks = different files or can be batched (processed by /speckit.implement)
- [E] tasks = complex algorithms triggering alpha-evolve (T035: sample strategies)
- [Story] label maps task to user story for traceability
- Verify tests fail before implementing
- Commit after each phase checkpoint
- All user stories are FULLY INDEPENDENT - no cross-dependencies
