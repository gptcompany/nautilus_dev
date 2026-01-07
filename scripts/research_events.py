#!/usr/bin/env python3
"""
Event Sourcing for Academic Research Pipeline.

Source of Truth: DuckDB events table
Auto-Sync: Daemon watches events → updates Neo4j

Robustness Features:
- Exponential backoff retries (3 attempts)
- Dead letter queue for permanently failed events
- Idempotency via event checksums
- Health check file for monitoring
- Graceful shutdown via SIGTERM/SIGINT
- Connection pooling for Neo4j

Usage:
    python research_events.py emit paper_discovered --entity-id "arxiv:1234" --data '{...}'
    python research_events.py daemon
    python research_events.py replay --from-event 100
    python research_events.py health
    python research_events.py dlq --retry    # Retry dead letter queue
"""

import argparse
import hashlib
import json
import signal
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import duckdb

# Configuration
DUCKDB_PATH = Path("/media/sam/1TB/nautilus_dev/data/research.duckdb")
HEALTH_FILE = Path("/tmp/research_events_health.json")
PID_FILE = Path("/tmp/research_events_daemon.pid")
POLL_INTERVAL = 2  # seconds
MAX_RETRIES = 3
BACKOFF_BASE = 2  # exponential: 2, 4, 8 seconds
BATCH_SIZE = 50  # max events per processing cycle

# Neo4j Configuration
NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "research123")

# Global for graceful shutdown
_shutdown_requested = False
_neo4j_driver = None


class EventType(str, Enum):
    """Research pipeline event types."""

    PAPER_DISCOVERED = "paper_discovered"
    PAPER_DOWNLOADED = "paper_downloaded"
    PAPER_PARSED = "paper_parsed"
    FORMULA_EXTRACTED = "formula_extracted"
    FORMULA_VALIDATED = "formula_validated"
    STRATEGY_CREATED = "strategy_created"
    STRATEGY_UPDATED = "strategy_updated"
    SYNC_COMPLETED = "sync_completed"


