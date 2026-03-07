"""
Scraper for the Nigerian Presidency / State House.

Source: https://statehouse.gov.ng
Extracts cabinet ministers, special advisers, and senior staff
from the official State House website.
"""

from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord
from africapep.scraper.utils.playwright_utils import get_page_content_sync

logger = structlog.get_logger(__name__)

BASE_URL = "https://statehouse.gov.ng"
CABINET_URL = f"{BASE_URL}/administration/cabinet"
ADVISERS_URL = f"{BASE_URL}/administration/special-advisers"
SENIOR_STAFF_URL = f"{BASE_URL}/administration/senior-staff"


class NigeriaPresidencyScraper(BaseScraper):
    """Scraper for the Nigerian Presidency and State House officials."""

    country_code = "NG"
    source_type = "PRESIDENCY"

    def scrape(self) -> list[RawPersonRecord]:
        """Scrape presidency officials from multiple State House pages."""
        records: list[RawPersonRecord] = []

        page_configs = [
            ("Cabinet Ministers", CABINET_URL, "Minister"),
            ("Special Advisers", ADVISERS_URL, "Special Adviser"),
            ("Senior Staff", SENIOR_STAFF_URL, "Senior Staff"),
        ]

        for category, url, default_title in page_configs:
            logger.info("presidency.scrape.start", category=category, url=url)
            try:
                html = get_page_content_sync(url, timeout=30000)
                parsed = self._parse_officials(html, category, default_title, url)
                records.extend(parsed)
                logger.info(
                    "presidency.scrape.complete",
                    category=category,
                    count=len(parsed),
                )
            except Exception:
                logger.exception("presidency.scrape.error", category=category, url=url)

        return records

    def _parse_officials(
        self,
        html: str,
        category: str,
        default_title: str,
        source_url: str,
    ) -> list[RawPersonRecord]:
        """Parse an officials listing page into RawPersonRecord objects."""
        soup = BeautifulSoup(html, "html.parser")
        records: list[RawPersonRecord] = []

        cards = soup.select(
            ".team-member, .official-card, .minister-card, .card, "
            ".member-item, [class*='official'], [class*='minister']"
        )

        if not cards:
            cards = soup.select("article, .post, .entry, li.list-item")

        for card in cards:
            try:
                name_el = card.select_one(
                    ".name, .title, h3, h4, h2, .card-title, strong"
                )
                if not name_el:
                    continue
                full_name = name_el.get_text(strip=True)
                if not full_name or len(full_name) < 3:
                    continue

                role_el = card.select_one(
                    ".position, .role, .designation, .subtitle, p, span.desc"
                )
                role = role_el.get_text(strip=True) if role_el else ""

                title = default_title
                if role:
                    role_lower = role.lower()
                    if "minister of state" in role_lower:
                        title = "Minister of State"
                    elif "minister" in role_lower:
                        title = "Minister"
                    elif "adviser" in role_lower or "advisor" in role_lower:
                        title = "Special Adviser"
                    elif "secretary" in role_lower:
                        title = "Secretary"

                portfolio = role if role else category

                img_el = card.select_one("img")
                photo_url = ""
                if img_el and img_el.get("src"):
                    photo_url = img_el["src"]
                    if photo_url.startswith("/"):
                        photo_url = BASE_URL + photo_url

                record = RawPersonRecord(
                    full_name=full_name,
                    title=f"{title} – {portfolio}" if portfolio != category else title,
                    institution="Presidency of the Federal Republic of Nigeria",
                    country_code=self.country_code,
                    source_type=self.source_type,
                    source_url=source_url,
                    raw_text=f"{full_name} – {portfolio}",
                    scraped_at=datetime.utcnow(),
                    extra_fields={
                        "category": category,
                        "portfolio": portfolio,
                        "photo_url": photo_url,
                        "html_snippet": str(card)[:500],
                    },
                )
                records.append(record)
            except Exception:
                logger.exception(
                    "presidency.parse_official.error", category=category
                )

        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        """Load fixture data for testing. Falls back to synthetic data."""
        fixture_path = (
            Path(__file__).parent.parent / "fixtures" / "nigeria_presidency.html"
        )
        if fixture_path.exists():
            html = fixture_path.read_text(encoding="utf-8")
            return self._parse_officials(html, "Cabinet Ministers", "Minister", CABINET_URL)
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        """Generate synthetic fixture data with real Nigerian presidency officials."""
        now = datetime.utcnow()
        officials = [
            # ── Tier 1: President & Vice President ──
            {
                "name": "Bola Ahmed Tinubu",
                "title": "President",
                "role": "President, Commander-in-Chief of the Armed Forces",
                "category": "President",
            },
            {
                "name": "Kashim Shettima",
                "title": "Vice President",
                "role": "Vice President of the Federal Republic of Nigeria",
                "category": "Vice President",
            },
            # ── Cabinet Ministers ──
            {
                "name": "Nyesom Wike",
                "title": "Minister",
                "role": "Minister of the Federal Capital Territory",
                "category": "Cabinet Ministers",
            },
            {
                "name": "Wale Edun",
                "title": "Minister",
                "role": "Minister of Finance and Coordinating Minister of the Economy",
                "category": "Cabinet Ministers",
            },
            {
                "name": "Lateef Fagbemi",
                "title": "Attorney General",
                "role": "Attorney General of the Federation and Minister of Justice",
                "category": "Cabinet Ministers",
            },
            {
                "name": "Dele Alake",
                "title": "Minister",
                "role": "Minister of Solid Minerals Development",
                "category": "Cabinet Ministers",
            },
            {
                "name": "Festus Keyamo",
                "title": "Minister",
                "role": "Minister of Aviation and Aerospace Development",
                "category": "Cabinet Ministers",
            },
            {
                "name": "Mohammed Idris",
                "title": "Minister",
                "role": "Minister of Information and National Orientation",
                "category": "Cabinet Ministers",
            },
            {
                "name": "Adegboyega Oyetola",
                "title": "Minister",
                "role": "Minister of Marine and Blue Economy",
                "category": "Cabinet Ministers",
            },
            {
                "name": "Abubakar Atiku Bagudu",
                "title": "Minister",
                "role": "Minister of Budget and Economic Planning",
                "category": "Cabinet Ministers",
            },
            {
                "name": "Simon Bako Lalong",
                "title": "Minister",
                "role": "Minister of Labour and Employment",
                "category": "Cabinet Ministers",
            },
            {
                "name": "Hannatu Musawa",
                "title": "Minister",
                "role": "Minister of Art, Culture and the Creative Economy",
                "category": "Cabinet Ministers",
            },
            {
                "name": "Tahir Mamman",
                "title": "Minister",
                "role": "Minister of Education",
                "category": "Cabinet Ministers",
            },
            {
                "name": "Muhammad Ali Pate",
                "title": "Minister",
                "role": "Coordinating Minister of Health and Social Welfare",
                "category": "Cabinet Ministers",
            },
            {
                "name": "Abubakar Momoh",
                "title": "Minister",
                "role": "Minister of Niger Delta Development",
                "category": "Cabinet Ministers",
            },
            {
                "name": "Olubunmi Tunji-Ojo",
                "title": "Minister",
                "role": "Minister of Interior",
                "category": "Cabinet Ministers",
            },
            {
                "name": "Bosun Tijani",
                "title": "Minister",
                "role": "Minister of Communications, Innovation and Digital Economy",
                "category": "Cabinet Ministers",
            },
            {
                "name": "David Umahi",
                "title": "Minister",
                "role": "Minister of Works",
                "category": "Cabinet Ministers",
            },
            {
                "name": "Uju Kennedy-Ohanenye",
                "title": "Minister",
                "role": "Minister of Women Affairs",
                "category": "Cabinet Ministers",
            },
            {
                "name": "Mohammed Badaru Abubakar",
                "title": "Minister",
                "role": "Minister of Defence",
                "category": "Cabinet Ministers",
            },
            {
                "name": "Yusuf Tuggar",
                "title": "Minister",
                "role": "Minister of Foreign Affairs",
                "category": "Cabinet Ministers",
            },
            {
                "name": "Adebayo Adelabu",
                "title": "Minister",
                "role": "Minister of Power",
                "category": "Cabinet Ministers",
            },
            {
                "name": "Shuaibu Husseini Audu",
                "title": "Minister",
                "role": "Minister of Steel Development",
                "category": "Cabinet Ministers",
            },
            {
                "name": "Heineken Lokpobiri",
                "title": "Minister of State",
                "role": "Minister of State for Petroleum Resources (Oil)",
                "category": "Cabinet Ministers",
            },
            {
                "name": "Ekperikpe Ekpo",
                "title": "Minister of State",
                "role": "Minister of State for Petroleum Resources (Gas)",
                "category": "Cabinet Ministers",
            },
            {
                "name": "John Enoh",
                "title": "Minister",
                "role": "Minister of Sports Development",
                "category": "Cabinet Ministers",
            },
            {
                "name": "Uche Nnaji",
                "title": "Minister",
                "role": "Minister of Innovation, Science and Technology",
                "category": "Cabinet Ministers",
            },
            {
                "name": "Joseph Utsev",
                "title": "Minister",
                "role": "Minister of Water Resources and Sanitation",
                "category": "Cabinet Ministers",
            },
            {
                "name": "Ahmed Dangiwa",
                "title": "Minister",
                "role": "Minister of Housing and Urban Development",
                "category": "Cabinet Ministers",
            },
            {
                "name": "Balarabe Abbas Lawal",
                "title": "Minister",
                "role": "Minister of Environment",
                "category": "Cabinet Ministers",
            },
            {
                "name": "Betta Edu",
                "title": "Minister",
                "role": "Minister of Humanitarian Affairs and Poverty Reduction",
                "category": "Cabinet Ministers",
            },
            {
                "name": "Lola Ade-John",
                "title": "Minister",
                "role": "Minister of Tourism",
                "category": "Cabinet Ministers",
            },
            {
                "name": "Ayodele Olawande",
                "title": "Minister",
                "role": "Minister of Youth Development",
                "category": "Cabinet Ministers",
            },
            {
                "name": "Doris Anite",
                "title": "Minister",
                "role": "Minister of Industry, Trade and Investment",
                "category": "Cabinet Ministers",
            },
            {
                "name": "Saidu Ahmed Alkali",
                "title": "Minister",
                "role": "Minister of Transportation",
                "category": "Cabinet Ministers",
            },
            {
                "name": "Abubakar Kyari",
                "title": "Minister",
                "role": "Minister of Agriculture and Food Security",
                "category": "Cabinet Ministers",
            },
            {
                "name": "Nyesom Ezenwo Wike",
                "title": "Minister",
                "role": "Minister of the Federal Capital Territory",
                "category": "Cabinet Ministers",
            },
            # ── Ministers of State ──
            {
                "name": "Mariya Mahmoud Bunkure",
                "title": "Minister of State",
                "role": "Minister of State for Defence",
                "category": "Cabinet Ministers",
            },
            {
                "name": "Bianca Odumegwu-Ojukwu",
                "title": "Minister of State",
                "role": "Minister of State for Foreign Affairs",
                "category": "Cabinet Ministers",
            },
            {
                "name": "Uba Maigari Ahmadu",
                "title": "Minister of State",
                "role": "Minister of State for Health",
                "category": "Cabinet Ministers",
            },
            {
                "name": "Imaan Sulaiman-Ibrahim",
                "title": "Minister of State",
                "role": "Minister of State for Police Affairs",
                "category": "Cabinet Ministers",
            },
            {
                "name": "Yusuf Abdullahi Ata",
                "title": "Minister of State",
                "role": "Minister of State for Housing and Urban Development",
                "category": "Cabinet Ministers",
            },
            {
                "name": "Tijjani Muhammad-Bande",
                "title": "Minister of State",
                "role": "Minister of State for Education",
                "category": "Cabinet Ministers",
            },
            # ── Special Advisers ──
            {
                "name": "Hadiza Bala Usman",
                "title": "Special Adviser",
                "role": "Special Adviser on Policy Coordination",
                "category": "Special Advisers",
            },
            {
                "name": "Zahrah Audu",
                "title": "Special Adviser",
                "role": "Special Adviser on Revenue",
                "category": "Special Advisers",
            },
            {
                "name": "Daniel Bwala",
                "title": "Special Adviser",
                "role": "Special Adviser to the President on Media and Public Communication",
                "category": "Special Advisers",
            },
            {
                "name": "Ibrahim Masari",
                "title": "Special Adviser",
                "role": "Special Adviser on National Assembly Matters (Senate)",
                "category": "Special Advisers",
            },
            {
                "name": "Abdullahi Abbas",
                "title": "Special Adviser",
                "role": "Special Adviser on National Assembly Matters (House of Representatives)",
                "category": "Special Advisers",
            },
            {
                "name": "Nuhu Ribadu",
                "title": "Special Adviser",
                "role": "National Security Adviser",
                "category": "Special Advisers",
            },
            # ── Senior Staff ──
            {
                "name": "Femi Gbajabiamila",
                "title": "Senior Staff",
                "role": "Chief of Staff to the President",
                "category": "Senior Staff",
            },
            {
                "name": "George Akume",
                "title": "Senior Staff",
                "role": "Secretary to the Government of the Federation",
                "category": "Senior Staff",
            },
            {
                "name": "Ajuri Ngelale",
                "title": "Senior Staff",
                "role": "Special Adviser to the President on Media and Publicity",
                "category": "Senior Staff",
            },
            {
                "name": "Sunday Dare",
                "title": "Senior Staff",
                "role": "Special Adviser on Public Communication and National Orientation",
                "category": "Senior Staff",
            },
            {
                "name": "Folasade Yemi-Esan",
                "title": "Senior Staff",
                "role": "Head of the Civil Service of the Federation",
                "category": "Senior Staff",
            },
            {
                "name": "Olayemi Cardoso",
                "title": "Senior Staff",
                "role": "Governor of the Central Bank of Nigeria",
                "category": "Senior Staff",
            },
            # ── Former Presidents & Vice Presidents ──
            {
                "name": "Olusegun Obasanjo",
                "title": "Former President",
                "role": "Former President of Nigeria (1999-2007)",
                "category": "Former Leaders",
            },
            {
                "name": "Umaru Musa Yar'Adua",
                "title": "Former President (deceased)",
                "role": "Former President of Nigeria (2007-2010, deceased)",
                "category": "Former Leaders",
            },
            {
                "name": "Goodluck Ebele Jonathan",
                "title": "Former President",
                "role": "Former President of Nigeria (2010-2015)",
                "category": "Former Leaders",
            },
            {
                "name": "Muhammadu Buhari",
                "title": "Former President",
                "role": "Former President of Nigeria (2015-2023)",
                "category": "Former Leaders",
            },
            {
                "name": "Namadi Sambo",
                "title": "Former Vice President",
                "role": "Former Vice President of Nigeria (2010-2015)",
                "category": "Former Leaders",
            },
            {
                "name": "Yemi Osinbajo",
                "title": "Former Vice President",
                "role": "Former Vice President of Nigeria (2015-2023)",
                "category": "Former Leaders",
            },
        ]

        records: list[RawPersonRecord] = []

        for official in officials:
            records.append(
                RawPersonRecord(
                    full_name=official["name"],
                    title=official["role"],
                    institution="Presidency of the Federal Republic of Nigeria",
                    country_code=self.country_code,
                    source_type=self.source_type,
                    source_url=CABINET_URL,
                    raw_text=f"{official['name']} – {official['role']}",
                    scraped_at=now,
                    extra_fields={
                        "category": official["category"],
                        "fixture": True,
                    },
                )
            )

        logger.info("presidency.synthetic_fixture.loaded", count=len(records))
        return records
