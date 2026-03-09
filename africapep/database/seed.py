"""Seed the database with PEP data from Wikidata.

Run with: python -m africapep.database.seed

Pulls verified politician data from Wikidata's SPARQL endpoint
for all 54 African countries. Entity resolver deduplicates records.
Idempotent — safe to run multiple times.
"""
import time

import structlog
from rapidfuzz import fuzz

from africapep.scraper.spiders.wikidata_scraper import (
    WikidataScraper, COUNTRY_QIDS, scrape_relationships,
)
from africapep.pipeline.normaliser import normalise_record
from africapep.pipeline.classifier import classify_pep_tier
from africapep.pipeline.resolver import EntityResolver
from africapep.database.neo4j_client import neo4j_client
from africapep.database.sync import sync_all

log = structlog.get_logger()


def main():
    print("=" * 50)
    print("  AfricaPEP Database Seed")
    print("  Source: Wikidata SPARQL (live data)")
    print("=" * 50)
    print()

    resolver = EntityResolver()
    total_raw = 0

    print(f"  Pulling PEP data for {len(COUNTRY_QIDS)} African countries...")
    print()

    for code in sorted(COUNTRY_QIDS.keys()):
        print(f"    [{code}] ", end="", flush=True)
        try:
            scraper = WikidataScraper(country_code=code)
            records = scraper.scrape()
            print(f"{len(records)} records")
            total_raw += len(records)
            for record in records:
                normalised = normalise_record(record)
                tier = classify_pep_tier(normalised.title, normalised.institution)
                resolver.add(normalised, tier)
        except Exception as exc:
            print(f"FAILED: {exc}")
            log.error("seed.failed", country=code, error=str(exc))

    stats = resolver.get_stats()
    print()
    print(f"  Total raw records: {total_raw}")
    print(f"  Resolved entities: {stats['total_entities']}")
    print(f"  Duplicates merged: {stats['potential_duplicates']}")
    print()

    print("  Writing to Neo4j...")
    written = resolver.flush_to_neo4j(neo4j_client)
    print(f"    Written {written} entities")

    # Build a name->entity_id lookup for relationship linking
    known_persons: dict[str, str] = {}
    for entity in resolver.entities.values():
        known_persons[entity.full_name] = entity.id
        for variant in entity.name_variants:
            if variant not in known_persons:
                known_persons[variant] = entity.id

    # Also build QID->entity_id from the resolver's mapping
    qid_to_entity = resolver._qid_to_entity

    # Relationship extraction: query Wikidata for family links per country
    print("  Scraping family relationships from Wikidata...")
    total_rels = 0
    linked_rels = 0

    for code in sorted(COUNTRY_QIDS.keys()):
        print(f"    [{code}] ", end="", flush=True)
        try:
            rels = scrape_relationships(code)
            print(f"{len(rels)} relationships")
            total_rels += len(rels)

            for rel in rels:
                # Find the source person by QID
                person_entity_id = qid_to_entity.get(rel.person_qid)
                if not person_entity_id:
                    continue

                # Find the related person by fuzzy name match
                related_entity_id = _find_person_by_name(
                    rel.related_name, known_persons
                )

                if related_entity_id:
                    rel_type = rel.relationship_type
                    if rel_type in ("SPOUSE", "CHILD", "SIBLING", "FATHER", "MOTHER"):
                        neo4j_client.link_family(
                            person_entity_id, related_entity_id, rel_type
                        )
                    else:
                        neo4j_client.link_associate(
                            person_entity_id, related_entity_id, rel_type
                        )
                    linked_rels += 1

            time.sleep(1)
        except Exception as exc:
            print(f"FAILED: {exc}")
            log.error("seed.relationships.failed", country=code, error=str(exc))

    print(f"\n    Total relationships found: {total_rels}")
    print(f"    Successfully linked: {linked_rels}")

    print("  Syncing to PostgreSQL...")
    synced = sync_all()
    print(f"    Synced {synced} profiles")

    print()
    print("=" * 50)
    print("  Seed complete!")
    print("=" * 50)

    neo4j_client.close()


def _find_person_by_name(name: str, known_persons: dict[str, str],
                         threshold: float = 0.80) -> str | None:
    """Find a person entity ID by fuzzy name matching."""
    best_match = None
    best_score = 0.0

    for known_name, known_id in known_persons.items():
        score = fuzz.token_sort_ratio(name, known_name) / 100.0
        if score > best_score and score >= threshold:
            best_score = score
            best_match = known_id

    return best_match


if __name__ == "__main__":
    main()
