# Tasks: NautilusTrader Auto-Update Pipeline

**Input**: Design documents from `/specs/023-nautilus-auto-update/`
**Prerequisites**: plan.md (required), spec.md (required), data-model.md, contracts/cli-interface.md, research.md, quickstart.md

**Tests**: Unit tests included (TDD approach specified in constitution.md)

**Organization**: Tasks grouped by user story. US1-US2 = MVP (Phase 1), US3-US4 = Phase 2, US5-US6 = Phase 3.

## Format: `[ID] [Markers] [Story] Description`

### Task Markers
- **[P]**: Can run in parallel (different files, no dependencies)
- **[E]**: Alpha-Evolve trigger (complex algorithms)
- **[Story]**: User story mapping (US1, US2, US3, US4, US5, US6)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and module structure

- [X] T001 Create module structure in scripts/auto_update/__init__.py
- [X] T002 [P] Add pydantic and click dependencies to pyproject.toml
- [X] T003 [P] Create test directory structure at tests/scripts/auto_update/__init__.py

**Checkpoint**: Module skeleton ready

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement Severity, Recommendation, ConfidenceLevel enums in scripts/auto_update/models.py
- [X] T005 Implement OpenIssue and ChangelogData models in scripts/auto_update/models.py
- [X] T006 Implement BreakingChange and AffectedFile models in scripts/auto_update/models.py
- [X] T007 Implement ImpactReport model with validation logic in scripts/auto_update/models.py
- [X] T008 Implement TestResult and UpdateResult models in scripts/auto_update/models.py
- [X] T009 Implement DispatchResult model in scripts/auto_update/models.py
- [X] T010 Implement AutoUpdateConfig model in scripts/auto_update/models.py
- [X] T011 [P] Create test fixtures for models in tests/scripts/auto_update/conftest.py
- [X] T012 [P] Add unit tests for all models in tests/scripts/auto_update/test_models.py

**Checkpoint**: Foundation ready - all Pydantic models validated

---

## Phase 3: User Story 1 - Changelog Monitoring (P1 - MVP) 🎯

**Goal**: Parse N8N-generated changelog.json and extract version info

**Independent Test**: `python -m scripts.auto_update check` shows current/latest version

### Tests for User Story 1

- [X] T013 [P] [US1] Unit test parse_changelog in tests/scripts/auto_update/test_parser.py
- [X] T014 [P] [US1] Unit test extract_breaking_changes in tests/scripts/auto_update/test_parser.py
- [X] T015 [P] [US1] Unit test detect_update_available in tests/scripts/auto_update/test_parser.py

### Implementation for User Story 1

- [X] T016 [US1] Implement load_changelog_json function in scripts/auto_update/parser.py
- [X] T017 [US1] Implement parse_changelog function returning ChangelogData in scripts/auto_update/parser.py
- [X] T018 [US1] Implement extract_breaking_changes function in scripts/auto_update/parser.py
- [X] T019 [US1] Implement detect_update_available function in scripts/auto_update/parser.py
- [X] T020 [US1] Add CLI `check` command skeleton in scripts/auto_update/cli.py

**Checkpoint**: US1 complete - `check` command shows changelog info

---

## Phase 4: User Story 2 - Breaking Change Detection (P1 - MVP) 🎯

**Goal**: Grep codebase for affected files and generate ImpactReport

**Independent Test**: `python -m scripts.auto_update check --verbose` shows affected files

### Tests for User Story 2

- [X] T021 [P] [US2] Unit test grep_codebase in tests/scripts/auto_update/test_analyzer.py
- [X] T022 [P] [US2] Unit test classify_severity in tests/scripts/auto_update/test_analyzer.py
- [X] T023 [P] [US2] Unit test calculate_confidence in tests/scripts/auto_update/test_analyzer.py
- [X] T024 [P] [US2] Unit test generate_impact_report in tests/scripts/auto_update/test_analyzer.py

### Implementation for User Story 2

- [X] T025 [US2] Implement grep_codebase function using subprocess/ripgrep in scripts/auto_update/analyzer.py
- [X] T026 [US2] Implement classify_severity function based on breaking change patterns in scripts/auto_update/analyzer.py
- [X] T027 [E] [US2] Implement calculate_confidence scoring algorithm in scripts/auto_update/analyzer.py
- [X] T028 [US2] Implement generate_impact_report function in scripts/auto_update/analyzer.py
- [X] T029 [US2] Integrate analyzer with CLI `check --verbose` in scripts/auto_update/cli.py
- [X] T030 [US2] Add JSON output format for `check --format json` in scripts/auto_update/cli.py

**Checkpoint**: US1+US2 complete - MVP ready for manual usage

---

## Phase 5: User Story 3 - Dependency Update (P2)

