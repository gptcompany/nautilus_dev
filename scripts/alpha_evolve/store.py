"""
SQLite Hall-of-Fame Store for evolved strategies.

Provides persistence for:
- Strategy code with lineage tracking
- Fitness metrics for evaluation results
- Parent selection algorithms (elite/exploit/explore)
- Population management with pruning
"""

import random
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import cast


@dataclass
class FitnessMetrics:
    """Strategy performance measurements."""

    sharpe_ratio: float
    calmar_ratio: float
    max_drawdown: float
    cagr: float
    total_return: float
    trade_count: int | None = None
    win_rate: float | None = None
    # MVP enhancements (2026-01-11)
    psr: float | None = None  # Probabilistic Sharpe Ratio (P1: probability SR > 0)
    net_sharpe: float | None = None  # Transaction cost-adjusted Sharpe (P2: power law)


@dataclass
class Program:
    """Evolved strategy with code, metrics, and lineage."""

    id: str
    code: str
    parent_id: str | None
    generation: int
    experiment: str | None
    metrics: FitnessMetrics | None
    created_at: float


class ProgramStore:
    """
    Persistence layer for evolved strategies.

    Stores strategies with their fitness metrics and lineage information.
    Supports parent selection algorithms and population management.
    """

    def __init__(
        self,
        db_path: Path | str,
        *,
        population_size: int = 500,
        archive_size: int = 50,
    ) -> None:
        """
        Initialize store.

        Args:
            db_path: Path to SQLite database file
            population_size: Maximum population size (triggers pruning)
            archive_size: Number of top performers protected from pruning
        """
        self.db_path = Path(db_path)
        self.population_size = population_size
        self.archive_size = archive_size
        self._init_db()

    def _init_db(self) -> None:
        """Create database schema if not exists."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS programs (
                    id TEXT PRIMARY KEY,
                    code TEXT NOT NULL,
                    parent_id TEXT,
                    generation INTEGER DEFAULT 0,
                    experiment TEXT,
                    sharpe REAL,
                    calmar REAL,
                    max_dd REAL,
                    cagr REAL,
                    total_return REAL,
                    trade_count INTEGER,
                    win_rate REAL,
                    created_at REAL NOT NULL,
                    FOREIGN KEY (parent_id) REFERENCES programs(id)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_calmar ON programs(calmar DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sharpe ON programs(sharpe DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_experiment ON programs(experiment)")

            # MVP schema migration (2026-01-11): Add psr and net_sharpe columns
            self._migrate_add_column(conn, "psr", "REAL")
            self._migrate_add_column(conn, "net_sharpe", "REAL")

            conn.commit()

    def _migrate_add_column(self, conn: sqlite3.Connection, column: str, dtype: str) -> None:
        """Add column to programs table if not exists (safe migration)."""
        cursor = conn.execute("PRAGMA table_info(programs)")
        columns = [row[1] for row in cursor.fetchall()]
        if column not in columns:
            conn.execute(f"ALTER TABLE programs ADD COLUMN {column} {dtype}")

    def insert(
        self,
        code: str,
        metrics: FitnessMetrics | None = None,
        parent_id: str | None = None,
        experiment: str | None = None,
    ) -> str:
        """
        Insert a new strategy.

        Args:
            code: Strategy Python code
            metrics: Performance metrics (None if not yet evaluated)
            parent_id: ID of parent strategy (None for seeds)
            experiment: Experiment name for grouping

        Returns:
            Generated UUID for the strategy
        """
        prog_id = str(uuid.uuid4())
        created_at = time.time()

        # Calculate generation from parent
        generation = 0
        if parent_id:
            parent = self.get(parent_id)
            if parent is None:
                raise ValueError(f"Parent not found: {parent_id}")
            generation = parent.generation + 1

        with sqlite3.connect(self.db_path) as conn:
            if metrics:
                conn.execute(
                    """
                    INSERT INTO programs (
                        id, code, parent_id, generation, experiment,
                        sharpe, calmar, max_dd, cagr, total_return,
                        trade_count, win_rate, psr, net_sharpe, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        prog_id,
                        code,
                        parent_id,
                        generation,
                        experiment,
                        metrics.sharpe_ratio,
                        metrics.calmar_ratio,
                        metrics.max_drawdown,
                        metrics.cagr,
                        metrics.total_return,
                        metrics.trade_count,
                        metrics.win_rate,
                        metrics.psr,
                        metrics.net_sharpe,
                        created_at,
                    ),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO programs (
                        id, code, parent_id, generation, experiment, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (prog_id, code, parent_id, generation, experiment, created_at),
                )
            conn.commit()

        return prog_id

    def update_metrics(self, prog_id: str, metrics: FitnessMetrics) -> None:
        """
        Update metrics for an existing strategy.

        Args:
            prog_id: Strategy ID
            metrics: Performance metrics from evaluation

        Raises:
            KeyError: If strategy not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                UPDATE programs SET
                    sharpe = ?,
                    calmar = ?,
                    max_dd = ?,
                    cagr = ?,
                    total_return = ?,
                    trade_count = ?,
                    win_rate = ?,
                    psr = ?,
                    net_sharpe = ?
                WHERE id = ?
                """,
                (
                    metrics.sharpe_ratio,
                    metrics.calmar_ratio,
                    metrics.max_drawdown,
                    metrics.cagr,
                    metrics.total_return,
                    metrics.trade_count,
                    metrics.win_rate,
                    metrics.psr,
                    metrics.net_sharpe,
                    prog_id,
                ),
            )
            conn.commit()

            if cursor.rowcount == 0:
                raise KeyError(f"Program not found: {prog_id}")

    def get(self, prog_id: str) -> Program | None:
        """
        Get strategy by ID.

        Args:
            prog_id: Strategy ID

        Returns:
            Program if found, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM programs WHERE id = ?", (prog_id,))
            row = cursor.fetchone()
            if row is None:
                return None
            return self._row_to_program(row)

    def top_k(
        self,
        k: int = 10,
        metric: str = "calmar",
        experiment: str | None = None,
    ) -> list[Program]:
        """
        Get top k strategies by fitness metric.

        Args:
            k: Number of strategies to return
            metric: Metric to sort by (calmar, sharpe, cagr)
            experiment: Filter by experiment name (None for all)

        Returns:
            List of top k programs, sorted descending by metric
        """
        metric_column = self._get_metric_column(metric)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if experiment:
                cursor = conn.execute(
                    f"""
                    SELECT * FROM programs
                    WHERE {metric_column} IS NOT NULL AND experiment = ?
                    ORDER BY {metric_column} DESC
                    LIMIT ?
                    """,
                    (experiment, k),
                )
            else:
                cursor = conn.execute(
                    f"""
                    SELECT * FROM programs
                    WHERE {metric_column} IS NOT NULL
                    ORDER BY {metric_column} DESC
                    LIMIT ?
                    """,
                    (k,),
                )
            return [self._row_to_program(row) for row in cursor.fetchall()]

    def sample(
        self,
        strategy: str = "exploit",
        experiment: str | None = None,
    ) -> Program | None:
        """
        Sample a parent strategy for mutation.

        Args:
            strategy: Selection strategy
                - "elite": Random from top 10%
                - "exploit": Fitness-weighted random
                - "explore": Uniform random
            experiment: Filter by experiment name

        Returns:
            Selected program, or None if store is empty
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            if strategy == "elite":
                return self._sample_elite(conn, experiment)
            elif strategy == "explore":
                return self._sample_explore(conn, experiment)
            else:  # exploit
                return self._sample_exploit(conn, experiment)

    def _sample_elite(self, conn: sqlite3.Connection, experiment: str | None) -> Program | None:
        """Sample from top 10% by calmar."""
        # Get count of evaluated programs
        if experiment:
            cursor = conn.execute(
                """
                SELECT COUNT(*) FROM programs
                WHERE calmar IS NOT NULL AND experiment = ?
                """,
                (experiment,),
            )
        else:
            cursor = conn.execute("SELECT COUNT(*) FROM programs WHERE calmar IS NOT NULL")
        count = cursor.fetchone()[0]
        if count == 0:
            return None

        # Top 10%, minimum 1
        elite_size = max(1, int(count * 0.1))

        if experiment:
            cursor = conn.execute(
                """
                SELECT * FROM programs
                WHERE calmar IS NOT NULL AND experiment = ?
                ORDER BY calmar DESC
                LIMIT ?
                """,
                (experiment, elite_size),
            )
        else:
            cursor = conn.execute(
                """
                SELECT * FROM programs
                WHERE calmar IS NOT NULL
                ORDER BY calmar DESC
                LIMIT ?
                """,
                (elite_size,),
            )

        rows = cursor.fetchall()
        if not rows:
            return None
        return self._row_to_program(random.choice(rows))

    def _sample_exploit(self, conn: sqlite3.Connection, experiment: str | None) -> Program | None:
        """Sample with fitness-weighted probability."""
        if experiment:
            cursor = conn.execute(
                """
                SELECT * FROM programs
                WHERE calmar IS NOT NULL AND experiment = ?
                """,
                (experiment,),
            )
        else:
            cursor = conn.execute("SELECT * FROM programs WHERE calmar IS NOT NULL")

        rows = cursor.fetchall()
        if not rows:
            return None

        # Fitness-weighted selection (using calmar, ensuring non-negative weights)
        programs = [self._row_to_program(row) for row in rows]
        weights = [max(0, p.metrics.calmar_ratio) if p.metrics else 0 for p in programs]

        # If all weights are 0, fall back to uniform random
        if sum(weights) == 0:
            return random.choice(programs)

        return random.choices(programs, weights=weights)[0]

    def _sample_explore(self, conn: sqlite3.Connection, experiment: str | None) -> Program | None:
        """Sample uniformly at random."""
        if experiment:
            cursor = conn.execute(
                """
                SELECT * FROM programs
                WHERE experiment = ?
                ORDER BY RANDOM()
                LIMIT 1
                """,
                (experiment,),
            )
        else:
            cursor = conn.execute("SELECT * FROM programs ORDER BY RANDOM() LIMIT 1")

        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_program(row)

    def get_lineage(self, prog_id: str) -> list[Program]:
        """
        Get full lineage chain from strategy to seed.

        Args:
            prog_id: Strategy ID

        Returns:
            List of programs from given ID to root seed
        """
        lineage = []
        current_id: str | None = prog_id

        while current_id:
            program = self.get(current_id)
            if program is None:
                break
            lineage.append(program)
            current_id = program.parent_id

        return lineage

    def count(self, experiment: str | None = None) -> int:
        """
        Count strategies in store.

        Args:
            experiment: Filter by experiment name

        Returns:
            Number of strategies
        """
        with sqlite3.connect(self.db_path) as conn:
            if experiment:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM programs WHERE experiment = ?",
                    (experiment,),
                )
            else:
                cursor = conn.execute("SELECT COUNT(*) FROM programs")
            result = cursor.fetchone()
            return cast(int, result[0]) if result else 0

    def prune(self) -> int:
        """
        Remove excess strategies to maintain population limit.

        Protects top archive_size performers from deletion.

        Returns:
            Number of strategies deleted
        """
        current_count = self.count()
        if current_count <= self.population_size:
            return 0

        # Get IDs to protect (top archive_size by calmar)
        elite = self.top_k(k=self.archive_size, metric="calmar")
        elite_ids = {p.id for p in elite}

        with sqlite3.connect(self.db_path) as conn:
            # Get all non-elite IDs
            cursor = conn.execute("SELECT id FROM programs")
            all_ids = [row[0] for row in cursor.fetchall()]
            candidate_ids = [pid for pid in all_ids if pid not in elite_ids]

            # Calculate excess
            excess = current_count - self.population_size
            to_delete = random.sample(candidate_ids, min(excess, len(candidate_ids)))

            # Delete
            if to_delete:
                placeholders = ",".join("?" * len(to_delete))
                conn.execute(f"DELETE FROM programs WHERE id IN ({placeholders})", to_delete)
                conn.commit()

            return len(to_delete)

    def _get_metric_column(self, metric: str) -> str:
        """Map metric name to column name."""
        mapping = {
            "calmar": "calmar",
            "sharpe": "sharpe",
            "cagr": "cagr",
            "max_dd": "max_dd",
            "total_return": "total_return",
            # MVP metrics (2026-01-11)
            "psr": "psr",
            "net_sharpe": "net_sharpe",
        }
        return mapping.get(metric, "calmar")

    def _row_to_program(self, row: sqlite3.Row) -> Program:
        """Convert database row to Program object."""
        metrics = None
        if row["calmar"] is not None:
            # Handle new columns that may not exist in old DBs
            row_keys = row.keys()
            metrics = FitnessMetrics(
                sharpe_ratio=row["sharpe"],
                calmar_ratio=row["calmar"],
                max_drawdown=row["max_dd"],
                cagr=row["cagr"],
                total_return=row["total_return"],
                trade_count=row["trade_count"],
                win_rate=row["win_rate"],
                psr=row["psr"] if "psr" in row_keys else None,
                net_sharpe=row["net_sharpe"] if "net_sharpe" in row_keys else None,
            )

        return Program(
            id=row["id"],
            code=row["code"],
            parent_id=row["parent_id"],
            generation=row["generation"],
            experiment=row["experiment"],
            metrics=metrics,
            created_at=row["created_at"],
        )
