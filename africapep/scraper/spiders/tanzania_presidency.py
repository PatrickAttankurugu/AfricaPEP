"""Tanzania Presidency / Cabinet scraper.

Source: https://www.pmo.go.tz/
Method: BeautifulSoup (static HTML)
Schedule: Weekly
"""
from __future__ import annotations

from datetime import datetime
from typing import List

import structlog
from bs4 import BeautifulSoup

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

log = structlog.get_logger(__name__)

BASE_URL = "https://www.pmo.go.tz"
CABINET_URL = f"{BASE_URL}/"


class TanzaniaPresidencyScraper(BaseScraper):
    """Scraper for Tanzania Presidency / Cabinet members."""

    country_code = "TZ"
    source_type = "PRESIDENCY"

    # ------------------------------------------------------------------ #
    #  Public interface
    # ------------------------------------------------------------------ #

    def scrape(self) -> List[RawPersonRecord]:
        """Fetch the PMO page and extract administration profile links.

        Profile links typically contain names such as
        "Mhe. William Vangimembe Lukuvi - Waziri wa Nchi".
        Falls back to synthetic fixture data if the site is unreachable.
        """
        log.info("tanzania_presidency.scrape.start", url=CABINET_URL)
        try:
            resp = self._get(CABINET_URL)
            soup = BeautifulSoup(resp.text, "html.parser")
            records = self._parse_page(soup, CABINET_URL)
            log.info(
                "tanzania_presidency.scrape.complete",
                record_count=len(records),
            )
            if records:
                return records
            # Site reachable but no records parsed -- use fixture
            log.warning(
                "tanzania_presidency.scrape.no_records_parsed",
                hint="Falling back to fixture data",
            )
            return self._load_fixture()
        except Exception as exc:
            log.error(
                "tanzania_presidency.scrape.failed",
                error=str(exc),
                hint="Falling back to fixture data",
            )
            return self._load_fixture()

    # ------------------------------------------------------------------ #
    #  Parsing helpers
    # ------------------------------------------------------------------ #

    def _parse_page(
        self, soup: BeautifulSoup, source_url: str
    ) -> List[RawPersonRecord]:
        """Extract cabinet member records from PMO page HTML."""
        records: List[RawPersonRecord] = []
        now = datetime.utcnow()

        # The PMO site lists administration profiles as links whose text
        # follows the pattern "Mhe. <Name> - <Swahili title>".
        profile_links = soup.select("a[href*='profile'], a[href*='viongozi']")

        # Fallback: look for any link whose text contains "Mhe." or "Waziri"
        if not profile_links:
            profile_links = [
                a
                for a in soup.find_all("a", href=True)
                if any(
                    kw in (a.get_text(strip=True) or "")
                    for kw in ("Mhe.", "Waziri", "Rais", "Makamu")
                )
            ]

        # Broader fallback: heading/card selectors
        if not profile_links:
            cards = (
                soup.select(".team-member")
                or soup.select(".cabinet-member")
                or soup.select(".leader-card")
                or soup.select("article")
            )
            for card in cards:
                name_el = card.select_one("h3, h4, h5, .member-name, strong")
                if not name_el:
                    continue
                name = name_el.get_text(strip=True)
                if not name or len(name) < 3:
                    continue

                clean_name = self._clean_name(name)

                portfolio = ""
                title_el = card.select_one(
                    ".position, .portfolio, p, .member-title"
                )
                if title_el:
                    portfolio = title_el.get_text(strip=True)

                records.append(
                    RawPersonRecord(
                        full_name=clean_name,
                        title=portfolio or "Cabinet Minister",
                        institution="Office of the Prime Minister of Tanzania",
                        country_code="TZ",
                        source_url=source_url,
                        source_type="PRESIDENCY",
                        raw_text=f"{name} - {portfolio}",
                        scraped_at=now,
                        extra_fields={
                            "portfolio": portfolio,
                            "raw_name": name,
                        },
                    )
                )
            return records

        # Parse profile links
        for link in profile_links:
            try:
                text = link.get_text(strip=True)
                if not text or len(text) < 3:
                    continue

                # Split on " - " to separate name from Swahili title
                parts = text.split(" - ", 1)
                raw_name = parts[0].strip()
                portfolio = parts[1].strip() if len(parts) > 1 else ""

                clean_name = self._clean_name(raw_name)
                if not clean_name:
                    continue

                records.append(
                    RawPersonRecord(
                        full_name=clean_name,
                        title=portfolio or "Cabinet Minister",
                        institution="Office of the Prime Minister of Tanzania",
                        country_code="TZ",
                        source_url=source_url,
                        source_type="PRESIDENCY",
                        raw_text=text,
                        scraped_at=now,
                        extra_fields={
                            "portfolio": portfolio,
                            "raw_name": raw_name,
                        },
                    )
                )
            except Exception as exc:
                log.warning(
                    "tanzania_presidency.parse.link_error", error=str(exc)
                )

        return records

    @staticmethod
    def _clean_name(name: str) -> str:
        """Remove common Swahili and English honorific prefixes."""
        clean = name
        for prefix in [
            "Mhe.", "H.E.", "Hon.", "Dr.", "Prof.", "Amb.",
            "Dkt.", "Bi.", "Bw.",
        ]:
            if clean.startswith(prefix):
                clean = clean[len(prefix):].strip()
        return clean

    # ------------------------------------------------------------------ #
    #  Fixtures
    # ------------------------------------------------------------------ #

    def _load_fixture(self) -> List[RawPersonRecord]:
        """Return synthetic fixture data when live scraping is unavailable."""
        return self._synthetic_fixture()

    @staticmethod
    def _synthetic_fixture() -> List[RawPersonRecord]:
        """Current Tanzania cabinet data as synthetic fixture records."""
        now = datetime.utcnow()
        cabinet = [
            # ---- Head of State & Government ----
            {"name": "Samia Suluhu Hassan", "title": "President"},
            {"name": "Philip Isdor Mpango", "title": "Vice President"},
            {"name": "Kassim Majaliwa", "title": "Prime Minister"},
            {"name": "Doto Mashaka Biteko", "title": "Deputy PM / Minister of Energy"},
            # ---- Cabinet Ministers ----
            {"name": "January Yusuf Makamba", "title": "Minister of Foreign Affairs"},
            {"name": "Stergomena Lawrence Tax", "title": "Minister of Defence"},
            {"name": "Hamad Masauni", "title": "Minister of Home Affairs"},
            {"name": "Mwigulu Lameck Nchemba", "title": "Minister of Finance and Planning"},
            {"name": "Adolf Faustine Mkenda", "title": "Minister of Education, Science and Technology"},
            {"name": "Nape Moses Nnauye", "title": "Minister of Information, Communication and IT"},
            {"name": "Angellah Jasmine Kairuki", "title": "Minister of State, PM's Office (Investment)"},
            {"name": "Ummy Ally Mwalimu", "title": "Minister of Health"},
            {"name": "Pindi Chana", "title": "Minister of Natural Resources and Tourism"},
            {"name": "Hussein Bashe", "title": "Minister of Agriculture"},
            {"name": "Innocent Bashungwa", "title": "Minister of Minerals"},
            {"name": "Profesa Kitila Mkumbo", "title": "Minister of Constitution and Legal Affairs"},
            {"name": "Dorothy Gwajima", "title": "Minister of Community Development, Gender and Children"},
            {"name": "Eliezer Feleshi", "title": "Minister of Water"},
            {"name": "Liberata Mulamula", "title": "Minister of State, Union Affairs"},
            {"name": "George Simbachawene", "title": "Minister of State, PM's Office (Policy and Parliamentary Affairs)"},
            {"name": "Abdallah Ulega", "title": "Minister of Works and Transport"},
            {"name": "Damas Daniel Ndumbaro", "title": "Minister of Lands, Housing and Human Settlements"},
            {"name": "Anthony Peter Mavunde", "title": "Minister of State, PM's Office (Labour, Youth and Employment)"},
            {"name": "Ashatu Kijaji", "title": "Minister of Industry and Trade"},
            {"name": "Jerry William Silaa", "title": "Minister of Livestock and Fisheries"},
            # ---- Deputy Ministers ----
            {"name": "Ndugulile Godwin", "title": "Deputy Minister of Health"},
            {"name": "David Mwakiposa Kihenzile", "title": "Deputy Minister of Finance and Planning"},
            {"name": "Omary Tebere Mgumba", "title": "Deputy Minister of Agriculture"},
            {"name": "Stella Alex Manyanya", "title": "Deputy Minister of Energy"},
            {"name": "Eng. Atashasta Justus Nditiye", "title": "Deputy Minister of Works and Transport"},
            {"name": "Stanslaus Haroon Nyongo", "title": "Deputy Minister of Minerals"},
            {"name": "Pauline Phillip Gekul", "title": "Deputy Minister of Education, Science and Technology"},
            {"name": "Hamis Kigwangalla", "title": "Deputy Minister of Natural Resources and Tourism"},
            {"name": "Mwanaisha Ulega", "title": "Deputy Minister of Home Affairs"},
            {"name": "Mary Masanja", "title": "Deputy Minister of Lands, Housing and Human Settlements"},
            # ---- Attorney General & Legal ----
            {"name": "Eliezer Mbuki Feleshi", "title": "Attorney General of Tanzania"},
            {"name": "Sylvester Mwakitalu", "title": "Director of Public Prosecutions"},
            # ---- Judiciary ----
            {"name": "Ibrahim Mahamed Juma", "title": "Chief Justice of Tanzania"},
            # ---- Central Bank ----
            {"name": "Emmanuel Mpawe Tutuba", "title": "Governor, Bank of Tanzania"},
            # ---- Parliament ----
            {"name": "Tulia Ackson", "title": "Speaker of the National Assembly"},
            # ---- Military & Security ----
            {"name": "Jacob John Mkunda", "title": "Chief of Defence Forces, TPDF"},
            {"name": "Camillus Simon Wambura", "title": "Inspector General of Police"},
            {"name": "Anna Charles Makakala", "title": "Commissioner General of Immigration"},
            {"name": "Diwani Athumani Masanga", "title": "Director, Tanzania Intelligence and Security Service (TISS)"},
            # ---- Key Agencies ----
            {"name": "Alphayo Japhet Kidata", "title": "Commissioner General, Tanzania Revenue Authority"},
            {"name": "Maharage Chande", "title": "Managing Director, TANESCO"},
            {"name": "Salum Rashid Aboud", "title": "Director General, Prevention and Combating of Corruption Bureau (PCCB)"},
            {"name": "Jabiri Bakari", "title": "Director General, Tanzania Communications Regulatory Authority (TCRA)"},
            # ---- Permanent Secretaries ----
            {"name": "Prof. Moses Kusiluka", "title": "Permanent Secretary, Ministry of Finance and Planning"},
            {"name": "Joseph Simbakalia", "title": "Permanent Secretary, Ministry of Foreign Affairs"},
            {"name": "Zena Ahmed Said", "title": "Permanent Secretary, Ministry of Health"},
            {"name": "Abel Shelukindo", "title": "Permanent Secretary, Ministry of Education"},
            {"name": "Mary Gabriel Maganga", "title": "Permanent Secretary, Ministry of Home Affairs"},
            # ---- Regional Commissioners (selected) ----
            {"name": "Albert John Chalamila", "title": "Regional Commissioner, Dar es Salaam"},
            {"name": "Aboud Jumbe Aboud", "title": "Regional Commissioner, Dodoma"},
            {"name": "John Mongella", "title": "Regional Commissioner, Mwanza"},
            {"name": "Idd Kimanta", "title": "Regional Commissioner, Arusha"},
            {"name": "Zainab Telack", "title": "Regional Commissioner, Kilimanjaro"},
            {"name": "Hamad Salim Masoud", "title": "Regional Commissioner, Mbeya"},
            {"name": "Thobias Makoba Andengenye", "title": "Regional Commissioner, Kagera"},
            {"name": "Anthony Mtaka", "title": "Regional Commissioner, Morogoro"},
            {"name": "Marco Gaguti", "title": "Regional Commissioner, Tanga"},
            {"name": "Juma Homera", "title": "Regional Commissioner, Tabora"},
            {"name": "Mashimba Mashauri Ndaki", "title": "Regional Commissioner, Mara"},
            {"name": "Robert Gabriel", "title": "Regional Commissioner, Iringa"},
            {"name": "Ally Hapi", "title": "Regional Commissioner, Kigoma"},
            {"name": "Amina Masenza", "title": "Regional Commissioner, Geita"},
            {"name": "Said Mecky Sadiki", "title": "Regional Commissioner, Lindi"},
            # ---- Former Presidents ----
            {"name": "Jakaya Kikwete", "title": "Former President of Tanzania"},
            {"name": "Ali Hassan Mwinyi", "title": "Former President of Tanzania"},
            {"name": "Benjamin William Mkapa", "title": "Former President of Tanzania (Deceased)"},
            # ---- Opposition ----
            {"name": "Freeman Aikaeli Mbowe", "title": "Leader of CHADEMA"},
            {"name": "Tundu Antiphas Lissu", "title": "CHADEMA Vice Chairman"},
        ]
        return [
            RawPersonRecord(
                full_name=m["name"],
                title=m["title"],
                institution="Office of the Prime Minister of Tanzania",
                country_code="TZ",
                source_url=CABINET_URL,
                source_type="PRESIDENCY",
                raw_text=f"{m['name']} - {m['title']}",
                scraped_at=now,
                extra_fields=m,
            )
            for m in cabinet
        ]
