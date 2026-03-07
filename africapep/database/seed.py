"""Seed the database with fixture data from all scrapers.
Run with: python -m africapep.database.seed

Idempotent — safe to run multiple times.
"""
import structlog

from africapep.scraper.spiders.ghana_parliament import GhanaParliamentScraper
from africapep.scraper.spiders.ghana_presidency import GhanaPresidencyScraper
from africapep.scraper.spiders.nigeria_nass import NigeriaNASSScraper
from africapep.scraper.spiders.nigeria_presidency import NigeriaPresidencyScraper
from africapep.scraper.spiders.kenya_parliament import KenyaParliamentScraper
from africapep.scraper.spiders.southafrica_parliament import SouthAfricaParliamentScraper
from africapep.pipeline.normaliser import normalise_record
from africapep.pipeline.classifier import classify_pep_tier
from africapep.pipeline.resolver import EntityResolver
from africapep.database.neo4j_client import neo4j_client
from africapep.database.sync import sync_all

log = structlog.get_logger()


def main():
    print("=" * 40)
    print("  AfricaPEP Database Seed")
    print("=" * 40)
    print()

    # Use fixture mode for all scrapers
    scrapers = [
        ("Ghana Parliament", GhanaParliamentScraper(use_fixture=True)),
        ("Ghana Presidency", GhanaPresidencyScraper(use_fixture=True)),
        ("Nigeria NASS", NigeriaNASSScraper(use_fixture=True)),
        ("Nigeria Presidency", NigeriaPresidencyScraper(use_fixture=True)),
        ("Kenya Parliament", KenyaParliamentScraper(use_fixture=True)),
        ("South Africa Parliament", SouthAfricaParliamentScraper(use_fixture=True)),
    ]

    resolver = EntityResolver()
    total_raw = 0

    for name, scraper in scrapers:
        print(f"  Scraping: {name}...")
        records = scraper.run()
        print(f"    Found {len(records)} records")
        total_raw += len(records)

        for record in records:
            normalised = normalise_record(record)
            tier = classify_pep_tier(normalised.title, normalised.institution)
            resolver.add(normalised, tier)

    print()
    print(f"  Total raw records: {total_raw}")
    print(f"  Resolved entities: {resolver.get_stats()['total_entities']}")
    print(f"  Potential duplicates: {resolver.get_stats()['potential_duplicates']}")
    print()

    print("  Writing to Neo4j...")
    written = resolver.flush_to_neo4j(neo4j_client)
    print(f"    Written {written} entities")

    print("  Syncing to PostgreSQL...")
    synced = sync_all()
    print(f"    Synced {synced} profiles")

    print()
    print("=" * 40)
    print("  Seed complete!")
    print("=" * 40)

    neo4j_client.close()


if __name__ == "__main__":
    main()
