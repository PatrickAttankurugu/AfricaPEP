"""Ghana Judiciary scraper — Supreme Court and Court of Appeal justices.
Source: https://judicial.gov.gh/
Method: BeautifulSoup (static HTML, numbered text list)
Schedule: Monthly
"""
import re
from bs4 import BeautifulSoup
from datetime import datetime

import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

log = structlog.get_logger()

BASE_URL = "https://judicial.gov.gh"
SUPREME_COURT_URL = f"{BASE_URL}/index.php/about-the-judiciary/judges-and-magistrates/supremecourt-judges"
COURT_OF_APPEAL_URL = f"{BASE_URL}/index.php/about-the-judiciary/judges-and-magistrates/courtof-appeal-judges"

# Pattern: "1. His Lordship Justice Paul Baffoe-Bonnie - Chief Justice"
# or "1. Justice Mabel Maame Agyemang"
JUSTICE_PATTERN = re.compile(
    r'(\d+)\.\s*(?:His Lordship|Her Ladyship)?\s*(?:Justice\s*)?(.+)',
    re.IGNORECASE,
)


class GhanaJudiciaryScraper(BaseScraper):
    """Scraper for Ghana Supreme Court and Court of Appeal justices."""

    country_code = "GH"
    source_type = "JUDICIARY"

    def scrape(self) -> list[RawPersonRecord]:
        records = []

        for url, court in [
            (SUPREME_COURT_URL, "Supreme Court of Ghana"),
            (COURT_OF_APPEAL_URL, "Court of Appeal of Ghana"),
        ]:
            try:
                resp = self._get(url)
                soup = BeautifulSoup(resp.text, "html.parser")
                batch = self._parse_justices(soup, url, court)
                records.extend(batch)
                log.info("ghana_judiciary_scraped", court=court, count=len(batch))
            except Exception as e:
                log.error("ghana_judiciary_failed", court=court, error=str(e))

        return records

    def _parse_justices(self, soup: BeautifulSoup, source_url: str,
                        institution: str) -> list[RawPersonRecord]:
        records = []
        now = datetime.utcnow()

        # The page content is a plain numbered list inside the article/content area
        content = soup.select_one("article, .item-page, #content, main")
        if not content:
            content = soup

        # Use space separator to get contiguous text (newline splits numbered items)
        text = content.get_text(" ", strip=True)
        text = text.replace("\xa0", " ").replace("\u00a0", " ")

        title_prefix = "Justice of the Supreme Court" if "Supreme" in institution else "Justice of the Court of Appeal"

        # Extract "N. Name" entries from flat text
        entries = re.findall(
            r'(\d+)\.\s+((?:His Lordship|Her Ladyship)?\s*(?:Justice)?\s*[A-Z][^0-9]+?)(?=\d+\.|$)',
            text,
        )

        for _, raw_name in entries:
            raw_name = raw_name.strip().rstrip(". ")

            # Remove trailing role like "- Chief Justice"
            role = ""
            if " - " in raw_name:
                parts = raw_name.split(" - ", 1)
                raw_name = parts[0].strip()
                role = parts[1].strip()

            # Clean prefixes
            clean_name = raw_name
            for prefix in ["His Lordship ", "Her Ladyship ", "Justice ", "Prof. ", "Professor ", "Dr. ", "Dr ", "Sir "]:
                if clean_name.startswith(prefix):
                    clean_name = clean_name[len(prefix):].strip()

            clean_name = " ".join(clean_name.split())

            if not clean_name or len(clean_name) < 4:
                continue

            title = role if role else title_prefix

            records.append(RawPersonRecord(
                full_name=clean_name,
                title=title,
                institution=institution,
                country_code="GH",
                source_url=source_url,
                source_type="JUDICIARY",
                raw_text=f"{raw_name} - {title}",
                scraped_at=now,
                extra_fields={"court": institution, "raw_name": raw_name},
            ))

        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        justices = [
            {"name": "Paul Baffoe-Bonnie", "title": "Chief Justice", "court": "Supreme Court of Ghana"},
            {"name": "Gabriel Pwamang", "title": "Justice of the Supreme Court", "court": "Supreme Court of Ghana"},
            {"name": "Avril Lovelace Johnson", "title": "Justice of the Supreme Court", "court": "Supreme Court of Ghana"},
            {"name": "Issifu Omoro Tanko Amadu", "title": "Justice of the Supreme Court", "court": "Supreme Court of Ghana"},
            {"name": "Henrietta Joy Abena Nyarko Mensa-Bonsu", "title": "Justice of the Supreme Court", "court": "Supreme Court of Ghana"},
            {"name": "Emmanuel Yonny Kulendi", "title": "Justice of the Supreme Court", "court": "Supreme Court of Ghana"},
            {"name": "Mabel Maame Agyemang", "title": "Justice of the Court of Appeal", "court": "Court of Appeal of Ghana"},
            {"name": "Anthony Oppong", "title": "Justice of the Court of Appeal", "court": "Court of Appeal of Ghana"},
        ]
        return [
            RawPersonRecord(
                full_name=j["name"],
                title=j["title"],
                institution=j["court"],
                country_code="GH",
                source_url=SUPREME_COURT_URL,
                source_type="JUDICIARY",
                raw_text=f"{j['name']} - {j['title']}",
                scraped_at=now,
                extra_fields=j,
            )
            for j in justices
        ]
