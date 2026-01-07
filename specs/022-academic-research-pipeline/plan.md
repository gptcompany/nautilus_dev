# Implementation Plan: Academic Research → Trading Strategy Pipeline

**Feature Branch**: `022-academic-research-pipeline`
**Created**: 2025-12-28
**Status**: Draft
**Spec Reference**: `specs/022-academic-research-pipeline/spec.md`

## Architecture Overview

This feature creates a bridge between the academic research system (`/media/sam/1TB1/academic_research`) and the trading strategy development pipeline (`nautilus_dev`), enabling automatic conversion of academic trading papers into NautilusTrader-compatible specifications.

### System Context

```
┌─────────────────────────────────────────────────────────────────────┐
│                    RESEARCH DOMAIN                                   │
│                 /media/sam/1TB1/academic_research                     │
│                                                                      │
│  User: "Research momentum strategies"                               │
│         ↓                                                           │
│  [semantic-router] → [paper-search] → [gemini-cli]                  │
│         ↓                                                           │
│  [memory.json] ← strategy__ entities                                │
│                                                                      │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ BRIDGE
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    TRADING DOMAIN                                    │
│                  /media/sam/1TB/nautilus_dev                         │
│                                                                      │
│  [strategy-researcher] ← reads memory.json                          │
│         ↓                                                           │
│  [paper-to-strategy skill] → spec.md                                │
│         ↓                                                           │
│  [speckit] → plan.md → tasks.md                                     │
│         ↓                                                           │
│  [alpha-evolve] → 3+ implementations                                │
│         ↓                                                           │
│  [nautilus-coder] → working strategy                                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Diagram

```
ACADEMIC_RESEARCH                          NAUTILUS_DEV
================                          ============

semantic_router_mcp/                      .claude/
├── routes_config.py                      ├── agents/
│   └── TRADING_STRATEGY_UTTERANCES       │   └── strategy-researcher.md [NEW]
│       (20+ routes) [NEW]                ├── skills/
│                                         │   └── paper-to-strategy/
docs/                                     │       └── SKILL.md [NEW]
├── entity_schemas.md                     │
│   └── strategy__ schema [NEW]           scripts/
│                                         └── sync_research.py [NEW]
memory.json
└── strategy__ entities [AUTO]            docs/research/
                                          └── strategies.json [SYNCED]
