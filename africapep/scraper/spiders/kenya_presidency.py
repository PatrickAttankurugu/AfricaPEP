"""Kenya Presidency / Cabinet scraper.
Source: https://www.president.go.ke/
Method: BeautifulSoup (static HTML)
Schedule: Weekly
"""
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path

import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

log = structlog.get_logger()

BASE_URL = "https://www.president.go.ke"
CABINET_URL = f"{BASE_URL}/the-cabinet/"


class KenyaPresidencyScraper(BaseScraper):
    """Scraper for Kenya Presidency / Cabinet members."""

    country_code = "KE"
    source_type = "PRESIDENCY"

    def scrape(self) -> list[RawPersonRecord]:
        records = []
        try:
            resp = self._get(CABINET_URL)
            soup = BeautifulSoup(resp.text, "html.parser")
            records = self._parse_page(soup, CABINET_URL)
            log.info("kenya_presidency_scraped", records=len(records))
        except Exception as e:
            log.error("kenya_presidency_failed", error=str(e))
        return records

    def _parse_page(self, soup: BeautifulSoup, source_url: str) -> list[RawPersonRecord]:
        records = []
        now = datetime.utcnow()

        # Try various selectors for cabinet member cards
        cards = (
            soup.select(".team-member") or
            soup.select(".cabinet-member") or
            soup.select(".elementor-widget-container .member") or
            soup.select("article") or
            soup.select(".entry-content h3")
        )

        for card in cards:
            try:
                name_el = card.select_one("h3, h4, h5, .member-name, strong")
                if not name_el:
                    continue

                name = name_el.get_text(strip=True)
                if not name or len(name) < 3:
                    continue

                # Clean name
                clean_name = name
                for prefix in ["H.E.", "Hon.", "Dr.", "Prof.", "Amb.", "CS ", "PS "]:
                    if clean_name.startswith(prefix):
                        clean_name = clean_name[len(prefix):].strip()

                # Get portfolio
                portfolio = ""
                title_el = card.select_one(".position, .portfolio, p, .member-title")
                if title_el:
                    portfolio = title_el.get_text(strip=True)

                records.append(RawPersonRecord(
                    full_name=clean_name,
                    title=portfolio or "Cabinet Secretary",
                    institution="Office of the President of Kenya",
                    country_code="KE",
                    source_url=source_url,
                    source_type="PRESIDENCY",
                    raw_text=f"{name} - {portfolio}",
                    scraped_at=now,
                    extra_fields={"portfolio": portfolio, "raw_name": name},
                ))
            except Exception as e:
                log.warning("kenya_presidency_parse_error", error=str(e))

        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        cabinet = [
            {"name": "William Samoei Ruto", "title": "President of the Republic of Kenya"},
            {"name": "Rigathi Gachagua", "title": "Deputy President"},
            {"name": "Musalia Mudavadi", "title": "Prime Cabinet Secretary and CS Foreign Affairs"},
            {"name": "Kithure Kindiki", "title": "Cabinet Secretary for Interior"},
            {"name": "Njuguna Ndung'u", "title": "Cabinet Secretary for Treasury"},
            {"name": "Aden Duale", "title": "Cabinet Secretary for Defence"},
            {"name": "Justin Muturi", "title": "Attorney General"},
            {"name": "Alfred Mutua", "title": "Cabinet Secretary for Tourism"},
            {"name": "Moses Kuria", "title": "Cabinet Secretary for Investment"},
            {"name": "Ezekiel Machogu", "title": "Cabinet Secretary for Education"},
            {"name": "Aisha Jumwa", "title": "Cabinet Secretary for Gender"},
            {"name": "Susan Nakhumicha", "title": "Cabinet Secretary for Health"},
        ]
        return [
            RawPersonRecord(
                full_name=m["name"],
                title=m["title"],
                institution="Office of the President of Kenya",
                country_code="KE",
                source_url=CABINET_URL,
                source_type="PRESIDENCY",
                raw_text=f"{m['name']} - {m['title']}",
                scraped_at=now,
                extra_fields=m,
            )
            for m in cabinet
        ]
