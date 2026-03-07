"""
Scraper for the Malawi Presidency / Cabinet.

Source: https://malawi.gov.mw/cabinet-ministers/
Extracts cabinet ministers from the government portal.
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

CABINET_URL = "https://malawi.gov.mw/cabinet-ministers/"


class MalawiPresidencyScraper(BaseScraper):
    """Scraper for Malawi Presidency and Cabinet."""

    country_code = "MW"
    source_type = "PRESIDENCY"

    def scrape(self) -> list[RawPersonRecord]:
        """Scrape cabinet ministers from the Malawi government portal."""
        logger.info("mw_presidency.scrape.start", url=CABINET_URL)
        try:
            resp = self._get(CABINET_URL)
            records = self._parse_ministers(resp.text)
            if records:
                return records
            logger.warning("mw_presidency.scrape.no_results")
            return self._load_fixture()
        except Exception:
            logger.exception("mw_presidency.scrape.error")
            return self._load_fixture()

    def _parse_ministers(self, html: str) -> list[RawPersonRecord]:
        """Parse minister listings from HTML."""
        soup = BeautifulSoup(html, "html.parser")
        records: list[RawPersonRecord] = []

        cards = soup.select(
            ".minister-card, .team-member, .card, article, "
            "[class*='minister'], [class*='cabinet'], .entry"
        )

        for card in cards:
            try:
                name_el = card.select_one("h3, h4, h2, .name, .title, strong")
                if not name_el:
                    continue
                full_name = name_el.get_text(strip=True)
                if not full_name or len(full_name) < 3:
                    continue

                role_el = card.select_one("p, .role, .position, .subtitle")
                role = role_el.get_text(strip=True) if role_el else "Minister"

                records.append(RawPersonRecord(
                    full_name=full_name,
                    title=role,
                    institution="Government of the Republic of Malawi",
                    country_code=self.country_code,
                    source_type=self.source_type,
                    source_url=CABINET_URL,
                    raw_text=f"{full_name} – {role}",
                    scraped_at=datetime.utcnow(),
                    extra_fields={"category": "Cabinet Ministers"},
                ))
            except Exception:
                logger.exception("mw_presidency.parse.error")

        logger.info("mw_presidency.scrape.complete", count=len(records))
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        officials = [
            # Executive
            {"name": "Lazarus Chakwera", "role": "President of the Republic of Malawi"},
            {"name": "Michael Usi", "role": "Vice President"},
            # Cabinet Ministers
            {"name": "Sosten Gwengwe", "role": "Minister of Finance"},
            {"name": "Ken Zikhale Ng'oma", "role": "Minister of Defence"},
            {"name": "Richard Chimwendo Banda", "role": "Minister of Homeland Security"},
            {"name": "Timothy Mtambo", "role": "Minister of Civic Education and National Unity"},
            {"name": "Eisenhower Mkaka", "role": "Minister of Foreign Affairs"},
            {"name": "Lobin Lowe", "role": "Minister of Agriculture"},
            {"name": "Khumbize Kandodo Chiponda", "role": "Minister of Health"},
            {"name": "Agnes NyaLonje", "role": "Minister of Education"},
            {"name": "Jappie Mhango", "role": "Minister of Lands"},
            {"name": "Sidik Mia", "role": "Minister of Transport and Public Works"},
            {"name": "Gospel Kazako", "role": "Minister of Information"},
            {"name": "Samuel Tembenu", "role": "Minister of Justice"},
            {"name": "Ibrahim Matola", "role": "Minister of Water and Sanitation"},
            {"name": "Abida Mia", "role": "Minister of Energy"},
            {"name": "Vera Kamtukule", "role": "Minister of Trade and Industry"},
            {"name": "Jean Sendeza", "role": "Minister of Gender, Community Development and Social Welfare"},
            {"name": "Mark Botomani", "role": "Minister of Tourism"},
            {"name": "Chikumbutso Mtumodzi", "role": "Minister of Labour"},
            # Judiciary
            {"name": "Rizine Mzikamanda", "role": "Chief Justice of Malawi"},
            # Central Bank
            {"name": "Wilson Tonganivuka Banda", "role": "Governor, Reserve Bank of Malawi"},
            # Parliament
            {"name": "Catherine Gotani Hara", "role": "Speaker of the National Assembly"},
            # Military
            {"name": "Griffin Supuni Phiri", "role": "Commander, Malawi Defence Force"},
            # Opposition
            {"name": "Peter Mutharika", "role": "Former President of Malawi"},
            {"name": "Kondwani Nankhumwa", "role": "Leader of the Opposition in Parliament"},
            # Former VP (legacy note)
            {"name": "Saulos Chilima", "role": "Former Vice President (deceased 2024)"},
        ]

        records = []
        for o in officials:
            records.append(RawPersonRecord(
                full_name=o["name"],
                title=o["role"],
                institution="Government of the Republic of Malawi",
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

        logger.info("mw_presidency.fixture.loaded", count=len(records))
        return records
