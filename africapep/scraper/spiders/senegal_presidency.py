"""
Scraper for the Senegal Presidency / Cabinet.

Source: https://www.presidence.sn/
Method: HTTP GET with fallback to synthetic fixture (site may be unreachable)
Schedule: Weekly
"""

from datetime import datetime
from typing import List

import structlog
from bs4 import BeautifulSoup

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

SOURCE_URL = "https://www.presidence.sn/"


class SenegalPresidencyScraper(BaseScraper):
    """Scraper for Senegal Presidency / Cabinet members."""

    country_code = "SN"
    source_type = "PRESIDENCY"

    # ------------------------------------------------------------------ #
    #  Public interface
    # ------------------------------------------------------------------ #

    def scrape(self) -> List[RawPersonRecord]:
        """Fetch the cabinet page and extract minister records.

        The Senegal presidency site may be unreachable, so we fall back
        to fixture data when the request fails.
        """
        logger.info("senegal_presidency.scrape.start", url=SOURCE_URL)
        try:
            resp = self._get(SOURCE_URL)
            soup = BeautifulSoup(resp.text, "html.parser")
            records = self._parse_cabinet_html(soup)
            if records:
                logger.info(
                    "senegal_presidency.scrape.complete",
                    record_count=len(records),
                )
                return records
            # Site returned HTML but no records could be parsed
            logger.warning(
                "senegal_presidency.scrape.no_records_parsed",
                hint="Falling back to fixture data",
            )
        except Exception:
            logger.exception(
                "senegal_presidency.scrape.error",
                url=SOURCE_URL,
                hint="Site unreachable, falling back to fixture data",
            )

        return self._load_fixture()

    # ------------------------------------------------------------------ #
    #  Parsing helpers
    # ------------------------------------------------------------------ #

    def _parse_cabinet_html(self, soup: BeautifulSoup) -> List[RawPersonRecord]:
        """Parse the raw HTML and return person records."""
        records: List[RawPersonRecord] = []
        now = datetime.utcnow()

        cards = (
            soup.select(".team-member")
            or soup.select(".cabinet-member")
            or soup.select(".member-item")
            or soup.select(".minister-card")
            or soup.select("article")
        )

        for card in cards:
            try:
                name_el = card.select_one("h3, h4, h2, .name, strong")
                if not name_el:
                    continue

                full_name = name_el.get_text(strip=True)
                if not full_name or len(full_name) < 3:
                    continue

                portfolio_el = card.select_one(".position, .role, .portfolio, p, span")
                portfolio = portfolio_el.get_text(strip=True) if portfolio_el else ""

                records.append(
                    RawPersonRecord(
                        full_name=full_name,
                        title=portfolio or "Cabinet Member",
                        institution="Presidency of the Republic of Senegal",
                        country_code=self.country_code,
                        source_url=SOURCE_URL,
                        source_type=self.source_type,
                        raw_text=f"{full_name} – {portfolio}",
                        scraped_at=now,
                        extra_fields={
                            "portfolio": portfolio,
                        },
                    )
                )
            except Exception:
                logger.exception("senegal_presidency.parse.block_error")

        return records

    # ------------------------------------------------------------------ #
    #  Fixtures
    # ------------------------------------------------------------------ #

    def _load_fixture(self) -> List[RawPersonRecord]:
        """Return synthetic fixture data for testing."""
        return self._synthetic_fixture()

    @staticmethod
    def _synthetic_fixture() -> List[RawPersonRecord]:
        """Realistic synthetic cabinet data using real Senegal cabinet members (since April 2024)."""
        now = datetime.utcnow()
        cabinet = [
            ("Bassirou Diomaye Faye", "President of the Republic of Senegal", "April 2024"),
            ("Ousmane Sonko", "Prime Minister", "April 2024"),
            ("Yassine Fall", "Minister of African Integration and Foreign Affairs", "April 2024"),
            ("Birame Diop", "Minister of Armed Forces", "April 2024"),
            ("Jean-Baptiste Tine", "Minister of Interior", "April 2024"),
            ("Cheikh Diba", "Minister of Finance and Budget", "April 2024"),
            ("Moustapha Sarr", "Minister of Justice", "April 2024"),
            ("Abdourahmane Diouf", "Minister of Higher Education", "April 2024"),
            ("Moustapha Guirassy", "Minister of National Education", "April 2024"),
            ("Ibrahima Sy", "Minister of Health", "April 2024"),
            ("Yankhoba Diemé", "Minister of Labour", "April 2024"),
            ("Mabouba Diagne", "Minister of Industry and Commerce", "April 2024"),
        ]
        return [
            RawPersonRecord(
                full_name=name,
                title=title,
                institution="Presidency of the Republic of Senegal",
                country_code="SN",
                source_url=SOURCE_URL,
                source_type="PRESIDENCY",
                raw_text=f"{name} – {title}",
                scraped_at=now,
                extra_fields={
                    "date_appointed": date,
                    "fixture": True,
                },
            )
            for name, title, date in cabinet
        ]
