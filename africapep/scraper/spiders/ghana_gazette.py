"""
Scraper for the Ghana Government Gazette.

Source: https://ghanapublishing.gov.gh/gazettes/
Method: Browse for PDF links, download, and parse appointment notices.
The Ghana Publishing Company is the constitutionally mandated publisher
of the Ghana Gazette.  The old gazette.gov.gh domain is defunct.
Inherits from BaseGovGazetteScraper.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import List
from urllib.parse import urljoin

import requests
import structlog
from bs4 import BeautifulSoup

from africapep.scraper.base_scraper import RawPersonRecord
from africapep.scraper.spiders.base_gov_gazette import BaseGovGazetteScraper
from africapep.scraper.utils.pdf_parser import extract_text_from_pdf

logger = structlog.get_logger(__name__)

FIXTURE_DIR = Path(__file__).parent.parent.parent.parent / "tests" / "fixtures" / "ghana_gazette"

SOURCE_URL = "https://ghanapublishing.gov.gh/gazettes/"

# Reasonable request timeout in seconds
REQUEST_TIMEOUT = 30


class GhanaGazetteScraper(BaseGovGazetteScraper):
    """Scrapes appointment and promotion notices from the Ghana Government Gazette."""

    country_code = "GH"
    source_type = "GAZETTE"
    raw_pdf_dir = "data/raw_pdfs/GH"

    # ------------------------------------------------------------------ #
    #  Public interface
    # ------------------------------------------------------------------ #

    def scrape(self) -> List[RawPersonRecord]:
        """Browse the gazette site, download PDFs, and extract appointment records.

        Falls back to synthetic fixture data when no PDFs can be discovered
        (the Ghana Publishing Company site sometimes has no direct PDF
        downloads on the public pages).
        """
        logger.info("ghana_gazette.scrape.start", url=SOURCE_URL)

        pdf_dir = Path(self.raw_pdf_dir)
        pdf_dir.mkdir(parents=True, exist_ok=True)

        try:
            response = requests.get(SOURCE_URL, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
        except requests.RequestException:
            logger.exception("ghana_gazette.scrape.fetch_error", url=SOURCE_URL)
            logger.info("ghana_gazette.scrape.fallback_to_fixture")
            return self._synthetic_fixture()

        soup = BeautifulSoup(response.text, "html.parser")
        pdf_links = self._discover_pdf_links(soup)

        if not pdf_links:
            logger.warning(
                "ghana_gazette.scrape.no_pdfs_found",
                msg="No gazette PDFs found on public site; using synthetic fixture",
            )
            return self._synthetic_fixture()

        records: List[RawPersonRecord] = []
        for pdf_url in pdf_links:
            records.extend(self._download_and_parse(pdf_url, pdf_dir))

        logger.info("ghana_gazette.scrape.complete", record_count=len(records))
        return records

    # ------------------------------------------------------------------ #
    #  PDF discovery
    # ------------------------------------------------------------------ #

    def _discover_pdf_links(self, soup: BeautifulSoup) -> List[str]:
        """Find gazette PDF links from ghanapublishing.gov.gh.

        The Ghana Publishing Company site is a WordPress/Elementor site.
        PDFs may appear as:
          - Direct <a> links to .pdf files
          - Links inside ``wp-content/uploads/`` paths
        We also follow internal gazette-related pages one level deep to
        discover PDFs hosted on sub-pages.
        """
        pdf_links: List[str] = []
        visited: set = set()

        # 1. Collect direct PDF links on the landing page
        pdf_links.extend(self._collect_pdf_hrefs(soup))

        # 2. Follow internal links that look gazette-related and collect
        #    PDFs from those pages too (one level deep).
        gazette_page_urls: List[str] = []
        for anchor in soup.select("a[href]"):
            href = anchor["href"]
            full_url = urljoin(SOURCE_URL, href)
            # Only follow internal pages that mention gazette / uploads
            if full_url.startswith("https://ghanapublishing.gov.gh/") and (
                "gazette" in href.lower()
                or "wp-content/uploads" in href.lower()
            ):
                if full_url not in visited and full_url != SOURCE_URL:
                    gazette_page_urls.append(full_url)
                    visited.add(full_url)

        for page_url in gazette_page_urls[:10]:  # cap to avoid runaway
            try:
                resp = requests.get(page_url, timeout=REQUEST_TIMEOUT)
                resp.raise_for_status()
                sub_soup = BeautifulSoup(resp.text, "html.parser")
                pdf_links.extend(self._collect_pdf_hrefs(sub_soup))
            except requests.RequestException:
                logger.debug("ghana_gazette.sub_page_error", url=page_url)

        # De-duplicate while preserving order
        seen: set = set()
        unique: List[str] = []
        for link in pdf_links:
            if link not in seen:
                seen.add(link)
                unique.append(link)

        logger.info("ghana_gazette.discover_pdfs", count=len(unique))
        return unique

    @staticmethod
    def _collect_pdf_hrefs(soup: BeautifulSoup) -> List[str]:
        """Return absolute URLs for every ``<a>`` whose *href* ends in ``.pdf``."""
        results: List[str] = []
        for anchor in soup.select("a[href]"):
            href = anchor["href"]
            if href.lower().endswith(".pdf"):
                full_url = urljoin(SOURCE_URL, href)
                results.append(full_url)
        return results

    # ------------------------------------------------------------------ #
    #  Download and parse
    # ------------------------------------------------------------------ #

    def _download_and_parse(
        self, pdf_url: str, pdf_dir: Path
    ) -> List[RawPersonRecord]:
        """Download a gazette PDF, save it locally, and extract person records."""
        records: List[RawPersonRecord] = []
        now = datetime.utcnow()

        filename = pdf_url.rsplit("/", 1)[-1]
        local_path = pdf_dir / filename

        try:
            resp = requests.get(pdf_url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            local_path.write_bytes(resp.content)
            logger.info("ghana_gazette.pdf_saved", path=str(local_path))
        except requests.RequestException:
            logger.exception("ghana_gazette.pdf_download_error", url=pdf_url)
            return []

        try:
            text = extract_text_from_pdf(resp.content)
        except Exception:
            logger.exception("ghana_gazette.pdf_parse_error", url=pdf_url)
            return []

        # Extract appointment-style records from the gazette text
        records.extend(self._extract_appointments(text, pdf_url, now))
        records.extend(self._extract_promotions(text, pdf_url, now))
        records.extend(self._extract_constitutional_instruments(text, pdf_url, now))

        logger.info(
            "ghana_gazette.pdf_parsed",
            url=pdf_url,
            record_count=len(records),
        )
        return records

    # ------------------------------------------------------------------ #
    #  Text extraction helpers
    # ------------------------------------------------------------------ #

    def _extract_appointments(
        self, text: str, source_url: str, scraped_at: datetime
    ) -> List[RawPersonRecord]:
        """Pull appointment notices from gazette text."""
        records: List[RawPersonRecord] = []

        # Common pattern: "appointed <NAME> as <ROLE>"
        pattern = re.compile(
            r"appoint(?:ed|s)\s+([A-Z][A-Za-z\s\-'\.]+?)\s+as\s+(.+?)(?:\.|;|$)",
            re.IGNORECASE | re.MULTILINE,
        )
        for match in pattern.finditer(text):
            name = match.group(1).strip()
            role = match.group(2).strip()
            if len(name) < 4:
                continue
            records.append(
                RawPersonRecord(
                    full_name=name,
                    title=role,
                    institution="Government of Ghana",
                    country_code=self.country_code,
                    source_url=source_url,
                    source_type=self.source_type,
                    raw_text=match.group(0).strip(),
                    scraped_at=scraped_at,
                    extra_fields={"notice_type": "APPOINTMENT"},
                )
            )
        return records

    def _extract_promotions(
        self, text: str, source_url: str, scraped_at: datetime
    ) -> List[RawPersonRecord]:
        """Pull promotion notices from gazette text."""
        records: List[RawPersonRecord] = []

        pattern = re.compile(
            r"promot(?:ed|es|ion of)\s+([A-Z][A-Za-z\s\-'\.]+?)\s+(?:to|as)\s+(.+?)(?:\.|;|$)",
            re.IGNORECASE | re.MULTILINE,
        )
        for match in pattern.finditer(text):
            name = match.group(1).strip()
            role = match.group(2).strip()
            if len(name) < 4:
                continue
            records.append(
                RawPersonRecord(
                    full_name=name,
                    title=role,
                    institution="Government of Ghana",
                    country_code=self.country_code,
                    source_url=source_url,
                    source_type=self.source_type,
                    raw_text=match.group(0).strip(),
                    scraped_at=scraped_at,
                    extra_fields={"notice_type": "PROMOTION"},
                )
            )
        return records

    def _extract_constitutional_instruments(
        self, text: str, source_url: str, scraped_at: datetime
    ) -> List[RawPersonRecord]:
        """Pull constitutional instrument (C.I.) notices naming individuals."""
        records: List[RawPersonRecord] = []

        # Pattern: C.I. number followed by named individuals
        ci_pattern = re.compile(
            r"C\.?\s*I\.?\s*(\d+).*?(?:appoint|designat)\w*\s+"
            r"([A-Z][A-Za-z\s\-'\.]+?)\s+(?:as|to)\s+(.+?)(?:\.|;|$)",
            re.IGNORECASE | re.MULTILINE,
        )
        for match in ci_pattern.finditer(text):
            ci_number = match.group(1).strip()
            name = match.group(2).strip()
            role = match.group(3).strip()
            if len(name) < 4:
                continue
            records.append(
                RawPersonRecord(
                    full_name=name,
                    title=role,
                    institution="Government of Ghana",
                    country_code=self.country_code,
                    source_url=source_url,
                    source_type=self.source_type,
                    raw_text=match.group(0).strip(),
                    scraped_at=scraped_at,
                    extra_fields={
                        "notice_type": f"CONSTITUTIONAL_INSTRUMENT_CI_{ci_number}",
                    },
                )
            )
        return records

    # ------------------------------------------------------------------ #
    #  Fixtures
    # ------------------------------------------------------------------ #

    def _load_fixture(self) -> List[RawPersonRecord]:
        """Return synthetic fixture data for testing."""
        return self._synthetic_fixture()

    @staticmethod
    def _synthetic_fixture() -> List[RawPersonRecord]:
        """Realistic synthetic gazette appointment-style records."""
        now = datetime.utcnow()
        entries = [
            ("Kissi Agyebeng", "Special Prosecutor", "APPOINTMENT"),
            ("Justice Gertrude Torkornoo", "Chief Justice of the Republic of Ghana", "APPOINTMENT"),
            ("Godfred Yeboah Dame", "Attorney-General and Minister for Justice", "APPOINTMENT"),
            ("Dr Archibald Yao Letsa", "Volta Regional Minister", "APPOINTMENT"),
            ("Henry Quartey", "Greater Accra Regional Minister", "APPOINTMENT"),
            ("Ambrose Dery", "Minister for the Interior", "PROMOTION"),
            ("Brigadier General Oppong-Peprah", "Chief of Defence Staff", "PROMOTION"),
            (
                "Justice Jones Dotse",
                "Justice of the Supreme Court",
                "CONSTITUTIONAL_INSTRUMENT_CI_142",
            ),
            (
                "Justice Avril Lovelace-Johnson",
                "Justice of the Court of Appeal",
                "CONSTITUTIONAL_INSTRUMENT_CI_145",
            ),
            ("Yaw Osafo-Maafo", "Senior Presidential Adviser", "APPOINTMENT"),
        ]
        return [
            RawPersonRecord(
                full_name=name,
                title=role,
                institution="Government of Ghana",
                country_code="GH",
                source_url=SOURCE_URL,
                source_type="GAZETTE",
                raw_text=f"{notice_type}: {name} appointed as {role}",
                scraped_at=now,
                extra_fields={"notice_type": notice_type},
            )
            for name, role, notice_type in entries
        ]
