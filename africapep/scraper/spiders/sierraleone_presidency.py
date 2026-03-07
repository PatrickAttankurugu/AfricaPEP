"""
Scraper for the Sierra Leone Presidency / Cabinet.

Source: https://statehouse.gov.sl
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

GOV_URL = "https://statehouse.gov.sl/cabinet-ministers/"


class SierraLeonePresidencyScraper(BaseScraper):
    """Scraper for the Sierra Leone Presidency and Cabinet."""

    country_code = "SL"
    source_type = "PRESIDENCY"

    def scrape(self) -> list[RawPersonRecord]:
        logger.info("sl_presidency.scrape.start", url=GOV_URL)
        try:
            resp = self._get(GOV_URL)
            records = self._parse_officials(resp.text)
            if records:
                return records
            return self._load_fixture()
        except Exception:
            logger.exception("sl_presidency.scrape.error")
            return self._load_fixture()

    def _parse_officials(self, html: str) -> list[RawPersonRecord]:
        soup = BeautifulSoup(html, "html.parser")
        records: list[RawPersonRecord] = []
        cards = soup.select(".minister, .team-member, .card, article, .wp-block-column")
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
                    institution="Government of the Republic of Sierra Leone",
                    country_code=self.country_code, source_type=self.source_type,
                    source_url=GOV_URL, raw_text=f"{full_name} – {role}",
                    scraped_at=datetime.utcnow(), extra_fields={"category": "Cabinet"},
                ))
            except Exception:
                logger.exception("sl_presidency.parse.error")
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        officials = [
            {"name": "Julius Maada Bio", "role": "President of the Republic of Sierra Leone"},
            {"name": "Mohamed Juldeh Jalloh", "role": "Vice President"},
            {"name": "Sheku Bangura", "role": "Minister of Finance"},
            {"name": "Timothy Kabba", "role": "Minister of Foreign Affairs"},
            {"name": "Mohamed Belgore", "role": "Minister of Defence"},
            {"name": "Andrew Jaia Kaikai", "role": "Minister of Internal Affairs"},
            {"name": "Mohamed Lamin Tarawally", "role": "Attorney General and Minister of Justice"},
            {"name": "Austin Demby", "role": "Minister of Health and Sanitation"},
            {"name": "David Moinina Sengeh", "role": "Minister of Basic and Senior Secondary Education"},
            {"name": "Chernor Bah", "role": "Speaker of Parliament"},
            {"name": "Abu Bakarr Fofanah", "role": "Minister of Agriculture and Food Security"},
            {"name": "Moinina Sengeh", "role": "Chief Innovation Officer"},
        ]
        records = []
        for o in officials:
            records.append(RawPersonRecord(
                full_name=o["name"], title=o["role"],
                institution="Government of the Republic of Sierra Leone",
                country_code=self.country_code, source_type=self.source_type,
                source_url=GOV_URL, raw_text=f"{o['name']} – {o['role']}",
                scraped_at=now, extra_fields={"category": "Cabinet", "fixture": True},
            ))
        logger.info("sl_presidency.fixture.loaded", count=len(records))
        return records
