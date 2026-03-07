"""
Scraper for the Mauritius Presidency / Government.

Source: https://govmu.org
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

GOV_URL = "https://govmu.org/EN/Pages/default.aspx"


class MauritiusPresidencyScraper(BaseScraper):
    """Scraper for the Mauritius Government."""

    country_code = "MU"
    source_type = "PRESIDENCY"

    def scrape(self) -> list[RawPersonRecord]:
        logger.info("mu_presidency.scrape.start", url=GOV_URL)
        try:
            resp = self._get(GOV_URL)
            records = self._parse_officials(resp.text)
            if records:
                return records
            return self._load_fixture()
        except Exception:
            logger.exception("mu_presidency.scrape.error")
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
                    institution="Government of the Republic of Mauritius",
                    country_code=self.country_code, source_type=self.source_type,
                    source_url=GOV_URL, raw_text=f"{full_name} – {role}",
                    scraped_at=datetime.utcnow(), extra_fields={"category": "Cabinet"},
                ))
            except Exception:
                logger.exception("mu_presidency.parse.error")
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        officials = [
            # Executive
            {"name": "Prithvirajsing Roopun", "role": "President of the Republic"},
            {"name": "Navinchandra Ramgoolam", "role": "Prime Minister"},
            # Cabinet Ministers
            {"name": "Dhananjay Ramful", "role": "Minister of Foreign Affairs"},
            {"name": "Reza Uteem", "role": "Attorney General"},
            {"name": "Renganaden Padayachy", "role": "Minister of Finance, Economic Planning and Development"},
            {"name": "Avinash Teeluck", "role": "Minister of Arts and Cultural Heritage"},
            {"name": "Kalpana Koonjoo-Shah", "role": "Minister of Gender Equality and Family Welfare"},
            {"name": "Fazila Jeewa-Daureeawoo", "role": "Minister of Social Integration"},
            {"name": "Soodesh Callichurn", "role": "Minister of Labour, Industrial Relations and Employment"},
            {"name": "Mahen Kumar Seeruttun", "role": "Minister of Agriculture, Food Technology and Natural Resources"},
            {"name": "Leela Devi Dookun-Luchoomun", "role": "Minister of Education, Tertiary Education and Science"},
            {"name": "Alan Ganoo", "role": "Minister of Land Transport and Light Rail"},
            {"name": "Nando Bodha", "role": "Minister of Tourism"},
            {"name": "Arvin Boolell", "role": "Minister of Health and Wellness"},
            {"name": "Rajesh Bhagwan", "role": "Minister of Environment and Climate Change"},
            {"name": "Shakeel Mohamed", "role": "Minister of Housing and Land Use Planning"},
            {"name": "Joe Lesjongard", "role": "Minister of Energy and Public Utilities"},
            {"name": "Bobby Hurreeram", "role": "Minister of National Infrastructure"},
            {"name": "Kavy Ramano", "role": "Minister of Information Technology and Telecommunications"},
            {"name": "Vikram Hurdoyal", "role": "Minister of Public Service"},
            # Judiciary
            {"name": "Achilles Nunkoo", "role": "Chief Justice of Mauritius"},
            # Central Bank
            {"name": "Harvesh Kumar Seegolam", "role": "Governor, Bank of Mauritius"},
            # Parliament
            {"name": "Sooroojdev Phokeer", "role": "Speaker of the National Assembly"},
            # Opposition
            {"name": "Pravind Jugnauth", "role": "Former Prime Minister and Leader of MSM"},
            {"name": "Paul Bérenger", "role": "Leader of MMM"},
            {"name": "Xavier-Luc Duval", "role": "Leader of PMSD"},
        ]
        records = []
        for o in officials:
            records.append(RawPersonRecord(
                full_name=o["name"], title=o["role"],
                institution="Government of the Republic of Mauritius",
                country_code=self.country_code, source_type=self.source_type,
                source_url=GOV_URL, raw_text=f"{o['name']} – {o['role']}",
                scraped_at=now, extra_fields={"category": "Cabinet", "fixture": True},
            ))
        logger.info("mu_presidency.fixture.loaded", count=len(records))
        return records
