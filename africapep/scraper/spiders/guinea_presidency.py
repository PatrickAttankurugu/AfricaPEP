"""
Scraper for the Guinea Presidency / Government.

Source: https://www.gouvernement.gov.gn
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

GOV_URL = "https://www.gouvernement.gov.gn"


class GuineaPresidencyScraper(BaseScraper):
    """Scraper for the Guinea Government."""

    country_code = "GN"
    source_type = "PRESIDENCY"

    def scrape(self) -> list[RawPersonRecord]:
        logger.info("gn_presidency.scrape.start", url=GOV_URL)
        try:
            resp = self._get(GOV_URL)
            records = self._parse_officials(resp.text)
            if records:
                return records
            return self._load_fixture()
        except Exception:
            logger.exception("gn_presidency.scrape.error")
            return self._load_fixture()

    def _parse_officials(self, html: str) -> list[RawPersonRecord]:
        soup = BeautifulSoup(html, "html.parser")
        records: list[RawPersonRecord] = []
        cards = soup.select(".minister, .team-member, .card, article, .membre")
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
                    institution="Government of the Republic of Guinea",
                    country_code=self.country_code, source_type=self.source_type,
                    source_url=GOV_URL, raw_text=f"{full_name} – {role}",
                    scraped_at=datetime.utcnow(), extra_fields={"category": "Cabinet"},
                ))
            except Exception:
                logger.exception("gn_presidency.parse.error")
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        officials = [
            {"name": "Mamadi Doumbouya", "role": "President of the Transition, Head of State"},
            {"name": "Amadou Oury Bah", "role": "Prime Minister, Head of Government"},
            {"name": "Morissanda Kouyaté", "role": "Minister of Foreign Affairs and Guineans Abroad"},
            {"name": "Bachir Diallo", "role": "Minister of Territorial Administration and Decentralisation"},
            {"name": "Mourana Soumah", "role": "Minister of Economy and Finance"},
            {"name": "Aboubacar Sidiki Camara", "role": "Minister of Defence"},
            {"name": "Alphonse Charles Wright", "role": "Minister of Justice and Human Rights"},
            {"name": "Oumar Maleya Camara", "role": "Minister of Health and Public Hygiene"},
            {"name": "Jean Paul Cedy", "role": "Minister of Pre-University Education"},
            {"name": "Fana Soumah", "role": "Minister of Communication and Information"},
            {"name": "Félix Lamah", "role": "Minister of Agriculture and Livestock"},
            {"name": "Kéamou Bogola Haba", "role": "Minister of Mines and Geology"},
            {"name": "Ismaël Dioubaté", "role": "Minister of Energy, Hydraulics and Hydrocarbons"},
            {"name": "Yaya Sow", "role": "Minister of Higher Education and Scientific Research"},
            {"name": "Rose Pola Pricemou", "role": "Minister of Planning and International Cooperation"},
            {"name": "Ousmane Gaoual Diallo", "role": "Minister of Posts, Telecommunications and Digital Economy"},
            {"name": "Djiba Diakité", "role": "Minister of Environment and Sustainable Development"},
            {"name": "Aminata Kourouma", "role": "Minister of Women's Promotion and Childhood"},
            {"name": "Dansa Kourouma", "role": "President of the National Transitional Council"},
            {"name": "Général Sadiba Koulibaly", "role": "Chief of Defence Staff"},
            {"name": "Moussa Cissé", "role": "Minister of Budget"},
            {"name": "Lanciné Condé", "role": "Governor, Central Bank of Guinea (BCRG)"},
            {"name": "Mamadou Sylla", "role": "Minister of Trade, Industry and SMEs"},
            {"name": "Alpha Condé", "role": "Former President of the Republic (ousted 2021)"},
            {"name": "Cellou Dalein Diallo", "role": "Opposition Leader, UFDG"},
            {"name": "Mamadou Saidou Bah", "role": "Chief Justice, Supreme Court"},
            {"name": "Amara Camara", "role": "Secretary General of the Presidency"},
        ]
        records = []
        for o in officials:
            records.append(RawPersonRecord(
                full_name=o["name"], title=o["role"],
                institution="Government of the Republic of Guinea",
                country_code=self.country_code, source_type=self.source_type,
                source_url=GOV_URL, raw_text=f"{o['name']} – {o['role']}",
                scraped_at=now, extra_fields={"category": "Cabinet", "fixture": True},
            ))
        logger.info("gn_presidency.fixture.loaded", count=len(records))
        return records
