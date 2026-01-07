# Quickstart: Academic Research → Trading Strategy Pipeline

**Spec**: 022-academic-research-pipeline

## Prerequisites

- `/media/sam/1TB1/academic_research` configured and operational
- semantic-router MCP running
- paper-search MCP available
- nautilus_dev environment activated

## Quick Usage

### 1. Research Trading Papers

```bash
# In academic_research workspace
cd /media/sam/1TB1/academic_research

# Start Claude Code
claude

# Research a trading topic
> Research momentum reversal strategies for crypto futures
```

**Expected Output**:
```
✅ Step 1: Memory Check → No existing entities
✅ Step 2: Classify → trading_strategy (confidence: 0.89)
✅ Step 3: Search
   - arXiv: 8 papers
   - SSRN: 3 papers
   - GitHub: 2 implementations
✅ Step 4: Create Entities
   - 11 source__ entities
   - 3 strategy__ entities
   - 5 concept__ entities
✅ Step 5: Update memory.json
✅ Step 6: Intelligence Report
```

### 2. Convert Paper to Strategy Spec

```bash
# In nautilus_dev workspace
cd /media/sam/1TB/nautilus_dev

# Start Claude Code
claude

# Convert best paper to strategy
> Convert paper arxiv:2301.12345 to strategy
```

**Expected Output**:
```
📄 Generating strategy specification...

Source: "Momentum Reversal in Crypto Futures"
Authors: Smith et al. (2023)

Methodology:
- Entry: RSI < 30 → RSI > 30 crossover
- Exit: RSI > 70 OR 2% trailing stop
- Position sizing: Volatility-scaled

NautilusTrader Mapping:
- Indicators: ExponentialMovingAverage, RelativeStrengthIndex
- Order types: MARKET, STOP_MARKET

Generated: specs/023-momentum-reversal-crypto/spec.md
```

### 3. Generate Implementation Plan

```bash
# Continue in nautilus_dev
> /speckit.plan
```

### 4. Generate Tasks

```bash
> /speckit.tasks
```

### 5. Implement with Alpha-Evolve

```bash
> /speckit.implement
# Alpha-evolve generates 3+ implementations
# Best one selected by backtest performance
```

---

## Full Pipeline Example

### Scenario: Find and Implement Mean Reversion Strategy

**Step 1: Research**
```
User: Research mean reversion strategies for pairs trading

Claude: [Executes research-query-workflow]
- Found 15 papers on pairs trading
- Created 4 strategy__ entities
- Best paper: "Statistical Arbitrage with Cointegration" (Sharpe: 2.1)
```

**Step 2: Review Entities**
```bash
# Check memory.json
cat /media/sam/1TB1/academic_research/memory.json | jq '.entities[] | select(.id | startswith("strategy__"))'
```

**Step 3: Convert to Spec**
```
User: Convert strategy__pairs_trading_crypto_2024 to nautilus spec

Claude: [Executes paper-to-strategy skill]
Generated: specs/024-pairs-trading-cointegration/
├── spec.md
├── research.md
└── data-model.md
```

**Step 4: Implement**
```
User: /speckit.plan for spec 024
User: /speckit.tasks
User: /speckit.implement
```

**Step 5: Backtest**
```
User: Run backtest for pairs trading strategy

Claude: [Uses test-runner agent]
Results:
- Sharpe: 1.9 (paper: 2.1) ✅ Within ±20%
- Max Drawdown: 12% (paper: 10%) ✅
- Win Rate: 54% (paper: 56%) ✅
```

---

## Common Workflows

### Research → Spec (Quick)

```
1. "Research {topic}"
2. "Convert best paper to strategy"
3. "/speckit.plan"
4. "/speckit.tasks"
```

### Specific Paper → Strategy

```
1. "Analyze paper arxiv:{id}"
2. "Create strategy entity for this paper"
3. "Convert to nautilus spec"
```

### Incremental Research

```
Session 1: "Research momentum strategies"
Session 2: "Find more papers on momentum reversal"  # Builds on session 1
Session 3: "Compare all momentum strategies found"
```

---

## Troubleshooting

### Classification Wrong

**Problem**: Trading paper classified as `stem_cs` instead of `trading_strategy`

**Solution**: Check if TRADING_STRATEGY_UTTERANCES installed
```bash
grep -r "momentum trading" /media/sam/1TB1/academic_research/semantic_router_mcp/routes_config.py
```

### No Strategy Entities Created

**Problem**: Research completes but no strategy__ entities in memory.json

**Solution**: Verify entity schema is defined
```bash
grep -r "strategy__" /media/sam/1TB1/academic_research/docs/entity_schemas.md
```

### Spec Generation Fails

**Problem**: paper-to-strategy skill doesn't trigger

**Solution**: Use exact trigger phrase
```
✅ "convert paper arxiv:2301.12345 to strategy"
❌ "make a strategy from this paper"
```

### Indicator Not Found

**Problem**: Paper uses indicator not in NautilusTrader

**Solution**: Check mapping in data-model.md, flag for custom implementation

### Sync Stale

**Problem**: nautilus_dev has old strategy data

**Solution**: Run sync manually
```bash
python scripts/sync_research.py
```

---

## Key Commands Reference

| Command | Location | Purpose |
|---------|----------|---------|
| "Research {topic}" | academic_research | Full research workflow |
| "Convert paper {id} to strategy" | nautilus_dev | Generate spec from paper |
| "/speckit.plan" | nautilus_dev | Create implementation plan |
| "/speckit.tasks" | nautilus_dev | Generate task list |
| "/speckit.implement" | nautilus_dev | Execute implementation |
| `python sync_research.py` | nautilus_dev | Sync memory.json |

---

## Performance Benchmarks

| Operation | Target | Actual |
|-----------|--------|--------|
| Paper classification | < 100ms | ~80ms |
| Research workflow (10 papers) | < 60s | ~45s |
| Spec generation | < 30s | ~20s |
| Full pipeline (paper → backtest) | < 2 hours | TBD |
