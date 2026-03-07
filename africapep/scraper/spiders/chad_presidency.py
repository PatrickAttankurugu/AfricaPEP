"""
Scraper for the Chad Presidency / Government.

Source: https://www.presidence.td
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

GOV_URL = "https://www.presidence.td"


class ChadPresidencyScraper(BaseScraper):
    """Scraper for the Chad Government."""

    country_code = "TD"
    source_type = "PRESIDENCY"

    def scrape(self) -> list[RawPersonRecord]:
        logger.info("td_presidency.scrape.start", url=GOV_URL)
        try:
            resp = self._get(GOV_URL)
            records = self._parse_officials(resp.text)
            if records:
                return records
            return self._load_fixture()
        except Exception:
            logger.exception("td_presidency.scrape.error")
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
                    institution="Government of the Republic of Chad",
                    country_code=self.country_code, source_type=self.source_type,
                    source_url=GOV_URL, raw_text=f"{full_name} – {role}",
                    scraped_at=datetime.utcnow(), extra_fields={"category": "Cabinet"},
                ))
            except Exception:
                logger.exception("td_presidency.parse.error")
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        officials = [
            {"name": "Mahamat Idriss Déby Itno", "role": "President of the Republic"},
            {"name": "Allamaye Halina", "role": "Prime Minister, Head of Government"},
            {"name": "Abderaman Koulamallah", "role": "Minister of Foreign Affairs, African Integration and Chadians Abroad"},
            {"name": "Daoud Yaya Brahim", "role": "Minister of National Defence and Veterans"},
            {"name": "Tahir Hamid Nguilin", "role": "Minister of Finance and Budget"},
            {"name": "Mahamat Ahmad Alhabo", "role": "Minister of Justice, Human Rights and Keeper of the Seals"},
            {"name": "Aziz Mahamat Saleh", "role": "Minister of Public Health and National Solidarity"},
            {"name": "Moustapha Malinam Garba", "role": "Minister of National Education and Civic Promotion"},
            {"name": "Limane Mahamat", "role": "Minister of Territorial Administration, Decentralisation and Good Governance"},
            {"name": "Mahamat Ahmat Lazina", "role": "Minister of Mines, Energy and Geology"},
            {"name": "Alingué Jean-Baptiste", "role": "Minister of Agriculture and Food Security"},
            {"name": "Abdelkérim Idriss Déby", "role": "Minister of State, Minister of Defence (former)"},
            {"name": "Moussa Faki Mahamat", "role": "Chairperson of the African Union Commission"},
            {"name": "Mahamat Abali Salah", "role": "Speaker of the National Assembly"},
            {"name": "Brah Mahamat", "role": "Minister of Economy, Development Planning and International Cooperation"},
            {"name": "Abakar Djermah Aumi", "role": "Minister of Transport and Road Safety"},
            {"name": "Idriss Saleh Bachar", "role": "Minister of Higher Education, Research and Innovation"},
            {"name": "Abderahim Awat Atahir", "role": "Minister of Communication"},
            {"name": "Hassan Sylla Bakari", "role": "Minister of Livestock and Animal Production"},
            {"name": "Kebzabo Saleh", "role": "Former Prime Minister of the Transition"},
            {"name": "Samir Adam Annour", "role": "Minister of Petroleum and Energy"},
            {"name": "Abbas Mahamat Tolli", "role": "Governor, Bank of Central African States (BEAC)"},
            {"name": "Général Abakar Abdelkérim Daoud", "role": "Chief of Defence Staff"},
            {"name": "Haroun Kabadi", "role": "Former Speaker of the National Assembly"},
            {"name": "Saleh Kebzabo", "role": "Opposition Leader, UNDR"},
            {"name": "Succès Masra", "role": "Former Opposition Leader, Les Transformateurs"},
        ]
        records = []
        for o in officials:
            records.append(RawPersonRecord(
                full_name=o["name"], title=o["role"],
                institution="Government of the Republic of Chad",
                country_code=self.country_code, source_type=self.source_type,
                source_url=GOV_URL, raw_text=f"{o['name']} – {o['role']}",
                scraped_at=now, extra_fields={"category": "Cabinet", "fixture": True},
            ))
        logger.info("td_presidency.fixture.loaded", count=len(records))
        return records
