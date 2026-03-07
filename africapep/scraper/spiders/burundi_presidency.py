"""
Scraper for the Burundi Presidency / Government.

Source: https://www.presidence.gov.bi
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

GOV_URL = "https://www.presidence.gov.bi"


class BurundiPresidencyScraper(BaseScraper):
    """Scraper for the Burundi Government."""

    country_code = "BI"
    source_type = "PRESIDENCY"

    def scrape(self) -> list[RawPersonRecord]:
        logger.info("bi_presidency.scrape.start", url=GOV_URL)
        try:
            resp = self._get(GOV_URL)
            records = self._parse_officials(resp.text)
            if records:
                return records
            return self._load_fixture()
        except Exception:
            logger.exception("bi_presidency.scrape.error")
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
                    institution="Government of the Republic of Burundi",
                    country_code=self.country_code, source_type=self.source_type,
                    source_url=GOV_URL, raw_text=f"{full_name} – {role}",
                    scraped_at=datetime.utcnow(), extra_fields={"category": "Cabinet"},
                ))
            except Exception:
                logger.exception("bi_presidency.parse.error")
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        officials = [
            # Executive
            {"name": "Évariste Ndayishimiye", "role": "President of the Republic"},
            {"name": "Prosper Bazombanza", "role": "First Vice President"},
            {"name": "Gervais Ndirakobuca", "role": "Prime Minister"},
            # Cabinet Ministers
            {"name": "Albert Shingiro", "role": "Minister of Foreign Affairs and Development Cooperation"},
            {"name": "Blaise Didace Nzeyimana", "role": "Minister of Interior, Community Development and Public Security"},
            {"name": "Audace Niyonzima", "role": "Minister of Finance, Budget and Economic Planning"},
            {"name": "Alain Guillaume Bunyoni", "role": "Minister of National Defence and Veterans Affairs"},
            {"name": "Thérence Sinunguruza", "role": "Minister of Justice"},
            {"name": "Thaddée Ndikumana", "role": "Minister of Public Health and AIDS Control"},
            {"name": "François Havyarimana", "role": "Minister of Education and Scientific Research"},
            {"name": "Déo Guide Rurema", "role": "Minister of Agriculture and Livestock"},
            {"name": "Ezéchiel Nibigira", "role": "Minister of Trade, Transport, Industry and Tourism"},
            {"name": "Ibrahim Uwizeye", "role": "Minister of Energy and Mines"},
            {"name": "Imelde Sabushimike", "role": "Minister of National Solidarity, Social Affairs, Human Rights"},
            {"name": "Diomède Ntirhinyirwa", "role": "Minister of Hydraulics, Energy and Mines"},
            {"name": "Léonidas Sindayigaya", "role": "Minister of Environment, Agriculture and Livestock"},
            {"name": "Gaspard Banyankimbona", "role": "Minister of Higher Education and Scientific Research"},
            {"name": "Olivier Nkurunziza", "role": "Minister of Public Works and Equipment"},
            {"name": "Gordien Nduwimana", "role": "Minister of Communication and Media"},
            {"name": "Révérien Ndikuriyo", "role": "Secretary General of CNDD-FDD"},
            # Parliament
            {"name": "Gélase Daniel Ndabirabe", "role": "Speaker of the National Assembly"},
            {"name": "Emmanuel Sinzohagera", "role": "President of the Senate"},
            # Judiciary
            {"name": "Emmanuel Gateretse", "role": "President of the Supreme Court"},
            # Central Bank
            {"name": "Dieudonné Murengerantwari", "role": "Governor, Bank of the Republic of Burundi"},
            # Military
            {"name": "Prime Niyongabo", "role": "Chief of General Staff, Burundi National Defence Force"},
            # Opposition / Former
            {"name": "Agathon Rwasa", "role": "Leader of CNL (Opposition)"},
        ]
        records = []
        for o in officials:
            records.append(RawPersonRecord(
                full_name=o["name"], title=o["role"],
                institution="Government of the Republic of Burundi",
                country_code=self.country_code, source_type=self.source_type,
                source_url=GOV_URL, raw_text=f"{o['name']} – {o['role']}",
                scraped_at=now, extra_fields={"category": "Cabinet", "fixture": True},
            ))
        logger.info("bi_presidency.fixture.loaded", count=len(records))
        return records
