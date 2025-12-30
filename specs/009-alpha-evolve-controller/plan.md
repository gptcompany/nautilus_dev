# Implementation Plan: Alpha-Evolve Controller & CLI

**Feature Branch**: `009-alpha-evolve-controller`
**Created**: 2025-12-27
**Status**: Complete ✅
**Spec Reference**: `specs/009-alpha-evolve-controller/spec.md`

## Architecture Overview

The Alpha-Evolve Controller orchestrates the evolutionary loop for strategy optimization. It coordinates parent selection, LLM-guided mutations, backtest evaluation, and population management.

### System Context

```
┌─────────────────────────────────────────────────────────────┐
│                    Alpha-Evolve System                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐               │
│  │   CLI    │───▶│Controller│───▶│  Store   │ (spec-006)   │
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

### Component Diagram

```
User                CLI                 Controller
  │                  │                      │
  │─ evolve start ──▶│                      │
  │                  │─ run() ─────────────▶│
  │                  │                      │─ select_parent()
  │                  │                      │
  │                  │                      │─ request_mutation()
  │                  │                      │     │
  │                  │                      │     ▼ (alpha-evolve agent)
  │                  │                      │◀──── mutated_code
  │                  │                      │
  │                  │                      │─ evaluate()
  │                  │                      │     │
  │                  │                      │     ▼ (BacktestEngine)
  │                  │                      │◀──── FitnessMetrics
  │                  │                      │
  │                  │                      │─ store.insert()
  │                  │                      │─ store.prune()
  │                  │                      │
  │◀── progress ─────│◀── on_progress() ───│
  │                  │                      │
```

## Technical Decisions

### Decision 1: LLM Integration Method

**Options Considered**:
1. **Direct Claude API**: Call API directly with mutation prompts
   - Pros: Full control, lower latency
   - Cons: API key management, external dependency
2. **Alpha-Evolve Agent Delegation**: Use Task tool to delegate to agent
   - Pros: Already exists, Opus quality, consistent patterns
   - Cons: Slightly higher overhead

**Selected**: Option 2 (Alpha-Evolve Agent Delegation)

**Rationale**: The alpha-evolve agent is already configured with the correct context, uses Opus model for high-quality mutations, and follows established patterns in the codebase.

---

### Decision 2: CLI Framework

**Options Considered**:
1. **argparse**: Standard library
   - Pros: No dependencies
   - Cons: Verbose, limited features
2. **click**: Decorator-based CLI framework
   - Pros: Already used in codebase, clean syntax, good progress support
   - Cons: External dependency (already present)

**Selected**: Option 2 (click)

**Rationale**: Consistent with existing `binance2nautilus/cli.py` pattern. Click provides better UX with progress bars and command grouping.

---

### Decision 3: Concurrency Model

**Options Considered**:
1. **Multiprocessing**: Parallel evaluations across processes
   - Pros: True parallelism, CPU utilization
   - Cons: Memory overhead, complex state sharing
2. **Single-threaded async**: One evaluation at a time with async I/O
   - Pros: Simple, memory efficient, easy debugging
   - Cons: Sequential evaluations

**Selected**: Option 2 (Single-threaded async)

**Rationale**: Per spec assumption "Evolution runs single-threaded with async I/O". BacktestEngine is memory-intensive (~4GB), so parallel evaluations risk OOM.

---

## Implementation Strategy

### Phase 1: Foundation (Complete)

**Goal**: Design documentation and contracts

**Deliverables**:
- [x] research.md - Technical decisions and unknowns resolution
- [x] data-model.md - Entity definitions and relationships
- [x] contracts/cli-api.md - CLI command specifications
- [x] contracts/controller-api.md - Python API specifications
- [x] quickstart.md - Usage examples

**Dependencies**: None

---

### Phase 2: Core Implementation (Complete)

**Goal**: Implement EvolutionController and Mutator

**Deliverables**:
- [x] `scripts/alpha_evolve/controller.py`
  - EvolutionController class
  - StopCondition dataclass
  - EvolutionProgress dataclass
  - EvolutionResult dataclass
- [x] `scripts/alpha_evolve/mutator.py`
  - Mutator protocol
  - LLMMutator implementation
  - MutationRequest/MutationResponse dataclasses
- [x] `tests/alpha_evolve/test_controller.py`
- [x] `tests/alpha_evolve/test_mutator.py`

**Dependencies**: Phase 1

---

### Phase 3: CLI Implementation (Complete)

**Goal**: Implement click-based CLI

**Deliverables**:
- [x] `scripts/alpha_evolve/cli.py`
  - start command
  - status command
  - best command
  - export command
  - stop command
  - list command
  - resume command
- [x] CLI entry point in `pyproject.toml` or setup
- [x] `tests/alpha_evolve/test_cli.py`

**Dependencies**: Phase 2

---

### Phase 4: Integration & Testing (Complete)

**Goal**: End-to-end testing and documentation

**Deliverables**:
- [x] `tests/alpha_evolve/test_controller_integration.py`
- [x] Update `docs/` with CLI usage → `docs/alpha-evolve-cli.md`
- [x] Performance benchmarks → `scripts/alpha_evolve/benchmark.py`

**Dependencies**: Phase 3

---

## File Structure

```
scripts/alpha_evolve/
├── __init__.py
├── config.py           # EvolutionConfig (spec-006) ✓
├── store.py            # ProgramStore (spec-006) ✓
├── patching.py         # EVOLVE-BLOCK patching (spec-006) ✓
├── evaluator.py        # StrategyEvaluator (spec-007) ✓
├── templates/
│   ├── __init__.py     # ✓
│   ├── base.py         # BaseEvolveStrategy (spec-008) ✓
│   └── momentum.py     # MomentumEvolveStrategy (spec-008) ✓
├── controller.py       # NEW: EvolutionController
├── mutator.py          # NEW: LLMMutator
└── cli.py              # NEW: Click CLI

