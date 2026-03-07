"""Reusable base class for government gazette PDF scrapers."""
import re
from abc import abstractmethod
from datetime import datetime
from pathlib import Path

import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord
from africapep.scraper.utils.pdf_parser import extract_text_from_pdf

log = structlog.get_logger()

# Patterns to detect appointments in gazette text
APPOINTMENT_PATTERNS = [
    # "appointed as Minister of ..."
    re.compile(
        r"(?:appointed|designated|assigned)\s+(?:as\s+)?(?:the\s+)?"
        r"(?P<title>[A-Z][^,.\n]{3,80}?)(?:\s+of\s+|\s+for\s+|\s*,)",
        re.IGNORECASE
    ),
    # "is hereby appointed as the ..."
    re.compile(
        r"is\s+hereby\s+(?:appointed|designated)\s+(?:as\s+)?(?:the\s+)?"
        r"(?P<title>[A-Z][^,.\n]{3,80})",
        re.IGNORECASE
    ),
    # "His Excellency ... President of ..."
    re.compile(
        r"(?:His|Her)\s+Excellency\s+(?P<name>[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4})",
        re.IGNORECASE
    ),
    # "Hon. John Doe"
    re.compile(
        r"(?:Hon\.|Honourable|Honorable)\s+(?P<name>[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})",
        re.IGNORECASE
    ),
    # "Nana/Alhaji/Chief Name Name"
    re.compile(
        r"(?:Nana|Alhaji|Alhaja|Otunba|Chief|Oba|Ooni)\s+"
        r"(?P<name>[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})",
        re.IGNORECASE
    ),
    # Constitutional Instrument patterns (Ghana specific)
    re.compile(
        r"(?:C\.?I\.?\s*\d+|Executive\s+Instrument|E\.?I\.?\s*\d+)\s*[-—:]\s*"
        r"(?P<title>[^\n]{5,100})",
        re.IGNORECASE
    ),
]


class BaseGovGazetteScraper(BaseScraper):
    """Base class for government gazette PDF scrapers."""

    source_type = "GAZETTE"
    gazette_base_url: str = ""
    raw_pdf_dir: str = ""

    def _save_pdf(self, url: str, filename: str) -> str:
        """Download PDF and save to raw_pdfs directory."""
        dest = Path(self.raw_pdf_dir) / filename
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            resp = self._get(url)
            dest.write_bytes(resp.content)
            log.info("gazette_pdf_saved", path=str(dest), size=len(resp.content))
        return str(dest)

    def _parse_gazette_text(self, text: str, source_url: str) -> list[RawPersonRecord]:
        """Extract person records from gazette text using regex patterns."""
        records = []
        seen_names = set()

        for pattern in APPOINTMENT_PATTERNS:
            for match in pattern.finditer(text):
                groups = match.groupdict()
                name_candidate = groups.get("name") or groups.get("title", "")
                name_candidate = name_candidate.strip()

                if not name_candidate or len(name_candidate) < 4:
                    continue
                if name_candidate.lower() in seen_names:
                    continue
                seen_names.add(name_candidate.lower())

                # Extract surrounding context (200 chars each side)
                start = max(0, match.start() - 200)
                end = min(len(text), match.end() + 200)
                context = text[start:end].strip()

                # Try to determine title from context
                title = groups.get("title", "")

                records.append(RawPersonRecord(
                    full_name=name_candidate[:200],
                    title=title[:200] if title else "",
                    institution=self.__class__.__name__.replace("Scraper", ""),
                    country_code=self.country_code,
                    source_url=source_url,
                    source_type="GAZETTE",
                    raw_text=context,
                    scraped_at=datetime.utcnow(),
                    extra_fields={
                        "pattern_matched": pattern.pattern[:50],
                        "gazette_url": source_url,
                    },
                ))

        log.info("gazette_parsed", url=source_url, records=len(records))
        return records

    @abstractmethod
    def scrape(self) -> list[RawPersonRecord]:
        ...

    @abstractmethod
    def _load_fixture(self) -> list[RawPersonRecord]:
        ...
