# Quickstart: Alpha-Evolve Dashboard

**Created**: 2025-12-28
**Time to complete**: ~15 minutes

## Prerequisites

- [x] Grafana running at http://localhost:3000
- [x] QuestDB running and healthy
- [x] Docker Compose stack active (`monitoring/docker-compose.yml`)
- [x] Alpha-Evolve installed (`scripts/alpha_evolve/`)

## Step 1: Create QuestDB Table (2 min)

```bash
# Apply the schema to QuestDB
curl -G "http://localhost:9000/exec" \
  --data-urlencode "query=$(cat specs/010-alpha-evolve-dashboard/contracts/evolution_metrics.sql)"
```

Or via QuestDB web console (http://localhost:9000):
- Copy contents of `specs/010-alpha-evolve-dashboard/contracts/evolution_metrics.sql`
- Paste and execute

## Step 2: Deploy Dashboard (2 min)

```bash
# Copy dashboard to Grafana provisioning
cp monitoring/grafana/dashboards/evolution.json \
   monitoring/grafana/dashboards/

# Restart Grafana to pick up new dashboard (if not hot-reloading)
docker-compose -f monitoring/docker-compose.yml restart grafana
```

## Step 3: Verify Installation (1 min)

1. Open Grafana: http://localhost:3000
2. Navigate to Dashboards
3. Find "Alpha-Evolve Evolution" dashboard
4. Verify all 4 panels load (may show "No data" initially)

## Step 4: Generate Test Data (5 min)

Option A: Run a quick evolution:
```bash
cd /media/sam/1TB/nautilus_dev
source /media/sam/2TB-NVMe/prod/apps/nautilus_nightly/nautilus_nightly_env/bin/activate

# Run 5 iterations for testing
python -m scripts.alpha_evolve.cli start \
  --seed momentum \
  --experiment dashboard_test \
  --iterations 5
```

Option B: Insert sample data directly:
```sql
-- In QuestDB console
INSERT INTO evolution_metrics VALUES
  (now() - interval '1h', 'seed-001', 'test_exp', 0, NULL, 1.5, 2.0, 10.5, 0.35, 0.65, 100, 0.55, 'seed', 0),
  (now() - interval '50m', 'child-001', 'test_exp', 1, 'seed-001', 1.8, 2.5, 8.2, 0.42, 0.78, 120, 0.58, 'success', 2340),
  (now() - interval '40m', 'child-002', 'test_exp', 1, 'seed-001', 0, 0, 0, 0, 0, 0, 0, 'syntax_error', 1500),
  (now() - interval '30m', 'child-003', 'test_exp', 2, 'child-001', 2.1, 3.2, 6.5, 0.48, 0.92, 150, 0.62, 'success', 2100),
  (now() - interval '20m', 'child-004', 'test_exp', 3, 'child-003', 2.4, 3.8, 5.2, 0.55, 1.05, 180, 0.65, 'success', 1890);
```

## Step 5: Explore Dashboard

### Panel 1: Fitness Progress
- Shows best fitness (Calmar ratio) over time
- Filter by experiment using dropdown
- Hover for details on each generation

### Panel 2: Top Strategies
- Table of top 10 strategies by Calmar ratio
- Click column headers to sort by different metrics
- Strategy ID links to code (if configured)

### Panel 3: Population Stats
- Gauges showing current population size
- Generation count and average fitness
- Fitness distribution histogram

### Panel 4: Mutation Stats
- Pie chart of mutation outcomes
- Success rate gauge
- Trend over time (if available)

## Troubleshooting

### Dashboard shows "No data"
1. Check QuestDB is running: `curl http://localhost:9000/exec?query=SELECT+1`
2. Verify table exists: `SELECT * FROM evolution_metrics LIMIT 5`
3. Check experiment filter matches your data

### Dashboard not appearing
1. Verify JSON is valid: `python -m json.tool monitoring/grafana/dashboards/evolution.json`
2. Check Grafana logs: `docker-compose -f monitoring/docker-compose.yml logs grafana`
3. Verify provisioning path in `monitoring/grafana/provisioning/dashboards/default.yaml`

### Auto-refresh not working
1. Dashboard should auto-refresh every 5 seconds
2. Check browser console for errors
3. Verify QuestDB connection in Grafana data sources

## Next Steps

- Configure alerting for fitness stagnation
- Add custom panels for specific metrics
- Export dashboard for sharing
