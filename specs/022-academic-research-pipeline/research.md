# Research: Academic Research Pipeline Integration

**Spec**: 022-academic-research-pipeline
**Date**: 2025-12-28
**Status**: Complete

## Existing System Analysis

### academic_research Configuration

**Location**: `/media/sam/1TB1/academic_research`

#### Current State

| Component | Status | Quality |
|-----------|--------|---------|
| **CLAUDE.md** | ✅ Present | Well-structured, tech stack documented |
| **Skills** | ✅ 2 skills | `research-query-workflow`, `paper-entity-generator` |
| **MCP Servers** | ✅ 6 servers | semantic-router, paper-search, gemini, firecrawl |
| **Hooks** | ⚠️ Partial | WebSearch hook, missing some notifications |
| **Subagents** | ❌ Missing | No agents in `.claude/agents/` |
| **Commands** | ❌ Missing | No slash commands |
| **Knowledge Graph** | ✅ Present | memory.json with entities |

#### MCP Servers

```json
{
  "semantic-router": "Deterministic query routing (100ms, $0)",
  "paper-search-mcp": "arXiv, PubMed, bioRxiv, Semantic Scholar, CrossRef",
  "papers-with-code-mcp": "GitHub implementations",
  "gemini-cli": "2M token context for long papers",
  "download-mcp": "Multi-threaded file downloads",
  "firecrawl-mcp": "Web scraping"
}
```

#### Skills Analysis

**research-query-workflow** (78% token savings):
- 6-step workflow: Memory → Classify → Search → Extract → Store → Report
- Triggers on: "research {topic}", "find papers on..."
- Templates for: Biomedical, STEM/CS, Finance, Blockchain

**paper-entity-generator** (75% token savings):
- Creates source__, concept__, domain__, expert__ entities
- Canonical ID format prevents duplicates
- Extracts observations from paper metadata

#### Knowledge Graph Schema (memory.json)

```
Entity Types:
├── source__     (papers, with DOI/arXiv/PMID)
├── concept__    (methods, algorithms)
├── domain__     (research areas)
├── expert__     (authors, researchers)
└── strategy__   [MISSING - need to add]

Relationship Types:
├── cites
├── implements
├── contradicts
├── extends
├── authored_by
└── bridges_domains
```

### nautilus_dev Configuration

**Location**: `/media/sam/1TB/nautilus_dev`

#### Current State

| Component | Count | Examples |
|-----------|-------|----------|
| **Agents** | 13 | nautilus-coder, alpha-evolve, test-runner |
| **Skills** | 3 | pytest-test-generator, github-workflow, pydantic-model-generator |
| **Commands** | 15 | speckit.*, tdd.*, undo.* |
| **MCP Servers** | 3 | context7, grafana, serena |

#### Relevant Agents for Integration

| Agent | Role in Pipeline |
|-------|-----------------|
| **alpha-evolve** | Multi-implementation from paper spec |
| **nautilus-coder** | Strategy implementation |
| **test-runner** | Backtest execution |
| **alpha-debug** | Edge case discovery |
| **backtest-analyzer** | Performance analysis |

---

## Gap Analysis

### Missing in academic_research

| Gap | Impact | Priority |
|-----|--------|----------|
| No trading_strategy route | Papers misclassified | P1 |
| No strategy__ entity type | Can't store trading metadata | P1 |
| No slash commands | Manual workflow trigger | P2 |
| No subagents | No specialized paper analysis | P2 |
| No bridge to nautilus_dev | Manual copy/paste | P1 |

### Missing in nautilus_dev

| Gap | Impact | Priority |
|-----|--------|----------|
| No strategy-researcher agent | Can't read memory.json | P1 |
| No paper-to-strategy skill | Manual spec writing | P1 |
| No sync mechanism | Stale research data | P2 |
| No research directory | No place for synced data | P2 |

---

## Integration Design Decisions

### Decision 1: Where to Add Trading Routes?

**Options**:
1. Add to existing STEM_CS_UTTERANCES
2. Create new TRADING_STRATEGY route

**Decision**: Option 2 - New route
**Rationale**: Trading papers have distinct vocabulary and should be classified separately for specialized processing

### Decision 2: Entity Storage Location?

**Options**:
1. Store strategy__ only in academic_research
2. Sync to nautilus_dev via script
3. Dual-write to both repos

**Decision**: Option 2 - Sync script
**Rationale**: Single source of truth (memory.json), nautilus_dev gets read-only copy

### Decision 3: Paper Analysis Tool?

