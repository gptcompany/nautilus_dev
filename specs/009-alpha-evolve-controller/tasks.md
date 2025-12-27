# Tasks: Alpha-Evolve Controller & CLI

**Input**: Design documents from `/specs/009-alpha-evolve-controller/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓

**Tests**: Included per TDD discipline from constitution (tests written before implementation).

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [Markers] [Story] Description`

### Task Markers
- **[P]**: Can run in parallel (different files, no dependencies)
- **[E]**: Alpha-Evolve trigger - use for complex algorithmic tasks
- **[Story]**: Which user story this task belongs to (US1-US5)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and module structure

- [X] T001 Verify existing alpha_evolve module structure in scripts/alpha_evolve/__init__.py
- [X] T002 [P] Add click and tqdm dependencies to pyproject.toml (if not present)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core dataclasses and entities that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Create EvolutionStatus enum in scripts/alpha_evolve/controller.py
- [X] T004 Create StopCondition dataclass in scripts/alpha_evolve/controller.py
- [X] T005 Create EvolutionProgress dataclass in scripts/alpha_evolve/controller.py
- [X] T006 Create ProgressEvent and ProgressEventType in scripts/alpha_evolve/controller.py
- [X] T007 Create EvolutionResult dataclass in scripts/alpha_evolve/controller.py
- [X] T008 Create MutationRequest dataclass in scripts/alpha_evolve/mutator.py
- [X] T009 Create MutationResponse dataclass in scripts/alpha_evolve/mutator.py
- [X] T010 Create Mutator protocol in scripts/alpha_evolve/mutator.py

**Checkpoint**: Foundation ready - core entities defined, user story implementation can begin ✓

---

## Phase 3: User Story 1 - Evolution Loop Execution (Priority: P1) 🎯 MVP

**Goal**: Execute configurable evolution loop that iteratively mutates and evaluates strategies

**Independent Test**: Run single iteration, verify seed → mutate → evaluate → store cycle completes

### Tests for User Story 1

- [X] T011 [US1] Write test_controller_init in tests/alpha_evolve/test_controller.py
- [X] T012 [US1] Write test_run_single_iteration in tests/alpha_evolve/test_controller.py
- [X] T013 [US1] Write test_run_stops_at_iteration_limit in tests/alpha_evolve/test_controller.py
- [X] T014 [US1] Write test_continues_on_evaluation_failure in tests/alpha_evolve/test_controller.py
- [X] T015 [US1] Write test_stop_condition_target_fitness in tests/alpha_evolve/test_controller.py
- [X] T016 [US1] Write test_progress_event_emission in tests/alpha_evolve/test_controller.py

### Implementation for User Story 1

- [X] T017 [US1] Implement EvolutionController.__init__() in scripts/alpha_evolve/controller.py
- [X] T018 [US1] Implement EvolutionController._load_seed_strategy() in scripts/alpha_evolve/controller.py
- [X] T019 [E] [US1] Implement EvolutionController.run() main loop in scripts/alpha_evolve/controller.py
- [X] T020 [US1] Implement EvolutionController._run_iteration() in scripts/alpha_evolve/controller.py
- [X] T021 [US1] Implement EvolutionController._check_stop_conditions() in scripts/alpha_evolve/controller.py
- [X] T022 [US1] Implement EvolutionController._emit_progress() in scripts/alpha_evolve/controller.py
- [X] T023 [US1] Implement EvolutionController.get_progress() in scripts/alpha_evolve/controller.py

**Checkpoint**: Evolution loop executes for configured iterations, stores results, emits progress ✓

---

## Phase 4: User Story 2 - Parent Selection Strategy (Priority: P1)

**Goal**: Implement intelligent parent selection balancing exploitation with exploration

**Independent Test**: Run 1000 selections, verify distribution matches 10% elite / 70% exploit / 20% explore

### Tests for User Story 2

- [X] T024 [US2] Write test_select_parent_mode_distribution in tests/alpha_evolve/test_controller.py
- [X] T025 [US2] Write test_select_parent_elite in tests/alpha_evolve/test_controller.py
- [X] T026 [US2] Write test_select_parent_exploit in tests/alpha_evolve/test_controller.py
- [X] T027 [US2] Write test_select_parent_explore in tests/alpha_evolve/test_controller.py
- [X] T028 [US2] Write test_select_parent_empty_store in tests/alpha_evolve/test_controller.py

### Implementation for User Story 2

- [X] T029 [US2] Implement EvolutionController._select_parent_mode() in scripts/alpha_evolve/controller.py
- [X] T030 [US2] Implement EvolutionController._select_parent() in scripts/alpha_evolve/controller.py
- [X] T031 [US2] Integrate parent selection into _run_iteration() in scripts/alpha_evolve/controller.py

**Checkpoint**: Parent selection works with correct distribution, integrates into loop ✓