```

---

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| Black Box Design | ✅ PASS | strategy-researcher is modular, replaceable |
| KISS & YAGNI | ✅ PASS | Only building what's needed for paper→spec |
| Native First | ✅ PASS | Uses existing speckit, alpha-evolve |
| NO df.iterrows() | N/A | No pandas in this feature |
| TDD Discipline | ✅ PASS | Test plan included |
| Subagent Usage | ✅ PASS | New agent follows pattern |
| Skill Usage | ✅ PASS | New skill follows pattern |

---

## Technical Decisions

### Decision 1: Where to Store Trading Routes?

**Options Considered**:
1. **Option A**: Extend existing `STEM_CS_UTTERANCES`
   - Pros: No new route type, simpler
   - Cons: Mixed with non-trading CS topics, less accurate classification
2. **Option B**: Create new `TRADING_STRATEGY` route
   - Pros: Dedicated classification, specialized processing, clearer intent
   - Cons: More configuration, one more route to maintain

**Selected**: Option B

**Rationale**: Trading papers have distinct vocabulary (momentum, mean reversion, Sharpe ratio). Separate route enables specialized downstream processing and clearer metrics.

---

### Decision 2: Entity Storage Architecture

**Options Considered**:
1. **Option A**: Store strategy__ only in academic_research/memory.json
   - Pros: Single source of truth
   - Cons: nautilus_dev must always read from external path
2. **Option B**: Sync to nautilus_dev via script
   - Pros: nautilus_dev has local copy, works offline
   - Cons: Potential sync staleness
3. **Option C**: Dual-write to both repos
   - Pros: Always in sync
   - Cons: Complex, potential conflicts

**Selected**: Option B

**Rationale**: Single source of truth in academic_research, with periodic sync to nautilus_dev. Sync script includes timestamps to detect staleness.

---

### Decision 3: Paper Analysis Tool Selection

**Options Considered**:
1. **Option A**: Always use gemini-cli (2M tokens)
   - Pros: Handles any paper size
   - Cons: $0.15/paper, overkill for short papers
2. **Option B**: Always use Claude context (200k tokens)
   - Pros: Included in usage, fast
   - Cons: Can't handle 100+ page papers
3. **Option C**: Hybrid (Claude for <50 pages, Gemini for >50)
   - Pros: Cost-effective, handles all sizes
   - Cons: Logic to detect paper length

**Selected**: Option C

**Rationale**: Most trading papers are 20-40 pages (fit in Claude). Reserve Gemini for comprehensive surveys and books. Page count estimated from PDF metadata or word count.

---

### Decision 4: Spec Generation Automation Level

**Options Considered**:
1. **Option A**: Fully automated (paper → spec without review)
   - Pros: Fastest, no human bottleneck
   - Cons: Risk of incorrect methodology extraction
2. **Option B**: Semi-automated (generate draft, human review)
   - Pros: Catches errors, human validation
   - Cons: Slower, requires attention
3. **Option C**: Manual with templates
   - Pros: Most accurate
   - Cons: No automation benefit

**Selected**: Option B

**Rationale**: Trading strategies require human validation before implementation. Automation extracts methodology and generates draft spec; human reviews before speckit execution.

---

## Implementation Strategy

### Phase 1: Academic Research Extensions

**Goal**: Enable trading paper classification and storage

**Deliverables**:
- [ ] Add `TRADING_STRATEGY_UTTERANCES` to `routes_config.py` (20+ utterances)
- [ ] Add `trading_strategy` route to semantic-router
- [ ] Create `strategy__` entity schema in `entity_schemas.md`
- [ ] Update `research-query-workflow` skill with trading template
- [ ] Test classification accuracy (target >85%)

**Dependencies**: None

**Location**: `/media/sam/1TB1/academic_research/`

**Estimated Effort**: 1 day

---

### Phase 2: Bridge Components

**Goal**: Create nautilus_dev components to consume research

**Deliverables**:
- [ ] Create `strategy-researcher` agent in `.claude/agents/`
- [ ] Create `paper-to-strategy` skill in `.claude/skills/`
- [ ] Create `sync_research.py` script
- [ ] Create `docs/research/` directory structure
- [ ] Test agent with mock memory.json data

**Dependencies**: Phase 1

**Location**: `/media/sam/1TB/nautilus_dev/`

**Estimated Effort**: 2 days

---

### Phase 3: Integration & Testing

**Goal**: End-to-end pipeline validation

**Deliverables**:
- [ ] End-to-end test: "Research momentum reversal" → working strategy
- [ ] Validate classification accuracy with 10 test papers
- [ ] Verify spec generation matches paper methodology
- [ ] Test alpha-evolve integration (generate 3 implementations)
- [ ] Backtest comparison: strategy vs paper results (±20%)

**Dependencies**: Phase 2

**Estimated Effort**: 2 days

---

### Phase 4: Documentation & Polish

**Goal**: Production-ready documentation

**Deliverables**:
- [ ] Update academic_research/CLAUDE.md
- [ ] Update nautilus_dev/CLAUDE.md
- [ ] Create quickstart.md with usage examples
- [ ] Document troubleshooting guide
- [ ] Update docs/ARCHITECTURE.md

**Dependencies**: Phase 3

**Estimated Effort**: 1 day

---

## File Structure

### academic_research (modifications)

```
academic_research/
├── semantic_router_mcp/
│   └── routes_config.py              # MODIFY: Add TRADING_STRATEGY_UTTERANCES
├── docs/
│   └── entity_schemas.md             # MODIFY: Add strategy__ schema
├── scripts/
│   └── validate_entity.py            # NEW: Entity validation function
├── .claude/
│   └── skills/
│       └── research-query-workflow/
│           └── SKILL.md              # MODIFY: Add trading template
└── memory.json                       # AUTO: strategy__ entities created
```

### nautilus_dev (additions)

```
nautilus_dev/
├── .claude/
│   ├── agents/
│   │   └── strategy-researcher.md    # NEW: Bridge agent
│   └── skills/
│       └── paper-to-strategy/
│           ├── SKILL.md              # NEW: Conversion skill
│           └── templates/
│               └── strategy_spec.md  # NEW: Spec template
├── scripts/
│   └── sync_research.py              # NEW: Sync script
├── docs/
│   └── research/
│       ├── strategies.json           # NEW: Synced from memory.json
│       └── README.md                 # NEW: Research usage guide
└── specs/
    └── 022-academic-research-pipeline/
        ├── spec.md                   # EXISTS
        ├── research.md               # EXISTS
        ├── plan.md                   # THIS FILE
        ├── data-model.md             # EXISTS
        ├── quickstart.md             # EXISTS
        └── tasks.md                  # EXISTS
```

---

## API Design

### strategy-researcher Agent Interface

```yaml
# .claude/agents/strategy-researcher.md

Inputs:
  - topic: str           # Research topic or paper ID
  - memory_path: str     # Path to memory.json (default: academic_research)
  - output_dir: str      # Specs directory (default: specs/)

Outputs:
  - spec.md             # Generated strategy specification
  - research.md         # Paper summary and methodology
  - data-model.md       # Strategy config model

