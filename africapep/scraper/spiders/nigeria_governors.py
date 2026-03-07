"""
Scraper for Nigerian State Governors.

Source: https://statehouse.gov.ng/the-government/state-governors/
Extracts sitting governors and deputy governors from all 36 states.
"""

from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord
from africapep.scraper.utils.playwright_utils import get_page_content_sync

logger = structlog.get_logger(__name__)

GOVERNORS_URL = "https://statehouse.gov.ng/the-government/state-governors/"
NGF_URL = "https://nggovernorsforum.org/governors/"


class NigeriaGovernorsScraper(BaseScraper):
    """Scraper for Nigerian State Governors and Deputy Governors."""

    country_code = "NG"
    source_type = "STATE_EXECUTIVE"

    def scrape(self) -> list[RawPersonRecord]:
        """Scrape governors from State House and NGF websites."""
        records: list[RawPersonRecord] = []

        for label, url in [
            ("State House", GOVERNORS_URL),
            ("NGF", NGF_URL),
        ]:
            logger.info("governors.scrape.start", source=label, url=url)
            try:
                html = get_page_content_sync(url, timeout=30000)
                parsed = self._parse_governors(html, url)
                records.extend(parsed)
                logger.info(
                    "governors.scrape.complete", source=label, count=len(parsed)
                )
            except Exception:
                logger.exception("governors.scrape.error", source=label, url=url)

        return records

    def _parse_governors(self, html: str, source_url: str) -> list[RawPersonRecord]:
        """Parse governor listing page HTML into RawPersonRecord objects."""
        soup = BeautifulSoup(html, "html.parser")
        records: list[RawPersonRecord] = []

        cards = soup.select(
            ".governor-card, .team-member, .card, "
            "[class*='governor'], [class*='member'], article"
        )

        for card in cards:
            try:
                name_el = card.select_one(
                    ".name, .card-title, h3, h4, h2, strong"
                )
                if not name_el:
                    continue
                full_name = name_el.get_text(strip=True)
                if not full_name or len(full_name) < 3:
                    continue

                state_el = card.select_one(
                    ".state, .subtitle, .designation, p, span.desc"
                )
                state = state_el.get_text(strip=True) if state_el else ""

                party_el = card.select_one(".party, .party-name")
                party = party_el.get_text(strip=True) if party_el else ""

                record = RawPersonRecord(
                    full_name=full_name,
                    title=f"Governor of {state}" if state else "Governor",
                    institution=f"{state} State Government" if state else "State Government of Nigeria",
                    country_code=self.country_code,
                    source_type=self.source_type,
                    source_url=source_url,
                    raw_text=f"{full_name} – Governor, {state} State",
                    scraped_at=datetime.utcnow(),
                    extra_fields={
                        "state": state,
                        "party": party,
                        "html_snippet": str(card)[:500],
                    },
                )
                records.append(record)
            except Exception:
                logger.exception("governors.parse.error")

        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        """Load fixture data for testing. Falls back to synthetic data."""
        fixture_path = (
            Path(__file__).parent.parent / "fixtures" / "nigeria_governors.html"
        )
        if fixture_path.exists():
            html = fixture_path.read_text(encoding="utf-8")
            return self._parse_governors(html, GOVERNORS_URL)
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        """Generate synthetic fixture data with real Nigerian state governors."""
        now = datetime.utcnow()
        governors = [
            # ── South-West ──
            {
                "name": "Babajide Olusola Sanwo-Olu",
                "state": "Lagos",
                "party": "APC",
                "deputy": "Obafemi Hamzat",
                "since": "2019",
            },
            {
                "name": "Dapo Abiodun",
                "state": "Ogun",
                "party": "APC",
                "deputy": "Noimot Salako-Oyedele",
                "since": "2019",
            },
            {
                "name": "Ademola Adeleke",
                "state": "Osun",
                "party": "PDP",
                "deputy": "Kola Adewusi",
                "since": "2022",
            },
            {
                "name": "Seyi Makinde",
                "state": "Oyo",
                "party": "PDP",
                "deputy": "Bayo Lawal",
                "since": "2019",
            },
            {
                "name": "Biodun Oyebanji",
                "state": "Ekiti",
                "party": "APC",
                "deputy": "Monisade Afuye",
                "since": "2022",
            },
            {
                "name": "Lucky Aiyedatiwa",
                "state": "Ondo",
                "party": "APC",
                "deputy": "",
                "since": "2024",
            },
            # ── South-East ──
            {
                "name": "Charles Chukwuma Soludo",
                "state": "Anambra",
                "party": "APGA",
                "deputy": "Onyekachukwu Ibezim",
                "since": "2022",
            },
            {
                "name": "Alex Otti",
                "state": "Abia",
                "party": "LP",
                "deputy": "Ikechukwu Emetu",
                "since": "2023",
            },
            {
                "name": "Peter Mbah",
                "state": "Enugu",
                "party": "PDP",
                "deputy": "Ifeanyi Ossai",
                "since": "2023",
            },
            {
                "name": "Hope Uzodinma",
                "state": "Imo",
                "party": "APC",
                "deputy": "Placid Njoku",
                "since": "2020",
            },
            {
                "name": "Francis Nwifuru",
                "state": "Ebonyi",
                "party": "APC",
                "deputy": "Patricia Obila",
                "since": "2023",
            },
            # ── South-South ──
            {
                "name": "Siminalayi Fubara",
                "state": "Rivers",
                "party": "PDP",
                "deputy": "",
                "since": "2023",
            },
            {
                "name": "Monday Okpebholo",
                "state": "Edo",
                "party": "APC",
                "deputy": "Dennis Idahosa",
                "since": "2024",
            },
            {
                "name": "Umo Eno",
                "state": "Akwa Ibom",
                "party": "PDP",
                "deputy": "Akon Eyakenyi",
                "since": "2023",
            },
            {
                "name": "Sheriff Oborevwori",
                "state": "Delta",
                "party": "PDP",
                "deputy": "Monday Onyeme",
                "since": "2023",
            },
            {
                "name": "Douye Diri",
                "state": "Bayelsa",
                "party": "PDP",
                "deputy": "Lawrence Ewhrudjakpo",
                "since": "2020",
            },
            {
                "name": "Bassey Otu",
                "state": "Cross River",
                "party": "APC",
                "deputy": "Peter Odey",
                "since": "2023",
            },
            # ── North-West ──
            {
                "name": "Abba Kabir Yusuf",
                "state": "Kano",
                "party": "NNPP",
                "deputy": "Aminu Abdulsalam Gwarzo",
                "since": "2023",
            },
            {
                "name": "Uba Sani",
                "state": "Kaduna",
                "party": "APC",
                "deputy": "Hadiza Balarabe",
                "since": "2023",
            },
            {
                "name": "Dauda Lawal",
                "state": "Zamfara",
                "party": "PDP",
                "deputy": "Mani Malam Sani",
                "since": "2023",
            },
            {
                "name": "Ahmad Aliyu",
                "state": "Sokoto",
                "party": "APC",
                "deputy": "Idris Gobir",
                "since": "2023",
            },
            {
                "name": "Nasir Idris",
                "state": "Kebbi",
                "party": "PDP",
                "deputy": "Umar Tafida Abubakar",
                "since": "2023",
            },
            {
                "name": "Dikko Umaru Radda",
                "state": "Katsina",
                "party": "APC",
                "deputy": "Faruq Lawal Jobe",
                "since": "2023",
            },
            {
                "name": "Mohammed Bago",
                "state": "Niger",
                "party": "APC",
                "deputy": "Yakubu Garba",
                "since": "2023",
            },
            # ── North-East ──
            {
                "name": "Babagana Umara Zulum",
                "state": "Borno",
                "party": "APC",
                "deputy": "Umar Usman Kadafur",
                "since": "2019",
            },
            {
                "name": "Ahmadu Umaru Fintiri",
                "state": "Adamawa",
                "party": "PDP",
                "deputy": "Kaletapwa Farauta",
                "since": "2019",
            },
            {
                "name": "Mai Mala Buni",
                "state": "Yobe",
                "party": "APC",
                "deputy": "Idi Barde Gubana",
                "since": "2019",
            },
            {
                "name": "Inuwa Yahaya",
                "state": "Gombe",
                "party": "APC",
                "deputy": "Manassah Daniel Jatau",
                "since": "2019",
            },
            {
                "name": "Bala Mohammed",
                "state": "Bauchi",
                "party": "PDP",
                "deputy": "Auwal Jatau",
                "since": "2019",
            },
            {
                "name": "Datti Baba-Ahmed",
                "state": "Taraba",
                "party": "APC",
                "deputy": "",
                "since": "2023",
            },
            # ── North-Central ──
            {
                "name": "AbdulRahman AbdulRazaq",
                "state": "Kwara",
                "party": "APC",
                "deputy": "Kayode Alabi",
                "since": "2019",
            },
            {
                "name": "Caleb Mutfwang",
                "state": "Plateau",
                "party": "PDP",
                "deputy": "Josephine Piyo",
                "since": "2023",
            },
            {
                "name": "Hyacinth Alia",
                "state": "Benue",
                "party": "APC",
                "deputy": "Sam Ode",
                "since": "2023",
            },
            {
                "name": "Ahmed Aliyu Sokoto",
                "state": "Kogi",
                "party": "APC",
                "deputy": "Joel Salifu Onawo",
                "since": "2024",
            },
            {
                "name": "Abdullahi Sule",
                "state": "Nasarawa",
                "party": "APC",
                "deputy": "Emmanuel Akabe",
                "since": "2019",
            },
            # ── Former Governors (still politically active PEPs) ──
            {
                "name": "Abdullahi Umar Ganduje",
                "state": "Kano",
                "party": "APC",
                "deputy": "",
                "since": "2015-2023 (now APC National Chairman)",
            },
            {
                "name": "Godwin Obaseki",
                "state": "Edo",
                "party": "PDP",
                "deputy": "Philip Shaibu",
                "since": "2016-2024 (former governor)",
            },
            {
                "name": "Atiku Abubakar",
                "state": "Adamawa",
                "party": "PDP",
                "deputy": "",
                "since": "Former Vice President (1999-2007); perennial presidential candidate",
            },
        ]

        records: list[RawPersonRecord] = []

        for gov in governors:
            is_former = "former" in gov.get("since", "").lower() or "now" in gov.get("since", "").lower()
            if is_former:
                title = f"Former Governor of {gov['state']} State"
                institution = f"{gov['state']} State Government (former)"
            else:
                title = f"Governor of {gov['state']} State"
                institution = f"{gov['state']} State Government"

            # Override title for Atiku
            if gov["name"] == "Atiku Abubakar":
                title = "Former Vice President of Nigeria"
                institution = "Federal Government of Nigeria (former)"

            records.append(
                RawPersonRecord(
                    full_name=gov["name"],
                    title=title,
                    institution=institution,
                    country_code=self.country_code,
                    source_type=self.source_type,
                    source_url=GOVERNORS_URL,
                    raw_text=f"{gov['name']} – {title} ({gov['party']})",
                    scraped_at=now,
                    extra_fields={
                        "state": gov["state"],
                        "party": gov["party"],
                        "deputy_governor": gov.get("deputy", ""),
                        "in_office_since": gov.get("since", ""),
                        "fixture": True,
                    },
                )
            )

            # Also add deputy governors where available
            if gov.get("deputy") and not is_former:
                records.append(
                    RawPersonRecord(
                        full_name=gov["deputy"],
                        title=f"Deputy Governor of {gov['state']} State",
                        institution=f"{gov['state']} State Government",
                        country_code=self.country_code,
                        source_type=self.source_type,
                        source_url=GOVERNORS_URL,
                        raw_text=f"{gov['deputy']} – Deputy Governor, {gov['state']} State ({gov['party']})",
                        scraped_at=now,
                        extra_fields={
                            "state": gov["state"],
                            "party": gov["party"],
                            "governor": gov["name"],
                            "fixture": True,
                        },
                    )
                )

        logger.info("governors.synthetic_fixture.loaded", count=len(records))
        return records
