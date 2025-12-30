# Data Model: Alpha-Evolve Controller

**Feature Branch**: `009-alpha-evolve-controller`
**Created**: 2025-12-27

## Entities

### Core Entities

#### EvolutionController

Main orchestrator for the evolution process.

```python
@dataclass
class EvolutionController:
    """Main orchestrator for evolution loop."""

    config: EvolutionConfig          # From spec-006
    store: ProgramStore              # From spec-006
    evaluator: StrategyEvaluator     # From spec-007

    # Runtime state
    experiment: str | None = None
    current_iteration: int = 0
    best_fitness: float = float('-inf')
    status: EvolutionStatus = EvolutionStatus.IDLE

    # Callbacks
    on_progress: Callable[[ProgressEvent], None] | None = None
```

**Relationships**:
- Uses `EvolutionConfig` (spec-006) for parameters
- Uses `ProgramStore` (spec-006) for persistence
- Uses `StrategyEvaluator` (spec-007) for fitness calculation
- Integrates with `alpha-evolve` agent for mutations

---

#### MutationRequest

Request payload for LLM mutation.

```python
@dataclass
class MutationRequest:
    """Request to LLM for code mutation."""

    parent_code: str                 # Full strategy code with EVOLVE-BLOCK
    parent_metrics: FitnessMetrics   # From spec-006
    block_name: str = "decision_logic"
    guidance: str = ""               # Optional mutation hints

    # Retry context
    previous_error: str | None = None
    retry_count: int = 0
```

**Validation Rules**:
- `parent_code` must contain valid EVOLVE-BLOCK markers
- `retry_count` <= 3 (max retries per mutation)

---

#### MutationResponse

Response from LLM mutation request.

```python
@dataclass
class MutationResponse:
    """LLM response with mutated code."""

    success: bool
    mutated_code: str | None = None  # Full patched strategy code
    error: str | None = None
    error_type: str | None = None    # "syntax", "block_not_found", "llm_error"
```

**State Transitions**:
- `success=True` → Code ready for evaluation
- `success=False, error_type="syntax"` → Retry with error context
- `success=False, retry_count >= 3` → Skip mutation, log failure

---

#### EvolutionProgress

Current state snapshot for monitoring.

```python
@dataclass
class EvolutionProgress:
    """Current evolution state for monitoring."""

    experiment: str
    iteration: int
    generation: int
    best_fitness: float
    best_strategy_id: str | None
    population_size: int
    elapsed_seconds: float
    status: EvolutionStatus

    # Optional progress indicators
    mutations_attempted: int = 0
    mutations_successful: int = 0
    evaluations_completed: int = 0
    evaluations_failed: int = 0
```

---

#### EvolutionStatus

Enum for controller state machine.

```python
class EvolutionStatus(Enum):
    """Controller state machine states."""

    IDLE = "idle"              # Not started
    RUNNING = "running"        # Active evolution
    PAUSED = "paused"          # Gracefully paused
    COMPLETED = "completed"    # Target reached or iterations exhausted
    FAILED = "failed"          # Unrecoverable error
```

---

#### ProgressEvent

Event emitted during evolution for monitoring.

```python
@dataclass
class ProgressEvent:
    """Progress event for callbacks/monitoring."""

    event_type: ProgressEventType
    iteration: int
    timestamp: datetime
    data: dict                    # Type-specific payload
```

```python
class ProgressEventType(Enum):
    """Types of progress events."""

    ITERATION_START = "iteration_start"
    PARENT_SELECTED = "parent_selected"
    MUTATION_REQUESTED = "mutation_requested"
    MUTATION_COMPLETE = "mutation_complete"
    EVALUATION_START = "evaluation_start"
    EVALUATION_COMPLETE = "evaluation_complete"
    ITERATION_COMPLETE = "iteration_complete"
    EVOLUTION_COMPLETE = "evolution_complete"
    ERROR = "error"
```

---

