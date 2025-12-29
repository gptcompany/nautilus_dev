#!/usr/bin/env python3
"""
Sync strategy entities from academic_research to nautilus_dev.

This script extracts strategy__ entities from the academic_research memory.json
and syncs them to nautilus_dev/docs/research/strategies.json.

Features:
- Entity extraction with strategy__ prefix filter
- Staleness detection via timestamp comparison
- JSON output with sync metadata
- Dry-run mode for testing

Usage:
    python scripts/sync_research.py              # Normal sync
    python scripts/sync_research.py --dry-run    # Preview changes
    python scripts/sync_research.py --force      # Force sync even if fresh
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# Configuration
CONFIG = {
    "source": Path("/media/sam/1TB/academic_research/memory.json"),
    "target": Path("/media/sam/1TB/nautilus_dev/docs/research/strategies.json"),
    "entity_prefix": "strategy__",
    "stale_threshold_hours": 24,
}


def load_memory(path: Path) -> dict[str, Any]:
    """Load memory.json from academic_research."""
    if not path.exists():
        print(f"ERROR: Source file not found: {path}")
        sys.exit(1)

    try:
        with open(path) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {path}: {e}")
        sys.exit(1)


def extract_strategies(memory: dict[str, Any], prefix: str) -> list[dict[str, Any]]:
    """Extract entities with the specified prefix."""
    entities = memory.get("entities", [])

    # Validate entities is a list
    if not isinstance(entities, list):
        print(
            f"WARNING: 'entities' is not a list (got {type(entities).__name__}), skipping"
        )
        return []

    strategies = []
    for entity in entities:
        # Skip non-dict entities
        if not isinstance(entity, dict):
            continue
        # Get id and ensure it's a string
        entity_id = entity.get("id", "")
        if not isinstance(entity_id, str):
            continue
        if entity_id.startswith(prefix):
            strategies.append(entity)

    return strategies


def load_existing_sync(path: Path) -> dict[str, Any] | None:
    """Load existing sync file if it exists."""
    try:
        if not path.exists():
            return None
    except PermissionError:
        print(f"WARNING: Cannot access {path}, treating as non-existent")
        return None

    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, PermissionError, OSError):
        return None


def is_stale(existing: dict[str, Any] | None, threshold_hours: int) -> bool:
    """Check if existing sync is stale based on timestamp."""
    if existing is None:
        return True

    synced_at = existing.get("synced_at")
    if not synced_at:
        return True

    try:
        sync_time = datetime.fromisoformat(synced_at.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        age_hours = (now - sync_time).total_seconds() / 3600
        return age_hours > threshold_hours
    except (ValueError, TypeError):
        return True


def create_sync_output(
    strategies: list[dict[str, Any]],
    source_path: Path,
) -> dict[str, Any]:
    """Create the sync output structure."""
    return {
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "source": str(source_path),
        "count": len(strategies),
        "strategies": strategies,
    }


def write_sync_output(output: dict[str, Any], path: Path) -> bool:
    """Write sync output to target path. Returns True on success."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except (PermissionError, OSError) as e:
        print(f"ERROR: Cannot create directory {path.parent}: {e}")
        return False

    try:
        with open(path, "w") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        return True
    except (PermissionError, OSError) as e:
        print(f"ERROR: Cannot write to {path}: {e}")
        return False


def print_strategy_summary(strategies: list[dict[str, Any]]) -> None:
    """Print summary of strategies."""
    if not strategies:
        print("No strategy__ entities found.")
        return

    print(f"\nFound {len(strategies)} strategy__ entities:")
    for s in strategies:
        entity_id = s.get("id", "unknown")
        name = s.get("name", "Unnamed")
        print(f"  - {entity_id}: {name}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync strategy entities from academic_research to nautilus_dev"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force sync even if not stale",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=CONFIG["source"],
        help="Source memory.json path",
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=CONFIG["target"],
        help="Target strategies.json path",
    )

    args = parser.parse_args()

    print("=== Research Sync ===")
    print(f"Source: {args.source}")
    print(f"Target: {args.target}")

    # Load existing sync
    existing = load_existing_sync(args.target)

    # Check staleness
    stale = is_stale(existing, CONFIG["stale_threshold_hours"])

    if existing:
        synced_at = existing.get("synced_at", "unknown")
        count = existing.get("count", 0)
        print(f"\nExisting sync: {synced_at} ({count} strategies)")
        print(f"Stale: {stale}")

    if not stale and not args.force:
        print("\nSync is fresh, skipping. Use --force to override.")
        return

    # Load memory and extract strategies
    print("\nLoading memory.json...")
    memory = load_memory(args.source)

    strategies = extract_strategies(memory, CONFIG["entity_prefix"])
    print_strategy_summary(strategies)

    # Create output
    output = create_sync_output(strategies, args.source)

    if args.dry_run:
        print("\n[DRY RUN] Would write:")
        print(json.dumps(output, indent=2)[:500] + "...")
        return

    # Write output
    print(f"\nWriting to {args.target}...")
    if write_sync_output(output, args.target):
        print(f"Synced {len(strategies)} strategies successfully!")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
