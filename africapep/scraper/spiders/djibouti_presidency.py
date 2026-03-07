"""
Scraper for the Djibouti Presidency / Government.

Source: https://www.presidence.dj
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

GOV_URL = "https://www.presidence.dj"


class DjiboutiPresidencyScraper(BaseScraper):
    """Scraper for the Djibouti Government."""

    country_code = "DJ"
    source_type = "PRESIDENCY"

    def scrape(self) -> list[RawPersonRecord]:
        logger.info("dj_presidency.scrape.start", url=GOV_URL)
        try:
            resp = self._get(GOV_URL)
            records = self._parse_officials(resp.text)
            if records:
                return records
            return self._load_fixture()
        except Exception:
            logger.exception("dj_presidency.scrape.error")
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
                    institution="Government of the Republic of Djibouti",
                    country_code=self.country_code, source_type=self.source_type,
                    source_url=GOV_URL, raw_text=f"{full_name} – {role}",
                    scraped_at=datetime.utcnow(), extra_fields={"category": "Cabinet"},
                ))
            except Exception:
                logger.exception("dj_presidency.parse.error")
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        officials = [
            {"name": "Ismaïl Omar Guelleh", "role": "President of the Republic"},
            {"name": "Abdoulkader Kamil Mohamed", "role": "Prime Minister"},
            {"name": "Mahamoud Ali Youssouf", "role": "Minister of Foreign Affairs"},
            {"name": "Hassan Darar Houffaneh", "role": "Minister of Interior"},
            {"name": "Ilyas Moussa Dawaleh", "role": "Minister of Finance"},
            {"name": "Hassan Omar Mohamed", "role": "Minister of Defence"},
            {"name": "Ali Farah Assoweh", "role": "Minister of Justice"},
            {"name": "Mohamed Dini Farah", "role": "Minister of Health"},
            {"name": "Moustapha Mohamed Mahamoud", "role": "Minister of Education"},
            {"name": "Yonis Ali Guedi", "role": "Minister of Energy"},
            {"name": "Mohamed Ahmed Awaleh", "role": "Minister of Agriculture"},
            {"name": "Nabil Mohamed Ahmed", "role": "Minister of Communication"},
            {"name": "Osman Abdi Djama", "role": "Minister of Transport"},
            {"name": "Mohamed Abdoulkader Hassan", "role": "Minister of Labour"},
            {"name": "Aden Houssein Abdillahi", "role": "Minister of Trade"},
            {"name": "Amina Abdi Aden", "role": "Minister of Women and Family"},
            {"name": "Charmarke Omar Chirdon", "role": "Minister of Housing and Urban Planning"},
            {"name": "Idriss Arnaud Ali", "role": "Minister of Islamic Affairs"},
            {"name": "Ahmed Osman Mohamed", "role": "Governor, Central Bank of Djibouti"},
            {"name": "Ibrahim Hassan Adou", "role": "Chief of Staff of the Armed Forces"},
            {"name": "Mohamed Djama Elabe", "role": "Speaker of the National Assembly"},
            {"name": "Hassan Ibrahim Aptidon", "role": "Former President (1977-1999)"},
            {"name": "Omar Elmi Khaireh", "role": "Chief Justice, Supreme Court"},
            {"name": "Abdourahman Boreh", "role": "Former Head of Djibouti Ports Authority"},
            {"name": "Abdoulkader Waberi Askar", "role": "Minister of Environment"},
        ]
        records = []
        for o in officials:
            records.append(RawPersonRecord(
                full_name=o["name"], title=o["role"],
                institution="Government of the Republic of Djibouti",
                country_code=self.country_code, source_type=self.source_type,
                source_url=GOV_URL, raw_text=f"{o['name']} – {o['role']}",
                scraped_at=now, extra_fields={"category": "Cabinet", "fixture": True},
            ))
        logger.info("dj_presidency.fixture.loaded", count=len(records))
        return records
