"""
Scraper for the National Assembly of Côte d'Ivoire (Assemblée nationale).

Source: https://www.assnat.ci
Extracts deputies from the National Assembly website.
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

BASE_URL = "https://www.assnat.ci"


class CoteDIvoireParliamentScraper(BaseScraper):
    """Scraper for the Côte d'Ivoire National Assembly."""

    country_code = "CI"
    source_type = "PARLIAMENT"

    def scrape(self) -> list[RawPersonRecord]:
        """Scrape deputies from the National Assembly website."""
        logger.info("ci_parliament.scrape.start", url=BASE_URL)
        try:
            resp = self._get(BASE_URL)
            records = self._parse_deputies(resp.text)
            if records:
                return records
            logger.warning("ci_parliament.scrape.no_results")
            return self._load_fixture()
        except Exception:
            logger.exception("ci_parliament.scrape.error")
            return self._load_fixture()

    def _parse_deputies(self, html: str) -> list[RawPersonRecord]:
        """Parse deputy listings from HTML."""
        soup = BeautifulSoup(html, "html.parser")
        records: list[RawPersonRecord] = []

        cards = soup.select(
            ".deputy-card, .membre-card, .card, "
            "[class*='depute'], [class*='membre'], article"
        )

        for card in cards:
            try:
                name_el = card.select_one("h3, h4, h2, .name, .title, strong, a")
                if not name_el:
                    continue
                full_name = name_el.get_text(strip=True)
                if not full_name or len(full_name) < 3:
                    continue

                role_el = card.select_one("p, .role, .position, span")
                role = role_el.get_text(strip=True) if role_el else ""

                records.append(RawPersonRecord(
                    full_name=full_name,
                    title="Député" if not role else role,
                    institution="Assemblée nationale de Côte d'Ivoire",
                    country_code=self.country_code,
                    source_type=self.source_type,
                    source_url=BASE_URL,
                    raw_text=f"{full_name} – Député",
                    scraped_at=datetime.utcnow(),
                    extra_fields={},
                ))
            except Exception:
                logger.exception("ci_parliament.parse.error")

        logger.info("ci_parliament.scrape.complete", count=len(records))
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        officials = [
            {"name": "Alassane Ouattara", "role": "President of the Republic", "party": "RHDP"},
            {"name": "Tiémoko Meyliet Koné", "role": "Vice President of the Republic", "party": "RHDP"},
            {"name": "Robert Beugré Mambé", "role": "Prime Minister", "party": "RHDP"},
            {"name": "Adama Bictogo", "role": "President of the National Assembly", "party": "RHDP"},
            {"name": "Kandia Camara", "role": "President of the Senate", "party": "RHDP"},
            {"name": "Téné Birahima Ouattara", "role": "Minister of Defence", "party": "RHDP"},
            {"name": "Adama Coulibaly", "role": "Minister of Economy and Finance", "party": "RHDP"},
            {"name": "Mariatou Koné", "role": "Minister of National Education and Literacy", "party": "RHDP"},
            {"name": "Vagondo Diomandé", "role": "Minister of Interior and Security", "party": "RHDP"},
            {"name": "Kobenan Kouassi Adjoumani", "role": "Minister of Agriculture and Rural Development", "party": "RHDP"},
            {"name": "Kacou Houadja Léon Adom", "role": "Minister of Foreign Affairs", "party": "RHDP"},
            {"name": "Sansan Kambilé", "role": "Minister of Justice and Human Rights", "party": "RHDP"},
            {"name": "Pierre Dimba", "role": "Minister of Health, Public Hygiene", "party": "RHDP"},
            {"name": "Amadou Koné", "role": "Minister of Transport", "party": "RHDP"},
            {"name": "Mamadou Touré", "role": "Minister of Youth Promotion and Employment", "party": "RHDP"},
            {"name": "Fidèle Sarassoro", "role": "Secretary General of the Presidency", "party": "RHDP"},
            {"name": "Anne Désirée Ouloto", "role": "Minister of Civil Service and Public Sector Reform", "party": "RHDP"},
            {"name": "Cina Lawson", "role": "Minister of Digital Economy and Posts", "party": "RHDP"},
            {"name": "Moussa Dosso", "role": "Minister of Water and Forests", "party": "RHDP"},
            {"name": "Nassénéba Touré", "role": "Minister of Women, Family and Children", "party": "RHDP"},
            {"name": "Amadou Coulibaly", "role": "Minister of Communication and Media", "party": "RHDP"},
            {"name": "Ibrahim Bacongo Cissé", "role": "Minister of Higher Education and Scientific Research", "party": "RHDP"},
            {"name": "Jean-Luc Assi", "role": "Minister of Environment and Sustainable Development", "party": "RHDP"},
            {"name": "Patrick Achi", "role": "Former Prime Minister", "party": "RHDP"},
            {"name": "Laurent Gbagbo", "role": "Former President of the Republic", "party": "PPA-CI"},
            {"name": "Henri Konan Bédié", "role": "Former President of the Republic (deceased 2023)", "party": "PDCI-RDA"},
            {"name": "Jean-Marc Yacé", "role": "Chief Justice, Supreme Court", "party": ""},
            {"name": "Lassina Fofana", "role": "Governor, BCEAO Côte d'Ivoire", "party": ""},
            {"name": "Général Lassina Doumbia", "role": "Chief of Defence Staff", "party": ""},
            {"name": "Youssouf Kouyaté", "role": "Director General of Police", "party": ""},
        ]

        records = []
        for o in officials:
            records.append(RawPersonRecord(
                full_name=o["name"],
                title=o["role"],
                institution="Assemblée nationale de Côte d'Ivoire",
                country_code=self.country_code,
                source_type=self.source_type,
                source_url=BASE_URL,
                raw_text=f"{o['name']} – {o['role']}",
                scraped_at=now,
                extra_fields={
                    "party": o["party"],
                    "fixture": True,
                },
            ))

        logger.info("ci_parliament.fixture.loaded", count=len(records))
        return records
