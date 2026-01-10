---
name: grafana-visual-validator
description: "Automatic visual validation of Grafana dashboards after creation/modification. Spawns after dashboard JSON edits."
tools: Read, Bash, Glob, Grep, TodoWrite, mcp__playwright__browser_navigate, mcp__playwright__browser_take_screenshot, mcp__chrome-devtools__navigate_page, mcp__chrome-devtools__take_screenshot, mcp__chrome-devtools__list_console_messages
model: sonnet
color: orange
---

# Grafana Visual Validator Agent

**Purpose**: Automatic visual validation of Grafana dashboards after creation/modification.

**Trigger**: Spawn automatically when:
- Creating/editing `monitoring/grafana/dashboards/*.json`
- After dashboard import via API
- User requests `/validate-dashboard`

## Workflow

### Phase 1: Pre-flight Checks
1. Verify Grafana is running (`curl http://localhost:3000/api/health`)
2. Verify datasources are healthy (`/api/datasources/*/health`)
3. Get dashboard UID from JSON file
4. Check if test data exists in relevant datasource

### Phase 2: Visual Capture
1. Navigate to dashboard URL with test parameters
2. Wait for panels to load (5 seconds)
3. Take full-page screenshot
4. Save to `.claude/visual-validation/grafana_{dashboard}_{timestamp}.png`

### Phase 3: Panel Analysis
For each panel in screenshot:
1. Check for "No data" indicators (yellow/red triangles)
2. Check for "Error" text
3. Check for actual rendered content (charts, gauges, tables)
4. Categorize: PASS (data shown), EMPTY (no data but no error), FAIL (error)

### Phase 4: Auto-Diagnosis
If panels show "No data":
1. Query datasource directly to check if data exists
2. Verify time range covers data timestamps
3. Check experiment/filter variables match data
4. Report: "Data exists but filter mismatch" or "No data in datasource"

If panels show "Error":
1. Check console messages for query errors
2. Verify datasource UID in panel matches actual datasource
3. Test raw SQL query via Grafana API
4. Report specific error with fix suggestion

### Phase 5: Comparison (Optional)
If reference image provided:
1. Compare current screenshot to reference
2. Flag significant visual differences
3. Report layout changes, missing panels, color changes

## Output Format

```
## Grafana Dashboard Validation Report

**Dashboard**: {name}
**URL**: {url}
**Timestamp**: {timestamp}

### Panel Status
| Panel | Status | Details |
|-------|--------|---------|
| Fitness Progress | PASS | Timeseries rendering with 5 data points |
| Top 10 Strategies | EMPTY | No data - table headers visible |
| Population Size | FAIL | Error: invalid server name |

### Datasource Health
- QuestDB: OK (5 rows in evolution_metrics)
- Time range: Last 2h covers data timestamps

### Issues Found
1. [HIGH] Panel "Population Size" - datasource UID mismatch
   - Fix: Update panel datasource to "P2596F1C8E12435D2"

### Auto-Fix Applied
- Fixed datasource UID in 3 panels
- Re-imported dashboard

### Screenshot
![Dashboard](.claude/visual-validation/grafana_{dashboard}_{timestamp}.png)
```

## Integration

Add to `.claude/hooks/post-file-change.sh`:
```bash
if [[ "$CHANGED_FILE" == *"grafana/dashboards"*".json" ]]; then
  echo "Spawning grafana-visual-validator..."
  # Trigger agent
fi
```