**Goal**: Auto-update pyproject.toml, run uv sync, create update branch

**Independent Test**: `python -m scripts.auto_update update --dry-run` shows update plan

### Tests for User Story 3

- [ ] T031 [P] [US3] Unit test update_pyproject_version in tests/scripts/auto_update/test_updater.py
- [ ] T032 [P] [US3] Unit test run_uv_sync in tests/scripts/auto_update/test_updater.py
- [ ] T033 [P] [US3] Unit test git_create_branch in tests/scripts/auto_update/test_git_ops.py
- [ ] T034 [P] [US3] Unit test git_commit_changes in tests/scripts/auto_update/test_git_ops.py
- [ ] T035 [P] [US3] Unit test git_push_branch in tests/scripts/auto_update/test_git_ops.py
- [ ] T036 [P] [US3] Unit test create_pr in tests/scripts/auto_update/test_git_ops.py

### Implementation for User Story 3

- [ ] T037 [US3] Implement update_pyproject_version in scripts/auto_update/updater.py
- [ ] T038 [US3] Implement run_uv_sync wrapper in scripts/auto_update/updater.py
- [ ] T039 [US3] Implement git_create_branch in scripts/auto_update/git_ops.py
- [ ] T040 [US3] Implement git_commit_changes in scripts/auto_update/git_ops.py
- [ ] T041 [US3] Implement git_push_branch in scripts/auto_update/git_ops.py
- [ ] T042 [US3] Implement create_pr using gh CLI in scripts/auto_update/git_ops.py
- [ ] T043 [US3] Implement auto_update orchestrator function in scripts/auto_update/updater.py
- [ ] T044 [US3] Add CLI `update` command with --dry-run, --force, --no-pr in scripts/auto_update/cli.py

**Checkpoint**: US3 complete - can auto-update dependencies and create PR

---

## Phase 6: User Story 4 - Compatibility Validation (P2)

**Goal**: Run pytest and capture test results, block merge on failure

**Independent Test**: `python -m scripts.auto_update update` runs tests and reports pass/fail

### Tests for User Story 4

- [ ] T045 [P] [US4] Unit test run_pytest in tests/scripts/auto_update/test_validator.py
- [ ] T046 [P] [US4] Unit test parse_test_results in tests/scripts/auto_update/test_validator.py
- [ ] T047 [P] [US4] Integration test full update flow in tests/scripts/auto_update/test_integration.py

### Implementation for User Story 4

- [ ] T048 [US4] Implement run_pytest using subprocess in scripts/auto_update/validator.py
- [ ] T049 [US4] Implement parse_test_results from pytest JSON output in scripts/auto_update/validator.py
- [ ] T050 [US4] Implement validate_update orchestrator in scripts/auto_update/validator.py
- [ ] T051 [US4] Integrate validator into CLI `update` command in scripts/auto_update/cli.py
- [ ] T052 [US4] Add test result annotation to PR description in scripts/auto_update/git_ops.py

**Checkpoint**: US3+US4 complete - full auto-update with validation

---

## Phase 7: User Story 5 - Auto-Fix Simple Changes (P3)

**Goal**: Apply simple regex-based fixes (import renames, method renames)

**Independent Test**: Update with simple breaking change auto-fixes affected files

### Tests for User Story 5

- [ ] T053 [P] [US5] Unit test apply_import_rename in tests/scripts/auto_update/test_auto_fix.py
- [ ] T054 [P] [US5] Unit test apply_method_rename in tests/scripts/auto_update/test_auto_fix.py

### Implementation for User Story 5

- [ ] T055 [US5] Create auto_fix module at scripts/auto_update/auto_fix.py
- [ ] T056 [US5] Implement apply_import_rename using regex in scripts/auto_update/auto_fix.py
- [ ] T057 [US5] Implement apply_method_rename using regex in scripts/auto_update/auto_fix.py
- [ ] T058 [US5] Implement auto_fix_files orchestrator in scripts/auto_update/auto_fix.py
- [ ] T059 [US5] Integrate auto-fix into update flow in scripts/auto_update/updater.py

**Checkpoint**: US5 complete - simple changes auto-fixed

---

## Phase 8: User Story 6 - Claude Code Integration (P3)

**Goal**: Dispatch Claude Code agent for complex fixes, send notifications

**Independent Test**: `python -m scripts.auto_update dispatch` spawns Claude agent

### Tests for User Story 6

- [ ] T060 [P] [US6] Unit test build_task_prompt in tests/scripts/auto_update/test_dispatcher.py
- [ ] T061 [P] [US6] Unit test dispatch_claude_code in tests/scripts/auto_update/test_dispatcher.py
- [ ] T062 [P] [US6] Unit test send_discord_notification in tests/scripts/auto_update/test_notifier.py
- [ ] T063 [P] [US6] Unit test send_email_notification in tests/scripts/auto_update/test_notifier.py

