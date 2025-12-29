# Troubleshooting Guide: Academic Research Pipeline

## Common Issues

### 1. Semantic Router Classification

#### Problem: Queries always classified as "unknown"

**Symptoms**:
- Confidence score below threshold (0.5)
- Domain shows as "unknown" for valid trading queries

**Solutions**:

1. **Check utterances match query style**:
   ```python
   # Look at routes_config.py
   # Ensure TRADING_STRATEGY_UTTERANCES includes similar phrasing
   ```

2. **Lower confidence threshold temporarily**:
   ```python
   # In routes_config.py
   CONFIDENCE_THRESHOLD = 0.3  # Lower for testing
   ```

3. **Add more utterances**:
   - If queries like "momentum backtest" fail, add similar utterances
   - Aim for 20+ utterances per domain

#### Problem: Trading queries classified as "stem_cs"

**Cause**: Overlap between trading and STEM_CS utterances

**Solution**: Move trading-specific utterances from STEM_CS to TRADING_STRATEGY:
```python
# These should be in TRADING_STRATEGY_UTTERANCES:
"algorithmic trading strategies"
"market making spread optimization"
"pairs trading cointegration"
```

---

### 2. Entity Validation

#### Problem: "Missing required observation" error

**Symptoms**:
```
ValidationError: observations.source_paper: Missing required observation
```

**Solution**: Ensure all required observations are present:
```python
required_obs = [
    "source_paper",      # Must start with "source__"
    "methodology_type",  # Must be valid enum value
    "entry_logic",       # Natural language description
    "exit_logic",        # Natural language description
    "implementation_status"  # Must be valid enum value
]
```

#### Problem: Invalid methodology_type

**Symptoms**:
```
ValidationError: observations.methodology_type: Invalid type 'trend_reversal'
```

**Solution**: Use valid methodology types only:
- momentum
- mean_reversion
- market_making
- arbitrage
- trend_following
- statistical_arbitrage

---

### 3. Sync Script

#### Problem: "Invalid JSON in memory.json"

**Symptoms**:
```
ERROR: Invalid JSON in /media/sam/1TB/academic_research/memory.json: Expecting ',' delimiter
```

**Solutions**:

1. **Validate JSON manually**:
   ```bash
   python -m json.tool < memory.json > /dev/null
   ```

2. **Find the error location**:
   ```bash
   python -c "import json; json.load(open('memory.json'))"
   ```

3. **Common fixes**:
   - Missing comma between array elements
   - Trailing comma after last element
   - Unescaped quotes in strings

#### Problem: Sync shows "fresh, skipping"

**Symptoms**:
```
Sync is fresh, skipping. Use --force to override.
```

**Solution**: Force sync or wait for staleness threshold:
```bash
# Force immediate sync
python scripts/sync_research.py --force

# Or adjust threshold in CONFIG
"stale_threshold_hours": 1  # Lower for testing
```

---

### 4. Paper-to-Strategy Conversion

#### Problem: Missing NautilusTrader indicator mapping

**Symptoms**:
```
Warning: Indicator 'VWMA' not found in indicator_mapping.md
```

**Solutions**:

1. **Check indicator_mapping.md** for closest match
2. **Add to custom_indicators_needed** section
3. **Use alternative indicator**:
   - VWMA → Consider VWAP or SMA
   - Ichimoku → Use EMA combination

#### Problem: Generated spec has [NEEDS CLARIFICATION] markers

**Cause**: Paper methodology was unclear

**Solution**:
1. Read paper sections marked as unclear
2. Fill in missing details manually
3. Remove [NEEDS CLARIFICATION] markers before proceeding

---

### 5. Alpha-Evolve Integration

#### Problem: All variants have similar scores

**Symptoms**:
```
| A | 1.5 | 15% | 55% | 77 |
| B | 1.4 | 16% | 54% | 75 |
| C | 1.5 | 14% | 56% | 76 |
```

**Cause**: Strategy logic too simple, or variants too similar

**Solutions**:
1. Request more diverse approaches
2. Vary indicator parameters significantly
3. Use different risk management strategies

#### Problem: Backtest crashes during evaluation

**Solutions**:

1. **Check data availability**:
   ```python
   catalog = ParquetDataCatalog("./catalog")
   bars = catalog.bars(bar_type=bar_type)
   print(f"Available bars: {len(list(bars))}")
   ```

2. **Verify indicator initialization**:
   ```python
   if not self.ema.initialized:
       return  # Skip until indicators warm up
   ```

3. **Check for division by zero** in custom logic

---

### 6. Cross-Repository Issues

#### Problem: "Path not found" for academic_research

**Symptoms**:
```
ERROR: Source file not found: /media/sam/1TB/academic_research/memory.json
```

**Solutions**:

1. **Verify path exists**:
   ```bash
   ls -la /media/sam/1TB/academic_research/memory.json
   ```

2. **Check mount** (if external drive):
   ```bash
   mount | grep academic_research
   ```

3. **Update CONFIG** if path changed:
   ```python
   CONFIG = {
       "source": Path("/new/path/to/memory.json"),
   }
   ```

#### Problem: Permission denied accessing memory.json

**Solutions**:
```bash
# Check permissions
ls -la /media/sam/1TB/academic_research/memory.json

# Fix permissions if needed
chmod 644 /media/sam/1TB/academic_research/memory.json
```

---

## Debug Commands

### Test semantic router classification
```bash
cd /media/sam/1TB/academic_research/semantic_router_mcp
python -c "
from routes_config import *
from semantic_router import Route, SemanticRouter
from semantic_router.encoders import HuggingFaceEncoder

routes = [
    Route(name='trading_strategy', utterances=TRADING_STRATEGY_UTTERANCES),
]
encoder = HuggingFaceEncoder(name='sentence-transformers/all-MiniLM-L6-v2')
router = SemanticRouter(encoder=encoder, routes=routes)
router.sync(sync_mode='local')

test_queries = [
    'momentum trading backtest results',
    'mean reversion pairs trading',
    'market making spread optimization',
]
for q in test_queries:
    result = router(q)
    print(f'{q}: {result.name if result else \"unknown\"}')
"
```

### Test entity validation
```bash
cd /media/sam/1TB/academic_research
python scripts/validate_entity.py --test
```

### Test sync script
```bash
cd /media/sam/1TB/nautilus_dev
python scripts/sync_research.py --dry-run
```

---

## Getting Help

1. **Check Discord docs** (`docs/discord/*.md`) for community solutions
2. **Search Context7** for NautilusTrader API questions
3. **Run alpha-debug** on failing code
4. **Review spec.md** for this pipeline: `specs/022-academic-research-pipeline/spec.md`

---

**Last Updated**: 2025-12-29
**Spec**: 022-academic-research-pipeline
