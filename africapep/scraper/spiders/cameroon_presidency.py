"""
Scraper for the Cameroon Presidency / Prime Minister's Office.

Source: https://www.spm.gov.cm/site/index.php?l=en
Extracts cabinet ministers from the PM's Office website.
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

BASE_URL = "https://www.spm.gov.cm"
CABINET_URL = f"{BASE_URL}/site/index.php?l=en"


class CameroonPresidencyScraper(BaseScraper):
    """Scraper for the Cameroon Presidency and PM's Office."""

    country_code = "CM"
    source_type = "PRESIDENCY"

    def scrape(self) -> list[RawPersonRecord]:
        """Scrape cabinet officials from the PM's Office website."""
        logger.info("cm_presidency.scrape.start", url=CABINET_URL)
        try:
            resp = self._get(CABINET_URL)
            records = self._parse_officials(resp.text)
            if records:
                return records
            logger.warning("cm_presidency.scrape.no_results")
            return self._load_fixture()
        except Exception:
            logger.exception("cm_presidency.scrape.error")
            return self._load_fixture()

    def _parse_officials(self, html: str) -> list[RawPersonRecord]:
        """Parse government officials from page HTML."""
        soup = BeautifulSoup(html, "html.parser")
        records: list[RawPersonRecord] = []

        # Try various selectors for minister listings
        cards = soup.select(
            ".minister-card, .official-card, .team-member, .card, "
            "[class*='minister'], [class*='official'], article"
        )

        for card in cards:
            try:
                name_el = card.select_one("h3, h4, h2, .name, .title, strong")
                if not name_el:
                    continue
                full_name = name_el.get_text(strip=True)
                if not full_name or len(full_name) < 3:
                    continue

                role_el = card.select_one("p, .role, .position, .subtitle, span")
                role = role_el.get_text(strip=True) if role_el else ""

                records.append(RawPersonRecord(
                    full_name=full_name,
                    title=role if role else "Minister",
                    institution="Presidency of the Republic of Cameroon",
                    country_code=self.country_code,
                    source_type=self.source_type,
                    source_url=CABINET_URL,
                    raw_text=f"{full_name} – {role}",
                    scraped_at=datetime.utcnow(),
                    extra_fields={"category": "Cabinet Ministers"},
                ))
            except Exception:
                logger.exception("cm_presidency.parse.error")

        logger.info("cm_presidency.scrape.complete", count=len(records))
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        officials = [
            # --- President and Prime Minister ---
            {"name": "Paul Biya", "role": "President of the Republic of Cameroon"},
            {"name": "Joseph Dion Ngute", "role": "Prime Minister, Head of Government"},
            # --- Ministers of State ---
            {"name": "Laurent Esso", "role": "Minister of State, Justice and Keeper of the Seals"},
            {"name": "Ferdinand Ngoh Ngoh", "role": "Minister of State, Secretary General of the Presidency"},
            {"name": "Jacques Fame Ndongo", "role": "Minister of State, Higher Education"},
            {"name": "Marafa Hamidou Yaya", "role": "Former Minister of State, Territorial Administration (imprisoned)"},
            # --- Cabinet Ministers ---
            {"name": "Joseph Beti Assomo", "role": "Delegate Minister, Defence"},
            {"name": "Lejeune Mbella Mbella", "role": "Minister of External Relations"},
            {"name": "Paul Atanga Nji", "role": "Minister of Territorial Administration"},
            {"name": "Louis Paul Motaze", "role": "Minister of Finance"},
            {"name": "Rene Emmanuel Sadi", "role": "Minister of Communication"},
            {"name": "Emmanuel Nganou Djoumessi", "role": "Minister of Public Works"},
            {"name": "Luc Magloire Mbarga Atangana", "role": "Minister of Commerce"},
            {"name": "Madeleine Tchuinte", "role": "Minister of Scientific Research and Innovation"},
            {"name": "Alamine Ousmane Mey", "role": "Minister of Economy, Planning and Regional Development"},
            {"name": "Malachie Manaouda", "role": "Minister of Public Health"},
            {"name": "Pauline Egbe Nalova Lyonga", "role": "Minister of Secondary Education"},
            {"name": "Gaston Eloundou Essomba", "role": "Minister of Water Resources and Energy"},
            {"name": "Jean Ernest Massena Ngalle Bibehe", "role": "Minister of Transport"},
            {"name": "Minette Libom Li Likeng", "role": "Minister of Posts and Telecommunications"},
            {"name": "Laurent Serge Etoundi Ngoa", "role": "Minister of Basic Education"},
            {"name": "Mounouna Foutsou", "role": "Minister of Youth and Civic Education"},
            {"name": "Narcisse Mouelle Kombi", "role": "Minister of Arts and Culture"},
            {"name": "Henri Eyebe Ayissi", "role": "Minister of Agriculture and Rural Development"},
            {"name": "Jules Doret Ndongo", "role": "Minister of Forests and Wildlife"},
            {"name": "Celestine Ketcha Courtes", "role": "Minister of Housing and Urban Development"},
            {"name": "Jean De Dieu Momo", "role": "Delegate Minister, Justice"},
            {"name": "Gregoire Owona", "role": "Minister of Labour and Social Security"},
            {"name": "Marie Therese Abena Ondoa", "role": "Minister of Women's Empowerment and the Family"},
            {"name": "Amadou Ali", "role": "Vice-Prime Minister (former)"},
            {"name": "Issa Tchiroma Bakary", "role": "Minister of Employment and Vocational Training"},
            {"name": "Charles Ndongo", "role": "Director General, CRTV"},
            {"name": "Jean Claude Mbwentchou", "role": "Minister of Lands and State Property"},
            {"name": "Pierre Hele", "role": "Minister of Environment, Protection of Nature and Sustainable Development"},
            {"name": "Manaouda Malachie", "role": "Minister of Public Health"},
            {"name": "Edouard Akame Mfoumou", "role": "Minister of State Property, Surveys and Land Tenure (former)"},
            {"name": "Bolvine Wakata", "role": "Minister of Livestock, Fisheries and Animal Industries"},
            {"name": "Achille Bassilekin III", "role": "Minister of Small and Medium-Sized Enterprises, Social Economy and Handicrafts"},
            {"name": "Ernest Gbwaboubou", "role": "Minister of Mines, Industry and Technological Development"},
            {"name": "Nalova Lyonga Pauline Egbe", "role": "Minister of Secondary Education"},
            {"name": "Ismaël Bidoung Mkpatt", "role": "Minister of Sports and Physical Education"},
            # --- Secretaries of State ---
            {"name": "Koung A Bessike", "role": "Secretary of State for Defence, in charge of the Gendarmerie"},
            {"name": "Galax Etoga", "role": "Secretary of State for Defence, in charge of Veterans and War Victims"},
            {"name": "Yaouba Abdoulaye", "role": "Secretary of State for Public Health"},
            # --- Previous Prime Ministers ---
            {"name": "Philemon Yang", "role": "Former Prime Minister (2009-2019)"},
            {"name": "Ephraim Inoni", "role": "Former Prime Minister (2004-2009)"},
            {"name": "Peter Mafany Musonge", "role": "Former Prime Minister (1996-2004)"},
            {"name": "Simon Achidi Achu", "role": "Former Prime Minister (1992-1996, deceased)"},
            # --- Parliament ---
            {"name": "Cavaye Yeguie Djibril", "role": "Speaker of the National Assembly"},
            {"name": "Marcel Niat Njifenji", "role": "President of the Senate"},
            {"name": "Hilarion Etong", "role": "First Vice-President of the National Assembly"},
            {"name": "Aboubakary Abdoulaye", "role": "First Vice-President of the Senate"},
            # --- Judiciary ---
            {"name": "Daniel Mekobe Sone", "role": "Chief Justice, Supreme Court"},
            {"name": "Clement Atangana", "role": "President of the Constitutional Council"},
            {"name": "Alexis Dipanda Mouelle", "role": "Former President of the Constitutional Council"},
            # --- Central Bank ---
            {"name": "Abbas Mahamat Tolli", "role": "Governor, Bank of Central African States (BEAC)"},
            # --- Military ---
            {"name": "Général René Claude Meka", "role": "Chief of Defence Staff"},
            {"name": "Nkoa Atenga", "role": "Chief of Army Staff"},
            {"name": "Jacob Kodji", "role": "Commander of the Air Force"},
            {"name": "Fabien Nkot", "role": "Commander of the Navy"},
            {"name": "Général Galax Etoga", "role": "Secretary of State for the Gendarmerie"},
            # --- Intelligence and Security ---
            {"name": "Martin Mbarga Nguele", "role": "Delegate General of National Security"},
            {"name": "Léopold Maxime Eko Eko", "role": "Director General of External Research (DGRE)"},
            # --- Regional Governors ---
            {"name": "Samuel Dieudonne Ivaha Diboua", "role": "Governor, Littoral Region"},
            {"name": "Naseri Paul Bea", "role": "Governor, Centre Region"},
            {"name": "Midjiyawa Bakari", "role": "Governor, Far North Region"},
            {"name": "Kildadi Taguieke Boukar", "role": "Governor, Adamawa Region"},
            {"name": "Awa Fonka Augustine", "role": "Governor, North West Region"},
            {"name": "Okalia Bilai", "role": "Governor, South West Region"},
            {"name": "Jean Claude Tsila", "role": "Governor, South Region"},
            {"name": "Grégoire Nlend", "role": "Governor, East Region"},
            {"name": "Abakar Ahamat", "role": "Governor, North Region"},
            {"name": "Haman Adama", "role": "Governor, West Region"},
            # --- Heads of State-Owned Enterprises and Key Agencies ---
            {"name": "Ibrahim Talba Malla", "role": "Director General, SONARA (National Oil Refining Company)"},
            {"name": "Adolphe Moudiki", "role": "Director General, SNH (National Hydrocarbons Corporation)"},
            {"name": "Judith Yah Sunday Achidi", "role": "Director General, CAMTEL"},
            {"name": "Cyrus Ngo'o", "role": "Director General, Cameroon Port Authority (PAD)"},
            {"name": "Blaise Moussa", "role": "Director General, CAMWATER"},
            {"name": "Joël Nana Kontchou", "role": "Director General, ENEO (Electricity of Cameroon)"},
            {"name": "Lena Ndjapfou", "role": "Director General, National Social Insurance Fund (CNPS)"},
            {"name": "Martin Camus Mimb", "role": "Director General, Douala Stock Exchange"},
            # --- Anti-Corruption ---
            {"name": "Dieudonné Massi Gams", "role": "Chairman, National Anti-Corruption Commission (CONAC)"},
            # --- Political Party Leaders and Opposition ---
            {"name": "Maurice Kamto", "role": "President, Cameroon Renaissance Movement (MRC)"},
            {"name": "John Fru Ndi", "role": "Former Chairman, Social Democratic Front (SDF, deceased 2023)"},
            {"name": "Joshua Osih", "role": "First Vice-President, Social Democratic Front (SDF)"},
            {"name": "Adamou Ndam Njoya", "role": "President, Cameroon Democratic Union (UDC, deceased 2020)"},
            {"name": "Bello Bouba Maigari", "role": "President, National Union for Democracy and Progress (UNDP)"},
            {"name": "Jean Jacques Ekindi", "role": "President, Mouvement Progressiste (MP)"},
            {"name": "Cabral Libii", "role": "President, Cameroon Party for National Reconciliation (PCRN)"},
            # --- Ambassadors ---
            {"name": "Henri Etoundi Essomba", "role": "Ambassador of Cameroon to the United States"},
            {"name": "André Magnus Ekoumou", "role": "Ambassador of Cameroon to France"},
            {"name": "Michel Tommo Monthé", "role": "Permanent Representative to the United Nations"},
            # --- Former President ---
            {"name": "Ahmadou Ahidjo", "role": "Former President of the Republic (1960-1982, deceased 1989)"},
        ]

        records = []
        for o in officials:
            records.append(RawPersonRecord(
                full_name=o["name"],
                title=o["role"],
                institution="Presidency of the Republic of Cameroon",
                country_code=self.country_code,
                source_type=self.source_type,
                source_url=CABINET_URL,
                raw_text=f"{o['name']} – {o['role']}",
                scraped_at=now,
                extra_fields={
                    "category": "Cabinet Ministers",
                    "fixture": True,
                },
            ))

        logger.info("cm_presidency.fixture.loaded", count=len(records))
        return records
