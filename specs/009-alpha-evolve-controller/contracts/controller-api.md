# Controller API Contract: Alpha-Evolve

**Feature Branch**: `009-alpha-evolve-controller`
**Created**: 2025-12-27

## EvolutionController

Main orchestrator class for the evolution loop.

### Constructor

```python
class EvolutionController:
    def __init__(
        self,
        config: EvolutionConfig,
        store: ProgramStore,
        evaluator: StrategyEvaluator,
        mutator: Mutator | None = None,  # Defaults to LLM-based mutator
    ) -> None:
        """
        Initialize evolution controller.

        Args:
            config: Evolution configuration (population, selection ratios)
            store: Strategy persistence store (spec-006)
            evaluator: Backtest evaluator (spec-007)
            mutator: Code mutation provider (defaults to Claude agent)

        Raises:
            ValueError: If config is invalid
        """
```

---

### Core Methods

#### `run()`

```python
async def run(
    self,
    seed_strategy: str,
    experiment: str,
    iterations: int,
    stop_condition: StopCondition | None = None,
    on_progress: Callable[[ProgressEvent], None] | None = None,
) -> EvolutionResult:
    """
    Execute evolution loop.

    Args:
        seed_strategy: Name of seed strategy ("momentum")
        experiment: Unique experiment name
        iterations: Number of iterations to run
        stop_condition: Optional early termination conditions
        on_progress: Callback for progress events

    Returns:
        EvolutionResult with final statistics

    Raises:
        ValueError: If seed strategy not found
        RuntimeError: If evolution fails unrecoverably
    """
```

**Iteration Flow**:
```
for iteration in range(iterations):
    1. Select parent (elite/exploit/explore)
    2. Request mutation from LLM
    3. Validate mutation syntax
    4. If valid: evaluate via backtest
    5. Store result with metrics
    6. Prune population if needed
    7. Emit progress event
    8. Check stop conditions
```

---

#### `stop()`

```python
def stop(self, force: bool = False) -> None:
    """
    Request graceful stop.

    Args:
        force: If True, interrupt immediately
               If False, complete current iteration

    Note:
        Sets status to PAUSED, persists state for resume.
    """
```

---

#### `resume()`

```python
async def resume(
    self,
    experiment: str,
    additional_iterations: int = 0,
    on_progress: Callable[[ProgressEvent], None] | None = None,
) -> EvolutionResult:
    """
    Resume paused evolution.

    Args:
        experiment: Experiment name to resume
        additional_iterations: Extra iterations beyond original target
        on_progress: Callback for progress events

    Returns:
        EvolutionResult with final statistics

    Raises:
        ValueError: If experiment not found or not paused
    """
```

---

#### `get_progress()`

```python
def get_progress(self, experiment: str | None = None) -> EvolutionProgress:
    """
    Get current evolution progress.

    Args:
        experiment: Experiment name (None for active experiment)

    Returns:
        EvolutionProgress snapshot

    Raises:
        ValueError: If experiment not found
    """
```

---

### Parent Selection

#### `_select_parent()`

```python
def _select_parent(self, experiment: str) -> Program:
    """
    Select parent strategy for mutation.

    Selection strategy distribution:
        - 10% elite: Random from top 10% by fitness
        - 70% exploit: Fitness-weighted random
        - 20% explore: Uniform random

    Args:
        experiment: Experiment name for filtering

    Returns:
        Selected parent Program

    Raises:
        RuntimeError: If store is empty
    """
```

---

### Mutation

#### `_request_mutation()`

```python
async def _request_mutation(
    self,
    parent: Program,
    retry_count: int = 0,
) -> MutationResponse:
    """
    Request code mutation from LLM.

    Args:
        parent: Parent strategy to mutate
        retry_count: Current retry attempt (max 3)

    Returns:
        MutationResponse with mutated code or error

    Note:
        Uses alpha-evolve agent via Task tool delegation.
        Includes parent metrics in prompt for informed mutation.
    """
```

---

## Mutator Protocol

Interface for mutation providers.

```python
class Mutator(Protocol):
    """Protocol for code mutation providers."""

    async def mutate(
        self,
        request: MutationRequest,
    ) -> MutationResponse:
        """
        Generate mutation for strategy code.

        Args:
            request: Mutation request with parent code and metrics

        Returns:
            MutationResponse with mutated code or error
        """
        ...
```

---

## LLMMutator

Default implementation using Claude Code alpha-evolve agent.

```python
class LLMMutator:
    """LLM-based code mutation using alpha-evolve agent."""

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        """
        Initialize LLM mutator.

        Args:
            max_retries: Maximum retry attempts per mutation
            retry_delay: Delay between retries in seconds
        """

    async def mutate(
        self,
        request: MutationRequest,
    ) -> MutationResponse:
        """
        Request mutation via alpha-evolve agent.

        Prompt structure:
            1. Parent strategy code (with EVOLVE-BLOCK)
            2. Parent performance metrics
            3. Mutation guidance (optional)
            4. Previous error context (if retry)

        Returns:
            MutationResponse with patched code or error
        """
```

**Mutation Prompt Template**:
```
You are mutating a trading strategy. Improve the EVOLVE-BLOCK decision logic.

Parent Strategy Performance:
- Calmar: {calmar}
- Sharpe: {sharpe}
- Max DD: {max_dd}
- CAGR: {cagr}
- Win Rate: {win_rate}

Parent Code:
```python
{parent_code}
```

Requirements:
1. Only modify code inside # === EVOLVE-BLOCK: decision_logic ===
2. Use native NautilusTrader indicators (no custom implementations)
3. Return ONLY the new EVOLVE-BLOCK body code

{retry_context if previous_error}
```

---

## EvolutionResult

```python
@dataclass
class EvolutionResult:
    """Final result from evolution run."""

    experiment: str
    status: EvolutionStatus
    iterations_completed: int
    best_strategy: Program
    final_population_size: int
    elapsed_seconds: float

    # Statistics
    total_mutations: int
    successful_mutations: int
    total_evaluations: int
    successful_evaluations: int

    # Early stop reason (if applicable)
    stop_reason: str | None = None
```

---

## Error Handling

### Recoverable Errors

| Error | Handling |
|-------|----------|
| Mutation syntax error | Retry with error context (max 3) |
| Evaluation timeout | Log, skip, continue |
| LLM API rate limit | Exponential backoff retry |

### Unrecoverable Errors

| Error | Handling |
|-------|----------|
| Store corruption | Fail fast, set status FAILED |
| Invalid seed strategy | Raise ValueError |
| Missing EVOLVE-BLOCK | Raise ValueError |

---

## Thread Safety

- Controller is **not thread-safe**
- Use async/await for concurrent operations
- Store uses SQLite transactions for atomicity
- Evaluator uses semaphore for concurrency limit

---

## Logging

```python
# Controller logs to:
import logging
logger = logging.getLogger("alpha_evolve.controller")

# Log levels:
# DEBUG: Iteration details, parent selection
# INFO: Start/stop, best fitness updates
# WARNING: Mutation retries, evaluation timeouts
# ERROR: Unrecoverable failures
```
