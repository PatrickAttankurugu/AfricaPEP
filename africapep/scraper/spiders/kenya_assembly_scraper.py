"""Scraper for current Members of Parliament published by Kenya's National Assembly."""
from __future__ import annotations

from datetime import datetime, timezone
from html.parser import HTMLParser

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

SOURCE_URL = "https://www.parliament.go.ke/the-national-assembly/mps"


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
            members = parse_members(response.text)
            if not members:
                break

            scraped_at = datetime.now(timezone.utc)
            for member in members:
                raw_parts = [
                    member["name"],
                    member.get("constituency"),
                    member.get("county"),
                    member.get("party"),
                    member.get("status"),
                ]
                records.append(
                    RawPersonRecord(
                        full_name=member["name"],
                        title="Member of Parliament",
                        institution="National Assembly of Kenya",
                        country_code=self.country_code,
                        source_url=SOURCE_URL,
                        source_type=self.source_type,
                        raw_text=" ".join(filter(None, raw_parts)),
                        scraped_at=scraped_at,
                        extra_fields={
                            key: value
                            for key, value in member.items()
                            if key != "name" and value
                        },
                    )
                )
            page += 1

            # Safety guard against infinite loops in tests or pagination drifts
            if page > 50:
                break

        return records
