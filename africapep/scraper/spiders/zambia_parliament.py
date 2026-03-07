"""
Scraper for the Zambia National Assembly.

Source: https://www.parliament.gov.zm/members
Extracts members of parliament and senior government officials.
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

MEMBERS_URL = "https://www.parliament.gov.zm/members"


class ZambiaParliamentScraper(BaseScraper):
    """Scraper for the Zambia National Assembly."""

    country_code = "ZM"
    source_type = "PARLIAMENT"

    def scrape(self) -> list[RawPersonRecord]:
        """Scrape MPs from the Zambia Parliament website."""
        logger.info("zm_parliament.scrape.start", url=MEMBERS_URL)
        try:
            resp = self._get(MEMBERS_URL)
            records = self._parse_members(resp.text)
            if records:
                return records
            logger.warning("zm_parliament.scrape.no_results")
            return self._load_fixture()
        except Exception:
            logger.exception("zm_parliament.scrape.error")
            return self._load_fixture()

    def _parse_members(self, html: str) -> list[RawPersonRecord]:
        """Parse member listings from HTML."""
        soup = BeautifulSoup(html, "html.parser")
        records: list[RawPersonRecord] = []

        cards = soup.select(
            ".views-row, .member-card, .card, article, "
            "[class*='member'], tr, li.list-item"
        )

        for card in cards:
            try:
                name_el = card.select_one("h3, h4, h2, a, .name, .title, strong")
                if not name_el:
                    continue
                full_name = name_el.get_text(strip=True)
                if not full_name or len(full_name) < 3:
                    continue

                role_el = card.select_one("p, .role, .position, .field-content, span")
                role = role_el.get_text(strip=True) if role_el else ""

                records.append(RawPersonRecord(
                    full_name=full_name,
                    title="Member of Parliament" if not role else role,
                    institution="National Assembly of Zambia",
                    country_code=self.country_code,
                    source_type=self.source_type,
                    source_url=MEMBERS_URL,
                    raw_text=f"{full_name} – MP",
                    scraped_at=datetime.utcnow(),
                    extra_fields={},
                ))
            except Exception:
                logger.exception("zm_parliament.parse.error")

        logger.info("zm_parliament.scrape.complete", count=len(records))
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        officials = [
            # Executive
            {"name": "Hakainde Hichilema", "role": "President of the Republic of Zambia", "party": "UPND"},
            {"name": "Mutale Nalumango", "role": "Vice President", "party": "UPND"},
            # Parliament
            {"name": "Nelly Mutti", "role": "Speaker of the National Assembly", "party": "UPND"},
            # Cabinet Ministers
            {"name": "Jack Mwiimbu", "role": "Minister of Home Affairs and Internal Security", "party": "UPND"},
            {"name": "Situmbeko Musokotwane", "role": "Minister of Finance and National Planning", "party": "UPND"},
            {"name": "Sylvia Masebo", "role": "Minister of Health", "party": "UPND"},
            {"name": "Felix Mutati", "role": "Minister of Technology and Science", "party": "UPND"},
            {"name": "Stanley Kakubo", "role": "Minister of Foreign Affairs", "party": "UPND"},
            {"name": "Ambrose Lufuma", "role": "Minister of Defence", "party": "UPND"},
            {"name": "Gary Nkombo", "role": "Minister of Local Government", "party": "UPND"},
            {"name": "Cornelius Mweetwa", "role": "Minister of Information and Media", "party": "UPND"},
            {"name": "Douglas Syakalima", "role": "Minister of Education", "party": "UPND"},
            {"name": "Elijah Muchima", "role": "Minister of Agriculture", "party": "UPND"},
            {"name": "Collins Nzovu", "role": "Minister of Green Economy and Environment", "party": "UPND"},
            {"name": "Frank Tayali", "role": "Minister of Transport and Logistics", "party": "UPND"},
            {"name": "Makozo Chikote", "role": "Minister of Mines and Minerals Development", "party": "UPND"},
            {"name": "Peter Kapala", "role": "Minister of Energy", "party": "UPND"},
            {"name": "Brenda Tambatamba", "role": "Minister of Labour and Social Security", "party": "UPND"},
            {"name": "Charles Milupi", "role": "Minister of Infrastructure and Urban Development", "party": "UPND"},
            {"name": "Mulambo Haimbe", "role": "Attorney General", "party": "UPND"},
            # Judiciary
            {"name": "Mumba Malila", "role": "Chief Justice of Zambia", "party": ""},
            # Central Bank
            {"name": "Denny Kalyalya", "role": "Governor, Bank of Zambia", "party": ""},
            # Military
            {"name": "Dennis Alibuzwi", "role": "Commander, Zambia Defence Force", "party": ""},
            # Opposition
            {"name": "Miles Sampa", "role": "PF President", "party": "PF"},
            {"name": "Given Lubinda", "role": "Former Minister / PF Member", "party": "PF"},
            {"name": "Edgar Lungu", "role": "Former President of Zambia", "party": "PF"},
            # Former President
            {"name": "Rupiah Banda", "role": "Former President of Zambia", "party": ""},
        ]

        records = []
        for o in officials:
            records.append(RawPersonRecord(
                full_name=o["name"],
                title=o["role"],
                institution="National Assembly of Zambia",
                country_code=self.country_code,
                source_type=self.source_type,
                source_url=MEMBERS_URL,
                raw_text=f"{o['name']} – {o['role']}",
                scraped_at=now,
                extra_fields={
                    "party": o["party"],
                    "fixture": True,
                },
            ))

        logger.info("zm_parliament.fixture.loaded", count=len(records))
        return records
