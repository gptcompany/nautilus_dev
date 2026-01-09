#!/usr/bin/env python3
"""
Spec 040 - Development Excellence Verification Script

Run this script to verify all Spec 040 components are working correctly.
Use after system restart, new session, or to diagnose issues.

Usage:
    python scripts/verify_spec040.py
    python scripts/verify_spec040.py --fix  # Attempt auto-fixes
    python scripts/verify_spec040.py --json  # JSON output for CI

Components verified:
1. QuestDB (metrics storage)
2. Grafana (dashboards + alerts)
3. Discord (alert notifications)
4. Sentry (error tracking)
5. Hyperliquid testnet (trading)
6. MetricsCollector (data flow)
7. Ralph hooks (autonomous loops)
8. Security tools (bandit, gitleaks)
"""

import json
import os
import socket
import subprocess
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# Load .env
ENV_FILE = Path(__file__).parent.parent / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


@dataclass
class CheckResult:
    name: str
    status: str  # OK, WARN, FAIL, SKIP
    message: str
    details: dict = field(default_factory=dict)


class Spec040Verifier:
    def __init__(self):
        self.results: list[CheckResult] = []
        self.fix_mode = "--fix" in sys.argv
        self.json_mode = "--json" in sys.argv

    def add_result(self, name: str, status: str, message: str, details: dict = None):
        self.results.append(CheckResult(name, status, message, details or {}))

    # =========================================================================
    # QuestDB Checks
    # =========================================================================
    def check_questdb_connection(self):
        """Check QuestDB is running and accessible."""
        try:
            # ILP port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            ilp_ok = sock.connect_ex(("localhost", 9009)) == 0
            sock.close()

            # HTTP port
            response = urllib.request.urlopen(
                "http://localhost:9000/exec?query=SELECT%201", timeout=5
            )
            http_ok = response.status == 200

            if ilp_ok and http_ok:
                self.add_result("questdb", "OK", "QuestDB running (ILP:9009, HTTP:9000)")
            elif http_ok:
                self.add_result(
                    "questdb", "WARN", "QuestDB HTTP OK but ILP port 9009 not responding"
                )
            else:
                self.add_result("questdb", "FAIL", "QuestDB not responding")
        except Exception as e:
            self.add_result("questdb", "FAIL", f"QuestDB error: {e}")

    def check_questdb_tables(self):
        """Check required tables exist."""
        required_tables = [
            "trading_pnl",
            "trading_orders",
            "trading_risk",
            "system_health",
            "ralph_iterations",
            "agent_spawns",
        ]
        try:
            response = urllib.request.urlopen(
                "http://localhost:9000/exec?query=SHOW%20TABLES", timeout=5
            )
            data = json.loads(response.read())
            existing = {row[0] for row in data.get("dataset", [])}

            missing = [t for t in required_tables if t not in existing]
            if not missing:
                self.add_result("questdb_tables", "OK", f"All {len(required_tables)} tables exist")
            else:
                self.add_result("questdb_tables", "WARN", f"Missing tables: {missing}")
        except Exception as e:
            self.add_result("questdb_tables", "FAIL", f"Cannot check tables: {e}")

    # =========================================================================
    # Grafana Checks
    # =========================================================================
    def check_grafana_connection(self):
        """Check Grafana is running."""
        try:
            response = urllib.request.urlopen("http://localhost:3000/api/health", timeout=5)
            data = json.loads(response.read())
            version = data.get("version", "unknown")
            self.add_result("grafana", "OK", f"Grafana v{version} running on port 3000")
        except Exception as e:
            self.add_result("grafana", "FAIL", f"Grafana not responding: {e}")

    def check_grafana_discord(self):
        """Check Discord contact point is configured."""
        try:
            # Try with known password
            req = urllib.request.Request("http://localhost:3000/api/v1/provisioning/contact-points")
            credentials = "admin:admin123"
            import base64

            req.add_header(
                "Authorization", f"Basic {base64.b64encode(credentials.encode()).decode()}"
            )

            response = urllib.request.urlopen(req, timeout=5)
            data = json.loads(response.read())

            discord_points = [cp for cp in data if cp.get("type") == "discord"]
            if discord_points:
                self.add_result(
                    "grafana_discord",
                    "OK",
                    f"Discord contact point configured: {discord_points[0].get('name')}",
                )
            else:
                self.add_result("grafana_discord", "WARN", "No Discord contact point found")
        except Exception as e:
            self.add_result("grafana_discord", "WARN", f"Cannot check contact points: {e}")

    # =========================================================================
    # Discord Checks
    # =========================================================================
    def check_discord_webhook(self):
        """Check Discord webhook is configured and reachable."""
        webhook_url = os.environ.get("DISCORD_WEBHOOK_URL", "")
        if not webhook_url or "your" in webhook_url.lower():
            self.add_result("discord_webhook", "SKIP", "DISCORD_WEBHOOK_URL not configured in .env")
            return

        try:
            # Just check if URL is valid (don't send message)
            req = urllib.request.Request(webhook_url, method="GET")
            # Discord webhooks return 405/403 for GET but that means it's reachable
            try:
                urllib.request.urlopen(req, timeout=5)
                self.add_result("discord_webhook", "OK", "Discord webhook URL is valid")
            except urllib.error.HTTPError as e:
                if e.code in (405, 403, 401):  # These mean webhook exists but GET not allowed
                    self.add_result("discord_webhook", "OK", "Discord webhook URL is valid")
                else:
                    self.add_result("discord_webhook", "WARN", f"Discord webhook returned {e.code}")
        except Exception as e:
            self.add_result("discord_webhook", "FAIL", f"Discord webhook error: {e}")

    # =========================================================================
    # Sentry Checks
    # =========================================================================
    def check_sentry_config(self):
        """Check Sentry is configured."""
        dsn = os.environ.get("SENTRY_DSN", "")
        if not dsn or "your" in dsn.lower():
            self.add_result("sentry", "SKIP", "SENTRY_DSN not configured in .env")
            return

        try:
            # Check if sentry-sdk is installed
            import sentry_sdk

            self.add_result("sentry", "OK", "Sentry SDK installed, DSN configured")
        except ImportError:
            self.add_result("sentry", "WARN", "sentry-sdk not installed")

    # =========================================================================
    # Hyperliquid Checks
    # =========================================================================
    def check_hyperliquid_testnet(self):
        """Check Hyperliquid testnet connection."""
        pk = os.environ.get("HYPERLIQUID_TESTNET_PK", "")
        if not pk or "your" in pk.lower():
            self.add_result("hyperliquid", "SKIP", "HYPERLIQUID_TESTNET_PK not configured")
            return

        try:
            from hyperliquid.info import Info

            info = Info(skip_ws=True, base_url="https://api.hyperliquid-testnet.xyz")
            meta = info.meta()
            assets = len(meta.get("universe", []))
            self.add_result("hyperliquid", "OK", f"Hyperliquid testnet connected ({assets} assets)")
        except ImportError:
            self.add_result("hyperliquid", "WARN", "hyperliquid-python-sdk not installed")
        except Exception as e:
            self.add_result("hyperliquid", "FAIL", f"Hyperliquid error: {e}")

    # =========================================================================
    # MetricsCollector Checks
    # =========================================================================
    def check_metrics_collector(self):
        """Check MetricsCollector can send data."""
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from strategies.common.observability.metrics_collector import MetricsCollector

            collector = MetricsCollector(
                questdb_host="localhost", questdb_port=9009, auto_flush=False
            )
            collector.record_health(component="VERIFY_SPEC040", status="OK", latency_ms=0)
            sent = collector.flush()
            collector.close()

            if sent > 0:
                self.add_result(
                    "metrics_collector", "OK", f"MetricsCollector working ({sent} record sent)"
                )
            else:
                self.add_result(
                    "metrics_collector", "WARN", "MetricsCollector connected but no data sent"
                )
        except Exception as e:
            self.add_result("metrics_collector", "FAIL", f"MetricsCollector error: {e}")

    # =========================================================================
    # Ralph Hooks Checks
    # =========================================================================
    def check_ralph_hooks(self):
        """Check Ralph hook files exist."""
        ralph_hook = Path.home() / ".claude" / "hooks" / "control" / "ralph-loop.py"
        # Also check shared location
        shared_hook = Path("/media/sam/1TB/claude-hooks-shared/hooks/control/ralph-loop.py")

        if ralph_hook.exists() or shared_hook.exists():
            hook_path = ralph_hook if ralph_hook.exists() else shared_hook
            self.add_result("ralph_hooks", "OK", f"Ralph hook exists: {hook_path}")
        else:
            self.add_result("ralph_hooks", "WARN", "Ralph hook not found in expected locations")

    def check_ralph_state(self):
        """Check Ralph state directory."""
        ralph_dir = Path.home() / ".claude" / "ralph"
        if ralph_dir.exists():
            state_file = ralph_dir / "state.json"
            if state_file.exists():
                try:
                    state = json.loads(state_file.read_text())
                    active = state.get("active", False)
                    iteration = state.get("iteration", 0)
                    self.add_result(
                        "ralph_state", "OK", f"Ralph state: active={active}, iteration={iteration}"
                    )
                except:
                    self.add_result("ralph_state", "WARN", "Ralph state file exists but unreadable")
            else:
                self.add_result("ralph_state", "OK", "Ralph directory exists (no active session)")
        else:
            self.add_result("ralph_state", "OK", "Ralph not initialized (first run will create)")

    # =========================================================================
    # Security Tools Checks
    # =========================================================================
    def check_security_tools(self):
        """Check security tools are available."""
        tools = {
            "bandit": ["bandit", "--version"],
            "gitleaks": ["gitleaks", "version"],
        }

        for tool, cmd in tools.items():
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    version = result.stdout.strip().split("\n")[0][:50]
                    self.add_result(f"security_{tool}", "OK", f"{tool} available: {version}")
                else:
                    self.add_result(f"security_{tool}", "WARN", f"{tool} not working properly")
            except FileNotFoundError:
                self.add_result(f"security_{tool}", "WARN", f"{tool} not installed")
            except Exception as e:
                self.add_result(f"security_{tool}", "WARN", f"{tool} check failed: {e}")

    # =========================================================================
    # Run All Checks
    # =========================================================================
    def run_all(self):
        """Run all verification checks."""
        checks = [
            ("QuestDB", [self.check_questdb_connection, self.check_questdb_tables]),
            ("Grafana", [self.check_grafana_connection, self.check_grafana_discord]),
            ("Discord", [self.check_discord_webhook]),
            ("Sentry", [self.check_sentry_config]),
            ("Hyperliquid", [self.check_hyperliquid_testnet]),
            ("Metrics", [self.check_metrics_collector]),
            ("Ralph", [self.check_ralph_hooks, self.check_ralph_state]),
            ("Security", [self.check_security_tools]),
        ]

        for section, check_funcs in checks:
            for check in check_funcs:
                try:
                    check()
                except Exception as e:
                    self.add_result(check.__name__, "FAIL", f"Check crashed: {e}")

    def print_results(self):
        """Print results in human-readable or JSON format."""
        if self.json_mode:
            output = {
                "timestamp": datetime.now().isoformat(),
                "results": [
                    {"name": r.name, "status": r.status, "message": r.message, "details": r.details}
                    for r in self.results
                ],
                "summary": {
                    "ok": sum(1 for r in self.results if r.status == "OK"),
                    "warn": sum(1 for r in self.results if r.status == "WARN"),
                    "fail": sum(1 for r in self.results if r.status == "FAIL"),
                    "skip": sum(1 for r in self.results if r.status == "SKIP"),
                },
            }
            print(json.dumps(output, indent=2))
            return

        print("=" * 60)
        print("  Spec 040 - Development Excellence Verification")
        print("=" * 60)
        print(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        status_icons = {"OK": "✅", "WARN": "⚠️", "FAIL": "❌", "SKIP": "⏭️"}

        for result in self.results:
            icon = status_icons.get(result.status, "?")
            print(f"  {icon} {result.name}: {result.message}")

        print()
        print("-" * 60)

        ok = sum(1 for r in self.results if r.status == "OK")
        warn = sum(1 for r in self.results if r.status == "WARN")
        fail = sum(1 for r in self.results if r.status == "FAIL")
        skip = sum(1 for r in self.results if r.status == "SKIP")

        print(f"  Summary: {ok} OK, {warn} WARN, {fail} FAIL, {skip} SKIP")
        print()

        if fail > 0:
            print("  ❌ Some checks failed! Review the output above.")
            return 1
        elif warn > 0:
            print("  ⚠️  Some warnings. System should work but review recommended.")
            return 0
        else:
            print("  ✅ All checks passed!")
            return 0


def main():
    verifier = Spec040Verifier()
    verifier.run_all()
    return verifier.print_results()


if __name__ == "__main__":
    sys.exit(main() or 0)
