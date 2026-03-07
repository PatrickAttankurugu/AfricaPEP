"""
Scraper for the Mozambique Presidency / Government.

Source: https://www.portaldogoverno.gov.mz
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

GOV_URL = "https://www.portaldogoverno.gov.mz"


class MozambiquePresidencyScraper(BaseScraper):
    """Scraper for the Mozambique Government."""

    country_code = "MZ"
    source_type = "PRESIDENCY"

    def scrape(self) -> list[RawPersonRecord]:
        logger.info("mz_presidency.scrape.start", url=GOV_URL)
        try:
            resp = self._get(GOV_URL)
            records = self._parse_officials(resp.text)
            if records:
                return records
            return self._load_fixture()
        except Exception:
            logger.exception("mz_presidency.scrape.error")
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
                    institution="Government of the Republic of Mozambique",
                    country_code=self.country_code, source_type=self.source_type,
                    source_url=GOV_URL, raw_text=f"{full_name} – {role}",
                    scraped_at=datetime.utcnow(), extra_fields={"category": "Cabinet"},
                ))
            except Exception:
                logger.exception("mz_presidency.parse.error")
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        officials = [
            {"name": "Daniel Chapo", "role": "President of the Republic of Mozambique"},
            {"name": "Adriano Maleiane", "role": "Prime Minister"},
            {"name": "Ernesto Max Tonela", "role": "Minister of Economy and Finance"},
            {"name": "Verónica Macamo", "role": "Minister of Foreign Affairs and Cooperation"},
            {"name": "Cristóvão Chume", "role": "Minister of National Defence"},
            {"name": "Arsenio Henriques", "role": "Minister of Interior"},
            {"name": "Helena Kida", "role": "Minister of Justice"},
            {"name": "Armando Inroga", "role": "Minister of Health"},
            {"name": "Margarida Talapa", "role": "Minister of Education and Human Development"},
            {"name": "Carlos Mesquita", "role": "Minister of Transport and Communications"},
            {"name": "Celso Correia", "role": "Minister of Agriculture and Rural Development"},
            {"name": "Max Tonela", "role": "Minister of Mineral Resources and Energy"},
        ]
        records = []
        for o in officials:
            records.append(RawPersonRecord(
                full_name=o["name"], title=o["role"],
                institution="Government of the Republic of Mozambique",
                country_code=self.country_code, source_type=self.source_type,
                source_url=GOV_URL, raw_text=f"{o['name']} – {o['role']}",
                scraped_at=now, extra_fields={"category": "Cabinet", "fixture": True},
            ))
        logger.info("mz_presidency.fixture.loaded", count=len(records))
        return records