Methods:
  - search_memory(topic) → List[StrategyEntity]
  - extract_methodology(paper) → Methodology
  - map_to_nautilus(methodology) → NautilusMapping
  - generate_spec(mapping) → SpecFile
```

### paper-to-strategy Skill Interface

```yaml
# .claude/skills/paper-to-strategy/SKILL.md

Triggers:
  - "convert paper {id} to strategy"
  - "paper to strategy {arxiv_id}"
  - "implement strategy from {paper}"

Template Variables:
  - paper_title: str
  - arxiv_id: str
  - authors: List[str]
  - entry_conditions: str
  - exit_conditions: str
  - indicators: List[Indicator]
  - risk_management: str
  - backtest_params: BacktestConfig
```

### strategy__ Entity Schema

```python
@dataclass
class StrategyEntity:
    id: str                    # strategy__{methodology}_{asset}_{year}
    name: str
    source_paper: str          # source__{arxiv_id}
    methodology: Methodology
    indicators: List[Indicator]
    backtest_results: BacktestResults
    nautilus_mapping: NautilusMapping
    implementation_status: Literal["researched", "specified", "implemented", "backtested"]

@dataclass
class Methodology:
    type: Literal["momentum", "mean_reversion", "market_making", "arbitrage"]
    entry_logic: str
    exit_logic: str
    position_sizing: Literal["fixed", "volatility_scaled", "kelly"]
    risk_management: str

@dataclass
class NautilusMapping:
    indicators: List[str]      # ["ExponentialMovingAverage", "RelativeStrengthIndex"]
    order_types: List[str]     # ["MARKET", "STOP_MARKET"]
    events: List[str]          # ["PositionOpened", "OrderFilled"]
```

---

## Testing Strategy

### Unit Tests

- [ ] Test TRADING_STRATEGY_UTTERANCES classification (10 samples)
- [ ] Test strategy__ entity creation and validation
- [ ] Test sync_research.py with mock data
- [ ] Test paper-to-strategy template rendering

### Integration Tests

- [ ] Test research workflow → memory.json → strategy__ entity
- [ ] Test strategy-researcher agent → spec.md generation
- [ ] Test spec.md → speckit.plan → speckit.tasks
- [ ] Test alpha-evolve with generated spec

### End-to-End Tests

- [ ] Full pipeline: "Research momentum reversal" → working backtest
- [ ] Validate: strategy backtest results within ±20% of paper claims
- [ ] Time benchmark: paper → working strategy < 2 hours

---

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Paper methodology unclear | Strategy incorrect | Medium | Use gemini-cli for detailed extraction; human review |
| Indicator not in NautilusTrader | Can't implement natively | Low | Flag in spec; create custom indicator task |
| Classification accuracy < 85% | Papers misrouted | Medium | More training utterances; confidence threshold |
| Sync script fails | Stale data | Low | Timestamp checking; manual trigger option |
| Backtest results don't match paper | User distrust | Medium | Document assumptions; ±20% tolerance |

---

## Dependencies

### External Dependencies

**academic_research**:
- semantic-router >= 0.1.0
- paper-search-mcp (operational)
- gemini-cli MCP (for long papers)
- memory.json schema

**nautilus_dev**:
- NautilusTrader nightly >= 1.222.0
- Context7 MCP (for API docs)
- speckit commands (operational)
- alpha-evolve agent (operational)

### Internal Dependencies

| Component | Depends On |
|-----------|------------|
| strategy-researcher | paper-to-strategy skill |
| paper-to-strategy | strategy__ schema |
| sync_research.py | memory.json format |
| spec generation | speckit templates |

---

## Configuration

### semantic-router Trading Route

See `spec.md` Component 1 for the full `TRADING_STRATEGY_UTTERANCES` list (20+ utterances covering momentum, mean reversion, market making, and crypto-specific strategies).

### sync_research.py Configuration

```python
# scripts/sync_research.py

CONFIG = {
    "source": "/media/sam/1TB1/academic_research/memory.json",
    "target": "/media/sam/1TB/nautilus_dev/docs/research/strategies.json",
    "entity_prefix": "strategy__",
    "stale_threshold_hours": 24,
}
```

---

## Acceptance Criteria

- [ ] Classification accuracy > 85% for trading papers (10 test samples)
- [ ] strategy__ entities created correctly in memory.json
- [ ] strategy-researcher agent generates valid spec.md
- [ ] paper-to-strategy skill triggers on documented phrases
- [ ] sync_research.py syncs entities without errors
- [ ] End-to-end: paper → working backtest in < 2 hours
- [ ] Backtest results within ±20% of paper claims
- [ ] All documentation updated (CLAUDE.md, quickstart.md)
- [ ] No [NEEDS CLARIFICATION] items remaining
