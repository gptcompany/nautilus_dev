#!/usr/bin/env python3
"""
Research Versioning Service - Event log history and deduplication.

Uses DuckDB events table as source of truth for version history.

Usage:
    # Get entity history
    python research_versioning.py history paper arxiv:1234

    # Get entity state at a point in time
    python research_versioning.py state paper arxiv:1234 --at 2024-01-01

    # Check for duplicates before adding
    python research_versioning.py dedup --arxiv 1234.5678 --doi 10.1234/abc

    # Show version statistics
    python research_versioning.py stats
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import duckdb

# Configuration
DUCKDB_PATH = Path("/media/sam/1TB/nautilus_dev/data/research.duckdb")


def get_entity_history(entity_type: str, entity_id: str) -> list[dict[str, Any]]:
    """
    Get version history for an entity from event log.

    Returns list of events that modified this entity, in chronological order.
    """
    db = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    try:
        result = db.execute(
            """
            SELECT event_id, event_type, data, created_at, processed_neo4j
            FROM events
            WHERE entity_id = ?
            ORDER BY event_id ASC
        """,
            [entity_id],
        ).fetchall()

        history = []
        for event_id, event_type, data, created_at, processed in result:
            # Handle timestamp conversion safely
            timestamp = None
            if created_at is not None:
                try:
                    timestamp = created_at.isoformat()
                except AttributeError:
                    timestamp = str(created_at)
            history.append(
                {
                    "version": event_id,
                    "event_type": event_type,
                    "data": json.loads(data) if data else {},
                    "timestamp": timestamp,
                    "synced": processed,
                }
            )

        return history
    finally:
        db.close()


def get_entity_state_at(
    entity_type: str, entity_id: str, at_time: datetime | None = None
) -> dict[str, Any]:
    """
    Reconstruct entity state at a given point in time by replaying events.

    If at_time is None, returns current state.
    """
    db = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    try:
        query = """
            SELECT event_type, data, created_at
            FROM events
            WHERE entity_id = ?
        """
        params = [entity_id]

        if at_time:
            query += " AND created_at <= ?"
            params.append(at_time)

        query += " ORDER BY event_id ASC"

        result = db.execute(query, params).fetchall()

        if not result:
            return {}

        # Replay events to reconstruct state
        state = {"entity_id": entity_id}

        for event_type, data, created_at in result:
            data_dict = json.loads(data) if data else {}

            if event_type.endswith("_discovered") or event_type.endswith("_created"):
                # Initial creation - set all fields
                state.update(data_dict)
                state["created_at"] = created_at.isoformat() if created_at else None
            else:
                # Update - merge fields
                state.update(data_dict)

            state["last_modified"] = created_at.isoformat() if created_at else None
            state["last_event"] = event_type

        return state
    finally:
        db.close()


def get_version_diff(entity_id: str, version1: int, version2: int) -> dict[str, Any]:
    """
    Get diff between two versions of an entity.
    """
    db = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    try:
        v1 = db.execute(
            "SELECT data FROM events WHERE entity_id = ? AND event_id = ?",
            [entity_id, version1],
        ).fetchone()

        v2 = db.execute(
            "SELECT data FROM events WHERE entity_id = ? AND event_id = ?",
            [entity_id, version2],
        ).fetchone()

        if not v1 or not v2:
            return {"error": "Version not found"}

        data1 = json.loads(v1[0]) if v1[0] else {}
        data2 = json.loads(v2[0]) if v2[0] else {}

        # Calculate diff
        added = {k: v for k, v in data2.items() if k not in data1}
        removed = {k: v for k, v in data1.items() if k not in data2}
        changed = {
            k: {"from": data1[k], "to": data2[k]}
            for k in data1.keys() & data2.keys()
            if data1[k] != data2[k]
        }

        return {
            "version1": version1,
            "version2": version2,
            "added": added,
            "removed": removed,
            "changed": changed,
        }
    finally:
        db.close()


def check_duplicate(
    arxiv_id: str | None = None, doi: str | None = None, title: str | None = None
) -> dict[str, Any]:
    """
    Check if a paper already exists in the database.

    Returns matching papers if found.
    """
    db = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    try:
        duplicates = []

        # Check by arXiv ID
        if arxiv_id:
            result = db.execute(
                """
                SELECT paper_id, title, arxiv_id, doi
                FROM papers
                WHERE arxiv_id = ? OR paper_id LIKE ?
            """,
                [arxiv_id, f"%{arxiv_id}%"],
            ).fetchall()
            for r in result:
                duplicates.append(
                    {
                        "paper_id": r[0],
                        "title": r[1],
                        "arxiv_id": r[2],
                        "doi": r[3],
                        "match_type": "arxiv_id",
                    }
                )

        # Check by DOI
        if doi:
            result = db.execute(
                """
                SELECT paper_id, title, arxiv_id, doi
                FROM papers
                WHERE doi = ?
            """,
                [doi],
            ).fetchall()
            for r in result:
                if r[0] not in [d["paper_id"] for d in duplicates]:
                    duplicates.append(
                        {
                            "paper_id": r[0],
                            "title": r[1],
                            "arxiv_id": r[2],
                            "doi": r[3],
                            "match_type": "doi",
                        }
                    )

        # Check by title similarity (exact match)
        if title:
            result = db.execute(
                """
                SELECT paper_id, title, arxiv_id, doi
                FROM papers
                WHERE title = ? OR title ILIKE ?
            """,
                [title, f"%{title}%"],
            ).fetchall()
            for r in result:
                if r[0] not in [d["paper_id"] for d in duplicates]:
                    duplicates.append(
                        {
                            "paper_id": r[0],
                            "title": r[1],
                            "arxiv_id": r[2],
                            "doi": r[3],
                            "match_type": "title",
                        }
                    )

        return {
            "is_duplicate": len(duplicates) > 0,
            "matches": duplicates,
            "checked": {
                "arxiv_id": arxiv_id,
                "doi": doi,
                "title": title,
            },
        }
    finally:
        db.close()


def get_version_stats() -> dict[str, Any]:
    """Get versioning statistics from event log."""
    db = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    try:
        # Total events
        total_events = db.execute("SELECT COUNT(*) FROM events").fetchone()[0]

        # Unique entities
        unique_entities = db.execute(
            "SELECT COUNT(DISTINCT entity_id) FROM events WHERE entity_id IS NOT NULL"
        ).fetchone()[0]

        # Events per entity type
        events_by_type = db.execute(
            """
            SELECT event_type, COUNT(*) as count
            FROM events
            GROUP BY event_type
            ORDER BY count DESC
        """
        ).fetchall()

        # Most modified entities
        most_modified = db.execute(
            """
            SELECT entity_id, COUNT(*) as version_count
            FROM events
            WHERE entity_id IS NOT NULL
            GROUP BY entity_id
            HAVING COUNT(*) > 1
            ORDER BY version_count DESC
            LIMIT 10
        """
        ).fetchall()

        # Event timeline
        timeline = db.execute(
            """
            SELECT DATE(created_at) as date, COUNT(*) as events
            FROM events
            WHERE created_at IS NOT NULL
            GROUP BY DATE(created_at)
            ORDER BY date DESC
            LIMIT 30
        """
        ).fetchall()

        return {
            "total_events": total_events,
            "unique_entities": unique_entities,
            "events_by_type": {r[0]: r[1] for r in events_by_type},
            "most_modified": [
                {"entity_id": r[0], "version_count": r[1]} for r in most_modified
            ],
            "timeline": [{"date": str(r[0]), "events": r[1]} for r in timeline],
        }
    finally:
        db.close()


def list_entity_versions(entity_id: str) -> None:
    """Print version history for an entity."""
    history = get_entity_history("any", entity_id)

    if not history:
        print(f"No history found for entity: {entity_id}")
        return

    print(f"\n=== Version History: {entity_id} ===\n")
    print(f"Total versions: {len(history)}\n")

    for v in history:
        synced = "✓" if v["synced"] else "○"
        print(f"[{synced}] v{v['version']} - {v['event_type']}")
        print(f"    Time: {v['timestamp']}")
        if v["data"]:
            for key, val in list(v["data"].items())[:3]:
                val_str = str(val)[:50] + "..." if len(str(val)) > 50 else str(val)
                print(f"    {key}: {val_str}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Research Versioning Service")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # history command
    history_parser = subparsers.add_parser("history", help="Get entity history")
    history_parser.add_argument(
        "entity_type", help="Entity type (paper, formula, strategy)"
    )
    history_parser.add_argument("entity_id", help="Entity ID")

    # state command
    state_parser = subparsers.add_parser("state", help="Get entity state at time")
    state_parser.add_argument("entity_type", help="Entity type")
    state_parser.add_argument("entity_id", help="Entity ID")
    state_parser.add_argument("--at", help="Timestamp (YYYY-MM-DD or ISO format)")

    # diff command
    diff_parser = subparsers.add_parser("diff", help="Diff between versions")
    diff_parser.add_argument("entity_id", help="Entity ID")
    diff_parser.add_argument("version1", type=int, help="First version (event_id)")
    diff_parser.add_argument("version2", type=int, help="Second version (event_id)")

    # dedup command
    dedup_parser = subparsers.add_parser("dedup", help="Check for duplicates")
    dedup_parser.add_argument("--arxiv", help="arXiv ID")
    dedup_parser.add_argument("--doi", help="DOI")
    dedup_parser.add_argument("--title", help="Paper title")

    # stats command
    subparsers.add_parser("stats", help="Show version statistics")

    args = parser.parse_args()

    if args.command == "history":
        list_entity_versions(args.entity_id)

    elif args.command == "state":
        at_time = None
        if args.at:
            try:
                at_time = datetime.fromisoformat(args.at)
            except ValueError:
                at_time = datetime.strptime(args.at, "%Y-%m-%d")

        state = get_entity_state_at(args.entity_type, args.entity_id, at_time)
        if state:
            print(json.dumps(state, indent=2, default=str))
        else:
            print(f"No state found for {args.entity_id}")

    elif args.command == "diff":
        diff = get_version_diff(args.entity_id, args.version1, args.version2)
        print(json.dumps(diff, indent=2, default=str))

    elif args.command == "dedup":
        if not any([args.arxiv, args.doi, args.title]):
            print("Error: Provide at least one of --arxiv, --doi, or --title")
            return

        result = check_duplicate(args.arxiv, args.doi, args.title)
        if result["is_duplicate"]:
            print("⚠️ DUPLICATE FOUND!\n")
            for match in result["matches"]:
                print(f"  Paper ID: {match['paper_id']}")
                print(f"  Title: {match['title']}")
                print(f"  Match Type: {match['match_type']}")
                print()
        else:
            print("✓ No duplicates found")

    elif args.command == "stats":
        stats = get_version_stats()
        print("\n=== Versioning Statistics ===\n")
        print(f"Total Events:     {stats['total_events']}")
        print(f"Unique Entities:  {stats['unique_entities']}")
        print("\nEvents by Type:")
        for event_type, count in stats["events_by_type"].items():
            print(f"  {event_type}: {count}")

        if stats["most_modified"]:
            print("\nMost Modified Entities:")
            for e in stats["most_modified"][:5]:
                print(f"  {e['entity_id']}: {e['version_count']} versions")

        if stats["timeline"]:
            print("\nRecent Activity:")
            for t in stats["timeline"][:7]:
                print(f"  {t['date']}: {t['events']} events")


if __name__ == "__main__":
    main()
