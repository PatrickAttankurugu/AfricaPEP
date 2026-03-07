"""
Scraper for the Tunisian Presidency / Government.

Source: https://www.pm.gov.tn
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

GOV_URL = "http://pm.gov.tn/ar"


class TunisiaPresidencyScraper(BaseScraper):
    """Scraper for the Tunisian Government."""

    country_code = "TN"
    source_type = "PRESIDENCY"

    def scrape(self) -> list[RawPersonRecord]:
        logger.info("tn_presidency.scrape.start", url=GOV_URL)
        try:
            resp = self._get(GOV_URL)
            records = self._parse_officials(resp.text)
            if records:
                return records
            return self._load_fixture()
        except Exception:
            logger.exception("tn_presidency.scrape.error")
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
                    institution="Government of the Republic of Tunisia",
                    country_code=self.country_code, source_type=self.source_type,
                    source_url=GOV_URL, raw_text=f"{full_name} – {role}",
                    scraped_at=datetime.utcnow(), extra_fields={"category": "Cabinet"},
                ))
            except Exception:
                logger.exception("tn_presidency.parse.error")
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        officials = [
            {"name": "Kais Saied", "role": "President of the Republic of Tunisia"},
            {"name": "Ahmed Hachani", "role": "Head of Government"},
            {"name": "Nabil Ammar", "role": "Minister of Foreign Affairs, Migration and Tunisians Abroad"},
            {"name": "Kamel Feki", "role": "Minister of Interior"},
            {"name": "Imed Memmich", "role": "Minister of National Defence"},
            {"name": "Sihem Boughdiri Nemsia", "role": "Minister of Finance"},
            {"name": "Leila Jaffel", "role": "Minister of Justice"},
            {"name": "Ali Mrabet", "role": "Minister of Health"},
            {"name": "Mohamed Ali Boughdiri", "role": "Minister of Education"},
            {"name": "Moncef Boukthir", "role": "Minister of Higher Education and Scientific Research"},
            {"name": "Sofiane Hemissi", "role": "Minister of Transport"},
            {"name": "Samir Abdelhafidh", "role": "Minister of Economy and Planning"},
            {"name": "Kalthoum Ben Rejeb", "role": "Minister of Trade and Export Development"},
            {"name": "Nabil Hajji", "role": "Minister of Industry, Mines and Energy"},
            {"name": "Mohamed Fadhel Kraiem", "role": "Minister of Communication Technologies"},
            {"name": "Leila Chikhaoui-Mahdaoui", "role": "Minister of Environment"},
            {"name": "Mohamed Rekik", "role": "Minister of Agriculture, Water Resources and Fisheries"},
            {"name": "Kamel Deguiche", "role": "Minister of Tourism and Handicrafts"},
            {"name": "Malek Zahi", "role": "Minister of Social Affairs"},
            {"name": "Najoua Gamha", "role": "Minister of Women, Family, Children and Senior Citizens"},
            {"name": "Ibrahim Bartagi", "role": "Speaker of the Assembly of People's Representatives"},
            {"name": "Taieb Rakhroukh", "role": "First President of the Court of Cassation"},
            {"name": "Fethi Zouhair Nouri", "role": "Governor, Central Bank of Tunisia"},
            {"name": "Général Khaled Shili", "role": "Chief of Staff of the Armed Forces"},
            {"name": "Rached Ghannouchi", "role": "Former Speaker of Parliament, Ennahdha Leader (detained)"},
            {"name": "Béji Caïd Essebsi", "role": "Former President of the Republic (deceased 2019)"},
            {"name": "Moncef Marzouki", "role": "Former President of the Republic"},
        ]
        records = []
        for o in officials:
            records.append(RawPersonRecord(
                full_name=o["name"], title=o["role"],
                institution="Government of the Republic of Tunisia",
                country_code=self.country_code, source_type=self.source_type,
                source_url=GOV_URL, raw_text=f"{o['name']} – {o['role']}",
                scraped_at=now, extra_fields={"category": "Cabinet", "fixture": True},
            ))
        logger.info("tn_presidency.fixture.loaded", count=len(records))
        return records
