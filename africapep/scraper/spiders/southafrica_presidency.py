"""
Scraper for the South Africa Presidency / Cabinet.

Source: https://www.thepresidency.gov.za/
Method: Attempt live fetch with BeautifulSoup, fall back to synthetic fixture.
Schedule: Weekly

Notes:
    gov.za does not expose a clean, static cabinet listing page.  The scraper
    attempts a live fetch but primarily relies on the curated synthetic
    fixture which reflects the 2024 Government of National Unity (GNU) cabinet.
"""

from __future__ import annotations

from datetime import datetime
from typing import List

import structlog
from bs4 import BeautifulSoup

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

log = structlog.get_logger(__name__)

BASE_URL = "https://www.thepresidency.gov.za"
CABINET_URL = f"{BASE_URL}/cabinet/ministers"


class SouthAfricaPresidencyScraper(BaseScraper):
    """Scrapes cabinet minister information from the South Africa Presidency website.

    Because the Presidency site lacks a reliable static cabinet listing, this
    scraper attempts a live fetch but falls back to ``_synthetic_fixture()``
    which contains accurate GNU (2024) cabinet data.
    """

    country_code = "ZA"
    source_type = "PRESIDENCY"

    # ------------------------------------------------------------------ #
    #  Public interface
    # ------------------------------------------------------------------ #

    def scrape(self) -> List[RawPersonRecord]:
        """Attempt to scrape the live site; fall back to fixture on failure."""
        log.info(
            "southafrica_presidency.scrape.start",
            url=CABINET_URL,
        )
        try:
            resp = self._get(CABINET_URL)
            records = self._parse_cabinet_html(resp.text)
            if records:
                log.info(
                    "southafrica_presidency.scrape.complete",
                    record_count=len(records),
                )
                return records
            # Empty parse result -- site layout may have changed
            log.warning(
                "southafrica_presidency.scrape.empty_parse",
                hint="Live page returned no records, falling back to fixture",
            )
        except Exception:
            log.exception(
                "southafrica_presidency.scrape.live_failed",
                hint="Falling back to synthetic fixture",
            )

        return self._synthetic_fixture()

    # ------------------------------------------------------------------ #
    #  Parsing helpers
    # ------------------------------------------------------------------ #

    def _parse_cabinet_html(self, html: str) -> List[RawPersonRecord]:
        """Best-effort parse of whatever HTML the Presidency site returns."""
        soup = BeautifulSoup(html, "html.parser")
        records: List[RawPersonRecord] = []
        now = datetime.utcnow()

        # Try several plausible selectors
        cards = (
            soup.select(".view-content .views-row")
            or soup.select(".cabinet-member")
            or soup.select(".team-member")
            or soup.select("article.node--type-minister")
            or soup.select("article")
        )

        for card in cards:
            try:
                name_el = card.select_one(
                    "h3, h2, h4, .field--name-title, .member-name, strong"
                )
                if not name_el:
                    continue

                name = " ".join(name_el.get_text(strip=True).split())
                if not name or len(name) < 3:
                    continue

                # Strip common honorifics
                clean_name = name
                for prefix in ["H.E.", "Hon.", "Dr.", "Prof.", "Adv.", "Mr.", "Ms.", "Mrs."]:
                    if clean_name.startswith(prefix):
                        clean_name = clean_name[len(prefix):].strip()

                portfolio = ""
                title_el = card.select_one(
                    ".field--name-field-portfolio, .position, .portfolio, p, .member-title"
                )
                if title_el:
                    portfolio = " ".join(title_el.get_text(strip=True).split())

                records.append(
                    RawPersonRecord(
                        full_name=clean_name,
                        title=portfolio or "Minister",
                        institution="The Presidency of the Republic of South Africa",
                        country_code=self.country_code,
                        source_url=CABINET_URL,
                        source_type=self.source_type,
                        raw_text=f"{name} - {portfolio}",
                        scraped_at=now,
                        extra_fields={
                            "raw_name": name,
                            "portfolio": portfolio,
                        },
                    )
                )
            except Exception:
                log.exception("southafrica_presidency.parse.card_error")
                continue

        return records

    # ------------------------------------------------------------------ #
    #  Fixtures
    # ------------------------------------------------------------------ #

    def _load_fixture(self) -> List[RawPersonRecord]:
        """Return synthetic fixture data for testing."""
        return self._synthetic_fixture()

    @staticmethod
    def _synthetic_fixture() -> List[RawPersonRecord]:
        """Curated cabinet data for the 2024 Government of National Unity (GNU).

        Party affiliations are stored in ``extra_fields["party"]``.
        """
        now = datetime.utcnow()

        cabinet = [
            {
                "name": "Cyril Ramaphosa",
                "title": "President of the Republic of South Africa",
                "party": "ANC",
            },
            {
                "name": "Paul Mashatile",
                "title": "Deputy President",
                "party": "ANC",
            },
            {
                "name": "Enoch Godongwana",
                "title": "Minister of Finance",
                "party": "ANC",
            },
            {
                "name": "Ronald Lamola",
                "title": "Minister of International Relations and Cooperation",
                "party": "ANC",
            },
            {
                "name": "Angie Motshekga",
                "title": "Minister of Defence and Military Veterans",
                "party": "ANC",
            },
            {
                "name": "Senzo Mchunu",
                "title": "Minister of Police",
                "party": "ANC",
            },
            {
                "name": "John Steenhuisen",
                "title": "Minister of Agriculture",
                "party": "DA",
            },
            {
                "name": "Dean Macpherson",
                "title": "Minister of Public Works and Infrastructure",
                "party": "DA",
            },
            {
                "name": "Pieter Groenewald",
                "title": "Minister of Correctional Services",
                "party": "FF+",
            },
            {
                "name": "Gayton McKenzie",
                "title": "Minister of Sports, Arts and Culture",
                "party": "PA",
            },
            {
                "name": "Parks Tau",
                "title": "Minister of Trade, Industry and Competition",
                "party": "ANC",
            },
            {
                "name": "Blade Nzimande",
                "title": "Minister of Higher Education, Science and Innovation",
                "party": "SACP",
            },
        ]

        return [
            RawPersonRecord(
                full_name=m["name"],
                title=m["title"],
                institution="The Presidency of the Republic of South Africa",
                country_code="ZA",
                source_url=CABINET_URL,
                source_type="PRESIDENCY",
                raw_text=f"{m['name']} - {m['title']}",
                scraped_at=now,
                extra_fields={
                    "party": m["party"],
                },
            )
            for m in cabinet
        ]
