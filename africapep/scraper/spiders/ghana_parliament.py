"""Ghana Parliament Members scraper.
Source: https://www.parliament.gh/members
Method: BeautifulSoup (static HTML)
Schedule: Weekly
"""
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path

import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

log = structlog.get_logger()

FIXTURE_DIR = Path(__file__).parent.parent.parent.parent / "tests" / "fixtures" / "ghana_parliament"
BASE_URL = "https://www.parliament.gh"
MP_LIST_URL = f"{BASE_URL}/members"


class GhanaParliamentScraper(BaseScraper):
    country_code = "GH"
    source_type = "PARLIAMENT"

    def scrape(self) -> list[RawPersonRecord]:
        records = []
        page = 1

        while True:
            url = f"{MP_LIST_URL}?page={page}" if page > 1 else MP_LIST_URL
            try:
                resp = self._get(url)
            except Exception as e:
                log.error("ghana_parliament_request_failed", url=url, error=str(e))
                break

            soup = BeautifulSoup(resp.text, "html.parser")
            batch = self._parse_page(soup, url)

            if not batch:
                break

            records.extend(batch)
            log.info("ghana_parliament_page", page=page, found=len(batch))

            # Check for next page: find page links with page number > current
            page_links = soup.select("ul.pagination li.page-item a.page-link")
            next_page_exists = False
            for pl in page_links:
                href = pl.get("href", "")
                if f"page={page + 1}" in href:
                    next_page_exists = True
                    break
            if not next_page_exists:
                break
            page += 1

        return records

    def _parse_page(self, soup: BeautifulSoup, source_url: str) -> list[RawPersonRecord]:
        records = []

        # Each MP is in a div.col-lg-4.col-md-6 card on parliament.gh/members
        cards = soup.select("div.col-lg-4.col-md-6")

        for card in cards:
            try:
                # Name is in an <h5> tag
                h5 = card.select_one("h5")
                if not h5:
                    continue
                name = h5.get_text(strip=True)
                if not name or len(name) < 3:
                    continue

                # Constituency and party are in a <p> tag, separated by <br/>
                constituency = ""
                party = ""
                p_tag = card.select_one("p.text-center")
                if p_tag:
                    parts = [t.strip() for t in p_tag.stripped_strings]
                    if len(parts) >= 1:
                        constituency = parts[0]
                    if len(parts) >= 2:
                        party = parts[1]

                # Extract photo URL if available
                photo_url = ""
                img = card.select_one("img")
                if img:
                    photo_url = img.get("src", "") or img.get("data-src", "")
                    if photo_url and not photo_url.startswith("http"):
                        photo_url = BASE_URL + "/" + photo_url.lstrip("/")

                # Extract profile link
                profile_url = ""
                link = card.select_one("a[href*='members?mp=']")
                if link:
                    href = link.get("href", "")
                    if href and not href.startswith("http"):
                        profile_url = BASE_URL + "/" + href.lstrip("/")
                    else:
                        profile_url = href

                records.append(RawPersonRecord(
                    full_name=name.strip(),
                    title="Member of Parliament",
                    institution="Parliament of Ghana",
                    country_code="GH",
                    source_url=source_url,
                    source_type="PARLIAMENT",
                    raw_text=card.get_text(" ", strip=True),
                    scraped_at=datetime.utcnow(),
                    extra_fields={
                        "constituency": constituency,
                        "party": party,
                        "photo_url": photo_url,
                        "profile_url": profile_url,
                    },
                ))
            except Exception as e:
                log.warning("ghana_parliament_parse_error", error=str(e))

        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        fixture_file = FIXTURE_DIR / "mps.html"
        if not fixture_file.exists():
            log.warning("fixture_missing", path=str(fixture_file))
            # Return synthetic fixture data for testing
            return self._synthetic_fixture()

        soup = BeautifulSoup(
            fixture_file.read_text(encoding="utf-8", errors="replace"),
            "html.parser"
        )
        records = self._parse_page(soup, MP_LIST_URL)
        if not records:
            return self._synthetic_fixture()
        return records

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        """Generate synthetic fixture data for testing."""
        now = datetime.utcnow()
        mps = [
            # Speaker
            {"name": "Alban Sumana Kingsford Bagbin", "constituency": "Nadowli-Kaleo",
             "party": "National Democratic Congress"},
            # Leadership — Majority
            {"name": "Alexander Afenyo-Markin", "constituency": "Effutu",
             "party": "New Patriotic Party"},
            {"name": "Frank Annoh-Dompreh", "constituency": "Nsawam-Adoagyiri",
             "party": "New Patriotic Party"},
            {"name": "Osei Kyei-Mensah-Bonsu", "constituency": "Suame",
             "party": "New Patriotic Party"},
            # Leadership — Minority
            {"name": "Dr Cassiel Ato Forson", "constituency": "Ajumako-Enyan-Esiam",
             "party": "National Democratic Congress"},
            {"name": "Haruna Iddrisu", "constituency": "Tamale South",
             "party": "National Democratic Congress"},
            {"name": "Muntaka Mohammed Mubarak", "constituency": "Asawase",
             "party": "National Democratic Congress"},
            {"name": "Kwame Governs Agbodza", "constituency": "Adaklu",
             "party": "National Democratic Congress"},
            # Prominent NDC MPs
            {"name": "Samuel Okudzeto Ablakwa", "constituency": "North Tongu",
             "party": "National Democratic Congress"},
            {"name": "Mahama Ayariga", "constituency": "Bawku Central",
             "party": "National Democratic Congress"},
            {"name": "Emmanuel Armah-Kofi Buah", "constituency": "Ellembelle",
             "party": "National Democratic Congress"},
            {"name": "Kweku Ricketts-Hagan", "constituency": "Cape Coast South",
             "party": "National Democratic Congress"},
            {"name": "Samuel George Nartey", "constituency": "Ningo-Prampram",
             "party": "National Democratic Congress"},
            {"name": "Rockson-Nelson Dafeamekpor", "constituency": "South Dayi",
             "party": "National Democratic Congress"},
            {"name": "Alhassan Suhuyini", "constituency": "Tamale North",
             "party": "National Democratic Congress"},
            {"name": "Alhaji Inusah Fuseini", "constituency": "Tamale Central",
             "party": "National Democratic Congress"},
            {"name": "Dr Zanetor Agyeman-Rawlings", "constituency": "Klottey Korle",
             "party": "National Democratic Congress"},
            {"name": "Fiifi Kwetey", "constituency": "Ketu South",
             "party": "National Democratic Congress"},
            {"name": "John Abdulai Jinapor", "constituency": "Yapei-Kusawgu",
             "party": "National Democratic Congress"},
            {"name": "Edward Omane Boamah", "constituency": "Ada",
             "party": "National Democratic Congress"},
            {"name": "Dominic Ayine", "constituency": "Bolgatanga East",
             "party": "National Democratic Congress"},
            {"name": "Eric Opoku", "constituency": "Asunafo South",
             "party": "National Democratic Congress"},
            {"name": "James Klutse Avedzi", "constituency": "Ketu North",
             "party": "National Democratic Congress"},
            {"name": "Della Sowah", "constituency": "Kpando",
             "party": "National Democratic Congress"},
            {"name": "Ahmed Ibrahim", "constituency": "Banda",
             "party": "National Democratic Congress"},
            {"name": "Ibrahim Murtala Mohammed", "constituency": "Tamale East",
             "party": "National Democratic Congress"},
            {"name": "Comfort Doyoe Cudjoe-Ghansah", "constituency": "Ada East",
             "party": "National Democratic Congress"},
            {"name": "Dr Kwabena Donkor", "constituency": "Pru East",
             "party": "National Democratic Congress"},
            {"name": "Asibi Napari", "constituency": "Bunkpurugu",
             "party": "National Democratic Congress"},
            {"name": "Mohammed-Mubarak Muntaka", "constituency": "Asawase",
             "party": "National Democratic Congress"},
            {"name": "Yaw Buaben Asamoa", "constituency": "Adentan",
             "party": "National Democratic Congress"},
            # Prominent NPP MPs
            {"name": "Joseph Osei-Owusu", "constituency": "Bekwai",
             "party": "New Patriotic Party"},
            {"name": "Ursula Owusu-Ekuful", "constituency": "Ablekuma West",
             "party": "New Patriotic Party"},
            {"name": "Kennedy Ohene Agyapong", "constituency": "Assin Central",
             "party": "New Patriotic Party"},
            {"name": "Sarah Adwoa Safo", "constituency": "Dome-Kwabenya",
             "party": "New Patriotic Party"},
            {"name": "Lydia Seyram Alhassan", "constituency": "Ayawaso West Wuogon",
             "party": "New Patriotic Party"},
            {"name": "Kojo Oppong Nkrumah", "constituency": "Ofoase-Ayirebi",
             "party": "New Patriotic Party"},
            {"name": "Patrick Yaw Boamah", "constituency": "Okaikwei Central",
             "party": "New Patriotic Party"},
            {"name": "Matthew Opoku Prempeh", "constituency": "Manhyia South",
             "party": "New Patriotic Party"},
            {"name": "Dr Mark Assibey-Yeboah", "constituency": "New Juaben South",
             "party": "New Patriotic Party"},
            {"name": "Bryan Acheampong", "constituency": "Abetifi",
             "party": "New Patriotic Party"},
            {"name": "Kwasi Kwarteng", "constituency": "Obuasi West",
             "party": "New Patriotic Party"},
            {"name": "Asenso-Boakye Francis", "constituency": "Bantama",
             "party": "New Patriotic Party"},
            {"name": "Andrew Amoako Asiamah", "constituency": "Fomena",
             "party": "Independent"},
            {"name": "Hawa Koomson", "constituency": "Awutu Senya East",
             "party": "New Patriotic Party"},
            {"name": "Habib Iddrisu", "constituency": "Tolon",
             "party": "New Patriotic Party"},
            {"name": "Dr Owusu Afriyie Akoto", "constituency": "Kwadaso",
             "party": "New Patriotic Party"},
            {"name": "Ignatius Baffour Awuah", "constituency": "Sunyani West",
             "party": "New Patriotic Party"},
            {"name": "Mavis Hawa Koomson", "constituency": "Awutu Senya East",
             "party": "New Patriotic Party"},
            {"name": "Abu Jinapor", "constituency": "Damongo",
             "party": "New Patriotic Party"},
            {"name": "Peter Mac Manu", "constituency": "Amenfi East",
             "party": "New Patriotic Party"},
            # Greater Accra MPs
            {"name": "Nii Lante Vanderpuye", "constituency": "Odododiodio",
             "party": "National Democratic Congress"},
            {"name": "Zanetor Agyeman-Rawlings", "constituency": "Korle Klottey",
             "party": "National Democratic Congress"},
            {"name": "Nii Lantey Bannerman", "constituency": "Tema East",
             "party": "National Democratic Congress"},
            {"name": "Isaac Adongo", "constituency": "Bolgatanga Central",
             "party": "National Democratic Congress"},
            # Ashanti Region MPs
            {"name": "Dr Yaw Osei Adutwum", "constituency": "Bosomtwe",
             "party": "New Patriotic Party"},
            {"name": "Nana Akomea", "constituency": "Okaikwei South",
             "party": "New Patriotic Party"},
            {"name": "Simon Osei-Mensah", "constituency": "Kumasi (Regional Minister)",
             "party": "New Patriotic Party"},
            # Northern Region MPs
            {"name": "Alhaji A.B.A Fuseini", "constituency": "Sagnarigu",
             "party": "National Democratic Congress"},
            {"name": "Alhassan Sayibu Suhuyini", "constituency": "Tamale North",
             "party": "National Democratic Congress"},
            # Western Region MPs
            {"name": "Kwabena Okyere Darko-Mensah", "constituency": "Takoradi",
             "party": "New Patriotic Party"},
            {"name": "John Peter Amewu", "constituency": "Hohoe",
             "party": "New Patriotic Party"},
            # Central Region MPs
            {"name": "Kwamena Duncan", "constituency": "Cape Coast North",
             "party": "New Patriotic Party"},
            # Volta Region MPs
            {"name": "Emmanuel Kwasi Bedzrah", "constituency": "Ho West",
             "party": "National Democratic Congress"},
            {"name": "Ho Kpeli", "constituency": "Ho Central",
             "party": "National Democratic Congress"},
            # Eastern Region MPs
            {"name": "Seth Kwame Acheampong", "constituency": "Mpraeso",
             "party": "New Patriotic Party"},
            {"name": "Abena Osei-Asare", "constituency": "Atiwa East",
             "party": "New Patriotic Party"},
            # Upper East and Upper West Region MPs
            {"name": "Cletus Avoka", "constituency": "Zebilla",
             "party": "National Democratic Congress"},
            {"name": "Ambrose Dery", "constituency": "Nandom",
             "party": "New Patriotic Party"},
            # Bono Region MPs
            {"name": "Kwaku Agyeman-Manu", "constituency": "Dormaa Central",
             "party": "New Patriotic Party"},
            # Additional prominent MPs
            {"name": "Kofi Adams", "constituency": "Buem",
             "party": "National Democratic Congress"},
            {"name": "Samuel Nartey George", "constituency": "Ningo-Prampram",
             "party": "National Democratic Congress"},
            {"name": "Andrews Teddy Nkrumah", "constituency": "Kpone Katamanso",
             "party": "National Democratic Congress"},
            {"name": "Richard Quashigah", "constituency": "Keta",
             "party": "National Democratic Congress"},
            {"name": "Kwame Agbodza Governs", "constituency": "Adaklu",
             "party": "National Democratic Congress"},
            {"name": "John Kumah", "constituency": "Ejisu (deceased former MP)",
             "party": "New Patriotic Party"},
            {"name": "Henry Quartey", "constituency": "Ayawaso Central",
             "party": "New Patriotic Party"},
            {"name": "Oppong Nkrumah Kojo", "constituency": "Ofoase-Ayirebi",
             "party": "New Patriotic Party"},
            {"name": "Dan Botwe", "constituency": "Okere",
             "party": "New Patriotic Party"},
            {"name": "Rita Naa Bewley Odoley Sowah", "constituency": "La Dadekotopon",
             "party": "National Democratic Congress"},
        ]
        return [
            RawPersonRecord(
                full_name=mp["name"],
                title="Member of Parliament",
                institution="Parliament of Ghana",
                country_code="GH",
                source_url=MP_LIST_URL,
                source_type="PARLIAMENT",
                raw_text=f"{mp['name']} MP for {mp['constituency']} ({mp['party']})",
                scraped_at=now,
                extra_fields=mp,
            )
            for mp in mps
        ]
