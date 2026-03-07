"""Scraper for the Kenya National Assembly members list.

Source: https://www.parliament.go.ke/the-national-assembly/mps
Method: BeautifulSoup (static HTML with pagination)
Extracts: MP name, county, constituency, party
Schedule: Weekly
"""
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path

import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

log = structlog.get_logger()

BASE_URL = "https://www.parliament.go.ke"
MP_LIST_URL = f"{BASE_URL}/the-national-assembly/mps"
# The site uses Drupal views with field_parliament_value filter
# 2022 = 13th Parliament (current as of 2025/2026)
MP_QUERY_URL = f"{MP_LIST_URL}?field_parliament_value=2022"
FIXTURE_DIR = Path(__file__).parent.parent.parent.parent / "tests" / "fixtures" / "kenya_parliament"


class KenyaParliamentScraper(BaseScraper):
    """Scraper for Kenya National Assembly MPs."""

    country_code = "KE"
    source_type = "PARLIAMENT"

    def scrape(self) -> list[RawPersonRecord]:
        records = []
        page = 0

        while True:
            url = f"{MP_QUERY_URL}&page={page}" if page > 0 else MP_QUERY_URL
            try:
                resp = self._get(url)
            except Exception as e:
                log.error("kenya_parliament_request_failed", url=url, error=str(e))
                break

            soup = BeautifulSoup(resp.text, "html.parser")
            batch = self._parse_page(soup, url)

            if not batch:
                break

            records.extend(batch)
            log.info("kenya_parliament_page", page=page, found=len(batch))

            # Check for next page
            next_link = soup.select_one(".pager__item--next a, .pager .next a")
            if not next_link:
                break
            page += 1

        return records

    def _parse_page(self, soup: BeautifulSoup, source_url: str) -> list[RawPersonRecord]:
        records = []
        now = datetime.utcnow()

        # The Kenya Parliament site uses Drupal views with these CSS classes:
        # .views-field-field-name for MP name
        # .views-field-field-county for county
        # .views-field-field-constituency for constituency
        # .views-field-field-party for party

        name_fields = soup.select(".views-field-field-name")
        county_fields = soup.select(".views-field-field-county")
        constituency_fields = soup.select(".views-field-field-constituency")
        party_fields = soup.select(".views-field-field-party")

        # The first element is usually the header label, skip it
        # Align all lists by length
        max_len = max(len(name_fields), 1)
        skip_header = 1 if max_len > 1 else 0

        for i in range(skip_header, len(name_fields)):
            try:
                name = name_fields[i].get_text(strip=True) if i < len(name_fields) else ""
                county = county_fields[i].get_text(strip=True) if i < len(county_fields) else ""
                constituency = constituency_fields[i].get_text(strip=True) if i < len(constituency_fields) else ""
                party = party_fields[i].get_text(strip=True) if i < len(party_fields) else ""

                # Clean up name (remove "HON." prefix etc.)
                if not name or name == "Member of Parliament" or len(name) < 3:
                    continue

                # Remove common prefixes
                clean_name = name
                for prefix in ["HON.", "HON ", "Hon.", "Hon "]:
                    if clean_name.upper().startswith(prefix.upper()):
                        clean_name = clean_name[len(prefix):].strip()

                # Remove trailing qualifications like ", CBS" ", EGH"
                # but keep the name intact
                if not clean_name:
                    continue

                records.append(RawPersonRecord(
                    full_name=clean_name.strip(),
                    title="Member of Parliament",
                    institution="National Assembly of Kenya",
                    country_code="KE",
                    source_url=source_url,
                    source_type="PARLIAMENT",
                    raw_text=f"{name} - MP, {constituency}, {county} ({party})",
                    scraped_at=now,
                    extra_fields={
                        "county": county,
                        "constituency": constituency,
                        "party": party,
                        "raw_name": name,
                    },
                ))
            except Exception as e:
                log.warning("kenya_parliament_parse_error", error=str(e))

        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        fixture_file = FIXTURE_DIR / "mps.html"
        if fixture_file.exists():
            log.info("fixture_loading", path=str(fixture_file))
            soup = BeautifulSoup(
                fixture_file.read_text(encoding="utf-8", errors="replace"),
                "html.parser"
            )
            records = self._parse_page(soup, MP_LIST_URL)
            if records:
                return records

        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        mps = [
            {"name": "Moses Wetang'ula", "county": "Bungoma", "constituency": "Bungoma County", "party": "Ford Kenya"},
            {"name": "Kimani Ichung'wah", "county": "Kiambu", "constituency": "Kikuyu", "party": "UDA"},
            {"name": "Junet Mohamed", "county": "Migori", "constituency": "Suna East", "party": "ODM"},
            {"name": "Didmus Barasa", "county": "Bungoma", "constituency": "Kimilili", "party": "UDA"},
            {"name": "Sabina Chege", "county": "Murang'a", "constituency": "Nominated", "party": "Jubilee"},
            {"name": "Babu Owino", "county": "Nairobi", "constituency": "Embakasi East", "party": "ODM"},
            {"name": "Millie Odhiambo", "county": "Homa Bay", "constituency": "Suba North", "party": "ODM"},
            {"name": "Ndindi Nyoro", "county": "Murang'a", "constituency": "Kiharu", "party": "UDA"},
            {"name": "Caleb Amisi", "county": "Kakamega", "constituency": "Saboti", "party": "ODM"},
            {"name": "Timothy Wanyonyi", "county": "Nairobi", "constituency": "Westlands", "party": "ODM"},
            {"name": "Robert Mbui", "county": "Machakos", "constituency": "Kathiani", "party": "Wiper"},
            {"name": "TJ Kajwang", "county": "Homa Bay", "constituency": "Ruaraka", "party": "ODM"},
            {"name": "Otiende Amollo", "county": "Siaya", "constituency": "Rarieda", "party": "ODM"},
            {"name": "Amos Kimunya", "county": "Kipipiri", "constituency": "Kipipiri", "party": "Jubilee"},
            {"name": "Oscar Sudi", "county": "Uasin Gishu", "constituency": "Kapseret", "party": "UDA"},
            {"name": "Sylvanus Osoro", "county": "Kisii", "constituency": "South Mugirango", "party": "UDA"},
            {"name": "Gathoni Wamuchomba", "county": "Kiambu", "constituency": "Githunguri", "party": "UDA"},
            {"name": "Mwengi Mutuse", "county": "Makueni", "constituency": "Kibwezi West", "party": "Wiper"},
            {"name": "Patrick Makau", "county": "Machakos", "constituency": "Mavoko", "party": "Wiper"},
            {"name": "Emmanuel Wangwe", "county": "Kakamega", "constituency": "Navakholo", "party": "ODM"},
            {"name": "Johana Ng'eno", "county": "Bomet", "constituency": "Emurua Dikirr", "party": "UDA"},
            {"name": "Martha Wangari", "county": "Nyandarua", "constituency": "Gilgil", "party": "UDA"},
            {"name": "Benjamin Washiali", "county": "Kakamega", "constituency": "Mumias East", "party": "ANC"},
            {"name": "George Theuri", "county": "Kiambu", "constituency": "Embakasi West", "party": "UDA"},
            {"name": "Irene Njoki", "county": "Nairobi", "constituency": "Nominated", "party": "UDA"},
            {"name": "Dan Maanzo", "county": "Machakos", "constituency": "Makueni", "party": "Wiper"},
            {"name": "Hassan Omar", "county": "Mombasa", "constituency": "Mombasa County", "party": "Wiper"},
            {"name": "Beatrice Elachi", "county": "Nairobi", "constituency": "Dagoretti North", "party": "ODM"},
            {"name": "Mark Nyamita", "county": "Siaya", "constituency": "Uriri", "party": "ODM"},
            {"name": "Faith Gitau", "county": "Nyandarua", "constituency": "Nyandarua County", "party": "UDA"},
        ]
        return [
            RawPersonRecord(
                full_name=mp["name"],
                title="Member of Parliament",
                institution="National Assembly of Kenya",
                country_code="KE",
                source_url=MP_LIST_URL,
                source_type="PARLIAMENT",
                raw_text=f"{mp['name']} - MP, {mp['constituency']}, {mp['county']} ({mp['party']})",
                scraped_at=now,
                extra_fields=mp,
            )
            for mp in mps
        ]
