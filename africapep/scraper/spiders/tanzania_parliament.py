"""Scraper for the Tanzania Parliament (Bunge) members list.

Source: https://www.parliament.go.tz/parliament_member
API:    https://polis.bunge.go.tz/api/members (DataTable server-side API)
Method: JSON API via HTTP GET (params: start, length)
Extracts: MP name, constituency, party, member_type
Schedule: Weekly
"""
from datetime import datetime

import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

log = structlog.get_logger()

SOURCE_URL = "https://www.parliament.go.tz/parliament_member"
API_URL = "https://polis.bunge.go.tz/api/members"
PAGE_SIZE = 100


class TanzaniaParliamentScraper(BaseScraper):
    """Scraper for Tanzania Parliament (Bunge) MPs."""

    country_code = "TZ"
    source_type = "PARLIAMENT"

    def scrape(self) -> list[RawPersonRecord]:
        records = []
        start = 0

        while True:
            try:
                resp = self._get(f"{API_URL}?start={start}&length={PAGE_SIZE}")
                data = resp.json()
            except Exception as e:
                log.error("tanzania_parliament_request_failed", url=API_URL, start=start, error=str(e))
                break

            members = data.get("data", [])
            if not members:
                break

            batch = self._parse_members(members)
            records.extend(batch)
            log.info("tanzania_parliament_page", start=start, found=len(batch))

            # Check if we have fetched all records
            total = data.get("recordsTotal", 0)
            start += PAGE_SIZE
            if start >= total:
                break

        return records

    def _parse_members(self, members: list[dict]) -> list[RawPersonRecord]:
        records = []
        now = datetime.utcnow()

        for member in members:
            try:
                first_name = (member.get("first_name") or "").strip()
                middle_name = (member.get("middle_name") or "").strip()
                surname = (member.get("surname") or "").strip()

                name_parts = [p for p in [first_name, middle_name, surname] if p]
                full_name = " ".join(name_parts)

                if not full_name or len(full_name) < 3:
                    continue

                constituency = (member.get("constituent") or "").strip()
                party = (member.get("political_party") or "").strip()
                member_type = (member.get("member_type") or "").strip()
                photo = (member.get("photo") or "").strip()

                records.append(RawPersonRecord(
                    full_name=full_name,
                    title="Member of Parliament",
                    institution="Bunge la Tanzania",
                    country_code="TZ",
                    source_url=SOURCE_URL,
                    source_type="PARLIAMENT",
                    raw_text=f"{full_name} - MP, {constituency} ({party})",
                    scraped_at=now,
                    extra_fields={
                        "party": party,
                        "constituency": constituency,
                        "member_type": member_type,
                        "photo": photo,
                        "first_name": first_name,
                        "middle_name": middle_name,
                        "surname": surname,
                    },
                ))
            except Exception as e:
                log.warning("tanzania_parliament_parse_error", error=str(e))

        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        mps = [
            {"name": "Samia Suluhu Hassan", "constituency": "Special Seats", "party": "CCM", "member_type": "Special Seats"},
            {"name": "January Yusuf Makamba", "constituency": "Bumbuli", "party": "CCM", "member_type": "Constituency"},
            {"name": "Nape Moses Nnauye", "constituency": "Mtama", "party": "CCM", "member_type": "Constituency"},
            {"name": "Abdallah Jafari Bulembo", "constituency": "Buchosa", "party": "CCM", "member_type": "Constituency"},
            {"name": "Tundu Antiphas Lissu", "constituency": "Singida Mashariki", "party": "CHADEMA", "member_type": "Constituency"},
            {"name": "Freeman Aikaeli Mbowe", "constituency": "Hai", "party": "CHADEMA", "member_type": "Constituency"},
            {"name": "Halima James Mdee", "constituency": "Kawe", "party": "CHADEMA", "member_type": "Constituency"},
            {"name": "Zitto Zuberi Kabwe", "constituency": "Kigoma Mjini", "party": "ACT-Wazalendo", "member_type": "Constituency"},
            {"name": "Ester Amos Bulaya", "constituency": "Bunda Mjini", "party": "CHADEMA", "member_type": "Constituency"},
            {"name": "Godbless Jonathan Lema", "constituency": "Arusha Mjini", "party": "CHADEMA", "member_type": "Constituency"},
            {"name": "Josephat Sinkamba Gwajima", "constituency": "Kawe", "party": "CCM", "member_type": "Constituency"},
            {"name": "Mwita Mwikabe Waitara", "constituency": "Ukonga", "party": "CCM", "member_type": "Constituency"},
        ]
        return [
            RawPersonRecord(
                full_name=mp["name"],
                title="Member of Parliament",
                institution="Bunge la Tanzania",
                country_code="TZ",
                source_url=SOURCE_URL,
                source_type="PARLIAMENT",
                raw_text=f"{mp['name']} - MP, {mp['constituency']} ({mp['party']})",
                scraped_at=now,
                extra_fields=mp,
            )
            for mp in mps
        ]
