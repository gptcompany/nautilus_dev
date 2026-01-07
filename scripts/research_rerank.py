#!/usr/bin/env python3
"""
Research Rerank Service - Semantic similarity search with embeddings.

Uses sentence-transformers to generate embeddings and DuckDB for vector search.

Usage:
    # Generate embeddings for all papers
    python research_rerank.py embed

    # Search with reranking
    python research_rerank.py search "momentum trading strategies"

    # Get similar papers
    python research_rerank.py similar arxiv:1234 --top 5
"""

import argparse
from pathlib import Path
from typing import Any

import duckdb
import numpy as np

# Configuration
DUCKDB_PATH = Path("/media/sam/1TB/nautilus_dev/data/research.duckdb")
MODEL_NAME = "all-MiniLM-L6-v2"  # Fast, 384 dimensions
EMBEDDING_DIM = 384

# Lazy load model
_model = None


def get_model():
    """Lazy load sentence-transformers model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer

            _model = SentenceTransformer(MODEL_NAME)
            print(f"Loaded model: {MODEL_NAME}")
        except ImportError:
            print("Error: sentence-transformers not installed")
            print("Install with: pip install sentence-transformers")
            raise
    return _model


def init_embedding_table():
    """Create separate embeddings table to avoid FK issues."""
    db = duckdb.connect(str(DUCKDB_PATH))

    db.execute("""
        CREATE TABLE IF NOT EXISTS paper_embeddings (
            paper_id VARCHAR PRIMARY KEY,
            embedding FLOAT[] NOT NULL,
            model_name VARCHAR DEFAULT 'all-MiniLM-L6-v2',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.execute("""
        CREATE INDEX IF NOT EXISTS idx_embeddings_paper
        ON paper_embeddings (paper_id)
    """)

    print("Embeddings table ready")
    db.close()


def generate_paper_text(paper: dict) -> str:
    """Generate text representation of paper for embedding."""
    parts = []
    if paper.get("title"):
        parts.append(paper["title"])
    if paper.get("abstract"):
        parts.append(paper["abstract"])
    if paper.get("methodology_type"):
        parts.append(f"methodology: {paper['methodology_type']}")
    return " ".join(parts)


def generate_embeddings() -> tuple[int, int]:
    """Generate embeddings for all papers without embeddings."""
    model = get_model()
    db = duckdb.connect(str(DUCKDB_PATH))
    init_embedding_table()

    # Get papers without embeddings (using LEFT JOIN)
    papers = db.execute("""
        SELECT p.paper_id, p.title, p.abstract, p.methodology_type
        FROM papers p
        LEFT JOIN paper_embeddings pe ON p.paper_id = pe.paper_id
        WHERE pe.paper_id IS NULL
    """).fetchall()

    if not papers:
        print("All papers already have embeddings")
        db.close()
        return 0, 0

    print(f"Generating embeddings for {len(papers)} papers...")

    updated = 0
    errors = 0

    for paper_id, title, abstract, methodology in papers:
        try:
            paper = {
                "title": title,
                "abstract": abstract,
                "methodology_type": methodology,
            }
            text = generate_paper_text(paper)

            if not text.strip():
                continue

            embedding = model.encode(text, convert_to_numpy=True)
            embedding_list = embedding.tolist()

            db.execute(
                """
                INSERT OR REPLACE INTO paper_embeddings (paper_id, embedding, model_name)
                VALUES (?, ?, ?)
            """,
                [paper_id, embedding_list, MODEL_NAME],
            )
            updated += 1
            print(f"  ✓ {paper_id}: {title[:50]}...")
        except Exception as e:
            errors += 1
            print(f"  ✗ {paper_id}: {e}")

    db.close()
    return updated, errors


def search_papers(
    query: str, top_k: int = 10, min_similarity: float = 0.3
) -> list[dict[str, Any]]:
    """
    Search papers using semantic similarity.

    Returns papers ranked by cosine similarity to query.
    """
    model = get_model()
    db = duckdb.connect(str(DUCKDB_PATH), read_only=True)

    # Generate query embedding
    query_embedding = model.encode(query, convert_to_numpy=True)

    # Get all papers with embeddings (using JOIN)
    papers = db.execute("""
        SELECT p.paper_id, p.title, p.abstract, p.methodology_type,
               pe.embedding, p.relevance_score
        FROM papers p
        INNER JOIN paper_embeddings pe ON p.paper_id = pe.paper_id
    """).fetchall()

    if not papers:
        db.close()
        return []

    # Calculate similarities
    results = []
    query_norm = np.linalg.norm(query_embedding)

    for paper_id, title, abstract, methodology, embedding, relevance in papers:
        if embedding is None:
            continue

        paper_embedding = np.array(embedding)
        paper_norm = np.linalg.norm(paper_embedding)

        if paper_norm == 0:
            continue

        similarity = np.dot(query_embedding, paper_embedding) / (
            query_norm * paper_norm
        )

        if similarity >= min_similarity:
            results.append(
                {
                    "paper_id": paper_id,
                    "title": title,
                    "abstract": abstract[:200] + "..."
                    if abstract and len(abstract) > 200
                    else abstract,
                    "methodology_type": methodology,
                    "similarity": float(similarity),
                    "relevance_score": relevance,
                    "combined_score": float(similarity) * 0.7
                    + (relevance or 0) / 10 * 0.3,
                }
            )

    # Sort by combined score (similarity + relevance)
    results.sort(key=lambda x: x["combined_score"], reverse=True)

    db.close()
    return results[:top_k]


def get_similar_papers(paper_id: str, top_k: int = 5) -> list[dict[str, Any]]:
    """
    Find papers similar to a given paper.
    """
    db = duckdb.connect(str(DUCKDB_PATH), read_only=True)

    # Get target paper embedding
    target = db.execute(
        """
        SELECT pe.embedding, p.title
        FROM paper_embeddings pe
        JOIN papers p ON pe.paper_id = p.paper_id
        WHERE pe.paper_id = ?
    """,
        [paper_id],
    ).fetchone()

    if not target or not target[0]:
        db.close()
        return []

    target_embedding = np.array(target[0])
    target_norm = np.linalg.norm(target_embedding)

    # Get all other papers
    papers = db.execute(
        """
        SELECT p.paper_id, p.title, p.methodology_type, pe.embedding
        FROM papers p
        INNER JOIN paper_embeddings pe ON p.paper_id = pe.paper_id
        WHERE p.paper_id != ?
    """,
        [paper_id],
    ).fetchall()

    results = []

    for pid, title, methodology, embedding in papers:
        if embedding is None:
            continue

        paper_embedding = np.array(embedding)
        paper_norm = np.linalg.norm(paper_embedding)

        if paper_norm == 0:
            continue

        similarity = np.dot(target_embedding, paper_embedding) / (
            target_norm * paper_norm
        )

        results.append(
            {
                "paper_id": pid,
                "title": title,
                "methodology_type": methodology,
                "similarity": float(similarity),
            }
        )

    results.sort(key=lambda x: x["similarity"], reverse=True)
    db.close()

    return results[:top_k]


def rerank_search_results(
    search_results: list[dict], query: str, weight_similarity: float = 0.7
) -> list[dict]:
    """
    Rerank search results using semantic similarity.

    Args:
        search_results: List of papers from initial search
        query: Original search query
        weight_similarity: Weight for similarity (1 - weight = relevance weight)
    """
    if not search_results:
        return []

    model = get_model()
    query_embedding = model.encode(query, convert_to_numpy=True)
    query_norm = np.linalg.norm(query_embedding)

    for paper in search_results:
        text = generate_paper_text(paper)
        if text.strip():
            paper_embedding = model.encode(text, convert_to_numpy=True)
            paper_norm = np.linalg.norm(paper_embedding)
            if paper_norm > 0:
                similarity = np.dot(query_embedding, paper_embedding) / (
                    query_norm * paper_norm
                )
                paper["similarity"] = float(similarity)
                relevance = paper.get("relevance_score", 5) / 10
                paper["combined_score"] = similarity * weight_similarity + relevance * (
                    1 - weight_similarity
                )
            else:
                paper["similarity"] = 0.0
                paper["combined_score"] = paper.get("relevance_score", 5) / 10
        else:
            paper["similarity"] = 0.0
            paper["combined_score"] = paper.get("relevance_score", 5) / 10

    search_results.sort(key=lambda x: x["combined_score"], reverse=True)
    return search_results


def show_stats():
    """Show embedding statistics."""
    db = duckdb.connect(str(DUCKDB_PATH), read_only=True)

    total = db.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
    with_embedding = db.execute("SELECT COUNT(*) FROM paper_embeddings").fetchone()[0]

    print("=== Embedding Statistics ===\n")
    print(f"Total papers:      {total}")
    print(f"With embeddings:   {with_embedding}")
    print(f"Missing:           {total - with_embedding}")
    print(
        f"Coverage:          {with_embedding / total * 100:.1f}%"
        if total > 0
        else "N/A"
    )
    print(f"\nModel: {MODEL_NAME}")
    print(f"Dimensions: {EMBEDDING_DIM}")

    db.close()


def main():
    parser = argparse.ArgumentParser(description="Research Rerank Service")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # embed command
    subparsers.add_parser("embed", help="Generate embeddings for papers")

    # search command
    search_parser = subparsers.add_parser("search", help="Semantic search")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--top", type=int, default=10, help="Top K results")
    search_parser.add_argument(
        "--min-sim", type=float, default=0.3, help="Minimum similarity"
    )

    # similar command
    similar_parser = subparsers.add_parser("similar", help="Find similar papers")
    similar_parser.add_argument("paper_id", help="Paper ID")
    similar_parser.add_argument("--top", type=int, default=5, help="Top K results")

    # stats command
    subparsers.add_parser("stats", help="Show embedding statistics")

    # init command
    subparsers.add_parser("init", help="Initialize embedding column")

    args = parser.parse_args()

    if args.command == "embed":
        updated, errors = generate_embeddings()
        print(f"\nUpdated: {updated}, Errors: {errors}")

    elif args.command == "search":
        results = search_papers(args.query, args.top, args.min_sim)
        if results:
            print(f"\n=== Search Results for '{args.query}' ===\n")
            for i, r in enumerate(results, 1):
                print(f"{i}. [{r['similarity']:.3f}] {r['title']}")
                print(f"   ID: {r['paper_id']}, Methodology: {r['methodology_type']}")
                if r.get("abstract"):
                    print(f"   {r['abstract'][:100]}...")
                print()
        else:
            print("No results found")

    elif args.command == "similar":
        results = get_similar_papers(args.paper_id, args.top)
        if results:
            print(f"\n=== Papers Similar to {args.paper_id} ===\n")
            for i, r in enumerate(results, 1):
                print(f"{i}. [{r['similarity']:.3f}] {r['title']}")
                print(f"   ID: {r['paper_id']}, Methodology: {r['methodology_type']}")
                print()
        else:
            print("No similar papers found")

    elif args.command == "stats":
        show_stats()

    elif args.command == "init":
        init_embedding_table()


if __name__ == "__main__":
    main()
