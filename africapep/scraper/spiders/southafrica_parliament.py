"""
Scraper for the South Africa Parliament members list.

Source: https://www.parliament.gov.za/members-of-parliament
Method: JSON API (POST /group-details-filter)
Extracts: MP name, party, province, chamber (National Assembly / NCOP)
"""

import requests
from datetime import datetime
from pathlib import Path

import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)


class SouthAfricaParliamentScraper(BaseScraper):
    """Scraper for South Africa National Assembly and NCOP MPs."""

    country_code = "ZA"
    source_type = "PARLIAMENT"

    SOURCE_URL = "https://www.parliament.gov.za/members-of-parliament"
    API_URL = "https://www.parliament.gov.za/group-details-filter"
    FIXTURE_PATH = Path(__file__).parent / "fixtures" / "southafrica_parliament.html"

    def scrape(self) -> list[RawPersonRecord]:
        """Scrape the South Africa Parliament via the internal JSON API.

        The parliament website uses an AngularJS frontend that loads member
        data from a POST endpoint at /group-details-filter. We call that
        API directly, which returns all members as JSON.

        Returns:
            List of RawPersonRecord objects containing MP data.
        """
        logger.info(
            "scraper.southafrica_parliament.start",
            url=self.SOURCE_URL,
            country_code=self.country_code,
        )

        try:
            data = self._fetch_api()
        except Exception as exc:
            logger.error(
                "scraper.southafrica_parliament.fetch_failed",
                url=self.API_URL,
                error=str(exc),
            )
            raise

        return self._parse_api_response(data)

    def _fetch_api(self) -> dict:
        """Fetch member data from the parliament JSON API.

        Returns:
            Parsed JSON response dict with 'members' and 'member_count'.
        """
        resp = requests.post(
            self.API_URL,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": self.SOURCE_URL,
            },
            json={
                "committee": "",
                "ministry": "",
                "party": "",
                "chamber": "",
                "national": "",
                "province": "",
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        if not data.get("success"):
            raise RuntimeError(
                f"Parliament API returned success=false: {data}"
            )

        return data

    def _parse_api_response(self, data: dict) -> list[RawPersonRecord]:
        """Parse the JSON API response into RawPersonRecord objects.

        The API returns members grouped alphabetically (a-d, e-g, etc.).
        Each member dict has: id, full_name, profile_pic_url, party,
        province, national (1 = National Assembly, 0 = NCOP).

        Args:
            data: Parsed JSON response from the API.

        Returns:
            List of RawPersonRecord objects.
        """
        records: list[RawPersonRecord] = []
        now = datetime.utcnow().isoformat()

        members_groups = data.get("members", {})
        for _group_key, members in members_groups.items():
            for member in members:
                name = member.get("full_name", "").strip()
                if not name:
                    continue

                party = member.get("party", "")
                province = member.get("province", "")
                is_national = member.get("national", 0)
                chamber = (
                    "National Assembly" if is_national
                    else "National Council of Provinces"
                )
                member_id = member.get("id", "")
                profile_pic = member.get("profile_pic_url", "")

                records.append(
                    RawPersonRecord(
                        full_name=name,
                        title="Member of Parliament",
                        institution="Parliament of South Africa",
                        country_code=self.country_code,
                        source_type=self.source_type,
                        source_url=self.SOURCE_URL,
                        raw_text=f"{name} – {chamber}, {party}",
                        scraped_at=now,
                        extra_fields={
                            "party": party,
                            "province": province,
                            "chamber": chamber,
                            "member_id": member_id,
                            "profile_pic_url": profile_pic,
                        },
                    )
                )

        logger.info(
            "scraper.southafrica_parliament.complete",
            record_count=len(records),
            reported_count=data.get("member_count"),
        )
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        """Load synthetic fixture data for testing and development.

        Returns:
            List of RawPersonRecord objects from fixture data.
        """
        logger.info("scraper.southafrica_parliament.using_synthetic_fixture")
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        """Generate synthetic fixture data with real South African MP names.

        Returns:
            List of RawPersonRecord objects with realistic data.
        """
        now = datetime.utcnow().isoformat()

        mps = [
            {
                "name": "Cyril Ramaphosa",
                "party": "African National Congress",
                "province": "Gauteng",
                "committee": "Joint Standing Committee on Defence",
            },
            {
                "name": "John Steenhuisen",
                "party": "Democratic Alliance",
                "province": "KwaZulu-Natal",
                "committee": "Portfolio Committee on Agriculture",
            },
            {
                "name": "Julius Malema",
                "party": "Economic Freedom Fighters",
                "province": "Limpopo",
                "committee": "",
            },
            {
                "name": "Mmusi Maimane",
                "party": "Build One South Africa",
                "province": "Gauteng",
                "committee": "",
            },
            {
                "name": "Naledi Pandor",
                "party": "African National Congress",
                "province": "Gauteng",
                "committee": "Portfolio Committee on International Relations",
            },
            {
                "name": "Angie Motshekga",
                "party": "African National Congress",
                "province": "Gauteng",
                "committee": "Portfolio Committee on Basic Education",
            },
            {
                "name": "Pieter Groenewald",
                "party": "Freedom Front Plus",
                "province": "North West",
                "committee": "Portfolio Committee on Police",
            },
            {
                "name": "Bantu Holomisa",
                "party": "United Democratic Movement",
                "province": "Eastern Cape",
                "committee": "Portfolio Committee on Defence and Military Veterans",
            },
            {
                "name": "Mangosuthu Buthelezi",
                "party": "Inkatha Freedom Party",
                "province": "KwaZulu-Natal",
                "committee": "",
            },
            {
                "name": "Nkosazana Dlamini-Zuma",
                "party": "African National Congress",
                "province": "KwaZulu-Natal",
                "committee": "Portfolio Committee on Cooperative Governance",
            },
            {
                "name": "Gwede Mantashe",
                "party": "African National Congress",
                "province": "Eastern Cape",
                "committee": "Portfolio Committee on Mineral Resources and Energy",
            },
            {
                "name": "Lindiwe Sisulu",
                "party": "African National Congress",
                "province": "Gauteng",
                "committee": "Portfolio Committee on Human Settlements",
            },
        ]

        records = []
        for mp in mps:
            records.append(
                RawPersonRecord(
                    full_name=mp["name"],
                    title="Member of Parliament",
                    institution="Parliament of South Africa",
                    country_code=self.country_code,
                    source_type=self.source_type,
                    source_url=self.SOURCE_URL,
                    raw_text=f"{mp['name']} – Member of Parliament, {mp['party']}",
                    scraped_at=now,
                    extra_fields={
                        "party": mp["party"],
                        "province": mp["province"],
                        "portfolio_committee": mp["committee"],
                    },
                )
            )

        logger.info(
            "scraper.southafrica_parliament.synthetic_fixture_loaded",
            record_count=len(records),
        )
        return records
