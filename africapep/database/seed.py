"""Seed the database with PEP data from Wikidata + fixture scrapers.
Run with: python -m africapep.database.seed

Modes:
  --wikidata     Pull live data from Wikidata SPARQL (primary source)
  --fixtures     Use hardcoded fixture data only (fast, offline)
  --all          Both Wikidata + fixtures (default, most complete)

Idempotent — safe to run multiple times. Entity resolver deduplicates.
"""
import sys
import structlog

from africapep.scraper.spiders import ALL_SCRAPERS
from africapep.scraper.spiders.wikidata_scraper import WikidataScraper, COUNTRY_QIDS
from africapep.pipeline.normaliser import normalise_record
from africapep.pipeline.classifier import classify_pep_tier
from africapep.pipeline.resolver import EntityResolver
from africapep.database.neo4j_client import neo4j_client
from africapep.database.sync import sync_all

log = structlog.get_logger()


def _seed_fixtures(resolver: EntityResolver) -> int:
    """Load fixture data from all country scrapers."""
    scrapers = [
        (cls.__name__, cls(use_fixture=True))
        for cls in ALL_SCRAPERS
    ]
    total = 0
    for name, scraper in scrapers:
        print(f"    {name}...")
        records = scraper.run()
        total += len(records)
        for record in records:
            normalised = normalise_record(record)
            tier = classify_pep_tier(normalised.title, normalised.institution)
            resolver.add(normalised, tier)
    return total


def _seed_wikidata(resolver: EntityResolver) -> int:
    """Pull live PEP data from Wikidata for all 54 African countries."""
    total = 0
    for code in sorted(COUNTRY_QIDS.keys()):
        print(f"    Wikidata [{code}]...", end=" ", flush=True)
        try:
            scraper = WikidataScraper(country_code=code)
            records = scraper.scrape()
            print(f"{len(records)} records")
            total += len(records)
            for record in records:
                normalised = normalise_record(record)
                tier = classify_pep_tier(normalised.title, normalised.institution)
                resolver.add(normalised, tier)
        except Exception as exc:
            print(f"FAILED: {exc}")
            log.error("seed.wikidata.failed", country=code, error=str(exc))
    return total


def main():
    args = set(sys.argv[1:])
    use_wikidata = "--wikidata" in args or "--all" in args or not args
    use_fixtures = "--fixtures" in args or "--all" in args or not args

    print("=" * 50)
    print("  AfricaPEP Database Seed")
    print(f"  Sources: {'Wikidata' if use_wikidata else ''}"
          f"{'+ ' if use_wikidata and use_fixtures else ''}"
          f"{'Fixtures' if use_fixtures else ''}")
    print("=" * 50)
    print()

    resolver = EntityResolver()
    total_raw = 0

    if use_wikidata:
        print("  [1/2] Pulling from Wikidata SPARQL...")
        wikidata_count = _seed_wikidata(resolver)
        total_raw += wikidata_count
        print(f"  Wikidata total: {wikidata_count} raw records")
        print()

    if use_fixtures:
        step = "2/2" if use_wikidata else "1/1"
        print(f"  [{step}] Loading fixture data...")
        fixture_count = _seed_fixtures(resolver)
        total_raw += fixture_count
        print(f"  Fixtures total: {fixture_count} raw records")
        print()

    stats = resolver.get_stats()
    print(f"  Total raw records: {total_raw}")
    print(f"  Resolved entities: {stats['total_entities']}")
    print(f"  Potential duplicates: {stats['potential_duplicates']}")
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
