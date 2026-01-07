#!/usr/bin/env python3
"""monitoring/scripts/retention_cleanup.py

T061: Retention policy script for QuestDB tables.

Drops old partitions beyond the retention period to manage storage.
Run via cron or scheduled task (e.g., daily at 3 AM).

Usage:
    python retention_cleanup.py [--dry-run] [--retention-days N]

Example cron entry (daily at 3 AM):
    0 3 * * * /path/to/venv/bin/python /path/to/retention_cleanup.py >> /var/log/questdb-cleanup.log 2>&1
"""

import argparse
import logging
from datetime import datetime, timedelta, timezone

import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Tables to manage retention for
MONITORED_TABLES = [
    "daemon_metrics",
    "exchange_status",
    "pipeline_metrics",
    "trading_metrics",
]

# Default retention period in days
DEFAULT_RETENTION_DAYS = 90


def get_questdb_url() -> str:
    """Get QuestDB HTTP API URL from environment or default."""
    import os

    host = os.getenv("MONITORING_QUESTDB_HOST", "localhost")
    port = os.getenv("MONITORING_QUESTDB_HTTP_PORT", "9000")
    return f"http://{host}:{port}"


def execute_query(client: httpx.Client, query: str) -> dict | None:
    """Execute a SQL query against QuestDB.

    Args:
        client: HTTP client.
        query: SQL query to execute.

    Returns:
        Query result as dict, or None on error.
    """
    try:
        response = client.get("/exec", params={"query": query})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Query failed: {e}")
        return None


def get_partitions(client: httpx.Client, table: str) -> list[dict]:
    """Get list of partitions for a table.

    Args:
        client: HTTP client.
        table: Table name.

    Returns:
        List of partition info dicts.
    """
    query = f"SELECT * FROM table_partitions('{table}')"
    result = execute_query(client, query)

    if not result or "dataset" not in result:
        return []

    # Parse result columns and data
    columns = result.get("columns", [])
    data = result.get("dataset", [])

    partitions = []
    for row in data:
        partition = dict(zip([c["name"] for c in columns], row))
        partitions.append(partition)

    return partitions


def drop_old_partitions(
    client: httpx.Client,
    table: str,
    cutoff_date: datetime,
    dry_run: bool = False,
) -> int:
    """Drop partitions older than cutoff date.

    Args:
        client: HTTP client.
        table: Table name.
        cutoff_date: Drop partitions older than this date.
        dry_run: If True, only log what would be dropped.

    Returns:
        Number of partitions dropped.
    """
    partitions = get_partitions(client, table)
    dropped = 0

    for partition in partitions:
        # Partition name format is typically 'YYYY-MM-DD' for DAY partitioning
        partition_name = partition.get("name", "")
        try:
            # Try to parse partition name as date
            partition_date = datetime.strptime(partition_name, "%Y-%m-%d")
            partition_date = partition_date.replace(tzinfo=timezone.utc)

            if partition_date < cutoff_date:
                if dry_run:
                    logger.info(f"[DRY-RUN] Would drop partition {table}.{partition_name}")
                else:
                    # QuestDB uses ALTER TABLE to drop partitions
                    drop_query = (
                        f"ALTER TABLE {table} DROP PARTITION "
                        f"WHERE timestamp < '{cutoff_date.strftime('%Y-%m-%d')}'"
                    )
                    result = execute_query(client, drop_query)
                    if result is not None:
                        logger.info(f"Dropped partition {table}.{partition_name}")
                        dropped += 1
                    else:
                        logger.error(f"Failed to drop partition {table}.{partition_name}")
        except ValueError:
            # Skip non-date partition names (e.g., default partition)
            continue

    return dropped


def cleanup_table(
    client: httpx.Client,
    table: str,
    retention_days: int,
    dry_run: bool = False,
) -> int:
    """Clean up old data from a single table.

    Args:
        client: HTTP client.
        table: Table name.
        retention_days: Number of days to retain.
        dry_run: If True, only log what would be dropped.

    Returns:
        Number of partitions dropped.
    """
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
    logger.info(f"Cleaning {table}: retention={retention_days}d, cutoff={cutoff_date}")

    return drop_old_partitions(client, table, cutoff_date, dry_run)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="QuestDB retention cleanup script")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only log what would be dropped, don't actually drop",
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=DEFAULT_RETENTION_DAYS,
        help=f"Number of days to retain (default: {DEFAULT_RETENTION_DAYS})",
    )
    parser.add_argument(
        "--tables",
        nargs="+",
        default=MONITORED_TABLES,
        help="Tables to clean up (default: all monitored tables)",
    )
    args = parser.parse_args()

    base_url = get_questdb_url()
    logger.info(f"Connecting to QuestDB at {base_url}")

    total_dropped = 0

    with httpx.Client(base_url=base_url, timeout=30.0) as client:
        for table in args.tables:
            try:
                dropped = cleanup_table(
                    client,
                    table,
                    args.retention_days,
                    args.dry_run,
                )
                total_dropped += dropped
            except Exception as e:
                logger.error(f"Error cleaning {table}: {e}")

    action = "Would drop" if args.dry_run else "Dropped"
    logger.info(f"{action} {total_dropped} partition(s) total")


if __name__ == "__main__":
    main()
