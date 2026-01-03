# /research - Academic Research Pipeline

Automated research pipeline for trading strategies. Searches academic papers, extracts methodologies, and syncs to nautilus_dev.

## Usage

```
/research <topic>
/research walk-forward validation
/research momentum reversal crypto
/research mean reversion pairs trading
```

## Workflow

Execute the following steps automatically:

### Step 1: Query Classification

Use `mcp__semantic-router__classify_query` to classify the topic:
- If `trading_strategy` (confidence > 0.5): Proceed with trading-focused search
- If other domain: Warn user, ask to proceed or refine query

### Step 2: Paper Search

Use `mcp__paper-search-mcp__search` with sources:
- arXiv (categories: q-fin.TR, q-fin.PM, q-fin.CP)
- Semantic Scholar
- SSRN (if available)

Search query: "$ARGUMENTS algorithmic trading"

Retrieve top 5-10 papers.

### Step 2.5: Paper Download (MANDATORY)

**CRITICAL**: Papers MUST be downloaded for future analysis, not just searched.

For each paper found, attempt download using priority sources:

1. **arXiv papers**: Use `mcp__paper-search-mcp__download_arxiv`
2. **Semantic Scholar**: Use `mcp__paper-search-mcp__download_semantic`
3. **bioRxiv/medRxiv**: Use respective download tools

Save location: `/media/sam/1TB/nautilus_dev/docs/research/papers/`

Create a download manifest:
```markdown
## Downloaded Papers

| Paper ID | Title | Source | Status | Path |
|----------|-------|--------|--------|------|
| arxiv:2106.12345 | Title | arXiv | ✅ Downloaded | papers/2106.12345.pdf |
| 10.2139/ssrn.XXX | Title | SSRN | ❌ Paywall | - |
```

**Fallback for paywalled papers**:
- Document DOI/URL for manual download
- Note: SSRN, JSTOR, Wiley often require institutional access
- Consider open-access alternatives (preprints, author websites)

### Step 3: Paper Analysis

For each paper found, extract:
```yaml
- title: Paper title
- arxiv_id: arXiv ID if available
- authors: Author list
- abstract: Paper abstract
- methodology_type: momentum|mean_reversion|market_making|arbitrage|trend_following|statistical_arbitrage
- key_concepts: List of trading concepts mentioned
- indicators: List of indicators used
- relevance_score: 1-10 rating for the topic
```

### Step 4: Create Strategy Entities

For the top 3 most relevant papers, create `strategy__` entities in memory.json:

```json
{
  "name": "strategy__{methodology}_{topic}_{year}",
  "entityType": "strategy",
  "observations": [
    "source_paper: source__arxiv_{id}",
    "methodology_type: {type}",
    "entry_logic: {extracted from paper}",
    "exit_logic: {extracted from paper}",
    "implementation_status: not_started"
  ]
}
```

Use Memory MCP if available, otherwise document for manual addition.

### Step 5: Sync to nautilus_dev

Execute:
```bash
python /media/sam/1TB/nautilus_dev/scripts/sync_research.py --force
```

### Step 6: Generate Research Report

Output a structured report:

```markdown
## Research Report: {topic}

### Classification
- Domain: {domain}
- Confidence: {confidence}

### Papers Found ({count})

| # | Title | Year | Relevance | Methodology |
|---|-------|------|-----------|-------------|
| 1 | {title} | {year} | {score}/10 | {type} |

### Top Paper Summary

**{title}** ({arxiv_id})

{methodology_summary}

**Key Indicators**: {indicators_list}

**NautilusTrader Mapping**:
- {indicator} → {nautilus_class}

### Entities Created
- strategy__{id1}
- strategy__{id2}

### Next Steps
1. Review entities in `docs/research/strategies.json`
2. Run `/speckit.specify spec-{N}` to create spec from findings
3. Run `/speckit.plan spec-{N}` to plan implementation
```

## Integration with SpecKit

After `/research {topic}`, you can:
```
/speckit.specify spec-020   # Uses research findings
/speckit.plan spec-020      # Creates implementation plan
```

## Requirements

- MCP: `semantic-router` (query classification)
- MCP: `paper-search-mcp` (paper search)
- Script: `scripts/sync_research.py` (entity sync)
- Agent: `strategy-researcher` (paper analysis)

## Examples

```
/research walk-forward validation
/research momentum factor investing
/research high frequency market making
/research statistical arbitrage cointegration
```
