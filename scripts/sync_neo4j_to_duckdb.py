#!/usr/bin/env python3
"""
Sync Neo4j graph data to DuckDB for analytics.

Usage:
    python sync_neo4j_to_duckdb.py [--export-parquet]

Options:
    --export-parquet    Also export tables to Parquet files
"""

import sys
from pathlib import Path

import duckdb
from neo4j import GraphDatabase

# Configuration
NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "research123")
DUCKDB_PATH = Path("/media/sam/1TB/nautilus_dev/data/research.duckdb")
PARQUET_DIR = Path("/media/sam/1TB/nautilus_dev/data/parquet")


def fetch_papers(neo4j_session) -> list[dict]:
    """Fetch all Paper nodes from Neo4j."""
    result = neo4j_session.run("""
        MATCH (p:Paper)
        OPTIONAL MATCH (p)-[:WRITTEN_BY]->(a:Author)
        RETURN p.paper_id as paper_id,
               p.title as title,
               collect(a.name) as authors,
               p.abstract as abstract,
               p.arxiv_id as arxiv_id,
               p.doi as doi,
               p.source as source,
               p.methodology_type as methodology_type,
               p.relevance_score as relevance_score,
               p.pdf_path as pdf_path,
               p.parsed_content_path as parsed_content_path,
               p.synced_at as synced_at
    """)
    return [dict(record) for record in result]


def fetch_formulas(neo4j_session) -> list[dict]:
    """Fetch all Formula nodes with paper relationships."""
    result = neo4j_session.run("""
        MATCH (f:Formula)
        OPTIONAL MATCH (p:Paper)-[:CONTAINS]->(f)
        RETURN f.formula_id as formula_id,
               p.paper_id as paper_id,
               f.latex as latex,
               f.description as description,
               f.formula_type as formula_type,
               f.validation_status as validation_status,
               f.wolfram_verified as wolfram_verified,
               f.wolfram_result as wolfram_result,
               f.equation_number as equation_number,
               f.context as context,
               f.synced_at as synced_at
    """)
    return [dict(record) for record in result]


def fetch_strategies(neo4j_session) -> list[dict]:
    """Fetch all Strategy nodes with paper relationships."""
    result = neo4j_session.run("""
        MATCH (s:Strategy)
        OPTIONAL MATCH (s)-[:BASED_ON]->(p:Paper)
        OPTIONAL MATCH (s)-[:USES]->(f:Formula)
        RETURN s.strategy_id as strategy_id,
               s.name as name,
               p.paper_id as paper_id,
               s.methodology_type as methodology_type,
               s.entry_logic as entry_logic,
               s.exit_logic as exit_logic,
               s.position_sizing as position_sizing,
               s.risk_management as risk_management,
               collect(DISTINCT f.formula_id) as formula_ids,
               s.sharpe_ratio as sharpe_ratio,
               s.max_drawdown as max_drawdown,
               s.win_rate as win_rate,
               s.profit_factor as profit_factor,
               s.implementation_status as implementation_status,
               s.implementation_path as implementation_path,
               s.spec_path as spec_path,
               s.synced_at as synced_at
    """)
    return [dict(record) for record in result]


