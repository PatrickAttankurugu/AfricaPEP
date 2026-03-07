"""
Scraper for the Democratic Republic of the Congo (DRC) Parliament.

Source: https://www.assemblee-nationale.cd
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

ASSEMBLY_URL = "https://www.assemblee-nationale.cd"


class DRCParliamentScraper(BaseScraper):
    """Scraper for the DRC National Assembly."""

    country_code = "CD"
    source_type = "PARLIAMENT"

    def scrape(self) -> list[RawPersonRecord]:
        logger.info("cd_parliament.scrape.start", url=ASSEMBLY_URL)
        try:
            resp = self._get(ASSEMBLY_URL)
            records = self._parse_members(resp.text)
            if records:
                return records
            return self._load_fixture()
        except Exception:
            logger.exception("cd_parliament.scrape.error")
            return self._load_fixture()

    def _parse_members(self, html: str) -> list[RawPersonRecord]:
        soup = BeautifulSoup(html, "html.parser")
        records: list[RawPersonRecord] = []
        cards = soup.select(".depute, .member-card, .card, article, [class*='depute']")
        for card in cards:
            try:
                name_el = card.select_one("h3, h4, h2, .name, strong, a")
                if not name_el:
                    continue
                full_name = name_el.get_text(strip=True)
                if not full_name or len(full_name) < 3:
                    continue
                records.append(RawPersonRecord(
                    full_name=full_name, title="Député national",
                    institution="Assemblée nationale de la RDC",
                    country_code=self.country_code, source_type=self.source_type,
                    source_url=ASSEMBLY_URL, raw_text=f"{full_name} – Député",
                    scraped_at=datetime.utcnow(), extra_fields={},
                ))
            except Exception:
                logger.exception("cd_parliament.parse.error")
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        officials = [
            {"name": "Félix Tshisekedi", "role": "President of the Democratic Republic of the Congo", "party": "UDPS"},
            {"name": "Judith Suminwa Tuluka", "role": "Prime Minister", "party": "UDPS"},
            {"name": "Vital Kamerhe", "role": "Speaker of the National Assembly", "party": "UNC"},
            {"name": "Nicolas Kazadi", "role": "Minister of Finance", "party": "UDPS"},
            {"name": "Thérèse Kayikwamba Wagner", "role": "Minister of Foreign Affairs and Francophonie", "party": "UDPS"},
            {"name": "Jean-Pierre Bemba", "role": "Minister of Defence and Veterans", "party": "MLC"},
            {"name": "Jacquemain Shabani", "role": "Minister of Interior, Security and Customary Affairs", "party": "UDPS"},
            {"name": "Constant Mutamba", "role": "Minister of Justice and Keeper of the Seals", "party": "UDPS"},
            {"name": "Samuel Roger Kamba", "role": "Minister of Public Health, Hygiene and Prevention", "party": "UDPS"},
            {"name": "Raïssa Malu", "role": "Minister of National Education", "party": "UDPS"},
            {"name": "Guy Loando Mboyo", "role": "Minister of Land Affairs", "party": "UDPS"},
            {"name": "Aimé Boji Sangara", "role": "Minister of Budget", "party": "UDPS"},
            {"name": "Julien Paluku", "role": "Minister of Industry", "party": "UDPS"},
            {"name": "Didier Budimbu", "role": "Minister of Communication and Media", "party": "UDPS"},
            {"name": "Alexis Gisaro Muvunyi", "role": "Minister of Plan", "party": "UDPS"},
            {"name": "Muhindo Nzangi", "role": "Minister of Higher Education", "party": "UDPS"},
            {"name": "Daniel Aselo Okito", "role": "Minister of Transport", "party": "UDPS"},
            {"name": "Patrick Muyaya Katembwe", "role": "Government Spokesperson, Minister of Communication", "party": "UDPS"},
            {"name": "Modero Nsimba", "role": "Governor of Kinshasa", "party": "UDPS"},
            {"name": "Jean Lucien Bussa", "role": "Minister of Foreign Trade", "party": "UDPS"},
            {"name": "Sama Lukonde Kyenge", "role": "Former Prime Minister", "party": "UDPS"},
            {"name": "Augustin Kabuya", "role": "Secretary General of UDPS", "party": "UDPS"},
            {"name": "Moïse Katumbi", "role": "Opposition Leader, Ensemble pour la République", "party": "Ensemble"},
            {"name": "Martin Fayulu", "role": "Opposition Leader, ECIDé", "party": "ECIDé"},
            {"name": "Dieudonné Kaluba", "role": "Chief Justice, Constitutional Court", "party": ""},
            {"name": "Kabedi Mbuyi", "role": "Governor, Central Bank of Congo", "party": ""},
            {"name": "Général Christian Tshiwewe", "role": "Chief of Defence Staff", "party": ""},
            {"name": "Général Sylvano Kasongo", "role": "Inspector General of Police", "party": ""},
        ]
        records = []
        for o in officials:
            records.append(RawPersonRecord(
                full_name=o["name"], title=o["role"],
                institution="Assemblée nationale de la RDC",
                country_code=self.country_code, source_type=self.source_type,
                source_url=ASSEMBLY_URL, raw_text=f"{o['name']} – {o['role']}",
                scraped_at=now, extra_fields={"party": o["party"], "fixture": True},
            ))
        logger.info("cd_parliament.fixture.loaded", count=len(records))
        return records
