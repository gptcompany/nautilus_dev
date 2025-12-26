# Nautilus Monitoring Stack

Production monitoring for NautilusTrader using QuestDB (time-series) + Grafana (visualization).

## Quick Start

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Start the stack
docker-compose up -d

# 3. Verify services
./scripts/healthcheck.sh --verbose

# 4. Access Grafana
open http://localhost:3000  # admin/admin
```

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Collectors    │────▶│    QuestDB      │◀────│    Grafana      │
│  (Python)       │ ILP │  (Time-Series)  │ SQL │  (Dashboards)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
   DaemonCollector         Port 9000            Port 3000
   ExchangeCollector       Port 9009 (ILP)      Dashboards
   PipelineCollector       Port 8812 (PG)       Alerting
   TradingCollector
```

## Docker Compose Commands (T072)

### Service Management

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d questdb
docker-compose up -d grafana

# Stop all services
docker-compose down

# Stop and remove volumes (CAUTION: deletes data)
docker-compose down -v

# Restart services
docker-compose restart
docker-compose restart grafana

# View logs
docker-compose logs -f
docker-compose logs -f questdb
docker-compose logs -f grafana --tail=100
```

### Status & Health

```bash
# Check running containers
docker-compose ps

# Health check
./scripts/healthcheck.sh --verbose

# Resource usage
docker stats nautilus-questdb nautilus-grafana
```

### Debugging

```bash
# Shell into container
docker-compose exec questdb sh
docker-compose exec grafana sh

# QuestDB Web Console
open http://localhost:9000

# Test QuestDB connection
curl -s "http://localhost:9000/exec?query=SELECT%201"

# List tables
curl -s "http://localhost:9000/exec?query=SHOW%20TABLES"
```

### Database Operations

```bash
# Initialize tables (run SQL schemas)
for sql in schemas/*.sql; do
    curl -G "http://localhost:9000/exec" --data-urlencode "query=$(cat $sql)"
done

# Backup QuestDB data
docker-compose exec questdb tar -czvf /tmp/backup.tar.gz /var/lib/questdb/db
docker cp nautilus-questdb:/tmp/backup.tar.gz ./backup.tar.gz

# Restore QuestDB data
docker cp backup.tar.gz nautilus-questdb:/tmp/
docker-compose exec questdb tar -xzvf /tmp/backup.tar.gz -C /
```

## Directory Structure

```
monitoring/
├── docker-compose.yml      # Container orchestration
├── .env.example            # Environment template
├── README.md               # This file
│
├── questdb/
│   └── server.conf         # QuestDB configuration
│
├── grafana/
│   ├── dashboards/         # Dashboard JSON definitions
│   │   ├── health.json     # Daemon health (US1)
│   │   ├── pipeline.json   # Pipeline metrics (US2)
│   │   ├── exchange.json   # Exchange connectivity (US3)
│   │   └── trading.json    # Trading performance (US5)
│   └── provisioning/
│       ├── datasources/    # QuestDB datasource
│       ├── dashboards/     # Dashboard provider
│       └── alerting/       # Alert rules & contacts
│
├── schemas/                # QuestDB table schemas
│   ├── daemon_metrics.sql
│   ├── exchange_status.sql
│   ├── pipeline_metrics.sql
│   └── trading_metrics.sql
│
├── scripts/
│   ├── healthcheck.sh      # Service health check
│   ├── retention_cleanup.py # Data retention management
│   └── export_queries.sql  # CSV export examples
│
├── collectors/             # Python metric collectors
│   ├── __init__.py         # BaseCollector interface
│   ├── daemon.py           # DaemonCollector
│   ├── exchange.py         # ExchangeCollector
│   ├── pipeline.py         # PipelineCollector
│   └── trading.py          # TradingCollector
│
├── models.py               # Pydantic metric models
├── config.py               # MonitoringConfig
├── client.py               # MetricsClient (QuestDB HTTP ILP)
└── metrics_collector.py    # Main orchestrator
```

## Dashboards

| Dashboard | UID | Description |
|-----------|-----|-------------|
| Health | nautilus-health | Daemon uptime, memory, errors |
| Pipeline | nautilus-pipeline | OI/Funding fetches, data gaps |
| Exchange | nautilus-exchange | Connection status, latency |
| Trading | nautilus-trading | PnL, positions, orders |

## Alerting

Alerts are provisioned via YAML files in `grafana/provisioning/alerting/`:

- **alert-rules.yaml**: Alert conditions
- **contact-points.yaml**: Notification channels (Telegram, Discord, Email)
- **policies.yaml**: Routing rules (severity-based)

### Configure Notifications

1. Edit `.env` with your credentials:
   ```bash
   TELEGRAM_BOT_TOKEN=your_bot_token
   TELEGRAM_CHAT_ID=your_chat_id
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
   ```

2. Restart Grafana:
   ```bash
   docker-compose restart grafana
   ```

## Running the Metrics Collector

```bash
# Using the orchestrator
python -m monitoring.metrics_collector

# With Prometheus endpoint
python -m monitoring.metrics_collector --prometheus-port 8080

# Prometheus metrics
curl http://localhost:8080/metrics

# Health check
curl http://localhost:8080/health
```

## Data Retention

Default retention is 90 days. Run cleanup manually or via cron:

```bash
# Dry run (see what would be deleted)
python scripts/retention_cleanup.py --dry-run

# Execute cleanup
python scripts/retention_cleanup.py --retention-days 90

# Cron entry (daily at 3 AM)
0 3 * * * /path/to/venv/bin/python /path/to/retention_cleanup.py >> /var/log/questdb-cleanup.log 2>&1
```

## Ports Reference

| Service | Port | Protocol | Purpose |
|---------|------|----------|---------|
| QuestDB | 9000 | HTTP | API + Web Console |
| QuestDB | 9009 | TCP | InfluxDB Line Protocol |
| QuestDB | 8812 | TCP | PostgreSQL wire protocol |
| Grafana | 3000 | HTTP | Web UI |
| Collector | 8080 | HTTP | Prometheus /metrics |

## Troubleshooting

### QuestDB not starting
```bash
# Check logs
docker-compose logs questdb

# Check disk space
df -h

# Check if port is in use
sudo netstat -tlnp | grep 9000
```

### Grafana dashboards not loading
```bash
# Check provisioning logs
docker-compose logs grafana | grep provisioning

# Verify dashboard files
ls -la grafana/dashboards/

# Restart Grafana
docker-compose restart grafana
```

### Metrics not appearing
```bash
# Check if tables exist
curl "http://localhost:9000/exec?query=SHOW%20TABLES"

# Check recent data
curl "http://localhost:9000/exec?query=SELECT%20*%20FROM%20daemon_metrics%20LIMIT%205"

# Check collector logs
docker-compose logs -f | grep collector
```

## Performance Tuning

For high-throughput environments (>10k writes/sec):

1. **QuestDB**: Increase WAL quota in `server.conf`:
   ```
   cairo.wal.apply.table.time.quota=200
   ```

2. **Collector**: Adjust batch size in `.env`:
   ```
   MONITORING_BATCH_SIZE=1000
   MONITORING_FLUSH_INTERVAL=1.0
   ```

3. **Docker**: Increase memory limits:
   ```yaml
   services:
     questdb:
       deploy:
         resources:
           limits:
             memory: 4G
   ```
