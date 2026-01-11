#!/usr/bin/env python3
"""
State Snapshot Tool

Captures system state before deployments for rollback capability.
Creates snapshots of positions, configs, and database state.

Usage:
    python scripts/state_snapshot.py                    # Full snapshot
    python scripts/state_snapshot.py --positions       # Positions only
    python scripts/state_snapshot.py --config          # Config only
    python scripts/state_snapshot.py --restore <id>    # Restore from snapshot
"""

import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Snapshot directory
SNAPSHOT_DIR = Path.home() / ".nautilus" / "snapshots"
MAX_SNAPSHOTS = 10  # Keep last N snapshots


def get_snapshot_id() -> str:
    """Generate unique snapshot ID."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def capture_positions() -> dict:
    """Capture current trading positions from Redis cache."""
    positions = {"timestamp": datetime.now().isoformat(), "positions": []}

    try:
        import redis

        r = redis.Redis(host="localhost", port=6379, decode_responses=True)

        # Get all position keys
        for key in r.scan_iter("POSITION:*"):
            data = r.hgetall(key)
            if data:
                positions["positions"].append({"key": key, "data": data})

        print(f"  Captured {len(positions['positions'])} positions")
    except Exception as e:
        print(f"  Warning: Could not capture positions: {e}")

    return positions


def capture_config() -> dict:
    """Capture current configuration files."""
    config = {"timestamp": datetime.now().isoformat(), "files": {}}

    config_files = [
        ".env",
        "pyproject.toml",
        "docker-compose.yml",
        "docker-compose.staging.yml",
        "configs/hyperliquid/trading_node.py",
    ]

    for file_path in config_files:
        full_path = Path(file_path)
        if full_path.exists():
            try:
                # For .env, redact sensitive values
                if file_path == ".env":
                    lines = []
                    for line in full_path.read_text().splitlines():
                        if "=" in line and not line.startswith("#"):
                            key = line.split("=")[0]
                            if any(
                                s in key.upper()
                                for s in ["SECRET", "KEY", "TOKEN", "PASSWORD", "PK"]
                            ):
                                lines.append(f"{key}=<REDACTED>")
                            else:
                                lines.append(line)
                        else:
                            lines.append(line)
                    config["files"][file_path] = "\n".join(lines)
                else:
                    config["files"][file_path] = full_path.read_text()
                print(f"  Captured {file_path}")
            except Exception as e:
                print(f"  Warning: Could not read {file_path}: {e}")

    return config


def capture_git_state() -> dict:
    """Capture current git state."""
    git_state = {"timestamp": datetime.now().isoformat()}

    try:
        # Current commit
        result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
        git_state["commit"] = result.stdout.strip()

        # Current branch
        result = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True)
        git_state["branch"] = result.stdout.strip()

        # Uncommitted changes
        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        git_state["uncommitted"] = (
            result.stdout.strip().split("\n") if result.stdout.strip() else []
        )

        # Recent tags
        result = subprocess.run(
            ["git", "tag", "--sort=-creatordate"], capture_output=True, text=True
        )
        git_state["recent_tags"] = result.stdout.strip().split("\n")[:5]

        print(f"  Git: {git_state['branch']}@{git_state['commit'][:8]}")
    except Exception as e:
        print(f"  Warning: Could not capture git state: {e}")

    return git_state


def capture_db_state() -> dict:
    """Capture QuestDB table schemas and row counts."""
    db_state = {"timestamp": datetime.now().isoformat(), "tables": {}}

    try:
        import requests

        # Get all tables
        resp = requests.get(
            "http://localhost:9000/exec", params={"query": "SHOW TABLES"}, timeout=5
        )
        if resp.status_code == 200:
            data = resp.json()
            tables = [row[0] for row in data.get("dataset", [])]

            for table in tables:
                # Get row count
                count_resp = requests.get(
                    "http://localhost:9000/exec",
                    params={"query": f"SELECT COUNT(*) FROM {table}"},
                    timeout=5,
                )
                if count_resp.status_code == 200:
                    count_data = count_resp.json()
                    count = count_data.get("dataset", [[0]])[0][0]
                    db_state["tables"][table] = {"row_count": count}

            print(f"  Captured {len(db_state['tables'])} tables")
    except Exception as e:
        print(f"  Warning: Could not capture DB state: {e}")

    return db_state


def create_snapshot(
    include_positions: bool = True,
    include_config: bool = True,
    include_git: bool = True,
    include_db: bool = True,
) -> str:
    """Create a full state snapshot."""
    snapshot_id = get_snapshot_id()
    snapshot_path = SNAPSHOT_DIR / snapshot_id

    print(f"\nCreating snapshot: {snapshot_id}")
    snapshot_path.mkdir(parents=True, exist_ok=True)

    snapshot = {
        "id": snapshot_id,
        "created_at": datetime.now().isoformat(),
        "components": [],
    }

    if include_positions:
        print("Capturing positions...")
        positions = capture_positions()
        (snapshot_path / "positions.json").write_text(json.dumps(positions, indent=2))
        snapshot["components"].append("positions")

    if include_config:
        print("Capturing config...")
        config = capture_config()
        (snapshot_path / "config.json").write_text(json.dumps(config, indent=2))
        snapshot["components"].append("config")

    if include_git:
        print("Capturing git state...")
        git_state = capture_git_state()
        (snapshot_path / "git.json").write_text(json.dumps(git_state, indent=2))
        snapshot["components"].append("git")

    if include_db:
        print("Capturing database state...")
        db_state = capture_db_state()
        (snapshot_path / "database.json").write_text(json.dumps(db_state, indent=2))
        snapshot["components"].append("database")

    # Save manifest
    (snapshot_path / "manifest.json").write_text(json.dumps(snapshot, indent=2))

    # Cleanup old snapshots
    cleanup_old_snapshots()

    print(f"\n✅ Snapshot saved: {snapshot_path}")
    return snapshot_id


def cleanup_old_snapshots():
    """Remove old snapshots beyond MAX_SNAPSHOTS."""
    if not SNAPSHOT_DIR.exists():
        return

    snapshots = sorted(SNAPSHOT_DIR.iterdir(), reverse=True)
    for old_snapshot in snapshots[MAX_SNAPSHOTS:]:
        if old_snapshot.is_dir():
            shutil.rmtree(old_snapshot)
            print(f"  Cleaned up old snapshot: {old_snapshot.name}")


def list_snapshots():
    """List available snapshots."""
    if not SNAPSHOT_DIR.exists():
        print("No snapshots found.")
        return

    print("\nAvailable snapshots:")
    for snapshot_dir in sorted(SNAPSHOT_DIR.iterdir(), reverse=True):
        manifest_path = snapshot_dir / "manifest.json"
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text())
            print(
                f"  {manifest['id']} - {manifest['created_at']} [{', '.join(manifest['components'])}]"
            )


def restore_snapshot(snapshot_id: str):
    """Restore from a snapshot (shows instructions, doesn't auto-restore)."""
    snapshot_path = SNAPSHOT_DIR / snapshot_id

    if not snapshot_path.exists():
        print(f"Snapshot not found: {snapshot_id}")
        return

    manifest = json.loads((snapshot_path / "manifest.json").read_text())
    print(f"\nSnapshot: {manifest['id']}")
    print(f"Created: {manifest['created_at']}")
    print(f"Components: {', '.join(manifest['components'])}")

    if "git" in manifest["components"]:
        git_state = json.loads((snapshot_path / "git.json").read_text())
        print("\nTo restore git state:")
        print(f"  git checkout {git_state['commit']}")

    if "config" in manifest["components"]:
        print("\nConfig files backed up in:")
        print(f"  {snapshot_path / 'config.json'}")

    if "positions" in manifest["components"]:
        positions = json.loads((snapshot_path / "positions.json").read_text())
        print(f"\nPositions at snapshot time: {len(positions['positions'])}")

    print("\n⚠️  Manual review required before restoration.")


def main():
    if len(sys.argv) < 2:
        # Full snapshot
        create_snapshot()
    elif sys.argv[1] == "--positions":
        create_snapshot(include_config=False, include_git=False, include_db=False)
    elif sys.argv[1] == "--config":
        create_snapshot(include_positions=False, include_git=False, include_db=False)
    elif sys.argv[1] == "--list":
        list_snapshots()
    elif sys.argv[1] == "--restore" and len(sys.argv) > 2:
        restore_snapshot(sys.argv[2])
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
