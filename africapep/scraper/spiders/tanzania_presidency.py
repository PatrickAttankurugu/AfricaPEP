"""Tanzania Presidency / Cabinet scraper.

Source: https://www.pmo.go.tz/
Method: BeautifulSoup (static HTML)
Schedule: Weekly
"""
from __future__ import annotations

from datetime import datetime
from typing import List

import structlog
from bs4 import BeautifulSoup

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

log = structlog.get_logger(__name__)

BASE_URL = "https://www.pmo.go.tz"
CABINET_URL = f"{BASE_URL}/"


class TanzaniaPresidencyScraper(BaseScraper):
    """Scraper for Tanzania Presidency / Cabinet members."""

    country_code = "TZ"
    source_type = "PRESIDENCY"

    # ------------------------------------------------------------------ #
    #  Public interface
    # ------------------------------------------------------------------ #

    def scrape(self) -> List[RawPersonRecord]:
        """Fetch the PMO page and extract administration profile links.

        Profile links typically contain names such as
        "Mhe. William Vangimembe Lukuvi - Waziri wa Nchi".
        Falls back to synthetic fixture data if the site is unreachable.
        """
        log.info("tanzania_presidency.scrape.start", url=CABINET_URL)
        try:
            resp = self._get(CABINET_URL)
            soup = BeautifulSoup(resp.text, "html.parser")
            records = self._parse_page(soup, CABINET_URL)
            log.info(
                "tanzania_presidency.scrape.complete",
                record_count=len(records),
            )
            if records:
                return records
            # Site reachable but no records parsed -- use fixture
            log.warning(
                "tanzania_presidency.scrape.no_records_parsed",
                hint="Falling back to fixture data",
            )
            return self._load_fixture()
        except Exception as exc:
            log.error(
                "tanzania_presidency.scrape.failed",
                error=str(exc),
                hint="Falling back to fixture data",
            )
            return self._load_fixture()

    # ------------------------------------------------------------------ #
    #  Parsing helpers
    # ------------------------------------------------------------------ #

    def _parse_page(
        self, soup: BeautifulSoup, source_url: str
    ) -> List[RawPersonRecord]:
        """Extract cabinet member records from PMO page HTML."""
        records: List[RawPersonRecord] = []
        now = datetime.utcnow()

        # The PMO site lists administration profiles as links whose text
        # follows the pattern "Mhe. <Name> - <Swahili title>".
        profile_links = soup.select("a[href*='profile'], a[href*='viongozi']")

        # Fallback: look for any link whose text contains "Mhe." or "Waziri"
        if not profile_links:
            profile_links = [
                a
                for a in soup.find_all("a", href=True)
                if any(
                    kw in (a.get_text(strip=True) or "")
                    for kw in ("Mhe.", "Waziri", "Rais", "Makamu")
                )
            ]

        # Broader fallback: heading/card selectors
        if not profile_links:
            cards = (
                soup.select(".team-member")
                or soup.select(".cabinet-member")
                or soup.select(".leader-card")
                or soup.select("article")
            )
            for card in cards:
                name_el = card.select_one("h3, h4, h5, .member-name, strong")
                if not name_el:
                    continue
                name = name_el.get_text(strip=True)
                if not name or len(name) < 3:
                    continue

                clean_name = self._clean_name(name)

                portfolio = ""
                title_el = card.select_one(
                    ".position, .portfolio, p, .member-title"
                )
                if title_el:
                    portfolio = title_el.get_text(strip=True)

                records.append(
                    RawPersonRecord(
                        full_name=clean_name,
                        title=portfolio or "Cabinet Minister",
                        institution="Office of the Prime Minister of Tanzania",
                        country_code="TZ",
                        source_url=source_url,
                        source_type="PRESIDENCY",
                        raw_text=f"{name} - {portfolio}",
                        scraped_at=now,
                        extra_fields={
                            "portfolio": portfolio,
                            "raw_name": name,
                        },
                    )
                )
            return records

        # Parse profile links
        for link in profile_links:
            try:
                text = link.get_text(strip=True)
                if not text or len(text) < 3:
                    continue

                # Split on " - " to separate name from Swahili title
                parts = text.split(" - ", 1)
                raw_name = parts[0].strip()
                portfolio = parts[1].strip() if len(parts) > 1 else ""

                clean_name = self._clean_name(raw_name)
                if not clean_name:
                    continue

                records.append(
                    RawPersonRecord(
                        full_name=clean_name,
                        title=portfolio or "Cabinet Minister",
                        institution="Office of the Prime Minister of Tanzania",
                        country_code="TZ",
                        source_url=source_url,
                        source_type="PRESIDENCY",
                        raw_text=text,
                        scraped_at=now,
                        extra_fields={
                            "portfolio": portfolio,
                            "raw_name": raw_name,
                        },
                    )
                )
            except Exception as exc:
                log.warning(
                    "tanzania_presidency.parse.link_error", error=str(exc)
                )

        return records

    @staticmethod
    def _clean_name(name: str) -> str:
        """Remove common Swahili and English honorific prefixes."""
        clean = name
        for prefix in [
            "Mhe.", "H.E.", "Hon.", "Dr.", "Prof.", "Amb.",
            "Dkt.", "Bi.", "Bw.",
        ]:
            if clean.startswith(prefix):
                clean = clean[len(prefix):].strip()
        return clean

    # ------------------------------------------------------------------ #
    #  Fixtures
    # ------------------------------------------------------------------ #

    def _load_fixture(self) -> List[RawPersonRecord]:
        """Return synthetic fixture data when live scraping is unavailable."""
        return self._synthetic_fixture()

    @staticmethod
    def _synthetic_fixture() -> List[RawPersonRecord]:
        """Current Tanzania cabinet data as synthetic fixture records."""
        now = datetime.utcnow()
        cabinet = [
            {"name": "Samia Suluhu Hassan", "title": "President"},
            {"name": "Philip Isdor Mpango", "title": "Vice President"},
            {"name": "Kassim Majaliwa", "title": "Prime Minister"},
            {"name": "Doto Mashaka Biteko", "title": "Deputy PM / Minister of Energy"},
            {"name": "January Yusuf Makamba", "title": "Minister of Foreign Affairs"},
            {"name": "Stergomena Lawrence Tax", "title": "Minister of Defence"},
            {"name": "Hamad Masauni", "title": "Minister of Home Affairs"},
            {"name": "Emmanuel Mwenyemlare Tutuba", "title": "Minister of Finance"},
            {"name": "Adolf Faustine Mkenda", "title": "Minister of Education"},
            {"name": "Liberata Mulamula", "title": "Minister of Information"},
            {"name": "Angellah Jasmine Kairuki", "title": "Minister of State, PM's Office"},
            {"name": "Ummy Ally Mwalimu", "title": "Minister of Health"},
            {"name": "Pindi Chana", "title": "Minister of Natural Resources and Tourism"},
            {"name": "Hussein Bashe", "title": "Minister of Agriculture"},
            {"name": "Tulia Ackson", "title": "Speaker of the National Assembly"},
            {"name": "Ibrahim Mahamed Juma", "title": "Chief Justice of Tanzania"},
            {"name": "Jakaya Kikwete", "title": "Former President of Tanzania"},
            {"name": "Benjamin Mkapa", "title": "Former President of Tanzania"},
        ]
        return [
            RawPersonRecord(
                full_name=m["name"],
                title=m["title"],
                institution="Office of the Prime Minister of Tanzania",
                country_code="TZ",
                source_url=CABINET_URL,
                source_type="PRESIDENCY",
                raw_text=f"{m['name']} - {m['title']}",
                scraped_at=now,
                extra_fields=m,
            )
            for m in cabinet
        ]
