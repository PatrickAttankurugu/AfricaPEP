"""Rwanda Chamber of Deputies scraper.
Source: https://www.parliament.gov.rw/chamber-of-deputies-2/member-profile/deputies-profiles
Method: BeautifulSoup (static HTML with pagination)
Schedule: Weekly
"""
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path

import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

log = structlog.get_logger()

BASE_URL = "https://www.parliament.gov.rw"
DEPUTIES_URL = f"{BASE_URL}/chamber-of-deputies-2/member-profile/deputies-profiles"
SENATORS_URL = f"{BASE_URL}/the-senate-2/member-profile/senators-profiles"
FIXTURE_DIR = Path(__file__).parent.parent.parent.parent / "tests" / "fixtures" / "rwanda_parliament"


class RwandaParliamentScraper(BaseScraper):
    """Scraper for Rwanda Parliament (Chamber of Deputies + Senate)."""

    country_code = "RW"
    source_type = "PARLIAMENT"

    def scrape(self) -> list[RawPersonRecord]:
        records = []

        # Scrape Chamber of Deputies
        records.extend(self._scrape_chamber(DEPUTIES_URL, "Chamber of Deputies"))

        # Scrape Senate
        records.extend(self._scrape_chamber(SENATORS_URL, "Senate"))

        return records

    def _scrape_chamber(self, base_url: str, chamber: str) -> list[RawPersonRecord]:
        records = []
        page = 1

        while True:
            url = f"{base_url}/page/{page}/" if page > 1 else base_url
            try:
                resp = self._get(url)
            except Exception as e:
                log.error("rwanda_parliament_request_failed", url=url, error=str(e))
                break

            soup = BeautifulSoup(resp.text, "html.parser")
            batch = self._parse_page(soup, url, chamber)

            if not batch:
                break

            records.extend(batch)
            log.info("rwanda_parliament_page", chamber=chamber, page=page, found=len(batch))

            # Check pagination
            next_link = soup.select_one(".next.page-numbers, a.next")
            if not next_link:
                break
            page += 1

        return records

    def _parse_page(self, soup: BeautifulSoup, source_url: str,
                    chamber: str) -> list[RawPersonRecord]:
        records = []
        now = datetime.utcnow()

        # Rwanda parliament uses h3 tags for deputy/senator names
        h3_elements = soup.select("h3")

        for h3 in h3_elements:
            name = h3.get_text(strip=True)
            if not name or len(name) < 4:
                continue

            # Skip non-name h3s (navigation, headers)
            if any(skip in name.lower() for skip in [
                "menu", "search", "home", "about", "committee",
                "legislation", "news", "contact", "parliament",
            ]):
                continue

            # Clean up name: remove "Hon." prefix, fix tabs
            clean_name = name.replace("\t", " ").strip()
            for prefix in ["Hon.", "Hon ", "Rt. Hon.", "H.E."]:
                if clean_name.startswith(prefix):
                    clean_name = clean_name[len(prefix):].strip()

            if not clean_name or len(clean_name) < 3:
                continue

            # Determine title based on chamber
            title = "Deputy" if chamber == "Chamber of Deputies" else "Senator"

            # Try to get additional info from parent/sibling elements
            party = ""
            parent = h3.parent
            if parent:
                parent_text = parent.get_text(" ", strip=True)
                # Look for party info in surrounding text
                for p_name in ["RPF", "PSD", "PL", "DGPR", "PSR"]:
                    if p_name in parent_text:
                        party = p_name
                        break

            records.append(RawPersonRecord(
                full_name=clean_name,
                title=title,
                institution=f"{chamber} of Rwanda",
                country_code="RW",
                source_url=source_url,
                source_type="PARLIAMENT",
                raw_text=f"{name} - {title}, {chamber} of Rwanda",
                scraped_at=now,
                extra_fields={
                    "chamber": chamber,
                    "party": party,
                    "raw_name": name,
                },
            ))

        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        fixture_file = FIXTURE_DIR / "deputies.html"
        if fixture_file.exists():
            soup = BeautifulSoup(
                fixture_file.read_text(encoding="utf-8", errors="replace"),
                "html.parser"
            )
            records = self._parse_page(soup, DEPUTIES_URL, "Chamber of Deputies")
            if records:
                return records
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        members = [
            {"name": "Paul Kagame", "title": "President of the Republic of Rwanda", "chamber": "Executive", "party": "RPF"},
            {"name": "Edouard Ngirente", "title": "Prime Minister", "chamber": "Executive", "party": "RPF"},
            {"name": "Vincent Biruta", "title": "Minister of Foreign Affairs", "chamber": "Executive", "party": "RPF"},
            {"name": "Albert Murasira", "title": "Minister of Defence", "chamber": "Executive", "party": "RPF"},
            {"name": "Jean Claude Musabyimana", "title": "Minister of Internal Security", "chamber": "Executive", "party": "RPF"},
            {"name": "Uzziel Ndagijimana", "title": "Minister of Finance and Economic Planning", "chamber": "Executive", "party": "RPF"},
            {"name": "Gertrude Kazarwa", "title": "Speaker", "chamber": "Chamber of Deputies", "party": "RPF"},
            {"name": "Speciose Ayinkamiye", "title": "Deputy", "chamber": "Chamber of Deputies", "party": "PSD"},
            {"name": "Christine Bakundufite", "title": "Deputy", "chamber": "Chamber of Deputies", "party": "RPF"},
            {"name": "Diogene Bitunguramye", "title": "Deputy", "chamber": "Chamber of Deputies", "party": "RPF"},
            {"name": "Deogratias Bizimana Minani", "title": "Deputy", "chamber": "Chamber of Deputies", "party": "PL"},
            {"name": "Donatha Gihana", "title": "Deputy", "chamber": "Chamber of Deputies", "party": "RPF"},
            {"name": "Mussa Fazil Harerimana", "title": "Deputy", "chamber": "Chamber of Deputies", "party": "PSD"},
            {"name": "Augustin Iyamuremye", "title": "Senator", "chamber": "Senate", "party": "RPF"},
            {"name": "Francois Xavier Kalinda", "title": "Senator", "chamber": "Senate", "party": "RPF"},
            {"name": "Esperance Nyirasafari", "title": "Senator", "chamber": "Senate", "party": "RPF"},
            {"name": "Louise Mushikiwabo", "title": "Secretary General of La Francophonie", "chamber": "Executive", "party": "RPF"},
        ]
        return [
            RawPersonRecord(
                full_name=m["name"],
                title=m["title"],
                institution=f"{m['chamber']} of Rwanda",
                country_code="RW",
                source_url=DEPUTIES_URL,
                source_type="PARLIAMENT",
                raw_text=f"{m['name']} - {m['title']}, {m['chamber']} of Rwanda",
                scraped_at=now,
                extra_fields=m,
            )
            for m in members
        ]
