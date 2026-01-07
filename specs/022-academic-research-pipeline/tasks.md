# Tasks: Academic Research → Trading Strategy Pipeline

**Input**: Design documents from `/specs/022-academic-research-pipeline/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Integration tests included per Testing Strategy in plan.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [Markers] [Story] Description`

### Task Markers
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US5)

---

## Phase 1: Setup (Project Structure)

**Purpose**: Create directory structures in both repositories

- [X] T001 Create docs/research/ directory in /media/sam/1TB/nautilus_dev/
- [X] T002 [P] Create .claude/skills/paper-to-strategy/ directory in /media/sam/1TB/nautilus_dev/
- [X] T003 [P] Verify /media/sam/1TB1/academic_research/semantic_router_mcp/ exists and is accessible

**Checkpoint**: Directory structure ready for component creation

---

## Phase 2: Foundational (Cross-Repository Schemas)

**Purpose**: Define shared schemas and entity types that ALL user stories depend on

**CRITICAL**: Complete this phase before ANY user story work

- [X] T004 Add strategy__ entity schema to /media/sam/1TB1/academic_research/docs/entity_schemas.md
- [X] T005 Create strategy__ validation function in /media/sam/1TB1/academic_research/scripts/validate_entity.py
- [X] T006 Test strategy__ entity creation with sample data in /media/sam/1TB1/academic_research/memory.json
- [X] T007 [P] Create NautilusTrader indicator mapping table in /media/sam/1TB/nautilus_dev/docs/research/indicator_mapping.md
- [X] T008 [P] Create order type mapping table in /media/sam/1TB/nautilus_dev/docs/research/order_mapping.md

**Checkpoint**: Foundation ready - entity schemas defined, validated, mappings documented

---

## Phase 3: User Story 1 - Trading Paper Classification (Priority: P1) 🎯 MVP

**Goal**: Enable semantic-router to classify trading papers into `trading_strategy` domain

**Independent Test**: Query "momentum trading backtest" → classified as `trading_strategy` with confidence > 0.8

### Implementation for User Story 1

- [X] T009 [US1] Add TRADING_STRATEGY_UTTERANCES (20+ entries) to /media/sam/1TB1/academic_research/semantic_router_mcp/routes_config.py
- [X] T010 [US1] Create trading_strategy Route object in /media/sam/1TB1/academic_research/semantic_router_mcp/routes_config.py
- [X] T011 [US1] Register trading_strategy route in semantic-router encoder in /media/sam/1TB1/academic_research/semantic_router_mcp/server.py
- [X] T012 [US1] Add "Trading Strategy Research" template to /media/sam/1TB1/academic_research/.claude/skills/research-query-workflow/SKILL.md
- [X] T013 [US1] Test classification accuracy with 10 sample queries (target > 85%) [REQUIRES MANUAL VALIDATION]

**Checkpoint**: User Story 1 complete - trading papers correctly classified

---

## Phase 4: User Story 2 - Paper → Strategy Spec (Priority: P1) 🎯 MVP

**Goal**: Convert academic paper into NautilusTrader-compatible spec.md

**Independent Test**: `/paper-to-strategy arxiv:2209.03307` → generates valid spec.md with indicators

### Implementation for User Story 2

- [X] T014 [P] [US2] Create strategy_spec.md template in /media/sam/1TB/nautilus_dev/.claude/skills/paper-to-strategy/templates/strategy_spec.md
- [X] T015 [P] [US2] Create SKILL.md for paper-to-strategy skill in /media/sam/1TB/nautilus_dev/.claude/skills/paper-to-strategy/SKILL.md
- [X] T016 [US2] Create strategy-researcher agent in /media/sam/1TB/nautilus_dev/.claude/agents/strategy-researcher.md
- [X] T017 [US2] Implement methodology extraction workflow in strategy-researcher agent
- [X] T018 [US2] Implement NautilusTrader indicator mapping in strategy-researcher agent
- [X] T019 [US2] Implement spec.md generation in strategy-researcher agent
- [X] T020 [US2] Test end-to-end: paper → spec.md with sample paper [REQUIRES MANUAL VALIDATION]

**Checkpoint**: User Story 2 complete - paper-to-strategy pipeline functional

---

## Phase 5: User Story 3 - Multi-Implementation Generation (Priority: P2)

**Goal**: Use alpha-evolve to generate multiple strategy implementations from one spec

