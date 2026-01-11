#!/usr/bin/env python3
"""
Research Query Router - Unified API for Neo4j and DuckDB.

Routes queries to the appropriate database:
- Graph queries (relationships, paths, traversal) → Neo4j
- Analytics queries (aggregations, statistics) → DuckDB

Usage:
    from scripts.research_query import ResearchQuery

    rq = ResearchQuery()

    # Graph queries (auto-routes to Neo4j)
    papers = rq.get_papers_by_formula("kelly criterion")
    chain = rq.get_citation_chain("arxiv:1234")
    related = rq.get_related_strategies("momentum")

    # Analytics queries (auto-routes to DuckDB)
    stats = rq.get_strategy_stats()
    top = rq.get_top_strategies(min_sharpe=1.5)
    trends = rq.get_paper_trends_by_year()

    # Direct queries (specify engine)
    result = rq.query(engine="neo4j", query="MATCH (p:Paper) RETURN p LIMIT 10")
    result = rq.query(engine="duckdb", query="SELECT * FROM papers LIMIT 10")
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb

# Configuration - SECURITY: Credentials from environment
DUCKDB_PATH = Path("/media/sam/1TB/nautilus_dev/data/research.duckdb")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
_neo4j_user = os.getenv("NEO4J_USER", "neo4j")
_neo4j_password = os.getenv("NEO4J_PASSWORD")
if not _neo4j_password:
    raise ValueError("NEO4J_PASSWORD environment variable required")
NEO4J_AUTH = (_neo4j_user, _neo4j_password)


@dataclass
class QueryResult:
    """Unified query result."""

    engine: str
    data: list[dict]
    columns: list[str] | None = None
    query: str | None = None
    error: str | None = None

    @property
    def success(self) -> bool:
        return self.error is None

    def __len__(self) -> int:
        return len(self.data)

    def __iter__(self):
        return iter(self.data)


class ResearchQuery:
    """
    Unified query interface for research data.

    Automatically routes to appropriate database:
    - Neo4j: Graph traversals, relationships, paths
    - DuckDB: Analytics, aggregations, filtering
    """

    def __init__(self):
        self._neo4j_driver = None
        self._duckdb_conn = None

    def _get_neo4j(self):
        """Lazy load Neo4j driver."""
        if self._neo4j_driver is None:
            from neo4j import GraphDatabase

            self._neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
        return self._neo4j_driver

    def _get_duckdb(self):
        """Lazy load DuckDB connection."""
        if self._duckdb_conn is None:
            self._duckdb_conn = duckdb.connect(str(DUCKDB_PATH), read_only=True)
        return self._duckdb_conn

    def close(self):
        """Close all connections."""
        if self._neo4j_driver:
            self._neo4j_driver.close()
            self._neo4j_driver = None
        if self._duckdb_conn:
            self._duckdb_conn.close()
            self._duckdb_conn = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    # =====================
    # Direct Query Methods
    # =====================

    def query(self, engine: str, query: str, params: dict | list | None = None) -> QueryResult:
        """
        Execute a direct query on specified engine.

        Args:
            engine: 'neo4j' or 'duckdb'
            query: Cypher (Neo4j) or SQL (DuckDB) query
            params: Query parameters (dict for Neo4j, list for DuckDB)
        """
        if engine == "neo4j":
            neo4j_params = params if isinstance(params, dict) else {}
            return self._query_neo4j(query, neo4j_params)
        elif engine == "duckdb":
            # Accept list or tuple for DuckDB params
            if isinstance(params, (list, tuple)):
                duckdb_params = list(params)
            else:
                duckdb_params = []
            return self._query_duckdb(query, duckdb_params)
        else:
            return QueryResult(engine=engine, data=[], error=f"Unknown engine: {engine}")

    def _query_neo4j(self, query: str, params: dict | None = None) -> QueryResult:
        """Execute Cypher query."""
        try:
            driver = self._get_neo4j()
            with driver.session() as session:
                result = session.run(query, params or {})
                data = [dict(record) for record in result]
                return QueryResult(engine="neo4j", data=data, query=query)
        except Exception as e:
            return QueryResult(engine="neo4j", data=[], error=str(e), query=query)

    def _query_duckdb(self, query: str, params: list | None = None) -> QueryResult:
        """Execute SQL query."""
        try:
            conn = self._get_duckdb()
            result = conn.execute(query, params or [])
            columns = [desc[0] for desc in result.description] if result.description else []
            rows = result.fetchall()
            from typing import cast

            data = [dict(zip(columns, cast(tuple, row), strict=True)) for row in rows]
            return QueryResult(engine="duckdb", data=data, columns=columns, query=query)
        except Exception as e:
            return QueryResult(engine="duckdb", data=[], error=str(e), query=query)

    # =====================
    # Graph Queries (Neo4j)
    # =====================

    def get_papers_by_formula(self, formula_keyword: str) -> QueryResult:
        """Find papers containing a specific formula."""
        return self._query_neo4j(
            """
            MATCH (p:Paper)-[:CONTAINS]->(f:Formula)
            WHERE f.latex CONTAINS $keyword OR f.description CONTAINS $keyword
            RETURN p.paper_id AS paper_id, p.title AS title, f.latex AS formula
            """,
            {"keyword": formula_keyword},
        )

    def get_citation_chain(self, paper_id: str, depth: int = 3) -> QueryResult:
        """Get citation chain for a paper (papers that cite this one and vice versa)."""
        # Note: Cypher path patterns require literal integers for variable length,
        # so we must sanitize and interpolate depth directly (validated as int)
        if not isinstance(depth, int) or depth < 1 or depth > 10:
            depth = 3  # Safe default, prevent injection
        return self._query_neo4j(
            f"""
            MATCH path = (p:Paper {{paper_id: $paper_id}})-[:CITES*1..{depth}]-(related:Paper)
            RETURN DISTINCT related.paper_id AS paper_id, related.title AS title,
                   length(path) AS distance
            ORDER BY distance
            """,
            {"paper_id": paper_id},
        )

    def get_related_strategies(self, methodology: str) -> QueryResult:
        """Find strategies with similar methodology."""
        return self._query_neo4j(
            """
            MATCH (s:Strategy)
            WHERE s.methodology_type CONTAINS $methodology
            OPTIONAL MATCH (s)-[:BASED_ON]->(p:Paper)
            RETURN s.strategy_id AS strategy_id, s.name AS name,
                   s.methodology_type AS methodology, p.title AS source_paper
            """,
            {"methodology": methodology},
        )

    def get_strategy_with_formulas(self, strategy_id: str) -> QueryResult:
        """Get strategy with all its formulas."""
        return self._query_neo4j(
            """
            MATCH (s:Strategy {strategy_id: $strategy_id})
            OPTIONAL MATCH (s)-[:USES]->(f:Formula)
            OPTIONAL MATCH (s)-[:BASED_ON]->(p:Paper)
            RETURN s.strategy_id AS strategy_id, s.name AS name,
                   s.entry_logic AS entry_logic, s.exit_logic AS exit_logic,
                   collect(DISTINCT f.latex) AS formulas,
                   p.title AS source_paper
            """,
            {"strategy_id": strategy_id},
        )

    def get_papers_by_concept(self, concept: str) -> QueryResult:
        """Find papers related to a concept."""
        return self._query_neo4j(
            """
            MATCH (p:Paper)
            WHERE p.title CONTAINS $concept OR p.abstract CONTAINS $concept
            OPTIONAL MATCH (p)-[:CONTAINS]->(f:Formula)
            RETURN p.paper_id AS paper_id, p.title AS title,
                   count(f) AS formula_count
            ORDER BY formula_count DESC
            """,
            {"concept": concept},
        )

    def get_formula_usage(self, formula_id: str) -> QueryResult:
        """Find all papers and strategies using a formula."""
        return self._query_neo4j(
            """
            MATCH (f:Formula {formula_id: $formula_id})
            OPTIONAL MATCH (p:Paper)-[:CONTAINS]->(f)
            OPTIONAL MATCH (s:Strategy)-[:USES]->(f)
            RETURN f.latex AS formula,
                   collect(DISTINCT p.title) AS papers,
                   collect(DISTINCT s.name) AS strategies
            """,
            {"formula_id": formula_id},
        )

    # ========================
    # Analytics Queries (DuckDB)
    # ========================

    def get_strategy_stats(self) -> QueryResult:
        """Get aggregate statistics for all strategies."""
        return self._query_duckdb("""
            SELECT
                COUNT(DISTINCT s.strategy_id) AS total_strategies,
                COUNT(DISTINCT s.methodology_type) AS methodology_types,
                AVG(b.sharpe_ratio) AS avg_sharpe,
                MAX(b.sharpe_ratio) AS max_sharpe,
                AVG(b.max_drawdown) AS avg_max_drawdown,
                AVG(b.win_rate) AS avg_win_rate
            FROM strategies s
            LEFT JOIN backtests b ON s.strategy_id = b.strategy_id
            WHERE b.sharpe_ratio IS NOT NULL
        """)

    def get_top_strategies(self, min_sharpe: float = 1.0, limit: int = 10) -> QueryResult:
        """Get top strategies by Sharpe ratio."""
        return self._query_duckdb(
            """
            SELECT s.strategy_id, s.name, s.methodology_type,
                   b.sharpe_ratio, b.max_drawdown, b.win_rate, b.profit_factor
            FROM strategies s
            INNER JOIN backtests b ON s.strategy_id = b.strategy_id
            WHERE b.sharpe_ratio >= ?
            ORDER BY b.sharpe_ratio DESC
            LIMIT ?
        """,
            [min_sharpe, limit],
        )

    def get_paper_trends_by_year(self) -> QueryResult:
        """Get paper count by year."""
        return self._query_duckdb("""
            SELECT
                EXTRACT(YEAR FROM created_at) AS year,
                COUNT(*) AS paper_count,
                COUNT(DISTINCT methodology_type) AS methodology_count
            FROM papers
            WHERE created_at IS NOT NULL
            GROUP BY year
            ORDER BY year DESC
        """)

    def get_methodology_breakdown(self) -> QueryResult:
        """Get strategy count by methodology type."""
        return self._query_duckdb("""
            SELECT
                s.methodology_type,
                COUNT(DISTINCT s.strategy_id) AS strategy_count,
                AVG(b.sharpe_ratio) AS avg_sharpe,
                AVG(b.max_drawdown) AS avg_drawdown
            FROM strategies s
            LEFT JOIN backtests b ON s.strategy_id = b.strategy_id
            WHERE s.methodology_type IS NOT NULL
            GROUP BY s.methodology_type
            ORDER BY strategy_count DESC
        """)

    def get_formula_stats(self) -> QueryResult:
        """Get formula statistics by type."""
        return self._query_duckdb("""
            SELECT
                formula_type,
                COUNT(*) AS count,
                SUM(CASE WHEN validation_status = 'valid' THEN 1 ELSE 0 END) AS validated,
                SUM(CASE WHEN wolfram_verified THEN 1 ELSE 0 END) AS wolfram_verified
            FROM formulas
            GROUP BY formula_type
            ORDER BY count DESC
        """)

    def search_papers(
        self,
        title_contains: str | None = None,
        methodology: str | None = None,
        min_relevance: float | None = None,
        limit: int = 20,
    ) -> QueryResult:
        """Search papers with filters."""
        conditions: list[str] = []
        params: list[str | float] = []

        if title_contains:
            conditions.append("title ILIKE ?")
            params.append(f"%{title_contains}%")
        if methodology:
            conditions.append("methodology_type = ?")
            params.append(methodology)
        if min_relevance is not None:
            conditions.append("relevance_score >= ?")
            params.append(min_relevance)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        return self._query_duckdb(
            f"""
            SELECT paper_id, title, arxiv_id, methodology_type, relevance_score
            FROM papers
            WHERE {where_clause}
            ORDER BY relevance_score DESC NULLS LAST
            LIMIT ?
        """,
            params + [limit],
        )

    def get_event_summary(self) -> QueryResult:
        """Get summary of research events."""
        return self._query_duckdb("""
            SELECT
                event_type,
                COUNT(*) AS count,
                SUM(CASE WHEN processed_neo4j THEN 1 ELSE 0 END) AS synced,
                MAX(created_at) AS last_event
            FROM events
            GROUP BY event_type
            ORDER BY count DESC
        """)

    # ========================
    # Hybrid Queries
    # ========================

    def get_full_strategy_report(self, strategy_id: str) -> dict[str, Any]:
        """
        Get complete strategy report combining graph and analytics.

        Returns combined data from Neo4j (relationships) and DuckDB (metrics).
        """
        # Graph data from Neo4j
        graph_result = self.get_strategy_with_formulas(strategy_id)

        # Analytics data from DuckDB
        analytics_result = self._query_duckdb(
            """
            SELECT s.implementation_status, s.implementation_path, s.updated_at,
                   b.sharpe_ratio, b.max_drawdown, b.win_rate, b.profit_factor
            FROM strategies s
            LEFT JOIN backtests b ON s.strategy_id = b.strategy_id
            WHERE s.strategy_id = ?
        """,
            [strategy_id],
        )

        report: dict[str, Any] = {
            "strategy_id": strategy_id,
            "graph_data": graph_result.data[0] if graph_result.data else {},
            "analytics": analytics_result.data[0] if analytics_result.data else {},
            "errors": [],
        }

        if graph_result.error:
            report["errors"].append(f"Neo4j: {graph_result.error}")
        if analytics_result.error:
            report["errors"].append(f"DuckDB: {analytics_result.error}")

        return report


def main():
    """CLI for research queries."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Research Query Router")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # query command
    query_parser = subparsers.add_parser("query", help="Direct query")
    query_parser.add_argument("engine", choices=["neo4j", "duckdb"])
    query_parser.add_argument("query", help="Query string")

    # stats command
    subparsers.add_parser("stats", help="Show strategy stats")

    # top command
    top_parser = subparsers.add_parser("top", help="Top strategies")
    top_parser.add_argument("--min-sharpe", type=float, default=1.0)
    top_parser.add_argument("--limit", type=int, default=10)

    # search command
    search_parser = subparsers.add_parser("search", help="Search papers")
    search_parser.add_argument("--title", help="Title contains")
    search_parser.add_argument("--methodology", help="Methodology type")
    search_parser.add_argument("--min-relevance", type=float)

    # events command
    subparsers.add_parser("events", help="Event summary")

    args = parser.parse_args()

    with ResearchQuery() as rq:
        if args.command == "query":
            result = rq.query(args.engine, args.query)
        elif args.command == "stats":
            result = rq.get_strategy_stats()
        elif args.command == "top":
            result = rq.get_top_strategies(args.min_sharpe, args.limit)
        elif args.command == "search":
            result = rq.search_papers(args.title, args.methodology, args.min_relevance)
        elif args.command == "events":
            result = rq.get_event_summary()
        else:
            print(f"Unknown command: {args.command}")
            return

        if result.error:
            print(f"Error: {result.error}")
        else:
            print(json.dumps(result.data, indent=2, default=str))


if __name__ == "__main__":
    main()
