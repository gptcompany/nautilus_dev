# Research: Alpha-Evolve Controller & CLI

**Feature Branch**: `009-alpha-evolve-controller`
**Created**: 2025-12-27
**Status**: Complete

## Technical Context - Resolved Unknowns

### 1. LLM Integration for Mutations

**Decision**: Use Claude Code alpha-evolve agent via task delegation

**Rationale**:
- Alpha-evolve agent already exists in `.claude/agents/alpha-evolve.md`
- Agent uses Opus model and generates 3+ implementation approaches
- Integration via `Task` tool with `subagent_type='alpha-evolve'`
- Returns mutated EVOLVE-BLOCK code directly

**Alternatives Considered**:
1. Direct API calls to Claude API - Rejected: Adds external dependency, requires API key management
2. Local LLM (Ollama) - Rejected: Lower quality mutations, requires additional setup
3. Random genetic mutations - Rejected: Inferior to LLM-guided evolution

**Mutation Prompt Structure**:
```python
@dataclass
class MutationRequest:
    parent_code: str           # Full strategy code with EVOLVE-BLOCK
    parent_metrics: FitnessMetrics
    block_name: str = "decision_logic"
    guidance: str = ""         # Optional focus hints
```

### 2. CLI Framework Selection

**Decision**: Use `click` for CLI implementation

**Rationale**:
- Already used in `strategies/binance2nautilus/cli.py` (established pattern)
- Clean decorator-based command definitions
- Good progress bar support via `tqdm` integration
- Type hints and validation built-in

**Alternatives Considered**:
1. `argparse` - Rejected: More verbose, less feature-rich
2. `typer` - Rejected: Not established in codebase, adds dependency

**CLI Structure**:
```
evolve <command> [options]
├── start    - Begin evolution run
├── status   - Show progress
├── best     - Display top strategies
├── export   - Export strategy to file
├── stop     - Graceful shutdown
└── list     - List experiments
```

### 3. Concurrency Model

**Decision**: Single-threaded with async I/O

**Rationale**:
- Spec assumption: "Evolution runs single-threaded with async I/O"
- BacktestEngine is memory-intensive (~4GB per evaluation)
- `asyncio.Semaphore` already implemented in evaluator
- Simpler to reason about for debugging

**Alternatives Considered**:
1. Multiprocessing - Rejected: Memory overhead, complex state sharing
2. Threading - Rejected: GIL limits, potential race conditions

### 4. State Persistence Strategy

**Decision**: Use SQLite store with checkpoint after each iteration

**Rationale**:
- Store already exists (spec-006)
- Atomic transactions for insert+prune
- Recoverable from interruption via experiment name
- Simple resume mechanism

**Checkpoint Data**:
```python
@dataclass
class EvolutionCheckpoint:
    experiment: str
    iteration: int
    generation: int
    best_fitness: float
    elapsed_seconds: float
    status: str  # "running", "paused", "completed"
```

### 5. Parent Selection Distribution

**Decision**: Use configurable ratios (default 10/70/20)

**Rationale**:
- Spec defines: elite (10%), exploit (70%), explore (20%)
- Already implemented in `ProgramStore.sample(strategy=...)`
- Configurable via `EvolutionConfig`

**Selection Algorithm**:
```python
def select_parent_mode() -> str:
    r = random.random()
    if r < 0.10:  # 10%
        return "elite"
    elif r < 0.80:  # 70% (0.10-0.80)
        return "exploit"
    else:  # 20%
        return "explore"
```

### 6. Error Recovery Strategy

**Decision**: Log and continue for individual failures

**Rationale**:
- FR-003: "Controller MUST continue on individual evaluation failures"
- LLM failures should not halt evolution
- Retry mutations up to 3 times (FR-012)
- Log all failures for post-mortem analysis

**Error Categories**:
| Error Type | Handling |
|------------|----------|
| Syntax error in mutation | Retry with clarified prompt |
| Backtest timeout | Log and skip, continue |
| LLM API failure | Retry with backoff |
| Store error | Fail fast (data integrity) |

### 7. Progress Event System

**Decision**: Use callback-based progress reporting

**Rationale**:
- FR-005: "Controller MUST emit progress events for monitoring"
- Simple callback interface for CLI/dashboard integration
- Avoids complex event bus for initial implementation

**Event Types**:
```python
@dataclass
class ProgressEvent:
    event_type: str  # "iteration_start", "mutation", "evaluation", "iteration_complete"
    iteration: int
    data: dict  # Type-specific payload
```

## Dependencies Analysis

### Spec-006: Store (Implemented)
- `ProgramStore` ✓
- `FitnessMetrics` ✓
- `Program` ✓
- `apply_patch()` ✓

### Spec-007: Evaluator (Implemented)
- `StrategyEvaluator` ✓
- `BacktestConfig` ✓
- `EvaluationRequest` ✓
- `EvaluationResult` ✓

### Spec-008: Templates (Implemented)
- `BaseEvolveStrategy` ✓
- `MomentumEvolveStrategy` ✓
- EVOLVE-BLOCK markers ✓

## Best Practices Applied

### From Constitution
- [x] Black Box Design: Controller has clean interface, hidden implementation
- [x] KISS: Single-threaded, simple state machine
- [x] Native First: Uses native NautilusTrader components
- [x] Fail Fast: Validates config before evolution starts

### From CLAUDE.md
- [x] Use subagents: alpha-evolve for mutations
- [x] No df.iterrows(): Uses store for data access
- [x] Follow NautilusTrader patterns: Async where needed

## Integration Points

```
┌─────────────────────────────────────────────────────────────┐
│                    Alpha-Evolve Controller                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐               │
│  │   CLI    │───▶│ Controller│───▶│  Store   │ (spec-006)   │
│  └──────────┘    │          │    └──────────┘               │
│       │          │          │          │                     │
│       │          │          │          │                     │
│       ▼          ▼          ▼          ▼                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │  Config  │  │ Mutator  │  │Evaluator │  │Templates │     │
│  │(spec-006)│  │(LLM Task)│  │(spec-007)│  │(spec-008)│     │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │
│                     │                                        │
│                     ▼                                        │
│              ┌──────────────┐                                │
│              │ alpha-evolve │                                │
│              │    agent     │                                │
│              └──────────────┘                                │
└─────────────────────────────────────────────────────────────┘
```

## Open Questions (CLARIFIED)

1. **Mutation Retry Prompt**: When mutation fails syntax validation, include error message in retry prompt
2. **Graceful Shutdown**: Set flag, complete current iteration, persist state
3. **Resume Logic**: Load experiment from store, query max generation, continue from there
4. **Progress Format**: Human-readable for CLI, structured events for dashboard

## Next Steps

1. Generate data-model.md with entity definitions
2. Define CLI API contracts
3. Generate quickstart.md with usage examples