**Independent Test**: Spec from US2 → alpha-evolve generates 3+ implementations → backtest ranks them

### Implementation for User Story 3

- [X] T021 [US3] Create alpha-evolve integration hook in /media/sam/1TB/nautilus_dev/.claude/skills/paper-to-strategy/SKILL.md
- [X] T022 [US3] Add backtest evaluation criteria (Sharpe, drawdown) to strategy-researcher workflow
- [X] T023 [US3] Create implementation ranking logic in strategy-researcher agent
- [X] T024 [US3] Add "best implementation promotion" step to strategy-researcher agent
- [X] T025 [US3] Test multi-implementation: spec → 3 variants → ranked by backtest [REQUIRES MANUAL VALIDATION]

**Checkpoint**: User Story 3 complete - multi-implementation with ranking operational

---

## Phase 6: User Story 4 - Knowledge Graph Sync (Priority: P2)

**Goal**: Synchronize strategy entities between academic_research and nautilus_dev

**Independent Test**: Create strategy__ in memory.json → run sync → appears in strategies.json

### Implementation for User Story 4

- [X] T026 [US4] Create sync_research.py script in /media/sam/1TB/nautilus_dev/scripts/sync_research.py
- [X] T027 [US4] Implement entity extraction (strategy__ prefix filter) in sync_research.py
- [X] T028 [US4] Implement JSON output to docs/research/strategies.json in sync_research.py
- [X] T029 [US4] Add staleness detection (timestamp comparison) to sync_research.py
- [X] T030 [P] [US4] Create README.md in /media/sam/1TB/nautilus_dev/docs/research/README.md
- [X] T031 [US4] Test sync with mock strategy__ entity in memory.json

**Checkpoint**: User Story 4 complete - sync with staleness detection operational

---

## Phase 7: User Story 5 - Incremental Research (Priority: P3)

**Goal**: Build on previous research sessions without repeating work

**Independent Test**: "Research momentum strategies" → shows differential from last session

### Implementation for User Story 5

- [X] T032 [US5] Add session tracking to research-query-workflow skill in /media/sam/1TB1/academic_research/.claude/skills/research-query-workflow/SKILL.md
- [X] T033 [US5] Implement "find existing" logic in strategy-researcher agent (query memory.json first)
- [X] T034 [US5] Add differential reporting ("3 new papers since last session") to strategy-researcher
- [X] T035 [US5] Link existing strategies to similar concepts in strategy-researcher output
- [X] T036 [US5] Test incremental: research topic twice → second run shows differential [REQUIRES MANUAL VALIDATION]

**Checkpoint**: User Story 5 complete - incremental research with history

---

## Phase 8: Documentation & Polish

**Purpose**: Production-ready documentation and final validation

- [X] T037 [P] Update /media/sam/1TB1/academic_research/CLAUDE.md with trading route documentation
- [X] T038 [P] Update /media/sam/1TB/nautilus_dev/CLAUDE.md with strategy-researcher agent reference
- [X] T039 [P] Create troubleshooting guide in /media/sam/1TB/nautilus_dev/specs/022-academic-research-pipeline/troubleshooting.md
- [X] T040 Update /media/sam/1TB/nautilus_dev/docs/ARCHITECTURE.md with pipeline diagram
- [X] T041 Run alpha-debug verification on strategy-researcher agent
- [X] T042 End-to-end validation: "Research momentum reversal" → working backtest < 2 hours

---

## Phase 9: User Story 6 - Storage Layer DuckDB + Neo4j (Priority: P1) 🆕

**Goal**: Persistent storage with graph traversal and SQL analytics

**Independent Test**: Cypher query returns papers citing a formula, SQL aggregates strategies by Sharpe

### Implementation for User Story 6

- [X] T043 [US6] Install Neo4j Docker: `docker run -d -p 7474:7474 -p 7687:7687 neo4j:community`
- [X] T044 [US6] Create Neo4j schema: Paper, Formula, Strategy, Concept nodes
- [X] T045 [US6] Create Neo4j relationships: CITES, CONTAINS, USES, BASED_ON
- [X] T046 [US6] Create DuckDB database: /media/sam/1TB/nautilus_dev/data/research.duckdb
- [X] T047 [US6] Create DuckDB tables: papers, formulas, strategies, backtests, walk_forward_analyses, parameter_sets, indicators
- [X] T048 [P] [US6] Create sync script: memory.json → Neo4j (scripts/sync_memory_to_neo4j.py)
- [X] T049 [P] [US6] Create sync script: Neo4j → DuckDB (scripts/sync_neo4j_to_duckdb.py)
- [X] T050 [US6] Test Cypher: MATCH (p:Paper)-[:CONTAINS]->(f:Formula) RETURN p,f ✅
- [X] T051 [US6] Test SQL: SELECT * FROM strategies WHERE sharpe_ratio > 1.5 ✅

