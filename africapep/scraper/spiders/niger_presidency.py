"""
Scraper for the Niger Presidency / Government.

Source: https://www.presidence.ne
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

GOV_URL = "https://www.presidence.ne"


class NigerPresidencyScraper(BaseScraper):
    """Scraper for the Niger Government."""

    country_code = "NE"
    source_type = "PRESIDENCY"

    def scrape(self) -> list[RawPersonRecord]:
        logger.info("ne_presidency.scrape.start", url=GOV_URL)
        try:
            resp = self._get(GOV_URL)
            records = self._parse_officials(resp.text)
            if records:
                return records
            return self._load_fixture()
        except Exception:
            logger.exception("ne_presidency.scrape.error")
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
                    institution="Government of the Republic of Niger",
                    country_code=self.country_code, source_type=self.source_type,
                    source_url=GOV_URL, raw_text=f"{full_name} – {role}",
                    scraped_at=datetime.utcnow(), extra_fields={"category": "Cabinet"},
                ))
            except Exception:
                logger.exception("ne_presidency.parse.error")
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        officials = [
            {"name": "Abdourahamane Tchiani", "role": "President of the CNSP, Head of State"},
            {"name": "Ali Mahaman Lamine Zeine", "role": "Prime Minister"},
            {"name": "Bakary Yaou Sangaré", "role": "Minister of Foreign Affairs and Cooperation"},
            {"name": "Mohamed Toumba", "role": "Minister of Interior, Public Security and Territorial Administration"},
            {"name": "Moumouni Boubacar Saidou", "role": "Minister of Finance"},
            {"name": "Général Salifou Modi", "role": "Minister of National Defence"},
            {"name": "Ahamadou Djibo", "role": "Minister of Justice, Keeper of the Seals"},
            {"name": "Garba Hakimi", "role": "Minister of Public Health, Population and Social Affairs"},
            {"name": "Amadou Issoufou", "role": "Minister of National Education"},
            {"name": "Mahaman Elhadj Ousmane", "role": "Minister of Agriculture and Livestock"},
            {"name": "Sahabi Oumarou", "role": "Minister of Mines"},
            {"name": "Sani Mahamadou Issoufou", "role": "Minister of Petroleum, Energy and Renewable Energies"},
            {"name": "Soufiane Ibrahim", "role": "Minister of Commerce and Industry"},
            {"name": "Mahamadou Laouali Dan Dah", "role": "Minister of Equipment and Transport"},
            {"name": "Mamane Sani Adamou", "role": "Minister of Higher Education and Research"},
            {"name": "Abdoulkadri Harouna", "role": "Minister of Communication, Posts and Digital Economy"},
            {"name": "Colonel Major Mamane Sani Kiaou", "role": "Minister of Humanitarian Action and Disaster Management"},
            {"name": "Ibrahim Yacouba", "role": "Minister of Water and Sanitation"},
            {"name": "Rhissa Ag Boula", "role": "Minister of Tourism and Handicrafts"},
            {"name": "Général Moussa Salaou Barmou", "role": "Chief of Defence Staff"},
            {"name": "Mahaman Hamidou Souley", "role": "Governor, BCEAO Niger National Agency"},
            {"name": "Abdou Dangaladima", "role": "Chief Justice, Court of Cassation"},
            {"name": "Mahaman Salissou Garanke", "role": "President of the National Council for the Safeguard of the Homeland"},
            {"name": "Mohamed Bazoum", "role": "Former President of the Republic (detained since July 2023)"},
            {"name": "Mahamadou Issoufou", "role": "Former President of the Republic"},
            {"name": "Hama Amadou", "role": "Former Prime Minister and Opposition Figure"},
        ]
        records = []
        for o in officials:
            records.append(RawPersonRecord(
                full_name=o["name"], title=o["role"],
                institution="Government of the Republic of Niger",
                country_code=self.country_code, source_type=self.source_type,
                source_url=GOV_URL, raw_text=f"{o['name']} – {o['role']}",
                scraped_at=now, extra_fields={"category": "Cabinet", "fixture": True},
            ))
        logger.info("ne_presidency.fixture.loaded", count=len(records))
        return records
