# Feature Specification: Alpha-Evolve Controller & CLI

**Feature Branch**: `009-alpha-evolve-controller`
**Created**: 2025-12-27
**Status**: Implemented
**Input**: Loop di evoluzione e interfaccia CLI. Parent selection (elite/exploit/explore), integrazione alpha-evolve agent per mutazioni, pruning automatico popolazione.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Evolution Loop Execution (Priority: P1)

As a user, I need to run an evolution loop that iteratively mutates and evaluates strategies so that I can discover improved trading logic automatically.

**Why this priority**: Core system functionality. Everything else supports this main loop.

**Independent Test**: Can be fully tested by running single iteration and verifying seed → mutate → evaluate → store cycle completes.

**Acceptance Scenarios**:

1. **Given** seed strategy and configured iterations, **When** evolution.run() is called, **Then** loop executes specified number of iterations.
2. **Given** running evolution, **When** iteration completes, **Then** child strategy is stored in hall-of-fame with metrics.
3. **Given** evolution progress, **When** requesting status, **Then** returns current generation, best fitness, population size.
4. **Given** evolution in progress, **When** error occurs in single evaluation, **Then** loop continues with next iteration.
5. **Given** configured stop condition (e.g., target fitness), **When** condition met, **Then** evolution stops early.

---

### User Story 2 - Parent Selection Strategy (Priority: P1)

As an evolution system, I need intelligent parent selection so that evolution balances exploitation (improving good strategies) with exploration (discovering new approaches).

**Why this priority**: Selection pressure drives evolution quality. Without proper selection, evolution degrades to random search.

**Independent Test**: Can be fully tested by running many selections and verifying distribution matches expected ratios.

**Acceptance Scenarios**:

1. **Given** selection mode="elite" (10% of selections), **When** selecting parent, **Then** returns random strategy from top 10% by fitness.
2. **Given** selection mode="exploit" (70% of selections), **When** selecting parent, **Then** returns strategy weighted by fitness (better strategies selected more often).
3. **Given** selection mode="explore" (20% of selections), **When** selecting parent, **Then** returns random strategy from full population.
4. **Given** 1000 parent selections, **When** counting by mode, **Then** approximately 10% elite, 70% exploit, 20% explore.

---

### User Story 3 - LLM Mutation Integration (Priority: P1)

As an evolution system, I need to request code mutations from Claude Code so that strategy improvements are guided by language model understanding.

**Why this priority**: LLM-guided mutation is the differentiator from random genetic algorithms. Quality of mutations determines evolution success.

**Independent Test**: Can be fully tested by requesting mutation and verifying EVOLVE-BLOCK is modified appropriately.

**Acceptance Scenarios**:

1. **Given** parent strategy EVOLVE-BLOCK, **When** requesting mutation, **Then** returns modified EVOLVE-BLOCK code.
2. **Given** mutation prompt with parent performance, **When** LLM responds, **Then** mutation attempts to improve on parent weaknesses.
3. **Given** invalid mutation (syntax error), **When** detected, **Then** retry with clarified prompt (max 3 retries).
4. **Given** mutation request, **When** prompt is built, **Then** includes parent code, parent metrics, and mutation guidance.

---

### User Story 4 - CLI Interface (Priority: P1)

As a user, I need a command-line interface to start, monitor, and manage evolution runs so that I can operate the system without writing code.

**Why this priority**: Primary user interface. Enables non-programmatic usage.

**Independent Test**: Can be fully tested by running CLI commands and verifying expected behavior.

**Acceptance Scenarios**:

1. **Given** CLI command `evolve start --seed momentum --iterations 50`, **When** executed, **Then** evolution starts with momentum seed for 50 iterations.
2. **Given** running evolution, **When** `evolve status` is called, **Then** displays current progress, best fitness, ETA.
3. **Given** completed evolution, **When** `evolve best` is called, **Then** displays top strategy with metrics.
4. **Given** evolution ID, **When** `evolve export <id>` is called, **Then** exports strategy code to file.
5. **Given** running evolution, **When** `evolve stop` is called, **Then** gracefully stops after current iteration.

---

### User Story 5 - Experiment Management (Priority: P2)

As a user, I need to organize evolution runs into named experiments so that I can compare different configurations and track progress.

**Why this priority**: Enables systematic experimentation. Not blocking for initial implementation.

**Independent Test**: Can be fully tested by creating experiments and verifying isolation.

**Acceptance Scenarios**:

1. **Given** `--experiment btc_momentum_v1`, **When** evolution runs, **Then** all data stored under experiment name.
2. **Given** multiple experiments, **When** `evolve list`, **Then** shows all experiments with summary stats.
3. **Given** experiment name, **When** `evolve resume <experiment>`, **Then** continues from last checkpoint.

---

### Edge Cases

- What happens when hall-of-fame is empty (first iteration)?
- What happens when LLM API is unavailable?
- How does system handle keyboard interrupt during evolution?
- What happens when disk space is exhausted during evolution?
- How does system recover from partial database corruption?

## Requirements *(mandatory)*

### Functional Requirements

#### Evolution Loop
- **FR-001**: Controller MUST execute configurable number of iterations
- **FR-002**: Controller MUST persist state after each iteration (resumable)
- **FR-003**: Controller MUST continue on individual evaluation failures
- **FR-004**: Controller MUST support stop conditions (iterations, fitness, time)
- **FR-005**: Controller MUST emit progress events for monitoring

#### Parent Selection
- **FR-006**: Controller MUST implement 3-tier selection: elite (10%), exploit (70%), explore (20%)
- **FR-007**: Selection ratios MUST be configurable via config.yaml
- **FR-008**: Exploit selection MUST use fitness-weighted probability
- **FR-009**: Elite selection MUST use top-k from hall-of-fame

#### LLM Integration
- **FR-010**: Controller MUST build mutation prompts with parent code and metrics
- **FR-011**: Controller MUST validate mutation output is syntactically valid
- **FR-012**: Controller MUST retry failed mutations (max 3 attempts)
- **FR-013**: Controller MUST log mutation prompts and responses for debugging
- **FR-014**: Controller MUST integrate with alpha-evolve agent for mutations

#### CLI
- **FR-015**: CLI MUST provide `start` command with seed and iterations options
- **FR-016**: CLI MUST provide `status` command showing evolution progress
- **FR-017**: CLI MUST provide `best` command showing top strategy
- **FR-018**: CLI MUST provide `export` command to save strategy to file
- **FR-019**: CLI MUST provide `stop` command for graceful shutdown
- **FR-020**: CLI MUST provide `list` command showing all experiments

### Key Entities

- **EvolutionController**: Main orchestrator. Coordinates selection, mutation, evaluation, storage.
- **MutationRequest**: Request to LLM. Attributes: parent_code, parent_metrics, mutation_prompt
- **MutationResponse**: LLM response. Attributes: mutated_code, success, error
- **EvolutionProgress**: Current state. Attributes: iteration, generation, best_fitness, population_size, elapsed_time

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Complete evolution loop (50 iterations) finishes in under 2 hours
- **SC-002**: 80% of LLM mutations produce syntactically valid code
- **SC-003**: Evolution shows fitness improvement in 70% of 50+ iteration runs
- **SC-004**: System recovers gracefully from interruption and resumes correctly
- **SC-005**: CLI commands respond in under 2 seconds (excluding evolution start)

## Assumptions

- Claude Code alpha-evolve agent is available for mutation requests
- Network connectivity to LLM is stable during evolution
- Evolution runs single-threaded with async I/O
- Experiments are isolated by name (no cross-contamination)

## Dependencies

- **spec-006**: Store for hall-of-fame, patching for mutations
- **spec-007**: Evaluator for fitness calculation
- **spec-008**: Strategy templates for seed strategies

## Out of Scope

- Distributed evolution across multiple machines
- Real-time visualization (see spec-010 for dashboard)
- Automatic hyperparameter tuning
- Strategy ensembling or combination

---

## Future Enhancements (Black Book Concepts)

> **Source**: "The Black Book of Financial Hacking" - J.C. Lotter
> **Philosophy**: Add complexity ONLY if OOS shows problems.

### FE-001: Adaptive Mutation Rate Control

**Current**: Fixed elite/exploit/explore ratios (10%/70%/20%)

**Enhancement**: Dynamic adjustment based on population diversity and progress

```python
class AdaptiveMutationController:
    """
    Adjust mutation strategy based on evolution health metrics.
    """
    def select_mutation_mode(self, population, history):
        # Calculate diversity (0-1 scale)
        diversity = self.calculate_code_diversity(population)

        # Calculate progress (fitness improvement rate)
        recent_gains = history[-10:]  # Last 10 generations
        progress = np.mean([g.best_fitness - g_prev.best_fitness
                           for g, g_prev in zip(recent_gains[1:], recent_gains)])

        # Low diversity + no progress = increase exploration
        if diversity < 0.2 and progress < 0.01:
            return {'elite': 0.05, 'exploit': 0.45, 'explore': 0.50}

        # High diversity + good progress = increase exploitation
        elif diversity > 0.6 and progress > 0.05:
            return {'elite': 0.20, 'exploit': 0.75, 'explore': 0.05}

        # Default
        else:
            return {'elite': 0.10, 'exploit': 0.70, 'explore': 0.20}
```