**Checkpoint**: Storage layer operational - graph + analytics queries working

---

## Phase 10: User Story 7 - MinerU PDF Parsing (Priority: P1) 🆕

**Goal**: Layout-aware PDF parsing with formula preservation

**Independent Test**: `mineru -p paper.pdf` outputs markdown with intact LaTeX formulas

### Implementation for User Story 7

- [X] T052 [US7] Verify MinerU standalone installed: /media/sam/1TB/academic_research/.venv_mineru (v2.7.1)
- [X] T053 [US7] Test MinerU on sample paper: 2024-unknown-adaptive-bandits-trading.pdf
- [X] T054 [US7] Create wrapper script: scripts/parse_paper.sh
- [X] T055 [US7] Integrate with /research command: Step 2.7 PDF Parsing
- [X] T056 [US7] Store parsed output in: docs/research/parsed/{paper_id}/
- [X] T057 [US7] Extract metadata: title, authors, abstract, sections

**Checkpoint**: MinerU parsing integrated - PDFs → structured markdown

---

## Phase 11: User Story 8 - Formula Extraction & Validation (Priority: P2) 🆕

**Goal**: Extract formulas from parsed PDFs, validate with WolframAlpha

**Independent Test**: Extract Kelly Criterion formula, validate with WolframAlpha, create formula__ entity

### Implementation for User Story 8

- [X] T058 [US8] Create formula extraction script: scripts/extract_formulas.py
- [X] T059 [US8] Parse LaTeX from MinerU markdown output
- [X] T060 [US8] Create formula__ entity schema in Neo4j
- [X] T061 [US8] Integrate WolframAlpha validation: mcp__wolframalpha__ask_llm
- [X] T062 [US8] Store validation result: validation_status, wolfram_verified
- [X] T063 [US8] Create relationships: formula→paper, formula→strategy
- [X] T064 [US8] Test end-to-end: paper.pdf → extracted formulas → validated → Neo4j

**Checkpoint**: Formula pipeline complete - PDF → formulas → validated → stored

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - US1 (Classification): Can proceed first - other stories depend on it
  - US2 (Paper→Spec): Depends on US1 (needs classified papers)
  - US3 (Multi-Impl): Depends on US2 (needs spec from paper)
  - US4 (Sync): Can run parallel with US2/US3 (different files)
  - US5 (Incremental): Depends on US4 (needs sync for history)
- **Polish (Phase 8)**: Depends on all user stories

### User Story Dependencies

```
US1 (Classification) ───> US2 (Paper→Spec) ───> US3 (Multi-Impl)
         │
         └───────────────> US4 (Sync) ────────> US5 (Incremental)

US6 (Storage) ─────────> US7 (MinerU) ────────> US8 (Formulas)
     │                        │
     └────────────────────────┴──────────> US2,US5 (enhanced)
```

### Within Each User Story

- Schema/template tasks before implementation tasks
- Core logic before integration
- Story complete before moving to next priority
- Test at checkpoint before proceeding

### Parallel Opportunities

**Phase 1 (Setup)**:
- T002 + T003 can run in parallel

**Phase 2 (Foundational)**:
- T007 + T008 can run in parallel

**Phase 4 (US2)**:
- T014 + T015 can run in parallel (different files)

**Phase 6 (US4)**:
- T030 can run parallel with T026-T029 (different file)

**Phase 8 (Polish)**:
- T037 + T038 + T039 can all run in parallel

---

## Implementation Strategy

### MVP First (US1 + US2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: User Story 1 (Classification)
4. Complete Phase 4: User Story 2 (Paper→Spec)
5. **STOP and VALIDATE**: Test with real paper
6. Can use pipeline for basic paper-to-spec conversion

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 → Test classification → Papers classified (MVP!)
3. Add US2 → Test spec generation → Paper→Spec working
4. Add US3 → Test multi-impl → Ranked implementations
5. Add US4 → Test sync → Entities synchronized
6. Add US5 → Test history → Incremental research
7. Polish → Production-ready

