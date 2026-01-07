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

### Step 2.6: Paper Renaming (MANDATORY)

**CRITICAL**: Rename downloaded papers to standardized kebab-case format for discoverability.

**Folder Structure**:
```
docs/research/papers/
├── spec-032/                    # Papers for spec-032
│   ├── 2021-russo-adaptive-discounted-thompson.pdf
│   └── 2019-agrawal-thompson-sampling-contextual.pdf
├── spec-033/                    # Papers for spec-033
│   └── 2020-zhang-momentum-factor.pdf
└── general/                     # Papers not tied to a spec
    └── 2018-smith-market-microstructure.pdf
```

**File Naming Convention**:
```
{year}-{first_author_lastname}-{short_title_kebab}.pdf
```

**Examples**:
- `2106.12345.pdf` → `spec-032/2021-russo-adaptive-discounted-thompson.pdf`
- `10.1016_j.jfin.2023.pdf` → `general/2023-zhang-momentum-factor-crypto.pdf`

**Folder Rules**:
- If `/research` is called with spec context → save to `papers/spec-{NNN}/`
- If no spec context → save to `papers/general/`
- Create folder if it doesn't exist

**Renaming Rules**:
1. Extract year from paper metadata (publication_date or arxiv_id prefix)
2. Extract first author's lastname (lowercase, no accents)
3. Create short title: first 5-6 keywords, lowercase, hyphen-separated
4. Remove special characters, keep only `[a-z0-9-]`
5. Max 60 characters total (truncate title if needed)

**Implementation** (after each download):
```python
import re
from pathlib import Path

PAPERS_BASE = Path("/media/sam/1TB/nautilus_dev/docs/research/papers")

def standardize_paper_name(
    original_path: str,
    metadata: dict,
    spec_id: str | None = None
) -> str:
    """Rename and move paper to standardized location.

    Args:
        original_path: Path to downloaded PDF
        metadata: Paper metadata (year, authors, title)
        spec_id: Optional spec number (e.g., "032") for folder organization

    Returns:
        New path to the renamed/moved paper
    """
    year = metadata.get("year", "unknown")
    authors = metadata.get("authors", ["unknown"])
    first_author = authors[0].split()[-1].lower() if authors else "unknown"
    # Remove accents: é→e, ü→u, etc.
    first_author = first_author.encode('ascii', 'ignore').decode()
    title = metadata.get("title", "untitled")

    # Create kebab-case short title (5 words max)
    title_clean = re.sub(r'[^a-z0-9\s]', '', title.lower())
    title_words = title_clean.split()[:5]
    title_kebab = '-'.join(title_words)

    # Build filename (no spec prefix - folder handles that)
    filename = f"{year}-{first_author}-{title_kebab}"[:56] + ".pdf"

    # Determine target folder
    if spec_id:
        target_dir = PAPERS_BASE / f"spec-{spec_id}"
    else:
        target_dir = PAPERS_BASE / "general"

    # Create folder if needed
    target_dir.mkdir(parents=True, exist_ok=True)

    # Move and rename file
    old_path = Path(original_path)
    new_path = target_dir / filename
    if old_path.exists():
        old_path.rename(new_path)

    return str(new_path)
```

**Update manifest with folder paths**:
```markdown
| Paper ID | Title | Source | Status | Path |
|----------|-------|--------|--------|------|
| arxiv:2106.12345 | Adaptive Thompson... | arXiv | ✅ Downloaded | papers/spec-032/2021-russo-adaptive-thompson.pdf |
| arxiv:1904.56789 | General Trading... | arXiv | ✅ Downloaded | papers/general/2019-smith-general-trading-theory.pdf |
```

### Step 2.7: MinerU PDF Parsing (Optional - for downloaded PDFs)

**When to use**: If paper was downloaded AND contains complex math/tables.

**Skip if**: Paper is text-only or already parsed via API.

**Execution**:
```bash
# Activate MinerU venv
source /media/sam/1TB/academic_research/.venv_mineru/bin/activate

# Parse PDF to markdown (use standardized paper name from Step 2.6)
# Example: 2021-russo-adaptive-discounted-thompson.pdf → 2021-russo-adaptive-discounted-thompson/
PAPER_ID=$(basename "{paper_path}" .pdf)
OUTPUT_DIR="/media/sam/1TB/nautilus_dev/docs/research/parsed/${PAPER_ID}"

mineru -p "{paper_path}" -o "${OUTPUT_DIR}" -b pipeline -m auto -l en
```

**Output location**: `/media/sam/1TB/nautilus_dev/docs/research/parsed/{paper_id}/`

**Output files**:
```
docs/research/parsed/{paper_id}/
├── auto/
│   ├── {paper_id}.md       # Main markdown with LaTeX preserved
│   ├── images/             # Extracted figures
│   └── content_list.json   # Structured content
```

**Performance note**: CPU mode ~5-10min per 10-page paper. Background process recommended.

