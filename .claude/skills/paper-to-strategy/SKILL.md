---
name: paper-to-strategy
description: Convert academic trading paper into NautilusTrader strategy specification. 70% token savings (2500→750).
---

# Paper to Strategy Conversion Skill

Convert academic trading papers into NautilusTrader-compatible strategy specifications, complete with indicator mappings, entry/exit logic, and backtest parameters.

## Quick Start

**User says**: "Convert paper arxiv:2209.03307 to strategy"

**Skill executes**:
```markdown
✅ Step 1: Paper Retrieval
   → Fetching paper metadata from arXiv...
   → Title: "A Primer on Perpetuals"

✅ Step 2: Methodology Extraction
   → Strategy Type: arbitrage (funding rate)
   → Entry: When funding rate > 0.1% annualized
   → Exit: When funding rate < 0 or position age > 8h

✅ Step 3: NautilusTrader Mapping
   → Indicators: None (uses funding rate API)
   → Order Types: MARKET, STOP_MARKET
   → Custom: FundingRateMonitor (needs implementation)

✅ Step 4: Spec Generation
   → Created: specs/023-funding-rate-arb/spec.md
   → Entity: strategy__arbitrage_perp_funding_2022

✅ Ready for: /speckit.plan
```

## Triggers

- "convert paper {id} to strategy"
- "paper to strategy {arxiv_id}"
- "implement strategy from {paper}"
- "create nautilus strategy for {methodology}"
- "turn {paper} into trading spec"

## Workflow

### Step 1: Paper Retrieval & Analysis

```yaml
Input: Paper ID (arXiv, DOI, SSRN, or URL)
Actions:
  - Fetch paper metadata (title, authors, abstract)
  - If paper > 50 pages: Use mcp__gemini-cli__ask-gemini for analysis
  - If paper < 50 pages: Use Claude context for analysis
Output: Structured paper summary
```

### Step 2: Methodology Extraction

```yaml
Extract from paper:
  - Strategy type: momentum|mean_reversion|market_making|arbitrage|trend_following|statistical_arbitrage
  - Entry conditions (natural language)
  - Exit conditions (natural language)
  - Indicators used (with parameters)
  - Position sizing method
  - Risk management rules
  - Backtest methodology
  - Reported results (Sharpe, drawdown, returns)
```

### Step 3: NautilusTrader Mapping

```yaml
Use mapping tables from:
  - docs/research/indicator_mapping.md
  - docs/research/order_mapping.md

Map each paper component:
  - Paper indicator → NautilusTrader class + params
  - Paper order type → NautilusTrader OrderType enum
  - Paper event → NautilusTrader event handler

Flag custom indicators needed:
  - If indicator not in mapping → Add to "custom_indicators_needed"
  - Suggest implementation approach
```

### Step 4: Spec Generation

```yaml
Generate files:
  - specs/{n}-{strategy_name}/spec.md (from template)
  - Update memory.json with strategy__ entity (via sync)

Create spec directory:
  - Use next available spec number
  - Name: {methodology}_{asset}_{author_year}
```

## Template Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{strategy_name}` | Human-readable name | "Funding Rate Arbitrage" |
| `{paper_title}` | Original paper title | "A Primer on Perpetuals" |
| `{authors}` | Paper authors | "Smith J, Doe A" |
| `{paper_id}` | ArXiv/DOI/SSRN ID | "arxiv:2209.03307" |
| `{year}` | Publication year | "2022" |
| `{methodology_type}` | Strategy classification | "arbitrage" |
| `{entry_conditions}` | Natural language entry | "When funding > 0.1%" |
| `{exit_conditions}` | Natural language exit | "When funding < 0" |
| `{StrategyClass}` | Python class name | "FundingRateArbitrageStrategy" |
| `{indicator_mapping_table}` | Markdown table | See template |

## Usage Examples

### Example 1: Momentum Paper

```
User: "Convert arxiv:2103.15879 momentum paper to strategy"

Output:
- Strategy: Crypto Momentum Cross-Sectional
- Type: momentum
- Indicators: ExponentialMovingAverage, RelativeStrengthIndex
- Entry: Buy top 5 by 7-day momentum, RSI < 70
- Exit: Hold 7 days or RSI > 80
- Spec: specs/024-crypto-momentum/spec.md
```

### Example 2: Market Making Paper

```
User: "paper to strategy Avellaneda-Stoikov"

Output:
- Strategy: Optimal Market Making (Avellaneda-Stoikov)
- Type: market_making
- Indicators: OrderBookImbalance (custom), InventoryRisk (custom)
- Entry: Continuous quote updates
- Exit: Inventory limits exceeded
- Spec: specs/025-optimal-mm/spec.md
- Note: Requires custom indicators
```

### Example 3: Mean Reversion Paper

```
User: "implement strategy from pairs trading cointegration paper"

Output:
- Strategy: Statistical Pairs Trading
- Type: mean_reversion
- Indicators: LinearRegression (custom), ZScore (custom)
- Entry: Z-score > 2 (short), Z-score < -2 (long)
- Exit: Z-score crosses 0
- Spec: specs/026-pairs-trading/spec.md
```

