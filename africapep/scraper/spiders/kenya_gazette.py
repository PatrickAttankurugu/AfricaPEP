"""
Scraper for the Kenya Government Gazette appointments.

Source: https://kenyagazette.go.ke
Method: PDF download and text extraction
Extracts: Government appointments from gazette PDFs
"""

from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path

import requests
import structlog

from africapep.scraper.spiders.base_gov_gazette import BaseGovGazetteScraper
from africapep.scraper.base_scraper import RawPersonRecord
from africapep.scraper.utils.pdf_parser import extract_text_from_pdf

logger = structlog.get_logger(__name__)


class KenyaGazetteScraper(BaseGovGazetteScraper):
    """Scraper for Kenya Government Gazette appointment notices."""

    country_code = "KE"
    source_type = "GOV_GAZETTE"
    raw_pdf_dir = "data/raw_pdfs/KE"

    SOURCE_URL = "https://kenyagazette.go.ke"
    FIXTURE_PATH = Path(__file__).parent / "fixtures" / "kenya_gazette.html"

    def scrape(self) -> list[RawPersonRecord]:
        """Scrape the Kenya Gazette website for appointment notices.

        Downloads gazette PDFs, extracts text, and parses appointment
        records from the extracted content.

        Returns:
            List of RawPersonRecord objects containing appointment data.
        """
        logger.info(
            "scraper.kenya_gazette.start",
            url=self.SOURCE_URL,
            country_code=self.country_code,
        )

        try:
            response = requests.get(self.SOURCE_URL, timeout=30)
            response.raise_for_status()
            html = response.text
        except requests.RequestException as exc:
            logger.error(
                "scraper.kenya_gazette.fetch_failed",
                url=self.SOURCE_URL,
                error=str(exc),
            )
            raise

        pdf_urls = self._extract_pdf_urls(html)
        logger.info(
            "scraper.kenya_gazette.pdf_urls_found",
            count=len(pdf_urls),
        )

        pdf_dir = Path(self.raw_pdf_dir)
        pdf_dir.mkdir(parents=True, exist_ok=True)

        records: list[RawPersonRecord] = []
        for pdf_url in pdf_urls:
            try:
                pdf_path = self._download_pdf(pdf_url, pdf_dir)
                text = extract_text_from_pdf(str(pdf_path))
                extracted = self._parse_appointments(text, pdf_url)
                records.extend(extracted)
            except Exception as exc:
                logger.error(
                    "scraper.kenya_gazette.pdf_processing_failed",
                    pdf_url=pdf_url,
                    error=str(exc),
                )
                continue

        logger.info(
            "scraper.kenya_gazette.complete",
            record_count=len(records),
        )
        return records

    def _extract_pdf_urls(self, html: str) -> list[str]:
        """Extract PDF download URLs from the gazette index page.

        Args:
            html: Raw HTML from the gazette website.

        Returns:
            List of absolute URLs to gazette PDF files.
        """
        soup = BeautifulSoup(html, "html.parser")
        pdf_links: list[str] = []

        for link in soup.find_all("a", href=True):
            href = link["href"]
            if href.endswith(".pdf") or "gazette" in href.lower():
                if href.startswith("http"):
                    pdf_links.append(href)
                elif href.startswith("/"):
                    pdf_links.append(f"{self.SOURCE_URL}{href}")

        return pdf_links

    def _download_pdf(self, pdf_url: str, pdf_dir: Path) -> Path:
        """Download a PDF file to the local raw PDF directory.

        Args:
            pdf_url: URL of the PDF to download.
            pdf_dir: Local directory to save the PDF.

        Returns:
            Path to the downloaded PDF file.
        """
        filename = pdf_url.split("/")[-1]
        if not filename.endswith(".pdf"):
            filename = f"{filename}.pdf"

        pdf_path = pdf_dir / filename
        if pdf_path.exists():
            logger.debug(
                "scraper.kenya_gazette.pdf_already_exists",
                path=str(pdf_path),
            )
            return pdf_path

        logger.info(
            "scraper.kenya_gazette.downloading_pdf",
            url=pdf_url,
        )
        response = requests.get(pdf_url, timeout=60)
        response.raise_for_status()

        pdf_path.write_bytes(response.content)
        return pdf_path

    def _parse_appointments(
        self, text: str, source_pdf_url: str
    ) -> list[RawPersonRecord]:
        """Parse extracted PDF text for government appointment records.

        Looks for appointment patterns such as:
        - 'APPOINTMENT OF ...'
        - 'is hereby appointed as ...'
        - Tabular appointment listings

        Args:
            text: Extracted text content from a gazette PDF.
            source_pdf_url: URL of the source PDF for provenance.

        Returns:
            List of RawPersonRecord objects extracted from the text.
        """
        records: list[RawPersonRecord] = []
        now = datetime.utcnow().isoformat()

        lines = text.split("\n")
        current_section = ""

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Track gazette section headers
            if stripped.isupper() and len(stripped) > 10:
                current_section = stripped

            # Look for appointment keywords
            appointment_keywords = [
                "is hereby appointed",
                "has been appointed",
                "appointment of",
                "nominated as",
                "designated as",
            ]

            for keyword in appointment_keywords:
                if keyword.lower() in stripped.lower():
                    name, position = self._extract_name_and_position(
                        stripped, keyword, lines, i
                    )
                    if name:
                        records.append(
                            RawPersonRecord(
                                full_name=name,
                                title=position or "Government Appointee",
                                institution="Government of Kenya",
                                country_code=self.country_code,
                                source_type=self.source_type,
                                source_url=source_pdf_url,
                                raw_text=stripped[:500],
                                scraped_at=now,
                                extra_fields={
                                    "position": position,
                                    "gazette_section": current_section,
                                    "appointment_text": stripped[:500],
                                    "source": "Kenya Gazette",
                                },
                            )
                        )
                    break

        return records

    def _extract_name_and_position(
        self,
        line: str,
        keyword: str,
        lines: list[str],
        line_index: int,
    ) -> tuple[str, str]:
        """Extract the appointee name and position from an appointment line.

        Args:
            line: The line containing the appointment keyword.
            keyword: The matched keyword.
            lines: All lines from the document for context.
            line_index: Index of the current line.

        Returns:
            Tuple of (name, position). Either may be empty if not found.
        """
        lower_line = line.lower()
        keyword_lower = keyword.lower()
        idx = lower_line.find(keyword_lower)

        name = ""
        position = ""

        if "appointment of" in keyword_lower:
            # Pattern: "APPOINTMENT OF John Doe AS Secretary"
            after = line[idx + len(keyword) :].strip()
            if " as " in after.lower():
                parts = after.split(" as ", 1)
                name = parts[0].strip().strip(",").strip(".")
                position = parts[1].strip().strip(",").strip(".")
            else:
                name = after.strip().strip(",").strip(".")
        else:
            # Pattern: "John Doe is hereby appointed as Secretary"
            before = line[:idx].strip()
            name = before.strip().strip(",").strip(".")

            after_keyword = line[idx + len(keyword) :].strip()
            if after_keyword.lower().startswith("as "):
                position = after_keyword[3:].strip().strip(",").strip(".")
            elif after_keyword:
                position = after_keyword.strip().strip(",").strip(".")

        # Clean up the name -- remove titles/prefixes
        for prefix in ["mr.", "mrs.", "ms.", "dr.", "hon.", "prof."]:
            if name.lower().startswith(prefix):
                name = name[len(prefix) :].strip()

        return name, position

    def _load_fixture(self) -> list[RawPersonRecord]:
        """Load fixture data for testing and development.

        If a fixture HTML file exists on disk, extract PDF URLs and
        process them. Otherwise, fall back to synthetic fixture data.

        Returns:
            List of RawPersonRecord objects from fixture data.
        """
        if self.FIXTURE_PATH.exists():
            logger.info(
                "scraper.kenya_gazette.loading_fixture",
                path=str(self.FIXTURE_PATH),
            )
            html = self.FIXTURE_PATH.read_text(encoding="utf-8")
            pdf_urls = self._extract_pdf_urls(html)
            # In fixture mode, we just return synthetic data
            # since we cannot download actual PDFs
            logger.info(
                "scraper.kenya_gazette.fixture_pdf_urls",
                count=len(pdf_urls),
            )

        logger.info("scraper.kenya_gazette.using_synthetic_fixture")
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        """Generate synthetic fixture data with realistic Kenya Gazette appointments.

        Returns:
            List of RawPersonRecord objects with realistic appointment data.
        """
        now = datetime.utcnow().isoformat()

        appointments = [
            {
                "name": "James Macharia",
                "position": "Cabinet Secretary for Transport and Infrastructure",
                "gazette_section": "GAZETTE NOTICE NO. 3456",
                "text": "Hon. James Macharia is hereby appointed as Cabinet Secretary for Transport and Infrastructure with effect from 1st January 2026.",
            },
            {
                "name": "Margaret Kobia",
                "position": "Chairperson, Public Service Commission",
                "gazette_section": "GAZETTE NOTICE NO. 3457",
                "text": "Prof. Margaret Kobia has been appointed as Chairperson of the Public Service Commission.",
            },
            {
                "name": "Fred Matiang'i",
                "position": "Cabinet Secretary for Interior and Coordination of National Government",
                "gazette_section": "GAZETTE NOTICE NO. 3458",
                "text": "Dr. Fred Matiang'i is hereby appointed as Cabinet Secretary for Interior and Coordination of National Government.",
            },
            {
                "name": "Amina Mohamed",
                "position": "Cabinet Secretary for Sports, Culture and Heritage",
                "gazette_section": "GAZETTE NOTICE NO. 3459",
                "text": "Amb. Amina Mohamed is hereby appointed as Cabinet Secretary for Sports, Culture and Heritage.",
            },
            {
                "name": "Peter Munya",
                "position": "Cabinet Secretary for Agriculture",
                "gazette_section": "GAZETTE NOTICE NO. 3460",
                "text": "Hon. Peter Munya has been appointed as Cabinet Secretary for Agriculture, Livestock, Fisheries and Cooperatives.",
            },
            {
                "name": "Keriako Tobiko",
                "position": "Cabinet Secretary for Environment and Forestry",
                "gazette_section": "GAZETTE NOTICE NO. 3461",
                "text": "Appointment of Keriako Tobiko as Cabinet Secretary for Environment and Forestry.",
            },
            {
                "name": "Mutahi Kagwe",
                "position": "Cabinet Secretary for Health",
                "gazette_section": "GAZETTE NOTICE NO. 3462",
                "text": "Hon. Mutahi Kagwe is hereby appointed as Cabinet Secretary for Health with immediate effect.",
            },
            {
                "name": "Betty Maina",
                "position": "Cabinet Secretary for Industrialization, Trade and Enterprise Development",
                "gazette_section": "GAZETTE NOTICE NO. 3463",
                "text": "Betty Maina has been appointed as Cabinet Secretary for Industrialization, Trade and Enterprise Development.",
            },
            {
                "name": "Eugene Wamalwa",
                "position": "Cabinet Secretary for Defence",
                "gazette_section": "GAZETTE NOTICE NO. 3464",
                "text": "Hon. Eugene Wamalwa is hereby appointed as Cabinet Secretary for Defence.",
            },
            {
                "name": "Njuguna Ndung'u",
                "position": "Cabinet Secretary for the National Treasury",
                "gazette_section": "GAZETTE NOTICE NO. 3465",
                "text": "Prof. Njuguna Ndung'u is hereby appointed as Cabinet Secretary for the National Treasury and Economic Planning.",
            },
            {
                "name": "Monica Juma",
                "position": "Cabinet Secretary for Energy",
                "gazette_section": "GAZETTE NOTICE NO. 3466",
                "text": "Amb. Monica Juma is hereby appointed as Cabinet Secretary for Energy.",
            },
            {
                "name": "Rachael Omamo",
                "position": "Cabinet Secretary for Foreign Affairs",
                "gazette_section": "GAZETTE NOTICE NO. 3467",
                "text": "Hon. Rachael Omamo has been appointed as Cabinet Secretary for Foreign Affairs.",
            },
        ]

        records = []
        for appt in appointments:
            records.append(
                RawPersonRecord(
                    full_name=appt["name"],
                    title=appt["position"],
                    institution="Government of Kenya",
                    country_code=self.country_code,
                    source_type=self.source_type,
                    source_url=self.SOURCE_URL,
                    raw_text=appt["text"],
                    scraped_at=now,
                    extra_fields={
                        "position": appt["position"],
                        "gazette_section": appt["gazette_section"],
                        "appointment_text": appt["text"],
                        "source": "Kenya Gazette",
                    },
                )
            )

        logger.info(
            "scraper.kenya_gazette.synthetic_fixture_loaded",
            record_count=len(records),
        )
        return records
