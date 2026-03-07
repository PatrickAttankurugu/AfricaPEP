"""
Scraper for the Equatorial Guinea Presidency / Government.

Source: https://www.guineaecuatorialpress.com
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

GOV_URL = "https://www.guineaecuatorialpress.com"


class EqGuineaPresidencyScraper(BaseScraper):
    """Scraper for the Equatorial Guinea Government."""

    country_code = "GQ"
    source_type = "PRESIDENCY"

    def scrape(self) -> list[RawPersonRecord]:
        logger.info("gq_presidency.scrape.start", url=GOV_URL)
        try:
            resp = self._get(GOV_URL)
            records = self._parse_officials(resp.text)
            if records:
                return records
            return self._load_fixture()
        except Exception:
            logger.exception("gq_presidency.scrape.error")
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
                    institution="Government of the Republic of Equatorial Guinea",
                    country_code=self.country_code, source_type=self.source_type,
                    source_url=GOV_URL, raw_text=f"{full_name} – {role}",
                    scraped_at=datetime.utcnow(), extra_fields={"category": "Cabinet"},
                ))
            except Exception:
                logger.exception("gq_presidency.parse.error")
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        officials = [
            {"name": "Teodoro Obiang Nguema Mbasogo", "role": "President of the Republic"},
            {"name": "Teodoro Nguema Obiang Mangue", "role": "Vice President"},
            {"name": "Manuela Roka Botey", "role": "Prime Minister"},
            {"name": "Simeón Oyono Esono Angue", "role": "Minister of Foreign Affairs and International Cooperation"},
            {"name": "Nicolás Obama Nchama", "role": "Minister of Interior and Local Corporations"},
            {"name": "Valentin Ela Maye", "role": "Minister of Finance and Budget"},
            {"name": "Evangelina Filomena Oyo Ebule", "role": "Minister of Justice, Worship and Penitentiary Institutions"},
            {"name": "Mitoha Ondo'o Ayekaba", "role": "Minister of Health and Social Welfare"},
            {"name": "Jesús Engonga Ndong", "role": "Minister of Education, University Education and Sports"},
            {"name": "Gabriel Mbega Obiang Lima", "role": "Minister of Mines and Hydrocarbons"},
            {"name": "Diosdado Vicente Nsue Milang", "role": "Minister of National Defence"},
            {"name": "Clemente Engonga Nguema Onguene", "role": "President of the Senate"},
            {"name": "Antonio Nve Nseng", "role": "Minister of Agriculture, Livestock and Food Security"},
            {"name": "Baltasar Engonga Edjo", "role": "Secretary General of the Presidency"},
            {"name": "Lucas Nguema Esono", "role": "Minister of Public Works and Infrastructure"},
            {"name": "Domingo Mba Esono", "role": "Minister of Transport, Technology, Posts and Telecommunications"},
            {"name": "Filiberto Ntutumu Nguema Eneme", "role": "Speaker of the Chamber of Deputies"},
            {"name": "Miguel Abia Biteo Boricó", "role": "Minister of State for Regional Integration"},
            {"name": "Rufino Ovono Ondo", "role": "Attorney General"},
            {"name": "Estanislao Don Malavo", "role": "Minister of Information, Press and Radio"},
            {"name": "Ángel Masie Mibuy", "role": "Minister of Labour, Employment and Social Security"},
            {"name": "Salvador Ondo Ncumu", "role": "Chief Justice, Supreme Court"},
            {"name": "Abbas Mahamat Tolli", "role": "Governor, Bank of Central African States (BEAC)"},
            {"name": "General Antonio Mba Nguema", "role": "Military Governor of Bioko Norte"},
            {"name": "Severo Moto Nsá", "role": "Opposition Leader (in exile)"},
        ]
        records = []
        for o in officials:
            records.append(RawPersonRecord(
                full_name=o["name"], title=o["role"],
                institution="Government of the Republic of Equatorial Guinea",
                country_code=self.country_code, source_type=self.source_type,
                source_url=GOV_URL, raw_text=f"{o['name']} – {o['role']}",
                scraped_at=now, extra_fields={"category": "Cabinet", "fixture": True},
            ))
        logger.info("gq_presidency.fixture.loaded", count=len(records))
        return records
