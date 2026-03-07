"""
Scraper for the Republic of the Congo (Congo-Brazzaville) Presidency / Government.

Source: https://www.gouvernement.cg
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

GOV_URL = "https://www.gouvernement.cg"


class CongoPresidencyScraper(BaseScraper):
    """Scraper for the Republic of the Congo Government."""

    country_code = "CG"
    source_type = "PRESIDENCY"

    def scrape(self) -> list[RawPersonRecord]:
        logger.info("cg_presidency.scrape.start", url=GOV_URL)
        try:
            resp = self._get(GOV_URL)
            records = self._parse_officials(resp.text)
            if records:
                return records
            return self._load_fixture()
        except Exception:
            logger.exception("cg_presidency.scrape.error")
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
                    institution="Government of the Republic of the Congo",
                    country_code=self.country_code, source_type=self.source_type,
                    source_url=GOV_URL, raw_text=f"{full_name} – {role}",
                    scraped_at=datetime.utcnow(), extra_fields={"category": "Cabinet"},
                ))
            except Exception:
                logger.exception("cg_presidency.parse.error")
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        officials = [
            {"name": "Denis Sassou Nguesso", "role": "President of the Republic"},
            {"name": "Anatole Collinet Makosso", "role": "Prime Minister, Head of Government"},
            {"name": "Jean-Claude Gakosso", "role": "Minister of Foreign Affairs, Francophonie and Congolese Abroad"},
            {"name": "Raymond Zéphirin Mboulou", "role": "Minister of Interior, Decentralisation and Local Development"},
            {"name": "Rigobert Roger Andely", "role": "Minister of Finance and Budget"},
            {"name": "Charles Richard Mondjo", "role": "Minister of Defence"},
            {"name": "Aimé Ange Wilfrid Bininga", "role": "Minister of Justice, Human Rights and Promotion of Indigenous Peoples"},
            {"name": "Gilbert Mokoki", "role": "Minister of Health and Population"},
            {"name": "Jean-Luc Mouthou", "role": "Minister of Primary and Secondary Education"},
            {"name": "Bruno Jean Richard Itoua", "role": "Minister of Hydrocarbons"},
            {"name": "Paul Valentin Ngobo", "role": "Minister of Agriculture, Livestock and Fisheries"},
            {"name": "Isidore Mvouba", "role": "Speaker of the National Assembly"},
            {"name": "Denis Christel Sassou Nguesso", "role": "Minister of International Cooperation and Public-Private Partnership"},
            {"name": "Hugues Ngouélondélé", "role": "Minister of Construction, Town Planning and Housing"},
            {"name": "Ingrid Olga Ghislaine Ebouka-Babackas", "role": "Minister of Social Affairs and Humanitarian Action"},
            {"name": "Emilienne Raoul", "role": "Minister of Small and Medium-Sized Enterprises"},
            {"name": "Firmin Ayessa", "role": "Minister of Civil Service and State Reform"},
            {"name": "Jean-Marc Thystère-Tchicaya", "role": "Minister of Transport, Civil Aviation and Merchant Navy"},
            {"name": "Ange Antoine Abena", "role": "Minister of Higher Education"},
            {"name": "Josué Rodrigue Ngouonimba", "role": "Minister of Communication and Media"},
            {"name": "Pierre Ngolo", "role": "President of the Senate"},
            {"name": "Placide Lenga", "role": "Chief Justice, Supreme Court"},
            {"name": "Abbas Mahamat Tolli", "role": "Governor, Bank of Central African States (BEAC)"},
            {"name": "Général Guy Blanchard Okoï", "role": "Chief of Defence Staff"},
            {"name": "Jean Dominique Okemba", "role": "Secretary General of the National Security Council"},
            {"name": "Pascal Tsaty Mabiala", "role": "Opposition Leader, UPADS"},
            {"name": "Guy-Brice Parfait Kolélas", "role": "Former Opposition Leader (deceased 2021)"},
        ]
        records = []
        for o in officials:
            records.append(RawPersonRecord(
                full_name=o["name"], title=o["role"],
                institution="Government of the Republic of the Congo",
                country_code=self.country_code, source_type=self.source_type,
                source_url=GOV_URL, raw_text=f"{o['name']} – {o['role']}",
                scraped_at=now, extra_fields={"category": "Cabinet", "fixture": True},
            ))
        logger.info("cg_presidency.fixture.loaded", count=len(records))
        return records
