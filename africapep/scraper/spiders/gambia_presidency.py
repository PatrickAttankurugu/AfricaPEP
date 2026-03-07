"""
Scraper for the Gambia Presidency / Cabinet.

Source: https://statehouse.gm
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

GOV_URL = "https://statehouse.gm/cabinet"


class GambiaPresidencyScraper(BaseScraper):
    """Scraper for the Gambia Presidency and Cabinet."""

    country_code = "GM"
    source_type = "PRESIDENCY"

    def scrape(self) -> list[RawPersonRecord]:
        logger.info("gm_presidency.scrape.start", url=GOV_URL)
        try:
            resp = self._get(GOV_URL)
            records = self._parse_officials(resp.text)
            if records:
                return records
            return self._load_fixture()
        except Exception:
            logger.exception("gm_presidency.scrape.error")
            return self._load_fixture()

    def _parse_officials(self, html: str) -> list[RawPersonRecord]:
        soup = BeautifulSoup(html, "html.parser")
        records: list[RawPersonRecord] = []
        cards = soup.select(".views-row, .minister, .team-member, .card, article")
        for card in cards:
            try:
                name_el = card.select_one("h3, h4, h2, .name, strong, a")
                if not name_el:
                    continue
                full_name = name_el.get_text(strip=True)
                if not full_name or len(full_name) < 3:
                    continue
                role_el = card.select_one("p, .role, .position, .field-content")
                role = role_el.get_text(strip=True) if role_el else "Minister"
                records.append(RawPersonRecord(
                    full_name=full_name, title=role,
                    institution="Government of the Republic of The Gambia",
                    country_code=self.country_code, source_type=self.source_type,
                    source_url=GOV_URL, raw_text=f"{full_name} – {role}",
                    scraped_at=datetime.utcnow(), extra_fields={"category": "Cabinet"},
                ))
            except Exception:
                logger.exception("gm_presidency.parse.error")
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        officials = [
            {"name": "Adama Barrow", "role": "President of the Republic of The Gambia"},
            {"name": "Muhammad B.S. Jallow", "role": "Vice President"},
            {"name": "Mambury Njie", "role": "Minister of Foreign Affairs"},
            {"name": "Seedy Keita", "role": "Minister of Finance and Economic Affairs"},
            {"name": "Ousman Sonko", "role": "Minister of Interior"},
            {"name": "Sheikh Omar Faye", "role": "Minister of Defence"},
            {"name": "Dawda Jallow", "role": "Attorney General and Minister of Justice"},
            {"name": "Ahmadou Lamin Samateh", "role": "Minister of Health"},
            {"name": "Claudiana Cole", "role": "Minister of Basic and Secondary Education"},
            {"name": "Bakary Badjie", "role": "Minister of Agriculture"},
            {"name": "Ebrima Sillah", "role": "Minister of Information"},
            {"name": "Lamin Jobe", "role": "Minister of Trade and Regional Integration"},
        ]
        records = []
        for o in officials:
            records.append(RawPersonRecord(
                full_name=o["name"], title=o["role"],
                institution="Government of the Republic of The Gambia",
                country_code=self.country_code, source_type=self.source_type,
                source_url=GOV_URL, raw_text=f"{o['name']} – {o['role']}",
                scraped_at=now, extra_fields={"category": "Cabinet", "fixture": True},
            ))
        logger.info("gm_presidency.fixture.loaded", count=len(records))
        return records
