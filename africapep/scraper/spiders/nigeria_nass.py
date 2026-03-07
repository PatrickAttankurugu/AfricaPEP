"""
Scraper for the National Assembly of Nigeria (NASS).

Source: https://nass.gov.ng/members
Extracts senators and members of the House of Representatives,
including name, state, party, and committee memberships.
"""

from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord
from africapep.scraper.utils.playwright_utils import get_page_content_sync

logger = structlog.get_logger(__name__)

SENATE_URL = "https://nass.gov.ng/members/senate"
HOUSE_URL = "https://nass.gov.ng/members/house-of-reps"


class NigeriaNASSScraper(BaseScraper):
    """Scraper for the Nigerian National Assembly (Senate + House of Reps)."""

    country_code = "NG"
    source_type = "PARLIAMENT"

    def scrape(self) -> list[RawPersonRecord]:
        """Scrape both chambers of the National Assembly."""
        records: list[RawPersonRecord] = []

        for chamber, url in [("Senate", SENATE_URL), ("House of Representatives", HOUSE_URL)]:
            logger.info("nass.scrape.start", chamber=chamber, url=url)
            try:
                html = get_page_content_sync(url, timeout=30000)
                chamber_records = self._parse_members(html, chamber)
                records.extend(chamber_records)
                logger.info(
                    "nass.scrape.complete",
                    chamber=chamber,
                    count=len(chamber_records),
                )
            except Exception:
                logger.exception("nass.scrape.error", chamber=chamber, url=url)

        return records

    def _parse_members(self, html: str, chamber: str) -> list[RawPersonRecord]:
        """Parse member listing page HTML into RawPersonRecord objects."""
        soup = BeautifulSoup(html, "html.parser")
        records: list[RawPersonRecord] = []

        member_cards = soup.select(".member-card, .member-item, .card, tr.member-row")
        if not member_cards:
            member_cards = soup.select("[class*='member'], [class*='senator'], [class*='rep']")

        for card in member_cards:
            try:
                name_el = card.select_one(
                    ".member-name, .card-title, h3, h4, td:first-child, .name"
                )
                if not name_el:
                    continue
                full_name = name_el.get_text(strip=True)
                if not full_name:
                    continue

                state_el = card.select_one(
                    ".member-state, .state, .constituency, td:nth-child(2)"
                )
                state = state_el.get_text(strip=True) if state_el else ""

                party_el = card.select_one(
                    ".member-party, .party, td:nth-child(3)"
                )
                party = party_el.get_text(strip=True) if party_el else ""

                committees_el = card.select(".committee, .committee-name")
                committees = [c.get_text(strip=True) for c in committees_el]

                title = "Senator" if chamber == "Senate" else "Honourable Member"

                record = RawPersonRecord(
                    full_name=full_name,
                    title=title,
                    institution=f"National Assembly of Nigeria – {chamber}",
                    country_code=self.country_code,
                    source_type=self.source_type,
                    source_url=SENATE_URL if chamber == "Senate" else HOUSE_URL,
                    raw_text=f"{full_name} – {title}, {chamber}",
                    scraped_at=datetime.utcnow(),
                    extra_fields={
                        "party": party,
                        "state": state,
                        "chamber": chamber,
                        "committees": committees,
                        "html_snippet": str(card)[:500],
                    },
                )
                records.append(record)
            except Exception:
                logger.exception("nass.parse_member.error", chamber=chamber)

        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        """Load fixture data for testing. Falls back to synthetic data."""
        fixture_path = Path(__file__).parent.parent / "fixtures" / "nigeria_nass.html"
        if fixture_path.exists():
            html = fixture_path.read_text(encoding="utf-8")
            senate_records = self._parse_members(html, "Senate")
            house_records = self._parse_members(html, "House of Representatives")
            return senate_records + house_records
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        """Generate synthetic fixture data with real Nigerian legislators."""
        now = datetime.utcnow()
        senators = [
            # ── Senate Leadership ──
            {
                "name": "Godswill Akpabio",
                "state": "Akwa Ibom North-West",
                "party": "APC",
                "role": "Senate President",
                "committees": ["Rules and Business", "Appropriations"],
            },
            {
                "name": "Barau I. Jibrin",
                "state": "Kano North",
                "party": "APC",
                "role": "Deputy Senate President",
                "committees": ["Finance", "National Planning"],
            },
            {
                "name": "Opeyemi Bamidele",
                "state": "Ekiti Central",
                "party": "APC",
                "role": "Senate Leader",
                "committees": ["Judiciary, Human Rights and Legal Matters"],
            },
            # ── Prominent Senators ──
            {
                "name": "Ali Ndume",
                "state": "Borno South",
                "party": "APC",
                "role": "Senator",
                "committees": ["Army", "Defence"],
            },
            {
                "name": "Adams Oshiomhole",
                "state": "Edo North",
                "party": "APC",
                "role": "Senator",
                "committees": ["Labour", "Employment", "Productivity"],
            },
            {
                "name": "Ned Nwoko",
                "state": "Delta North",
                "party": "PDP",
                "role": "Senator",
                "committees": ["Appropriations", "Federal Character"],
            },
            {
                "name": "Shehu Buba",
                "state": "Yobe North",
                "party": "APC",
                "role": "Senator",
                "committees": ["National Security and Intelligence"],
            },
            {
                "name": "Danjuma Goje",
                "state": "Gombe Central",
                "party": "APC",
                "role": "Senator",
                "committees": ["Appropriations"],
            },
            {
                "name": "Orji Uzor Kalu",
                "state": "Abia North",
                "party": "APC",
                "role": "Chief Whip of the Senate",
                "committees": ["Privatisation and Commercialisation"],
            },
            {
                "name": "Osita Izunaso",
                "state": "Imo West",
                "party": "APC",
                "role": "Senator",
                "committees": ["Petroleum Resources (Upstream)"],
            },
            {
                "name": "Seriake Dickson",
                "state": "Bayelsa West",
                "party": "PDP",
                "role": "Senator",
                "committees": ["Marine Transport"],
            },
            {
                "name": "Ireti Kingibe",
                "state": "FCT",
                "party": "LP",
                "role": "Senator",
                "committees": ["FCT", "Women Affairs"],
            },
            {
                "name": "Oluremi Tinubu",
                "state": "Lagos Central",
                "party": "APC",
                "role": "Senator",
                "committees": ["Health (Secondary and Tertiary)"],
            },
            {
                "name": "Abdul Ahmed Ningi",
                "state": "Bauchi Central",
                "party": "PDP",
                "role": "Deputy Minority Leader",
                "committees": ["Finance"],
            },
            {
                "name": "Sumaila Abu Sadiq",
                "state": "Kwara North",
                "party": "APC",
                "role": "Senator",
                "committees": ["Agriculture"],
            },
            {
                "name": "Abubakar Kyari",
                "state": "Borno North",
                "party": "APC",
                "role": "Senator",
                "committees": ["Defence", "Interior"],
            },
            {
                "name": "Adamu Aliero",
                "state": "Kebbi Central",
                "party": "APC",
                "role": "Senator",
                "committees": ["Water Resources"],
            },
        ]

        house_members = [
            # ── House Leadership ──
            {
                "name": "Abbas Tajudeen",
                "state": "Zaria Federal Constituency, Kaduna",
                "party": "APC",
                "role": "Speaker, House of Representatives",
                "committees": ["Rules and Business"],
            },
            {
                "name": "Benjamin Kalu",
                "state": "Bende Federal Constituency, Abia",
                "party": "APC",
                "role": "Deputy Speaker",
                "committees": ["Media and Public Affairs"],
            },
            {
                "name": "Julius Ihonvbere",
                "state": "Owan Federal Constituency, Edo",
                "party": "APC",
                "role": "House Leader",
                "committees": ["Education"],
            },
            {
                "name": "Kingsley Chinda",
                "state": "Obio/Akpor Federal Constituency, Rivers",
                "party": "PDP",
                "role": "Minority Leader",
                "committees": ["Public Accounts"],
            },
            # ── Prominent House Members ──
            {
                "name": "Akin Alabi",
                "state": "Egbeda/Ona Ara Federal Constituency, Oyo",
                "party": "APC",
                "role": "Honourable Member",
                "committees": ["Commerce", "Public Procurement"],
            },
            {
                "name": "Muktar Betara",
                "state": "Biu/Bayo/Shani Federal Constituency, Borno",
                "party": "APC",
                "role": "Chairman, Appropriations Committee",
                "committees": ["Appropriations"],
            },
            {
                "name": "Oghene Egoh",
                "state": "Amuwo-Odofin Federal Constituency, Lagos",
                "party": "APC",
                "role": "Honourable Member",
                "committees": ["Finance"],
            },
            {
                "name": "Miriam Onuoha",
                "state": "Okigwe South Federal Constituency, Imo",
                "party": "APC",
                "role": "Honourable Member",
                "committees": ["Women in Parliament"],
            },
        ]

        records: list[RawPersonRecord] = []

        for s in senators:
            records.append(
                RawPersonRecord(
                    full_name=s["name"],
                    title=s["role"],
                    institution="National Assembly of Nigeria – Senate",
                    country_code=self.country_code,
                    source_type=self.source_type,
                    source_url=SENATE_URL,
                    raw_text=f"{s['name']} – {s['role']}, Senate",
                    scraped_at=now,
                    extra_fields={
                        "party": s["party"],
                        "state": s["state"],
                        "chamber": "Senate",
                        "committees": s["committees"],
                        "fixture": True,
                    },
                )
            )

        for m in house_members:
            records.append(
                RawPersonRecord(
                    full_name=m["name"],
                    title=m["role"],
                    institution="National Assembly of Nigeria – House of Representatives",
                    country_code=self.country_code,
                    source_type=self.source_type,
                    source_url=HOUSE_URL,
                    raw_text=f"{m['name']} – {m['role']}, House of Representatives",
                    scraped_at=now,
                    extra_fields={
                        "party": m["party"],
                        "state": m["state"],
                        "chamber": "House of Representatives",
                        "committees": m["committees"],
                        "fixture": True,
                    },
                )
            )

        logger.info("nass.synthetic_fixture.loaded", count=len(records))
        return records
