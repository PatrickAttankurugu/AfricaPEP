"""Ghana Parliament Members scraper.
Source: https://www.parliament.gh/members
Method: BeautifulSoup (static HTML)
Schedule: Weekly
"""
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path

import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

log = structlog.get_logger()

FIXTURE_DIR = Path(__file__).parent.parent.parent.parent / "tests" / "fixtures" / "ghana_parliament"
BASE_URL = "https://www.parliament.gh"
MP_LIST_URL = f"{BASE_URL}/members"


class GhanaParliamentScraper(BaseScraper):
    country_code = "GH"
    source_type = "PARLIAMENT"

    def scrape(self) -> list[RawPersonRecord]:
        records = []
        page = 1

        while True:
            url = f"{MP_LIST_URL}?page={page}" if page > 1 else MP_LIST_URL
            try:
                resp = self._get(url)
            except Exception as e:
                log.error("ghana_parliament_request_failed", url=url, error=str(e))
                break

            soup = BeautifulSoup(resp.text, "html.parser")
            batch = self._parse_page(soup, url)

            if not batch:
                break

            records.extend(batch)
            log.info("ghana_parliament_page", page=page, found=len(batch))

            # Check for next page: find page links with page number > current
            page_links = soup.select("ul.pagination li.page-item a.page-link")
            next_page_exists = False
            for pl in page_links:
                href = pl.get("href", "")
                if f"page={page + 1}" in href:
                    next_page_exists = True
                    break
            if not next_page_exists:
                break
            page += 1

        return records

    def _parse_page(self, soup: BeautifulSoup, source_url: str) -> list[RawPersonRecord]:
        records = []

        # Each MP is in a div.col-lg-4.col-md-6 card on parliament.gh/members
        cards = soup.select("div.col-lg-4.col-md-6")

        for card in cards:
            try:
                # Name is in an <h5> tag
                h5 = card.select_one("h5")
                if not h5:
                    continue
                name = h5.get_text(strip=True)
                if not name or len(name) < 3:
                    continue

                # Constituency and party are in a <p> tag, separated by <br/>
                constituency = ""
                party = ""
                p_tag = card.select_one("p.text-center")
                if p_tag:
                    parts = [t.strip() for t in p_tag.stripped_strings]
                    if len(parts) >= 1:
                        constituency = parts[0]
                    if len(parts) >= 2:
                        party = parts[1]

                # Extract photo URL if available
                photo_url = ""
                img = card.select_one("img")
                if img:
                    photo_url = img.get("src", "") or img.get("data-src", "")
                    if photo_url and not photo_url.startswith("http"):
                        photo_url = BASE_URL + "/" + photo_url.lstrip("/")

                # Extract profile link
                profile_url = ""
                link = card.select_one("a[href*='members?mp=']")
                if link:
                    href = link.get("href", "")
                    if href and not href.startswith("http"):
                        profile_url = BASE_URL + "/" + href.lstrip("/")
                    else:
                        profile_url = href

                records.append(RawPersonRecord(
                    full_name=name.strip(),
                    title="Member of Parliament",
                    institution="Parliament of Ghana",
                    country_code="GH",
                    source_url=source_url,
                    source_type="PARLIAMENT",
                    raw_text=card.get_text(" ", strip=True),
                    scraped_at=datetime.utcnow(),
                    extra_fields={
                        "constituency": constituency,
                        "party": party,
                        "photo_url": photo_url,
                        "profile_url": profile_url,
                    },
                ))
            except Exception as e:
                log.warning("ghana_parliament_parse_error", error=str(e))

        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        fixture_file = FIXTURE_DIR / "mps.html"
        if not fixture_file.exists():
            log.warning("fixture_missing", path=str(fixture_file))
            # Return synthetic fixture data for testing
            return self._synthetic_fixture()

        soup = BeautifulSoup(
            fixture_file.read_text(encoding="utf-8", errors="replace"),
            "html.parser"
        )
        records = self._parse_page(soup, MP_LIST_URL)
        if not records:
            return self._synthetic_fixture()
        return records

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        """Generate synthetic fixture data for testing."""
        now = datetime.utcnow()
        mps = [
            {"name": "Alban Sumana Kingsford Bagbin", "constituency": "Nadowli-Kaleo",
             "party": "National Democratic Congress"},
            {"name": "Joseph Osei-Owusu", "constituency": "Bekwai",
             "party": "New Patriotic Party"},
            {"name": "Samuel Okudzeto Ablakwa", "constituency": "North Tongu",
             "party": "National Democratic Congress"},
            {"name": "Ursula Owusu-Ekuful", "constituency": "Ablekuma West",
             "party": "New Patriotic Party"},
            {"name": "Kennedy Ohene Agyapong", "constituency": "Assin Central",
             "party": "New Patriotic Party"},
            {"name": "Sarah Adwoa Safo", "constituency": "Dome-Kwabenya",
             "party": "New Patriotic Party"},
            {"name": "Haruna Iddrisu", "constituency": "Tamale South",
             "party": "National Democratic Congress"},
            {"name": "Afenyo-Markin Alexander", "constituency": "Effutu",
             "party": "New Patriotic Party"},
            {"name": "Mahama Ayariga", "constituency": "Bawku Central",
             "party": "National Democratic Congress"},
            {"name": "Lydia Seyram Alhassan", "constituency": "Ayawaso West Wuogon",
             "party": "New Patriotic Party"},
        ]
        return [
            RawPersonRecord(
                full_name=mp["name"],
                title="Member of Parliament",
                institution="Parliament of Ghana",
                country_code="GH",
                source_url=MP_LIST_URL,
                source_type="PARLIAMENT",
                raw_text=f"{mp['name']} MP for {mp['constituency']} ({mp['party']})",
                scraped_at=now,
                extra_fields=mp,
            )
            for mp in mps
        ]
