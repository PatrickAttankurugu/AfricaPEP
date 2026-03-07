"""Wikidata SPARQL scraper for African PEPs.

Pulls verified politician data from Wikidata's public SPARQL endpoint.
Each person has referenced sources (Wikipedia, government sites, etc.).
This is the primary data source — fixture data is only a fallback.

Usage:
    scraper = WikidataScraper(country_code="NG")
    records = scraper.scrape()
"""
from __future__ import annotations

import time
from datetime import datetime
from typing import Dict, List, Optional

import requests
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

log = structlog.get_logger(__name__)

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"

# Wikidata QIDs for African countries, keyed by ISO 3166-1 alpha-2
COUNTRY_QIDS: Dict[str, str] = {
    "DZ": "Q262", "AO": "Q916", "BJ": "Q962", "BW": "Q963",
    "BF": "Q965", "BI": "Q967", "CM": "Q1009", "CV": "Q1011",
    "CF": "Q929", "TD": "Q657", "KM": "Q970", "CG": "Q971",
    "CD": "Q974", "CI": "Q1008", "DJ": "Q977", "EG": "Q79",
    "GQ": "Q983", "ER": "Q986", "SZ": "Q1050", "ET": "Q115",
    "GA": "Q1000", "GM": "Q1005", "GH": "Q117", "GN": "Q1006",
    "GW": "Q1007", "KE": "Q114", "LS": "Q1013", "LR": "Q1014",
    "LY": "Q1016", "MG": "Q1019", "MW": "Q1020", "ML": "Q912",
    "MR": "Q1025", "MU": "Q1027", "MA": "Q1028", "MZ": "Q1029",
    "NA": "Q1030", "NE": "Q1032", "NG": "Q1033", "RW": "Q1037",
    "ST": "Q1039", "SN": "Q1041", "SC": "Q1042", "SL": "Q1044",
    "SO": "Q1045", "ZA": "Q258", "SS": "Q958", "SD": "Q1049",
    "TZ": "Q924", "TG": "Q945", "TN": "Q948", "UG": "Q1036",
    "ZM": "Q953", "ZW": "Q954",
}


def _build_query(country_qid: str) -> str:
    """Build SPARQL query to fetch politicians for a country.

    Returns people who hold/held positions (P39) in institutions
    tied to the given country (P17). Includes position start/end dates.
    """
    return f"""
SELECT DISTINCT ?personLabel ?positionLabel ?institutionLabel ?start ?end WHERE {{
  ?person wdt:P39 ?position .
  ?position wdt:P17 wd:{country_qid} .
  OPTIONAL {{
    ?person p:P39 ?stmt .
    ?stmt ps:P39 ?position .
    OPTIONAL {{ ?stmt pq:P580 ?start }}
    OPTIONAL {{ ?stmt pq:P582 ?end }}
  }}
  OPTIONAL {{ ?position wdt:P361 ?institution }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
}}
ORDER BY ?personLabel
LIMIT 2000
"""


class WikidataScraper(BaseScraper):
    """Scraper that pulls PEP data from Wikidata's SPARQL endpoint."""

    source_type = "WIKIDATA"

    def __init__(self, country_code: str, use_fixture: bool = False):
        super().__init__(use_fixture=use_fixture)
        self.country_code = country_code.upper()
        qid = COUNTRY_QIDS.get(self.country_code)
        if not qid:
            raise ValueError(f"Unknown country code: {self.country_code}")
        self._country_qid = qid

    def scrape(self) -> List[RawPersonRecord]:
        """Query Wikidata SPARQL for politicians of this country."""
        log.info(
            "wikidata.scrape.start",
            country=self.country_code,
            qid=self._country_qid,
        )
        try:
            records = self._query_sparql()
            log.info(
                "wikidata.scrape.complete",
                country=self.country_code,
                record_count=len(records),
            )
            if records:
                return records
            log.warning(
                "wikidata.scrape.no_results",
                country=self.country_code,
                hint="Falling back to fixture data",
            )
            return self._load_fixture()
        except Exception as exc:
            log.error(
                "wikidata.scrape.failed",
                country=self.country_code,
                error=str(exc),
                hint="Falling back to fixture data",
            )
            return self._load_fixture()

    def _query_sparql(self) -> List[RawPersonRecord]:
        """Execute SPARQL query and parse results into records."""
        query = _build_query(self._country_qid)
        now = datetime.utcnow()

        # Polite delay before querying
        time.sleep(1)

        resp = requests.get(
            SPARQL_ENDPOINT,
            params={"query": query, "format": "json"},
            headers={
                "User-Agent": "AfricaPEP/1.0 (KYC research; https://github.com/PatrickAttankurugu/AfricaPEP)",
                "Accept": "application/json",
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()

        records: List[RawPersonRecord] = []
        seen: set = set()

        for binding in data.get("results", {}).get("bindings", []):
            name = binding.get("personLabel", {}).get("value", "")
            position = binding.get("positionLabel", {}).get("value", "")
            institution = binding.get("institutionLabel", {}).get("value", "")

            # Skip blank or QID-only labels (unresolved entities)
            if not name or name.startswith("Q") or not position:
                continue

            # Deduplicate by name+position
            key = (name.lower(), position.lower())
            if key in seen:
                continue
            seen.add(key)

            # Parse dates
            start_date = _parse_date(binding.get("start", {}).get("value"))
            end_date = _parse_date(binding.get("end", {}).get("value"))
            is_current = end_date is None

            records.append(
                RawPersonRecord(
                    full_name=name,
                    title=position,
                    institution=institution or position,
                    country_code=self.country_code,
                    source_url=f"https://www.wikidata.org/wiki/{self._country_qid}",
                    source_type="WIKIDATA",
                    raw_text=f"{name} - {position}",
                    scraped_at=now,
                    extra_fields={
                        "start_date": start_date,
                        "end_date": end_date,
                        "is_current": is_current,
                        "wikidata_country_qid": self._country_qid,
                    },
                )
            )

        return records

    def _load_fixture(self) -> List[RawPersonRecord]:
        """No fixture data for Wikidata scraper — returns empty list."""
        return []


def _parse_date(value: Optional[str]) -> Optional[str]:
    """Parse Wikidata date string to ISO format."""
    if not value:
        return None
    try:
        # Wikidata dates look like "2023-05-29T00:00:00Z"
        return value[:10]
    except (IndexError, TypeError):
        return None


def scrape_all_countries() -> Dict[str, List[RawPersonRecord]]:
    """Scrape PEP data for all 54 African countries from Wikidata.

    Returns a dict keyed by country code.
    Adds a polite 2-second delay between countries.
    """
    results: Dict[str, List[RawPersonRecord]] = {}
    for code in sorted(COUNTRY_QIDS.keys()):
        log.info("wikidata.scrape_all", country=code)
        try:
            scraper = WikidataScraper(country_code=code)
            records = scraper.scrape()
            results[code] = records
            log.info("wikidata.scrape_all.done", country=code, count=len(records))
        except Exception as exc:
            log.error("wikidata.scrape_all.failed", country=code, error=str(exc))
            results[code] = []
        # Polite delay between countries
        time.sleep(2)
    return results
