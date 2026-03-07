"""
Scraper for the South Africa Parliament members list.

Source: https://www.parliament.gov.za/mps
Method: Playwright (JS-rendered) + BeautifulSoup parsing
Extracts: MP name, party, province, portfolio committee
"""

from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path

import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord
from africapep.scraper.utils.playwright_utils import get_page_content_sync

logger = structlog.get_logger(__name__)


class SouthAfricaParliamentScraper(BaseScraper):
    """Scraper for South Africa National Assembly MPs."""

    country_code = "ZA"
    source_type = "PARLIAMENT"

    SOURCE_URL = "https://www.parliament.gov.za/mps"
    FIXTURE_PATH = Path(__file__).parent / "fixtures" / "southafrica_parliament.html"

    def scrape(self) -> list[RawPersonRecord]:
        """Scrape the South Africa Parliament website for current MPs.

        Uses Playwright to render JavaScript content, then parses the
        resulting HTML with BeautifulSoup.

        Returns:
            List of RawPersonRecord objects containing MP data.
        """
        logger.info(
            "scraper.southafrica_parliament.start",
            url=self.SOURCE_URL,
            country_code=self.country_code,
        )

        try:
            html = get_page_content_sync(self.SOURCE_URL)
        except Exception as exc:
            logger.error(
                "scraper.southafrica_parliament.fetch_failed",
                url=self.SOURCE_URL,
                error=str(exc),
            )
            raise

        return self._parse_html(html)

    def _parse_html(self, html: str) -> list[RawPersonRecord]:
        """Parse the rendered HTML content and extract MP records.

        Args:
            html: Rendered HTML string from the parliament page.

        Returns:
            List of RawPersonRecord objects.
        """
        soup = BeautifulSoup(html, "html.parser")
        records: list[RawPersonRecord] = []
        now = datetime.utcnow().isoformat()

        # The SA Parliament site uses JS-rendered cards/tables for MP listings.
        # Try table-based layout first.
        table = soup.find("table")
        if table:
            rows = table.find_all("tr")[1:]  # skip header
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 3:
                    name = cols[0].get_text(strip=True)
                    party = cols[1].get_text(strip=True)
                    province = cols[2].get_text(strip=True) if len(cols) > 2 else ""
                    committee = cols[3].get_text(strip=True) if len(cols) > 3 else ""

                    if not name:
                        continue

                    records.append(
                        RawPersonRecord(
                            full_name=name,
                            title="Member of Parliament",
                            institution="Parliament of South Africa",
                            country_code=self.country_code,
                            source_type=self.source_type,
                            source_url=self.SOURCE_URL,
                            raw_text=f"{name} – Member of Parliament, {party}",
                            scraped_at=now,
                            extra_fields={
                                "party": party,
                                "province": province,
                                "portfolio_committee": committee,
                            },
                        )
                    )
        else:
            # Fallback: card/div-based layout
            mp_cards = soup.select(
                ".member-card, .mp-item, .views-row, .member-profile, .mp-listing-item"
            )
            for card in mp_cards:
                name_el = card.select_one(
                    ".member-name, .mp-name, .field-name, h3, h4, .title"
                )
                party_el = card.select_one(
                    ".member-party, .mp-party, .field-party, .party"
                )
                province_el = card.select_one(
                    ".member-province, .mp-province, .field-province, .province"
                )
                committee_el = card.select_one(
                    ".member-committee, .mp-committee, .field-committee, .portfolio"
                )

                name = name_el.get_text(strip=True) if name_el else ""
                party = party_el.get_text(strip=True) if party_el else ""
                province = province_el.get_text(strip=True) if province_el else ""
                committee = committee_el.get_text(strip=True) if committee_el else ""

                if not name:
                    continue

                records.append(
                    RawPersonRecord(
                        full_name=name,
                        title="Member of Parliament",
                        institution="Parliament of South Africa",
                        country_code=self.country_code,
                        source_type=self.source_type,
                        source_url=self.SOURCE_URL,
                        raw_text=f"{name} – Member of Parliament, {party}",
                        scraped_at=now,
                        extra_fields={
                            "party": party,
                            "province": province,
                            "portfolio_committee": committee,
                        },
                    )
                )

        logger.info(
            "scraper.southafrica_parliament.complete",
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
                "scraper.southafrica_parliament.loading_fixture",
                path=str(self.FIXTURE_PATH),
            )
            html = self.FIXTURE_PATH.read_text(encoding="utf-8")
            return self._parse_html(html)

        logger.info("scraper.southafrica_parliament.using_synthetic_fixture")
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        """Generate synthetic fixture data with real South African MP names.

        Returns:
            List of RawPersonRecord objects with realistic data.
        """
        now = datetime.utcnow().isoformat()

        mps = [
            {
                "name": "Cyril Ramaphosa",
                "party": "African National Congress",
                "province": "Gauteng",
                "committee": "Joint Standing Committee on Defence",
            },
            {
                "name": "John Steenhuisen",
                "party": "Democratic Alliance",
                "province": "KwaZulu-Natal",
                "committee": "Portfolio Committee on Agriculture",
            },
            {
                "name": "Julius Malema",
                "party": "Economic Freedom Fighters",
                "province": "Limpopo",
                "committee": "",
            },
            {
                "name": "Mmusi Maimane",
                "party": "Build One South Africa",
                "province": "Gauteng",
                "committee": "",
            },
            {
                "name": "Naledi Pandor",
                "party": "African National Congress",
                "province": "Gauteng",
                "committee": "Portfolio Committee on International Relations",
            },
            {
                "name": "Angie Motshekga",
                "party": "African National Congress",
                "province": "Gauteng",
                "committee": "Portfolio Committee on Basic Education",
            },
            {
                "name": "Pieter Groenewald",
                "party": "Freedom Front Plus",
                "province": "North West",
                "committee": "Portfolio Committee on Police",
            },
            {
                "name": "Bantu Holomisa",
                "party": "United Democratic Movement",
                "province": "Eastern Cape",
                "committee": "Portfolio Committee on Defence and Military Veterans",
            },
            {
                "name": "Mangosuthu Buthelezi",
                "party": "Inkatha Freedom Party",
                "province": "KwaZulu-Natal",
                "committee": "",
            },
            {
                "name": "Nkosazana Dlamini-Zuma",
                "party": "African National Congress",
                "province": "KwaZulu-Natal",
                "committee": "Portfolio Committee on Cooperative Governance",
            },
            {
                "name": "Gwede Mantashe",
                "party": "African National Congress",
                "province": "Eastern Cape",
                "committee": "Portfolio Committee on Mineral Resources and Energy",
            },
            {
                "name": "Lindiwe Sisulu",
                "party": "African National Congress",
                "province": "Gauteng",
                "committee": "Portfolio Committee on Human Settlements",
            },
        ]

        records = []
        for mp in mps:
            records.append(
                RawPersonRecord(
                    full_name=mp["name"],
                    title="Member of Parliament",
                    institution="Parliament of South Africa",
                    country_code=self.country_code,
                    source_type=self.source_type,
                    source_url=self.SOURCE_URL,
                    raw_text=f"{mp['name']} – Member of Parliament, {mp['party']}",
                    scraped_at=now,
                    extra_fields={
                        "party": mp["party"],
                        "province": mp["province"],
                        "portfolio_committee": mp["committee"],
                    },
                )
            )

        logger.info(
            "scraper.southafrica_parliament.synthetic_fixture_loaded",
            record_count=len(records),
        )
        return records
