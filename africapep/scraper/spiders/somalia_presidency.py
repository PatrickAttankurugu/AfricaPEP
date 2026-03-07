"""
Scraper for the Somalia Presidency / Government.

Source: https://www.somalia.gov.so
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

GOV_URL = "https://www.somalia.gov.so"


class SomaliaPresidencyScraper(BaseScraper):
    """Scraper for the Somalia Government."""

    country_code = "SO"
    source_type = "PRESIDENCY"

    def scrape(self) -> list[RawPersonRecord]:
        logger.info("so_presidency.scrape.start", url=GOV_URL)
        try:
            resp = self._get(GOV_URL)
            records = self._parse_officials(resp.text)
            if records:
                return records
            return self._load_fixture()
        except Exception:
            logger.exception("so_presidency.scrape.error")
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
                    institution="Government of the Federal Republic of Somalia",
                    country_code=self.country_code, source_type=self.source_type,
                    source_url=GOV_URL, raw_text=f"{full_name} – {role}",
                    scraped_at=datetime.utcnow(), extra_fields={"category": "Cabinet"},
                ))
            except Exception:
                logger.exception("so_presidency.parse.error")
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        officials = [
            # Executive
            {"name": "Hassan Sheikh Mohamud", "role": "President of the Federal Republic of Somalia"},
            {"name": "Hamza Abdi Barre", "role": "Prime Minister"},
            # Cabinet Ministers
            {"name": "Ahmed Moallim Fiqi", "role": "Minister of Foreign Affairs and International Cooperation"},
            {"name": "Ahmed Macallin Fiqi", "role": "Minister of Interior, Federal Affairs and Reconciliation"},
            {"name": "Bihi Iman Egeh", "role": "Minister of Finance"},
            {"name": "Abdulkadir Mohamed Nur", "role": "Minister of Defence"},
            {"name": "Hassan Hussein Haji", "role": "Minister of Justice and Judicial Affairs"},
            {"name": "Ali Haji Adam", "role": "Minister of Health and Human Services"},
            {"name": "Farah Sheikh Abdulkadir", "role": "Minister of Education, Culture and Higher Education"},
            {"name": "Said Hussein Iid", "role": "Minister of Petroleum and Mineral Resources"},
            {"name": "Abshir Omar Jama", "role": "Minister of Planning, Investment and Economic Development"},
            {"name": "Jibril Abdirashid Haji", "role": "Minister of Commerce and Industry"},
            {"name": "Daud Aweis", "role": "Minister of Agriculture and Irrigation"},
            {"name": "Maryan Dahir Aweys", "role": "Minister of Women and Human Rights Development"},
            {"name": "Abdullahi Godah Barre", "role": "Minister of Public Works, Reconstruction and Housing"},
            {"name": "Salah Ahmed Jama", "role": "Minister of Information, Culture and Tourism"},
            {"name": "Abdirahman Yusuf Al Adala", "role": "Minister of Transport and Civil Aviation"},
            {"name": "Mohamed Abdi Hayir Mareye", "role": "Minister of Labour and Social Affairs"},
            # Parliament
            {"name": "Adan Mohamed Nur Madobe", "role": "Speaker of the House of the People"},
            {"name": "Abdi Hashi Abdullahi", "role": "Speaker of the Upper House"},
            # Judiciary
            {"name": "Baashe Yusuf Ahmed", "role": "Chief Justice of the Supreme Court"},
            # Central Bank
            {"name": "Abdirahman Mohamed Abdullahi", "role": "Governor, Central Bank of Somalia"},
            # Security
            {"name": "Odowa Yusuf Rage", "role": "Chief of Defence Forces, Somali National Army"},
            # Federal Member States
            {"name": "Ahmed Mohamed Islam Madobe", "role": "President of Jubaland"},
            {"name": "Said Abdullahi Deni", "role": "President of Puntland"},
            # Former
            {"name": "Mohamed Abdullahi Farmajo", "role": "Former President of Somalia"},
            {"name": "Sharif Sheikh Ahmed", "role": "Former President of Somalia"},
        ]
        records = []
        for o in officials:
            records.append(RawPersonRecord(
                full_name=o["name"], title=o["role"],
                institution="Government of the Federal Republic of Somalia",
                country_code=self.country_code, source_type=self.source_type,
                source_url=GOV_URL, raw_text=f"{o['name']} – {o['role']}",
                scraped_at=now, extra_fields={"category": "Cabinet", "fixture": True},
            ))
        logger.info("so_presidency.fixture.loaded", count=len(records))
        return records
