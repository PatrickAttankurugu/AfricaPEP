"""
Scraper for the Mauritania Presidency / Government.

Source: https://www.presidence.mr
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

GOV_URL = "https://www.presidence.mr"


class MauritaniaPresidencyScraper(BaseScraper):
    """Scraper for the Mauritania Government."""

    country_code = "MR"
    source_type = "PRESIDENCY"

    def scrape(self) -> list[RawPersonRecord]:
        logger.info("mr_presidency.scrape.start", url=GOV_URL)
        try:
            resp = self._get(GOV_URL)
            records = self._parse_officials(resp.text)
            if records:
                return records
            return self._load_fixture()
        except Exception:
            logger.exception("mr_presidency.scrape.error")
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
                    institution="Government of the Islamic Republic of Mauritania",
                    country_code=self.country_code, source_type=self.source_type,
                    source_url=GOV_URL, raw_text=f"{full_name} – {role}",
                    scraped_at=datetime.utcnow(), extra_fields={"category": "Cabinet"},
                ))
            except Exception:
                logger.exception("mr_presidency.parse.error")
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        officials = [
            {"name": "Mohamed Ould Ghazouani", "role": "President of the Islamic Republic of Mauritania"},
            {"name": "Mouhamed Ould Bilal Messoud", "role": "Prime Minister"},
            {"name": "Mohamed Salem Ould Merzoug", "role": "Minister of Foreign Affairs, Cooperation and Mauritanians Abroad"},
            {"name": "Mohamed Ahmed Ould Mohamed Lemine", "role": "Minister of Interior and Decentralisation"},
            {"name": "Isselmou Ould Mohamed M'Bady", "role": "Minister of Finance"},
            {"name": "Hanena Ould Sidi", "role": "Minister of Defence"},
            {"name": "Mohamed Mahmoud Ould Boya", "role": "Minister of Justice"},
            {"name": "Mohamed Nedhirou Ould Hamed", "role": "Minister of Health"},
            {"name": "Mohamed Melainine Ould Eyih", "role": "Minister of National Education and Reform"},
            {"name": "Dy Ould Zein", "role": "Minister of Agriculture"},
            {"name": "Abdessalam Ould Mohamed Saleh", "role": "Minister of Petroleum, Mines and Energy"},
            {"name": "Naha Mint Mouknass", "role": "Minister of Environment and Sustainable Development"},
            {"name": "Moctar Ould Djay", "role": "Minister of Economy and Sustainable Development"},
            {"name": "Mohamed Ould Abdel Vetah", "role": "Minister of Equipment, Transport and Communication"},
            {"name": "Sidi Mohamed Ould Taleb Amar", "role": "Minister of Higher Education and Scientific Research"},
            {"name": "Hamadi Ould Meimou", "role": "Minister of Islamic Affairs and Traditional Education"},
            {"name": "Mohamed Abdallahi Ould Oudaa", "role": "Minister of Trade, Industry and Tourism"},
            {"name": "Yahya Ould Abdel Daim", "role": "Minister of Water and Sanitation"},
            {"name": "Mohamed Lemine Ould Aboye", "role": "Minister of Fisheries and Maritime Economy"},
            {"name": "Mohamedou Mbareck Ould Seyidi", "role": "Speaker of the National Assembly"},
            {"name": "Hademine Ould Saleck", "role": "Chief Justice, Supreme Court"},
            {"name": "Cheikh El Kebir Moulaye Taher", "role": "Governor, Central Bank of Mauritania"},
            {"name": "Général Mohamed Ould Cheikh Mohamed Ahmed Ghazouani", "role": "Chief of Defence Staff"},
            {"name": "Messaoud Ould Boulkheir", "role": "Former Speaker, Anti-Slavery Activist"},
            {"name": "Mohamed Ould Abdel Aziz", "role": "Former President of the Republic"},
            {"name": "Biram Dah Abeid", "role": "Opposition Leader, Anti-Slavery Activist"},
        ]
        records = []
        for o in officials:
            records.append(RawPersonRecord(
                full_name=o["name"], title=o["role"],
                institution="Government of the Islamic Republic of Mauritania",
                country_code=self.country_code, source_type=self.source_type,
                source_url=GOV_URL, raw_text=f"{o['name']} – {o['role']}",
                scraped_at=now, extra_fields={"category": "Cabinet", "fixture": True},
            ))
        logger.info("mr_presidency.fixture.loaded", count=len(records))
        return records
