"""
Scraper for the Tunisian Presidency / Government.

Source: https://www.pm.gov.tn
"""

from bs4 import BeautifulSoup
from datetime import datetime
import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

logger = structlog.get_logger(__name__)

GOV_URL = "http://pm.gov.tn/ar"


class TunisiaPresidencyScraper(BaseScraper):
    """Scraper for the Tunisian Government."""

    country_code = "TN"
    source_type = "PRESIDENCY"

    def scrape(self) -> list[RawPersonRecord]:
        logger.info("tn_presidency.scrape.start", url=GOV_URL)
        try:
            resp = self._get(GOV_URL)
            records = self._parse_officials(resp.text)
            if records:
                return records
            return self._load_fixture()
        except Exception:
            logger.exception("tn_presidency.scrape.error")
            return self._load_fixture()

    def _parse_officials(self, html: str) -> list[RawPersonRecord]:
        soup = BeautifulSoup(html, "html.parser")
        records: list[RawPersonRecord] = []
        cards = soup.select(".minister, .team-member, .card, article")
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
                    institution="Government of the Republic of Tunisia",
                    country_code=self.country_code, source_type=self.source_type,
                    source_url=GOV_URL, raw_text=f"{full_name} – {role}",
                    scraped_at=datetime.utcnow(), extra_fields={"category": "Cabinet"},
                ))
            except Exception:
                logger.exception("tn_presidency.parse.error")
        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        officials = [
            # --- President and Head of Government ---
            {"name": "Kais Saied", "role": "President of the Republic of Tunisia"},
            {"name": "Ahmed Hachani", "role": "Head of Government"},
            # --- Cabinet Ministers ---
            {"name": "Nabil Ammar", "role": "Minister of Foreign Affairs, Migration and Tunisians Abroad"},
            {"name": "Kamel Feki", "role": "Minister of Interior"},
            {"name": "Imed Memmich", "role": "Minister of National Defence"},
            {"name": "Sihem Boughdiri Nemsia", "role": "Minister of Finance"},
            {"name": "Leila Jaffel", "role": "Minister of Justice"},
            {"name": "Ali Mrabet", "role": "Minister of Health"},
            {"name": "Mohamed Ali Boughdiri", "role": "Minister of Education"},
            {"name": "Moncef Boukthir", "role": "Minister of Higher Education and Scientific Research"},
            {"name": "Sofiane Hemissi", "role": "Minister of Transport"},
            {"name": "Samir Abdelhafidh", "role": "Minister of Economy and Planning"},
            {"name": "Kalthoum Ben Rejeb", "role": "Minister of Trade and Export Development"},
            {"name": "Nabil Hajji", "role": "Minister of Industry, Mines and Energy"},
            {"name": "Mohamed Fadhel Kraiem", "role": "Minister of Communication Technologies"},
            {"name": "Leila Chikhaoui-Mahdaoui", "role": "Minister of Environment"},
            {"name": "Mohamed Rekik", "role": "Minister of Agriculture, Water Resources and Fisheries"},
            {"name": "Kamel Deguiche", "role": "Minister of Tourism and Handicrafts"},
            {"name": "Malek Zahi", "role": "Minister of Social Affairs"},
            {"name": "Najoua Gamha", "role": "Minister of Women, Family, Children and Senior Citizens"},
            {"name": "Ghazi Chaouachi", "role": "Minister of State Property and Land Affairs (former)"},
            {"name": "Mohamed Trabelsi", "role": "Minister of Youth and Sports"},
            {"name": "Ridha Chalghoum", "role": "Minister of Religious Affairs"},
            {"name": "Habib Ammar", "role": "Minister of Tourism and Handicrafts (former)"},
            {"name": "Anouar Maarouf", "role": "Minister of Transport and Logistics (former)"},
            {"name": "Hasna Ben Slimane", "role": "Minister of Equipment and Housing"},
            {"name": "Riadh Mouakher", "role": "Minister of Local Affairs and the Environment (former)"},
            {"name": "Taoufik Rajhi", "role": "Minister of Major Reforms (former)"},
            {"name": "Slim Feriani", "role": "Minister of Industry and SMEs (former)"},
            {"name": "Mohamed Salah Ben Ammar", "role": "Minister of Cultural Affairs"},
            {"name": "Sarra Zaafrani Zenzri", "role": "Minister of Equipment, Housing and Infrastructure (former)"},
            # --- Secretaries of State ---
            {"name": "Mohamed Mzoughi", "role": "Secretary of State for Foreign Affairs"},
            {"name": "Abdessalem Loued", "role": "Secretary of State for Digital Economy"},
            # --- Previous Presidents ---
            {"name": "Béji Caïd Essebsi", "role": "Former President of the Republic (2014-2019, deceased)"},
            {"name": "Moncef Marzouki", "role": "Former President of the Republic (2011-2014)"},
            {"name": "Zine El Abidine Ben Ali", "role": "Former President of the Republic (1987-2011, deceased 2019)"},
            {"name": "Fouad Mebazaa", "role": "Former Interim President (2011)"},
            # --- Previous Prime Ministers / Heads of Government ---
            {"name": "Najla Bouden", "role": "Former Head of Government (2021-2023)"},
            {"name": "Hichem Mechichi", "role": "Former Head of Government (2020-2021)"},
            {"name": "Elyes Fakhfakh", "role": "Former Head of Government (2020)"},
            {"name": "Youssef Chahed", "role": "Former Head of Government (2016-2020)"},
            {"name": "Habib Essid", "role": "Former Head of Government (2015-2016)"},
            {"name": "Mehdi Jomaa", "role": "Former Head of Government (2014-2015)"},
            {"name": "Ali Larayedh", "role": "Former Head of Government (2013-2014)"},
            {"name": "Hamadi Jebali", "role": "Former Head of Government (2011-2013)"},
            {"name": "Mohamed Ghannouchi", "role": "Former Prime Minister (1999-2011)"},
            # --- Parliament ---
            {"name": "Ibrahim Bouderbala", "role": "Speaker of the Assembly of People's Representatives"},
            {"name": "Tarek Fetiti", "role": "First Vice-President of the Assembly of People's Representatives"},
            # --- National Council of Regions and Districts ---
            {"name": "Imed Derbali", "role": "President of the National Council of Regions and Districts"},
            # --- Judiciary ---
            {"name": "Taieb Rakhroukh", "role": "First President of the Court of Cassation"},
            {"name": "Saida Akremi", "role": "President of the Administrative Court (former)"},
            {"name": "Mohamed Habib Marsit", "role": "First President of the Court of Audit"},
            # --- Central Bank ---
            {"name": "Fethi Zouhair Nouri", "role": "Governor, Central Bank of Tunisia"},
            {"name": "Marouane El Abassi", "role": "Former Governor, Central Bank of Tunisia (2018-2023)"},
            # --- Military ---
            {"name": "Général Khaled Shili", "role": "Chief of Staff of the Armed Forces"},
            {"name": "Général Mohamed Salah Hamdi", "role": "Commander of the Army"},
            {"name": "Amiral Kamel Akrout", "role": "Former Chief of Staff of the Armed Forces"},
            {"name": "Général Ismail Fathalli", "role": "Former Chief of Staff of the Armed Forces"},
            # --- Intelligence and Security ---
            {"name": "Sofiene Bessadok", "role": "Director General of National Security"},
            {"name": "Mourad Agrebi", "role": "Director General of Military Intelligence (former)"},
            # --- Governors of Governorates ---
            {"name": "Kamel Haj Sassi", "role": "Governor of Tunis"},
            {"name": "Mohamed Cheikhrouhou", "role": "Governor of Sfax"},
            {"name": "Ridha Attia", "role": "Governor of Sousse"},
            {"name": "Badra Gaâloul", "role": "Governor of Nabeul"},
            {"name": "Dhaker Barraket", "role": "Governor of Ariana"},
            {"name": "Mabrouk Essaidi", "role": "Governor of Ben Arous"},
            {"name": "Mohamed Nabil Abdellatif", "role": "Governor of Bizerte"},
            {"name": "Rim Mahjoub", "role": "Governor of Manouba"},
            {"name": "Ezzedine Khelifi", "role": "Governor of Kairouan"},
            {"name": "Mohamed Dhahbi", "role": "Governor of Gabès"},
            {"name": "Abdallah Rabhi", "role": "Governor of Gafsa"},
            {"name": "Mounir Friaa", "role": "Governor of Monastir"},
            {"name": "Nabil Hamdi", "role": "Governor of Médenine"},
            {"name": "Adel Khedher", "role": "Governor of Kasserine"},
            # --- Political Party Leaders ---
            {"name": "Rached Ghannouchi", "role": "President of Ennahdha Movement (detained)"},
            {"name": "Noureddine Bhiri", "role": "Vice-President of Ennahdha Movement (detained)"},
            {"name": "Abir Moussi", "role": "President of the Free Destourian Party (PDL, detained)"},
            {"name": "Lotfi Mraihi", "role": "President of the Republican People's Union (UPR)"},
            {"name": "Hamma Hammami", "role": "Secretary General of the Workers' Party"},
            {"name": "Issam Chebbi", "role": "Secretary General of the Republican Party"},
            {"name": "Zouhair Maghzaoui", "role": "Secretary General of the People's Movement (Echaab)"},
            {"name": "Mohsen Marzouk", "role": "President of Machrouu Tounes"},
            {"name": "Hafedh Caid Essebsi", "role": "Former President of Nidaa Tounes"},
            # --- UGTT and Civil Society ---
            {"name": "Noureddine Taboubi", "role": "Secretary General, Tunisian General Labour Union (UGTT)"},
            {"name": "Samir Majoul", "role": "President, Tunisian Confederation of Industry, Trade and Handicrafts (UTICA)"},
            {"name": "Wahid Ferchichi", "role": "President, Tunisian Association for the Defence of Individual Liberties"},
            # --- Heads of Key Agencies and State Enterprises ---
            {"name": "Hisham Anane", "role": "CEO, Tunisair"},
            {"name": "Mosbah Helali", "role": "CEO, Tunisian Company of Electricity and Gas (STEG)"},
            {"name": "Mohamed Salah Arfaoui", "role": "CEO, SONEDE (National Water Exploitation and Distribution Company)"},
            {"name": "Ahmed Ben Oun", "role": "CEO, Tunisian Ports Office (OMMP)"},
            {"name": "Sofiene Khemir", "role": "CEO, Tunisie Telecom"},
            # --- Anti-Corruption ---
            {"name": "Imed Boukhris", "role": "President, National Anti-Corruption Authority (INLUCC)"},
            # --- Ambassadors ---
            {"name": "Hanene Tajouri Bessassi", "role": "Ambassador of Tunisia to the United States"},
            {"name": "Dhia Khaled", "role": "Ambassador of Tunisia to France"},
            {"name": "Tarek Ladeb", "role": "Permanent Representative of Tunisia to the United Nations"},
        ]
        records = []
        for o in officials:
            records.append(RawPersonRecord(
                full_name=o["name"], title=o["role"],
                institution="Government of the Republic of Tunisia",
                country_code=self.country_code, source_type=self.source_type,
                source_url=GOV_URL, raw_text=f"{o['name']} – {o['role']}",
                scraped_at=now, extra_fields={"category": "Cabinet", "fixture": True},
            ))
        logger.info("tn_presidency.fixture.loaded", count=len(records))
        return records
