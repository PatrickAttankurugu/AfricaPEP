"""Seed the database from the bundled offline sample dataset.

Run with: python -m africapep.database.seed_sample

Loads real Wikidata records for two countries (Seychelles and Gambia,
captured 2026-07-13) from sample_data.json and pushes them through the
exact same pipeline as the full seed: normalise -> classify -> resolve ->
Neo4j -> PostgreSQL sync. No network access required.

Use this to get a populated local API in under a minute. For the full
54-country dataset, run: python -m africapep.database.seed
"""
import json
from datetime import datetime
from pathlib import Path

import structlog

from africapep.scraper.base_scraper import RawPersonRecord
from africapep.scraper.spiders.wikidata_scraper import WikidataRelationship

log = structlog.get_logger()

SAMPLE_PATH = Path(__file__).parent / "sample_data.json"


def load_sample() -> tuple[list[RawPersonRecord], list[WikidataRelationship]]:
    """Load the bundled sample dataset from disk."""
    with open(SAMPLE_PATH, encoding="utf-8") as f:
        data = json.load(f)

    records = []
    for d in data["records"]:
        d = dict(d)
        d["scraped_at"] = datetime.fromisoformat(d["scraped_at"])
        records.append(RawPersonRecord(**d))

    relationships = [WikidataRelationship(**r) for r in data["relationships"]]
    return records, relationships


def main():
    # DB-touching imports stay local so load_sample() is importable
    # (and testable) without database drivers installed.
    from africapep.pipeline.normaliser import normalise_record
    from africapep.pipeline.classifier import classify_pep_tier
    from africapep.pipeline.resolver import EntityResolver
    from africapep.database.neo4j_client import neo4j_client
    from africapep.database.sync import sync_all
    from africapep.database.seed import _find_person_by_name

    print("=" * 50)
    print("  AfricaPEP Sample Seed (offline)")
    print("  Source: bundled sample_data.json (SC + GM)")
    print("=" * 50)
    print()

    records, relationships = load_sample()
    print(f"  Loaded {len(records)} records, {len(relationships)} relationships")

    resolver = EntityResolver()
    for record in records:
        normalised = normalise_record(record)
        tier = classify_pep_tier(normalised.title, normalised.institution)
        resolver.add(normalised, tier)

    stats = resolver.get_stats()
    print(f"  Resolved entities: {stats['total_entities']}")
    print(f"  Duplicates merged: {stats['potential_duplicates']}")

    print("  Writing to Neo4j...")
    written = resolver.flush_to_neo4j(neo4j_client)
    print(f"    Written {written} entities")

    known_persons: dict[str, str] = {}
    for entity in resolver.entities.values():
        known_persons[entity.full_name] = entity.id
        for variant in entity.name_variants:
            if variant not in known_persons:
                known_persons[variant] = entity.id

    qid_to_entity = resolver._qid_to_entity

    linked = 0
    for rel in relationships:
        person_entity_id = qid_to_entity.get(rel.person_qid)
        if not person_entity_id:
            continue
        related_entity_id = _find_person_by_name(rel.related_name, known_persons)
        if related_entity_id:
            if rel.relationship_type in ("SPOUSE", "CHILD", "SIBLING", "FATHER", "MOTHER"):
                neo4j_client.link_family(person_entity_id, related_entity_id, rel.relationship_type)
            else:
                neo4j_client.link_associate(person_entity_id, related_entity_id, rel.relationship_type)
            linked += 1
    print(f"    Linked {linked} relationships")

    print("  Syncing to PostgreSQL...")
    synced = sync_all()
    print(f"    Synced {synced} profiles")

    print()
    print("=" * 50)
    print("  Sample seed complete. Try:")
    print('  curl -X POST http://localhost:8000/api/v1/screen \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"name": "Adama Barrow"}\'')
    print("=" * 50)

    neo4j_client.close()


if __name__ == "__main__":
    main()
