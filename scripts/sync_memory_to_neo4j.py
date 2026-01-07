#!/usr/bin/env python3
"""
Sync memory.json entities to Neo4j knowledge graph.

Usage:
    python sync_memory_to_neo4j.py [--force]

Options:
    --force     Sync all entities, not just new ones
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from neo4j import GraphDatabase

# Configuration
MEMORY_JSON_PATH = Path("/media/sam/1TB1/academic_research/memory.json")
NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "research123")


def load_memory_json() -> dict:
    """Load memory.json file."""
    if not MEMORY_JSON_PATH.exists():
        print(f"Warning: {MEMORY_JSON_PATH} not found")
        return {"entities": [], "relations": []}

    with open(MEMORY_JSON_PATH) as f:
        return json.load(f)


def sync_entity_to_neo4j(tx, entity: dict):
    """Sync a single entity to Neo4j based on its type."""
    name = entity.get("name", "")
    entity_type = entity.get("entityType", "Entity")
    observations = entity.get("observations", [])

    # Parse observations into properties
    props = {"name": name, "synced_at": datetime.now().isoformat()}
    for obs in observations:
        if ": " in obs:
            key, value = obs.split(": ", 1)
            props[key.replace(" ", "_").lower()] = value

    # Whitelist of allowed labels to prevent Cypher injection
    ALLOWED_LABELS = {
        "Strategy",
        "Paper",
        "Formula",
        "Concept",
        "Author",
        "Entity",
        "Source",
        "Code",
        "Indicator",
        "Methodology",
    }

    # Determine node label based on entity type or name prefix
    if name.startswith("strategy__"):
        label = "Strategy"
        props["strategy_id"] = name
    elif name.startswith("source__"):
        label = "Paper"
        props["paper_id"] = name
    elif name.startswith("formula__"):
        label = "Formula"
        props["formula_id"] = name
    elif entity_type == "concept":
        label = "Concept"
    else:
        # Sanitize label: only allow alphanumeric
        label = entity_type.title().replace("_", "")
        # Validate against whitelist
        if label not in ALLOWED_LABELS:
            label = "Entity"  # Safe default

    # Create or update node
    query = f"""
        MERGE (n:{label} {{name: $name}})
        SET n += $props
        RETURN n
    """
    tx.run(query, name=name, props=props)
    return label


def sync_relation_to_neo4j(tx, relation: dict):
    """Sync a relation to Neo4j."""
    from_entity = relation.get("from", "")
    to_entity = relation.get("to", "")
    rel_type = relation.get("relationType", "RELATED_TO").upper().replace(" ", "_")

    # Whitelist of allowed relationship types to prevent Cypher injection
    ALLOWED_REL_TYPES = {
        "RELATED_TO",
        "BASED_ON",
        "USES",
        "CONTAINS",
        "WRITTEN_BY",
        "CITES",
        "IMPLEMENTS",
        "DERIVED_FROM",
        "HAS_FORMULA",
        "HAS_INDICATOR",
    }

    # Validate relationship type
    if rel_type not in ALLOWED_REL_TYPES:
        # Sanitize: only allow alphanumeric and underscore
        import re

        if not re.match(r"^[A-Z_]+$", rel_type) or len(rel_type) > 50:
            rel_type = "RELATED_TO"  # Safe default

    query = (
        """
        MATCH (a {name: $from_name})
        MATCH (b {name: $to_name})
        MERGE (a)-[r:"""
        + rel_type
        + """]->(b)
        SET r.synced_at = $synced_at
        RETURN type(r) as rel_type
    """
    )
    result = tx.run(
        query,
        from_name=from_entity,
        to_name=to_entity,
        synced_at=datetime.now().isoformat(),
    )
    return result.single()


def main():
    _force = "--force" in sys.argv  # Reserved for future use

    print(f"Loading memory.json from {MEMORY_JSON_PATH}...")
    memory = load_memory_json()

    entities = memory.get("entities", [])
    relations = memory.get("relations", [])

    print(f"Found {len(entities)} entities, {len(relations)} relations")

    if not entities:
        print("No entities to sync")
        return

    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)

    try:
        with driver.session() as session:
            # Sync entities
            synced_labels = {}
            for entity in entities:
                label = session.execute_write(sync_entity_to_neo4j, entity)
                synced_labels[label] = synced_labels.get(label, 0) + 1

            print("\nSynced entities by type:")
            for label, count in synced_labels.items():
                print(f"  {label}: {count}")

            # Sync relations
            synced_rels = 0
            for relation in relations:
                result = session.execute_write(sync_relation_to_neo4j, relation)
                if result:
                    synced_rels += 1

            print(f"\nSynced {synced_rels} relations")

            # Show final counts
            result = session.run(
                "MATCH (n) RETURN labels(n)[0] as label, count(n) as count"
            )
            print("\nNeo4j node counts:")
            for record in result:
                print(f"  {record['label']}: {record['count']}")

    finally:
        driver.close()

    print("\nSync complete!")


if __name__ == "__main__":
    main()
