"""Ghana Parliament Members scraper.
Source: https://www.parliament.gh/mps
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
MP_LIST_URL = f"{BASE_URL}/mps"


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

            # Check for next page
            next_link = soup.select_one("a[rel=next], .pagination .next a, li.next a")
            if not next_link:
                break
            page += 1

        return records

    def _parse_page(self, soup: BeautifulSoup, source_url: str) -> list[RawPersonRecord]:
        records = []

        # Try multiple CSS selectors for different site layouts
        cards = (
            soup.select(".mp-card") or
            soup.select(".member-item") or
            soup.select(".views-row") or
            soup.select("table.mp-table tbody tr") or
            soup.select("table tbody tr") or
            soup.select(".team-member") or
            soup.select(".member-box")
        )

        for card in cards:
            try:
                name = self._extract_text(card, [
                    ".mp-name", ".member-name", "h3", "h4", "h5",
                    "td:first-child", ".field-name-title",
                ])
                if not name or len(name) < 3:
                    continue

                constituency = self._extract_text(card, [
                    ".constituency", ".field-constituency",
                    "td:nth-child(2)", ".mp-constituency",
                ])
                party = self._extract_text(card, [
                    ".party", ".field-party", "td:nth-child(3)", ".mp-party",
                ])
                region = self._extract_text(card, [
                    ".region", ".field-region", "td:nth-child(4)", ".mp-region",
                ])

                # Extract photo URL if available
                photo_url = ""
                img = card.select_one("img")
                if img:
                    photo_url = img.get("src", "") or img.get("data-src", "")
                    if photo_url and not photo_url.startswith("http"):
                        photo_url = BASE_URL + "/" + photo_url.lstrip("/")

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
                        "region": region,
                        "photo_url": photo_url,
                    },
                ))
            except Exception as e:
                log.warning("ghana_parliament_parse_error", error=str(e))

        return records

    def _extract_text(self, tag, selectors: list[str]) -> str:
        for sel in selectors:
            el = tag.select_one(sel)
            if el:
                return el.get_text(strip=True)
        return ""

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
             "party": "NDC", "region": "Upper West"},
            {"name": "Joseph Osei-Owusu", "constituency": "Bekwai",
             "party": "NPP", "region": "Ashanti"},
            {"name": "Samuel Okudzeto Ablakwa", "constituency": "North Tongu",
             "party": "NDC", "region": "Volta"},
            {"name": "Ursula Owusu-Ekuful", "constituency": "Ablekuma West",
             "party": "NPP", "region": "Greater Accra"},
            {"name": "Kennedy Ohene Agyapong", "constituency": "Assin Central",
             "party": "NPP", "region": "Central"},
            {"name": "Sarah Adwoa Safo", "constituency": "Dome-Kwabenya",
             "party": "NPP", "region": "Greater Accra"},
            {"name": "Haruna Iddrisu", "constituency": "Tamale South",
             "party": "NDC", "region": "Northern"},
            {"name": "Afenyo-Markin Alexander", "constituency": "Effutu",
             "party": "NPP", "region": "Central"},
            {"name": "Mahama Ayariga", "constituency": "Bawku Central",
             "party": "NDC", "region": "Upper East"},
            {"name": "Lydia Seyram Alhassan", "constituency": "Ayawaso West Wuogon",
             "party": "NPP", "region": "Greater Accra"},
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
