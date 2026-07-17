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
from africapep.scraper.spiders.ghana_parliament_scraper import GhanaParliamentScraper

__all__ = [
    "WikidataScraper",
    "GhanaParliamentScraper",
    "COUNTRY_QIDS",
    "REGIONAL_BODY_QIDS",
    "scrape_regional_bodies",
]