**Integration with Step 3.5**: If MinerU output exists, use it for better LaTeX extraction instead of API-based reading.

### Step 3: Paper Analysis + Rerank (AUTOMATIC)

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

**RERANK (AUTOMATIC)**: After scoring all papers:
```python
# Sort by relevance_score descending
papers_ranked = sorted(papers, key=lambda p: p['relevance_score'], reverse=True)

# Select top 3 for deep analysis (Step 7)
top_papers = papers_ranked[:3]

# Only papers with relevance >= 7 get downloaded
papers_to_download = [p for p in papers_ranked if p['relevance_score'] >= 7]
```

**Dedup check**: Skip papers already in Neo4j (check by arxiv_id or DOI).

**Metadata from MinerU output** (if Step 2.7 was executed):

Parse `{paper_id}_content_list.json` for structured metadata:
```python
import json

def extract_metadata_from_mineru(content_list_path: str) -> dict:
    """Extract title, authors, sections from MinerU content_list.json."""
    with open(content_list_path) as f:
        items = json.load(f)

    metadata = {"title": "", "authors": [], "sections": []}

    for item in items:
        if item.get("type") != "text":
            continue

        text = item.get("text", "").strip()
        level = item.get("text_level", 0)
        page = item.get("page_idx", 0)

        # Title: level 1, page 0
        if level == 1 and page == 0 and not metadata["title"]:
            metadata["title"] = text

        # Authors: page 0, after title, before Abstract
        elif page == 0 and metadata["title"] and "abstract" not in text.lower():
            if "@" in text or any(x in text.lower() for x in ["university", "institute", "department"]):
                metadata["authors"].append(text)

        # Sections: text_level >= 2 (headings)
        elif level >= 2:
            metadata["sections"].append({"level": level, "title": text, "page": page})

    return metadata
```

This supplements search metadata with section structure for deeper analysis.

### Step 3.5: Formula Extraction & Validation (if paper contains math)

**CRITICAL**: For papers with mathematical formulas, extract and validate them.

**Detection**: Check if paper contains:
- LaTeX equations (`$...$`, `\begin{equation}`)
- Trading formulas (Sharpe, Kelly, position sizing)
- Statistical models (regression, volatility)

**Extraction** (for downloaded PDFs):

Use the formula extraction script on MinerU output:
```bash
python /media/sam/1TB/nautilus_dev/scripts/extract_formulas.py \
    docs/research/parsed/{paper_id}/auto/{paper_id}.md \
    --output json > formulas.json
```

Or via API for papers not locally parsed:
```yaml
1. Use mcp__paper-search-mcp__read_arxiv_paper or read_semantic_paper
2. Extract LaTeX formulas from content
3. For each formula found:
   - latex: Raw LaTeX representation
   - description: What the formula computes
   - variables: List of variables with meanings
   - domain: trading|statistics|optimization
```

**Validation with WolframAlpha**:
```yaml
For each extracted formula:
1. Use mcp__wolframalpha__ask_llm with query:
   "Validate formula: {latex} - check mathematical correctness and simplify"

2. Record validation result:
   - validation_status: valid|invalid|needs_review
   - wolfram_simplification: Simplified form if available
   - numerical_example: Sample calculation

3. For trading formulas specifically:
   - "Kelly Criterion f* = (bp-q)/b" → Validate parameters
   - "Sharpe Ratio" → Verify standard form
   - "Position sizing" → Check risk constraints
```

**Create formula__ entities**:
```json
{
  "id": "formula__{domain}_{name}_{year}",
  "entityType": "mathematical_formula",
  "observations": [
    "latex: {extracted_latex}",
    "description: {what_it_computes}",
    "source_paper: source__arxiv_{id}",
    "validation_status: valid",
    "wolfram_verified: true",
    "variables: {variable_list}"
  ]
}
```

**Store in Neo4j**:
```cypher
// Create Formula node
CREATE (f:Formula {
    id: 'formula__{domain}_{name}_{year}',
    latex: '{extracted_latex}',
    domain: '{domain}',
    known_type: '{known_type}',
    validation_status: '{valid|invalid|needs_review}',
    wolfram_verified: {true|false},
    created_at: datetime()
});

// Link to Paper
MATCH (p:Paper {id: 'paper__{paper_id}'})
MATCH (f:Formula {id: 'formula__{formula_id}'})
MERGE (p)-[:CONTAINS]->(f);
```

**Skip if**: Paper has no mathematical content (pure empirical/qualitative).

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

### Step 5: Emit Events (AUTOMATIC SYNC)

**ARCHITECTURE**: Event-driven sync via daemon. Events emitted here are automatically synced to Neo4j.

**Ensure daemon is running**:
```bash
# Check health
python /media/sam/1TB/nautilus_dev/scripts/research_events.py health

# Start daemon if not running (background)
nohup python /media/sam/1TB/nautilus_dev/scripts/research_events.py daemon >> /tmp/research_events.log 2>&1 &
```

