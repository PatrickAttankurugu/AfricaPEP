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
from dataclasses import dataclass
from datetime import datetime, timezone
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

# Wikidata QIDs for African regional organisations
REGIONAL_BODY_QIDS: Dict[str, str] = {
    "AU": "Q7159",       # African Union
    "ECOWAS": "Q166546", # Economic Community of West African States
    "SADC": "Q170552",   # Southern African Development Community
    "EAC": "Q190571",    # East African Community
}


def _build_regional_query(org_qid: str) -> str:
    """Build SPARQL query for officials of a regional organisation.

    Fetches people who hold/held positions (P39) in the given organisation,
    or positions that are part of (P361) the organisation.
    """
    return f"""
SELECT DISTINCT ?person ?personLabel ?positionLabel ?start ?end
       ?dob ?dod ?partyLabel ?nationalityLabel WHERE {{
  {{
    ?person wdt:P39 ?position .
    ?position wdt:P361* wd:{org_qid} .
  }} UNION {{
    ?person p:P39 ?stmt .
    ?stmt ps:P39 ?position .
    ?stmt pq:P642 wd:{org_qid} .
  }}
  OPTIONAL {{
    ?person p:P39 ?stmt2 .
    ?stmt2 ps:P39 ?position .
    OPTIONAL {{ ?stmt2 pq:P580 ?start }}
    OPTIONAL {{ ?stmt2 pq:P582 ?end }}
  }}
  OPTIONAL {{ ?person wdt:P569 ?dob }}
  OPTIONAL {{ ?person wdt:P570 ?dod }}
  OPTIONAL {{ ?person wdt:P102 ?party }}
  OPTIONAL {{ ?person wdt:P27 ?nationality }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
}}
ORDER BY ?personLabel
LIMIT 5000
"""


def _build_query(country_qid: str, since: Optional[str] = None) -> str:
    """Build SPARQL query to fetch politicians for a country.

    Returns people who hold/held positions (P39) in institutions
    tied to the given country (P17). Includes position start/end dates,
    date of birth (P569), date of death (P570), and party affiliation (P102).

    Args:
        country_qid: Wikidata QID for the country.
        since: Optional ISO date string (e.g. ``"2024-01-15"``).  When
            provided an extra ``FILTER`` restricts results to items whose
            Wikidata revision timestamp (``schema:dateModified``) is after
            this date, enabling incremental scraping.
    """
    modified_filter = ""
    if since:
        modified_filter = (
            f'  ?person schema:dateModified ?modified .\n'
            f'  FILTER(?modified >= "{since}T00:00:00Z"^^xsd:dateTime)\n'
        )
    return f"""
SELECT DISTINCT ?person ?personLabel ?positionLabel ?institutionLabel
       ?start ?end ?dob ?dod ?partyLabel WHERE {{
  ?person wdt:P39 ?position .
  ?position wdt:P17 wd:{country_qid} .
{modified_filter}  OPTIONAL {{
    ?person p:P39 ?stmt .
    ?stmt ps:P39 ?position .
    OPTIONAL {{ ?stmt pq:P580 ?start }}
    OPTIONAL {{ ?stmt pq:P582 ?end }}
  }}
  OPTIONAL {{ ?position wdt:P361 ?institution }}
  OPTIONAL {{ ?person wdt:P569 ?dob }}
  OPTIONAL {{ ?person wdt:P570 ?dod }}
  OPTIONAL {{ ?person wdt:P102 ?party }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
}}
ORDER BY ?personLabel
LIMIT 10000
"""


