---
description: "Task list template for feature implementation"
---

# Tasks: [FEATURE NAME]

**Input**: Design documents from `/specs/[###-feature-name]/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [Markers] [Story] Description`

### Task Markers
- **[P]**: Can run in parallel (different files, no dependencies)
- **[E]**: Alpha-Evolve trigger - use for complex algorithmic tasks requiring multi-implementation exploration
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)

### When to use [P] marker (CRITICAL)
- **USE [P]** only when tasks edit **different files** with no dependencies
- **NEVER use [P]** when multiple tasks edit the **same file** (they conflict)
- **Examples**:
  - ✅ `T001 [P] Create user.py` + `T002 [P] Create order.py` → different files, OK
  - ❌ `T001 [P] Add class A to models.py` + `T002 [P] Add class B to models.py` → same file, WRONG
  - ❌ `T001 [P] Write test_foo in test_x.py` + `T002 [P] Write test_bar in test_x.py` → same file, WRONG

### When to use [E] marker
- Core algorithm implementations (statistical, mathematical)
- Distance metrics, similarity calculations
- State machines with complex transition logic
- Performance-critical code needing optimization exploration

Include exact file paths in descriptions

## Path Conventions
- **NautilusTrader strategies**: `strategies/`, `tests/`
- **Indicators**: `indicators/`
- **Data pipelines**: `data/`
- Paths shown below assume single project - adjust based on plan.md structure

<!--
  ============================================================================
  IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

  The /speckit.tasks command MUST replace these with actual tasks based on:
  - User stories from spec.md (with their priorities P1, P2, P3...)
  - Feature requirements from plan.md
  - Entities from data-model.md
  - Endpoints from contracts/

  Tasks MUST be organized by user story so each story can be:
  - Implemented independently
  - Tested independently
  - Delivered as an MVP increment

  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan
- [ ] T002 Initialize Python project with dependencies
- [ ] T003 [P] Configure linting and formatting tools (ruff)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T004 Create strategy configuration model (Pydantic)
- [ ] T005 [P] Setup test fixtures with NautilusTrader TestKit
- [ ] T006 [P] Create base indicator setup
- [ ] T007 Configure BacktestNode for testing
- [ ] T008 Setup logging infrastructure

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - [Title] (Priority: P1) 🎯 MVP

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

**NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for strategy initialization in tests/test_[strategy].py
- [ ] T011 [P] [US1] Integration test with BacktestNode in tests/integration/test_[strategy].py

### Implementation for User Story 1

- [ ] T012 [P] [US1] Create strategy config in strategies/[name]/config.py
- [ ] T013 [P] [US1] Create indicator setup in strategies/[name]/indicators.py
- [ ] T014 [US1] Implement strategy logic in strategies/[name]/strategy.py (depends on T012, T013)
- [ ] T015 [US1] Implement signal generation
- [ ] T016 [US1] Add order management logic
- [ ] T017 [US1] Add logging for strategy operations

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - [Title] (Priority: P2)

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for [feature] in tests/test_[name].py
- [ ] T019 [P] [US2] Integration test in tests/integration/test_[name].py

### Implementation for User Story 2

- [ ] T020 [P] [US2] Create [component] in strategies/[name]/[component].py
- [ ] T021 [US2] Implement [Service] logic
- [ ] T022 [US2] Implement [feature]
- [ ] T023 [US2] Integrate with User Story 1 components (if needed)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - [Title] (Priority: P3)

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Unit test for [feature] in tests/test_[name].py
- [ ] T025 [P] [US3] Integration test in tests/integration/test_[name].py

### Implementation for User Story 3

- [ ] T026 [P] [US3] Create [component] in strategies/[name]/[component].py
- [ ] T027 [US3] Implement [feature] logic
- [ ] T028 [US3] Implement [endpoint/feature]

**Checkpoint**: All user stories should now be independently functional

---

[Add more user story phases as needed, following the same pattern]

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] TXXX [P] Documentation updates in docs/
- [ ] TXXX Code cleanup and refactoring
- [ ] TXXX Performance optimization across all stories
- [ ] TXXX [P] Additional unit tests (if requested) in tests/unit/
- [ ] TXXX Security hardening
- [ ] TXXX Run alpha-debug verification

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Config models before strategy logic
- Indicators before signal generation
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for strategy initialization in tests/test_[strategy].py"
Task: "Integration test with BacktestNode in tests/integration/test_[strategy].py"

# Launch all config/models for User Story 1 together:
Task: "Create strategy config in strategies/[name]/config.py"
Task: "Create indicator setup in strategies/[name]/indicators.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies (processed by /speckit.implement)
- [E] tasks = complex algorithms triggering alpha-evolve (processed by auto-alpha-debug hook)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
