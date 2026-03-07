"""
Scraper for the Ghana Presidency cabinet page.

Source: https://presidency.gov.gh/members-of-the-cabinet/
Method: Playwright (JS-rendered) + BeautifulSoup HTML parsing
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import List

import structlog
from bs4 import BeautifulSoup

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord
from africapep.scraper.utils.playwright_utils import get_page_content_sync

logger = structlog.get_logger(__name__)

FIXTURE_DIR = Path(__file__).parent.parent.parent.parent / "tests" / "fixtures" / "ghana_parliament"

SOURCE_URL = "https://presidency.gov.gh/members-of-the-cabinet/"


class GhanaPresidencyScraper(BaseScraper):
    """Scrapes cabinet minister information from the Ghana Presidency website."""

    country_code = "GH"
    source_type = "PRESIDENCY"

    # ------------------------------------------------------------------ #
    #  Public interface
    # ------------------------------------------------------------------ #

    def scrape(self) -> List[RawPersonRecord]:
        """Fetch the cabinet page via Playwright and extract minister records."""
        logger.info(
            "ghana_presidency.scrape.start",
            url=SOURCE_URL,
        )
        try:
            html = get_page_content_sync(SOURCE_URL)
        except Exception:
            logger.exception(
                "ghana_presidency.scrape.playwright_error",
                url=SOURCE_URL,
            )
            return []

        records = self._parse_cabinet_html(html)
        logger.info(
            "ghana_presidency.scrape.complete",
            record_count=len(records),
        )
        return records

    # ------------------------------------------------------------------ #
    #  Parsing helpers
    # ------------------------------------------------------------------ #

    def _parse_cabinet_html(self, html: str) -> List[RawPersonRecord]:
        """Parse the raw HTML returned by Playwright and return person records."""
        soup = BeautifulSoup(html, "html.parser")
        records: List[RawPersonRecord] = []
        now = datetime.utcnow()

        # The cabinet page lists ministers in .member-i-title blocks,
        # each containing an <h3> (name) and <p> (portfolio/role).
        # Structure: .grid-item > .member-i > .member-i-main > .member-i-title
        minister_blocks = soup.select(".member-i-title")

        if not minister_blocks:
            # Fallback: try broader selectors in case the site layout changes
            logger.warning(
                "ghana_presidency.parse.no_blocks_found",
                hint="Primary selector .member-i-title failed, trying fallbacks",
            )
            minister_blocks = (
                soup.select(".member-i-main")
                or soup.select(".member-i")
                or soup.select("div.card")
            )

        for block in minister_blocks:
            try:
                name_tag = (
                    block.select_one("h3")
                    or block.select_one("h2")
                    or block.select_one("h4")
                    or block.select_one("strong")
                )
                if not name_tag:
                    continue

                name = " ".join(name_tag.get_text(strip=True).split())
                if not name:
                    continue

                # Portfolio / role – the <p> sibling inside .member-i-title
                portfolio_tag = block.select_one("p")
                portfolio = " ".join(portfolio_tag.get_text(strip=True).split()) if portfolio_tag else ""

                # Attempt to extract an appointment date if present
                date_appointed = self._extract_date(block.get_text(" ", strip=True))

                records.append(
                    RawPersonRecord(
                        full_name=name,
                        title=portfolio,
                        institution="Office of the President of Ghana",
                        country_code=self.country_code,
                        source_url=SOURCE_URL,
                        source_type=self.source_type,
                        raw_text=f"{name} – {portfolio}",
                        scraped_at=now,
                        extra_fields={
                            "date_appointed": date_appointed,
                        },
                    )
                )
            except Exception:
                logger.exception("ghana_presidency.parse.block_error")
                continue

        return records

    @staticmethod
    def _extract_date(text: str) -> str | None:
        """Try to pull a date string (e.g. '7 January 2025') from free text."""
        match = re.search(
            r"(\d{1,2}\s+(?:January|February|March|April|May|June|July|"
            r"August|September|October|November|December)\s+\d{4})",
            text,
            re.IGNORECASE,
        )
        return match.group(1) if match else None

    # ------------------------------------------------------------------ #
    #  Fixtures
    # ------------------------------------------------------------------ #

    def _load_fixture(self) -> List[RawPersonRecord]:
        """Return synthetic fixture data for testing."""
        return self._synthetic_fixture()

    @staticmethod
    def _synthetic_fixture() -> List[RawPersonRecord]:
        """Realistic synthetic cabinet data using real Ghana minister names."""
        now = datetime.utcnow()
        ministers = [
            ("John Dramani Mahama", "President of the Republic of Ghana", "7 January 2025"),
            ("Naana Jane Opoku-Agyemang", "Vice President of the Republic of Ghana", "7 January 2025"),
            ("Dr Cassiel Ato Forson", "Minister for Finance", "7 January 2025"),
            ("John Abdulai Jinapor", "Minister for Energy", "7 January 2025"),
            ("Edward Omane Boamah", "Minister for Defence", "7 January 2025"),
            ("Alhaji Inusah Fuseini", "Minister for the Interior", "7 January 2025"),
            ("Dr Dominic Ayine", "Attorney-General and Minister for Justice", "7 January 2025"),
            ("Ibrahim Mohammed Awal", "Minister for Trade and Industry", "7 January 2025"),
            ("Samuel Okudzeto Ablakwa", "Minister for Foreign Affairs", "7 January 2025"),
            ("Dr Zanetor Agyeman-Rawlings", "Minister for Health", "7 January 2025"),
        ]
        return [
            RawPersonRecord(
                full_name=name,
                title=portfolio,
                institution="Office of the President of Ghana",
                country_code="GH",
                source_url=SOURCE_URL,
                source_type="PRESIDENCY",
                raw_text=f"{name} – {portfolio}",
                scraped_at=now,
                extra_fields={
                    "date_appointed": date,
                },
            )
            for name, portfolio, date in ministers
        ]
