# Research Pipeline Skill

Automated academic research pipeline for trading strategies. Combines semantic classification, paper search, methodology extraction, and entity sync.

## Invocation

```
/research <topic>
```

## Arguments

- `topic`: Research topic (e.g., "walk-forward validation", "momentum reversal")

## Workflow

When invoked, execute these steps:

### 1. Classify Query

```
Use semantic-router MCP to classify: "{topic} algorithmic trading"
Expected: trading_strategy domain with confidence > 0.5
```

If classification fails or returns non-trading domain:
- Warn user
- Ask to proceed anyway or refine topic

### 2. Search Papers

Use paper-search MCP or WebSearch:

```yaml
Sources:
  - arXiv: categories q-fin.TR, q-fin.PM, q-fin.CP
  - Semantic Scholar: trading, quantitative finance
  - SSRN: finance, trading strategies

Query: "{topic} algorithmic trading backtesting"
Limit: 10 papers
```

### 3. Analyze & Rank Papers

For each paper, evaluate:

| Criterion | Weight |
|-----------|--------|
| Relevance to topic | 40% |
| Methodology clarity | 30% |
| Implementation detail | 20% |
| Recency (prefer recent) | 10% |

Select top 3 papers for detailed extraction.

### 4. Extract Methodology

For each top paper:

```yaml
Paper:
  title: "{title}"
  arxiv_id: "{id}"
  year: {year}

Methodology:
  type: momentum|mean_reversion|market_making|arbitrage|trend_following|statistical_arbitrage
  entry_logic: "Natural language description"
  exit_logic: "Natural language description"
  indicators:
    - name: "{indicator}"
      params: {parameters}
      nautilus_class: "{NautilusTrader class}"
  risk_management: "Description"

Backtest (if reported):
  period: "{start} - {end}"
  assets: [list]
  sharpe: {value}
  max_drawdown: {value}
```

### 5. Map to NautilusTrader

Reference: `docs/research/indicator_mapping.md`

```yaml
Mapping:
  - paper: "20-period EMA"
    nautilus: ExponentialMovingAverage(period=20)
  - paper: "RSI(14)"
    nautilus: RelativeStrengthIndex(period=14)

Custom Needed:
  - "{indicator not in NautilusTrader}"
```

### 6. Create Entities

Create strategy__ entities for memory.json:

```json
{
  "name": "strategy__{methodology}_{asset}_{year}",
  "entityType": "strategy",
  "observations": [
    "source_paper: source__arxiv_{id}",
    "methodology_type: {type}",
    "entry_logic: {entry}",
    "exit_logic: {exit}",
    "indicators: {json_list}",
    "implementation_status: not_started",
    "research_topic: {topic}"
  ]
}
```

### 7. Sync Entities

```bash
python scripts/sync_research.py --force
```

### 8. Output Report

```markdown
# Research Report: {topic}

**Date**: {date}
**Classification**: {domain} (confidence: {conf})

## Papers Analyzed

| Paper | Year | Methodology | Relevance |
|-------|------|-------------|-----------|
| {title} | {year} | {type} | {score}/10 |

## Top Finding: {best_paper_title}

### Methodology
{methodology_summary}

### Entry Logic
{entry_logic}

### Exit Logic
{exit_logic}

### Indicators
| Paper | NautilusTrader | Status |
|-------|----------------|--------|
| {ind} | {nautilus} | ✅ Native / ⚠️ Custom |

## Entities Created
- `strategy__{id1}`
- `strategy__{id2}`

## Next Steps
1. `/speckit.specify spec-{N}` - Create spec from research
2. `/speckit.plan spec-{N}` - Plan implementation
3. `/speckit.implement spec-{N}` - Implement strategy

## References
- [{paper1_title}]({url1})
- [{paper2_title}]({url2})
```

## Error Handling

| Error | Action |
|-------|--------|
| semantic-router unavailable | Use WebSearch, warn about classification |
| paper-search unavailable | Fall back to WebSearch |
| No papers found | Suggest alternative topics |
| memory.json inaccessible | Save entities to local file |

## Integration

After research completes:
```
/speckit.specify spec-020  # Imports research findings
/speckit.plan spec-020     # Uses methodology from papers
```

## Examples

```bash
# Walk-forward validation research
/research walk-forward validation

# Momentum strategies
/research momentum factor rotation

# Market making
/research market making spread optimization

# Statistical arbitrage
/research pairs trading cointegration
```
