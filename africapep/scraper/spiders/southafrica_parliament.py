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
            # ── Parliamentary Leadership ──
            {"name": "Thoko Didiza", "party": "African National Congress", "province": "Gauteng", "committee": "Speaker of the National Assembly"},
            {"name": "Refilwe Mtsweni-Tsipane", "party": "African National Congress", "province": "Mpumalanga", "committee": "Chairperson of the NCOP"},
            {"name": "Lechesa Tsenoli", "party": "African National Congress", "province": "Free State", "committee": "Deputy Speaker of the National Assembly"},
            {"name": "Sylvia Lucas", "party": "African National Congress", "province": "Northern Cape", "committee": "Deputy Chairperson of the NCOP"},
            # ── Chief Whips ──
            {"name": "Mdumiseni Ntuli", "party": "African National Congress", "province": "KwaZulu-Natal", "committee": "Chief Whip of the Majority Party"},
            {"name": "Siviwe Gwarube", "party": "Democratic Alliance", "province": "Western Cape", "committee": "Chief Whip of the Opposition (former)"},
            {"name": "Natasha Mazzone", "party": "Democratic Alliance", "province": "Gauteng", "committee": "DA Chief Whip"},
            {"name": "Veronica Mente", "party": "Economic Freedom Fighters", "province": "Northern Cape", "committee": "EFF Chief Whip"},
            # ── Party Leaders in Parliament ──
            {"name": "Cyril Ramaphosa", "party": "African National Congress", "province": "Gauteng", "committee": "Leader, ANC"},
            {"name": "John Steenhuisen", "party": "Democratic Alliance", "province": "KwaZulu-Natal", "committee": "Leader, DA"},
            {"name": "Julius Malema", "party": "Economic Freedom Fighters", "province": "Limpopo", "committee": "Commander in Chief, EFF"},
            {"name": "Jacob Zuma", "party": "uMkhonto weSizwe", "province": "KwaZulu-Natal", "committee": "Leader, MK Party"},
            {"name": "Floyd Shivambu", "party": "uMkhonto weSizwe", "province": "Limpopo", "committee": "Secretary General, MK Party"},
            {"name": "Velenkosini Hlabisa", "party": "Inkatha Freedom Party", "province": "KwaZulu-Natal", "committee": "Leader, IFP"},
            {"name": "Mangosuthu Buthelezi", "party": "Inkatha Freedom Party", "province": "KwaZulu-Natal", "committee": "Founder and President Emeritus, IFP (deceased 2023)"},
            {"name": "Pieter Groenewald", "party": "Freedom Front Plus", "province": "North West", "committee": "Leader, FF+"},
            {"name": "Herman Mashaba", "party": "ActionSA", "province": "Gauteng", "committee": "Leader, ActionSA"},
            {"name": "Gayton McKenzie", "party": "Patriotic Alliance", "province": "Northern Cape", "committee": "Leader, PA"},
            {"name": "Bantu Holomisa", "party": "United Democratic Movement", "province": "Eastern Cape", "committee": "Leader, UDM"},
            {"name": "Mmusi Maimane", "party": "Build One South Africa", "province": "Gauteng", "committee": "Leader, BOSA"},
            # ── Portfolio Committee Chairs ──
            {"name": "Naledi Pandor", "party": "African National Congress", "province": "Gauteng", "committee": "Portfolio Committee on International Relations"},
            {"name": "Gwede Mantashe", "party": "African National Congress", "province": "Eastern Cape", "committee": "Portfolio Committee on Mineral Resources"},
            {"name": "Hlengiwe Mkhize", "party": "African National Congress", "province": "Gauteng", "committee": "Portfolio Committee on Justice and Correctional Services"},
            {"name": "Supra Mahumapelo", "party": "African National Congress", "province": "North West", "committee": "Portfolio Committee on Energy"},
            {"name": "Cedric Frolick", "party": "African National Congress", "province": "Eastern Cape", "committee": "Portfolio Committee on Public Enterprises"},
            {"name": "Mosebenzi Zwane", "party": "African National Congress", "province": "Free State", "committee": "Portfolio Committee on Agriculture (former)"},
            {"name": "Tina Joemat-Pettersson", "party": "African National Congress", "province": "Northern Cape", "committee": "Portfolio Committee on Transport"},
            {"name": "Bheki Cele", "party": "African National Congress", "province": "KwaZulu-Natal", "committee": "Portfolio Committee on Police (former)"},
            {"name": "Peace Mabe", "party": "African National Congress", "province": "Limpopo", "committee": "Portfolio Committee on Water and Sanitation"},
            # ── Prominent ANC MPs ──
            {"name": "Fikile Mbalula", "party": "African National Congress", "province": "Free State", "committee": "ANC Secretary General"},
            {"name": "Pemmy Majodina", "party": "African National Congress", "province": "Eastern Cape", "committee": ""},
            {"name": "Nkosazana Dlamini-Zuma", "party": "African National Congress", "province": "KwaZulu-Natal", "committee": ""},
            {"name": "Angie Motshekga", "party": "African National Congress", "province": "Gauteng", "committee": ""},
            {"name": "Lindiwe Sisulu", "party": "African National Congress", "province": "Gauteng", "committee": ""},
            {"name": "Zizi Kodwa", "party": "African National Congress", "province": "Gauteng", "committee": ""},
            {"name": "David Mabuza", "party": "African National Congress", "province": "Mpumalanga", "committee": ""},
            {"name": "Pravin Gordhan", "party": "African National Congress", "province": "KwaZulu-Natal", "committee": ""},
            {"name": "Jeff Radebe", "party": "African National Congress", "province": "Gauteng", "committee": ""},
            {"name": "Nosiviwe Mapisa-Nqakula", "party": "African National Congress", "province": "Gauteng", "committee": ""},
            # ── Prominent DA MPs ──
            {"name": "Leon Schreiber", "party": "Democratic Alliance", "province": "Western Cape", "committee": "Portfolio Committee on Home Affairs"},
            {"name": "Dean Macpherson", "party": "Democratic Alliance", "province": "KwaZulu-Natal", "committee": ""},
            {"name": "Solly Malatsi", "party": "Democratic Alliance", "province": "Gauteng", "committee": ""},
            {"name": "Glynnis Breytenbach", "party": "Democratic Alliance", "province": "Gauteng", "committee": "Portfolio Committee on Justice"},
            {"name": "Helen Zille", "party": "Democratic Alliance", "province": "Western Cape", "committee": "DA Federal Council Chair"},
            {"name": "Geordin Hill-Lewis", "party": "Democratic Alliance", "province": "Western Cape", "committee": ""},
            # ── Prominent EFF MPs ──
            {"name": "Mbuyiseni Ndlozi", "party": "Economic Freedom Fighters", "province": "Gauteng", "committee": ""},
            {"name": "Omphile Maotwe", "party": "Economic Freedom Fighters", "province": "Limpopo", "committee": "EFF Shadow Minister of Finance"},
            {"name": "Naledi Chirwa", "party": "Economic Freedom Fighters", "province": "Gauteng", "committee": ""},
            # ── Prominent MK Party MPs ──
            {"name": "John Hlophe", "party": "uMkhonto weSizwe", "province": "Western Cape", "committee": ""},
            {"name": "Nhlanhla Lux Dlamini", "party": "uMkhonto weSizwe", "province": "Gauteng", "committee": ""},
            # ── Other Party MPs ──
            {"name": "Narend Singh", "party": "Inkatha Freedom Party", "province": "KwaZulu-Natal", "committee": ""},
            {"name": "Sithembile Dlomo", "party": "African National Congress", "province": "KwaZulu-Natal", "committee": ""},
            # ── Provincial Premiers ──
            {"name": "Panyaza Lesufi", "party": "African National Congress", "province": "Gauteng", "committee": "Premier of Gauteng"},
            {"name": "Alan Winde", "party": "Democratic Alliance", "province": "Western Cape", "committee": "Premier of the Western Cape"},
            {"name": "Nomusa Dube-Ncube", "party": "African National Congress", "province": "KwaZulu-Natal", "committee": "Premier of KwaZulu-Natal"},
            {"name": "Zamani Saul", "party": "African National Congress", "province": "Northern Cape", "committee": "Premier of the Northern Cape"},
            {"name": "Oscar Mabuyane", "party": "African National Congress", "province": "Eastern Cape", "committee": "Premier of the Eastern Cape"},
            {"name": "Maqueen Letsoha-Mathae", "party": "African National Congress", "province": "Free State", "committee": "Premier of the Free State"},
            {"name": "Chupu Mathabatha", "party": "African National Congress", "province": "Limpopo", "committee": "Premier of Limpopo"},
            {"name": "Refilwe Mtsweni-Tsipane", "party": "African National Congress", "province": "Mpumalanga", "committee": "Premier of Mpumalanga (former)"},
            {"name": "Bushy Maape", "party": "African National Congress", "province": "North West", "committee": "Premier of North West"},
            # ── Metro Mayors ──
            {"name": "Dada Morero", "party": "African National Congress", "province": "Gauteng", "committee": "Mayor of Johannesburg"},
            {"name": "Geordin Hill-Lewis", "party": "Democratic Alliance", "province": "Western Cape", "committee": "Mayor of Cape Town"},
            {"name": "Mxolisi Kaunda", "party": "African National Congress", "province": "KwaZulu-Natal", "committee": "Mayor of eThekwini (Durban)"},
            {"name": "Cilliers Brink", "party": "Democratic Alliance", "province": "Gauteng", "committee": "Mayor of Tshwane (Pretoria) (former)"},
            {"name": "Eugene Johnson", "party": "African National Congress", "province": "Eastern Cape", "committee": "Mayor of Nelson Mandela Bay"},
            {"name": "Xola Pakati", "party": "African National Congress", "province": "Eastern Cape", "committee": "Mayor of Buffalo City"},
            {"name": "Gcinikhaya Mpumza", "party": "African National Congress", "province": "Gauteng", "committee": "Mayor of Ekurhuleni"},
            {"name": "Olly Mlamleli", "party": "African National Congress", "province": "Free State", "committee": "Mayor of Mangaung"},
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
