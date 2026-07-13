"""Scraper for current Members of Parliament published by Ghana's Parliament."""
from __future__ import annotations

from datetime import datetime, timezone
from html.parser import HTMLParser

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

SOURCE_URL = "https://www.parliament.gh/members"


class _MemberParser(HTMLParser):
    """Extract member cards from the Parliament site's server-rendered HTML."""

    def __init__(self) -> None:
        super().__init__()
        self.records: list[dict[str, str]] = []
        self._card_depth = 0
        self._card: dict[str, str] | None = None
        self._field: str | None = None
        self._field_parts: list[str] = []
        self._paragraph_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        classes = set((attrs_dict.get("class") or "").split())

        if tag == "div" and "position-relative" in classes and self._card is None:
            self._card = {}
            self._card_depth = 1
            return

        if self._card is None:
            return
        if tag == "div":
            self._card_depth += 1
        if tag == "h5":
            self._field = "name"
            self._field_parts = []
        elif tag == "p":
            self._field = "details"
            self._field_parts = []
            self._paragraph_parts = []

    def handle_data(self, data: str) -> None:
        if self._field is not None:
            self._field_parts.append(data.strip())
            if self._field == "details":
                self._paragraph_parts.append(data.strip())

    def handle_endtag(self, tag: str) -> None:
        if self._card is None:
            return
        if tag == "h5" and self._field == "name":
            self._card["name"] = " ".join(filter(None, self._field_parts))
            self._field = None
        elif tag == "p" and self._field == "details":
            details = [part for part in self._paragraph_parts if part]
            if details:
                self._card["constituency"] = details[0]
            if len(details) > 1:
                self._card["party"] = details[1]
            self._field = None
        elif tag == "div":
            self._card_depth -= 1
            if self._card_depth == 0:
                if self._card.get("name"):
                    self.records.append(self._card)
                self._card = None


def parse_members(html: str) -> list[dict[str, str]]:
    parser = _MemberParser()
    parser.feed(html)
    return parser.records


class GhanaParliamentScraper(BaseScraper):
    """Scrape current Ghanaian MPs from the official Parliament website."""

    country_code = "GH"
    source_type = "GHANA_PARLIAMENT"

    def scrape(self) -> list[RawPersonRecord]:
        records: list[RawPersonRecord] = []
        page = 1
        while True:
            url = SOURCE_URL if page == 1 else f"{SOURCE_URL}?page={page}"
            response = self._get(url)
            members = parse_members(response.text)
            if not members:
                break
            scraped_at = datetime.now(timezone.utc)
            for member in members:
                records.append(
                    RawPersonRecord(
                        full_name=member["name"],
                        title="Member of Parliament",
                        institution="Parliament of Ghana",
                        country_code=self.country_code,
                        source_url=SOURCE_URL,
                        source_type=self.source_type,
                        raw_text=" ".join(
                            filter(None, [member["name"], member.get("constituency"), member.get("party")])
                        ),
                        scraped_at=scraped_at,
                        extra_fields={
                            key: value
                            for key, value in member.items()
                            if key != "name"
                        },
                    )
                )
            page += 1
        return records
