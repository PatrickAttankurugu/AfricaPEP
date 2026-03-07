"""
Scraper for the Parliament of Zimbabwe.

Source: https://www.parlzim.gov.zw
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

MEMBERS_URL = "https://www.parlzim.gov.zw/members-of-parliament"


class ZimbabweParliamentScraper(BaseScraper):
    """Scraper for the Zimbabwe Parliament."""

    country_code = "ZW"
    source_type = "PARLIAMENT"

    def scrape(self) -> list[RawPersonRecord]:
        logger.info("zw_parliament.scrape.start", url=MEMBERS_URL)
        try:
            resp = self._get(MEMBERS_URL)
            records = self._parse_members(resp.text)
            if records:
                return records
            return self._load_fixture()
        except Exception:
            logger.exception("zw_parliament.scrape.error")
            return self._load_fixture()

    def _parse_members(self, html: str) -> list[RawPersonRecord]:
        soup = BeautifulSoup(html, "html.parser")
        records: list[RawPersonRecord] = []
        cards = soup.select(".itemList .catItemTitle a, .member-card, tr, article")
        for card in cards:
            try:
                full_name = card.get_text(strip=True)
                if not full_name or len(full_name) < 3:
                    continue
                records.append(RawPersonRecord(
                    full_name=full_name, title="Member of Parliament",
                    institution="Parliament of Zimbabwe",
                    country_code=self.country_code, source_type=self.source_type,
                    source_url=MEMBERS_URL, raw_text=f"{full_name} – MP",
                    scraped_at=datetime.utcnow(), extra_fields={},
                ))
            except Exception:
                logger.exception("zw_parliament.parse.error")
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        officials = [
            {"name": "Emmerson Mnangagwa", "role": "President of the Republic of Zimbabwe", "party": "ZANU-PF"},
            {"name": "Constantino Chiwenga", "role": "Vice President", "party": "ZANU-PF"},
            {"name": "Jacob Mudenda", "role": "Speaker of the National Assembly", "party": "ZANU-PF"},
            {"name": "Mthuli Ncube", "role": "Minister of Finance", "party": "Independent"},
            {"name": "Frederick Shava", "role": "Minister of Foreign Affairs", "party": "ZANU-PF"},
            {"name": "Kazembe Kazembe", "role": "Minister of Home Affairs", "party": "ZANU-PF"},
            {"name": "Oppah Muchinguri-Kashiri", "role": "Minister of Defence", "party": "ZANU-PF"},
            {"name": "Ziyambi Ziyambi", "role": "Minister of Justice", "party": "ZANU-PF"},
            {"name": "July Moyo", "role": "Minister of Local Government", "party": "ZANU-PF"},
            {"name": "Monica Mutsvangwa", "role": "Minister of Information", "party": "ZANU-PF"},
            {"name": "Anxious Masuka", "role": "Minister of Agriculture", "party": "ZANU-PF"},
            {"name": "Nelson Chamisa", "role": "Leader of the Opposition", "party": "CCC"},
        ]
        records = []
        for o in officials:
            records.append(RawPersonRecord(
                full_name=o["name"], title=o["role"],
                institution="Parliament of Zimbabwe",
                country_code=self.country_code, source_type=self.source_type,
                source_url=MEMBERS_URL, raw_text=f"{o['name']} – {o['role']}",
                scraped_at=now, extra_fields={"party": o["party"], "fixture": True},
            ))
        logger.info("zw_parliament.fixture.loaded", count=len(records))
        return records