def sync_to_duckdb(papers: list, formulas: list, strategies: list):
    """Insert/update records in DuckDB."""
    db = duckdb.connect(str(DUCKDB_PATH))

    # Sync papers
    for paper in papers:
        if not paper.get("paper_id"):
            continue
        db.execute(
            """
            INSERT INTO papers
            (paper_id, title, authors, abstract, arxiv_id, doi, source,
             methodology_type, relevance_score, pdf_path, parsed_content_path, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT (paper_id) DO UPDATE SET
                title = EXCLUDED.title,
                updated_at = CURRENT_TIMESTAMP
        """,
            [
                paper["paper_id"],
                paper.get("title"),
                paper.get("authors", []),
                paper.get("abstract"),
                paper.get("arxiv_id"),
                paper.get("doi"),
                paper.get("source"),
                paper.get("methodology_type"),
                paper.get("relevance_score"),
                paper.get("pdf_path"),
                paper.get("parsed_content_path"),
            ],
        )

    # Sync formulas
    for formula in formulas:
        if not formula.get("formula_id"):
            continue
        db.execute(
            """
            INSERT INTO formulas
            (formula_id, paper_id, latex, description, formula_type,
             validation_status, wolfram_verified, wolfram_result,
             equation_number, context)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (formula_id) DO UPDATE SET
                latex = EXCLUDED.latex,
                validation_status = EXCLUDED.validation_status
        """,
            [
                formula["formula_id"],
                formula.get("paper_id"),
                formula.get("latex"),
                formula.get("description"),
                formula.get("formula_type"),
                formula.get("validation_status"),
                formula.get("wolfram_verified"),
                formula.get("wolfram_result"),
                formula.get("equation_number"),
                formula.get("context"),
            ],
        )

    # Sync strategies
    for strategy in strategies:
        if not strategy.get("strategy_id"):
            continue
        db.execute(
            """
            INSERT INTO strategies
            (strategy_id, name, paper_id, methodology_type, entry_logic,
             exit_logic, position_sizing, risk_management, indicators,
             sharpe_ratio, max_drawdown, win_rate, profit_factor,
             implementation_status, implementation_path, spec_path, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT (strategy_id) DO UPDATE SET
                name = EXCLUDED.name,
                implementation_status = EXCLUDED.implementation_status,
                updated_at = CURRENT_TIMESTAMP
        """,
            [
                strategy["strategy_id"],
                strategy.get("name"),
                strategy.get("paper_id"),
                strategy.get("methodology_type"),
                strategy.get("entry_logic"),
                strategy.get("exit_logic"),
                strategy.get("position_sizing"),
                strategy.get("risk_management"),
                strategy.get(
                    "formula_ids", []
                ),  # Using formula_ids as indicators proxy
                strategy.get("sharpe_ratio"),
                strategy.get("max_drawdown"),
                strategy.get("win_rate"),
                strategy.get("profit_factor"),
                strategy.get("implementation_status"),
                strategy.get("implementation_path"),
                strategy.get("spec_path"),
            ],
        )

    db.close()
    return len(papers), len(formulas), len(strategies)


def export_to_parquet():
    """Export DuckDB tables to Parquet files."""
    PARQUET_DIR.mkdir(parents=True, exist_ok=True)
    db = duckdb.connect(str(DUCKDB_PATH))

    tables = ["papers", "formulas", "strategies", "code_entities"]
    for table in tables:
        path = PARQUET_DIR / f"{table}.parquet"
        db.execute(f"COPY {table} TO '{path}' (FORMAT PARQUET)")
        print(f"  Exported {table} to {path}")

    db.close()


def main():
    export_parquet = "--export-parquet" in sys.argv

    print("Connecting to Neo4j...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)

    try:
        with driver.session() as session:
            print("Fetching data from Neo4j...")
            papers = fetch_papers(session)
            formulas = fetch_formulas(session)
            strategies = fetch_strategies(session)

            print(f"  Papers: {len(papers)}")
            print(f"  Formulas: {len(formulas)}")
            print(f"  Strategies: {len(strategies)}")

    finally:
        driver.close()

    print("\nSyncing to DuckDB...")
    p, f, s = sync_to_duckdb(papers, formulas, strategies)
    print(f"  Synced {p} papers, {f} formulas, {s} strategies")

    if export_parquet:
        print("\nExporting to Parquet...")
        export_to_parquet()

    # Show DuckDB stats
    db = duckdb.connect(str(DUCKDB_PATH))
    print("\nDuckDB table counts:")
    for table in ["papers", "formulas", "strategies"]:
        count = db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {count}")
    db.close()

    print("\nSync complete!")


if __name__ == "__main__":
    main()
