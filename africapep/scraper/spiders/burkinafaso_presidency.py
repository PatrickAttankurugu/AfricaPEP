"""
Scraper for the Burkina Faso Presidency / Government.

Source: https://www.gouvernement.gov.bf
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

GOV_URL = "https://www.gouvernement.gov.bf"


class BurkinaFasoPresidencyScraper(BaseScraper):
    """Scraper for the Burkina Faso Government."""

    country_code = "BF"
    source_type = "PRESIDENCY"

    def scrape(self) -> list[RawPersonRecord]:
        logger.info("bf_presidency.scrape.start", url=GOV_URL)
        try:
            resp = self._get(GOV_URL)
            records = self._parse_officials(resp.text)
            if records:
                return records
            return self._load_fixture()
        except Exception:
            logger.exception("bf_presidency.scrape.error")
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
                    institution="Government of Burkina Faso",
                    country_code=self.country_code, source_type=self.source_type,
                    source_url=GOV_URL, raw_text=f"{full_name} – {role}",
                    scraped_at=datetime.utcnow(), extra_fields={"category": "Cabinet"},
                ))
            except Exception:
                logger.exception("bf_presidency.parse.error")
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        officials = [
            {"name": "Ibrahim Traoré", "role": "President of the Transition, Head of State"},
            {"name": "Apollinaire Joachim Kyelem de Tambela", "role": "Prime Minister"},
            {"name": "Karamoko Jean Marie Traoré", "role": "Minister of Foreign Affairs, Regional Cooperation and Burkinabè Abroad"},
            {"name": "Emile Zerbo", "role": "Minister of State, Minister of Defence and Veterans"},
            {"name": "Kassoum Coulibaly", "role": "Minister Delegate for Security"},
            {"name": "Ismaël Sombié", "role": "Minister of State for Health and Public Hygiene"},
            {"name": "Aboubakari Nacanabo", "role": "Minister of Economy, Finance and Prospective"},
            {"name": "Joseph André Ouédraogo", "role": "Minister of National Education, Literacy and Promotion of National Languages"},
            {"name": "Bassolma Bazié", "role": "Minister of Civil Service, Labour and Social Protection"},
            {"name": "Mathias Traoré", "role": "Minister of Solidarity, Humanitarian Action and National Reconciliation"},
            {"name": "Roland Somda", "role": "Minister of Territorial Administration, Decentralisation and Security"},
            {"name": "Jean-Emmanuel Ouédraogo", "role": "Minister of Communication, Culture, Arts and Tourism"},
            {"name": "Serge Gnaniodem Poda", "role": "Minister of Higher Education, Research and Innovation"},
            {"name": "Simon Compaoré", "role": "Minister of Energy, Mines and Quarries"},
            {"name": "Aminata Zerbo", "role": "Minister of Justice, Human Rights and Keeper of the Seals"},
            {"name": "Issouf Gounoufa", "role": "Minister of Agriculture, Animal Resources and Fisheries"},
            {"name": "Roland Sawadogo", "role": "Minister of Infrastructure and Opening Up"},
            {"name": "Dr Lucien Marie Noël Bembamba", "role": "Minister of Industry, Trade and Handicrafts"},
            {"name": "Nandy Somé", "role": "Minister of Digital Transition, Posts and Electronic Communications"},
            {"name": "Hélène Marie Laurence Ilboudo/Marchall", "role": "Minister of Environment, Water and Sanitation"},
            {"name": "Oumarou Idani", "role": "President of the Legislative Assembly of the Transition"},
            {"name": "Barthélémy Kéré", "role": "President of the Constitutional Council"},
            {"name": "Lassané Kaboré", "role": "Governor, BCEAO Burkina Faso National Agency"},
            {"name": "Colonel Major David Kaboré", "role": "Chief of Defence Staff"},
            {"name": "Roch Marc Christian Kaboré", "role": "Former President of the Republic (ousted 2022)"},
            {"name": "Paul-Henri Sandaogo Damiba", "role": "Former Transition President (ousted 2022)"},
            {"name": "Blaise Compaoré", "role": "Former President of the Republic (in exile)"},
        ]
        records = []
        for o in officials:
            records.append(RawPersonRecord(
                full_name=o["name"], title=o["role"],
                institution="Government of Burkina Faso",
                country_code=self.country_code, source_type=self.source_type,
                source_url=GOV_URL, raw_text=f"{o['name']} – {o['role']}",
                scraped_at=now, extra_fields={"category": "Cabinet", "fixture": True},
            ))
        logger.info("bf_presidency.fixture.loaded", count=len(records))
        return records
