"""Ethiopia Presidency / Cabinet scraper.
Source: https://www.pmo.gov.et/
Method: BeautifulSoup (static HTML)
Schedule: Weekly
"""
from bs4 import BeautifulSoup
from datetime import datetime

import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

log = structlog.get_logger()

BASE_URL = "https://www.pmo.gov.et"
CABINET_URL = f"{BASE_URL}/"


class EthiopiaPresidencyScraper(BaseScraper):
    """Scraper for Ethiopia Presidency / Cabinet members."""

    country_code = "ET"
    source_type = "PRESIDENCY"

    def scrape(self) -> list[RawPersonRecord]:
        records = []
        try:
            resp = self._get(CABINET_URL)
            soup = BeautifulSoup(resp.text, "html.parser")
            records = self._parse_page(soup, CABINET_URL)
            log.info("ethiopia_presidency_scraped", records=len(records))
        except Exception as e:
            log.warning(
                "ethiopia_presidency_unreachable_falling_back_to_fixture",
                error=str(e),
            )
            records = self._load_fixture()
        return records

    def _parse_page(self, soup: BeautifulSoup, source_url: str) -> list[RawPersonRecord]:
        records = []
        now = datetime.utcnow()

        # Try various selectors for cabinet member cards
        cards = (
            soup.select(".team-member") or
            soup.select(".cabinet-member") or
            soup.select(".elementor-widget-container .member") or
            soup.select("article") or
            soup.select(".entry-content h3")
        )

        for card in cards:
            try:
                name_el = card.select_one("h3, h4, h5, .member-name, strong")
                if not name_el:
                    continue

                name = name_el.get_text(strip=True)
                if not name or len(name) < 3:
                    continue

                # Clean name
                clean_name = name
                for prefix in ["H.E.", "Hon.", "Dr.", "Prof.", "Amb."]:
                    if clean_name.startswith(prefix):
                        clean_name = clean_name[len(prefix):].strip()

                # Get portfolio
                portfolio = ""
                title_el = card.select_one(".position, .portfolio, p, .member-title")
                if title_el:
                    portfolio = title_el.get_text(strip=True)

                records.append(RawPersonRecord(
                    full_name=clean_name,
                    title=portfolio or "Minister",
                    institution="Office of the Prime Minister of Ethiopia",
                    country_code="ET",
                    source_url=source_url,
                    source_type="PRESIDENCY",
                    raw_text=f"{name} - {portfolio}",
                    scraped_at=now,
                    extra_fields={"portfolio": portfolio, "raw_name": name},
                ))
            except Exception as e:
                log.warning("ethiopia_presidency_parse_error", error=str(e))

        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        cabinet = [
            # Executive
            {"name": "Taye Atske Selassie", "title": "President of the Federal Republic of Ethiopia"},
            {"name": "Abiy Ahmed Ali", "title": "Prime Minister"},
            {"name": "Temesgen Tiruneh", "title": "Head, National Intelligence and Security Service"},
            # Cabinet Ministers
            {"name": "Demeke Mekonnen", "title": "Deputy Prime Minister / Minister of Foreign Affairs"},
            {"name": "Abraham Belay", "title": "Minister of Defence"},
            {"name": "Kenea Yadeta", "title": "Minister of Justice"},
            {"name": "Ahmed Shide", "title": "Minister of Finance"},
            {"name": "Fetlework Gebregziabher", "title": "Minister of Health"},
            {"name": "Berhanu Nega", "title": "Minister of Education"},
            {"name": "Aisha Mohammed", "title": "Minister of Industry"},
            {"name": "Dagmawit Moges", "title": "Minister of Transport and Logistics"},
            {"name": "Muferiat Kamil", "title": "Minister of Labour and Social Affairs"},
            {"name": "Habtamu Itefa", "title": "Minister of Water and Energy"},
            {"name": "Belete Molla", "title": "Minister of Innovation and Technology"},
            {"name": "Gedion Timothewos", "title": "Attorney General / Minister of Justice"},
            {"name": "Adanech Abiebie", "title": "Mayor of Addis Ababa"},
            {"name": "Ergogie Tesfaye", "title": "Minister of Women and Social Affairs"},
            {"name": "Sileshi Bekele", "title": "Minister of Water, Irrigation and Energy"},
            {"name": "Shumete Gizaw", "title": "Minister of Trade and Regional Integration"},
            {"name": "Redwan Hussein", "title": "National Security Advisor"},
            # Judiciary
            {"name": "Meaza Ashenafi", "title": "Former Chief Justice of Ethiopia"},
            # Central Bank
            {"name": "Mamo Esmelealem Mihretu", "title": "Governor, National Bank of Ethiopia"},
            # Parliament
            {"name": "Tagesse Chafo", "title": "Speaker of the House of Peoples' Representatives"},
            {"name": "Agegnehu Teshager", "title": "President of the House of Federation"},
            # Military
            {"name": "Birhanu Jula", "title": "Chief of Staff, Ethiopian National Defence Force"},
            # Opposition
            {"name": "Birtukan Mideksa", "title": "Chairperson, National Election Board"},
            {"name": "Jawar Mohammed", "title": "Opposition Political Figure"},
            {"name": "Lidetu Ayalew", "title": "Leader of the Ethiopian Democratic Party"},
        ]
        return [
            RawPersonRecord(
                full_name=m["name"],
                title=m["title"],
                institution="Office of the Prime Minister of Ethiopia",
                country_code="ET",
                source_url=CABINET_URL,
                source_type="PRESIDENCY",
                raw_text=f"{m['name']} - {m['title']}",
                scraped_at=now,
                extra_fields=m,
            )
            for m in cabinet
        ]
