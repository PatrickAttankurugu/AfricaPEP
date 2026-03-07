"""
Scraper for the Central African Republic Presidency / Government.

Source: https://www.presidence.cf
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

GOV_URL = "https://www.presidence.cf"


class CARPresidencyScraper(BaseScraper):
    """Scraper for the Central African Republic Government."""

    country_code = "CF"
    source_type = "PRESIDENCY"

    def scrape(self) -> list[RawPersonRecord]:
        logger.info("cf_presidency.scrape.start", url=GOV_URL)
        try:
            resp = self._get(GOV_URL)
            records = self._parse_officials(resp.text)
            if records:
                return records
            return self._load_fixture()
        except Exception:
            logger.exception("cf_presidency.scrape.error")
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
                    institution="Government of the Central African Republic",
                    country_code=self.country_code, source_type=self.source_type,
                    source_url=GOV_URL, raw_text=f"{full_name} – {role}",
                    scraped_at=datetime.utcnow(), extra_fields={"category": "Cabinet"},
                ))
            except Exception:
                logger.exception("cf_presidency.parse.error")
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        officials = [
            {"name": "Faustin-Archange Touadéra", "role": "President of the Republic"},
            {"name": "Félix Moloua", "role": "Prime Minister"},
            {"name": "Sylvie Baipo-Temon", "role": "Minister of Foreign Affairs"},
            {"name": "Henri Wanzet Linguissara", "role": "Minister of Defence"},
            {"name": "Hervé Ndoba", "role": "Minister of Finance"},
            {"name": "Arnaud Djoubaye Abazène", "role": "Minister of Justice"},
            {"name": "Pierre Somsé", "role": "Minister of Health"},
            {"name": "Aurélien Simplice Zingas", "role": "Minister of Education"},
            {"name": "Maxime Balalou", "role": "Minister of Interior"},
            {"name": "Gontran Djono-Ahaba", "role": "Minister of Mines and Geology"},
            {"name": "Arthur Piri", "role": "Minister of Agriculture"},
            {"name": "Simplice Mathieu Sarandji", "role": "Speaker of National Assembly"},
        ]
        records = []
        for o in officials:
            records.append(RawPersonRecord(
                full_name=o["name"], title=o["role"],
                institution="Government of the Central African Republic",
                country_code=self.country_code, source_type=self.source_type,
                source_url=GOV_URL, raw_text=f"{o['name']} – {o['role']}",
                scraped_at=now, extra_fields={"category": "Cabinet", "fixture": True},
            ))
        logger.info("cf_presidency.fixture.loaded", count=len(records))
        return records
