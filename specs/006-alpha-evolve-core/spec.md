# Feature Specification: Alpha-Evolve Core Infrastructure

**Feature Branch**: `006-alpha-evolve-core`
**Created**: 2025-12-27
**Status**: Draft
**Input**: Port del sistema di patching EVOLVE-BLOCK da pwb-alphaevolve, SQLite store per hall-of-fame delle strategie con top_k/sample/prune, e config YAML per parametri evoluzione.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - EVOLVE-BLOCK Patching System (Priority: P1)

As a strategy evolution system, I need to surgically replace code within EVOLVE-BLOCK markers so that mutations target only the decision logic while preserving strategy structure.

**Why this priority**: Core mutation mechanism - without this, no evolution can occur. All other components depend on the ability to patch strategy code.

**Independent Test**: Can be fully tested by providing sample strategy code with EVOLVE-BLOCK markers and verifying correct replacement while preserving indentation.

**Acceptance Scenarios**:

1. **Given** a strategy file with `# === EVOLVE-BLOCK: decision_logic ===` and `# === END EVOLVE-BLOCK ===` markers, **When** apply_patch() is called with new code, **Then** only the code between markers is replaced.
2. **Given** code with 4-space indentation inside EVOLVE-BLOCK, **When** replacement code with different indentation is provided, **Then** output preserves original indentation level.
3. **Given** strategy code without EVOLVE-BLOCK markers, **When** apply_patch() is called, **Then** an error is raised indicating missing markers.
4. **Given** strategy code with multiple EVOLVE-BLOCK sections (named differently), **When** patch targets specific block name, **Then** only that named block is modified.

---

### User Story 2 - SQLite Hall-of-Fame Store (Priority: P1)

As a strategy evolution system, I need to persist evolved strategies with their fitness metrics so that I can track the population, select parents, and maintain a hall-of-fame of top performers.

**Why this priority**: Without persistence, all evolution progress is lost between runs. Essential for tracking lineage and selecting best performers.

**Independent Test**: Can be fully tested by inserting strategies, querying top_k, sampling for parent selection, and verifying pruning behavior.

**Acceptance Scenarios**:

1. **Given** an empty store, **When** insert() is called with strategy code and metrics (sharpe, calmar, max_dd, cagr), **Then** strategy is persisted with unique ID and timestamp.
2. **Given** a store with 100 strategies, **When** top_k(k=10) is called, **Then** returns 10 strategies ordered by fitness (calmar by default).
3. **Given** a store with strategies, **When** sample(strategy="elite") is called, **Then** returns a random strategy from top 10% by fitness.
4. **Given** a store with strategies, **When** sample(strategy="exploit") is called, **Then** returns a random strategy weighted by fitness.
5. **Given** a store with strategies, **When** sample(strategy="explore") is called, **Then** returns a random strategy from the full population.
6. **Given** a store exceeding population_size (500), **When** prune() is called, **Then** lowest-fitness strategies are removed to maintain population limit.
7. **Given** a strategy ID, **When** get_lineage(id) is called, **Then** returns parent chain up to seed strategy.

---

### User Story 3 - Evolution Configuration (Priority: P2)

As a user, I need YAML configuration for evolution parameters so that I can tune the evolution process without modifying code.

**Why this priority**: Configuration allows experimentation with different hyperparameters. Not blocking for initial implementation but essential for tuning.

**Independent Test**: Can be fully tested by loading config and verifying all parameters are accessible with correct types and defaults.

**Acceptance Scenarios**:

1. **Given** a config.yaml file, **When** Config.load() is called, **Then** all evolution parameters are accessible as typed attributes.
2. **Given** missing config file, **When** Config.load() is called, **Then** default values are used for all parameters.
3. **Given** partial config (some values omitted), **When** Config.load() is called, **Then** specified values override defaults, others use defaults.
4. **Given** invalid parameter value (e.g., negative population_size), **When** Config.load() is called, **Then** validation error is raised with clear message.

---

### Edge Cases

- What happens when EVOLVE-BLOCK markers are malformed (missing END)?
- What happens when store database file is corrupted or locked?
- How does system handle concurrent writes to the store?
- What happens when config YAML has unknown parameters?
- How does pruning handle ties in fitness scores?

## Requirements *(mandatory)*

### Functional Requirements

#### Patching System
- **FR-001**: System MUST identify EVOLVE-BLOCK sections using regex pattern `# === EVOLVE-BLOCK: <name> ===` and `# === END EVOLVE-BLOCK ===`
- **FR-002**: System MUST preserve original indentation when applying patches
- **FR-003**: System MUST support named blocks to allow multiple evolvable sections per strategy
- **FR-004**: System MUST validate that replacement code is syntactically valid Python
- **FR-005**: System MUST return the full patched code as a string (not modify files directly)

#### SQLite Store
- **FR-006**: Store MUST persist: id (UUID), code (TEXT), parent_id (UUID nullable), generation (INT), created_at (TIMESTAMP), fitness metrics (sharpe, calmar, max_dd, cagr as REAL)
- **FR-007**: Store MUST implement top_k(k: int, metric: str) returning best k strategies by specified metric
- **FR-008**: Store MUST implement sample(strategy: str) for parent selection with strategies: "elite" (top 10%), "exploit" (fitness-weighted), "explore" (uniform random)
- **FR-009**: Store MUST implement prune(population_size: int) to remove lowest-fitness strategies
- **FR-010**: Store MUST track lineage via parent_id foreign key
- **FR-011**: Store MUST support atomic transactions for insert+prune operations

