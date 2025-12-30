#!/bin/bash
# QuestDB Grafana Data Source Verification Script

echo "=========================================="
echo "QuestDB Grafana Setup Verification"
echo "=========================================="
echo ""

# Check Grafana is running
echo "1. Checking Grafana service..."
if systemctl is-active --quiet grafana-server; then
    echo "   ✓ Grafana is running"
    grafana_version=$(curl -s http://localhost:3000/api/health | jq -r '.version')
    echo "   Version: $grafana_version"
else
    echo "   ✗ Grafana is not running"
    exit 1
fi
echo ""

# Check QuestDB plugin
echo "2. Checking QuestDB plugin..."
if sudo test -d "/var/lib/grafana/plugins/questdb-questdb-datasource"; then
    echo "   ✓ QuestDB plugin installed"
    plugin_version=$(sudo cat /var/lib/grafana/plugins/questdb-questdb-datasource/plugin.json | jq -r '.info.version')
    echo "   Version: $plugin_version"
else
    echo "   ✗ QuestDB plugin not found"
    exit 1
fi
echo ""

# Check plugin process
echo "3. Checking QuestDB plugin process..."
if pgrep -f "gpx_questdb_linux_amd64" > /dev/null; then
    echo "   ✓ QuestDB plugin process is running"
else
    echo "   ✗ QuestDB plugin process not running"
fi
echo ""

# Check QuestDB connection
echo "4. Checking QuestDB connection..."
if curl -s -f "http://localhost:9000/exec?query=SELECT%201" > /dev/null 2>&1; then
    echo "   ✓ QuestDB HTTP API is accessible (port 9000)"
    questdb_version=$(curl -s "http://localhost:9000/exec?query=SELECT%20version()" | jq -r '.dataset[0][0]')
    echo "   Version: $questdb_version"
else
    echo "   ✗ QuestDB HTTP API not accessible"
    exit 1
fi
echo ""

# Check provisioning file
echo "5. Checking provisioning configuration..."
if [ -f "/etc/grafana/provisioning/datasources/questdb.yaml" ]; then
    echo "   ✓ Provisioning file exists"
    file_perms=$(stat -c "%a %U:%G" /etc/grafana/provisioning/datasources/questdb.yaml)
    echo "   Permissions: $file_perms"
else
    echo "   ✗ Provisioning file not found"
    exit 1
fi
echo ""

# Check datasource in logs
echo "6. Checking Grafana logs for datasource..."
if sudo grep -q "inserting datasource from configuration.*name=QuestDB" /var/log/grafana/grafana.log; then
    echo "   ✓ QuestDB datasource provisioned successfully"
    uid=$(sudo grep "inserting datasource from configuration.*name=QuestDB" /var/log/grafana/grafana.log | tail -1 | grep -oP 'uid=\K[A-Z0-9]+')
    echo "   UID: $uid"
else
    echo "   ✗ Datasource not found in logs"
fi
echo ""

# Test query
echo "7. Testing QuestDB query..."
result=$(curl -s "http://localhost:9000/exec?query=SHOW%20TABLES" | jq -r '.dataset[] | .[0]')
if [ -n "$result" ]; then
    echo "   ✓ Query successful"
    echo "   Available tables:"
    echo "$result" | sed 's/^/     - /'
else
    echo "   ✗ Query failed"
fi
echo ""

echo "=========================================="
echo "Verification Complete!"
echo "=========================================="
echo ""
echo "Access Grafana at: http://localhost:3000"
echo "Data source: QuestDB (set as default)"
echo ""
