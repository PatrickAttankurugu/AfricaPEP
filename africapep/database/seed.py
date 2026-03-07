"""Seed the database with PEP data from Wikidata.

Run with: python -m africapep.database.seed

Pulls verified politician data from Wikidata's SPARQL endpoint
for all 54 African countries. Entity resolver deduplicates records.
Idempotent — safe to run multiple times.
"""
import structlog

from africapep.scraper.spiders.wikidata_scraper import WikidataScraper, COUNTRY_QIDS
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

    print("  Syncing to PostgreSQL...")
    synced = sync_all()
    print(f"    Synced {synced} profiles")

    print()
    print("=" * 50)
    print("  Seed complete!")
    print("=" * 50)

    neo4j_client.close()


if __name__ == "__main__":
    main()
