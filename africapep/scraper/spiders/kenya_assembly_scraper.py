"""Scraper for current Members of Parliament published by Kenya's National Assembly."""
from __future__ import annotations

from datetime import datetime, timezone
from html.parser import HTMLParser
import re

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

SOURCE_URL = "https://www.parliament.go.ke/the-national-assembly/mps"

KNOWN_POST_NOMINALS = {
    "CBS", "EGH", "EBS", "MBS", "OGW", "HSC", "MP", "CS", "MGH", "SC", "CGH", "QC", "FCA", "FCPA", "CPA",
}


def _is_post_nominal(token: str) -> bool:
    clean = token.strip().strip(".")
    if not clean:
        return False
    if clean.upper() in KNOWN_POST_NOMINALS:
        return True
    # Heuristic: post-nominals are short all-caps tokens (2-4 chars), while name parts are longer
    if clean.isupper() and 2 <= len(clean) <= 4 and clean.isalpha():
        return True
    return False


def _clean_name(raw_name: str) -> str:
    """Clean Kenyan MP name string for entity resolution.

    - Normalizes curly apostrophes to ASCII standard.
    - Strips leading HON/HONOURABLE (with or without dot).
    - Removes parenthesized titles like (DR.), (ENG.), (AMB.), (PROF.).
    - Removes trailing comma-separated post-nominal honours (CBS, EGH, MP, CS, ...).
    - Converts surname-first comma into space while preserving name parts.
    - Collapses consecutive whitespace.
    """
    if not raw_name:
        return ""

    name = raw_name.strip()
    # Normalize curly apostrophes (e.g. KING’OLA, JALANG’O)
    name = name.replace("’", "'").replace("‘", "'").replace("`", "'")

    # 1. Remove leading HON or HONOURABLE (with optional dot and whitespace)
    name = re.sub(r"^(?:HON\b\.?|HONOURABLE\b\.?)\s*", "", name, flags=re.IGNORECASE)

    # 2. Remove parenthesized titles such as (DR.), (ENG.), (AMB.), (PROF.)
    name = re.sub(r"\s*\([A-Za-z\.\s]+\)\s*", " ", name)

    # 3. Handle trailing post-nominals vs surname-first commas
    parts = [p.strip() for p in name.split(",") if p.strip()]
    if not parts:
        return ""

    while parts and _is_post_nominal(parts[-1]):
        parts.pop()

    # Join remaining parts (converts surname-first comma into space)
    cleaned = " ".join(parts)

    # 4. Collapse whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


class _MemberParser(HTMLParser):
    """Extract member rows from the Kenya National Assembly server-rendered HTML."""

    def __init__(self) -> None:
        super().__init__()
        self.records: list[dict[str, str]] = []
        self._in_table = False
        self._in_row = False
        self._current_cells: list[str] = []
        self._current_cell_data: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        classes = (attrs_dict.get("class") or "").split()

        if tag == "table" and "cols-7" in classes:
            self._in_table = True
        elif self._in_table and tag == "tr":
            self._in_row = True
            self._current_cells = []
        elif self._in_row and tag in ("td", "th"):
            self._current_cell_data = []

    def handle_data(self, data: str) -> None:
        if self._in_row:
            text = data.strip()
            if text:
                self._current_cell_data.append(text)

    def handle_endtag(self, tag: str) -> None:
        if tag == "table":
            self._in_table = False
        elif self._in_table and tag == "tr":
            self._in_row = False
            if len(self._current_cells) >= 6:
                name = self._current_cells[0].strip()
                # Skip header row or empty names
                if name and not name.lower().startswith("member of parliament"):
                    county = self._current_cells[2].strip() if len(self._current_cells) > 2 else ""
                    constituency = self._current_cells[3].strip() if len(self._current_cells) > 3 else ""
                    party = self._current_cells[4].strip() if len(self._current_cells) > 4 else ""
                    status = self._current_cells[5].strip() if len(self._current_cells) > 5 else ""

                    self.records.append({
                        "name": name,
                        "county": county,
                        "constituency": constituency,
                        "party": party,
                        "status": status,
                    })
        elif self._in_row and tag in ("td", "th"):
            cell_text = " ".join(self._current_cell_data)
            self._current_cells.append(cell_text)


def parse_members(html: str) -> list[dict[str, str]]:
    """Parse HTML and return list of member dictionaries."""
    parser = _MemberParser()
    parser.feed(html)
    return parser.records


class KenyaNationalAssemblyScraper(BaseScraper):
    """Scrape current Kenyan MPs from the official Kenya National Assembly website."""

    country_code = "KE"
    source_type = "KENYA_NATIONAL_ASSEMBLY"

    def scrape(self) -> list[RawPersonRecord]:
        records: list[RawPersonRecord] = []
        page = 0
        while True:
            url = SOURCE_URL if page == 0 else f"{SOURCE_URL}?page={page}"
            response = self._get(url)
            # Ensure correct UTF-8 decoding for apostrophes and accents
            response.encoding = "utf-8"
            members = parse_members(response.text)
            if not members:
                break

            scraped_at = datetime.now(timezone.utc)
            for member in members:
                raw_name = member["name"]
                cleaned_name = _clean_name(raw_name)
                raw_parts = [
                    cleaned_name,
                    member.get("constituency"),
                    member.get("county"),
                    member.get("party"),
                    member.get("status"),
                ]
                extra_fields = {
                    key: value
                    for key, value in member.items()
                    if key != "name" and value
                }
                if raw_name:
                    extra_fields["name_as_published"] = raw_name

                records.append(
                    RawPersonRecord(
                        full_name=cleaned_name,
                        title="Member of Parliament",
                        institution="National Assembly of Kenya",
                        country_code=self.country_code,
                        source_url=SOURCE_URL,
                        source_type=self.source_type,
                        raw_text=" ".join(filter(None, raw_parts)),
                        scraped_at=scraped_at,
                        extra_fields=extra_fields,
                    )
                )
            page += 1

            # Safety guard against infinite loops in tests or pagination drifts
            if page > 50:
                break

        return records
