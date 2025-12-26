# Quickstart: Grafana + QuestDB Monitoring Stack

**Time to First Dashboard**: ~15 minutes

## Prerequisites

- Docker >= 24.0
- Docker Compose >= 2.0
- 10GB+ free disk space

## 1. Start the Stack

```bash
# Navigate to monitoring directory
cd monitoring/

# Start all services
docker-compose up -d

# Verify services are healthy
docker-compose ps
```

Expected output:
```
NAME       STATUS          PORTS
questdb    Up (healthy)    9000, 8812, 9009
grafana    Up (healthy)    3000
```

## 2. Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| Grafana | http://localhost:3000 | admin / admin |
| QuestDB Console | http://localhost:9000 | (no auth) |

## 3. Verify Data Source

1. Open Grafana: http://localhost:3000
2. Navigate to: Connections → Data sources → QuestDB
3. Click "Test" - should show "Data source is working"

## 4. View Pre-Built Dashboards

1. Navigate to: Dashboards → Trading folder
2. Open "Health Dashboard"

Available dashboards:
- **Health Dashboard**: Daemon uptime, errors, fetches
- **Pipeline Dashboard**: OI/Funding/Liquidation throughput
- **Exchange Dashboard**: Connectivity status per exchange

## 5. Send Test Metrics

```python
from questdb.ingress import Sender
import time

# Connect to QuestDB
sender = Sender.from_conf("http::addr=localhost:9000")

# Send a test metric
sender.row(
    "daemon_metrics",
    symbols={"host": "test-server", "env": "dev"},
    columns={
        "fetch_count": 10,
        "error_count": 0,
        "liquidation_count": 5,
        "uptime_seconds": 3600.0,
        "running": True,
    },
    at=int(time.time() * 1e9)
)
sender.flush()
sender.close()

print("Test metric sent!")
```

## 6. Query Data

### QuestDB Console (http://localhost:9000)

```sql
-- View all daemon metrics
SELECT * FROM daemon_metrics
ORDER BY timestamp DESC
LIMIT 10;

-- Fetch rate per hour
SELECT
    timestamp,
    fetch_count
FROM daemon_metrics
SAMPLE BY 1h;
```

### Grafana Explore

1. Navigate to: Explore
2. Select: QuestDB data source
3. Enter query and run

## 7. Configure Alerts (Optional)

### Telegram

1. Create bot via @BotFather
2. Get chat ID from @userinfobot
3. Edit `.env`:
   ```
   TELEGRAM_BOT_TOKEN=your_token
   TELEGRAM_CHAT_ID=your_chat_id
   ```
4. Restart Grafana: `docker-compose restart grafana`

### Discord

1. Create webhook in Discord channel settings
2. Edit `.env`:
   ```
   DISCORD_WEBHOOK_URL=your_webhook_url
   ```
3. Restart Grafana

## Directory Structure

```
monitoring/
├── docker-compose.yml
├── .env                          # Environment variables
├── questdb/
│   └── server.conf               # QuestDB configuration
└── grafana/
    ├── provisioning/
    │   ├── datasources/
    │   │   └── questdb.yaml      # QuestDB data source
    │   ├── dashboards/
    │   │   └── default.yaml      # Dashboard provider
    │   └── alerting/
    │       ├── alert-rules.yaml  # Alert definitions
    │       └── contact-points.yaml
    └── dashboards/
        ├── health.json           # Health dashboard
        ├── pipeline.json         # Pipeline dashboard
        └── exchange.json         # Exchange dashboard
```

## Common Commands

```bash
# View logs
docker-compose logs -f questdb
docker-compose logs -f grafana

# Restart services
docker-compose restart

# Stop all
docker-compose down

# Stop and remove data
docker-compose down -v

# QuestDB health check
curl http://localhost:9000/api/v1/ready
```

## Troubleshooting

### Grafana can't connect to QuestDB

1. Check QuestDB is healthy: `docker-compose ps`
2. Verify network: `docker network ls`
3. Test connection: `docker exec grafana curl http://questdb:8812`

### No data in dashboards

1. Verify metrics are being sent (check QuestDB console)
2. Check time range selector in Grafana
3. Verify table exists: `SHOW TABLES;` in QuestDB

### Alerts not firing

1. Check alert rules: Alerting → Alert rules
2. Verify contact points: Alerting → Contact points
3. Check notification history: Alerting → Notification history

## Next Steps

1. Integrate with DaemonRunner (Spec 001)
2. Add custom dashboard panels
3. Configure retention policies
4. Set up backup strategy