**Emit events for each discovered paper**:
```python
# For each paper found in search:
from scripts.research_events import emit_event, EventType

# Paper discovery event
emit_event(
    EventType.PAPER_DISCOVERED,
    entity_id=f"arxiv:{paper['arxiv_id']}",
    data={
        "title": paper["title"],
        "arxiv_id": paper["arxiv_id"],
        "doi": paper.get("doi"),
        "source": "arxiv"
    }
)

# After download
emit_event(
    EventType.PAPER_DOWNLOADED,
    entity_id=f"arxiv:{paper['arxiv_id']}",
    data={"pdf_path": str(pdf_path)}
)

# After parsing
emit_event(
    EventType.PAPER_PARSED,
    entity_id=f"arxiv:{paper['arxiv_id']}",
    data={"parsed_path": str(parsed_dir)}
)

# For each formula extracted
emit_event(
    EventType.FORMULA_EXTRACTED,
    entity_id=f"formula_{paper_id}_{formula_idx}",
    data={
        "paper_id": f"arxiv:{paper['arxiv_id']}",
        "latex": formula["latex"],
        "description": formula.get("description"),
        "formula_type": formula.get("type"),
        "context": formula.get("context")
    }
)

# For each strategy created
emit_event(
    EventType.STRATEGY_CREATED,
    entity_id=f"strategy_{methodology}_{topic}_{year}",
    data={
        "paper_id": f"arxiv:{paper['arxiv_id']}",
        "name": strategy_name,
        "methodology_type": methodology,
        "entry_logic": entry,
        "exit_logic": exit_
    }
)
```

**The daemon automatically**:
- Syncs events to Neo4j every 2 seconds
- Retries failed syncs with exponential backoff (3 attempts)
- Moves permanently failed events to dead letter queue
- Provides health monitoring via `/tmp/research_events_health.json`

**Idempotency**: Duplicate events (same paper/formula) are automatically skipped via checksum.

**Verification**:
```bash
# Check event stats
python /media/sam/1TB/nautilus_dev/scripts/research_events.py stats

# Check daemon health
python /media/sam/1TB/nautilus_dev/scripts/research_events.py health

# Query Neo4j (browser: http://localhost:7474)
MATCH (p:Paper)-[:CONTAINS]->(f:Formula) RETURN p.title, f.latex
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
2. Run `/speckit:specify spec-{N}` to create spec from findings
3. Run `/speckit:plan spec-{N}` to plan implementation

### Deep Analysis Available
Papers queued for formula extraction: {list if any}
Run `/research:deep {paper_id}` for detailed formula analysis.
```

### Step 7: Deferred Deep Analysis (OPTIONAL - Background)

**Purpose**: Extract formulas from TOP papers without blocking workflow.

**Trigger conditions** (automatic):
- Paper has `relevance_score >= 8`
- Paper contains mathematical content (detected in abstract)
- Max 2 papers per session

**Trigger conditions** (manual):
- User runs `/research:deep {paper_id}`

**Execution** (background, non-blocking):
```bash
# Launch background parsing for top papers
for paper_id in top_papers:
    /media/sam/1TB/nautilus_dev/scripts/parse_paper_background.sh \
        "docs/research/papers/${paper_id}.pdf" \
        "${paper_id}"
```

**Status tracking via TodoWrite** (MANDATORY):
```python
# Add parsing tasks to todo list for user visibility
TodoWrite([
    {"content": "Parsing: 2021-russo-adaptive", "status": "in_progress",
     "activeForm": "MinerU parsing (started 14:30)"},
    {"content": "Parsing: 2019-agrawal-thompson", "status": "in_progress",
     "activeForm": "MinerU parsing (started 14:31)"},
])
```

**Check completion**:
```bash
# Check status
cat docs/research/parsed/{paper_id}/.status
# → completed:1704567890:2024-01-06T14:30:00

# View extracted formulas
cat docs/research/parsed/{paper_id}/.formulas.json
```

**On completion** (next session or manual check):
1. Read `.formulas.json` from parsed output
2. Validate key formulas with WolframAlpha
3. Update Neo4j with formula__ entities
4. Enrich strategy__ entities with formula references

**Skip if**: No papers with relevance >= 8, or user declines deep analysis.

## Integration with SpecKit

After `/research {topic}`, you can:
```
/speckit:specify spec-020   # Uses research findings
/speckit:plan spec-020      # Creates implementation plan
```

## Requirements

- MCP: `semantic-router` (query classification)
- MCP: `paper-search-mcp` (paper search)
- MCP: `wolframalpha` (formula validation)
- Script: `scripts/sync_research.py` (entity sync)
- Agent: `strategy-researcher` (paper analysis)

## Examples

```
/research walk-forward validation
/research momentum factor investing
/research high frequency market making
/research statistical arbitrage cointegration
```