---

## Cross-Repository Notes

**IMPORTANT**: This feature spans TWO repositories:
- `/media/sam/1TB1/academic_research` - Classification, entity storage
- `/media/sam/1TB/nautilus_dev` - Strategy generation, sync, agent

Tasks clearly indicate which repository each file belongs to.

### File Ownership

| Repository | Files |
|------------|-------|
| academic_research | routes_config.py, entity_schemas.md, research-query-workflow, memory.json |
| nautilus_dev | strategy-researcher.md, paper-to-strategy/, sync_research.py, strategies.json |

---

## Notes

- [P] tasks = different files, no dependencies
- Tests are integration-focused (end-to-end validation)
- Each user story should be independently testable
- Commit after each task or logical group
- Stop at checkpoints to validate functionality
- Cross-repository changes require careful coordination

---

## Implementation Status

**Phase 1-8 (Original)**: 42/42 tasks (100%) ✅
**Phase 9 (Storage Layer)**: 9/9 tasks (100%) ✅
**Phase 10 (MinerU)**: 6/6 tasks (100%) ✅
**Phase 11 (Formulas)**: 7/7 tasks (100%) ✅
**Phase 12 (Event Sourcing)**: 4/4 tasks (100%) ✅
**Phase 13 (Query Router)**: 4/4 tasks (100%) ✅
**Phase 14 (Rerank)**: 4/4 tasks (100%) ✅
**Phase 15 (Versioning)**: 4/4 tasks (100%) ✅

**Total**: 80/80 tasks (100%) 🎉

### Completed (All Phases)
- Academic paper search + classification
- Paper download + standardized naming
- MinerU PDF parsing (background, non-blocking)
- Formula extraction + WolframAlpha validation
- Neo4j + DuckDB storage (**AUTOMATIC via event daemon**)
- Event sourcing with retry/DLQ/health monitoring
- Query router (Neo4j for graphs, DuckDB for analytics)
- Semantic rerank with sentence-transformers
- Version history via event replay + deduplication

### Architecture (Implemented)

**GAPS FIXED**:
1. ✅ Storage sync is AUTOMATIC (event daemon watches + syncs)
2. ✅ Reranking via embeddings (sentence-transformers)
3. ✅ Versioning via event log replay
4. ✅ Deduplication by DOI/arXiv ID/title
5. ✅ Unified query router for both DBs

**Phase 12: Event Sourcing + Auto Sync** ✅
- [X] T065 Create event log table in DuckDB (source of truth) - `scripts/research_events.py`
- [X] T066 Implement event types: paper_discovered, paper_downloaded, formula_extracted (8 types)
- [X] T067 Create sync daemon with retry/DLQ/health monitoring
- [X] T068 Update /research command to emit events (auto-sync via daemon)

**Phase 13: Query Router (Ensemble)** ✅
- [X] T069 Create query router - `scripts/research_query.py`
- [X] T070 Graph queries → Neo4j (papers_by_formula, citation_chain, related_strategies)
- [X] T071 SQL/Analytics → DuckDB (strategy_stats, top_strategies, methodology_breakdown)
- [X] T072 Unified API with QueryResult dataclass + hybrid queries

**Phase 14: Rerank Service** ✅
- [X] T073 Create paper_embeddings table - `scripts/research_rerank.py`
- [X] T074 Integrate sentence-transformers (all-MiniLM-L6-v2, 384 dims)
- [X] T075 Implement cosine similarity search with combined scoring
- [X] T076 Auto-rerank with rerank_search_results() function

**Phase 15: Versioning** ✅
- [X] T077 Version history via event replay - `scripts/research_versioning.py`
- [X] T078 Entity state reconstruction at any point in time
- [X] T079 Diff/history API (get_version_diff, get_entity_history)
- [X] T080 Deduplication by DOI/arXiv ID/title (check_duplicate)

**Architecture Target**:
```
Event Log (DuckDB) ─── Source of Truth
       │
       ├──► Neo4j (auto-sync) ─── Graph Queries
       │
       └──► DuckDB Views ─────── Analytics
```

**Repos involved**:
- /media/sam/1TB/nautilus_dev (scripts, commands)
- /media/sam/1TB/academic_research (storage, MinerU)