class WikidataScraper(BaseScraper):
    """Scraper that pulls PEP data from Wikidata's SPARQL endpoint."""

    source_type = "WIKIDATA"

    def __init__(self, country_code: str, since: Optional[str] = None):
        """
        Args:
            country_code: ISO 3166-1 alpha-2 country code.
            since: Optional ISO date (``"YYYY-MM-DD"``).  When supplied the
                SPARQL query includes a ``schema:dateModified`` filter so
                that only items modified after this date are returned
                (incremental scraping).
        """
        super().__init__()
        self.country_code = country_code.upper()
        self.since = since
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
        records = self._query_sparql()
        log.info(
            "wikidata.scrape.complete",
            country=self.country_code,
            record_count=len(records),
        )
        return records

    def _query_sparql(self) -> List[RawPersonRecord]:
        """Execute SPARQL query and parse results into records."""
        query = _build_query(self._country_qid, since=self.since)
        now = datetime.now(timezone.utc)

        # Use BaseScraper._get() for retry logic and rate limiting
        encoded_params = requests.compat.urlencode(  # type: ignore[attr-defined]
            {"query": query, "format": "json"}
        )
        url = f"{SPARQL_ENDPOINT}?{encoded_params}"
        self.session.headers["Accept"] = "application/json"
        resp = self._get(url)
        data = resp.json()

        records: List[RawPersonRecord] = []
        seen: set = set()

        for binding in data.get("results", {}).get("bindings", []):
            name = binding.get("personLabel", {}).get("value", "")
            position = binding.get("positionLabel", {}).get("value", "")
            institution = binding.get("institutionLabel", {}).get("value", "")

            # Extract Wikidata QID from the person URI
            person_uri = binding.get("person", {}).get("value", "")
            wikidata_qid = person_uri.split("/")[-1] if person_uri else ""

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
            date_of_birth = _parse_date(binding.get("dob", {}).get("value"))
            date_of_death = _parse_date(binding.get("dod", {}).get("value"))
            party = binding.get("partyLabel", {}).get("value", "")
            # Skip QID-only party labels
            if party.startswith("Q"):
                party = ""

            # Determine is_current: not current if position has ended,
            # or if the person has died (historical figures)
            is_current = _determine_is_current(
                end_date=end_date,
                date_of_death=date_of_death,
                start_date=start_date,
            )

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
                        "date_of_birth": date_of_birth,
                        "date_of_death": date_of_death,
                        "party": party,
                        "wikidata_qid": wikidata_qid,
                        "wikidata_country_qid": self._country_qid,
                    },
                )
            )

        return records

def _parse_date(value: Optional[str]) -> Optional[str]:
    """Parse Wikidata date string to ISO format."""
    if not value:
        return None
    try:
        # Wikidata dates look like "2023-05-29T00:00:00Z"
        return value[:10]
    except (IndexError, TypeError):
        return None


def _determine_is_current(
    end_date: Optional[str],
    date_of_death: Optional[str],
    start_date: Optional[str],
) -> bool:
    """Determine if a position is currently held.

    A position is NOT current if:
    - It has an explicit end date, OR
    - The person has died (date_of_death is set), OR
    - The start date is very old (before 1900) with no other signals,
      indicating a historical figure.
    """
    # Explicit end date means position has ended
    if end_date is not None:
        return False

    # Deceased persons cannot currently hold positions
    if date_of_death is not None:
        return False

    # Historical figures: positions starting before 1900 without end dates
    # are almost certainly not current
    if start_date is not None:
        try:
            year = int(start_date[:4])
            if year < 1900:
                return False
        except (ValueError, IndexError):
            pass

    return True


class _RegionalHelper(BaseScraper):
    """Minimal BaseScraper subclass used only to access _get() with retry."""
    source_type = "WIKIDATA"

    def scrape(self) -> List[RawPersonRecord]:
        return []  # pragma: no cover


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


def _build_relationships_query(country_qid: str) -> str:
    """Build SPARQL query to fetch family/associate relationships for PEPs.

    Fetches spouse (P26), father (P22), mother (P25), child (P40),
    and sibling (P3373) relationships.
    """
    return f"""
SELECT DISTINCT ?person ?personLabel ?relatedLabel ?relType WHERE {{
  ?person wdt:P39 ?position .
  ?position wdt:P17 wd:{country_qid} .
  {{
    ?person wdt:P26 ?related .
    BIND("SPOUSE" AS ?relType)
  }} UNION {{
    ?person wdt:P22 ?related .
    BIND("FATHER" AS ?relType)
  }} UNION {{
    ?person wdt:P25 ?related .
    BIND("MOTHER" AS ?relType)
  }} UNION {{
    ?person wdt:P40 ?related .
    BIND("CHILD" AS ?relType)
  }} UNION {{
    ?person wdt:P3373 ?related .
    BIND("SIBLING" AS ?relType)
  }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
}}
ORDER BY ?personLabel
LIMIT 10000
"""


@dataclass
class WikidataRelationship:
    """A family/associate relationship extracted from Wikidata."""
    person_qid: str
    person_name: str
    related_name: str
    relationship_type: str


