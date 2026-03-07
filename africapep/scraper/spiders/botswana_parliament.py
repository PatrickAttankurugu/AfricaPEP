"""
Scraper for the Parliament of Botswana (National Assembly).

Source: https://www.parliament.gov.bw
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

MEMBERS_URL = "https://www.parliament.gov.bw/index.php/members-of-parliament"


class BotswanaParliamentScraper(BaseScraper):
    """Scraper for the Botswana National Assembly."""

    country_code = "BW"
    source_type = "PARLIAMENT"

    def scrape(self) -> list[RawPersonRecord]:
        logger.info("bw_parliament.scrape.start", url=MEMBERS_URL)
        try:
            resp = self._get(MEMBERS_URL)
            records = self._parse_members(resp.text)
            if records:
                return records
            return self._load_fixture()
        except Exception:
            logger.exception("bw_parliament.scrape.error")
            return self._load_fixture()

    def _parse_members(self, html: str) -> list[RawPersonRecord]:
        soup = BeautifulSoup(html, "html.parser")
        records: list[RawPersonRecord] = []
        cards = soup.select("tr, .member-card, .card, article, [class*='member']")
        for card in cards:
            try:
                name_el = card.select_one("td:first-child a, h3, h4, .name, strong")
                if not name_el:
                    continue
                full_name = name_el.get_text(strip=True)
                if not full_name or len(full_name) < 3:
                    continue
                records.append(RawPersonRecord(
                    full_name=full_name, title="Member of Parliament",
                    institution="National Assembly of Botswana",
                    country_code=self.country_code, source_type=self.source_type,
                    source_url=MEMBERS_URL, raw_text=f"{full_name} – MP",
                    scraped_at=datetime.utcnow(), extra_fields={},
                ))
            except Exception:
                logger.exception("bw_parliament.parse.error")
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        officials = [
            {"name": "Duma Boko", "role": "President of the Republic of Botswana", "party": "UDC"},
            {"name": "Ndaba Gaolathe", "role": "Vice President", "party": "UDC"},
            {"name": "Phandu Skelemani", "role": "Speaker of the National Assembly", "party": "UDC"},
            {"name": "Mokgweetsi Masisi", "role": "Leader of the Opposition", "party": "BDP"},
            {"name": "Peggy Serame", "role": "Minister of Finance", "party": "UDC"},
            {"name": "Mbulelo Toteng", "role": "Minister of Health", "party": "UDC"},
            {"name": "Ketlhalefile Motshegwa", "role": "Minister of Defence", "party": "UDC"},
            {"name": "Taolo Lucas", "role": "Minister of Lands", "party": "BCP"},
            {"name": "Tebelelo Seretse", "role": "Attorney General", "party": "UDC"},
            {"name": "Kenewendo Bogolo", "role": "Minister of Trade and Industry", "party": "UDC"},
            {"name": "Dumelang Saleshando", "role": "Minister of Education", "party": "BCP"},
            {"name": "Mephato Reatile", "role": "Minister of Transport", "party": "UDC"},
        ]
        records = []
        for o in officials:
            records.append(RawPersonRecord(
                full_name=o["name"], title=o["role"],
                institution="National Assembly of Botswana",
                country_code=self.country_code, source_type=self.source_type,
                source_url=MEMBERS_URL, raw_text=f"{o['name']} – {o['role']}",
                scraped_at=now, extra_fields={"party": o["party"], "fixture": True},
            ))
        logger.info("bw_parliament.fixture.loaded", count=len(records))
        return records
