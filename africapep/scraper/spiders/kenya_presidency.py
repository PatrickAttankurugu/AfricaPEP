"""Kenya Presidency / Cabinet scraper.
Source: https://www.president.go.ke/
Method: BeautifulSoup (static HTML)
Schedule: Weekly
"""
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path

import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

log = structlog.get_logger()

BASE_URL = "https://www.president.go.ke"
CABINET_URL = f"{BASE_URL}/the-cabinet/"


class KenyaPresidencyScraper(BaseScraper):
    """Scraper for Kenya Presidency / Cabinet members."""

    country_code = "KE"
    source_type = "PRESIDENCY"

    def scrape(self) -> list[RawPersonRecord]:
        records = []
        try:
            resp = self._get(CABINET_URL)
            soup = BeautifulSoup(resp.text, "html.parser")
            records = self._parse_page(soup, CABINET_URL)
            log.info("kenya_presidency_scraped", records=len(records))
        except Exception as e:
            log.error("kenya_presidency_failed", error=str(e))
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
                for prefix in ["H.E.", "Hon.", "Dr.", "Prof.", "Amb.", "CS ", "PS "]:
                    if clean_name.startswith(prefix):
                        clean_name = clean_name[len(prefix):].strip()

                # Get portfolio
                portfolio = ""
                title_el = card.select_one(".position, .portfolio, p, .member-title")
                if title_el:
                    portfolio = title_el.get_text(strip=True)

                records.append(RawPersonRecord(
                    full_name=clean_name,
                    title=portfolio or "Cabinet Secretary",
                    institution="Office of the President of Kenya",
                    country_code="KE",
                    source_url=source_url,
                    source_type="PRESIDENCY",
                    raw_text=f"{name} - {portfolio}",
                    scraped_at=now,
                    extra_fields={"portfolio": portfolio, "raw_name": name},
                ))
            except Exception as e:
                log.warning("kenya_presidency_parse_error", error=str(e))

        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        cabinet = [
            {"name": "William Samoei Ruto", "title": "President of the Republic of Kenya"},
            {"name": "Kithure Kindiki", "title": "Deputy President"},
            {"name": "Musalia Mudavadi", "title": "Prime Cabinet Secretary and CS Foreign Affairs"},
            {"name": "Aden Duale", "title": "Cabinet Secretary for Defence"},
            {"name": "Justin Muturi", "title": "Attorney General"},
            {"name": "Njuguna Ndung'u", "title": "Cabinet Secretary for Treasury"},
            {"name": "Alfred Mutua", "title": "Cabinet Secretary for Tourism"},
            {"name": "Ezekiel Machogu", "title": "Cabinet Secretary for Education"},
            {"name": "Susan Nakhumicha", "title": "Cabinet Secretary for Health"},
            {"name": "Davis Chirchir", "title": "Cabinet Secretary for Energy"},
            {"name": "Kipchumba Murkomen", "title": "Cabinet Secretary for Youth Affairs and Sports"},
            {"name": "Rebecca Miano", "title": "Cabinet Secretary for Investments, Trade and Industry"},
            {"name": "Salim Mvurya", "title": "Cabinet Secretary for Mining, Blue Economy and Maritime Affairs"},
            {"name": "Florence Bore", "title": "Cabinet Secretary for Labour and Social Protection"},
            {"name": "Mithika Linturi", "title": "Cabinet Secretary for Agriculture"},
            {"name": "Roselinda Soipan Tuya", "title": "Cabinet Secretary for Environment"},
            {"name": "Opiyo Wandayi", "title": "Cabinet Secretary for Energy and Petroleum"},
            {"name": "John Mbadi", "title": "Cabinet Secretary for National Treasury"},
            {"name": "Hassan Joho", "title": "Cabinet Secretary for Mining"},
            {"name": "Wycliffe Oparanya", "title": "Cabinet Secretary for Cooperatives"},
            {"name": "Alice Wahome", "title": "Cabinet Secretary for Water"},
            {"name": "Margaret Ndung'u", "title": "Cabinet Secretary for ICT and Digital Economy"},
            {"name": "Eric Mugaa", "title": "Cabinet Secretary for Lands and Urban Planning"},
            # Judiciary
            {"name": "Martha Koome", "title": "Chief Justice of Kenya"},
            {"name": "Philomena Mwilu", "title": "Deputy Chief Justice of Kenya"},
            # Central Bank
            {"name": "Kamau Thugge", "title": "Governor, Central Bank of Kenya"},
            # Security Chiefs
            {"name": "Charles Muriu Kahariri", "title": "Chief of Defence Forces, Kenya Defence Forces"},
            {"name": "Japhet Koome", "title": "Inspector General of National Police Service"},
            # Parliament
            {"name": "Amason Kingi", "title": "Speaker of the Senate"},
            {"name": "Moses Wetangula", "title": "Speaker of the National Assembly"},
            # Former Presidents and Opposition
            {"name": "Uhuru Kenyatta", "title": "Former President of Kenya"},
            {"name": "Raila Odinga", "title": "Former Prime Minister and AU Commission Chairperson"},
            {"name": "Rigathi Gachagua", "title": "Former Deputy President"},
        ]
        return [
            RawPersonRecord(
                full_name=m["name"],
                title=m["title"],
                institution="Office of the President of Kenya",
                country_code="KE",
                source_url=CABINET_URL,
                source_type="PRESIDENCY",
                raw_text=f"{m['name']} - {m['title']}",
                scraped_at=now,
                extra_fields=m,
            )
            for m in cabinet
        ]