tests/alpha_evolve/
├── test_controller.py          # NEW
├── test_controller_integration.py  # NEW
├── test_mutator.py             # NEW
└── test_cli.py                 # NEW
```

## API Design

### Public Interface

```python
# Controller
class EvolutionController:
    def __init__(self, config, store, evaluator, mutator=None): ...
    async def run(self, seed_strategy, experiment, iterations, ...): ...
    def stop(self, force=False): ...
    async def resume(self, experiment, additional_iterations=0): ...
    def get_progress(self, experiment=None): ...

# Mutator
class LLMMutator:
    async def mutate(self, request: MutationRequest) -> MutationResponse: ...

# CLI
@click.group()
def evolve(): ...

@evolve.command()
def start(seed, iterations, experiment, ...): ...
```

## Testing Strategy

### Unit Tests
- [ ] EvolutionController.run() with mock mutator/evaluator
- [ ] Parent selection distribution validation
- [ ] Stop conditions triggering correctly
- [ ] Progress event emission

### Integration Tests
- [ ] Full evolution loop with real evaluator (short run)
- [ ] Resume from checkpoint
- [ ] Graceful shutdown and resume
- [ ] CLI commands with test database

### Performance Tests
- [ ] 50-iteration run completes in < 2 hours (SC-001)
- [ ] 80% mutation success rate (SC-002)

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| LLM mutations low quality | High | Medium | Retry logic, mutation prompt tuning |
| Memory exhaustion during backtest | High | Low | Single-threaded, semaphore |
| Evolution stagnation | Medium | Medium | Exploration ratio, fitness diversity |
| API rate limits | Medium | Low | Exponential backoff, local caching |

## Dependencies

### External Dependencies
- NautilusTrader >= 1.222.0 (nightly)
- click >= 8.0 (CLI)
- pydantic-settings >= 2.0 (config)
- tqdm >= 4.0 (progress bars)

### Internal Dependencies
- spec-006: Store, Config, Patching
- spec-007: Evaluator
- spec-008: Templates, Seed strategies
- alpha-evolve agent: LLM mutations

## Acceptance Criteria

- [x] Phase 1 documentation complete
- [x] All unit tests passing (coverage > 80%)
- [x] CLI commands functional
- [x] Integration tests passing
- [x] 50-iteration evolution completes successfully → `benchmark.py` validates SC-001
- [x] Resume from interrupt works
- [x] Documentation updated → `docs/alpha-evolve-cli.md`
