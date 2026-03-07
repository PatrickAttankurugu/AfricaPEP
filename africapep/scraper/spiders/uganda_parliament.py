"""Uganda Parliament Members scraper.
Source: https://mpsdb.parliament.go.ug/
Method: Playwright (JS-rendered) + BeautifulSoup
Schedule: Weekly
"""
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path

import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

log = structlog.get_logger()

BASE_URL = "https://mpsdb.parliament.go.ug"
FIXTURE_DIR = Path(__file__).parent.parent.parent.parent / "tests" / "fixtures" / "uganda_parliament"


class UgandaParliamentScraper(BaseScraper):
    """Scraper for Uganda Parliament members."""

    country_code = "UG"
    source_type = "PARLIAMENT"

    def scrape(self) -> list[RawPersonRecord]:
        records = []

        try:
            from africapep.scraper.utils.playwright_utils import get_page_content_sync

            # The main page lists MPs by party with links
            html = get_page_content_sync(BASE_URL, wait_selector=".card", timeout=30000)
            soup = BeautifulSoup(html, "html.parser")

            # Find all MP cards
            records.extend(self._parse_page(soup, BASE_URL))

            # Also try party member pages for more data
            party_links = soup.select("a[href*='party-members']")
            for link in party_links[:5]:  # Top 5 parties
                href = link.get("href", "")
                if not href.startswith("http"):
                    href = BASE_URL + "/" + href.lstrip("/")
                try:
                    party_html = get_page_content_sync(href, wait_selector=".card", timeout=30000)
                    party_soup = BeautifulSoup(party_html, "html.parser")
                    party_records = self._parse_page(party_soup, href)
                    records.extend(party_records)
                    log.info("uganda_party_page", url=href, found=len(party_records))
                except Exception as e:
                    log.warning("uganda_party_page_failed", url=href, error=str(e))

        except Exception as e:
            log.error("uganda_parliament_failed", error=str(e))

        # Deduplicate by name
        seen = set()
        unique = []
        for r in records:
            if r.full_name not in seen:
                seen.add(r.full_name)
                unique.append(r)
        return unique

    def _parse_page(self, soup: BeautifulSoup, source_url: str) -> list[RawPersonRecord]:
        records = []
        now = datetime.utcnow()

        # Uganda MPs DB uses .card elements with MP info
        cards = soup.select(".card")

        for card in cards:
            # Find name element
            name_el = card.select_one("h5, h4, .card-title, strong, a[href*='/home/mp/']")
            if not name_el:
                continue

            name = name_el.get_text(strip=True)

            # Clean name
            clean_name = name
            for prefix in ["Hon.", "Hon ", "Rt. Hon."]:
                if clean_name.startswith(prefix):
                    clean_name = clean_name[len(prefix):].strip()

            if not clean_name or len(clean_name) < 3:
                continue

            # Skip non-name cards (party counts, navigation)
            if any(skip in clean_name.lower() for skip in [
                "search", "nrm", "nup", "fdc", "upc", "independent",
                "jeema", "ppp", "army", "n/a",
            ]):
                continue

            # Try to extract constituency/district and party
            card_text = card.get_text(" ", strip=True)
            constituency = ""
            party = ""
            district = ""

            # Look for small text or secondary elements
            details = card.select("small, .text-muted, p, span")
            for det in details:
                text = det.get_text(strip=True)
                if "constituency" in text.lower() or "county" in text.lower():
                    constituency = text
                elif "district" in text.lower():
                    district = text
                elif any(p in text for p in ["NRM", "NUP", "FDC", "UPC", "Independent"]):
                    party = text

            records.append(RawPersonRecord(
                full_name=clean_name,
                title="Member of Parliament",
                institution="Parliament of Uganda",
                country_code="UG",
                source_url=source_url,
                source_type="PARLIAMENT",
                raw_text=card_text[:500],
                scraped_at=now,
                extra_fields={
                    "constituency": constituency,
                    "district": district,
                    "party": party,
                },
            ))

        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        fixture_file = FIXTURE_DIR / "mps.html"
        if fixture_file.exists():
            soup = BeautifulSoup(
                fixture_file.read_text(encoding="utf-8", errors="replace"),
                "html.parser"
            )
            records = self._parse_page(soup, BASE_URL)
            if records:
                return records
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        mps = [
            # === Executive ===
            {"name": "Yoweri Kaguta Museveni", "constituency": "National", "party": "NRM", "title": "President of the Republic of Uganda"},
            {"name": "Jessica Rose Epel Alupo", "constituency": "National", "party": "NRM", "title": "Vice President"},
            {"name": "Robinah Nabbanja", "constituency": "Kakumiro", "party": "NRM", "title": "Prime Minister"},
            {"name": "Rebecca Kadaga", "constituency": "Kamuli", "party": "NRM", "title": "First Deputy Prime Minister"},
            {"name": "Moses Ali", "constituency": "Adjumani East", "party": "NRM", "title": "Second Deputy Prime Minister"},
            # Previous Vice Presidents
            {"name": "Edward Kiwanuka Ssekandi", "constituency": "Bukoto Central", "party": "NRM", "title": "Former Vice President"},
            {"name": "Gilbert Bukenya", "constituency": "Busiro North", "party": "NRM", "title": "Former Vice President"},
            # === Parliament Leadership ===
            {"name": "Anita Annet Among", "constituency": "Bukedea", "party": "NRM", "title": "Speaker of Parliament"},
            {"name": "Thomas Tayebwa", "constituency": "Ruhinda North", "party": "NRM", "title": "Deputy Speaker of Parliament"},
            {"name": "Joel Ssenyonyi", "constituency": "Nakawa West", "party": "NUP", "title": "Leader of Opposition in Parliament"},
            {"name": "Mathias Mpuuga", "constituency": "Nyendo-Mukungwe", "party": "NUP", "title": "Former Leader of Opposition"},
            # === Full Cabinet Ministers ===
            {"name": "Jeje Odongo", "constituency": "Kumi County", "party": "NRM", "title": "Minister of Foreign Affairs"},
            {"name": "Vincent Bamulangaki Ssempijja", "constituency": "Kalungu East", "party": "NRM", "title": "Minister of Defence and Veteran Affairs"},
            {"name": "Kahinda Otafiire", "constituency": "Ruhinda", "party": "NRM", "title": "Minister of Internal Affairs"},
            {"name": "Matia Kasaija", "constituency": "Buyanja", "party": "NRM", "title": "Minister of Finance, Planning and Economic Development"},
            {"name": "Janet Kataaha Museveni", "constituency": "Ruhaama", "party": "NRM", "title": "Minister of Education and Sports"},
            {"name": "Jane Ruth Aceng", "constituency": "Lira City", "party": "NRM", "title": "Minister of Health"},
            {"name": "Judith Nabakooba", "constituency": "Mityana", "party": "NRM", "title": "Minister of Lands, Housing and Urban Development"},
            {"name": "Frank Tumwebaze", "constituency": "Kibale East", "party": "NRM", "title": "Minister of Agriculture, Animal Industry and Fisheries"},
            {"name": "Nobert Mao", "constituency": "Gulu Municipality", "party": "DP", "title": "Minister of Justice and Constitutional Affairs"},
            {"name": "Raphael Magyezi", "constituency": "Igara West", "party": "NRM", "title": "Minister of Local Government"},
            {"name": "Chris Baryomunsi", "constituency": "Kinkizi East", "party": "NRM", "title": "Minister of ICT and National Guidance"},
            {"name": "Persis Namuganza", "constituency": "Bukono East", "party": "NRM", "title": "Minister of State for Lands"},
            {"name": "Mwebesa David Bahati", "constituency": "Ndorwa West", "party": "NRM", "title": "Minister of Trade, Industry and Cooperatives"},
            {"name": "Monica Azuba Ntege", "constituency": "Vurra", "party": "NRM", "title": "Minister of Works and Transport"},
            {"name": "Mary Goretti Kitutu", "constituency": "Manafwa", "party": "NRM", "title": "Minister of Energy and Mineral Development"},
            {"name": "Betty Amongi", "constituency": "Oyam South", "party": "NRM", "title": "Minister of Gender, Labour and Social Development"},
            {"name": "Sam Cheptoris", "constituency": "Tingey", "party": "NRM", "title": "Minister of Water and Environment"},
            {"name": "Tom Butime", "constituency": "Buhaguzi", "party": "NRM", "title": "Minister of Tourism, Wildlife and Antiquities"},
            {"name": "Musa Ecweru", "constituency": "Amuria", "party": "NRM", "title": "Minister of State for Works"},
            {"name": "Fred Byamukama", "constituency": "Kazo", "party": "NRM", "title": "Minister of State for Defence"},
            {"name": "Harriet Ntabazi", "constituency": "Rwampara", "party": "NRM", "title": "Minister of State for Trade"},
            {"name": "Esther Anyakun", "constituency": "Nakapiripirit", "party": "NRM", "title": "Minister of State for Relief and Disaster Preparedness"},
            {"name": "Godfrey Kiwanda", "constituency": "Mityana North", "party": "NRM", "title": "Minister of State for Tourism"},
            {"name": "Peter Ogwang", "constituency": "Usuk", "party": "NRM", "title": "Minister of State for Economic Monitoring"},
            {"name": "Anifa Kawooya", "constituency": "Sembabule", "party": "NRM", "title": "Minister of State for Housing"},
            {"name": "Henry Musasizi", "constituency": "Rubanda East", "party": "NRM", "title": "Minister of State for Finance (General Duties)"},
            {"name": "Amos Lugoloobi", "constituency": "Ntenjeru North", "party": "NRM", "title": "Minister of State for Finance (Planning)"},
            {"name": "Sidronius Okaasai Opolot", "constituency": "Tororo", "party": "NRM", "title": "Minister of State for Internal Affairs"},
            {"name": "Okello Oryem", "constituency": "Chua West", "party": "NRM", "title": "Minister of State for Foreign Affairs (International Affairs)"},
            {"name": "John Mulimba", "constituency": "Samia-Bugwe Central", "party": "NRM", "title": "Minister of State for Foreign Affairs (Regional Affairs)"},
            # === Judiciary ===
            {"name": "Alfonse Chigamoy Owiny-Dollo", "constituency": "National", "party": "", "title": "Chief Justice of Uganda"},
            {"name": "Richard Buteera", "constituency": "National", "party": "", "title": "Deputy Chief Justice of Uganda"},
            {"name": "Flavian Zeija", "constituency": "National", "party": "", "title": "Principal Judge of the High Court"},
            # === Bank of Uganda ===
            {"name": "Michael Atingi-Ego", "constituency": "National", "party": "", "title": "Deputy Governor, Bank of Uganda (Acting Governor)"},
            # === Military (UPDF) ===
            {"name": "Muhoozi Kainerugaba", "constituency": "National", "party": "", "title": "Chief of Defence Forces, UPDF"},
            {"name": "Peter Elwelu", "constituency": "National", "party": "", "title": "Former Joint Chief of Staff, UPDF"},
            {"name": "Wilson Mbadi", "constituency": "National", "party": "", "title": "Former Chief of Defence Forces, UPDF"},
            {"name": "Kayanja Muhanga", "constituency": "National", "party": "", "title": "Commander, UPDF Land Forces"},
            {"name": "Charles Okidi", "constituency": "National", "party": "", "title": "Commander, UPDF Air Force"},
            {"name": "David Mugisha", "constituency": "National", "party": "", "title": "Commander, Special Forces Command"},
            # === Intelligence Services ===
            {"name": "Tom Butime", "constituency": "National", "party": "", "title": "Former Director General, Internal Security Organisation (ISO)"},
            {"name": "Kaka Bagyenda", "constituency": "National", "party": "", "title": "Director General, Internal Security Organisation (ISO)"},
            {"name": "Charles Birungi", "constituency": "National", "party": "", "title": "Director General, External Security Organisation (ESO)"},
            {"name": "Abel Kandiho", "constituency": "National", "party": "", "title": "Former Chief of Military Intelligence (CMI)"},
            # === Police ===
            {"name": "Abbas Byakagaba", "constituency": "National", "party": "", "title": "Inspector General of Police"},
            # === Key Agencies ===
            {"name": "John Rujoki Musinguzi", "constituency": "National", "party": "", "title": "Commissioner General, Uganda Revenue Authority"},
            {"name": "Patrick Mweheire", "constituency": "National", "party": "", "title": "Managing Director, National Social Security Fund (NSSF)"},
            {"name": "Dorothy Kisaka", "constituency": "National", "party": "", "title": "Executive Director, Kampala Capital City Authority (KCCA)"},
            {"name": "Allen Kagina", "constituency": "National", "party": "", "title": "Executive Director, Uganda National Roads Authority (UNRA)"},
            {"name": "Proscovia Njuki", "constituency": "National", "party": "", "title": "Managing Director, Uganda Electricity Transmission Company (UETCL)"},
            # === Lord Mayor of Kampala ===
            {"name": "Erias Lukwago", "constituency": "Kampala", "party": "FDC-allied", "title": "Lord Mayor of Kampala"},
            # === Electoral Commission ===
            {"name": "Simon Byabakama", "constituency": "National", "party": "", "title": "Chairman, Electoral Commission of Uganda"},
            # === Inspector General of Government ===
            {"name": "Beti Kamya Turwomwe", "constituency": "National", "party": "", "title": "Inspector General of Government"},
            # === Political Party Leaders ===
            {"name": "Robert Kyagulanyi Ssentamu", "constituency": "Kyadondo East", "party": "NUP", "title": "President, National Unity Platform (NUP)"},
            {"name": "Patrick Oboi Amuriat", "constituency": "Kumi Municipality", "party": "FDC", "title": "President, Forum for Democratic Change (FDC)"},
            {"name": "Kizza Besigye", "constituency": "National", "party": "FDC", "title": "Former FDC President / Opposition Leader"},
            {"name": "Norbert Mao", "constituency": "Gulu Municipality", "party": "DP", "title": "President, Democratic Party (DP)"},
            {"name": "Jimmy Akena", "constituency": "Lira City East", "party": "UPC", "title": "President, Uganda People's Congress (UPC)"},
            {"name": "Mugisha Muntu", "constituency": "National", "party": "ANT", "title": "President, Alliance for National Transformation (ANT)"},
            # === Prominent Opposition MPs ===
            {"name": "Muwanga Kivumbi", "constituency": "Butambala", "party": "NUP", "title": "Member of Parliament, Shadow Minister"},
            {"name": "Medard Sseggona", "constituency": "Busiro East", "party": "NUP", "title": "Member of Parliament"},
            {"name": "Betty Nambooze", "constituency": "Mukono Municipality", "party": "NUP", "title": "Member of Parliament"},
            {"name": "Francis Zaake", "constituency": "Mityana Municipality", "party": "NUP", "title": "Member of Parliament"},
            {"name": "Allan Ssewanyana", "constituency": "Makindye West", "party": "NUP", "title": "Member of Parliament"},
            {"name": "Muhammad Ssegirinya", "constituency": "Kawempe North", "party": "NUP", "title": "Member of Parliament"},
            # === Prominent NRM MPs / Committee Chairs ===
            {"name": "David Bahati", "constituency": "Ndorwa West", "party": "NRM", "title": "Member of Parliament"},
            {"name": "Abed Bwanika", "constituency": "Kimanya-Kabonera", "party": "NRM", "title": "Member of Parliament"},
            {"name": "Anita Among", "constituency": "Soroti District", "party": "NRM", "title": "Chairperson, Committee on Rules"},
            {"name": "Kenneth Lubogo", "constituency": "Bulamogi", "party": "NRM", "title": "Chairperson, Committee on Legal and Parliamentary Affairs"},
            {"name": "Henry Musasizi", "constituency": "Rubanda East", "party": "NRM", "title": "Chairperson, Committee on Budget"},
            {"name": "Amos Kankunda", "constituency": "Rwampara", "party": "NRM", "title": "Chairperson, Committee on Finance"},
            {"name": "James Kakooza", "constituency": "Kabula", "party": "NRM", "title": "Chairperson, Committee on Defence and Internal Affairs"},
            # === Ambassadors ===
            {"name": "Adonia Ayebare", "constituency": "National", "party": "", "title": "Permanent Representative of Uganda to the United Nations"},
            {"name": "Robie Kakonge", "constituency": "National", "party": "", "title": "Ambassador of Uganda to the United States"},
            {"name": "Rebecca Amuge Otengo", "constituency": "National", "party": "", "title": "Ambassador of Uganda to the African Union"},
        ]
        return [
            RawPersonRecord(
                full_name=m["name"],
                title=m.get("title", "Member of Parliament"),
                institution="Parliament of Uganda",
                country_code="UG",
                source_url=BASE_URL,
                source_type="PARLIAMENT",
                raw_text=f"{m['name']} - {m.get('title', 'MP')}, {m['constituency']} ({m['party']})",
                scraped_at=now,
                extra_fields=m,
            )
            for m in mps
        ]