### Implementation for User Story 6

- [ ] T064 [US6] Implement build_task_prompt with ImpactReport context in scripts/auto_update/dispatcher.py
- [ ] T065 [US6] Implement dispatch_claude_code using subprocess in scripts/auto_update/dispatcher.py
- [ ] T066 [US6] Implement monitor_agent_completion in scripts/auto_update/dispatcher.py
- [ ] T067 [US6] Implement send_discord_notification with rich embeds in scripts/auto_update/notifier.py
- [ ] T068 [US6] Implement send_email_notification fallback in scripts/auto_update/notifier.py
- [ ] T069 [US6] Add CLI `dispatch` command in scripts/auto_update/cli.py
- [ ] T070 [US6] Add CLI `notify` command in scripts/auto_update/cli.py
- [ ] T071 [US6] Add CLI `status` command in scripts/auto_update/cli.py
- [ ] T072 [US6] Implement __main__.py entry point in scripts/auto_update/__main__.py

**Checkpoint**: Full pipeline complete - all user stories implemented

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Integration, documentation, and final validation

- [ ] T073 [P] Create GitHub Actions workflow at .github/workflows/nautilus-update-check.yml
- [ ] T074 [P] Add cron job documentation to quickstart.md
- [ ] T075 End-to-end integration test in tests/scripts/auto_update/test_integration.py
- [ ] T076 Run alpha-debug verification on all modules
- [ ] T077 Update CLAUDE.md with auto-update module documentation
- [ ] T078 Code cleanup and ruff formatting
- [ ] T079 [P] Verify test coverage >= 80% with pytest-cov in tests/scripts/auto_update/
- [ ] T080 [P] Run mypy type checking on scripts/auto_update/

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup) ─┐
                 ├─> Phase 2 (Foundational) ─┬─> Phase 3 (US1) ─┬─> Phase 4 (US2) ─┬─> [MVP DONE]
                 │                            │                  │                  │
                 │                            │                  │                  ├─> Phase 5 (US3) ─┬─> Phase 6 (US4) ─┬─> [P2 DONE]
                 │                            │                  │                  │                   │                  │
                 │                            │                  │                  │                   │                  ├─> Phase 7 (US5) ─┬─> Phase 8 (US6) ─┬─> Phase 9 (Polish)
```

### User Story Dependencies

- **US1 (P1)**: After Foundational - No story dependencies
- **US2 (P1)**: After US1 - Uses parser.py output (ChangelogData)
- **US3 (P2)**: After US2 - Uses analyzer.py output (ImpactReport)
- **US4 (P2)**: After US3 - Runs after updater.py
- **US5 (P3)**: After US4 - Enhances update flow
- **US6 (P3)**: After US5 - Final integration

### Parallel Opportunities

**Within Phase 2 (Foundational)**:
- T011 (conftest.py) || T012 (test_models.py) - different files

**Within Phase 3 (US1 Tests)**:
- T013, T014, T015 - all different test functions

**Within Phase 4 (US2 Tests)**:
- T021, T022, T023, T024 - all different test functions

**Within Phase 5 (US3 Tests)**:
- T031, T032 || T033, T034, T035, T036 - updater tests || git_ops tests

---

## Parallel Example: Phase 2 Foundational

```bash
# Launch model implementation sequentially (same file):
Task: T004 "Implement enums in models.py"
Task: T005 "Implement ChangelogData in models.py"
Task: T006 "Implement BreakingChange in models.py"
# ... etc (same file, sequential)

# Then launch tests in parallel (different files):
Task: T011 "Create conftest.py"
Task: T012 "Create test_models.py"
```

---

## Implementation Strategy

### MVP First (US1 + US2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (all models)
3. Complete Phase 3: US1 (parser)
4. Complete Phase 4: US2 (analyzer)
5. **STOP and VALIDATE**: `python -m scripts.auto_update check` works
6. Deploy/demo if ready

### Incremental Delivery

1. **MVP**: Setup + Foundational + US1 + US2 → Manual `check` command
2. **+US3+US4**: Add auto-update + validation → Automated PRs
3. **+US5+US6**: Add auto-fix + Claude dispatch → Full autonomy

---

## Notes

- [P] tasks = different files, parallelizable
- [E] tasks = complex algorithms (T027: confidence scoring)
- All models in single file (scripts/auto_update/models.py) - tasks T004-T010 must be sequential
- Total tasks: 80 (including coverage and type checking validation)
- Tests grouped by module (test_parser.py, test_analyzer.py, etc.) - each test file can have parallel test tasks
- Commit after each task or logical group
- Stop at MVP checkpoint to validate core functionality
