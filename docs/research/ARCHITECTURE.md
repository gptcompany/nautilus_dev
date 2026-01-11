# Research Pipeline Architecture

> Light documentation for Spec 022. Full details in `specs/022-academic-research-pipeline/`

## Overview

```
/research <topic>
     │
     ▼
[1. RAG Check] ─────────► Neo4j (existing papers?)
     │                        │
     │ (if new papers needed) │ (if existing found)
     ▼                        ▼
[2. paper-search MCP] ◄─── Return existing
     │
     ▼
[3. Download + Parse] ────► MinerU (formulas)
     │
     ▼
[4. Store] ───────────────► Neo4j (graph) + DuckDB (analytics)
```

## Components Status

| Component | Location | Status | Port |
|-----------|----------|--------|------|
| paper-search | pip package | MCP server (REQUIRED) | - |
| Neo4j | Docker: neo4j-research | ✅ Running | 7474, 7687 |
| DuckDB | nautilus_dev/data/research.duckdb | ✅ 7.6MB | - |
| Events Daemon | research_events.py | ✅ Running | - |
| MinerU | academic_research/.venv_mineru/ | ✅ Installed | - |
| WolframAlpha | MCP server | Optional (formula validation) | - |

> **Note**: semantic-router removed (2026-01-09). 100% trading focus = no multi-domain classification needed.

## Data Flow

### 1. RAG Retrieval (semantic search existing)
```python
from scripts.research_rerank import search_papers

# Semantic search with embeddings
existing = search_papers("momentum trading", top_k=10, min_similarity=0.4)
# → Returns papers ranked by cosine similarity
```

**RAG Components**:
| Component | Script | Function |
|-----------|--------|----------|
| Embeddings | `research_rerank.py` | all-MiniLM-L6-v2 (384 dim) |
| Vector Search | `search_papers()` | DuckDB + cosine similarity |
| Rerank | `rerank_search_results()` | 70% similarity + 30% relevance |
| Graph Query | `research_query.py` | Neo4j Cypher |

### 2. Paper Search (paper-search-mcp)
```
trading_strategy → arXiv q-fin, SSRN, papers-with-code
biomedical → PubMed, bioRxiv
stem_cs → arXiv, Semantic Scholar
```

### 3. Entity Storage

**memory.json** (academic_research):
- source__ → Papers
- strategy__ → Trading strategies
- formula__ → Mathematical formulas

**Neo4j** (graph relationships):
```cypher
MATCH (p:Paper)-[:CONTAINS]->(f:Formula)
MATCH (s:Strategy)-[:BASED_ON]->(p:Paper)
```

**DuckDB** (event sourcing + analytics):
```sql
SELECT * FROM events WHERE event_type = 'paper_discovered'
SELECT * FROM strategies WHERE sharpe > 1.5
```

### 4. Sync Scripts

| Script | Direction | Purpose |
|--------|-----------|---------|
| sync_research.py | memory.json → strategies.json | Cross-repo sync |
| sync_memory_to_neo4j.py | memory.json → Neo4j | Graph population |
| sync_neo4j_to_duckdb.py | Neo4j → DuckDB | Analytics export |
| research_events.py | Events → Neo4j (daemon) | Real-time sync |

## Event Types

```python
class EventType(Enum):
    PAPER_DISCOVERED = "paper_discovered"
    PAPER_DOWNLOADED = "paper_downloaded"
    PAPER_PARSED = "paper_parsed"
    FORMULA_EXTRACTED = "formula_extracted"
    FORMULA_VALIDATED = "formula_validated"
    STRATEGY_CREATED = "strategy_created"
```

## Quick Commands

```bash
# Check Neo4j
docker ps --filter "name=neo4j"
open http://localhost:7474

# Check daemon health
cat /tmp/research_events_health.json

# Sync entities
python scripts/sync_research.py --force

# Query DuckDB
python -c "import duckdb; print(duckdb.connect('data/research.duckdb').execute('SELECT COUNT(*) FROM events').fetchone())"
```

## MCP Configuration

**nautilus_dev/.mcp.json**:
```json
{
  "mcpServers": {
    "paper-search-mcp": {
      "command": "python3",
      "args": ["-m", "paper_search_mcp.server"],
      "description": "Multi-source paper search (REQUIRED)"
    },
    "wolframalpha": {
      "command": "node",
      "args": ["/path/to/wolframalpha-llm-mcp/build/index.js"],
      "description": "Formula validation (OPTIONAL)"
    }
  }
}
```

## Known Issues

| Issue | Cause | Workaround |
|-------|-------|------------|
| DuckDB lock conflict | Another process using file | Kill other process or wait |
| CUDA warning | Old NVIDIA driver | Ignored (uses CPU) |

## Related Specs

- **022**: Academic Research Pipeline (this)
- **028**: PMW Validation Philosophy
- **032**: ADTS Discounting (uses formulas)
