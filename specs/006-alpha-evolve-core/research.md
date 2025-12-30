# Research: Alpha-Evolve Core Infrastructure

**Created**: 2025-12-27
**Status**: Complete

## Research Questions

### Q1: EVOLVE-BLOCK Regex Pattern

**Decision**: Use regex pattern from pwb-alphaevolve with minor adjustments

**Rationale**: The pattern is battle-tested and handles edge cases (indentation, multiline).

**Pattern**:
```python
BLOCK_RE = re.compile(
    r"(^[ \t]*# === EVOLVE-BLOCK:\s*(?P<name>\w+).*?$\n)"  # head
    r"(?P<body>.*?)"  # body (lazy match)
    r"(?P<tail>^\s*# === END EVOLVE-BLOCK.*?$)",  # tail
    re.M | re.S,  # Multiline + Dotall
)
```

**Key Features**:
- Named groups for clarity (`name`, `body`, `tail`)
- Lazy `.*?` to match shortest body
- `re.M | re.S` for multiline matching
- Indentation detection from body's first line

**Alternatives Considered**:
- AST-based parsing: Too heavy, breaks on partial code
- Simple string split: Doesn't handle nested blocks

---

### Q2: SQLite Schema Design

**Decision**: Extend pwb-alphaevolve schema with NautilusTrader-specific fields

**Schema**:
```sql
CREATE TABLE programs (
    id TEXT PRIMARY KEY,
    code TEXT NOT NULL,
    parent_id TEXT,
    generation INTEGER DEFAULT 0,
    experiment TEXT,
    -- Fitness metrics (nullable until evaluated)
    sharpe REAL,
    calmar REAL,
    max_dd REAL,
    cagr REAL,
    total_return REAL,
    trade_count INTEGER,
    -- Metadata
    created_at REAL NOT NULL,
    FOREIGN KEY (parent_id) REFERENCES programs(id)
);

CREATE INDEX idx_calmar ON programs(calmar DESC);
CREATE INDEX idx_sharpe ON programs(sharpe DESC);
CREATE INDEX idx_experiment ON programs(experiment);
```

**Rationale**:
- Flat metrics (not JSON) for efficient SQL sorting
- Index on primary fitness metric (calmar) for fast top_k
- Experiment field for grouping runs
- Generation tracked for lineage analysis

**Alternatives Considered**:
- JSON metrics column: Harder to sort/filter
- DuckDB: Overkill for population < 10,000

---

### Q3: Parent Selection Algorithm

**Decision**: Three-tier weighted selection

**Implementation**:
```python
def sample(strategy: str = "exploit") -> Program:
    if strategy == "elite":
        # Top 10% by fitness
        return random.choice(top_k(population_size * 0.1))
    elif strategy == "explore":
        # Uniform random from full population
        return random_sample()
    else:  # exploit (default)
        # Fitness-weighted probability
        programs = get_all_evaluated()
        weights = [max(0, p.calmar) for p in programs]
        return random.choices(programs, weights=weights)[0]
```

**Selection Mix**:
- 10% elite: Exploit best performers
- 70% exploit: Fitness-weighted (better strategies more likely)
- 20% explore: Maintain diversity

**Rationale**: Balances exploitation (improving good) with exploration (finding new).

**Alternatives Considered**:
- Tournament selection: More complex, similar results
- Uniform random: No exploitation pressure

---

### Q4: Configuration System

**Decision**: Pydantic BaseSettings with YAML override

**Implementation**:
```python
from pydantic import BaseSettings, Field

class EvolutionConfig(BaseSettings):
    population_size: int = Field(500, ge=10)
    archive_size: int = Field(50, ge=1)
    elite_ratio: float = Field(0.1, ge=0.0, le=1.0)
    exploration_ratio: float = Field(0.2, ge=0.0, le=1.0)
    max_concurrent: int = Field(2, ge=1)

    class Config:
        env_prefix = "EVOLVE_"
```

**Rationale**:
- Built-in validation via Pydantic
- Environment variable override for CI/production
- YAML for human-friendly editing

**Alternatives Considered**:
- Raw YAML: No validation
- Click CLI options: Less reusable

---

### Q5: Pruning Strategy

**Decision**: Keep archive_size top performers, random prune rest

**Algorithm**:
```python
def prune():
    if count() <= population_size:
        return
    elite_ids = {p.id for p in top_k(archive_size)}
    candidates = [p.id for p in all() if p.id not in elite_ids]
    excess = count() - population_size
    to_delete = random.sample(candidates, min(excess, len(candidates)))
    delete_all(to_delete)
```

**Rationale**:
- Protects top performers from random deletion
- Random selection among non-elite maintains diversity
- Simple and deterministic

**Alternatives Considered**:
- Age-based pruning: Loses good old strategies
- Fitness-proportional culling: Too aggressive on weak strategies

---

### Q6: Syntax Validation

**Decision**: Use `ast.parse()` for validation

**Implementation**:
```python
import ast

def is_valid_python(code: str) -> tuple[bool, str]:
    try:
        ast.parse(code)
        return True, ""
    except SyntaxError as e:
        return False, f"Line {e.lineno}: {e.msg}"
```

**Rationale**:
- Built-in, no dependencies
- Returns line number for debugging
- Catches all syntax errors

**Alternatives Considered**:
- `compile()`: Less informative errors
- External linter: Overkill for syntax check

---

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| Black Box Design | ✅ | Each module has clean interface |
| KISS & YAGNI | ✅ | Minimal implementation, no over-engineering |
| Native First | ✅ | Uses Python stdlib (sqlite3, ast, re) |
| Performance | ✅ | No df.iterrows(), streaming where needed |
| TDD | ✅ | Tests ported from pwb-alphaevolve |

## Dependencies

- Python stdlib: `sqlite3`, `re`, `ast`, `json`, `uuid`, `time`, `random`
- Pydantic: Config validation (already in project)
- PyYAML: Config loading (already in project)

## No External Research Needed

All technical decisions can be resolved using:
1. pwb-alphaevolve reference implementation
2. Python stdlib documentation
3. Existing project patterns
