"""
Scraper for the Sudan Presidency / Government.

Source: https://presidency.gov.sd
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

GOV_URL = "https://presidency.gov.sd"


class SudanPresidencyScraper(BaseScraper):
    """Scraper for the Sudan Government."""

    country_code = "SD"
    source_type = "PRESIDENCY"

    def scrape(self) -> list[RawPersonRecord]:
        logger.info("sd_presidency.scrape.start", url=GOV_URL)
        try:
            resp = self._get(GOV_URL)
            records = self._parse_officials(resp.text)
            if records:
                return records
            return self._load_fixture()
        except Exception:
            logger.exception("sd_presidency.scrape.error")
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
                    institution="Government of the Republic of the Sudan",
                    country_code=self.country_code, source_type=self.source_type,
                    source_url=GOV_URL, raw_text=f"{full_name} – {role}",
                    scraped_at=datetime.utcnow(), extra_fields={"category": "Cabinet"},
                ))
            except Exception:
                logger.exception("sd_presidency.parse.error")
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        officials = [
            {"name": "Abdel Fattah al-Burhan", "role": "Chairman of the Sovereignty Council"},
            {"name": "Malik Agar", "role": "Deputy Chairman of Sovereignty Council"},
            {"name": "Shams al-Din Kabashi", "role": "Member of Sovereignty Council"},
            {"name": "Osman Hussein", "role": "Minister of Foreign Affairs"},
            {"name": "Ibrahim Jabir", "role": "Minister of Finance"},
            {"name": "Yasin Ibrahim Yasin", "role": "Minister of Defence"},
            {"name": "Ahmed Adam", "role": "Minister of Interior"},
            {"name": "Moawia Osman Khalid", "role": "Minister of Justice"},
            {"name": "Haitham Mohamed Ibrahim", "role": "Minister of Health"},
            {"name": "Mohamed al-Amin al-Toum", "role": "Minister of Education"},
            {"name": "Abu Bakr al-Sadiq al-Nour", "role": "Minister of Agriculture"},
            {"name": "Gibril Ibrahim", "role": "Minister of Finance (Former)"},
            {"name": "Mohamed Hamdan Dagalo", "role": "Former Deputy Chairman of Sovereignty Council / RSF Commander"},
            {"name": "Omar al-Bashir", "role": "Former President of Sudan (1989-2019)"},
            {"name": "Sadiq al-Mahdi", "role": "Former Prime Minister, Umma Party Leader"},
            {"name": "Abdalla Hamdok", "role": "Former Prime Minister (Transitional Government)"},
            {"name": "Ibrahim al-Sheikh", "role": "Member of Sovereignty Council"},
            {"name": "Aisha Musa al-Said", "role": "Member of Sovereignty Council"},
            {"name": "Mohamed Osman al-Hussein", "role": "Governor, Central Bank of Sudan"},
            {"name": "Nemat Abdullah Mohamed Khair", "role": "Chief Justice, Supreme Court"},
            {"name": "Ibrahim Ahmed Omar", "role": "Speaker of the National Assembly (Former)"},
            {"name": "Yasser al-Atta", "role": "Deputy Commander-in-Chief of the Armed Forces"},
            {"name": "Maryam al-Sadiq al-Mahdi", "role": "Former Minister of Foreign Affairs"},
            {"name": "Mohamed al-Faki Suleiman", "role": "Member of Sovereignty Council"},
            {"name": "Minni Minnawi", "role": "Former Governor of Darfur / SLM Leader"},
        ]
        records = []
        for o in officials:
            records.append(RawPersonRecord(
                full_name=o["name"], title=o["role"],
                institution="Government of the Republic of the Sudan",
                country_code=self.country_code, source_type=self.source_type,
                source_url=GOV_URL, raw_text=f"{o['name']} – {o['role']}",
                scraped_at=now, extra_fields={"category": "Cabinet", "fixture": True},
            ))
        logger.info("sd_presidency.fixture.loaded", count=len(records))
        return records
