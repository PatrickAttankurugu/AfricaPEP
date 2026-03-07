"""
Scraper for the Kingdom of Morocco Government / Cabinet.

Source: https://www.cg.gov.ma/en
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

GOV_URL = "https://www.cg.gov.ma/en"


class MoroccoPresidencyScraper(BaseScraper):
    """Scraper for the Moroccan Government (Head of Government's Office)."""

    country_code = "MA"
    source_type = "PRESIDENCY"

    def scrape(self) -> list[RawPersonRecord]:
        logger.info("ma_presidency.scrape.start", url=GOV_URL)
        try:
            resp = self._get(GOV_URL)
            records = self._parse_officials(resp.text)
            if records:
                return records
            return self._load_fixture()
        except Exception:
            logger.exception("ma_presidency.scrape.error")
            return self._load_fixture()

    def _parse_officials(self, html: str) -> list[RawPersonRecord]:
        soup = BeautifulSoup(html, "html.parser")
        records: list[RawPersonRecord] = []
        cards = soup.select(".minister, .team-member, .card, article, [class*='minister']")
        for card in cards:
            try:
                name_el = card.select_one("h3, h4, h2, .name, strong")
                if not name_el:
                    continue
                full_name = name_el.get_text(strip=True)
                if not full_name or len(full_name) < 3:
                    continue
                role_el = card.select_one("p, .role, .position")
                role = role_el.get_text(strip=True) if role_el else "Minister"
                records.append(RawPersonRecord(
                    full_name=full_name, title=role,
                    institution="Government of the Kingdom of Morocco",
                    country_code=self.country_code, source_type=self.source_type,
                    source_url=GOV_URL, raw_text=f"{full_name} – {role}",
                    scraped_at=datetime.utcnow(), extra_fields={"category": "Cabinet"},
                ))
            except Exception:
                logger.exception("ma_presidency.parse.error")
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        officials = [
            # ---- Head of State & Royal Family ----
            {"name": "King Mohammed VI", "role": "King of Morocco, Head of State"},
            {"name": "Prince Moulay Hassan", "role": "Crown Prince of Morocco"},
            {"name": "Prince Moulay Rachid", "role": "Prince, Royal Family"},
            {"name": "Princess Lalla Meryem", "role": "Princess, President of National Union of Moroccan Women"},
            {"name": "Princess Lalla Hasna", "role": "Princess, President of Mohammed VI Foundation for Environmental Protection"},
            # ---- Head of Government & Cabinet ----
            {"name": "Aziz Akhannouch", "role": "Head of Government"},
            {"name": "Nasser Bourita", "role": "Minister of Foreign Affairs, African Cooperation and Moroccans Abroad"},
            {"name": "Abdelouafi Laftit", "role": "Minister of Interior"},
            {"name": "Nadia Fettah Alaoui", "role": "Minister of Economy and Finance"},
            {"name": "Abdellatif Ouahbi", "role": "Minister of Justice"},
            {"name": "Abdellatif Miraoui", "role": "Minister of Higher Education, Scientific Research and Innovation"},
            {"name": "Chakib Benmoussa", "role": "Minister of National Education, Preschool and Sports"},
            {"name": "Nizar Baraka", "role": "Minister of Equipment and Water"},
            {"name": "Abdellatif Loudiyi", "role": "Minister Delegate for National Defence"},
            {"name": "Khalid Ait Taleb", "role": "Minister of Health and Social Protection"},
            {"name": "Younes Sekkouri", "role": "Minister of Economic Inclusion, Small Business, Employment and Skills"},
            {"name": "Fatim-Zahra Ammor", "role": "Minister of Tourism, Handicrafts and Social and Solidarity Economy"},
            {"name": "Mohcine Jazouli", "role": "Minister Delegate for Investment, Convergence and Public Policies"},
            {"name": "Ryad Mezzour", "role": "Minister of Industry and Commerce"},
            {"name": "Leila Benali", "role": "Minister of Energy Transition and Sustainable Development"},
            {"name": "Mohamed Abdeljalil", "role": "Minister of Transport and Logistics"},
            {"name": "Ghita Mezzour", "role": "Minister Delegate for Digital Transition and Administration Reform"},
            {"name": "Mohamed Sadiki", "role": "Minister of Agriculture, Maritime Fisheries, Rural Development and Water and Forests"},
            {"name": "Aawatif Hayar", "role": "Minister of Solidarity, Social Inclusion and Family"},
            {"name": "Mohamed Mehdi Bensaid", "role": "Minister of Youth, Culture and Communication"},
            {"name": "Mustapha Baitas", "role": "Government Spokesperson, Minister Delegate to Head of Government"},
            {"name": "Faouzi Lekjaa", "role": "Minister Delegate for Budget"},
            {"name": "Lahcen Daoudi", "role": "Minister Delegate for General Affairs and Governance"},
            {"name": "Mamoun Bouhdoud", "role": "Minister Delegate for Small Business and Entrepreneurship"},
            {"name": "Khalid Safir", "role": "Wali, Director General of Local Authorities, Ministry of Interior"},
            # ---- Parliament ----
            {"name": "Rachid Talbi El Alami", "role": "Speaker of the House of Representatives"},
            {"name": "Enaam Mayara", "role": "Speaker of the House of Councillors"},
            # ---- Judiciary ----
            {"name": "Mohamed Benabdelkader", "role": "First President of the Court of Cassation"},
            {"name": "Mohamed Abdennabaoui", "role": "Prosecutor General of the King at the Court of Cassation"},
            {"name": "Ahmed El Ghazali", "role": "Head of the Supreme Judicial Council (Delegated)"},
            # ---- Central Bank ----
            {"name": "Abdellatif Jouahri", "role": "Governor, Bank Al-Maghrib"},
            # ---- Military & Security ----
            {"name": "Belkhir El Farouk", "role": "Inspector General of the Royal Armed Forces (FAR)"},
            {"name": "Mohamed Haramou", "role": "Commander of the Royal Gendarmerie"},
            {"name": "Abdellatif Hammouchi", "role": "Director General of National Security (DGSN) and Territorial Surveillance (DGST)"},
            {"name": "Yassine Mansouri", "role": "Director General, External Intelligence (DGED)"},
            # ---- Court of Accounts ----
            {"name": "Zineb El Adaoui", "role": "First President of the Court of Accounts"},
            # ---- Previous Prime Ministers ----
            {"name": "Saadeddine El Othmani", "role": "Former Head of Government (2017-2021)"},
            {"name": "Abdelilah Benkirane", "role": "Former Head of Government (2011-2017), PJD Leader"},
            {"name": "Abbas El Fassi", "role": "Former Prime Minister (2007-2011)"},
            {"name": "Driss Jettou", "role": "Former Prime Minister (2002-2007)"},
            # ---- Political Party Leaders ----
            {"name": "Abdellatif Wahbi", "role": "Secretary General, Authenticity and Modernity Party (PAM)"},
            {"name": "Nizar Baraka", "role": "Secretary General, Istiqlal Party (PI)"},
            {"name": "Driss Lachgar", "role": "First Secretary, Socialist Union of Popular Forces (USFP)"},
            {"name": "Mohand Laenser", "role": "Secretary General, Popular Movement (MP)"},
            {"name": "Nabil Benabdellah", "role": "Secretary General, Party of Progress and Socialism (PPS)"},
            # ---- Ambassadors ----
            {"name": "Omar Hilale", "role": "Permanent Representative to the United Nations"},
            {"name": "Youssef Amrani", "role": "Ambassador to the United States"},
            {"name": "Samira Sitail", "role": "Ambassador to France"},
            # ---- Regional Governors / Walis ----
            {"name": "Said Ahmidouch", "role": "Wali of Casablanca-Settat Region"},
            {"name": "Mohamed Yacoubi", "role": "Wali of Rabat-Sale-Kenitra Region"},
            {"name": "Karim Kassi-Lahlou", "role": "Wali of Marrakech-Safi Region"},
            {"name": "Said Zniber", "role": "Wali of Fez-Meknes Region"},
            {"name": "Mohamed Mhidia", "role": "Wali of Tangier-Tetouan-Al Hoceima Region"},
            {"name": "Ahmed Hajji", "role": "Wali of Souss-Massa Region"},
            {"name": "Khatib El Hebil", "role": "Wali of Oriental Region"},
            # ---- Key Agencies & State Enterprises ----
            {"name": "Mostafa Terrab", "role": "Chairman and CEO, OCP Group"},
            {"name": "Anass Houir Alami", "role": "Director General, Caisse de Depot et de Gestion (CDG)"},
            {"name": "Tarik Hamane", "role": "Director General, Moroccan Agency for Sustainable Energy (MASEN)"},
            {"name": "Asmaa Rhlalou", "role": "Director General, National Telecommunications Regulatory Agency (ANRT)"},
            {"name": "Abderrahim El Hafidi", "role": "Director General, National Office of Electricity and Water (ONEE)"},
            {"name": "Mohamed Bachir Rachdi", "role": "President, National Authority for Probity, Prevention and Fight against Corruption (INPPLC)"},
            {"name": "Ahmed Reda Chami", "role": "President, Economic, Social and Environmental Council (CESE)"},
            # ---- Human Rights & Oversight ----
            {"name": "Amina Bouayach", "role": "President, National Human Rights Council (CNDH)"},
            {"name": "Omar Azziman", "role": "Advisor to the King, Former President of CESE"},
            {"name": "Andre Azoulay", "role": "Senior Advisor to King Mohammed VI"},
            {"name": "Fouad Ali El Himma", "role": "Senior Advisor to King Mohammed VI"},
            # ---- Competition & Regulation ----
            {"name": "Ahmed Rahhou", "role": "President, Competition Council"},
            {"name": "Latifa Akharbach", "role": "President, High Authority for Audiovisual Communication (HACA)"},
        ]
        records = []
        for o in officials:
            records.append(RawPersonRecord(
                full_name=o["name"], title=o["role"],
                institution="Government of the Kingdom of Morocco",
                country_code=self.country_code, source_type=self.source_type,
                source_url=GOV_URL, raw_text=f"{o['name']} – {o['role']}",
                scraped_at=now, extra_fields={"category": "Cabinet", "fixture": True},
            ))
        logger.info("ma_presidency.fixture.loaded", count=len(records))
        return records
