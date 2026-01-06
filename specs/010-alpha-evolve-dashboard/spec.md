# Feature Specification: Alpha-Evolve Grafana Dashboard

**Feature Branch**: `010-alpha-evolve-dashboard`
**Created**: 2025-12-27
**Status**: Draft
**Input**: Dashboard Grafana per monitoring evoluzione. Fitness over generations, top 10 strategie, mutation success rate.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Fitness Progress Visualization (Priority: P2)

As a user monitoring evolution, I need to see fitness improvement over generations so that I can understand if evolution is making progress.

**Why this priority**: Primary insight into evolution health. Shows if process is working.

**Independent Test**: Can be fully tested by generating mock data and verifying chart displays correctly.

**Acceptance Scenarios**:

1. **Given** evolution data in store, **When** dashboard loads, **Then** time-series chart shows best fitness per generation.
2. **Given** multiple experiments, **When** filtering by experiment, **Then** chart shows only selected experiment.
3. **Given** fitness data, **When** hovering over point, **Then** tooltip shows generation, fitness value, strategy ID.
4. **Given** ongoing evolution, **When** dashboard auto-refreshes, **Then** new data points appear (5-second refresh).

---

### User Story 2 - Top Strategies Leaderboard (Priority: P2)

As a user, I need to see the top performing strategies so that I can identify the best candidates for production use.

**Why this priority**: Enables quick identification of best results. Primary output of evolution process.

**Independent Test**: Can be fully tested by populating store and verifying table displays correctly.

**Acceptance Scenarios**:

1. **Given** populated hall-of-fame, **When** dashboard loads, **Then** table shows top 10 strategies by fitness.
2. **Given** strategy in table, **When** viewing details, **Then** shows: ID, generation, Sharpe, Calmar, MaxDD, CAGR.
3. **Given** strategy ID in table, **When** clicking, **Then** can view strategy code (or copy to clipboard).
4. **Given** sorting options, **When** changing sort metric, **Then** table reorders by selected metric.

---

### User Story 3 - Population Statistics (Priority: P2)

As a user, I need population-level statistics so that I can understand evolution diversity and progress.

**Why this priority**: Provides context for individual strategy performance. Helps diagnose evolution issues.

**Independent Test**: Can be fully tested by calculating stats from store and verifying gauges display correctly.

**Acceptance Scenarios**:

1. **Given** population data, **When** dashboard loads, **Then** gauges show: population size, generation count, average fitness.
2. **Given** population data, **When** viewing stats, **Then** shows fitness distribution (min, max, median, std).
3. **Given** lineage data, **When** viewing stats, **Then** shows average mutations per lineage.

---

### User Story 4 - Mutation Success Tracking (Priority: P3)

As a user, I need to track mutation success rate so that I can understand LLM mutation quality.

**Why this priority**: Diagnostic information for tuning mutation prompts. Lower priority than core metrics.

**Independent Test**: Can be fully tested by logging mutations and verifying pie chart displays correctly.

**Acceptance Scenarios**:

1. **Given** mutation logs, **When** dashboard loads, **Then** pie chart shows: success, syntax error, runtime error, timeout.
2. **Given** mutation stats, **When** viewing over time, **Then** shows trend of success rate.
3. **Given** failed mutations, **When** drilling down, **Then** shows error categories.

---

### Edge Cases

- What happens when no evolution data exists (empty dashboard)?
- How does dashboard handle very large populations (10,000+ strategies)?
- What happens when QuestDB is unavailable?
- How are timezone differences handled in timestamps?
- What happens during dashboard refresh while evolution is writing?

## Requirements *(mandatory)*

### Functional Requirements

#### Dashboard Structure
- **FR-001**: Dashboard MUST have 4 main panels: Fitness Progress, Top Strategies, Population Stats, Mutation Stats
- **FR-002**: Dashboard MUST auto-refresh every 5 seconds during active evolution
- **FR-003**: Dashboard MUST support filtering by experiment name
- **FR-004**: Dashboard MUST be provisioned via JSON (Infrastructure as Code)

#### Fitness Progress Panel
- **FR-005**: Panel MUST show time-series of best fitness per generation
- **FR-006**: Panel MUST support multiple fitness metrics (Sharpe, Calmar, MaxDD)
- **FR-007**: Panel MUST show trend line or moving average overlay

#### Top Strategies Panel
- **FR-008**: Panel MUST show table with top 10 strategies
- **FR-009**: Table MUST include columns: Rank, ID, Generation, Sharpe, Calmar, MaxDD, CAGR
- **FR-010**: Table MUST be sortable by any metric column
- **FR-011**: Table MUST provide strategy code access (copy or link)

#### Population Stats Panel
- **FR-012**: Panel MUST show gauges for population size and generation count
- **FR-013**: Panel MUST show fitness distribution histogram
- **FR-014**: Panel MUST show current best vs average fitness comparison

#### Mutation Stats Panel
- **FR-015**: Panel MUST show pie chart of mutation outcomes (success/failure types)
- **FR-016**: Panel MUST show success rate percentage as gauge
- **FR-017**: Panel SHOULD show success rate trend over time

### Key Entities