#### Configuration
- **FR-012**: Config MUST support these parameters: population_size (int), archive_size (int), elite_ratio (float), exploration_ratio (float), max_concurrent (int)
- **FR-013**: Config MUST validate parameter ranges (e.g., ratios between 0-1, sizes > 0)
- **FR-014**: Config MUST provide sensible defaults: population_size=500, archive_size=50, elite_ratio=0.1, exploration_ratio=0.2, max_concurrent=2

### Key Entities

- **Program**: Represents an evolved strategy with code, metrics, and lineage. Key attributes: id, code, parent_id, generation, fitness_metrics, created_at
- **FitnessMetrics**: Strategy performance measurements. Attributes: sharpe_ratio, calmar_ratio, max_drawdown, cagr, total_return
- **EvolutionConfig**: Runtime parameters for evolution process. Attributes: population_size, archive_size, elite_ratio, exploration_ratio, max_concurrent

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Patching operations complete in under 10ms for typical strategy files (< 500 lines)
- **SC-002**: Store queries (top_k, sample) return results in under 100ms for populations up to 1000 strategies
- **SC-003**: Store maintains data integrity across 1000+ insert/prune cycles without corruption
- **SC-004**: 100% of patched code maintains syntactic validity when given valid input
- **SC-005**: Configuration validation catches 100% of invalid parameter combinations before runtime

## Assumptions

- SQLite is sufficient for population sizes up to 10,000 strategies (migrate to DuckDB if performance issues arise)
- EVOLVE-BLOCK markers use Python comment syntax (`#`)
- Fitness metrics are calculated externally (by evaluator spec-007) before insertion
- Concurrent access is single-writer, multi-reader (SQLite default)

## Out of Scope

- Strategy evaluation/backtesting (see spec-007)
- Strategy templates (see spec-008)
- Evolution controller/CLI (see spec-009)
- Grafana dashboard (see spec-010)
- Migration tools for existing strategy libraries

---

## Future Enhancements (Black Book Concepts)

> **Source**: "The Black Book of Financial Hacking" - J.C. Lotter
> **Philosophy**: Add complexity ONLY if OOS shows problems.

### FE-001: Fitness Sharing (Niching)

**Current**: Fitness is absolute - strategies compete globally

**Enhancement**: Fitness sharing to maintain diversity via niching

```python
def shared_fitness(strategy, population, sigma_share=0.3):
    """
    Penalize fitness based on similarity to other strategies.

    Prevents premature convergence to local optima.
    """
    raw_fitness = strategy.fitness
    niche_count = sum(
        similarity(strategy, other) / sigma_share
        for other in population
        if similarity(strategy, other) > 0
    )
    return raw_fitness / (1 + niche_count)
```

**Trigger**: When evolution converges too quickly (all strategies look similar after 20 generations)

**Trade-off**: Requires similarity metric (code diff? AST distance?), slower selection

**Reference**: Goldberg & Richardson (1987) "Genetic Algorithms with Sharing for Multimodal Function Optimization"

### FE-002: Island Model (Parallel Populations)

**Current**: Single population evolves sequentially

**Enhancement**: Multiple isolated populations with periodic migration

```python
class IslandPopulation:
    def __init__(self, n_islands=4, migration_interval=10):
        self.islands = [Population() for _ in range(n_islands)]
        self.migration_interval = migration_interval

    def evolve(self):
        # Evolve islands independently
        for island in self.islands:
            island.evolve_generation()

        # Every N generations, migrate best strategies
        if self.generation % self.migration_interval == 0:
            self.migrate_elites()
```

**Trigger**: When single population gets stuck in local optimum (no improvement for 50+ generations)

**Trade-off**: Requires 4x compute resources, but explores search space better

**Reference**: Whitley et al. (1999) "Island Model Genetic Algorithms and Linearly Separable Problems"

### FE-003: Adaptive Mutation Rates

**Current**: Fixed elite/exploit/explore ratios (10%/70%/20%)

**Enhancement**: Adjust mutation rates based on population diversity

```python
def adaptive_mutation_rate(population):
    """
    Increase exploration when diversity is low.
    Increase exploitation when diversity is high.
    """
    diversity = calculate_diversity(population)  # 0-1 scale

    if diversity < 0.2:  # Low diversity
        return {'elite': 0.05, 'exploit': 0.50, 'explore': 0.45}
    elif diversity > 0.7:  # High diversity
        return {'elite': 0.15, 'exploit': 0.80, 'explore': 0.05}
    else:
        return {'elite': 0.10, 'exploit': 0.70, 'explore': 0.20}
```

**Trigger**: When population diversity metrics show premature convergence or excessive randomness

**Trade-off**: Needs diversity metric implementation, more complex parameter tuning

**Reference**: Eiben et al. (1999) "Parameter Control in Evolutionary Algorithms"

### FE-004: Lineage Pruning (Age-Based Selection)

**Current**: Pruning based only on fitness

**Enhancement**: Prune old lineages even if moderately fit

```python
def age_weighted_pruning(population, max_age=50):
    """
    Remove strategies from old lineages to prevent stagnation.
    """
    scores = []
    for strategy in population:
        age_penalty = 1.0 - (strategy.generation / max_age)
        age_penalty = max(0, age_penalty)  # Clamp to 0
        score = strategy.fitness * age_penalty
        scores.append((strategy, score))

    # Keep top N by age-weighted fitness
    return sorted(scores, key=lambda x: x[1], reverse=True)[:population_size]
```

**Trigger**: When hall-of-fame becomes dominated by old lineages (>80% from same parent)

**Trade-off**: May prune good strategies, but forces exploration of new lineages

**Reference**: Hornby (2006) "ALPS: The Age-Layered Population Structure"

---

**Decision Log** (2026-01-06):
- Simple fitness-based selection chosen for MVP
- Black Book enhancements documented for future need when OOS performance degrades
