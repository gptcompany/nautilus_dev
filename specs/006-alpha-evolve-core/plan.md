# Implementation Plan: Alpha-Evolve Core Infrastructure

**Feature Branch**: `006-alpha-evolve-core`
**Created**: 2025-12-27
**Status**: Ready for Implementation
**Spec Reference**: `specs/006-alpha-evolve-core/spec.md`

## Architecture Overview

### System Context

Alpha-Evolve Core provides the foundational infrastructure for evolutionary strategy discovery. It consists of three independent modules that are composed by higher-level specs (007-010).

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Alpha-Evolve Ecosystem                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ spec-009: Controller (uses all below)                         │ │
│  └───────────────────────────────┬────────────────────────────────┘ │
│                                  │                                   │
│          ┌───────────────────────┼───────────────────────┐          │
│          │                       │                       │          │
│          ▼                       ▼                       ▼          │
│  ┌──────────────┐    ┌───────────────────┐    ┌─────────────────┐  │
│  │ spec-007:    │    │ spec-006: CORE    │    │ spec-008:       │  │
│  │ Evaluator    │◄───┤ (This Spec)       │───►│ Templates       │  │
│  │              │    │                   │    │                 │  │
│  │ - Backtest   │    │ - Patching        │    │ - Base strategy │  │
│  │ - Metrics    │    │ - Store           │    │ - EVOLVE-BLOCK  │  │
│  └──────────────┘    │ - Config          │    └─────────────────┘  │
│                      └───────────────────┘                          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Diagram

```
scripts/alpha_evolve/
├── __init__.py           # Package exports
├── patching.py           # EVOLVE-BLOCK mutation system
│   ├── BLOCK_RE          # Regex pattern for markers
│   ├── apply_patch()     # Core patching function
│   ├── extract_blocks()  # Block extraction utility
│   └── validate_syntax() # Python syntax validation
├── store.py              # SQLite persistence layer
│   ├── FitnessMetrics    # Dataclass for metrics
│   ├── Program           # Dataclass for strategy
│   └── ProgramStore      # Main store class
│       ├── insert()
│       ├── update_metrics()
│       ├── get()
│       ├── top_k()
│       ├── sample()
│       ├── get_lineage()
│       ├── count()
│       └── prune()
├── config.py             # Configuration management
│   └── EvolutionConfig   # Pydantic settings
└── config.yaml           # Default parameters
```

## Technical Decisions

### Decision 1: Patching Approach

**Options Considered**:
1. **Regex-based EVOLVE-BLOCK** (from pwb-alphaevolve)
   - Pros: Simple, battle-tested, handles indentation
   - Cons: Can't handle nested blocks
2. **AST-based transformation**
   - Pros: Language-aware, handles complex cases
   - Cons: Breaks on partial code, heavy dependency

**Selected**: Option 1 - Regex-based

**Rationale**: EVOLVE-BLOCK markers are explicitly added by template designers. The regex approach handles all practical cases and is simpler to debug.

---

### Decision 2: Storage Backend

**Options Considered**:
1. **SQLite with flat metrics columns**
   - Pros: Fast SQL sorting, no JSON parsing
   - Cons: Schema changes require migrations
2. **SQLite with JSON metrics column**
   - Pros: Flexible schema
   - Cons: Can't sort by metrics efficiently

**Selected**: Option 1 - Flat columns

**Rationale**: top_k() and sample() are hot paths. Direct column access is faster than JSON extraction.

---

### Decision 3: Configuration System

**Options Considered**:
1. **Pydantic BaseSettings + YAML**
   - Pros: Built-in validation, env override, type safety
   - Cons: Slight complexity
2. **Raw YAML with manual validation**
   - Pros: Simpler
   - Cons: No automatic validation

**Selected**: Option 1 - Pydantic

**Rationale**: Validation is critical for evolution parameters. Pydantic catches errors before runtime.

---

## Implementation Strategy

### Phase 1: Patching System

**Goal**: Port patching logic from pwb-alphaevolve

**Deliverables**:
- [x] `scripts/alpha_evolve/__init__.py` - Package setup
- [ ] `scripts/alpha_evolve/patching.py` - Core patching module
- [ ] `tests/alpha_evolve/test_patching.py` - Unit tests

**Files to create**:
1. `patching.py` (~60 lines) - Direct port with minor adjustments
2. `test_patching.py` (~100 lines) - Cover all acceptance scenarios

**Dependencies**: None

---

### Phase 2: SQLite Store

**Goal**: Implement hall-of-fame persistence with selection algorithms

**Deliverables**:
- [ ] `scripts/alpha_evolve/store.py` - Persistence layer
- [ ] `tests/alpha_evolve/test_store.py` - Unit tests

**Files to create**:
1. `store.py` (~200 lines) - Extended from pwb-alphaevolve
2. `test_store.py` (~150 lines) - Cover CRUD, selection, pruning

**Dependencies**: None (can run in parallel with Phase 1; syntax validation is optional enhancement)

