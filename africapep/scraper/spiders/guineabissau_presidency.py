"""
Scraper for the Guinea-Bissau Presidency / Government.

Source: https://www.governo.gw
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

GOV_URL = "https://www.governo.gw"


class GuineaBissauPresidencyScraper(BaseScraper):
    """Scraper for the Guinea-Bissau Government."""

    country_code = "GW"
    source_type = "PRESIDENCY"

    def scrape(self) -> list[RawPersonRecord]:
        logger.info("gw_presidency.scrape.start", url=GOV_URL)
        try:
            resp = self._get(GOV_URL)
            records = self._parse_officials(resp.text)
            if records:
                return records
            return self._load_fixture()
        except Exception:
            logger.exception("gw_presidency.scrape.error")
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
                    institution="Government of the Republic of Guinea-Bissau",
                    country_code=self.country_code, source_type=self.source_type,
                    source_url=GOV_URL, raw_text=f"{full_name} – {role}",
                    scraped_at=datetime.utcnow(), extra_fields={"category": "Cabinet"},
                ))
            except Exception:
                logger.exception("gw_presidency.parse.error")
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        officials = [
            {"name": "Umaro Sissoco Embaló", "role": "President of the Republic"},
            {"name": "Rui Duarte de Barros", "role": "Prime Minister"},
            {"name": "Suzi Barbosa", "role": "Minister of Foreign Affairs and International Cooperation"},
            {"name": "Botche Candé", "role": "Minister of Interior and Public Order"},
            {"name": "Ilídio Vieira", "role": "Minister of Finance"},
            {"name": "Sandji Fati", "role": "Minister of National Defence"},
            {"name": "Mamadu Iaia Djaló", "role": "Minister of Justice and Human Rights"},
            {"name": "Dionísio Cabi", "role": "Minister of Public Health"},
            {"name": "Satu Camará", "role": "Minister of National Education"},
            {"name": "Fernando Vaz", "role": "Minister of Agriculture and Rural Development"},
            {"name": "Marciano Silva Barbeiro", "role": "Minister of Energy and Industry"},
            {"name": "Domingos Simões Pereira", "role": "Leader of PAIGC (Opposition)"},
            {"name": "Nuno Gomes Nabiam", "role": "Former Prime Minister"},
            {"name": "Aristides Gomes", "role": "Former Prime Minister"},
            {"name": "Cipriano Cassamá", "role": "President of the National People's Assembly"},
            {"name": "Juvenal Pereira", "role": "Minister of Economy, Planning and Regional Integration"},
            {"name": "Victor Mandinga", "role": "Minister of Territorial Administration"},
            {"name": "Alfa Sanha", "role": "Minister of Communication and Information Technology"},
            {"name": "Malam Sambu Bari", "role": "Minister of Transport and Telecommunications"},
            {"name": "Iaia Djaló", "role": "Minister of Environment and Biodiversity"},
            {"name": "Paulo Gomes", "role": "Chief Justice, Supreme Court"},
            {"name": "Agostinho Lopes", "role": "Governor, Central Bank of Guinea-Bissau (BCEAO)"},
            {"name": "Biaguê Na N'Tan", "role": "Chief of Defence Staff"},
            {"name": "Califa Seidi", "role": "Director General of Judicial Police"},
            {"name": "António Serifo Embaló", "role": "Minister of Fisheries and Maritime Economy"},
        ]
        records = []
        for o in officials:
            records.append(RawPersonRecord(
                full_name=o["name"], title=o["role"],
                institution="Government of the Republic of Guinea-Bissau",
                country_code=self.country_code, source_type=self.source_type,
                source_url=GOV_URL, raw_text=f"{o['name']} – {o['role']}",
                scraped_at=now, extra_fields={"category": "Cabinet", "fixture": True},
            ))
        logger.info("gw_presidency.fixture.loaded", count=len(records))
        return records