## Integration with Agents

### strategy-researcher Agent

This skill is invoked by the `strategy-researcher` agent during the paper-to-spec workflow:

```yaml
Agent: strategy-researcher
Uses: paper-to-strategy skill
Output: Complete spec.md ready for /speckit.plan
```

### alpha-evolve Agent

After spec generation, use alpha-evolve for multi-implementation:

```yaml
Input: specs/{n}/spec.md
Process: Generate 3+ implementation variants
Output: Ranked implementations by backtest performance
```

## Error Handling

### Paper Not Found

```yaml
Error: Paper ID not found in databases
Action:
  1. Try alternative databases (arXiv → SSRN → DOI)
  2. Ask user for direct PDF/URL
  3. If still not found → "Paper not accessible, please provide PDF"
```

### Unclear Methodology

```yaml
Error: Paper doesn't clearly define trading logic
Action:
  1. Ask clarifying questions about entry/exit
  2. Extract from "Methodology" or "Results" sections
  3. If still unclear → Generate partial spec with [NEEDS CLARIFICATION] markers
```

### Unmapped Indicators

```yaml
Warning: Indicator not in NautilusTrader
Action:
  1. Add to custom_indicators_needed section
  2. Suggest implementation approach
  3. Check if similar indicator exists (e.g., "momentum" → RateOfChange)
```

## Token Savings

| Task | Without Skill | With Skill | Savings |
|------|--------------|------------|---------|
| Paper → Spec (simple) | 2,500 tokens | 750 tokens | 70% |
| Paper → Spec (complex) | 4,000 tokens | 1,200 tokens | 70% |
| Paper → Spec + alpha-evolve | 6,000 tokens | 1,800 tokens | 70% |

**Average Savings**: 70% (3,500 → 1,050 tokens)

## Related Resources

- **Template**: `.claude/skills/paper-to-strategy/templates/strategy_spec.md`
- **Indicator Mapping**: `docs/research/indicator_mapping.md`
- **Order Mapping**: `docs/research/order_mapping.md`
- **Entity Schema**: See academic_research/docs/entity_schemas.md (strategy__ section)

## Alpha-Evolve Integration

After spec generation, trigger alpha-evolve for multi-implementation:

### Automatic Handoff

```yaml
Trigger: Spec generation complete
Command: Invoke alpha-evolve agent with spec.md path

alpha-evolve receives:
  - specs/{n}/spec.md: Strategy specification
  - specs/{n}/plan.md: Implementation plan (if exists)
  - Indicator mappings from docs/research/

alpha-evolve produces:
  - 3+ implementation variants
  - Fitness scores (tests, performance, quality)
  - Selected winner or ensemble
```

### Integration Hook

After generating spec.md, the skill outputs:

```markdown
## Next Steps

### Option 1: Standard Implementation
Run `/speckit.plan` to create implementation plan, then use nautilus-coder.

### Option 2: Multi-Implementation (Recommended for complex strategies)
Invoke alpha-evolve agent for 3+ implementation variants:

1. Read the generated spec: specs/{n}/spec.md
2. Generate 3 approaches varying:
   - Algorithm complexity
   - Indicator usage patterns
   - Risk management implementation
3. Backtest each variant
4. Select best by Sharpe ratio / drawdown
5. Promote winner to production

### Alpha-Evolve Command
Use Task tool with subagent_type='alpha-evolve':
"Implement strategy from specs/{n}/spec.md with 3 variants.
Evaluate by backtest Sharpe ratio and max drawdown.
Select best implementation."
```

### Backtest Evaluation Criteria

Alpha-evolve evaluates implementations using:

| Metric | Weight | Target |
|--------|--------|--------|
| Sharpe Ratio | 30% | > 1.0 |
| Max Drawdown | 25% | < 20% |
| Win Rate | 15% | > 50% |
| Profit Factor | 15% | > 1.5 |
| Test Coverage | 15% | > 80% |

### Implementation Ranking Output

```markdown
=== ALPHA-EVOLVE RESULTS ===

| Variant | Sharpe | Drawdown | Tests | TOTAL |
|---------|--------|----------|-------|-------|
| A: Event-driven | 1.8 | 15% | PASS | 85/100 |
| B: State machine | 1.5 | 12% | PASS | 78/100 |
| C: Rule-based | 2.1 | 22% | PASS | 72/100 |

Winner: Variant A (balanced performance + lower drawdown)
```

## Dependencies

- NautilusTrader nightly >= 1.222.0
- Context7 MCP (for API documentation)
- Paper search MCP (for paper retrieval)
- memory.json access (for entity creation)
- alpha-evolve agent (for multi-implementation)
- test-runner agent (for variant testing)

---

**VERSION**: 1.0
**LAST UPDATED**: 2025-12-29
**TOKEN ECONOMICS**: 70% savings
**STATUS**: ✅ Production Ready