def init_tables(db: duckdb.DuckDBPyConnection) -> None:
    """Create events and dead_letter_queue tables if not exist."""
    # Main events table
    db.execute("""
        CREATE TABLE IF NOT EXISTS events (
            event_id INTEGER PRIMARY KEY,
            event_type VARCHAR NOT NULL,
            entity_type VARCHAR,
            entity_id VARCHAR,
            data JSON NOT NULL,
            checksum VARCHAR(64),
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            processed_neo4j BOOLEAN DEFAULT FALSE,
            processed_at TIMESTAMPTZ,
            retry_count INTEGER DEFAULT 0
        )
    """)

    # Dead letter queue for permanently failed events
    db.execute("""
        CREATE TABLE IF NOT EXISTS dead_letter_queue (
            dlq_id INTEGER PRIMARY KEY,
            event_id INTEGER NOT NULL,
            event_type VARCHAR NOT NULL,
            entity_id VARCHAR,
            data JSON NOT NULL,
            error_message VARCHAR,
            failed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            retry_count INTEGER DEFAULT 0,
            resolved BOOLEAN DEFAULT FALSE
        )
    """)

    # Create sequences
    db.execute("CREATE SEQUENCE IF NOT EXISTS events_seq START 1")
    db.execute("CREATE SEQUENCE IF NOT EXISTS dlq_seq START 1")

    # Indexes (DuckDB doesn't support partial indexes)
    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_unprocessed
        ON events (processed_neo4j, retry_count)
    """)
    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_events_checksum
        ON events (checksum)
    """)
    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_dlq_unresolved
        ON dead_letter_queue (resolved)
    """)


def compute_checksum(event_type: str, entity_id: str, data: dict) -> str:
    """Compute idempotency checksum for event."""
    content = f"{event_type}:{entity_id}:{json.dumps(data, sort_keys=True)}"
    return hashlib.sha256(content.encode()).hexdigest()


def emit_event(
    event_type: EventType | str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    data: dict[str, Any] | None = None,
    skip_duplicate: bool = True,
) -> int | None:
    """
    Emit an event to the event log.

    Args:
        event_type: Type of event
        entity_type: Optional entity type
        entity_id: Optional entity ID
        data: Event payload
        skip_duplicate: If True, skip if checksum exists (idempotent)

    Returns:
        event_id if created, None if duplicate skipped
    """
    db = duckdb.connect(str(DUCKDB_PATH))
    try:
        init_tables(db)

        event_type_str = (
            event_type.value if isinstance(event_type, EventType) else event_type
        )
        data = data or {}
        data_json = json.dumps(data)
        checksum = compute_checksum(event_type_str, entity_id or "", data)

        # Check for duplicate (idempotency)
        if skip_duplicate:
            existing = db.execute(
                "SELECT event_id FROM events WHERE checksum = ?", [checksum]
            ).fetchone()
            if existing:
                return None  # Duplicate, skip

        result = db.execute(
            """
            INSERT INTO events (event_id, event_type, entity_type, entity_id, data, checksum)
            VALUES (nextval('events_seq'), ?, ?, ?, ?, ?)
            RETURNING event_id
        """,
            [event_type_str, entity_type, entity_id, data_json, checksum],
        ).fetchone()

        return result[0]
    finally:
        db.close()


def get_unprocessed_events(
    db: duckdb.DuckDBPyConnection, limit: int = BATCH_SIZE
) -> list[dict]:
    """Get events not yet synced to Neo4j, respecting retry limits."""
    result = db.execute(
        """
        SELECT event_id, event_type, entity_type, entity_id, data, created_at, retry_count
        FROM events
        WHERE processed_neo4j = FALSE AND retry_count < ?
        ORDER BY event_id ASC
        LIMIT ?
    """,
        [MAX_RETRIES, limit],
    ).fetchall()

    return [
        {
            "event_id": r[0],
            "event_type": r[1],
            "entity_type": r[2],
            "entity_id": r[3],
            "data": json.loads(r[4]) if r[4] else {},
            "created_at": r[5],
            "retry_count": r[6],
        }
        for r in result
    ]


def mark_processed(db: duckdb.DuckDBPyConnection, event_ids: list[int]) -> None:
    """Mark events as successfully processed."""
    if not event_ids:
        return
    placeholders = ",".join(["?" for _ in event_ids])
    db.execute(
        f"""
        UPDATE events
        SET processed_neo4j = TRUE, processed_at = CURRENT_TIMESTAMP
        WHERE event_id IN ({placeholders})
    """,
        event_ids,
    )


def increment_retry(db: duckdb.DuckDBPyConnection, event_id: int) -> int:
    """Increment retry count and return new count."""
    db.execute(
        "UPDATE events SET retry_count = retry_count + 1 WHERE event_id = ?",
        [event_id],
    )
    result = db.execute(
        "SELECT retry_count FROM events WHERE event_id = ?", [event_id]
    ).fetchone()
    return result[0] if result else 0


def move_to_dlq(db: duckdb.DuckDBPyConnection, event: dict, error_message: str) -> None:
    """Move permanently failed event to dead letter queue."""
    db.execute(
        """
        INSERT INTO dead_letter_queue
        (dlq_id, event_id, event_type, entity_id, data, error_message, retry_count)
        VALUES (nextval('dlq_seq'), ?, ?, ?, ?, ?, ?)
    """,
        [
            event["event_id"],
            event["event_type"],
            event["entity_id"],
            json.dumps(event["data"]),
            error_message,
            event["retry_count"],
        ],
    )
    # Mark original as processed to stop retries
    db.execute(
        "UPDATE events SET processed_neo4j = TRUE, processed_at = CURRENT_TIMESTAMP WHERE event_id = ?",
        [event["event_id"]],
    )


def get_neo4j_driver():
    """Get or create Neo4j driver (connection pooling)."""
    global _neo4j_driver
    if _neo4j_driver is None:
        from neo4j import GraphDatabase

        _neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
    return _neo4j_driver


def close_neo4j_driver():
    """Close Neo4j driver on shutdown."""
    global _neo4j_driver
    if _neo4j_driver:
        _neo4j_driver.close()
        _neo4j_driver = None


def sync_event_to_neo4j(event: dict) -> tuple[bool, str]:
    """
    Sync a single event to Neo4j.

    Returns:
        (success, error_message)
    """
    try:
        driver = get_neo4j_driver()

        with driver.session() as session:
            event_type = event["event_type"]
            data = event["data"]
            entity_id = event["entity_id"]

            if event_type == EventType.PAPER_DISCOVERED.value:
                session.run(
                    """
                    MERGE (p:Paper {paper_id: $paper_id})
                    SET p.title = $title,
                        p.arxiv_id = $arxiv_id,
                        p.doi = $doi,
                        p.source = $source,
                        p.discovered_at = datetime(),
                        p.synced_at = datetime()
                """,
                    paper_id=entity_id,
                    title=data.get("title"),
                    arxiv_id=data.get("arxiv_id"),
                    doi=data.get("doi"),
                    source=data.get("source"),
                )

            elif event_type == EventType.PAPER_DOWNLOADED.value:
                session.run(
                    """
                    MERGE (p:Paper {paper_id: $paper_id})
                    SET p.pdf_path = $pdf_path,
                        p.downloaded_at = datetime()
                """,
                    paper_id=entity_id,
                    pdf_path=data.get("pdf_path"),
                )

            elif event_type == EventType.PAPER_PARSED.value:
                session.run(
                    """
                    MERGE (p:Paper {paper_id: $paper_id})
                    SET p.parsed_content_path = $parsed_path,
                        p.parsed_at = datetime()
                """,
                    paper_id=entity_id,
                    parsed_path=data.get("parsed_path"),
                )

            elif event_type == EventType.FORMULA_EXTRACTED.value:
                session.run(
                    """
                    MERGE (f:Formula {formula_id: $formula_id})
                    SET f.latex = $latex,
                        f.description = $description,
                        f.formula_type = $formula_type,
                        f.context = $context,
                        f.synced_at = datetime()
                    WITH f
                    MATCH (p:Paper {paper_id: $paper_id})
                    MERGE (p)-[:CONTAINS]->(f)
                """,
                    formula_id=entity_id,
                    paper_id=data.get("paper_id"),
                    latex=data.get("latex"),
                    description=data.get("description"),
                    formula_type=data.get("formula_type"),
                    context=data.get("context"),
                )

            elif event_type == EventType.FORMULA_VALIDATED.value:
                session.run(
                    """
                    MATCH (f:Formula {formula_id: $formula_id})
                    SET f.validation_status = $validation_status,
                        f.wolfram_verified = $wolfram_verified,
                        f.wolfram_result = $wolfram_result,
                        f.validated_at = datetime()
                """,
                    formula_id=entity_id,
                    validation_status=data.get("validation_status"),
                    wolfram_verified=data.get("wolfram_verified"),
                    wolfram_result=data.get("wolfram_result"),
                )

            elif event_type == EventType.STRATEGY_CREATED.value:
                session.run(
                    """
                    MERGE (s:Strategy {strategy_id: $strategy_id})
                    SET s.name = $name,
                        s.methodology_type = $methodology_type,
                        s.entry_logic = $entry_logic,
                        s.exit_logic = $exit_logic,
                        s.implementation_status = 'not_started',
                        s.synced_at = datetime()
                    WITH s
                    OPTIONAL MATCH (p:Paper {paper_id: $paper_id})
                    FOREACH (_ IN CASE WHEN p IS NOT NULL THEN [1] ELSE [] END |
                        MERGE (s)-[:BASED_ON]->(p)
                    )
                """,
                    strategy_id=entity_id,
                    paper_id=data.get("paper_id"),
                    name=data.get("name"),
                    methodology_type=data.get("methodology_type"),
                    entry_logic=data.get("entry_logic"),
                    exit_logic=data.get("exit_logic"),
                )

            elif event_type == EventType.STRATEGY_UPDATED.value:
                # Whitelist of allowed property names to prevent Cypher injection
                ALLOWED_PROPERTIES = {
                    "name",
                    "methodology_type",
                    "entry_logic",
                    "exit_logic",
                    "position_sizing",
                    "risk_management",
                    "implementation_status",
                    "implementation_path",
                    "sharpe_ratio",
                    "max_drawdown",
                    "win_rate",
                    "profit_factor",
                    "spec_path",
                }
                set_parts = []
                params = {"strategy_id": entity_id}
                for key, value in data.items():
                    # Only allow whitelisted property names (prevent injection)
                    if key in ALLOWED_PROPERTIES:
                        set_parts.append(f"s.{key} = ${key}")
                        params[key] = value
                if set_parts:
                    session.run(
                        f"""
                        MATCH (s:Strategy {{strategy_id: $strategy_id}})
                        SET {", ".join(set_parts)}, s.synced_at = datetime()
                    """,
                        **params,
                    )

        return True, ""

    except Exception as e:
        return False, str(e)


def update_health(
    status: str,
    events_processed: int = 0,
    events_pending: int = 0,
    last_error: str | None = None,
) -> None:
    """Update health file for monitoring."""
    health = {
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "events_processed": events_processed,
        "events_pending": events_pending,
        "last_error": last_error,
        "pid": PID_FILE.read_text().strip() if PID_FILE.exists() else None,
    }
    HEALTH_FILE.write_text(json.dumps(health, indent=2))


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global _shutdown_requested
    print(f"\nReceived signal {signum}, shutting down gracefully...")
    _shutdown_requested = True


def run_daemon() -> None:
    """
    Run the sync daemon with robustness features.

    - Exponential backoff on failures
    - Dead letter queue for permanent failures
    - Health file updates
    - Graceful shutdown
    """
    global _shutdown_requested

    # Set up signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Write PID file
    import os

    PID_FILE.write_text(str(os.getpid()))

    print(f"Starting research event daemon (polling every {POLL_INTERVAL}s)...")
    print(f"DuckDB: {DUCKDB_PATH}")
    print(f"Neo4j: {NEO4J_URI}")
    print(f"Health file: {HEALTH_FILE}")
    print(f"Max retries: {MAX_RETRIES}")
    print("Press Ctrl+C to stop\n")

    db = duckdb.connect(str(DUCKDB_PATH))
    init_tables(db)
    total_processed = 0

    try:
        while not _shutdown_requested:
            events = get_unprocessed_events(db)
            pending_count = len(events)

            if events:
                print(
                    f"[{datetime.now().strftime('%H:%M:%S')}] Processing {len(events)} events..."
                )

                processed_ids = []
                for event in events:
                    if _shutdown_requested:
                        break

                    success, error = sync_event_to_neo4j(event)

                    if success:
                        processed_ids.append(event["event_id"])
                        print(f"  ✓ {event['event_type']}: {event['entity_id']}")
                    else:
                        retry_count = increment_retry(db, event["event_id"])
                        if retry_count >= MAX_RETRIES:
                            move_to_dlq(db, event, error)
                            print(
                                f"  ✗ {event['event_type']}: {event['entity_id']} → DLQ (max retries)"
                            )
                        else:
                            # Exponential backoff
                            backoff = BACKOFF_BASE**retry_count
                            print(
                                f"  ⟳ {event['event_type']}: {event['entity_id']} (retry {retry_count}/{MAX_RETRIES}, backoff {backoff}s)"
                            )
                            time.sleep(backoff)

                if processed_ids:
                    mark_processed(db, processed_ids)
                    total_processed += len(processed_ids)
                    print(
                        f"  Synced {len(processed_ids)}/{len(events)} events to Neo4j\n"
                    )

                update_health(
                    "running", total_processed, pending_count - len(processed_ids)
                )
            else:
                update_health("idle", total_processed, 0)

            time.sleep(POLL_INTERVAL)

    except Exception as e:
        update_health("error", total_processed, 0, str(e))
        raise
    finally:
        close_neo4j_driver()
        db.close()
        if PID_FILE.exists():
            PID_FILE.unlink()
        update_health("stopped", total_processed, 0)
        print(f"\nDaemon stopped. Total events processed: {total_processed}")


def replay_events(from_event: int = 0) -> None:
    """Replay all events from a given event_id."""
    db = duckdb.connect(str(DUCKDB_PATH))
    try:
        db.execute(
            """
            UPDATE events SET processed_neo4j = FALSE, processed_at = NULL, retry_count = 0
            WHERE event_id >= ?
        """,
            [from_event],
        )

        count = db.execute(
            "SELECT COUNT(*) FROM events WHERE event_id >= ?", [from_event]
        ).fetchone()[0]

        print(f"Reset {count} events for replay from event_id {from_event}")
        print("Run 'daemon' to process them")
    finally:
        db.close()


def retry_dlq() -> None:
    """Retry events in dead letter queue."""
    db = duckdb.connect(str(DUCKDB_PATH))
    try:
        init_tables(db)

        result = db.execute("""
            SELECT dlq_id, event_id, event_type, entity_id, data
            FROM dead_letter_queue
            WHERE resolved = FALSE
        """).fetchall()

        if not result:
            print("Dead letter queue is empty")
            return

        print(f"Retrying {len(result)} events from DLQ...")

        for row in result:
            dlq_id, event_id, event_type, entity_id, data = row
            event = {
                "event_id": event_id,
                "event_type": event_type,
                "entity_id": entity_id,
                "data": json.loads(data) if data else {},
                "retry_count": 0,
            }

            success, error = sync_event_to_neo4j(event)
            if success:
                db.execute(
                    "UPDATE dead_letter_queue SET resolved = TRUE WHERE dlq_id = ?",
                    [dlq_id],
                )
                print(f"  ✓ Resolved: {event_type} - {entity_id}")
            else:
                db.execute(
                    "UPDATE dead_letter_queue SET retry_count = retry_count + 1 WHERE dlq_id = ?",
                    [dlq_id],
                )
                print(f"  ✗ Still failing: {event_type} - {entity_id}: {error}")
    finally:
        close_neo4j_driver()
        db.close()


def show_stats() -> None:
    """Show event statistics."""
    db = duckdb.connect(str(DUCKDB_PATH))
    try:
        init_tables(db)

        print("=== Event Log Statistics ===\n")

        total = db.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        processed = db.execute(
            "SELECT COUNT(*) FROM events WHERE processed_neo4j = TRUE"
        ).fetchone()[0]
        pending = db.execute(
            "SELECT COUNT(*) FROM events WHERE processed_neo4j = FALSE AND retry_count < ?",
            [MAX_RETRIES],
        ).fetchone()[0]
        dlq_count = db.execute(
            "SELECT COUNT(*) FROM dead_letter_queue WHERE resolved = FALSE"
        ).fetchone()[0]

        print(f"Total Events:    {total}")
        print(f"  Processed:     {processed}")
        print(f"  Pending:       {pending}")
        print(f"  In DLQ:        {dlq_count}\n")

        print("By Event Type:")
        result = db.execute("""
            SELECT event_type, COUNT(*), SUM(CASE WHEN processed_neo4j THEN 1 ELSE 0 END)
            FROM events GROUP BY event_type ORDER BY COUNT(*) DESC
        """).fetchall()

        for row in result:
            print(f"  {row[0]}: {row[1]} ({row[2]} synced)")

        print("\nRecent Events (last 10):")
        result = db.execute("""
            SELECT event_id, event_type, entity_id, created_at, processed_neo4j, retry_count
            FROM events ORDER BY event_id DESC LIMIT 10
        """).fetchall()

        for row in result:
            status = "✓" if row[4] else f"○ ({row[5]} retries)"
            print(f"  [{row[0]}] {row[1]} - {row[2]} {status}")
    finally:
        db.close()


def show_health() -> None:
    """Show daemon health status."""
    if not HEALTH_FILE.exists():
        print("Daemon has not been started (no health file)")
        return

    health = json.loads(HEALTH_FILE.read_text())
    print("=== Daemon Health ===\n")
    print(f"Status:           {health['status']}")
    print(f"Last Update:      {health['timestamp']}")
    print(f"Events Processed: {health['events_processed']}")
    print(f"Events Pending:   {health['events_pending']}")
    if health.get("last_error"):
        print(f"Last Error:       {health['last_error']}")
    if health.get("pid"):
        print(f"PID:              {health['pid']}")


def main():
    parser = argparse.ArgumentParser(description="Research Event Sourcing System")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # emit command
    emit_parser = subparsers.add_parser("emit", help="Emit an event")
    emit_parser.add_argument("event_type", choices=[e.value for e in EventType])
    emit_parser.add_argument("--entity-type", help="Entity type")
    emit_parser.add_argument("--entity-id", required=True, help="Entity ID")
    emit_parser.add_argument("--data", type=json.loads, default={}, help="JSON data")
    emit_parser.add_argument(
        "--allow-duplicate", action="store_true", help="Skip idempotency check"
    )

    # daemon command
    subparsers.add_parser("daemon", help="Run sync daemon")

    # replay command
    replay_parser = subparsers.add_parser("replay", help="Replay events")
    replay_parser.add_argument(
        "--from-event", type=int, default=0, help="Start from event ID"
    )

    # dlq command
    dlq_parser = subparsers.add_parser("dlq", help="Dead letter queue operations")
    dlq_parser.add_argument("--retry", action="store_true", help="Retry failed events")

    # stats command
    subparsers.add_parser("stats", help="Show event statistics")

    # health command
    subparsers.add_parser("health", help="Show daemon health")

    # init command
    subparsers.add_parser("init", help="Initialize tables")

    args = parser.parse_args()

    if args.command == "emit":
        event_id = emit_event(
            args.event_type,
            entity_type=args.entity_type,
            entity_id=args.entity_id,
            data=args.data,
            skip_duplicate=not args.allow_duplicate,
        )
        if event_id:
            print(f"Event emitted: {event_id}")
        else:
            print("Duplicate event skipped (idempotent)")

    elif args.command == "daemon":
        run_daemon()

    elif args.command == "replay":
        replay_events(args.from_event)

    elif args.command == "dlq":
        if args.retry:
            retry_dlq()
        else:
            db = duckdb.connect(str(DUCKDB_PATH))
            init_tables(db)
            result = db.execute("""
                SELECT dlq_id, event_type, entity_id, error_message, failed_at
                FROM dead_letter_queue WHERE resolved = FALSE
            """).fetchall()
            if result:
                print("Dead Letter Queue:")
                for row in result:
                    print(f"  [{row[0]}] {row[1]} - {row[2]}: {row[3]}")
            else:
                print("Dead letter queue is empty")
            db.close()

    elif args.command == "stats":
        show_stats()

    elif args.command == "health":
        show_health()

    elif args.command == "init":
        db = duckdb.connect(str(DUCKDB_PATH))
        init_tables(db)
        db.close()
        print("Tables initialized (events + dead_letter_queue)")


if __name__ == "__main__":
    main()
