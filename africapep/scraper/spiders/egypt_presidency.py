"""
Scraper for the Egyptian Presidency / Cabinet.

Source: https://www.cabinet.gov.eg
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

CABINET_URL = "https://www.cabinet.gov.eg/English"


class EgyptPresidencyScraper(BaseScraper):
    """Scraper for the Egyptian Presidency and Cabinet."""

    country_code = "EG"
    source_type = "PRESIDENCY"

    def scrape(self) -> list[RawPersonRecord]:
        logger.info("eg_presidency.scrape.start", url=CABINET_URL)
        try:
            resp = self._get(CABINET_URL)
            records = self._parse_officials(resp.text)
            if records:
                return records
            return self._load_fixture()
        except Exception:
            logger.exception("eg_presidency.scrape.error")
            return self._load_fixture()

    def _parse_officials(self, html: str) -> list[RawPersonRecord]:
        soup = BeautifulSoup(html, "html.parser")
        records: list[RawPersonRecord] = []
        cards = soup.select(".minister-card, .team-member, .card, article, [class*='minister']")
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
                    institution="Government of the Arab Republic of Egypt",
                    country_code=self.country_code, source_type=self.source_type,
                    source_url=CABINET_URL, raw_text=f"{full_name} – {role}",
                    scraped_at=datetime.utcnow(), extra_fields={"category": "Cabinet"},
                ))
            except Exception:
                logger.exception("eg_presidency.parse.error")
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        officials = [
            {"name": "Abdel Fattah el-Sisi", "role": "President of the Arab Republic of Egypt"},
            {"name": "Mostafa Madbouly", "role": "Prime Minister"},
            {"name": "Mohamed Maait", "role": "Minister of Finance"},
            {"name": "Sameh Shoukry", "role": "Minister of Foreign Affairs"},
            {"name": "Mohamed Ahmed Morsi", "role": "Minister of Defence and Military Production"},
            {"name": "Mahmoud Tawfik", "role": "Minister of Interior"},
            {"name": "Khaled Abdel Ghaffar", "role": "Minister of Health and Population"},
            {"name": "Reda Hegazy", "role": "Minister of Education"},
            {"name": "Mohamed Ayman Ashour", "role": "Minister of Higher Education"},
            {"name": "Hani Sweilam", "role": "Minister of Water Resources and Irrigation"},
            {"name": "Kamel El-Wazir", "role": "Minister of Transport"},
            {"name": "Ahmed Issa", "role": "Minister of Tourism and Antiquities"},
        ]
        records = []
        for o in officials:
            records.append(RawPersonRecord(
                full_name=o["name"], title=o["role"],
                institution="Government of the Arab Republic of Egypt",
                country_code=self.country_code, source_type=self.source_type,
                source_url=CABINET_URL, raw_text=f"{o['name']} – {o['role']}",
                scraped_at=now, extra_fields={"category": "Cabinet", "fixture": True},
            ))
        logger.info("eg_presidency.fixture.loaded", count=len(records))
        return records
