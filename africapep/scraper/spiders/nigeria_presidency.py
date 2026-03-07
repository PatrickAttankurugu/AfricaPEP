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
                "name": "Lateef Fagbemi",
                "title": "Attorney General",
                "role": "Attorney General and Minister of Justice",
                "category": "Cabinet Ministers",
            },
            {
                "name": "Mohammed Idris",
                "title": "Minister",
                "role": "Minister of Information and National Orientation",
                "category": "Cabinet Ministers",
            },
            {
                "name": "Hadiza Bala Usman",
                "title": "Special Adviser",
                "role": "Special Adviser on Policy Coordination",
                "category": "Special Advisers",
            },
            {
                "name": "Femi Gbajabiamila",
                "title": "Senior Staff",
                "role": "Chief of Staff to the President",
                "category": "Senior Staff",
            },
            {
                "name": "Ajuri Ngelale",
                "title": "Senior Staff",
                "role": "Special Adviser to the President on Media and Publicity",
                "category": "Senior Staff",
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
