# Spec 022: Academic Research → Trading Strategy Pipeline

## Overview

Integrate `/media/sam/1TB1/academic_research` with nautilus_dev to automatically convert academic trading papers into NautilusTrader strategy specifications, leveraging our evolutionary architecture (alpha-evolve, speckit).

## Problem Statement

Currently:
- Academic research system exists but is isolated from trading development
- Papers are searched and stored in memory.json but not converted to code
- No bridge between research insights and strategy implementation
- Manual process: read paper → understand methodology → write spec → implement

**Goal**: Automated pipeline from "research topic X" to "runnable NautilusTrader strategy"

## User Stories

### US1: Trading Paper Classification (P1 - MVP)
**As a** quant researcher,
**I want** papers about trading strategies automatically classified and tagged,
**So that** I can quickly find relevant methodology for implementation.

**Acceptance Criteria**:
- [ ] semantic-router classifies "momentum trading" as `trading_strategy` domain
- [ ] New entity type `strategy__` created in memory.json
- [ ] Trading papers tagged with: strategy_type, asset_class, backtest_metrics

### US2: Paper → Strategy Spec (P1 - MVP)
**As a** developer,
**I want** to convert an academic paper into a NautilusTrader spec,
**So that** I can implement strategies faster with proper structure.

**Acceptance Criteria**:
- [ ] Command `/paper-to-strategy <arxiv_id>` generates spec.md
- [ ] Spec includes: entry/exit logic, risk management, indicators
- [ ] Mapping to NautilusTrader primitives (native Rust indicators)
- [ ] Backtest parameters from paper methodology

### US3: Multi-Implementation Generation (P2)
**As a** quant,
**I want** alpha-evolve to generate multiple implementations from one paper,
**So that** I can compare approaches and select the best.

**Acceptance Criteria**:
- [ ] alpha-evolve receives spec from paper
- [ ] Generates 3+ implementations with variations
- [ ] Backtest evaluator ranks by Sharpe/drawdown
- [ ] Best implementation promoted to main strategy

### US4: Knowledge Graph Sync (P2)
**As a** researcher,
**I want** trading insights synchronized between academic_research and nautilus_dev,
**So that** both systems share knowledge.

**Acceptance Criteria**:
- [ ] memory.json strategy__ entities synced to nautilus_dev/docs/research/strategies.json
- [ ] Sync includes staleness detection (timestamp comparison)
- [ ] Metadata link preserved: strategy entity references source paper ID

### US5: Incremental Research (P3)
**As a** trader,
**I want** to build on previous research sessions,
**So that** I don't repeat work and knowledge accumulates.

**Acceptance Criteria**:
- [ ] "Research momentum strategies" → finds existing in memory.json
- [ ] Shows differential: "3 new papers since last session"
- [ ] Links to existing strategies implementing similar concepts

### US6: Local RAG with Background Processing (P1) 🆕 [UPDATED 2026-01]
**As a** researcher,
**I want** papers parsed in background and indexed for semantic search,
**So that** I can query formulas without blocking research workflow.

**Acceptance Criteria**:
- [X] Background daemon processes PDFs with MinerU (non-blocking)
- [X] Local embeddings (bge-base-en-v1.5) for semantic search (NO LLM API)
- [X] Auto-indexing after parsing completes
- [X] Query: `query_formulas("Kelly criterion position sizing")`
- [X] Status: memory.json for knowledge graph (<500 entities)

**Architecture (Simplified 2026-01)**:
```
/research → queue_for_parsing() → Background Daemon → MinerU → Auto-Index → RAG Storage
                      ↓
              Immediate Response (abstracts)
```

**What was REMOVED**:
- Neo4j (TEXT-ONLY, requires LLM API - no benefit over memory.json)
- DuckDB sync (complexity without value for <500 entities)
- Bidirectional sync (YAGNI - memory.json + RAG sufficient)

### US7: MinerU PDF Parsing (P1) 🆕
**As a** researcher,
**I want** PDFs parsed with layout-aware extraction,
**So that** formulas and tables are properly extracted (not broken across lines).

**Acceptance Criteria**:
- [ ] MinerU installed in /media/sam/1TB/RAG-Anything
- [ ] `mineru -p paper.pdf -o output/` extracts structured markdown
- [ ] LaTeX formulas preserved: `$f^* = \frac{bp-q}{b}$`
- [ ] Tables extracted as markdown tables
- [ ] Integration with /research command

