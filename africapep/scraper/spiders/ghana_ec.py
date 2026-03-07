"""
Scraper for the Ghana Electoral Commission results page.

Source: https://ec.gov.gh/results/
Method: BeautifulSoup + PDF parsing for result sheets
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from urllib.parse import urljoin

import requests
import structlog
from bs4 import BeautifulSoup

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord
from africapep.scraper.utils.pdf_parser import extract_text_from_pdf

logger = structlog.get_logger(__name__)

FIXTURE_DIR = Path(__file__).parent.parent.parent.parent / "tests" / "fixtures" / "ghana_ec"

SOURCE_URL = "https://ec.gov.gh/results/"
BASE_URL = "https://ec.gov.gh"

# Reasonable request timeout in seconds
REQUEST_TIMEOUT = 30


class GhanaECScraper(BaseScraper):
    """Scrapes parliamentary election candidates and winners from the Ghana EC."""

    country_code = "GH"
    source_type = "ELECTORAL"

    # ------------------------------------------------------------------ #
    #  Public interface
    # ------------------------------------------------------------------ #

    def scrape(self) -> List[RawPersonRecord]:
        """Fetch the EC results page, discover PDF links, and parse them."""
        logger.info("ghana_ec.scrape.start", url=SOURCE_URL)

        try:
            response = requests.get(SOURCE_URL, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
        except requests.RequestException:
            logger.exception("ghana_ec.scrape.fetch_error", url=SOURCE_URL)
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        records: List[RawPersonRecord] = []

        # --- Phase 1: parse inline HTML tables for declared results --- #
        records.extend(self._parse_html_results(soup))

        # --- Phase 2: discover and parse linked PDF result sheets --- #
        pdf_links = self._discover_pdf_links(soup)
        for pdf_url in pdf_links:
            records.extend(self._parse_result_pdf(pdf_url))

        logger.info("ghana_ec.scrape.complete", record_count=len(records))
        return records

    # ------------------------------------------------------------------ #
    #  HTML parsing
    # ------------------------------------------------------------------ #

    def _parse_html_results(self, soup: BeautifulSoup) -> List[RawPersonRecord]:
        """Extract candidate records from any HTML result tables on the page."""
        records: List[RawPersonRecord] = []
        now = datetime.utcnow()

        tables = soup.select("table")
        for table in tables:
            rows = table.select("tr")
            for row in rows:
                cells = row.select("td")
                if len(cells) < 2:
                    continue

                try:
                    name = cells[0].get_text(strip=True)
                    if not name or name.lower() in ("candidate", "name", ""):
                        continue

                    party = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                    constituency = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                    votes = cells[3].get_text(strip=True) if len(cells) > 3 else ""
                    status = cells[4].get_text(strip=True) if len(cells) > 4 else ""

                    title = f"Parliamentary Candidate – {constituency}".strip(" –")
                    records.append(
                        RawPersonRecord(
                            full_name=name,
                            title=title,
                            institution="Electoral Commission of Ghana",
                            country_code=self.country_code,
                            source_url=SOURCE_URL,
                            source_type=self.source_type,
                            raw_text=f"{name} – {title} ({party})",
                            scraped_at=now,
                            extra_fields={
                                "party": party,
                                "votes": votes,
                                "status": status,
                                "constituency": constituency,
                            },
                        )
                    )
                except Exception:
                    logger.exception("ghana_ec.parse_html.row_error")
                    continue

        return records

    # ------------------------------------------------------------------ #
    #  PDF discovery and parsing
    # ------------------------------------------------------------------ #

    def _discover_pdf_links(self, soup: BeautifulSoup) -> List[str]:
        """Find all PDF links on the results page."""
        links: List[str] = []
        for anchor in soup.select("a[href]"):
            href = anchor["href"]
            if href.lower().endswith(".pdf"):
                full_url = urljoin(BASE_URL, href)
                links.append(full_url)
        logger.info("ghana_ec.discover_pdfs", count=len(links))
        return links

    def _parse_result_pdf(self, pdf_url: str) -> List[RawPersonRecord]:
        """Download a result-sheet PDF and extract candidate records."""
        records: List[RawPersonRecord] = []
        now = datetime.utcnow()

        try:
            resp = requests.get(pdf_url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
        except requests.RequestException:
            logger.exception("ghana_ec.pdf_download_error", url=pdf_url)
            return []

        try:
            text = extract_text_from_pdf(resp.content)
        except Exception:
            logger.exception("ghana_ec.pdf_parse_error", url=pdf_url)
            return []

        # Attempt to locate candidate lines in the extracted text.
        # EC result sheets commonly list: NAME  |  PARTY  |  VOTES
        lines = text.splitlines()
        for line in lines:
            candidate = self._parse_candidate_line(line)
            if candidate is None:
                continue
            name, party, votes = candidate
            records.append(
                RawPersonRecord(
                    full_name=name,
                    title="Parliamentary Candidate",
                    institution="Electoral Commission of Ghana",
                    country_code=self.country_code,
                    source_url=pdf_url,
                    source_type=self.source_type,
                    raw_text=f"{name} – Parliamentary Candidate ({party})",
                    scraped_at=now,
                    extra_fields={
                        "party": party,
                        "votes": votes,
                    },
                )
            )

        logger.info("ghana_ec.pdf_parsed", url=pdf_url, record_count=len(records))
        return records

    @staticmethod
    def _parse_candidate_line(line: str) -> Optional[tuple]:
        """
        Attempt to extract (name, party, votes) from a single text line.

        Returns ``None`` if the line does not look like a candidate entry.
        """
        line = line.strip()
        if not line or len(line) < 5:
            return None

        # Pattern: NAME   PARTY_ABBREV   DIGITS
        match = re.match(
            r"^([A-Z][A-Za-z\s\-'\.]+?)\s{2,}([A-Z]{2,10})\s{2,}([\d,]+)$",
            line,
        )
        if match:
            return match.group(1).strip(), match.group(2).strip(), match.group(3).strip()

        return None

    # ------------------------------------------------------------------ #
    #  Fixtures
    # ------------------------------------------------------------------ #

    def _load_fixture(self) -> List[RawPersonRecord]:
        """Return synthetic fixture data for testing."""
        return self._synthetic_fixture()

    @staticmethod
    def _synthetic_fixture() -> List[RawPersonRecord]:
        """Realistic synthetic data using real Ghana EC commissioner and candidate names."""
        now = datetime.utcnow()
        entries = [
            ("Jean Mensa", "Chairperson, Electoral Commission of Ghana", "NPP", "", "Declared"),
            ("Samuel Tettey", "Deputy Chairperson, Electoral Commission", "NPP", "", ""),
            ("Dr Eric Bossman Asare", "Deputy Chairperson, Electoral Commission", "", "", ""),
            ("Patrick Osei-Owusu", "Parliamentary Candidate – Bekwai", "NPP", "45,210", "Winner"),
            ("Lydia Seyram Alhassan", "Parliamentary Candidate – Ayawaso West Wuogon", "NPP", "52,301", "Winner"),
            ("Samuel Okudzeto Ablakwa", "Parliamentary Candidate – North Tongu", "NDC", "68,118", "Winner"),
            ("Haruna Iddrisu", "Parliamentary Candidate – Tamale South", "NDC", "55,702", "Winner"),
            ("Ursula Owusu-Ekuful", "Parliamentary Candidate – Ablekuma West", "NPP", "41,003", "Winner"),
        ]
        return [
            RawPersonRecord(
                full_name=name,
                title=role,
                institution="Electoral Commission of Ghana",
                country_code="GH",
                source_url=SOURCE_URL,
                source_type="ELECTORAL",
                raw_text=f"{name} – {role} ({party})",
                scraped_at=now,
                extra_fields={
                    "party": party,
                    "votes": votes,
                    "status": status,
                },
            )
            for name, role, party, votes, status in entries
        ]