- **DashboardConfig**: Grafana dashboard JSON structure
- **DataSource**: QuestDB connection configuration
- **Panel**: Individual visualization component (graph, table, gauge, pie)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Dashboard loads completely in under 3 seconds
- **SC-002**: Charts render correctly with populations up to 10,000 strategies
- **SC-003**: Auto-refresh works without page flicker or data loss
- **SC-004**: Dashboard is deployable via Grafana provisioning (no manual setup)
- **SC-005**: All panels display meaningful content with as few as 10 strategies

## Assumptions

- Grafana is already running and accessible
- QuestDB is available and contains evolution data
- User has dashboard viewer permissions
- Data is written to QuestDB by evolution controller (spec-009)

## Dependencies

- **spec-006**: Store schema defines metrics to display
- **Grafana**: Already running at localhost:3000
- **QuestDB**: Already running and healthy

## Out of Scope

- Real-time strategy execution visualization
- Interactive strategy editing
- Alerting/notification rules
- User authentication/authorization
- Dashboard embedding in external applications

---

## Future Enhancements (Black Book Concepts)

> **Source**: "The Black Book of Financial Hacking" - J.C. Lotter
> **Philosophy**: Add complexity ONLY if OOS shows problems.

### FE-001: Population Diversity Heatmap

**Current**: Single population statistics gauge

**Enhancement**: Visualize diversity over time with heatmap

```sql
-- Query for diversity heatmap
SELECT
    generation,
    AVG(code_similarity) as avg_similarity,
    STDDEV(fitness) as fitness_variance,
    COUNT(DISTINCT lineage_root) as unique_lineages
FROM
    population_history
GROUP BY
    generation
ORDER BY
    generation
```

**Visualization**: Heatmap with generation on X-axis, diversity metrics on Y-axis

**Trigger**: When evolution converges too quickly (need to diagnose when diversity drops)

**Trade-off**: Requires storing historical population snapshots, larger database

**Reference**: Black Book - "Monitor diversity to detect premature convergence"

### FE-002: Mutation Success Attribution

**Current**: Overall mutation success rate pie chart

**Enhancement**: Track which mutation prompts/strategies produce best results

```python
# Dashboard panel showing:
# - Elite mutations: 85% success rate (produce better child)
# - Exploit mutations: 45% success rate
# - Explore mutations: 15% success rate

# Bar chart: Mutation prompt → Success rate
# "Improve entry signals": 60%
# "Optimize exit timing": 55%
# "Add regime filter": 40%
# "Simplify logic": 35%
```

**Trigger**: When mutation success rate is consistently low (<30%)

**Trade-off**: Requires storing mutation prompts and outcomes, more complex queries

**Reference**: Black Book - "Measure what you manage - track mutation effectiveness"

### FE-003: Fitness Landscape Visualization

**Current**: Time-series of best fitness

**Enhancement**: 2D projection of fitness landscape (PCA/t-SNE)

```python
# Reduce strategy behavior space to 2D
# X-axis: PC1 (e.g., trade frequency)
# Y-axis: PC2 (e.g., holding time)
# Color: Fitness (red = low, green = high)
# Size: Generation (larger = newer)

# Shows:
# - Clusters of similar strategies
# - Exploration vs exploitation patterns
# - Local optima (fitness peaks)
```

**Trigger**: When evolution gets stuck (visualize where population is exploring)

**Trade-off**: Requires dimensionality reduction (PCA/t-SNE), complex computation

**Reference**: Black Book - "Visualize search space to understand convergence"

### FE-004: Lineage Tree Visualization

**Current**: Table of top strategies with parent_id

**Enhancement**: Interactive tree showing strategy lineage

```python
# D3.js tree visualization:
# - Root: Seed strategy
# - Branches: Lineages
# - Nodes: Individual strategies
# - Color: Fitness (green = good, red = poor)
# - Click node → show strategy code diff vs parent

# Shows:
# - Which lineages are productive
# - Dead-end branches (no improvement)
# - Breakthrough mutations (sudden fitness jump)
```

**Trigger**: When diagnosing why certain lineages dominate hall-of-fame

**Trade-off**: Requires frontend JavaScript (D3.js), more complex dashboard

**Reference**: Black Book - "Track lineage to understand evolution dynamics"

### FE-005: Overfitting Detection

**Current**: Single fitness metric

**Enhancement**: In-sample vs out-of-sample performance tracking

```sql
-- Query for overfitting detection
SELECT
    strategy_id,
    in_sample_sharpe,
    out_of_sample_sharpe,
    (in_sample_sharpe - out_of_sample_sharpe) as degradation
FROM
    strategy_metrics
WHERE
    degradation > 0.5  -- Flag potential overfitting
ORDER BY
    degradation DESC
```

**Panel**: Table showing strategies with largest IS/OOS gaps (overfitting red flags)

**Trigger**: When evolved strategies fail in live trading despite good backtest

**Trade-off**: Requires walk-forward validation during evolution (slower), more storage

**Reference**: Black Book - "Always validate OOS to detect overfitting early"

---

**Decision Log** (2026-01-06):
- Simple time-series and tables chosen for MVP
- Population stats and mutation success tracked
- Black Book enhancements documented for deeper diagnostics