### US8: Formula Extraction & Validation (P2) 🆕 [UPDATED 2026-01]
**As a** quant,
**I want** mathematical formulas extracted and indexed for semantic search,
**So that** I can query formulas across all papers.

**Acceptance Criteria**:
- [X] Extract formulas from MinerU output
- [X] Index formulas in RAG storage (bge-base-en-v1.5)
- [X] Query: `query_formulas("Kelly criterion")` returns formula context
- [X] Validate with WolframAlpha: `mcp__wolframalpha__ask_llm` (optional)
- [X] Link formula→paper via doc_id in chunk metadata

## Technical Design

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ACADEMIC RESEARCH                             │
│                 /media/sam/1TB1/academic_research                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [semantic-router MCP]  →  [paper-search MCP]  →  [gemini-cli]  │
│         ↓                        ↓                     ↓        │
│    classify_query           search_arxiv          analyze_paper │
│    (trading_strategy)       search_ssrn           (100+ pages)  │
│                                                                  │
│                    ┌─────────────────────┐                      │
│                    │    memory.json      │                      │
│                    │  - source__         │                      │
│                    │  - concept__        │                      │
│                    │  - strategy__ (NEW) │                      │
│                    └──────────┬──────────┘                      │
│                               │                                  │
└───────────────────────────────┼──────────────────────────────────┘
                                │ BRIDGE
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       NAUTILUS_DEV                               │
│                  /media/sam/1TB/nautilus_dev                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [strategy-researcher]  →  [speckit]  →  [alpha-evolve]         │
│         ↓                      ↓              ↓                 │
│    read memory.json      generate spec    multi-impl            │
│    extract methodology   plan + tasks     evaluate              │
│                                                                  │
│                    ┌─────────────────────┐                      │
│                    │  specs/{n}/         │                      │
│                    │  - spec.md          │                      │
│                    │  - plan.md          │                      │
│                    │  - research.md      │                      │
│                    └──────────┬──────────┘                      │
│                               │                                  │
│                               ▼                                  │
│  [nautilus-coder]  →  [test-runner]  →  [alpha-debug]           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Component 1: semantic-router Extension (academic_research)

```python
# semantic_router_mcp/routes_config.py

TRADING_STRATEGY_UTTERANCES = [
    # Momentum/Trend
    "momentum trading strategy backtest results",
    "trend following algorithm performance",
    "moving average crossover system",

    # Mean Reversion
    "mean reversion statistical arbitrage",
    "pairs trading cointegration analysis",
    "Ornstein-Uhlenbeck parameter estimation",

    # Market Making
    "market making spread optimization",
    "order book imbalance alpha signal",
    "bid-ask spread prediction model",

    # HFT/Microstructure
    "high frequency trading latency arbitrage",
    "market microstructure order flow",
    "queue position priority optimization",

    # Crypto-Specific
    "perpetual futures funding rate arbitrage",
    "liquidation cascade prediction model",
    "whale tracking UTXO on-chain analysis",
    "DEX AMM liquidity provision strategy",

    # Risk Management
    "portfolio risk management VaR model",
    "drawdown control dynamic position sizing",
    "stop loss optimization trailing stop",
]

# Add to routes
trading_strategy_route = Route(
    name="trading_strategy",
    utterances=TRADING_STRATEGY_UTTERANCES,
)
```

### Component 2: strategy__ Entity Schema (academic_research)

```json
{
  "entity_type": "strategy__",
  "schema": {
    "id": "strategy__{methodology}_{asset}_{year}",
    "name": "Strategy name from paper",
    "source_paper": "source__{arxiv_id}",
    "methodology": {
      "type": "momentum|mean_reversion|market_making|arbitrage",
      "entry_logic": "Description of entry conditions",
      "exit_logic": "Description of exit conditions",
      "position_sizing": "fixed|volatility_scaled|kelly",
      "risk_management": "stop_loss|trailing|dynamic"
    },
    "indicators": [
      {"name": "EMA", "params": {"period": 20}},
      {"name": "RSI", "params": {"period": 14}}
    ],
    "backtest_results": {
      "period": "2020-2024",
      "assets": ["BTC", "ETH"],
      "sharpe_ratio": 1.5,
      "max_drawdown": 0.15,
      "annual_return": 0.35
    },
    "nautilus_mapping": {
      "indicators": ["ExponentialMovingAverage", "RelativeStrengthIndex"],
      "order_types": ["MARKET", "STOP_MARKET"],
      "events": ["PositionOpened", "OrderFilled"]
    },
    "implementation_status": "researched|specified|implemented|backtested"
  }
}
```

