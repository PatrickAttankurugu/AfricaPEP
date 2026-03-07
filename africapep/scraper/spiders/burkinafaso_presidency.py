"""
Scraper for the Burkina Faso Presidency / Government.

Source: https://www.gouvernement.gov.bf
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

GOV_URL = "https://www.gouvernement.gov.bf"


class BurkinaFasoPresidencyScraper(BaseScraper):
    """Scraper for the Burkina Faso Government."""

    country_code = "BF"
    source_type = "PRESIDENCY"

    def scrape(self) -> list[RawPersonRecord]:
        logger.info("bf_presidency.scrape.start", url=GOV_URL)
        try:
            resp = self._get(GOV_URL)
            records = self._parse_officials(resp.text)
            if records:
                return records
            return self._load_fixture()
        except Exception:
            logger.exception("bf_presidency.scrape.error")
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
                    institution="Government of Burkina Faso",
                    country_code=self.country_code, source_type=self.source_type,
                    source_url=GOV_URL, raw_text=f"{full_name} – {role}",
                    scraped_at=datetime.utcnow(), extra_fields={"category": "Cabinet"},
                ))
            except Exception:
                logger.exception("bf_presidency.parse.error")
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        officials = [
            {"name": "Ibrahim Traoré", "role": "President of the Transition"},
            {"name": "Apollinaire Joachim Kyelem de Tambela", "role": "Prime Minister"},
            {"name": "Karamoko Jean Marie Traoré", "role": "Minister of Foreign Affairs"},
            {"name": "Emile Zerbo", "role": "Minister of State"},
            {"name": "Kassoum Coulibaly", "role": "Minister of Defence"},
            {"name": "Ismaël Sombié", "role": "Minister of State for Health"},
            {"name": "Aboubakari Nacanabo", "role": "Minister of Finance"},
            {"name": "Joseph André Ouédraogo", "role": "Minister of Education"},
            {"name": "Bassolma Bazié", "role": "Minister of Civil Service"},
            {"name": "Mathias Traoré", "role": "Minister of Solidarity"},
            {"name": "Roland Somda", "role": "Minister of Interior"},
            {"name": "Jean-Emmanuel Ouédraogo", "role": "Minister of Communication"},
        ]
        records = []
        for o in officials:
            records.append(RawPersonRecord(
                full_name=o["name"], title=o["role"],
                institution="Government of Burkina Faso",
                country_code=self.country_code, source_type=self.source_type,
                source_url=GOV_URL, raw_text=f"{o['name']} – {o['role']}",
                scraped_at=now, extra_fields={"category": "Cabinet", "fixture": True},
            ))
        logger.info("bf_presidency.fixture.loaded", count=len(records))
        return records