**Options**:
1. gemini-cli (2M tokens, $0.15/paper)
2. Claude context (200k tokens, included)
3. Hybrid: Claude for short, Gemini for long

**Decision**: Option 3 - Hybrid
**Rationale**: Most papers <50 pages can use Claude; Gemini for 100+ page papers

### Decision 4: Spec Generation Method?

**Options**:
1. Fully automated (paper → spec without review)
2. Semi-automated (generate draft, human review)
3. Manual with templates

**Decision**: Option 2 - Semi-automated
**Rationale**: Trading strategies need human validation; automation for extraction, human for approval

---

## Existing Research Assets

### Liquidation Models Report

**Location**: `/media/sam/1TB1/academic_research/liquidation_models_summary_report.md`

**Contents** (1430 lines):
- Liquidation price formulas (Binance, OKX) - 99% fidelity
- Mark price calculation - 80% fidelity
- Funding rate formula - 90% fidelity
- Tiered margin tables (complete)
- Python implementation (LiquidationModel class)
- Heatmap construction pseudocode

**Relevance to Trading Strategies**:
- Can be used for risk management in strategies
- Useful for liquidation cascade prediction strategies
- Mark price tracking for arbitrage strategies

### Downloaded Papers

**Location**: `/media/sam/1TB1/academic_research/papers/`

```
papers/
├── arxiv/
│   └── 2209.03307.pdf    # "A Primer on Perpetuals"
├── semantic/
│   ├── DOI:10.1007_s10551-021-04901-5.pdf
│   └── DOI:10.1016_j.jfineco.2024.103900.pdf
├── biorxiv/
├── crossref/
├── iacr/
└── pubmed/
```

### Semantic Router Routes

**Current domains** (from routes_config.py):
- `biomedical`: 24 utterances
- `stem_cs`: 24 utterances (includes some finance)
- `general`: 24 utterances

**Finance-related in stem_cs**:
- "quantitative finance model"
- "algorithmic trading strategy"
- "portfolio optimization"

**Missing trading-specific**:
- momentum/mean reversion
- market making
- HFT/microstructure
- crypto-specific (funding, liquidation)

---

## Implementation Roadmap

### Phase 1: academic_research Extensions (Day 1-2)

1. **Add TRADING_STRATEGY_UTTERANCES** (2h)
   - File: `semantic_router_mcp/routes_config.py`
   - Add 20+ trading-specific utterances
   - Test classification accuracy

2. **Create strategy__ entity schema** (2h)
   - File: `docs/entity_schemas.md`
   - Add schema with nautilus_mapping field
   - Test entity creation

3. **Update research-query-workflow** (2h)
   - File: `.claude/skills/research-query-workflow/SKILL.md`
   - Add "Trading Strategy Research" template
   - Include indicator extraction

### Phase 2: nautilus_dev Bridge (Day 2-3)

4. **Create strategy-researcher agent** (3h)
   - File: `.claude/agents/strategy-researcher.md`
   - Workflow: read memory.json → extract → map → generate

5. **Create paper-to-strategy skill** (2h)
   - File: `.claude/skills/paper-to-strategy/SKILL.md`
   - Template for NautilusTrader strategy spec

6. **Create sync script** (1h)
   - File: `scripts/sync_research.py`
   - Sync strategy__ entities to docs/research/

### Phase 3: Integration Testing (Day 3-4)

7. **End-to-end test** (4h)
   - Research: "momentum reversal crypto futures"
   - Extract: methodology from papers
   - Generate: spec.md in nautilus_dev
   - Implement: with alpha-evolve

8. **Validate backtest** (2h)
   - Run backtest with nautilus-coder
   - Compare to paper results
   - Document discrepancies

### Phase 4: Documentation (Day 4-5)

9. **Update CLAUDE.md** (both repos) (2h)
10. **Create usage examples** (2h)
11. **Write troubleshooting guide** (1h)

---

## References

### Internal
- `/media/sam/1TB1/academic_research/CLAUDE.md` - Research system docs
- `/media/sam/1TB1/academic_research/docs/entity_schemas.md` - Entity definitions
- `/media/sam/1TB1/academic_research/docs/workflow_templates.md` - 10 workflow patterns
- `/media/sam/1TB/nautilus_dev/CLAUDE.md` - Trading system docs

### External
- [semantic-router](https://github.com/aurelio-labs/semantic-router) - Query classification
- [paper-search-mcp](https://github.com/ivo-toby/paper-search-mcp) - Multi-source search
- [NautilusTrader Docs](https://docs.nautilustrader.io) - API reference

### Academic
- arXiv:2209.03307 - "A Primer on Perpetuals" (local copy available)
