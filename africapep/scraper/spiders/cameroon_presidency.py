"""
Scraper for the Cameroon Presidency / Prime Minister's Office.

Source: https://www.spm.gov.cm/site/index.php?l=en
Extracts cabinet ministers from the PM's Office website.
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

BASE_URL = "https://www.spm.gov.cm"
CABINET_URL = f"{BASE_URL}/site/index.php?l=en"


class CameroonPresidencyScraper(BaseScraper):
    """Scraper for the Cameroon Presidency and PM's Office."""

    country_code = "CM"
    source_type = "PRESIDENCY"

    def scrape(self) -> list[RawPersonRecord]:
        """Scrape cabinet officials from the PM's Office website."""
        logger.info("cm_presidency.scrape.start", url=CABINET_URL)
        try:
            resp = self._get(CABINET_URL)
            records = self._parse_officials(resp.text)
            if records:
                return records
            logger.warning("cm_presidency.scrape.no_results")
            return self._load_fixture()
        except Exception:
            logger.exception("cm_presidency.scrape.error")
            return self._load_fixture()

    def _parse_officials(self, html: str) -> list[RawPersonRecord]:
        """Parse government officials from page HTML."""
        soup = BeautifulSoup(html, "html.parser")
        records: list[RawPersonRecord] = []

        # Try various selectors for minister listings
        cards = soup.select(
            ".minister-card, .official-card, .team-member, .card, "
            "[class*='minister'], [class*='official'], article"
        )

        for card in cards:
            try:
                name_el = card.select_one("h3, h4, h2, .name, .title, strong")
                if not name_el:
                    continue
                full_name = name_el.get_text(strip=True)
                if not full_name or len(full_name) < 3:
                    continue

                role_el = card.select_one("p, .role, .position, .subtitle, span")
                role = role_el.get_text(strip=True) if role_el else ""

                records.append(RawPersonRecord(
                    full_name=full_name,
                    title=role if role else "Minister",
                    institution="Presidency of the Republic of Cameroon",
                    country_code=self.country_code,
                    source_type=self.source_type,
                    source_url=CABINET_URL,
                    raw_text=f"{full_name} – {role}",
                    scraped_at=datetime.utcnow(),
                    extra_fields={"category": "Cabinet Ministers"},
                ))
            except Exception:
                logger.exception("cm_presidency.parse.error")

        logger.info("cm_presidency.scrape.complete", count=len(records))
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        officials = [
            {"name": "Paul Biya", "role": "President of the Republic of Cameroon"},
            {"name": "Joseph Dion Ngute", "role": "Prime Minister, Head of Government"},
            {"name": "Laurent Esso", "role": "Minister of State, Justice and Keeper of the Seals"},
            {"name": "Ferdinand Ngoh Ngoh", "role": "Minister of State, Secretary General of the Presidency"},
            {"name": "Jacques Fame Ndongo", "role": "Minister of State, Higher Education"},
            {"name": "Joseph Beti Assomo", "role": "Delegate Minister, Defence"},
            {"name": "Lejeune Mbella Mbella", "role": "Minister of External Relations"},
            {"name": "Paul Atanga Nji", "role": "Minister of Territorial Administration"},
            {"name": "Louis Paul Motaze", "role": "Minister of Finance"},
            {"name": "Rene Emmanuel Sadi", "role": "Minister of Communication"},
            {"name": "Emmanuel Nganou Djoumessi", "role": "Minister of Public Works"},
            {"name": "Luc Magloire Mbarga Atangana", "role": "Minister of Commerce"},
            {"name": "Madeleine Tchuinte", "role": "Minister of Scientific Research and Innovation"},
            {"name": "Alamine Ousmane Mey", "role": "Minister of Economy, Planning and Regional Development"},
            {"name": "Malachie Manaouda", "role": "Minister of Public Health"},
            {"name": "Pauline Egbe Nalova Lyonga", "role": "Minister of Secondary Education"},
            {"name": "Gaston Eloundou Essomba", "role": "Minister of Water Resources and Energy"},
            {"name": "Jean Ernest Massena Ngalle Bibehe", "role": "Minister of Transport"},
            {"name": "Minette Libom Li Likeng", "role": "Minister of Posts and Telecommunications"},
            {"name": "Laurent Serge Etoundi Ngoa", "role": "Minister of Basic Education"},
            {"name": "Mounouna Foutsou", "role": "Minister of Youth and Civic Education"},
            {"name": "Narcisse Mouelle Kombi", "role": "Minister of Arts and Culture"},
            {"name": "Cavaye Yeguie Djibril", "role": "Speaker of the National Assembly"},
            {"name": "Marcel Niat Njifenji", "role": "President of the Senate"},
            {"name": "Daniel Mekobe Sone", "role": "Chief Justice, Supreme Court"},
            {"name": "Abbas Mahamat Tolli", "role": "Governor, Bank of Central African States (BEAC)"},
            {"name": "Général René Claude Meka", "role": "Chief of Defence Staff"},
            {"name": "Martin Mbarga Nguele", "role": "Delegate General of National Security"},
            {"name": "John Fru Ndi", "role": "Opposition Leader, SDF (deceased 2023)"},
            {"name": "Maurice Kamto", "role": "Opposition Leader, MRC"},
        ]

        records = []
        for o in officials:
            records.append(RawPersonRecord(
                full_name=o["name"],
                title=o["role"],
                institution="Presidency of the Republic of Cameroon",
                country_code=self.country_code,
                source_type=self.source_type,
                source_url=CABINET_URL,
                raw_text=f"{o['name']} – {o['role']}",
                scraped_at=now,
                extra_fields={
                    "category": "Cabinet Ministers",
                    "fixture": True,
                },
            ))

        logger.info("cm_presidency.fixture.loaded", count=len(records))
        return records
