"""
Scraper for the Angolan Presidency / Government.

Source: https://governo.gov.ao
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

GOV_URL = "https://governo.gov.ao"


class AngolaPresidencyScraper(BaseScraper):
    """Scraper for the Angolan Government."""

    country_code = "AO"
    source_type = "PRESIDENCY"

    def scrape(self) -> list[RawPersonRecord]:
        logger.info("ao_presidency.scrape.start", url=GOV_URL)
        try:
            resp = self._get(GOV_URL)
            records = self._parse_officials(resp.text)
            if records:
                return records
            return self._load_fixture()
        except Exception:
            logger.exception("ao_presidency.scrape.error")
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
                    institution="Government of the Republic of Angola",
                    country_code=self.country_code, source_type=self.source_type,
                    source_url=GOV_URL, raw_text=f"{full_name} – {role}",
                    scraped_at=datetime.utcnow(), extra_fields={"category": "Cabinet"},
                ))
            except Exception:
                logger.exception("ao_presidency.parse.error")
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        officials = [
            {"name": "João Lourenço", "role": "President of the Republic of Angola"},
            {"name": "Esperança da Costa", "role": "Vice President"},
            {"name": "Fernando Dias dos Santos", "role": "Minister of State for Economic Coordination"},
            {"name": "Téte António", "role": "Minister of External Relations"},
            {"name": "Francisco Tavares de Almeida", "role": "Minister of National Defence and Veterans"},
            {"name": "Eugénio Laborinho", "role": "Minister of Interior"},
            {"name": "Francisco Queiroz", "role": "Minister of Justice and Human Rights"},
            {"name": "Vera Daves de Sousa", "role": "Minister of Finance"},
            {"name": "Sílvia Lutucuta", "role": "Minister of Health"},
            {"name": "Luísa Grilo", "role": "Minister of Higher Education, Science, Technology and Innovation"},
            {"name": "Diamantino Azevedo", "role": "Minister of Mineral Resources, Petroleum and Gas"},
            {"name": "António Francisco de Assis", "role": "Minister of Agriculture and Forestry"},
            {"name": "Mário Augusto Caetano João", "role": "Minister of Telecommunications, Information Technology and Social Communication"},
            {"name": "Manuel Homem", "role": "Minister of Industry and Commerce"},
            {"name": "Adão de Almeida", "role": "Minister of Territorial Administration"},
            {"name": "Ricardo de Abreu", "role": "Minister of Transport"},
            {"name": "Manuel Nunes Júnior", "role": "Minister of State for Economic and Social Development"},
            {"name": "Carolina Cerqueira", "role": "Minister of Culture, Tourism and Environment"},
            {"name": "Ana Paula do Sacramento Neto", "role": "Speaker of the National Assembly"},
            {"name": "Joel Leonardo", "role": "Chief Justice, Supreme Court"},
            {"name": "Manuel Tiago Dias", "role": "Governor, National Bank of Angola"},
            {"name": "General António Egídio de Sousa Santos", "role": "Chief of General Staff of the Armed Forces"},
            {"name": "Arnaldo Manuel Calado", "role": "Commander General of the National Police"},
            {"name": "José Eduardo dos Santos", "role": "Former President of the Republic (deceased 2022)"},
            {"name": "Adalberto Costa Júnior", "role": "Opposition Leader, UNITA"},
            {"name": "Isabel dos Santos", "role": "Business Figure, Daughter of Former President (PEP)"},
            {"name": "Filomeno dos Santos", "role": "Son of Former President, Former Sovereign Wealth Fund Head (PEP)"},
        ]
        records = []
        for o in officials:
            records.append(RawPersonRecord(
                full_name=o["name"], title=o["role"],
                institution="Government of the Republic of Angola",
                country_code=self.country_code, source_type=self.source_type,
                source_url=GOV_URL, raw_text=f"{o['name']} – {o['role']}",
                scraped_at=now, extra_fields={"category": "Cabinet", "fixture": True},
            ))
        logger.info("ao_presidency.fixture.loaded", count=len(records))
        return records
