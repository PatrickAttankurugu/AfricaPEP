"""Nigeria Judiciary scraper — Supreme Court and Court of Appeal justices.
Source: https://supremecourt.gov.ng/
Method: BeautifulSoup (static HTML)
Schedule: Monthly
"""
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path

import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

log = structlog.get_logger()

SUPREME_COURT_URL = "https://supremecourt.gov.ng/TheJustices"
COURT_OF_APPEAL_URL = "https://courtofappeal.gov.ng/justices"


class NigeriaJudiciaryScraper(BaseScraper):
    """Scraper for Nigerian Supreme Court and Court of Appeal justices."""

    country_code = "NG"
    source_type = "JUDICIARY"

    def scrape(self) -> list[RawPersonRecord]:
        records = []

        # Supreme Court
        try:
            resp = self._get(SUPREME_COURT_URL)
            soup = BeautifulSoup(resp.text, "html.parser")
            records.extend(self._parse_justices(soup, SUPREME_COURT_URL, "Supreme Court of Nigeria"))
        except Exception as e:
            log.error("nigeria_supreme_court_failed", error=str(e))

        # Court of Appeal
        try:
            resp = self._get(COURT_OF_APPEAL_URL)
            soup = BeautifulSoup(resp.text, "html.parser")
            records.extend(self._parse_justices(soup, COURT_OF_APPEAL_URL, "Court of Appeal of Nigeria"))
        except Exception as e:
            log.error("nigeria_court_of_appeal_failed", error=str(e))

        return records

    def _parse_justices(self, soup: BeautifulSoup, source_url: str,
                        institution: str) -> list[RawPersonRecord]:
        records = []
        now = datetime.utcnow()

        # Try various selectors
        cards = (
            soup.select(".justice") or
            soup.select(".team-member") or
            soup.select(".member-card") or
            soup.select("article") or
            soup.select(".views-row") or
            soup.select("table tbody tr")
        )

        for card in cards:
            try:
                name_el = card.select_one("h3, h4, h5, .name, strong, td:first-child")
                if not name_el:
                    continue

                name = name_el.get_text(strip=True)
                if not name or len(name) < 4:
                    continue

                # Clean name
                clean_name = name
                for prefix in ["Hon.", "Justice", "JSC", "CJN", "PCA"]:
                    if clean_name.startswith(prefix):
                        clean_name = clean_name[len(prefix):].strip()

                title = "Justice of the Supreme Court" if "Supreme" in institution else "Justice of the Court of Appeal"

                records.append(RawPersonRecord(
                    full_name=clean_name,
                    title=title,
                    institution=institution,
                    country_code="NG",
                    source_url=source_url,
                    source_type="JUDICIARY",
                    raw_text=f"{name} - {title}",
                    scraped_at=now,
                    extra_fields={"court": institution, "raw_name": name},
                ))
            except Exception as e:
                log.warning("nigeria_judiciary_parse_error", error=str(e))

        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        justices = [
            # ── Supreme Court of Nigeria ──
            {"name": "Kudirat Motonmori Olatokunbo Kekere-Ekun", "title": "Chief Justice of Nigeria", "court": "Supreme Court"},
            {"name": "Uwani Musa Abba Aji", "title": "Justice of the Supreme Court", "court": "Supreme Court"},
            {"name": "Mohammed Lawal Garba", "title": "Justice of the Supreme Court", "court": "Supreme Court"},
            {"name": "Helen Moronkeji Ogunwumiju", "title": "Justice of the Supreme Court", "court": "Supreme Court"},
            {"name": "Adamu Jauro", "title": "Justice of the Supreme Court", "court": "Supreme Court"},
            {"name": "Tijjani Abubakar", "title": "Justice of the Supreme Court", "court": "Supreme Court"},
            {"name": "Emmanuel Akomaye Agim", "title": "Justice of the Supreme Court", "court": "Supreme Court"},
            {"name": "Lawal Maidama Garba", "title": "Justice of the Supreme Court", "court": "Supreme Court"},
            {"name": "Stephen Jonah Adah", "title": "Justice of the Supreme Court", "court": "Supreme Court"},
            {"name": "Abdu Aboki", "title": "Justice of the Supreme Court", "court": "Supreme Court"},
            {"name": "Habeeb Adewale Olumuyiwa Abiru", "title": "Justice of the Supreme Court", "court": "Supreme Court"},
            # ── Court of Appeal ──
            {"name": "Monica Bolna'an Dongban-Mensem", "title": "President, Court of Appeal", "court": "Court of Appeal"},
            {"name": "Uchechukwu Onyemenam", "title": "Justice of the Court of Appeal", "court": "Court of Appeal"},
            {"name": "Elfrieda Oluwayemisi Williams-Dawodu", "title": "Justice of the Court of Appeal", "court": "Court of Appeal"},
            {"name": "Biobele Abraham Georgewill", "title": "Justice of the Court of Appeal", "court": "Court of Appeal"},
            {"name": "Hamma Akawu Barka", "title": "Justice of the Court of Appeal", "court": "Court of Appeal"},
            # ── Federal High Court ──
            {"name": "John Tsoho", "title": "Chief Judge, Federal High Court", "court": "Federal High Court"},
        ]
        return [
            RawPersonRecord(
                full_name=j["name"],
                title=j["title"],
                institution=f"{j['court']} of Nigeria",
                country_code="NG",
                source_url=SUPREME_COURT_URL,
                source_type="JUDICIARY",
                raw_text=f"{j['name']} - {j['title']}",
                scraped_at=now,
                extra_fields=j,
            )
            for j in justices
        ]
