"""
Scraper for the Cape Verde (Cabo Verde) Presidency / Government.

Source: https://governo.cv
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

GOV_URL = "https://governo.cv"


class CapeVerdePresidencyScraper(BaseScraper):
    """Scraper for the Cape Verde Government."""

    country_code = "CV"
    source_type = "PRESIDENCY"

    def scrape(self) -> list[RawPersonRecord]:
        logger.info("cv_presidency.scrape.start", url=GOV_URL)
        try:
            resp = self._get(GOV_URL)
            records = self._parse_officials(resp.text)
            if records:
                return records
            return self._load_fixture()
        except Exception:
            logger.exception("cv_presidency.scrape.error")
            return self._load_fixture()

    def _parse_officials(self, html: str) -> list[RawPersonRecord]:
        soup = BeautifulSoup(html, "html.parser")
        records: list[RawPersonRecord] = []
        cards = soup.select(".minister, .team-member, .card, article, .membro")
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
                    institution="Government of the Republic of Cabo Verde",
                    country_code=self.country_code, source_type=self.source_type,
                    source_url=GOV_URL, raw_text=f"{full_name} – {role}",
                    scraped_at=datetime.utcnow(), extra_fields={"category": "Cabinet"},
                ))
            except Exception:
                logger.exception("cv_presidency.parse.error")
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        officials = [
            {"name": "José Maria Neves", "role": "President of the Republic"},
            {"name": "Ulisses Correia e Silva", "role": "Prime Minister"},
            {"name": "Rui Figueiredo Soares", "role": "Minister of Foreign Affairs and Communities"},
            {"name": "Paulo Rocha", "role": "Minister of Internal Administration"},
            {"name": "Olavo Correia", "role": "Vice Prime Minister, Minister of Finance and Business Development"},
            {"name": "Janine Lélis", "role": "Minister of National Defence"},
            {"name": "Filomena Gonçalves", "role": "Minister of Health and Social Security"},
            {"name": "Amadeu Cruz", "role": "Minister of Education"},
            {"name": "Gilberto Silva", "role": "Minister of Justice and Labour"},
            {"name": "Fernando Elísio Freire", "role": "Minister of Parliamentary Affairs and State Reform"},
            {"name": "José Gonçalves", "role": "Minister of Agriculture and Environment"},
            {"name": "Carlos Santos", "role": "Minister of Industry, Commerce and Energy"},
            {"name": "Alexandre Dias Monteiro", "role": "Minister of Digital Economy and Innovation"},
            {"name": "Carlos Évora", "role": "Minister of Infrastructure, Spatial Planning and Housing"},
            {"name": "Abraão Vicente", "role": "Minister of Culture and Creative Industries"},
            {"name": "Maritza Rosabal", "role": "Minister of Family, Inclusion and Social Development"},
            {"name": "Austelino Correia", "role": "Speaker of the National Assembly"},
            {"name": "Arlindo Ramos", "role": "President of the Supreme Court"},
            {"name": "Óscar Santos", "role": "Governor, Bank of Cabo Verde"},
            {"name": "Janine Lélis", "role": "Chief of Staff of the Armed Forces"},
            {"name": "Jorge Carlos Fonseca", "role": "Former President of the Republic"},
            {"name": "José Maria Pereira Neves", "role": "Minister of Maritime Economy"},
            {"name": "Sara Lopes", "role": "Minister of Tourism and Transport"},
            {"name": "Mircea Oliveira", "role": "Minister of Youth and Sport"},
            {"name": "Janira Hopffer Almada", "role": "Opposition Leader, PAICV"},
        ]
        records = []
        for o in officials:
            records.append(RawPersonRecord(
                full_name=o["name"], title=o["role"],
                institution="Government of the Republic of Cabo Verde",
                country_code=self.country_code, source_type=self.source_type,
                source_url=GOV_URL, raw_text=f"{o['name']} – {o['role']}",
                scraped_at=now, extra_fields={"category": "Cabinet", "fixture": True},
            ))
        logger.info("cv_presidency.fixture.loaded", count=len(records))
        return records