---

## Phase 5: User Story 3 - LLM Mutation Integration (Priority: P1)

**Goal**: Request code mutations from LLM with parent context and retry logic

**Independent Test**: Request mutation, verify EVOLVE-BLOCK is modified, syntax validated

### Tests for User Story 3

- [X] T032 [P] [US3] Write test_mutation_request_creation in tests/alpha_evolve/test_mutator.py
- [X] T033 [P] [US3] Write test_mutation_response_success in tests/alpha_evolve/test_mutator.py
- [X] T034 [P] [US3] Write test_mutation_response_syntax_error in tests/alpha_evolve/test_mutator.py
- [X] T035 [US3] Write test_llm_mutator_retry_on_syntax_error in tests/alpha_evolve/test_mutator.py
- [X] T036 [US3] Write test_llm_mutator_max_retries in tests/alpha_evolve/test_mutator.py
- [X] T037 [US3] Write test_mutation_prompt_includes_metrics in tests/alpha_evolve/test_mutator.py

### Implementation for User Story 3

- [X] T038 [US3] Implement LLMMutator.__init__() in scripts/alpha_evolve/mutator.py
- [X] T039 [US3] Implement LLMMutator._build_prompt() with mutation logging (FR-013) in scripts/alpha_evolve/mutator.py
- [X] T040 [E] [US3] Implement LLMMutator.mutate() with retry logic in scripts/alpha_evolve/mutator.py
- [X] T041 [US3] Implement LLMMutator._validate_mutation() in scripts/alpha_evolve/mutator.py
- [X] T042 [US3] Implement LLMMutator._handle_unavailable() for graceful LLM degradation in scripts/alpha_evolve/mutator.py
- [X] T043 [US3] Integrate LLMMutator into EvolutionController._request_mutation() in scripts/alpha_evolve/controller.py

**Checkpoint**: Mutations work, syntax validation works, retries work, integrates into loop ✓

---

## Phase 6: User Story 4 - CLI Interface (Priority: P1)

**Goal**: Command-line interface to start, monitor, and manage evolution runs

**Independent Test**: Run CLI commands, verify expected output and behavior

### Tests for User Story 4

- [X] T044 [P] [US4] Write test_cli_start_basic in tests/alpha_evolve/test_cli.py
- [X] T045 [P] [US4] Write test_cli_status_json_output in tests/alpha_evolve/test_cli.py
- [X] T046 [P] [US4] Write test_cli_best_top_k in tests/alpha_evolve/test_cli.py
- [X] T047 [P] [US4] Write test_cli_export_strategy in tests/alpha_evolve/test_cli.py
- [X] T048 [P] [US4] Write test_cli_list_experiments in tests/alpha_evolve/test_cli.py

### Implementation for User Story 4

- [X] T049 [US4] Create CLI group and global options in scripts/alpha_evolve/cli.py
- [X] T050 [US4] Implement evolve start command in scripts/alpha_evolve/cli.py
- [X] T051 [US4] Implement evolve status command in scripts/alpha_evolve/cli.py
- [X] T052 [US4] Implement evolve best command in scripts/alpha_evolve/cli.py
- [X] T053 [US4] Implement evolve export command in scripts/alpha_evolve/cli.py
- [X] T054 [US4] Implement evolve stop command in scripts/alpha_evolve/cli.py
- [X] T055 [US4] Implement evolve list command in scripts/alpha_evolve/cli.py
- [X] T056 [US4] Add CLI entry point to pyproject.toml

**Checkpoint**: All CLI commands work, proper exit codes, JSON output where specified ✓

---

## Phase 7: User Story 5 - Experiment Management (Priority: P2)

**Goal**: Organize evolution runs into named experiments with resume capability

**Independent Test**: Create experiments, verify isolation, resume from checkpoint

### Tests for User Story 5

- [X] T057 [US5] Write test_experiment_isolation in tests/alpha_evolve/test_controller.py
- [X] T058 [US5] Write test_resume_paused_experiment in tests/alpha_evolve/test_controller.py
- [X] T059 [US5] Write test_resume_adds_iterations in tests/alpha_evolve/test_controller.py
- [X] T060 [P] [US5] Write test_cli_resume_command in tests/alpha_evolve/test_cli.py

### Implementation for User Story 5

- [X] T061 [US5] Implement EvolutionController.stop() in scripts/alpha_evolve/controller.py
- [X] T062 [US5] Implement EvolutionController.resume() in scripts/alpha_evolve/controller.py
- [X] T063 [US5] Implement EvolutionController._load_checkpoint() in scripts/alpha_evolve/controller.py
- [X] T064 [US5] Implement evolve resume command in scripts/alpha_evolve/cli.py

**Checkpoint**: Experiments isolated, resume works, checkpoint persistence verified ✓

---

