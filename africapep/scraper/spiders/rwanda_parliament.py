"""Rwanda Chamber of Deputies scraper.
Source: https://www.parliament.gov.rw/chamber-of-deputies-2/member-profile/deputies-profiles
Method: BeautifulSoup (static HTML with pagination)
Schedule: Weekly
"""
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path

import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

log = structlog.get_logger()

BASE_URL = "https://www.parliament.gov.rw"
DEPUTIES_URL = f"{BASE_URL}/chamber-of-deputies-2/member-profile/deputies-profiles"
SENATORS_URL = f"{BASE_URL}/the-senate-2/member-profile/senators-profiles"
FIXTURE_DIR = Path(__file__).parent.parent.parent.parent / "tests" / "fixtures" / "rwanda_parliament"


class RwandaParliamentScraper(BaseScraper):
    """Scraper for Rwanda Parliament (Chamber of Deputies + Senate)."""

    country_code = "RW"
    source_type = "PARLIAMENT"

    def scrape(self) -> list[RawPersonRecord]:
        records = []

        # Scrape Chamber of Deputies
        records.extend(self._scrape_chamber(DEPUTIES_URL, "Chamber of Deputies"))

        # Scrape Senate
        records.extend(self._scrape_chamber(SENATORS_URL, "Senate"))

        return records

    def _scrape_chamber(self, base_url: str, chamber: str) -> list[RawPersonRecord]:
        records = []
        page = 1

        while True:
            url = f"{base_url}/page/{page}/" if page > 1 else base_url
            try:
                resp = self._get(url)
            except Exception as e:
                log.error("rwanda_parliament_request_failed", url=url, error=str(e))
                break

            soup = BeautifulSoup(resp.text, "html.parser")
            batch = self._parse_page(soup, url, chamber)

            if not batch:
                break

            records.extend(batch)
            log.info("rwanda_parliament_page", chamber=chamber, page=page, found=len(batch))

            # Check pagination
            next_link = soup.select_one(".next.page-numbers, a.next")
            if not next_link:
                break
            page += 1

        return records

    def _parse_page(self, soup: BeautifulSoup, source_url: str,
                    chamber: str) -> list[RawPersonRecord]:
        records = []
        now = datetime.utcnow()

        # Rwanda parliament uses h3 tags for deputy/senator names
        h3_elements = soup.select("h3")

        for h3 in h3_elements:
            name = h3.get_text(strip=True)
            if not name or len(name) < 4:
                continue

            # Skip non-name h3s (navigation, headers)
            if any(skip in name.lower() for skip in [
                "menu", "search", "home", "about", "committee",
                "legislation", "news", "contact", "parliament",
            ]):
                continue

            # Clean up name: remove "Hon." prefix, fix tabs
            clean_name = name.replace("\t", " ").strip()
            for prefix in ["Hon.", "Hon ", "Rt. Hon.", "H.E."]:
                if clean_name.startswith(prefix):
                    clean_name = clean_name[len(prefix):].strip()

            if not clean_name or len(clean_name) < 3:
                continue

            # Determine title based on chamber
            title = "Deputy" if chamber == "Chamber of Deputies" else "Senator"

            # Try to get additional info from parent/sibling elements
            party = ""
            parent = h3.parent
            if parent:
                parent_text = parent.get_text(" ", strip=True)
                # Look for party info in surrounding text
                for p_name in ["RPF", "PSD", "PL", "DGPR", "PSR"]:
                    if p_name in parent_text:
                        party = p_name
                        break

            records.append(RawPersonRecord(
                full_name=clean_name,
                title=title,
                institution=f"{chamber} of Rwanda",
                country_code="RW",
                source_url=source_url,
                source_type="PARLIAMENT",
                raw_text=f"{name} - {title}, {chamber} of Rwanda",
                scraped_at=now,
                extra_fields={
                    "chamber": chamber,
                    "party": party,
                    "raw_name": name,
                },
            ))

        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        fixture_file = FIXTURE_DIR / "deputies.html"
        if fixture_file.exists():
            soup = BeautifulSoup(
                fixture_file.read_text(encoding="utf-8", errors="replace"),
                "html.parser"
            )
            records = self._parse_page(soup, DEPUTIES_URL, "Chamber of Deputies")
            if records:
                return records
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        members = [
            # ── Executive: President & Prime Ministers ──
            {"name": "Paul Kagame", "title": "President of the Republic of Rwanda", "chamber": "Executive", "party": "RPF"},
            {"name": "Edouard Ngirente", "title": "Prime Minister", "chamber": "Executive", "party": "RPF"},
            # Former Prime Ministers
            {"name": "Anastase Murekezi", "title": "Former Prime Minister", "chamber": "Executive", "party": "RPF"},
            {"name": "Pierre Damien Habumuremyi", "title": "Former Prime Minister", "chamber": "Executive", "party": "RPF"},
            {"name": "Bernard Makuza", "title": "Former Prime Minister", "chamber": "Executive", "party": "RPF"},
            {"name": "Faustin Twagiramungu", "title": "Former Prime Minister", "chamber": "Executive", "party": "MDR"},
            # Former President
            {"name": "Pasteur Bizimungu", "title": "Former President of Rwanda", "chamber": "Executive", "party": ""},
            # ── Full Cabinet ──
            {"name": "Vincent Biruta", "title": "Minister of Foreign Affairs and International Cooperation", "chamber": "Executive", "party": "RPF"},
            {"name": "Albert Murasira", "title": "Minister of Defence", "chamber": "Executive", "party": "RPF"},
            {"name": "Jean Claude Musabyimana", "title": "Minister of Internal Security", "chamber": "Executive", "party": "RPF"},
            {"name": "Uzziel Ndagijimana", "title": "Minister of Finance and Economic Planning", "chamber": "Executive", "party": "RPF"},
            {"name": "Valentine Uwamariya", "title": "Minister of Education", "chamber": "Executive", "party": "RPF"},
            {"name": "Daniel Ngamije", "title": "Minister of Health", "chamber": "Executive", "party": "RPF"},
            {"name": "Ildephonse Musafiri", "title": "Minister of Agriculture and Animal Resources", "chamber": "Executive", "party": "RPF"},
            {"name": "Jean Chrysostome Ngabitsinze", "title": "Minister of Infrastructure", "chamber": "Executive", "party": "RPF"},
            {"name": "Francis Gatare", "title": "Minister of State for Mining", "chamber": "Executive", "party": "RPF"},
            {"name": "Paula Ingabire", "title": "Minister of ICT and Innovation", "chamber": "Executive", "party": "RPF"},
            {"name": "Ernest Nsabimana", "title": "Minister of Trade and Industry", "chamber": "Executive", "party": "RPF"},
            {"name": "Jeanne d'Arc Mujawamariya", "title": "Minister of Environment", "chamber": "Executive", "party": "RPF"},
            {"name": "Jean de Dieu Uwihanganye", "title": "Minister of Justice and Attorney General", "chamber": "Executive", "party": "RPF"},
            {"name": "Edouard Ngirente", "title": "Minister of Local Government", "chamber": "Executive", "party": "RPF"},
            {"name": "Germaine Kamayirese", "title": "Minister of Sports", "chamber": "Executive", "party": "RPF"},
            {"name": "Solange Kayisire", "title": "Minister of Gender and Family Promotion", "chamber": "Executive", "party": "RPF"},
            {"name": "Fanfan Rwanyindo Kayirangwa", "title": "Minister of Public Service and Labour", "chamber": "Executive", "party": "RPF"},
            {"name": "Olivier Nduhungirehe", "title": "Minister of State for East African Community", "chamber": "Executive", "party": "RPF"},
            {"name": "Claudette Irere", "title": "Minister of State for Transport", "chamber": "Executive", "party": "RPF"},
            {"name": "Gaspard Twagirayezu", "title": "Minister of State for Primary and Secondary Education", "chamber": "Executive", "party": "RPF"},
            {"name": "Aime Bosenibamwe", "title": "Minister of State for National Treasury", "chamber": "Executive", "party": "RPF"},
            {"name": "Teddy Mugabo", "title": "Minister of State for Constitution and Legal Affairs", "chamber": "Executive", "party": "RPF"},
            {"name": "Jean Nepo Abdallah Hashim", "title": "Minister of Youth and Culture", "chamber": "Executive", "party": "RPF"},
            # ── Judiciary ──
            {"name": "Faustin Ntezilyayo", "title": "Chief Justice of Rwanda", "chamber": "Judiciary", "party": ""},
            {"name": "Alphonse Hitiyaremye", "title": "Deputy Chief Justice of Rwanda", "chamber": "Judiciary", "party": ""},
            {"name": "Sam Rugege", "title": "Former Chief Justice of Rwanda", "chamber": "Judiciary", "party": ""},
            # ── Central Bank ──
            {"name": "John Rwangombwa", "title": "Governor, National Bank of Rwanda", "chamber": "Executive", "party": ""},
            # ── Military & Security ──
            {"name": "Jean Bosco Kazura", "title": "Chief of Defence Staff, Rwanda Defence Force", "chamber": "Security", "party": ""},
            {"name": "Jacques Musemakweli", "title": "Former Chief of Defence Staff, Rwanda Defence Force", "chamber": "Security", "party": ""},
            {"name": "Joseph Nzabamwita", "title": "Director General, National Intelligence and Security Services (NISS)", "chamber": "Security", "party": ""},
            {"name": "Dan Munyuza", "title": "Inspector General, Rwanda National Police", "chamber": "Security", "party": ""},
            {"name": "Jeannot Ruhunga", "title": "Secretary General, Rwanda Investigation Bureau (RIB)", "chamber": "Security", "party": ""},
            # ── Key Agencies ──
            {"name": "Pascal Bizimana Ruganintwali", "title": "Commissioner General, Rwanda Revenue Authority", "chamber": "Executive", "party": ""},
            {"name": "Clare Akamanzi", "title": "CEO, Rwanda Development Board (RDB)", "chamber": "Executive", "party": ""},
            {"name": "Patrick Nyirishema", "title": "Director General, Rwanda Utilities Regulatory Authority (RURA)", "chamber": "Executive", "party": ""},
            {"name": "Usta Kaitesi", "title": "Chairperson, Rwanda Governance Board (RGB)", "chamber": "Executive", "party": ""},
            {"name": "Juliet Kabera", "title": "Director General, Rwanda Environment Management Authority (REMA)", "chamber": "Executive", "party": ""},
            {"name": "Felix Gakuba", "title": "CEO, Rwanda Energy Group (REG)", "chamber": "Executive", "party": ""},
            # ── Parliament: Chamber of Deputies ──
            {"name": "Donatille Mukabalisa", "title": "Speaker of the Chamber of Deputies", "chamber": "Chamber of Deputies", "party": "RPF"},
            {"name": "Edouard Bamporiki", "title": "Deputy Speaker of the Chamber of Deputies", "chamber": "Chamber of Deputies", "party": "RPF"},
            {"name": "Speciose Ayinkamiye", "title": "Deputy", "chamber": "Chamber of Deputies", "party": "PSD"},
            {"name": "Christine Bakundufite", "title": "Deputy", "chamber": "Chamber of Deputies", "party": "RPF"},
            {"name": "Diogene Bitunguramye", "title": "Deputy", "chamber": "Chamber of Deputies", "party": "RPF"},
            {"name": "Deogratias Bizimana Minani", "title": "Deputy", "chamber": "Chamber of Deputies", "party": "PL"},
            {"name": "Donatha Gihana", "title": "Deputy", "chamber": "Chamber of Deputies", "party": "RPF"},
            {"name": "Mussa Fazil Harerimana", "title": "Deputy", "chamber": "Chamber of Deputies", "party": "PSD"},
            {"name": "Jean Pierre Dusingizemungu", "title": "Deputy", "chamber": "Chamber of Deputies", "party": "PSD"},
            {"name": "Marie Claire Mukasine", "title": "Deputy", "chamber": "Chamber of Deputies", "party": "RPF"},
            {"name": "Juvenal Nkusi", "title": "Deputy", "chamber": "Chamber of Deputies", "party": "RPF"},
            {"name": "Jean Damascene Ntawukuliryayo", "title": "Deputy", "chamber": "Chamber of Deputies", "party": "PSD"},
            {"name": "Agnes Mukazibera", "title": "Deputy", "chamber": "Chamber of Deputies", "party": "RPF"},
            {"name": "Theobald Mbonankira", "title": "Deputy", "chamber": "Chamber of Deputies", "party": "PL"},
            {"name": "Emmanuel Mudidi", "title": "Deputy", "chamber": "Chamber of Deputies", "party": "RPF"},
            {"name": "Dancille Nyirarukundo", "title": "Deputy", "chamber": "Chamber of Deputies", "party": "RPF"},
            # ── Parliament: Senate ──
            {"name": "Augustin Iyamuremye", "title": "President of the Senate", "chamber": "Senate", "party": "PSD"},
            {"name": "Espérance Nyirasafari", "title": "Vice President of the Senate", "chamber": "Senate", "party": "RPF"},
            {"name": "Francois Xavier Kalinda", "title": "Senator", "chamber": "Senate", "party": "RPF"},
            {"name": "Tito Rutaremara", "title": "Senator / Ombudsman Emeritus", "chamber": "Senate", "party": "RPF"},
            {"name": "Alvera Mukabaramba", "title": "Senator", "chamber": "Senate", "party": "PPC"},
            {"name": "Jean Pierre Gatera", "title": "Senator", "chamber": "Senate", "party": "RPF"},
            {"name": "Marie Immaculée Ingabire", "title": "Senator", "chamber": "Senate", "party": "RPF"},
            {"name": "Odette Uwamariya", "title": "Senator", "chamber": "Senate", "party": "PL"},
            {"name": "Jean Népomuscène Sindikubwabo", "title": "Senator", "chamber": "Senate", "party": "RPF"},
            # ── Provincial Governors ──
            {"name": "Aime Bosenibamwe", "title": "Governor, Kigali City", "chamber": "Executive", "party": "RPF"},
            {"name": "Emmanuel Gasana", "title": "Governor, Eastern Province", "chamber": "Executive", "party": "RPF"},
            {"name": "Jean Claude Musabyimana", "title": "Governor, Southern Province", "chamber": "Executive", "party": "RPF"},
            {"name": "Francois Habitegeko", "title": "Governor, Western Province", "chamber": "Executive", "party": "RPF"},
            {"name": "Dancille Nyirarukundo", "title": "Governor, Northern Province", "chamber": "Executive", "party": "RPF"},
            # Mayor of Kigali
            {"name": "Pudence Rubingisa", "title": "Mayor of the City of Kigali", "chamber": "Executive", "party": "RPF"},
            # ── Political Party Leaders ──
            {"name": "Frank Habineza", "title": "President, Democratic Green Party of Rwanda (DGPR)", "chamber": "Political Parties", "party": "DGPR"},
            {"name": "Christine Mukabunani", "title": "President, Parti Socialiste Rwandais (PSR)", "chamber": "Political Parties", "party": "PSR"},
            {"name": "Victoire Ingabire Umuhoza", "title": "President, DALFA Umurinzi Party", "chamber": "Political Parties", "party": "DALFA"},
            {"name": "Bernard Ntaganda", "title": "President, Parti Social Imberakuri (PS-Imberakuri)", "chamber": "Political Parties", "party": "PS-Imberakuri"},
            # ── Ambassadors ──
            {"name": "Mathilde Mukantabana", "title": "Ambassador of Rwanda to the United States", "chamber": "Diplomatic", "party": ""},
            {"name": "Valentine Rugwabiza", "title": "Permanent Representative of Rwanda to the United Nations", "chamber": "Diplomatic", "party": ""},
            {"name": "Johnston Busingye", "title": "High Commissioner of Rwanda to the United Kingdom", "chamber": "Diplomatic", "party": ""},
            # ── International ──
            {"name": "Louise Mushikiwabo", "title": "Secretary General of La Francophonie", "chamber": "Executive", "party": "RPF"},
        ]
        return [
            RawPersonRecord(
                full_name=m["name"],
                title=m["title"],
                institution=f"{m['chamber']} of Rwanda",
                country_code="RW",
                source_url=DEPUTIES_URL,
                source_type="PARLIAMENT",
                raw_text=f"{m['name']} - {m['title']}, {m['chamber']} of Rwanda",
                scraped_at=now,
                extra_fields=m,
            )
            for m in members
        ]
