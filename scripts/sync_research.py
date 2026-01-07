#!/usr/bin/env python3
"""
Sync research entities from academic_research to nautilus_dev.

This script extracts strategy__ and formula__ entities from the academic_research
memory.json and syncs them to nautilus_dev/docs/research/.

Synced entity types:
- strategy__  → strategies.json  (trading strategies from papers)
- formula__   → formulas.json    (mathematical formulas extracted from papers)

Features:
- Multi-entity type support
- Entity extraction with prefix filter
- Staleness detection via timestamp comparison
- JSON output with sync metadata
- Dry-run mode for testing

Usage:
    python scripts/sync_research.py              # Normal sync (all types)
    python scripts/sync_research.py --dry-run    # Preview changes
    python scripts/sync_research.py --force      # Force sync even if fresh
    python scripts/sync_research.py --type strategy  # Sync only strategies
    python scripts/sync_research.py --type formula   # Sync only formulas
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

# Configuration
CONFIG = {
    "source": Path("/media/sam/1TB1/academic_research/memory.json"),
    "target_dir": Path("/media/sam/1TB/nautilus_dev/docs/research"),
    "stale_threshold_hours": 24,
}

# Entity types to sync
ENTITY_TYPES = {
    "strategy": {
        "prefix": "strategy__",
        "target_file": "strategies.json",
        "description": "Trading strategies from academic papers",
    },
    "formula": {
        "prefix": "formula__",
        "target_file": "formulas.json",
        "description": "Mathematical formulas extracted from papers",
    },
}


def load_memory(path: Path) -> dict[str, Any]:
    """Load memory.json from academic_research."""
    if not path.exists():
        print(f"ERROR: Source file not found: {path}")
        sys.exit(1)

    try:
        with open(path) as f:
            data = json.load(f)
            return cast(dict[str, Any], data)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {path}: {e}")
        sys.exit(1)


def extract_strategies(memory: dict[str, Any], prefix: str) -> list[dict[str, Any]]:
    """Extract entities with the specified prefix."""
    entities = memory.get("entities", [])

    # Validate entities is a list
    if not isinstance(entities, list):
        print(f"WARNING: 'entities' is not a list (got {type(entities).__name__}), skipping")
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
            data = json.load(f)
            return cast(dict[str, Any], data)
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
        now = datetime.now(UTC)
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
        "synced_at": datetime.now(UTC).isoformat(),
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


def print_entity_summary(entities: list[dict[str, Any]], entity_type: str) -> None:
    """Print summary of entities."""
    prefix = ENTITY_TYPES[entity_type]["prefix"]
    if not entities:
        print(f"No {prefix} entities found.")
        return

    print(f"\nFound {len(entities)} {prefix} entities:")
    for e in entities[:10]:  # Show max 10
        entity_id = e.get("id", "unknown")
        name = e.get("name", "Unnamed")
        print(f"  - {entity_id}: {name}")
    if len(entities) > 10:
        print(f"  ... and {len(entities) - 10} more")


def sync_entity_type(
    entity_type: str,
    memory: dict[str, Any],
    target_dir: Path,
    force: bool,
    dry_run: bool,
) -> bool:
    """Sync a specific entity type. Returns True on success."""
    type_config = ENTITY_TYPES[entity_type]
    prefix = type_config["prefix"]
    target_file = target_dir / type_config["target_file"]

    print(f"\n--- Syncing {entity_type} ({prefix}) ---")

    # Load existing sync
    existing = load_existing_sync(target_file)

    # Check staleness
    threshold_hours = cast(int, CONFIG["stale_threshold_hours"])
    stale = is_stale(existing, threshold_hours)

    if existing:
        synced_at = existing.get("synced_at", "unknown")
        count = existing.get("count", 0)
        print(f"Existing: {synced_at} ({count} entities)")

    if not stale and not force:
        print("Fresh, skipping. Use --force to override.")
        return True

    # Extract entities
    entities = extract_strategies(memory, prefix)
    print_entity_summary(entities, entity_type)

    # Create output
    source_path = cast(Path, CONFIG["source"])
    output = create_sync_output(entities, source_path)

    if dry_run:
        print(f"[DRY RUN] Would write {len(entities)} to {target_file}")
        return True

    # Write output
    if write_sync_output(output, target_file):
        print(f"Synced {len(entities)} {prefix} entities!")
        return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync research entities from academic_research to nautilus_dev"
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
        "--type",
        choices=list(ENTITY_TYPES.keys()),
        help="Sync only specific entity type (default: all)",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=CONFIG["source"],
        help="Source memory.json path",
    )

    args = parser.parse_args()

    print("=== Research Sync ===")
    print(f"Source: {args.source}")
    print(f"Target dir: {CONFIG['target_dir']}")

    # Determine which types to sync
    types_to_sync = [args.type] if args.type else list(ENTITY_TYPES.keys())
    print(f"Entity types: {', '.join(types_to_sync)}")

    # Load memory once
    print("\nLoading memory.json...")
    memory = load_memory(args.source)

    # Sync each entity type
    success = True
    target_dir = cast(Path, CONFIG["target_dir"])
    for entity_type in types_to_sync:
        if not sync_entity_type(
            entity_type=entity_type,
            memory=memory,
            target_dir=target_dir,
            force=args.force,
            dry_run=args.dry_run,
        ):
            success = False

    if not success:
        sys.exit(1)

    print("\n=== Sync Complete ===")


if __name__ == "__main__":
    main()