**Trigger**: When evolution plateaus (no improvement for 50+ generations) or converges too quickly

**Trade-off**: Requires diversity metric (code diff? AST distance?), more complex tuning

**Reference**: Eiben et al. (1999) "Parameter Control in Evolutionary Algorithms"

### FE-002: Prompt Engineering Evolution

**Current**: Static mutation prompts

**Enhancement**: Evolve prompts based on mutation success rate

```python
class PromptEvolution:
    """
    Meta-learning for mutation prompts.

    Track which prompt styles produce best mutations.
    """
    def __init__(self):
        self.prompt_templates = [
            "Improve entry signals to reduce false positives",
            "Optimize exit timing to capture larger moves",
            "Add regime filter to avoid choppy markets",
            "Simplify logic to reduce overfitting"
        ]
        self.prompt_scores = [0.0] * len(self.prompt_templates)

    def select_prompt(self):
        # Thompson sampling for prompt selection
        samples = [np.random.beta(1 + score, 1) for score in self.prompt_scores]
        return self.prompt_templates[np.argmax(samples)]

    def update_prompt_score(self, prompt_idx, child_fitness, parent_fitness):
        improvement = child_fitness - parent_fitness
        # Reward prompt if child improved
        self.prompt_scores[prompt_idx] += improvement
```

**Trigger**: When mutation success rate is low (<30% produce better strategies)

**Trade-off**: Requires tracking prompt→outcome, but improves mutation quality over time

**Reference**: Black Book - "Evolve the evolution process itself"

### FE-003: Ensemble Strategy Selection

**Current**: Single best strategy from hall-of-fame

**Enhancement**: Deploy ensemble of top-k strategies with voting

```python
class EnsembleSelector:
    """
    Instead of single best, use ensemble for robustness.
    """
    def select_ensemble(self, hall_of_fame, k=5):
        # Get top-k strategies with low correlation
        top_strategies = hall_of_fame.top_k(k=20)

        # Calculate pairwise correlation of equity curves
        correlations = self.calculate_equity_correlation(top_strategies)

        # Select k strategies that maximize diversity
        ensemble = []
        ensemble.append(top_strategies[0])  # Best strategy

        for _ in range(k - 1):
            # Add strategy with lowest avg correlation to ensemble
            candidates = [s for s in top_strategies if s not in ensemble]
            best_candidate = min(
                candidates,
                key=lambda s: np.mean([correlations[s, e] for e in ensemble])
            )
            ensemble.append(best_candidate)

        return ensemble
```

**Trigger**: When single best strategy has high variance or fails in live trading

**Trade-off**: More complex deployment (multiple strategies), but more robust

**Reference**: Black Book - "Ensembles reduce model risk"

### FE-004: Novelty Search

**Current**: Fitness-only selection

**Enhancement**: Reward novel strategies even if not immediately high-fitness

```python
class NoveltySearch:
    """
    Maintain archive of novel behaviors to prevent convergence.
    """
    def __init__(self, k_neighbors=15):
        self.archive = []
        self.k_neighbors = k_neighbors

    def novelty_score(self, strategy):
        """
        Novelty = average distance to k-nearest neighbors in behavior space.

        Behavior space: equity curve shape, trade frequency, holding time, etc.
        """
        if len(self.archive) < self.k_neighbors:
            return float('inf')  # Everything is novel initially

        behavior = self.extract_behavior(strategy)
        distances = [self.behavior_distance(behavior, archived)
                    for archived in self.archive]
        k_nearest = sorted(distances)[:self.k_neighbors]
        return np.mean(k_nearest)

    def combined_fitness(self, strategy, alpha=0.5):
        """
        Combine fitness and novelty.

        fitness_combined = alpha * fitness + (1-alpha) * novelty
        """
        return alpha * strategy.fitness + (1 - alpha) * self.novelty_score(strategy)
```

**Trigger**: When evolution converges to local optimum (all strategies similar)

**Trade-off**: Requires behavior extraction and distance metric, slower convergence

**Reference**: Lehman & Stanley (2011) "Abandoning Objectives: Evolution Through the Search for Novelty Alone"

---

**Decision Log** (2026-01-06):
- Fixed mutation ratios chosen for MVP simplicity
- Static mutation prompts (no meta-learning yet)
- Single best strategy selection
- Black Book enhancements documented for plateaus and convergence issues
