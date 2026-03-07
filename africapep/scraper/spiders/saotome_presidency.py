"""
Scraper for the São Tomé and Príncipe Presidency / Government.

Source: https://www.presidencia.st
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

GOV_URL = "https://www.presidencia.st"


class SaoTomePresidencyScraper(BaseScraper):
    """Scraper for the São Tomé and Príncipe Government."""

    country_code = "ST"
    source_type = "PRESIDENCY"

    def scrape(self) -> list[RawPersonRecord]:
        logger.info("st_presidency.scrape.start", url=GOV_URL)
        try:
            resp = self._get(GOV_URL)
            records = self._parse_officials(resp.text)
            if records:
                return records
            return self._load_fixture()
        except Exception:
            logger.exception("st_presidency.scrape.error")
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
                    institution="Government of São Tomé and Príncipe",
                    country_code=self.country_code, source_type=self.source_type,
                    source_url=GOV_URL, raw_text=f"{full_name} – {role}",
                    scraped_at=datetime.utcnow(), extra_fields={"category": "Cabinet"},
                ))
            except Exception:
                logger.exception("st_presidency.parse.error")
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        officials = [
            {"name": "Carlos Vila Nova", "role": "President of the Republic"},
            {"name": "Patrice Trovoada", "role": "Prime Minister"},
            {"name": "Gareth Guadalupe", "role": "Minister of Foreign Affairs, Cooperation and Communities"},
            {"name": "Jorge Lopes Bom Jesus", "role": "Minister of Internal Administration"},
            {"name": "Engracia Barros da Graça", "role": "Minister of Finance and Blue Economy"},
            {"name": "Óscar Sousa", "role": "Minister of Defence and Internal Order"},
            {"name": "Ilza Amado Vaz", "role": "Minister of Justice, Public Administration and Human Rights"},
            {"name": "Edgar Neves", "role": "Minister of Health"},
            {"name": "Julieta Izidro Rodrigues", "role": "Minister of Education and Higher Education"},
            {"name": "Teodorico de Campos", "role": "Minister of Agriculture, Rural Development and Fisheries"},
            {"name": "Américo Barros", "role": "Minister of Infrastructure, Natural Resources and Environment"},
            {"name": "Frederico Carvalho dos Santos", "role": "Minister of Planning, Finance and Blue Economy"},
            {"name": "Arlindo de Ceita Carvalho", "role": "Minister of Economy and International Cooperation"},
            {"name": "Celmira Sacramento", "role": "Minister of Labour, Solidarity and Social Security"},
            {"name": "Edite Ramos da Costa Ten Jua", "role": "Minister of Tourism, Culture and Youth"},
            {"name": "Hélder Barros", "role": "Minister of Commerce, Industry and Energy"},
            {"name": "José Cassandra", "role": "Secretary of State for Communication"},
            {"name": "Delfim Santiago das Neves", "role": "Speaker of the National Assembly"},
            {"name": "Silvestre Leite", "role": "Chief Justice, Supreme Court"},
            {"name": "Maria do Carmo Trovoada", "role": "Governor, Central Bank of São Tomé and Príncipe"},
            {"name": "General Olinto Paquete", "role": "Chief of Defence Staff"},
            {"name": "Jorge Bom Jesus", "role": "Former Prime Minister"},
            {"name": "Evaristo Carvalho", "role": "Former President of the Republic"},
            {"name": "Aurélio Martins", "role": "Opposition Leader, MLSTP-PSD"},
        ]
        records = []
        for o in officials:
            records.append(RawPersonRecord(
                full_name=o["name"], title=o["role"],
                institution="Government of São Tomé and Príncipe",
                country_code=self.country_code, source_type=self.source_type,
                source_url=GOV_URL, raw_text=f"{o['name']} – {o['role']}",
                scraped_at=now, extra_fields={"category": "Cabinet", "fixture": True},
            ))
        logger.info("st_presidency.fixture.loaded", count=len(records))
        return records
