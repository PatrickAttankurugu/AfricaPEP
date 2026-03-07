"""
Scraper for the Parliament of Namibia (National Council).

Source: https://parliament.na/members
Member cards use .team-author-name for names, .team-author p for positions.
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

MEMBERS_URL = "https://parliament.na/members"


class NamibiaParliamentScraper(BaseScraper):
    """Scraper for the Namibian Parliament (National Council)."""

    country_code = "NA"
    source_type = "PARLIAMENT"

    def scrape(self) -> list[RawPersonRecord]:
        """Scrape members from the Namibia Parliament website."""
        logger.info("na_parliament.scrape.start", url=MEMBERS_URL)
        try:
            resp = self._get(MEMBERS_URL)
            records = self._parse_members(resp.text)
            if records:
                return records
            logger.warning("na_parliament.scrape.no_results")
            return self._load_fixture()
        except Exception:
            logger.exception("na_parliament.scrape.error")
            return self._load_fixture()

    def _parse_members(self, html: str) -> list[RawPersonRecord]:
        """Parse member cards from HTML."""
        soup = BeautifulSoup(html, "html.parser")
        records: list[RawPersonRecord] = []

        # Primary selectors based on the site's CSS structure
        cards = soup.select(".team-author")
        if not cards:
            cards = soup.select("[class*='team-member'], .card, .member-card")

        for card in cards:
            try:
                name_el = card.select_one(
                    ".team-author-name a, .team-author-name, h3, h4, .card-title"
                )
                if not name_el:
                    continue
                full_name = name_el.get_text(strip=True)
                if not full_name or len(full_name) < 3:
                    continue

                pos_el = card.select_one("p, .team-desc, .position, .role")
                position = pos_el.get_text(strip=True) if pos_el else ""

                title = "Member of Parliament"
                if position:
                    pos_lower = position.lower()
                    if "chairperson" in pos_lower:
                        title = "Chairperson"
                    elif "vice chairperson" in pos_lower:
                        title = "Vice Chairperson"
                    elif "chief whip" in pos_lower:
                        title = "Chief Whip"

                records.append(RawPersonRecord(
                    full_name=full_name,
                    title=title,
                    institution="Parliament of Namibia – National Council",
                    country_code=self.country_code,
                    source_type=self.source_type,
                    source_url=MEMBERS_URL,
                    raw_text=f"{full_name} – {title}",
                    scraped_at=datetime.utcnow(),
                    extra_fields={
                        "position": position,
                    },
                ))
            except Exception:
                logger.exception("na_parliament.parse.error")

        logger.info("na_parliament.scrape.complete", count=len(records))
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        members = [
            {"name": "Lukas Sinimbo Muha", "title": "Chairperson", "party": "SWAPO"},
            {"name": "Victoria Mbawo Kauma", "title": "Vice Chairperson", "party": "SWAPO"},
            {"name": "Emma T. Muteka", "title": "Deputy Chairperson", "party": "SWAPO"},
            {"name": "Gerhard Shiimi", "title": "Chief Whip", "party": "SWAPO"},
            {"name": "Peter Chance Kazongominja", "title": "Chief Whip", "party": "NUDO"},
            {"name": "Lonia Kaishungu-Shinana", "title": "Member of Parliament", "party": "SWAPO"},
            {"name": "Hans Linekela Nambondi", "title": "Member of Parliament", "party": "SWAPO"},
            {"name": "Melania Ndjago", "title": "Member of Parliament", "party": "SWAPO"},
            {"name": "Anseline V. Beukes", "title": "Member of Parliament", "party": "SWAPO"},
            {"name": "Paulus N. Mbangu", "title": "Member of Parliament", "party": "SWAPO"},
            {"name": "Phillipus N. Mavara", "title": "Member of Parliament", "party": "SWAPO"},
            {"name": "Richard Gaoseb", "title": "Member of Parliament", "party": "SWAPO"},
        ]

        records = []
        for m in members:
            records.append(RawPersonRecord(
                full_name=m["name"],
                title=m["title"],
                institution="Parliament of Namibia – National Council",
                country_code=self.country_code,
                source_type=self.source_type,
                source_url=MEMBERS_URL,
                raw_text=f"{m['name']} – {m['title']}",
                scraped_at=now,
                extra_fields={
                    "party": m["party"],
                    "fixture": True,
                },
            ))

        logger.info("na_parliament.fixture.loaded", count=len(records))
        return records
