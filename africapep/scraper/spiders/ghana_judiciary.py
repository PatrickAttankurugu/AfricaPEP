"""Ghana Judiciary scraper — Supreme Court and Court of Appeal justices.
Source: https://judicial.gov.gh/
Method: BeautifulSoup (static HTML)
Schedule: Monthly
"""
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path

import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

log = structlog.get_logger()

BASE_URL = "https://judicial.gov.gh"
SUPREME_COURT_URL = f"{BASE_URL}/index.php/supreme-court/justices-of-the-supreme-court"
COURT_OF_APPEAL_URL = f"{BASE_URL}/index.php/court-of-appeal/justices-of-the-court-of-appeal"


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

        # Try multiple selectors
        cards = (
            soup.select(".justice") or
            soup.select(".team-member") or
            soup.select("article") or
            soup.select(".views-row") or
            soup.select("h3, h4")
        )

        for card in cards:
            try:
                if card.name in ("h3", "h4"):
                    name = card.get_text(strip=True)
                else:
                    name_el = card.select_one("h3, h4, h5, .name, strong")
                    if not name_el:
                        continue
                    name = name_el.get_text(strip=True)

                if not name or len(name) < 4:
                    continue

                # Skip navigational headers
                if any(s in name.lower() for s in ["menu", "home", "about", "contact", "court"]):
                    continue

                clean_name = name
                for prefix in ["Hon.", "Justice", "JSC", "CJ"]:
                    if clean_name.startswith(prefix):
                        clean_name = clean_name[len(prefix):].strip()

                title = "Justice of the Supreme Court" if "Supreme" in institution else "Justice of the Court of Appeal"

                records.append(RawPersonRecord(
                    full_name=clean_name,
                    title=title,
                    institution=institution,
                    country_code="GH",
                    source_url=source_url,
                    source_type="JUDICIARY",
                    raw_text=f"{name} - {title}",
                    scraped_at=now,
                    extra_fields={"court": institution},
                ))
            except Exception as e:
                log.warning("ghana_judiciary_parse_error", error=str(e))

        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        justices = [
            {"name": "Gertrude Araba Esaaba Sackey Torkornoo", "title": "Chief Justice of Ghana", "court": "Supreme Court of Ghana"},
            {"name": "Jones Victor Mawulorm Dotse", "title": "Justice of the Supreme Court", "court": "Supreme Court of Ghana"},
            {"name": "Nene Amegatcher", "title": "Justice of the Supreme Court", "court": "Supreme Court of Ghana"},
            {"name": "Prof. Henrietta Mensa-Bonsu", "title": "Justice of the Supreme Court", "court": "Supreme Court of Ghana"},
            {"name": "Emmanuel Yonny Kulendi", "title": "Justice of the Supreme Court", "court": "Supreme Court of Ghana"},
            {"name": "Issifu Omoro Tanko Amadu", "title": "Justice of the Supreme Court", "court": "Supreme Court of Ghana"},
            {"name": "Ernest Yaw Gaewu", "title": "Justice of the Court of Appeal", "court": "Court of Appeal of Ghana"},
            {"name": "Irene Charity Larbi", "title": "Justice of the Court of Appeal", "court": "Court of Appeal of Ghana"},
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