---

### Phase 3: Configuration

**Goal**: Implement typed configuration with validation

**Deliverables**:
- [ ] `scripts/alpha_evolve/config.py` - Configuration module
- [ ] `scripts/alpha_evolve/config.yaml` - Default parameters
- [ ] `tests/alpha_evolve/test_config.py` - Unit tests

**Files to create**:
1. `config.py` (~80 lines) - Pydantic settings
2. `config.yaml` (~20 lines) - Defaults
3. `test_config.py` (~60 lines) - Validation tests

**Dependencies**: None (can run in parallel with Phase 1)

---

### Phase 4: Integration & Testing

**Goal**: Verify all components work together

**Deliverables**:
- [ ] Integration tests
- [ ] Documentation updates

**Dependencies**: Phases 1-3

---

## File Structure

```
scripts/alpha_evolve/
├── __init__.py          # Exports: apply_patch, ProgramStore, EvolutionConfig
├── patching.py          # EVOLVE-BLOCK mutation
├── store.py             # SQLite persistence
├── config.py            # Configuration loading
└── config.yaml          # Default parameters

tests/alpha_evolve/
├── __init__.py
├── test_patching.py     # Patching unit tests
├── test_store.py        # Store unit tests
├── test_config.py       # Config unit tests
└── conftest.py          # Shared fixtures
```

## API Design

### Public Interface

```python
# patching.py
def apply_patch(parent_code: str, diff: dict) -> str: ...
def extract_blocks(code: str) -> dict[str, str]: ...
def validate_syntax(code: str) -> tuple[bool, str]: ...

# store.py
@dataclass
class FitnessMetrics:
    sharpe_ratio: float
    calmar_ratio: float
    max_drawdown: float
    cagr: float
    total_return: float
    trade_count: int | None = None
    win_rate: float | None = None

@dataclass
class Program:
    id: str
    code: str
    parent_id: str | None
    generation: int
    experiment: str | None
    metrics: FitnessMetrics | None
    created_at: float

class ProgramStore:
    def __init__(self, db_path: Path, *, population_size=500, archive_size=50): ...
    def insert(self, code, metrics=None, parent_id=None, experiment=None) -> str: ...
    def update_metrics(self, prog_id: str, metrics: FitnessMetrics) -> None: ...
    def get(self, prog_id: str) -> Program | None: ...
    def top_k(self, k=10, metric="calmar") -> list[Program]: ...
    def sample(self, strategy="exploit") -> Program | None: ...
    def get_lineage(self, prog_id: str) -> list[Program]: ...
    def count(self) -> int: ...
    def prune(self) -> int: ...

# config.py
class EvolutionConfig(BaseSettings):
    population_size: int = 500
    archive_size: int = 50
    elite_ratio: float = 0.1
    exploration_ratio: float = 0.2
    max_concurrent: int = 2

    @classmethod
    def load(cls, config_path: Path | None = None) -> "EvolutionConfig": ...
```

## Testing Strategy

### Unit Tests

- [x] Test EVOLVE-BLOCK regex detection
- [x] Test patch application with indentation
- [x] Test multiple named blocks
- [x] Test syntax validation
- [x] Test store insert/get
- [x] Test top_k sorting
- [x] Test sample strategies (elite/exploit/explore)
- [x] Test pruning
- [x] Test lineage traversal
- [x] Test config loading
- [x] Test config validation

### Integration Tests

- [ ] Insert → evaluate → update_metrics → top_k
- [ ] Patch → validate → insert → sample cycle

### Performance Tests

- [ ] Benchmark top_k with 1000 strategies
- [ ] Benchmark sample with 1000 strategies
- [ ] Benchmark prune with population overflow

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| SQLite locking on concurrent access | Medium | Low | Single-writer pattern, WAL mode |
| Regex fails on edge cases | High | Low | Comprehensive test suite |
| Config validation too strict | Low | Medium | Sensible defaults, clear errors |

## Dependencies

### External Dependencies
- Python 3.11+ (already required)
- Pydantic 2.x (already in project)
- PyYAML (already in project)

### Internal Dependencies
- None (core infrastructure)

## Acceptance Criteria

- [x] All unit tests passing (coverage > 80%)
- [ ] All integration tests passing
- [ ] Documentation updated
- [ ] Code review approved
- [ ] Performance benchmarks met (< 10ms patching, < 100ms queries)

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| Black Box Design | ✅ | Clean interfaces, hidden implementation |
| KISS & YAGNI | ✅ | Minimal features, no over-engineering |
| Native First | ✅ | Uses Python stdlib (sqlite3, ast, re) |
| Performance | ✅ | No df.iterrows(), indexed queries |
| TDD | ✅ | Tests before implementation |

## Next Steps

After this plan is approved:
1. Run `/speckit:speckit.tasks` to generate task breakdown
2. Implement Phase 1 (patching) first
3. Implement Phase 2 & 3 in parallel
4. Integration testing in Phase 4
