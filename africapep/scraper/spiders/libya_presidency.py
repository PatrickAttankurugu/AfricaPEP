"""
Scraper for the Libya Presidency / Government.

Source: https://www.pm.gov.ly
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

GOV_URL = "https://www.pm.gov.ly"


class LibyaPresidencyScraper(BaseScraper):
    """Scraper for the Libya Government."""

    country_code = "LY"
    source_type = "PRESIDENCY"

    def scrape(self) -> list[RawPersonRecord]:
        logger.info("ly_presidency.scrape.start", url=GOV_URL)
        try:
            resp = self._get(GOV_URL)
            records = self._parse_officials(resp.text)
            if records:
                return records
            return self._load_fixture()
        except Exception:
            logger.exception("ly_presidency.scrape.error")
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
                    institution="Government of the State of Libya",
                    country_code=self.country_code, source_type=self.source_type,
                    source_url=GOV_URL, raw_text=f"{full_name} – {role}",
                    scraped_at=datetime.utcnow(), extra_fields={"category": "Cabinet"},
                ))
            except Exception:
                logger.exception("ly_presidency.parse.error")
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        officials = [
            {"name": "Mohamed al-Menfi", "role": "Chairman of the Presidential Council"},
            {"name": "Abdul Hamid Dbeibeh", "role": "Prime Minister (Government of National Unity - Tripoli)"},
            {"name": "Najla el-Mangoush", "role": "Former Minister of Foreign Affairs (GNU)"},
            {"name": "Emad al-Trabelsi", "role": "Minister of Interior (GNU)"},
            {"name": "Khalid al-Mabrouk", "role": "Minister of Finance (GNU)"},
            {"name": "Ahmed Ali Abu-Khzam", "role": "Minister of Defence (GNU)"},
            {"name": "Halima Ibrahim Abdulrahman", "role": "Minister of Justice (GNU)"},
            {"name": "Ramadan Abu Janah", "role": "Minister of Health (GNU)"},
            {"name": "Mousa al-Mgarief", "role": "Minister of Education (GNU)"},
            {"name": "Mohamed Aoun", "role": "Minister of Oil and Gas (GNU)"},
            {"name": "Aguila Saleh Issa", "role": "Speaker of House of Representatives (Tobruk)"},
            {"name": "Khaled al-Mishri", "role": "Head of High Council of State"},
            {"name": "Osama Hammad", "role": "Prime Minister (Eastern Government - Benghazi)"},
            {"name": "Khalifa Haftar", "role": "Commander of the Libyan National Army (East)"},
            {"name": "Saddam Haftar", "role": "Commander, Sub-Unit of Libyan National Army"},
            {"name": "Fathi Bashagha", "role": "Former Prime Minister (Eastern Government)"},
            {"name": "Taher al-Baour", "role": "Minister of Foreign Affairs (GNU)"},
            {"name": "Wedad al-Boueshi", "role": "Minister of Women's Affairs (GNU)"},
            {"name": "Ali al-Abed", "role": "Minister of Planning (GNU)"},
            {"name": "Farhat Bengdara", "role": "Chairman, National Oil Corporation"},
            {"name": "Mohamed al-Shukri", "role": "Chief Justice, Supreme Court"},
            {"name": "Saddek al-Kaber", "role": "Governor, Central Bank of Libya"},
            {"name": "Général Mohamed al-Haddad", "role": "Chief of Staff, Government Forces (Tripoli)"},
            {"name": "Abdel Moneim al-Arfi", "role": "Minister of Economy and Trade (GNU)"},
            {"name": "Musa al-Koni", "role": "Vice Chairman of the Presidential Council"},
            {"name": "Abdullah al-Lafi", "role": "Vice Chairman of the Presidential Council"},
        ]
        records = []
        for o in officials:
            records.append(RawPersonRecord(
                full_name=o["name"], title=o["role"],
                institution="Government of the State of Libya",
                country_code=self.country_code, source_type=self.source_type,
                source_url=GOV_URL, raw_text=f"{o['name']} – {o['role']}",
                scraped_at=now, extra_fields={"category": "Cabinet", "fixture": True},
            ))
        logger.info("ly_presidency.fixture.loaded", count=len(records))
        return records
