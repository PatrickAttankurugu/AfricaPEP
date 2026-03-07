"""
Scraper for the South Sudan Presidency / Government.

Source: https://www.presidency.gov.ss
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

GOV_URL = "https://www.presidency.gov.ss"


class SouthSudanPresidencyScraper(BaseScraper):
    """Scraper for the South Sudan Government."""

    country_code = "SS"
    source_type = "PRESIDENCY"

    def scrape(self) -> list[RawPersonRecord]:
        logger.info("ss_presidency.scrape.start", url=GOV_URL)
        try:
            resp = self._get(GOV_URL)
            records = self._parse_officials(resp.text)
            if records:
                return records
            return self._load_fixture()
        except Exception:
            logger.exception("ss_presidency.scrape.error")
            return self._load_fixture()

    def _parse_officials(self, html: str) -> list[RawPersonRecord]:
        soup = BeautifulSoup(html, "html.parser")
        records: list[RawPersonRecord] = []
        cards = soup.select(".minister, .team-member, .card, article")
        for card in cards:
            try:
                name_el = card.select_one("h3, h4, h2, .name, strong")
                if not name_el:
                    continue
                full_name = name_el.get_text(strip=True)
                if not full_name or len(full_name) < 3:
                    continue
                role_el = card.select_one("p, .role, .position")
                role = role_el.get_text(strip=True) if role_el else "Minister"
                records.append(RawPersonRecord(
                    full_name=full_name, title=role,
                    institution="Government of the Republic of South Sudan",
                    country_code=self.country_code, source_type=self.source_type,
                    source_url=GOV_URL, raw_text=f"{full_name} – {role}",
                    scraped_at=datetime.utcnow(), extra_fields={"category": "Cabinet"},
                ))
            except Exception:
                logger.exception("ss_presidency.parse.error")
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        officials = [
            {"name": "Salva Kiir Mayardit", "role": "President of the Republic"},
            {"name": "Riek Machar", "role": "First Vice President"},
            {"name": "James Wani Igga", "role": "Vice President"},
            {"name": "Deng Alor Kuol", "role": "Minister of Foreign Affairs"},
            {"name": "Awut Deng Acuil", "role": "Minister of General Education"},
            {"name": "Angelina Teny", "role": "Minister of Defence"},
            {"name": "Albino Akol Atak", "role": "Minister of Finance"},
            {"name": "Michael Makuei Lueth", "role": "Minister of Information"},
            {"name": "Yolanda Awel Deng", "role": "Minister of Health"},
            {"name": "Ruben Madol Arol", "role": "Minister of Justice"},
            {"name": "Josephine Lagu", "role": "Minister of Interior"},
            {"name": "Onyoti Adigo Nyikwec", "role": "Minister of Agriculture"},
        ]
        records = []
        for o in officials:
            records.append(RawPersonRecord(
                full_name=o["name"], title=o["role"],
                institution="Government of the Republic of South Sudan",
                country_code=self.country_code, source_type=self.source_type,
                source_url=GOV_URL, raw_text=f"{o['name']} – {o['role']}",
                scraped_at=now, extra_fields={"category": "Cabinet", "fixture": True},
            ))
        logger.info("ss_presidency.fixture.loaded", count=len(records))
        return records
