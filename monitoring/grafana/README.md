# Grafana Monitoring Setup

## Overview

Grafana instance configured for monitoring NautilusTrader trading operations with QuestDB as the primary data source.

## Instance Details

- **URL**: http://localhost:3000
- **Type**: Native systemd service (not Docker)
- **Version**: 12.3.0
- **Config**: /etc/grafana/grafana.ini
- **Data**: /var/lib/grafana
- **Logs**: /var/log/grafana/grafana.log
- **Provisioning**: /etc/grafana/provisioning

## Data Sources

### QuestDB (Default)

- **Plugin**: questdb-questdb-datasource v0.1.6
- **Type**: questdb-questdb-datasource
- **URL**: http://localhost:9000
- **UID**: P2596F1C8E12435D2
- **Protocol**: HTTP API (port 9000)
- **Provisioning**: /etc/grafana/provisioning/datasources/questdb.yaml

**Available Tables**:
- `trading_metrics` - Trading performance metrics
- `pipeline_metrics` - Data pipeline metrics
- `exchange_status` - Exchange connection status
- `daemon_metrics` - Background daemon metrics

## Provisioning Structure

```
/media/sam/1TB/nautilus_dev/monitoring/grafana/
└── provisioning/
    └── datasources/
        └── questdb.yaml (synced to /etc/grafana/provisioning/datasources/)
```

## Management Commands

### Grafana Service
```bash
# Status
sudo systemctl status grafana-server

# Restart
sudo systemctl restart grafana-server

# Logs
sudo tail -f /var/log/grafana/grafana.log
```

### Plugin Management
```bash
# List plugins
grafana-cli plugins ls

# Install plugin
sudo grafana-cli plugins install <plugin-name>

# Check plugin directory
sudo ls -la /var/lib/grafana/plugins/
```

### Provisioning Changes
```bash
# After updating questdb.yaml
sudo cp provisioning/datasources/questdb.yaml /etc/grafana/provisioning/datasources/
sudo chown grafana:grafana /etc/grafana/provisioning/datasources/questdb.yaml
sudo chmod 640 /etc/grafana/provisioning/datasources/questdb.yaml
sudo systemctl restart grafana-server
```

## QuestDB Connection Testing

### Via HTTP API
```bash
# Test connection
curl -s "http://localhost:9000/exec?query=SELECT%20'test'%20as%20message"

# List tables
curl -s "http://localhost:9000/exec?query=SHOW%20TABLES"

# Query table
curl -s "http://localhost:9000/exec?query=SELECT%20COUNT(*)%20FROM%20trading_metrics"
```

### Via PostgreSQL Protocol
QuestDB also supports PostgreSQL wire protocol on port 8812:
```bash
psql -h localhost -p 8812 -U admin -d qdb
```

## Troubleshooting

### Data Source Not Appearing
1. Check plugin installation: `sudo ls /var/lib/grafana/plugins/questdb-questdb-datasource/`
2. Check plugin permissions: `sudo chown -R grafana:grafana /var/lib/grafana/plugins/questdb-questdb-datasource`
3. Check logs: `sudo grep questdb /var/log/grafana/grafana.log`
4. Restart: `sudo systemctl restart grafana-server`

### Provisioning Errors
1. Check file permissions: `sudo ls -la /etc/grafana/provisioning/datasources/questdb.yaml`
2. Should be: `-rw-r----- grafana grafana questdb.yaml`
3. Fix: `sudo chown grafana:grafana /etc/grafana/provisioning/datasources/questdb.yaml`
4. Check logs: `sudo grep provisioning /var/log/grafana/grafana.log`

### QuestDB Connection Issues
1. Verify QuestDB is running: `docker ps | grep questdb`
2. Test HTTP API: `curl http://localhost:9000/exec?query=SELECT%201`
3. Check firewall: `sudo netstat -tlnp | grep 9000`

## Configuration File Reference

**questdb.yaml**:
```yaml
apiVersion: 1

datasources:
  - name: QuestDB
    type: questdb-questdb-datasource
    access: proxy
    url: http://localhost:9000
    isDefault: true
    jsonData:
      httpMode: http
    editable: true
    version: 1
```

## Next Steps

1. Create dashboards for trading metrics visualization
2. Set up alerting rules for trading anomalies
3. Configure additional data sources if needed (Prometheus, Loki, etc.)
4. Import pre-built dashboards from Grafana marketplace