### Component 3: strategy-researcher Agent (nautilus_dev)

```yaml
# .claude/agents/strategy-researcher.md

name: strategy-researcher
description: |
  Research academic papers for trading strategies and convert them into
  NautilusTrader-compatible specifications. Bridge between academic_research
  knowledge graph and nautilus_dev specs.

tools:
  - Read
  - Write
  - Glob
  - Grep
  - WebFetch
  - mcp__gemini-cli__ask-gemini
  - mcp__context7__get-library-docs
  - TodoWrite

workflow:
  1. RESEARCH PHASE:
     - Read /media/sam/1TB1/academic_research/memory.json
     - Query for strategy__ entities matching topic
     - If not found → suggest running research in academic_research first

  2. EXTRACTION PHASE:
     - Load source paper (PDF or cached analysis)
     - Extract trading methodology:
       * Entry signals (technical indicators, conditions)
       * Exit signals (take profit, stop loss, time-based)
       * Position sizing (fixed, volatility, Kelly)
       * Risk parameters (max drawdown, correlation limits)
     - Extract backtest methodology:
       * Time period, asset universe
       * Transaction costs, slippage assumptions
       * Performance metrics reported

  3. MAPPING PHASE:
     - Map indicators to NautilusTrader native Rust:
       * "20-day EMA" → ExponentialMovingAverage(period=20)
       * "RSI(14)" → RelativeStrengthIndex(period=14)
     - Map order types:
       * "market order" → MARKET
       * "stop loss" → STOP_MARKET with reduce_only=True
     - Identify missing components (custom indicators needed?)

  4. SPECIFICATION PHASE:
     - Generate spec.md using speckit format
     - Include research.md with paper summary
     - Create data-model.md for strategy config
     - Output to specs/{next_number}-{strategy_name}/

output_format: |
  ## Strategy Research Report

  **Paper**: {title} ({arxiv_id})
  **Authors**: {authors}
  **Classification**: {strategy_type}

  ### Methodology Summary
  {extracted_methodology}

  ### NautilusTrader Mapping
  {indicator_mapping}
  {order_mapping}

  ### Generated Spec
  Path: specs/{n}-{name}/spec.md

  ### Next Steps
  1. Run /speckit.plan to create implementation plan
  2. Run alpha-evolve for multi-implementation
  3. Backtest with nautilus-coder
```

### Component 4: paper-to-strategy Skill (nautilus_dev)

```yaml
# .claude/skills/paper-to-strategy/SKILL.md

name: paper-to-strategy
description: |
  Convert academic trading paper into NautilusTrader strategy specification.
  Token savings: 70% (2500 → 750 tokens)

triggers:
  - "convert paper {id} to strategy"
  - "implement strategy from {paper}"
  - "create nautilus strategy for {methodology}"
  - "paper to strategy {arxiv_id}"

template: |
  # Strategy: {strategy_name}

  ## Source
  - **Paper**: {paper_title}
  - **Authors**: {authors}
  - **ArXiv**: {arxiv_id}
  - **Year**: {year}

  ## Problem Statement
  {paper_abstract_summary}

  ## Trading Logic (from paper)

  ### Entry Conditions
  {entry_conditions}

  ### Exit Conditions
  {exit_conditions}

  ### Position Sizing
  {position_sizing_method}

  ### Risk Management
  {risk_management_rules}

  ## NautilusTrader Implementation

  ### Indicators (Native Rust)
  ```python
  from nautilus_trader.indicators.average.ema import ExponentialMovingAverage
  from nautilus_trader.indicators.momentum.rsi import RelativeStrengthIndex

  self.ema = ExponentialMovingAverage(period={ema_period})
  self.rsi = RelativeStrengthIndex(period={rsi_period})
  ```

  ### Strategy Skeleton
  ```python
  class {StrategyClass}(Strategy):
      def on_bar(self, bar: Bar) -> None:
          self.ema.handle_bar(bar)
          self.rsi.handle_bar(bar)

          if {entry_condition}:
              self._enter_position(bar)
          elif {exit_condition}:
              self._exit_position()
  ```

  ### Configuration
  ```python
  class {StrategyClass}Config(StrategyConfig):
      ema_period: int = {ema_period}
      rsi_period: int = {rsi_period}
      stop_loss_pct: Decimal = Decimal("{stop_loss}")
      take_profit_pct: Decimal = Decimal("{take_profit}")
  ```

  ## Backtest Parameters (from paper)
  - **Period**: {backtest_start} to {backtest_end}
  - **Assets**: {asset_list}
  - **Expected Sharpe**: {sharpe_ratio}
  - **Max Drawdown**: {max_drawdown}

  ## Dependencies
  - Spec 011 (Stop-Loss & Position Limits)
  - Spec 021 (Hyperliquid) OR Spec 015 (Binance)
```

