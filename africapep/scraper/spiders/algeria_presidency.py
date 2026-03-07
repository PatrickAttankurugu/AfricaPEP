"""
Scraper for the Algerian Presidency / Government.

Source: https://www.el-mouradia.dz
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

GOV_URL = "https://www.el-mouradia.dz/en"


class AlgeriaPresidencyScraper(BaseScraper):
    """Scraper for the Algerian Government."""

    country_code = "DZ"
    source_type = "PRESIDENCY"

    def scrape(self) -> list[RawPersonRecord]:
        logger.info("dz_presidency.scrape.start", url=GOV_URL)
        try:
            resp = self._get(GOV_URL)
            records = self._parse_officials(resp.text)
            if records:
                return records
            return self._load_fixture()
        except Exception:
            logger.exception("dz_presidency.scrape.error")
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
                    institution="Government of the People's Democratic Republic of Algeria",
                    country_code=self.country_code, source_type=self.source_type,
                    source_url=GOV_URL, raw_text=f"{full_name} – {role}",
                    scraped_at=datetime.utcnow(), extra_fields={"category": "Cabinet"},
                ))
            except Exception:
                logger.exception("dz_presidency.parse.error")
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        officials = [
            {"name": "Abdelmadjid Tebboune", "role": "President of the Republic"},
            {"name": "Nadir Larbaoui", "role": "Prime Minister"},
            {"name": "Ahmed Attaf", "role": "Minister of Foreign Affairs"},
            {"name": "Ibrahim Merad", "role": "Minister of Interior"},
            {"name": "Laaziz Faid", "role": "Minister of Finance"},
            {"name": "Mohamed Arkab", "role": "Minister of Energy and Mines"},
            {"name": "Abdelhak Saihi", "role": "Minister of Health"},
            {"name": "Abdelhakim Belaabed", "role": "Minister of National Education"},
            {"name": "Kamel Baddari", "role": "Minister of Higher Education"},
            {"name": "Chanegriha Said", "role": "Chief of Staff of the Army"},
            {"name": "Abderrachid Tabi", "role": "Minister of Justice"},
            {"name": "Mohamed Laagab", "role": "Minister of Communication"},
        ]
        records = []
        for o in officials:
            records.append(RawPersonRecord(
                full_name=o["name"], title=o["role"],
                institution="Government of the People's Democratic Republic of Algeria",
                country_code=self.country_code, source_type=self.source_type,
                source_url=GOV_URL, raw_text=f"{o['name']} – {o['role']}",
                scraped_at=now, extra_fields={"category": "Cabinet", "fixture": True},
            ))
        logger.info("dz_presidency.fixture.loaded", count=len(records))
        return records
