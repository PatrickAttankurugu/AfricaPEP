"""AfricaPEP scraper spiders.

Primary data source: Wikidata SPARQL endpoint.
Pulls verified, referenced PEP data for all 54 African countries.
"""

from africapep.scraper.spiders.wikidata_scraper import (
    WikidataScraper,
    COUNTRY_QIDS,
    REGIONAL_BODY_QIDS,
    scrape_regional_bodies,
)

__all__ = ["WikidataScraper", "COUNTRY_QIDS", "REGIONAL_BODY_QIDS", "scrape_regional_bodies"]