### Component 5: Sync Script

```python
# scripts/sync_research.py

"""
Sync strategy entities from academic_research to nautilus_dev.
Run periodically or on-demand.
"""

import json
from pathlib import Path

ACADEMIC_MEMORY = Path("/media/sam/1TB1/academic_research/memory.json")
NAUTILUS_RESEARCH = Path("/media/sam/1TB/nautilus_dev/docs/research/strategies.json")

def sync_strategies():
    """Extract strategy__ entities and sync to nautilus_dev."""
    with open(ACADEMIC_MEMORY) as f:
        memory = json.load(f)

    strategies = [
        entity for entity in memory.get("entities", [])
        if entity.get("id", "").startswith("strategy__")
    ]

    # Write to nautilus_dev
    NAUTILUS_RESEARCH.parent.mkdir(parents=True, exist_ok=True)
    with open(NAUTILUS_RESEARCH, "w") as f:
        json.dump({"strategies": strategies, "synced_at": "..."}, f, indent=2)

    return len(strategies)
```

## File Structure

### academic_research (additions)

```
academic_research/
├── semantic_router_mcp/
│   └── routes_config.py          # ADD: TRADING_STRATEGY_UTTERANCES
├── docs/
│   └── entity_schemas.md         # ADD: strategy__ schema
└── memory.json                   # AUTO: strategy__ entities
```

### nautilus_dev (additions)

```
nautilus_dev/
├── .claude/
│   ├── agents/
│   │   └── strategy-researcher.md   # NEW: Bridge agent
│   └── skills/
│       └── paper-to-strategy/
│           └── SKILL.md              # NEW: Conversion skill
├── scripts/
│   └── sync_research.py              # NEW: Sync script
└── docs/
    └── research/
        └── strategies.json           # SYNCED: From memory.json
```

## Dependencies

### Internal Dependencies
- Spec 011 (Stop-Loss & Position Limits) - Risk management for generated strategies
- Spec 021 (Hyperliquid) - Live execution target
- alpha-evolve agent - Multi-implementation generation
- speckit commands - Spec/plan/tasks generation

### External Dependencies
- `/media/sam/1TB1/academic_research` - Must be configured and operational
- semantic-router MCP - Query classification
- paper-search MCP - Paper retrieval
- gemini-cli MCP - Long paper analysis (2M tokens)
- Context7 MCP - NautilusTrader API docs

## Testing Strategy

### Phase 1: Classification Testing
- [ ] Add trading utterances to semantic-router
- [ ] Test classification: "momentum trading" → trading_strategy
- [ ] Verify confidence > 0.8 for trading queries

### Phase 2: Entity Testing
- [ ] Create strategy__ schema in entity_schemas.md
- [ ] Test entity creation from sample paper
- [ ] Verify nautilus_mapping fields populated

### Phase 3: Agent Testing
- [ ] Deploy strategy-researcher agent
- [ ] Test with known paper (e.g., momentum reversal)
- [ ] Verify spec.md generation

### Phase 4: End-to-End Testing
- [ ] Full pipeline: research → spec → alpha-evolve → backtest
- [ ] Measure time from paper to working strategy
- [ ] Validate backtest results match paper claims (within 20%)

## Success Metrics

| Metric | Target |
|--------|--------|
| Paper → Spec time | < 10 minutes |
| Spec → Working strategy | < 30 minutes (with alpha-evolve) |
| Classification accuracy | > 85% for trading papers |
| Strategy backtest correlation | ±20% of paper results |
| Token savings (skill) | > 70% |

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Paper methodology unclear | Strategy incorrect | Use gemini-cli for detailed extraction |
| Indicator not in NautilusTrader | Can't implement | Flag for custom implementation |
| Backtest assumptions differ | Results don't match | Document all assumptions |
| Cross-repo sync issues | Stale data | Sync script with timestamps |
