"""
Scraper for the Kenya National Assembly members list.

Source: http://www.parliament.go.ke/the-national-assembly/mps
Method: BeautifulSoup (static HTML)
Extracts: MP name, county, party
"""

from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path

import requests
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)


class KenyaParliamentScraper(BaseScraper):
    """Scraper for Kenya National Assembly MPs."""

    country_code = "KE"
    source_type = "PARLIAMENT"

    SOURCE_URL = "http://www.parliament.go.ke/the-national-assembly/mps"
    FIXTURE_PATH = Path(__file__).parent / "fixtures" / "kenya_parliament.html"

    def scrape(self) -> list[RawPersonRecord]:
        """Scrape the Kenya Parliament website for current MPs.

        Returns:
            List of RawPersonRecord objects containing MP data.
        """
        logger.info(
            "scraper.kenya_parliament.start",
            url=self.SOURCE_URL,
            country_code=self.country_code,
        )

        try:
            response = requests.get(self.SOURCE_URL, timeout=30)
            response.raise_for_status()
            html = response.text
        except requests.RequestException as exc:
            logger.error(
                "scraper.kenya_parliament.fetch_failed",
                url=self.SOURCE_URL,
                error=str(exc),
            )
            raise

        return self._parse_html(html)

    def _parse_html(self, html: str) -> list[RawPersonRecord]:
        """Parse the HTML content and extract MP records.

        Args:
            html: Raw HTML string from the parliament page.

        Returns:
            List of RawPersonRecord objects.
        """
        soup = BeautifulSoup(html, "html.parser")
        records: list[RawPersonRecord] = []
        now = datetime.utcnow().isoformat()

        # The parliament site lists MPs in table rows or card-style divs.
        # We look for common patterns: tables with MP data or repeated div structures.
        table = soup.find("table")
        if table:
            rows = table.find_all("tr")[1:]  # skip header row
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 3:
                    name = cols[0].get_text(strip=True)
                    county = cols[1].get_text(strip=True)
                    party = cols[2].get_text(strip=True)

                    if not name:
                        continue

                    records.append(
                        RawPersonRecord(
                            full_name=name,
                            title="Member of Parliament",
                            institution="Parliament of Kenya",
                            country_code=self.country_code,
                            source_type=self.source_type,
                            source_url=self.SOURCE_URL,
                            raw_text=f"{name} – Member of Parliament, {county}",
                            scraped_at=now,
                            extra_fields={
                                "county": county,
                                "party": party,
                            },
                        )
                    )
        else:
            # Fallback: look for div-based listings with class patterns
            mp_cards = soup.select(".views-row, .mp-card, .member-item")
            for card in mp_cards:
                name_el = card.select_one(
                    ".views-field-title, .mp-name, .field-name, h3, h4"
                )
                county_el = card.select_one(
                    ".views-field-field-county, .mp-county, .field-county"
                )
                party_el = card.select_one(
                    ".views-field-field-party, .mp-party, .field-party"
                )

                name = name_el.get_text(strip=True) if name_el else ""
                county = county_el.get_text(strip=True) if county_el else ""
                party = party_el.get_text(strip=True) if party_el else ""

                if not name:
                    continue

                records.append(
                    RawPersonRecord(
                        full_name=name,
                        title="Member of Parliament",
                        institution="Parliament of Kenya",
                        country_code=self.country_code,
                        source_type=self.source_type,
                        source_url=self.SOURCE_URL,
                        raw_text=f"{name} – Member of Parliament, {county}",
                        scraped_at=now,
                        extra_fields={
                            "county": county,
                            "party": party,
                        },
                    )
                )

        logger.info(
            "scraper.kenya_parliament.complete",
            record_count=len(records),
        )
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        """Load fixture data for testing and development.

        If a fixture HTML file exists on disk, parse it. Otherwise,
        fall back to synthetic fixture data.

        Returns:
            List of RawPersonRecord objects from fixture data.
        """
        if self.FIXTURE_PATH.exists():
            logger.info(
                "scraper.kenya_parliament.loading_fixture",
                path=str(self.FIXTURE_PATH),
            )
            html = self.FIXTURE_PATH.read_text(encoding="utf-8")
            return self._parse_html(html)

        logger.info("scraper.kenya_parliament.using_synthetic_fixture")
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        """Generate synthetic fixture data with real Kenyan MP names.

        Returns:
            List of RawPersonRecord objects with realistic data.
        """
        now = datetime.utcnow().isoformat()

        mps = [
            {
                "name": "Moses Wetang'ula",
                "county": "Bungoma",
                "party": "Ford Kenya",
            },
            {
                "name": "Aden Duale",
                "county": "Garissa Township",
                "party": "United Democratic Alliance",
            },
            {
                "name": "Junet Mohamed",
                "county": "Suna East",
                "party": "Orange Democratic Movement",
            },
            {
                "name": "Kimani Ichung'wah",
                "county": "Kikuyu",
                "party": "United Democratic Alliance",
            },
            {
                "name": "Opiyo Wandayi",
                "county": "Ugunja",
                "party": "Orange Democratic Movement",
            },
            {
                "name": "Didmus Barasa",
                "county": "Kimilili",
                "party": "United Democratic Alliance",
            },
            {
                "name": "John Mbadi",
                "county": "Suba South",
                "party": "Orange Democratic Movement",
            },
            {
                "name": "Sabina Chege",
                "county": "Murang'a County",
                "party": "Jubilee Party",
            },
            {
                "name": "Babu Owino",
                "county": "Embakasi East",
                "party": "Orange Democratic Movement",
            },
            {
                "name": "Millie Odhiambo",
                "county": "Suba North",
                "party": "Orange Democratic Movement",
            },
            {
                "name": "Gladys Wanga",
                "county": "Homa Bay County",
                "party": "Orange Democratic Movement",
            },
            {
                "name": "Ndindi Nyoro",
                "county": "Kiharu",
                "party": "United Democratic Alliance",
            },
        ]

        records = []
        for mp in mps:
            records.append(
                RawPersonRecord(
                    full_name=mp["name"],
                    title="Member of Parliament",
                    institution="Parliament of Kenya",
                    country_code=self.country_code,
                    source_type=self.source_type,
                    source_url=self.SOURCE_URL,
                    raw_text=f"{mp['name']} – Member of Parliament, {mp['county']}",
                    scraped_at=now,
                    extra_fields={
                        "county": mp["county"],
                        "party": mp["party"],
                    },
                )
            )

        logger.info(
            "scraper.kenya_parliament.synthetic_fixture_loaded",
            record_count=len(records),
        )
        return records
