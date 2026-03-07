"""
Scraper for the Benin Presidency / Government.

Source: https://www.gouv.bj
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

GOV_URL = "https://www.gouv.bj/membres/"


class BeninPresidencyScraper(BaseScraper):
    """Scraper for the Benin Government."""

    country_code = "BJ"
    source_type = "PRESIDENCY"

    def scrape(self) -> list[RawPersonRecord]:
        logger.info("bj_presidency.scrape.start", url=GOV_URL)
        try:
            resp = self._get(GOV_URL)
            records = self._parse_officials(resp.text)
            if records:
                return records
            return self._load_fixture()
        except Exception:
            logger.exception("bj_presidency.scrape.error")
            return self._load_fixture()

    def _parse_officials(self, html: str) -> list[RawPersonRecord]:
        soup = BeautifulSoup(html, "html.parser")
        records: list[RawPersonRecord] = []
        cards = soup.select(".minister, .team-member, .card, article, .membre")
        for card in cards:
            try:
                name_el = card.select_one("h3, h4, h2, .name, strong")
                if not name_el:
                    continue
                full_name = name_el.get_text(strip=True)
                if not full_name or len(full_name) < 3:
                    continue
                role_el = card.select_one("p, .role, .position, .fonction")
                role = role_el.get_text(strip=True) if role_el else "Minister"
                records.append(RawPersonRecord(
                    full_name=full_name, title=role,
                    institution="Government of the Republic of Benin",
                    country_code=self.country_code, source_type=self.source_type,
                    source_url=GOV_URL, raw_text=f"{full_name} – {role}",
                    scraped_at=datetime.utcnow(), extra_fields={"category": "Cabinet"},
                ))
            except Exception:
                logger.exception("bj_presidency.parse.error")
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        officials = [
            {"name": "Patrice Talon", "role": "President of the Republic"},
            {"name": "Mariam Chabi Talata Zimé", "role": "Vice President of the Republic"},
            {"name": "Abdoulaye Bio Tchané", "role": "Minister of State for Development and Coordination of Government Action"},
            {"name": "Romuald Wadagni", "role": "Minister of Economy and Finance"},
            {"name": "Yvon Detchenou", "role": "Minister of Justice and Legislation"},
            {"name": "Olushegun Adjadi Bakari", "role": "Minister of Foreign Affairs and Cooperation"},
            {"name": "Alassane Seidou", "role": "Minister of Interior and Public Security"},
            {"name": "Benjamin Hounkpatin", "role": "Minister of Health"},
            {"name": "Salimane Karimou", "role": "Minister of Secondary and Technical Education"},
            {"name": "Shadiya Alimatou Assouman", "role": "Minister of Industry and Commerce"},
            {"name": "Gaston Dossouhoui", "role": "Minister of Agriculture, Livestock and Fisheries"},
            {"name": "Aurelie Soule Zoumarou", "role": "Minister of Digital and Digitisation"},
            {"name": "Fortunet Alain Nouatin", "role": "Minister of Defence"},
            {"name": "Eléonore Yayi Ladékan", "role": "Minister of Higher Education and Scientific Research"},
            {"name": "Jean-Michel Abimbola", "role": "Minister of Tourism, Culture and Arts"},
            {"name": "Véronique Tognifodé", "role": "Minister of Social Affairs and Microfinance"},
            {"name": "Samou Seidou Adambi", "role": "Minister of Water and Mines"},
            {"name": "José Didier Tonato", "role": "Minister of Living Environment, Transport and Sustainable Development"},
            {"name": "Hervé Hêhomey", "role": "Minister of Decentralisation and Local Governance"},
            {"name": "Louis Vlavonou", "role": "Speaker of the National Assembly"},
            {"name": "Ousmane Batoko", "role": "President of the Supreme Court"},
            {"name": "Romuald Wadagni", "role": "Governor, BCEAO Benin National Agency"},
            {"name": "Général Fructueux Gbaguidi", "role": "Chief of Defence Staff"},
            {"name": "Soumaïla Yaya", "role": "Director General of National Police"},
            {"name": "Nicéphore Soglo", "role": "Former President of the Republic"},
            {"name": "Boni Yayi", "role": "Former President of the Republic"},
        ]
        records = []
        for o in officials:
            records.append(RawPersonRecord(
                full_name=o["name"], title=o["role"],
                institution="Government of the Republic of Benin",
                country_code=self.country_code, source_type=self.source_type,
                source_url=GOV_URL, raw_text=f"{o['name']} – {o['role']}",
                scraped_at=now, extra_fields={"category": "Cabinet", "fixture": True},
            ))
        logger.info("bj_presidency.fixture.loaded", count=len(records))
        return records