def scrape_relationships(country_code: str) -> List[WikidataRelationship]:
    """Scrape family relationships for PEPs from a given country."""
    country_code = country_code.upper()
    qid = COUNTRY_QIDS.get(country_code)
    if not qid:
        return []

    query = _build_relationships_query(qid)
    helper = _RegionalHelper()

    encoded_params = requests.compat.urlencode(  # type: ignore[attr-defined]
        {"query": query, "format": "json"}
    )
    url = f"{SPARQL_ENDPOINT}?{encoded_params}"
    helper.session.headers["Accept"] = "application/json"

    try:
        resp = helper._get(url)
        data = resp.json()
    except Exception as exc:
        log.error("wikidata.relationships.failed", country=country_code, error=str(exc))
        return []

    relationships: List[WikidataRelationship] = []
    seen: set = set()

    for binding in data.get("results", {}).get("bindings", []):
        person_name = binding.get("personLabel", {}).get("value", "")
        related_name = binding.get("relatedLabel", {}).get("value", "")
        rel_type = binding.get("relType", {}).get("value", "")
        person_uri = binding.get("person", {}).get("value", "")
        person_qid = person_uri.split("/")[-1] if person_uri else ""

        if not person_name or person_name.startswith("Q"):
            continue
        if not related_name or related_name.startswith("Q"):
            continue

        key = (person_qid, related_name.lower(), rel_type)
        if key in seen:
            continue
        seen.add(key)

        relationships.append(WikidataRelationship(
            person_qid=person_qid,
            person_name=person_name,
            related_name=related_name,
            relationship_type=rel_type,
        ))

    log.info("wikidata.relationships.done", country=country_code,
             count=len(relationships))
    return relationships


def scrape_regional_bodies() -> Dict[str, List[RawPersonRecord]]:
    """Scrape PEP data for AU, ECOWAS, SADC, EAC regional body officials.

    Returns a dict keyed by org code (e.g. "AU", "ECOWAS").
    """
    results: Dict[str, List[RawPersonRecord]] = {}

    # Use a lightweight BaseScraper-derived helper for _get() retry/rate-limiting
    helper = _RegionalHelper()

    for org_code, org_qid in sorted(REGIONAL_BODY_QIDS.items()):
        log.info("wikidata.regional.start", org=org_code, qid=org_qid)
        try:
            query = _build_regional_query(org_qid)
            now = datetime.now(timezone.utc)

            encoded_params = requests.compat.urlencode(  # type: ignore[attr-defined]
                {"query": query, "format": "json"}
            )
            url = f"{SPARQL_ENDPOINT}?{encoded_params}"
            helper.session.headers["Accept"] = "application/json"
            resp = helper._get(url)
            data = resp.json()

            records: List[RawPersonRecord] = []
            seen: set = set()

            for binding in data.get("results", {}).get("bindings", []):
                name = binding.get("personLabel", {}).get("value", "")
                position = binding.get("positionLabel", {}).get("value", "")

                # Extract Wikidata QID from the person URI
                person_uri = binding.get("person", {}).get("value", "")
                wikidata_qid = person_uri.split("/")[-1] if person_uri else ""

                if not name or name.startswith("Q") or not position:
                    continue

                key = (name.lower(), position.lower())
                if key in seen:
                    continue
                seen.add(key)

                start_date = _parse_date(binding.get("start", {}).get("value"))
                end_date = _parse_date(binding.get("end", {}).get("value"))
                date_of_birth = _parse_date(binding.get("dob", {}).get("value"))
                date_of_death = _parse_date(binding.get("dod", {}).get("value"))
                party = binding.get("partyLabel", {}).get("value", "")
                if party.startswith("Q"):
                    party = ""
                nationality = binding.get("nationalityLabel", {}).get("value", "")
                if nationality.startswith("Q"):
                    nationality = ""

                is_current = _determine_is_current(
                    end_date=end_date,
                    date_of_death=date_of_death,
                    start_date=start_date,
                )

                records.append(
                    RawPersonRecord(
                        full_name=name,
                        title=position,
                        institution=org_code,
                        country_code=nationality or org_code,
                        source_url=f"https://www.wikidata.org/wiki/{org_qid}",
                        source_type="WIKIDATA",
                        raw_text=f"{name} - {position} ({org_code})",
                        scraped_at=now,
                        extra_fields={
                            "start_date": start_date,
                            "end_date": end_date,
                            "is_current": is_current,
                            "date_of_birth": date_of_birth,
                            "date_of_death": date_of_death,
                            "party": party,
                            "wikidata_qid": wikidata_qid,
                            "regional_body": org_code,
                            "wikidata_org_qid": org_qid,
                        },
                    )
                )

            results[org_code] = records
            log.info("wikidata.regional.done", org=org_code, count=len(records))
        except Exception as exc:
            log.error("wikidata.regional.failed", org=org_code, error=str(exc))
            results[org_code] = []

        time.sleep(2)

    return results
