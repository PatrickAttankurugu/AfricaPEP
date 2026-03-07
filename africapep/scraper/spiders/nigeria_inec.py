"""
Scraper for the Independent National Electoral Commission (INEC) of Nigeria.

Source: https://inecnigeria.org
Extracts governorship and legislative election candidates and results.
Uses BeautifulSoup for HTML pages and PDF parsing for result documents.
"""

from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord
from africapep.scraper.utils.pdf_parser import extract_text_from_pdf
from africapep.scraper.utils.playwright_utils import get_page_content_sync

logger = structlog.get_logger(__name__)

BASE_URL = "https://inecnigeria.org"
ELECTION_RESULTS_URL = f"{BASE_URL}/election-results"
CANDIDATES_URL = f"{BASE_URL}/candidates"


class NigeriaINECScraper(BaseScraper):
    """Scraper for INEC Nigeria election candidates and results."""

    country_code = "NG"
    source_type = "ELECTORAL"

    def scrape(self) -> list[RawPersonRecord]:
        """Scrape election candidates and results from INEC website and PDFs."""
        records: list[RawPersonRecord] = []

        # Scrape HTML candidate listings
        records.extend(self._scrape_candidates_html())

        # Scrape PDF result documents
        records.extend(self._scrape_result_pdfs())

        return records

    def _scrape_candidates_html(self) -> list[RawPersonRecord]:
        """Scrape candidate listings from INEC HTML pages."""
        logger.info("inec.scrape_candidates.start", url=CANDIDATES_URL)
        records: list[RawPersonRecord] = []

        try:
            html = get_page_content_sync(CANDIDATES_URL, wait_seconds=5)
            records = self._parse_candidates_page(html)
            logger.info("inec.scrape_candidates.complete", count=len(records))
        except Exception:
            logger.exception("inec.scrape_candidates.error", url=CANDIDATES_URL)

        return records

    def _parse_candidates_page(self, html: str) -> list[RawPersonRecord]:
        """Parse candidate listing HTML into RawPersonRecord objects."""
        soup = BeautifulSoup(html, "html.parser")
        records: list[RawPersonRecord] = []

        rows = soup.select(
            "table tr, .candidate-row, .candidate-card, "
            "[class*='candidate'], [class*='result']"
        )

        for row in rows:
            try:
                cells = row.select("td")
                if cells and len(cells) >= 3:
                    full_name = cells[0].get_text(strip=True)
                    party = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                    constituency = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                    election_type = cells[3].get_text(strip=True) if len(cells) > 3 else ""
                    votes = cells[4].get_text(strip=True) if len(cells) > 4 else ""
                else:
                    name_el = row.select_one(".name, h3, h4, strong")
                    if not name_el:
                        continue
                    full_name = name_el.get_text(strip=True)
                    party_el = row.select_one(".party, .party-name")
                    party = party_el.get_text(strip=True) if party_el else ""
                    const_el = row.select_one(".constituency, .state, .region")
                    constituency = const_el.get_text(strip=True) if const_el else ""
                    election_type = ""
                    votes = ""

                if not full_name or len(full_name) < 3:
                    continue

                title = "Candidate"
                role = election_type if election_type else "Election Candidate"

                record = RawPersonRecord(
                    full_name=full_name,
                    title=f"{title} – {role}",
                    institution="Independent National Electoral Commission of Nigeria",
                    country_code=self.country_code,
                    source_type=self.source_type,
                    source_url=CANDIDATES_URL,
                    raw_text=f"{full_name} – {role} ({party})",
                    scraped_at=datetime.utcnow(),
                    extra_fields={
                        "party": party,
                        "constituency": constituency,
                        "election_type": election_type,
                        "votes": votes,
                        "data_source": "html",
                        "html_snippet": str(row)[:500],
                    },
                )
                records.append(record)
            except Exception:
                logger.exception("inec.parse_candidate.error")

        return records

    def _scrape_result_pdfs(self) -> list[RawPersonRecord]:
        """Discover and parse PDF result documents from INEC."""
        logger.info("inec.scrape_pdfs.start", url=ELECTION_RESULTS_URL)
        records: list[RawPersonRecord] = []

        try:
            html = get_page_content_sync(ELECTION_RESULTS_URL, wait_seconds=5)
            soup = BeautifulSoup(html, "html.parser")

            pdf_links = []
            for link in soup.select("a[href$='.pdf']"):
                href = link.get("href", "")
                if href:
                    pdf_url = urljoin(BASE_URL, href)
                    pdf_links.append(pdf_url)

            logger.info("inec.pdf_links.found", count=len(pdf_links))

            for pdf_url in pdf_links[:10]:  # Limit to 10 PDFs per run
                try:
                    pdf_records = self._parse_result_pdf(pdf_url)
                    records.extend(pdf_records)
                except Exception:
                    logger.exception("inec.parse_pdf.error", pdf_url=pdf_url)

        except Exception:
            logger.exception("inec.scrape_pdfs.error", url=ELECTION_RESULTS_URL)

        return records

    def _parse_result_pdf(self, pdf_url: str) -> list[RawPersonRecord]:
        """Extract candidate/result data from a single INEC PDF document."""
        logger.info("inec.parse_pdf.start", pdf_url=pdf_url)
        records: list[RawPersonRecord] = []

        try:
            text = extract_text_from_pdf(pdf_url)
        except Exception:
            logger.exception("inec.pdf_extract.error", pdf_url=pdf_url)
            return records

        lines = text.split("\n")

        current_state = ""
        current_election_type = ""

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            upper = stripped.upper()
            if "STATE" in upper and len(stripped.split()) <= 4:
                current_state = stripped.title()
                continue
            if "GOVERNORSHIP" in upper:
                current_election_type = "Governorship"
                continue
            if "SENATORIAL" in upper or "SENATE" in upper:
                current_election_type = "Senatorial"
                continue
            if "HOUSE OF REPRESENTATIVES" in upper:
                current_election_type = "House of Representatives"
                continue
            if "STATE HOUSE OF ASSEMBLY" in upper:
                current_election_type = "State House of Assembly"
                continue

            parts = [p.strip() for p in stripped.split("|")]
            if len(parts) < 2:
                parts = [p.strip() for p in stripped.split("\t")]

            if len(parts) >= 2:
                candidate_name = parts[0]
                party = parts[1] if len(parts) > 1 else ""
                votes = parts[2] if len(parts) > 2 else ""

                if not candidate_name or len(candidate_name) < 3:
                    continue
                if candidate_name.upper() == candidate_name and len(candidate_name) > 30:
                    continue  # Likely a header row

                election_label = current_election_type or "Election Candidate"
                record = RawPersonRecord(
                    full_name=candidate_name,
                    title=f"Candidate – {election_label}",
                    institution="Independent National Electoral Commission of Nigeria",
                    country_code=self.country_code,
                    source_type=self.source_type,
                    source_url=pdf_url,
                    raw_text=f"{candidate_name} – {election_label} ({party})",
                    scraped_at=datetime.utcnow(),
                    extra_fields={
                        "party": party,
                        "state": current_state,
                        "election_type": current_election_type,
                        "votes": votes,
                        "data_source": "pdf",
                        "pdf_url": pdf_url,
                    },
                )
                records.append(record)

        logger.info("inec.parse_pdf.complete", pdf_url=pdf_url, count=len(records))
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        """Load fixture data for testing. Falls back to synthetic data."""
        fixture_path = (
            Path(__file__).parent.parent / "fixtures" / "nigeria_inec.html"
        )
        if fixture_path.exists():
            html = fixture_path.read_text(encoding="utf-8")
            return self._parse_candidates_page(html)
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        """Generate synthetic fixture data with real Nigerian election candidates."""
        now = datetime.utcnow()
        candidates = [
            # 2023 Presidential election candidates
            {
                "name": "Bola Ahmed Tinubu",
                "party": "APC",
                "state": "Lagos",
                "election_type": "Presidential",
                "votes": "8,794,726",
                "result": "Winner",
            },
            {
                "name": "Atiku Abubakar",
                "party": "PDP",
                "state": "Adamawa",
                "election_type": "Presidential",
                "votes": "6,984,520",
                "result": "Runner-up",
            },
            {
                "name": "Peter Obi",
                "party": "LP",
                "state": "Anambra",
                "election_type": "Presidential",
                "votes": "6,101,533",
                "result": "Third Place",
            },
            {
                "name": "Rabiu Kwankwaso",
                "party": "NNPP",
                "state": "Kano",
                "election_type": "Presidential",
                "votes": "1,496,687",
                "result": "Fourth Place",
            },
            # Governorship candidates
            {
                "name": "Babajide Sanwo-Olu",
                "party": "APC",
                "state": "Lagos",
                "election_type": "Governorship",
                "votes": "762,134",
                "result": "Winner",
            },
            {
                "name": "Dapo Abiodun",
                "party": "APC",
                "state": "Ogun",
                "election_type": "Governorship",
                "votes": "299,465",
                "result": "Winner",
            },
            {
                "name": "Ademola Adeleke",
                "party": "PDP",
                "state": "Osun",
                "election_type": "Governorship",
                "votes": "403,371",
                "result": "Winner",
            },
            {
                "name": "Abdullahi Ganduje",
                "party": "APC",
                "state": "Kano",
                "election_type": "Governorship",
                "votes": "",
                "result": "Former Governor",
            },
            # Senatorial candidates
            {
                "name": "Oluremi Tinubu",
                "party": "APC",
                "state": "Lagos Central",
                "election_type": "Senatorial",
                "votes": "238,445",
                "result": "Winner",
            },
            {
                "name": "Ned Nwoko",
                "party": "PDP",
                "state": "Delta North",
                "election_type": "Senatorial",
                "votes": "154,890",
                "result": "Winner",
            },
            {
                "name": "Shehu Sani",
                "party": "PDP",
                "state": "Kaduna Central",
                "election_type": "Senatorial",
                "votes": "",
                "result": "Candidate",
            },
            {
                "name": "Dino Melaye",
                "party": "PDP",
                "state": "Kogi West",
                "election_type": "Senatorial",
                "votes": "",
                "result": "Candidate",
            },
        ]

        records: list[RawPersonRecord] = []

        for c in candidates:
            records.append(
                RawPersonRecord(
                    full_name=c["name"],
                    title=f"Candidate – {c['election_type']}",
                    institution="Independent National Electoral Commission of Nigeria",
                    country_code=self.country_code,
                    source_type=self.source_type,
                    source_url=CANDIDATES_URL,
                    raw_text=f"{c['name']} – {c['election_type']} Candidate ({c['party']})",
                    scraped_at=now,
                    extra_fields={
                        "party": c["party"],
                        "state": c["state"],
                        "election_type": c["election_type"],
                        "votes": c["votes"],
                        "result": c["result"],
                        "data_source": "synthetic",
                        "fixture": True,
                    },
                )
            )

        logger.info("inec.synthetic_fixture.loaded", count=len(records))
        return records