## Phase 8: Integration Testing

**Purpose**: End-to-end validation across all user stories

- [X] T065 Write test_evolution_loop_full_cycle in tests/alpha_evolve/test_controller_integration.py
- [X] T066 Write test_evolution_stop_and_resume in tests/alpha_evolve/test_controller_integration.py
- [X] T067 Write test_cli_full_workflow in tests/alpha_evolve/test_cli.py

**Checkpoint**: All user stories work together, full evolution cycle verified ✓

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T068 [P] Add comprehensive docstrings to controller.py
- [X] T069 [P] Add comprehensive docstrings to mutator.py
- [X] T070 [P] Add comprehensive docstrings to cli.py
- [X] T071 Run ruff check and format on all new files
- [ ] T072 Run alpha-debug verification on controller.py
- [ ] T073 Run alpha-debug verification on mutator.py
- [X] T074 Update alpha_evolve module __init__.py exports

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational - Core loop MVP
- **User Story 2 (Phase 4)**: Depends on Foundational - Can parallel with US1 initially
- **User Story 3 (Phase 5)**: Depends on Foundational - Can parallel with US1/US2 initially
- **User Story 4 (Phase 6)**: Depends on US1 complete (needs controller to wrap)
- **User Story 5 (Phase 7)**: Depends on US1 + US4 complete (needs stop/resume to exist)
- **Integration (Phase 8)**: Depends on all US complete
- **Polish (Phase 9)**: Depends on Integration

### User Story Dependencies

```
              ┌────────────────┐
              │  Foundational  │
              │   (Phase 2)    │
              └───────┬────────┘
                      │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
     ┌────────┐ ┌────────┐ ┌────────┐
     │  US1   │ │  US2   │ │  US3   │
     │ Loop   │ │ Select │ │ Mutate │
     └────┬───┘ └────┬───┘ └────┬───┘
          │          │          │
          └──────────┼──────────┘
                     │
                     ▼
               ┌──────────┐
               │   US4    │
               │   CLI    │
               └────┬─────┘
                    │
                    ▼
               ┌──────────┐
               │   US5    │
               │ Exp Mgmt │
               └──────────┘
```

### Parallel Opportunities

**Phase 2 (Foundational)**:
- T003-T010 are sequential (all modify same files: controller.py and mutator.py)

**Phase 3 (US1 Tests)**:
- All test tasks can run together as they're in same test file

**Phase 4-5 (US2/US3)**:
- US2 and US3 tests/implementation can overlap (different concerns)
- T032-T034 can run in parallel (within mutator tests)

**Phase 6 (US4 Tests)**:
- T044-T048 can run in parallel (CLI command tests)

---

## Parallel Example: User Story 3 (Mutation)

```bash
# Launch tests in parallel (different test functions, same file):
Task: "Write test_mutation_request_creation in tests/alpha_evolve/test_mutator.py"
Task: "Write test_mutation_response_success in tests/alpha_evolve/test_mutator.py"
Task: "Write test_mutation_response_syntax_error in tests/alpha_evolve/test_mutator.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup ✓
2. Complete Phase 2: Foundational (dataclasses)
3. Complete Phase 3: User Story 1 (Evolution Loop)
4. **STOP and VALIDATE**: Run single-iteration evolution
5. Controller works → MVP achieved!

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 (Loop) → Can run evolution manually
3. Add US2 (Selection) → Evolution has intelligent selection
4. Add US3 (Mutation) → Evolution uses LLM mutations
5. Add US4 (CLI) → Users can run via command line
6. Add US5 (Experiments) → Users can organize and resume runs

### Suggested MVP Scope

**MVP = Foundational + US1 + US2 + US3**

This gives a working evolution loop with:
- Parent selection (elite/exploit/explore)
- LLM mutations
- Backtest evaluation
- Hall-of-fame storage

CLI and experiment management are nice-to-have but not required for MVP.

---

## Summary

| Phase | Tasks | Parallel Tasks | Story |
|-------|-------|----------------|-------|
| Setup | 2 | 1 | - |
| Foundational | 8 | 0 | - |
| US1 (Loop) | 13 | 0 | MVP Core |
| US2 (Selection) | 8 | 0 | MVP |
| US3 (Mutation) | 12 | 3 | MVP |
| US4 (CLI) | 13 | 5 | Post-MVP |
| US5 (Experiments) | 8 | 1 | Post-MVP |
| Integration | 3 | 0 | - |
| Polish | 7 | 3 | - |
| **Total** | **74** | **13** | - |

---

## Notes

- [P] tasks = different files, can run in parallel
- [E] tasks = complex algorithms, trigger alpha-evolve for multi-approach generation
- [Story] label maps task to user story for traceability
- All tests written BEFORE implementation (TDD)
- Commit after each task or logical group
- Stop at any checkpoint to validate independently
