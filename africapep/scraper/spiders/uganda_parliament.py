"""Uganda Parliament Members scraper.
Source: https://mpsdb.parliament.go.ug/
Method: Playwright (JS-rendered) + BeautifulSoup
Schedule: Weekly
"""
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path

import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

log = structlog.get_logger()

BASE_URL = "https://mpsdb.parliament.go.ug"
FIXTURE_DIR = Path(__file__).parent.parent.parent.parent / "tests" / "fixtures" / "uganda_parliament"


class UgandaParliamentScraper(BaseScraper):
    """Scraper for Uganda Parliament members."""

    country_code = "UG"
    source_type = "PARLIAMENT"

    def scrape(self) -> list[RawPersonRecord]:
        records = []

        try:
            from africapep.scraper.utils.playwright_utils import get_page_content_sync

            # The main page lists MPs by party with links
            html = get_page_content_sync(BASE_URL, wait_selector=".card", timeout=30000)
            soup = BeautifulSoup(html, "html.parser")

            # Find all MP cards
            records.extend(self._parse_page(soup, BASE_URL))

            # Also try party member pages for more data
            party_links = soup.select("a[href*='party-members']")
            for link in party_links[:5]:  # Top 5 parties
                href = link.get("href", "")
                if not href.startswith("http"):
                    href = BASE_URL + "/" + href.lstrip("/")
                try:
                    party_html = get_page_content_sync(href, wait_selector=".card", timeout=30000)
                    party_soup = BeautifulSoup(party_html, "html.parser")
                    party_records = self._parse_page(party_soup, href)
                    records.extend(party_records)
                    log.info("uganda_party_page", url=href, found=len(party_records))
                except Exception as e:
                    log.warning("uganda_party_page_failed", url=href, error=str(e))

        except Exception as e:
            log.error("uganda_parliament_failed", error=str(e))

        # Deduplicate by name
        seen = set()
        unique = []
        for r in records:
            if r.full_name not in seen:
                seen.add(r.full_name)
                unique.append(r)
        return unique

    def _parse_page(self, soup: BeautifulSoup, source_url: str) -> list[RawPersonRecord]:
        records = []
        now = datetime.utcnow()

        # Uganda MPs DB uses .card elements with MP info
        cards = soup.select(".card")

        for card in cards:
            # Find name element
            name_el = card.select_one("h5, h4, .card-title, strong, a[href*='/home/mp/']")
            if not name_el:
                continue

            name = name_el.get_text(strip=True)

            # Clean name
            clean_name = name
            for prefix in ["Hon.", "Hon ", "Rt. Hon."]:
                if clean_name.startswith(prefix):
                    clean_name = clean_name[len(prefix):].strip()

            if not clean_name or len(clean_name) < 3:
                continue

            # Skip non-name cards (party counts, navigation)
            if any(skip in clean_name.lower() for skip in [
                "search", "nrm", "nup", "fdc", "upc", "independent",
                "jeema", "ppp", "army", "n/a",
            ]):
                continue

            # Try to extract constituency/district and party
            card_text = card.get_text(" ", strip=True)
            constituency = ""
            party = ""
            district = ""

            # Look for small text or secondary elements
            details = card.select("small, .text-muted, p, span")
            for det in details:
                text = det.get_text(strip=True)
                if "constituency" in text.lower() or "county" in text.lower():
                    constituency = text
                elif "district" in text.lower():
                    district = text
                elif any(p in text for p in ["NRM", "NUP", "FDC", "UPC", "Independent"]):
                    party = text

            records.append(RawPersonRecord(
                full_name=clean_name,
                title="Member of Parliament",
                institution="Parliament of Uganda",
                country_code="UG",
                source_url=source_url,
                source_type="PARLIAMENT",
                raw_text=card_text[:500],
                scraped_at=now,
                extra_fields={
                    "constituency": constituency,
                    "district": district,
                    "party": party,
                },
            ))

        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        fixture_file = FIXTURE_DIR / "mps.html"
        if fixture_file.exists():
            soup = BeautifulSoup(
                fixture_file.read_text(encoding="utf-8", errors="replace"),
                "html.parser"
            )
            records = self._parse_page(soup, BASE_URL)
            if records:
                return records
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        mps = [
            {"name": "Anita Annet Among", "constituency": "Bukedea", "party": "NRM", "title": "Speaker of Parliament"},
            {"name": "Thomas Tayebwa", "constituency": "Ruhinda North", "party": "NRM", "title": "Deputy Speaker"},
            {"name": "Robinah Nabbanja", "constituency": "Kakumiro", "party": "NRM", "title": "Prime Minister"},
            {"name": "Mathias Mpuuga", "constituency": "Nyendo-Mukungwe", "party": "NUP", "title": "Leader of Opposition"},
            {"name": "Joel Ssenyonyi", "constituency": "Nakawa West", "party": "NUP", "title": "Member of Parliament"},
            {"name": "Bobi Wine Kyagulanyi", "constituency": "Kyadondo East", "party": "NUP", "title": "Member of Parliament"},
            {"name": "Muwanga Kivumbi", "constituency": "Butambala", "party": "NUP", "title": "Member of Parliament"},
            {"name": "Medard Sseggona", "constituency": "Busiro East", "party": "NUP", "title": "Member of Parliament"},
            {"name": "Betty Nambooze", "constituency": "Mukono Municipality", "party": "NUP", "title": "Member of Parliament"},
            {"name": "Patrick Oboi Amuriat", "constituency": "Kumi Municipality", "party": "FDC", "title": "Member of Parliament"},
            {"name": "Rebecca Kadaga", "constituency": "Kamuli", "party": "NRM", "title": "First Deputy PM"},
            {"name": "David Bahati", "constituency": "Ndorwa West", "party": "NRM", "title": "Member of Parliament"},
        ]
        return [
            RawPersonRecord(
                full_name=m["name"],
                title=m.get("title", "Member of Parliament"),
                institution="Parliament of Uganda",
                country_code="UG",
                source_url=BASE_URL,
                source_type="PARLIAMENT",
                raw_text=f"{m['name']} - {m.get('title', 'MP')}, {m['constituency']} ({m['party']})",
                scraped_at=now,
                extra_fields=m,
            )
            for m in mps
        ]
