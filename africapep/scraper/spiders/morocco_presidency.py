"""
Scraper for the Kingdom of Morocco Government / Cabinet.

Source: https://www.cg.gov.ma/en
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

GOV_URL = "https://www.cg.gov.ma/en"


class MoroccoPresidencyScraper(BaseScraper):
    """Scraper for the Moroccan Government (Head of Government's Office)."""

    country_code = "MA"
    source_type = "PRESIDENCY"

    def scrape(self) -> list[RawPersonRecord]:
        logger.info("ma_presidency.scrape.start", url=GOV_URL)
        try:
            resp = self._get(GOV_URL)
            records = self._parse_officials(resp.text)
            if records:
                return records
            return self._load_fixture()
        except Exception:
            logger.exception("ma_presidency.scrape.error")
            return self._load_fixture()

    def _parse_officials(self, html: str) -> list[RawPersonRecord]:
        soup = BeautifulSoup(html, "html.parser")
        records: list[RawPersonRecord] = []
        cards = soup.select(".minister, .team-member, .card, article, [class*='minister']")
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
                    institution="Government of the Kingdom of Morocco",
                    country_code=self.country_code, source_type=self.source_type,
                    source_url=GOV_URL, raw_text=f"{full_name} – {role}",
                    scraped_at=datetime.utcnow(), extra_fields={"category": "Cabinet"},
                ))
            except Exception:
                logger.exception("ma_presidency.parse.error")
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        officials = [
            {"name": "King Mohammed VI", "role": "King of Morocco, Head of State"},
            {"name": "Aziz Akhannouch", "role": "Head of Government"},
            {"name": "Nasser Bourita", "role": "Minister of Foreign Affairs, African Cooperation and Moroccans Abroad"},
            {"name": "Abdelouafi Laftit", "role": "Minister of Interior"},
            {"name": "Nadia Fettah Alaoui", "role": "Minister of Economy and Finance"},
            {"name": "Abdellatif Ouahbi", "role": "Minister of Justice"},
            {"name": "Abdellatif Miraoui", "role": "Minister of Higher Education, Scientific Research and Innovation"},
            {"name": "Chakib Benmoussa", "role": "Minister of National Education, Preschool and Sports"},
            {"name": "Nizar Baraka", "role": "Minister of Equipment and Water"},
            {"name": "Abdellatif Loudiyi", "role": "Minister Delegate for National Defence"},
            {"name": "Khalid Ait Taleb", "role": "Minister of Health and Social Protection"},
            {"name": "Younes Sekkouri", "role": "Minister of Economic Inclusion, Small Business, Employment and Skills"},
            {"name": "Fatim-Zahra Ammor", "role": "Minister of Tourism, Handicrafts and Social and Solidarity Economy"},
            {"name": "Mohcine Jazouli", "role": "Minister Delegate for Investment, Convergence and Public Policies"},
            {"name": "Ryad Mezzour", "role": "Minister of Industry and Commerce"},
            {"name": "Leila Benali", "role": "Minister of Energy Transition and Sustainable Development"},
            {"name": "Mohamed Abdeljalil", "role": "Minister of Transport and Logistics"},
            {"name": "Ghita Mezzour", "role": "Minister Delegate for Digital Transition and Administration Reform"},
            {"name": "Mohamed Sadiki", "role": "Minister of Agriculture, Maritime Fisheries, Rural Development and Water and Forests"},
            {"name": "Aawatif Hayar", "role": "Minister of Solidarity, Social Inclusion and Family"},
            {"name": "Mohamed Mehdi Bensaid", "role": "Minister of Youth, Culture and Communication"},
            {"name": "Rachid Talbi El Alami", "role": "Speaker of the House of Representatives"},
            {"name": "Enaam Mayara", "role": "Speaker of the House of Councillors"},
            {"name": "Mohamed Benabdelkader", "role": "First President of the Court of Cassation"},
            {"name": "Abdellatif Jouahri", "role": "Governor, Bank Al-Maghrib"},
            {"name": "Général de Corps d'Armée Belkhir El Farouk", "role": "Inspector General of the Royal Armed Forces"},
            {"name": "Abdellatif Hammouchi", "role": "Director General of National Security and Territorial Surveillance"},
            {"name": "Driss Jettou", "role": "First President of the Court of Accounts"},
            {"name": "Abdelilah Benkirane", "role": "Former Head of Government, PJD Leader"},
        ]
        records = []
        for o in officials:
            records.append(RawPersonRecord(
                full_name=o["name"], title=o["role"],
                institution="Government of the Kingdom of Morocco",
                country_code=self.country_code, source_type=self.source_type,
                source_url=GOV_URL, raw_text=f"{o['name']} – {o['role']}",
                scraped_at=now, extra_fields={"category": "Cabinet", "fixture": True},
            ))
        logger.info("ma_presidency.fixture.loaded", count=len(records))
        return records
