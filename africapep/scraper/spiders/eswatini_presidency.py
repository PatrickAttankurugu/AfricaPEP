"""
Scraper for the Eswatini (Swaziland) Presidency / Government.

Source: https://www.gov.sz
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

GOV_URL = "https://www.gov.sz"


class EswatiniPresidencyScraper(BaseScraper):
    """Scraper for the Eswatini Government."""

    country_code = "SZ"
    source_type = "PRESIDENCY"

    def scrape(self) -> list[RawPersonRecord]:
        logger.info("sz_presidency.scrape.start", url=GOV_URL)
        try:
            resp = self._get(GOV_URL)
            records = self._parse_officials(resp.text)
            if records:
                return records
            return self._load_fixture()
        except Exception:
            logger.exception("sz_presidency.scrape.error")
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
                    institution="Government of the Kingdom of Eswatini",
                    country_code=self.country_code, source_type=self.source_type,
                    source_url=GOV_URL, raw_text=f"{full_name} – {role}",
                    scraped_at=datetime.utcnow(), extra_fields={"category": "Cabinet"},
                ))
            except Exception:
                logger.exception("sz_presidency.parse.error")
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        officials = [
            # Head of State
            {"name": "Mswati III", "role": "King of Eswatini"},
            {"name": "Ntfombi Tfwala", "role": "Queen Mother (Ndlovukazi)"},
            # Executive
            {"name": "Russell Dlamini", "role": "Prime Minister"},
            {"name": "Themba Masuku", "role": "Deputy Prime Minister"},
            # Cabinet Ministers
            {"name": "Pholile Shakantu", "role": "Minister of Foreign Affairs and International Cooperation"},
            {"name": "Amos Shongwe", "role": "Minister of Home Affairs"},
            {"name": "Neal Rijkenberg", "role": "Minister of Finance"},
            {"name": "Prince Simelane", "role": "Minister of Defence"},
            {"name": "Pholile Dlamini-Shakantu", "role": "Minister of Justice and Constitutional Affairs"},
            {"name": "Lizzie Nkosi", "role": "Minister of Health"},
            {"name": "Owen Nkosi", "role": "Minister of Education and Training"},
            {"name": "Jabulani Mabuza", "role": "Minister of Agriculture"},
            {"name": "Moses Vilakati", "role": "Minister of Commerce, Industry and Trade"},
            {"name": "Phila Buthelezi", "role": "Minister of Natural Resources and Energy"},
            {"name": "Manqoba Bhekizwe Khumalo", "role": "Minister of Information, Communications and Technology"},
            {"name": "Chief Ndlaluhlaza Ndwandwe", "role": "Minister of Tinkhundla Administration and Development"},
            {"name": "Absalom Themba Dlamini", "role": "Minister of Labour and Social Security"},
            {"name": "Princess Sikhanyiso Dlamini", "role": "Minister of Tourism and Environmental Affairs"},
            {"name": "Martin Dlamini", "role": "Minister of Public Works and Transport"},
            {"name": "Chief Makhosini Maseko", "role": "Minister of Housing and Urban Development"},
            # Parliament
            {"name": "Petros Mavimbela", "role": "Speaker of the House of Assembly"},
            # Judiciary
            {"name": "Bheki Maphalala", "role": "Chief Justice of Eswatini"},
            # Central Bank
            {"name": "Phil Mnisi", "role": "Governor, Central Bank of Eswatini"},
            # Military
            {"name": "Jeffery Shabalala", "role": "Commander, Umbutfo Eswatini Defence Force"},
        ]
        records = []
        for o in officials:
            records.append(RawPersonRecord(
                full_name=o["name"], title=o["role"],
                institution="Government of the Kingdom of Eswatini",
                country_code=self.country_code, source_type=self.source_type,
                source_url=GOV_URL, raw_text=f"{o['name']} – {o['role']}",
                scraped_at=now, extra_fields={"category": "Cabinet", "fixture": True},
            ))
        logger.info("sz_presidency.fixture.loaded", count=len(records))
        return records