#### StopCondition

Configuration for early termination.

```python
@dataclass
class StopCondition:
    """Conditions for early evolution termination."""

    # Iteration limit (required)
    max_iterations: int = 50

    # Optional early stop conditions
    target_fitness: float | None = None       # Stop when fitness >= target
    max_time_seconds: int | None = None       # Wall-clock timeout
    no_improvement_generations: int | None = None  # Stagnation detection
```

**Evaluation Order**:
1. Check `max_iterations` first
2. Check `target_fitness` if set
3. Check `max_time_seconds` if set
4. Check `no_improvement_generations` if set

---

### Extended Entities (from Dependencies)

#### From spec-006: EvolutionConfig

```python
class EvolutionConfig(BaseSettings):
    """Configuration for evolution process."""

    population_size: int = 500    # Max strategies in store
    archive_size: int = 50        # Protected from pruning
    elite_ratio: float = 0.1      # 10% elite selection
    exploration_ratio: float = 0.2  # 20% random exploration
    max_concurrent: int = 2       # Parallel evaluations
```

#### From spec-006: FitnessMetrics

```python
@dataclass
class FitnessMetrics:
    """Strategy performance measurements."""

    sharpe_ratio: float
    calmar_ratio: float
    max_drawdown: float
    cagr: float
    total_return: float
    trade_count: int | None = None
    win_rate: float | None = None
```

#### From spec-006: Program

```python
@dataclass
class Program:
    """Evolved strategy with code, metrics, and lineage."""

    id: str
    code: str
    parent_id: str | None
    generation: int
    experiment: str | None
    metrics: FitnessMetrics | None
    created_at: float
```

---

## Entity Relationships

```
┌─────────────────┐
│EvolutionConfig  │◀────────────────────────────────┐
└────────┬────────┘                                  │
         │                                           │
         ▼                                           │
┌─────────────────┐    ┌───────────────┐    ┌───────┴───────┐
│EvolutionController│───▶│  ProgramStore │    │ StopCondition │
└────────┬────────┘    └───────────────┘    └───────────────┘
         │                      │
         │                      ▼
         │             ┌───────────────┐
         │             │    Program    │
         │             └───────────────┘
         │                      │
         │                      ▼
         │             ┌───────────────┐
         │             │FitnessMetrics │
         │             └───────────────┘
         │
         ├────────────────────────────────────────────┐
         │                                            │
         ▼                                            ▼
┌─────────────────┐                         ┌─────────────────┐
│ MutationRequest │                         │StrategyEvaluator│
└────────┬────────┘                         └─────────────────┘
         │
         ▼
┌─────────────────┐
│MutationResponse │
└─────────────────┘
```

---

## State Machine: Evolution Controller

```
     ┌─────────────────────────────────────────────────────┐
     │                                                      │
     ▼                                                      │
  ┌──────┐    start()    ┌─────────┐    stop()    ┌────────┤
  │ IDLE │──────────────▶│ RUNNING │─────────────▶│ PAUSED │
  └──────┘               └────┬────┘              └────────┘
                              │                        │
                              │ complete/error         │ resume()
                              │                        │
                              ▼                        │
                    ┌────────────────────┐             │
                    │ COMPLETED / FAILED │◀────────────┘
                    └────────────────────┘
```

---

## Database Schema Extension

No new tables required. Uses existing `programs` table from spec-006.

**Experiment Filtering**:
- All controller operations filter by `experiment` column
- Experiments are isolated by name (no cross-contamination)

---

## Validation Rules Summary

| Entity | Field | Validation |
|--------|-------|------------|
| MutationRequest | parent_code | Must contain EVOLVE-BLOCK markers |
| MutationRequest | retry_count | <= 3 |
| StopCondition | max_iterations | >= 1 |
| StopCondition | target_fitness | None or > 0 |
| EvolutionProgress | iteration | >= 0 |
| EvolutionProgress | generation | >= 0 |
