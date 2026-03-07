"""AfricaPEP scraper spiders.

Primary data source: Wikidata SPARQL endpoint.
Pulls verified, referenced PEP data for all 54 African countries.
"""

from africapep.scraper.spiders.wikidata_scraper import WikidataScraper, COUNTRY_QIDS

__all__ = ["WikidataScraper", "COUNTRY_QIDS"]
