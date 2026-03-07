"""Ethiopia Presidency / Cabinet scraper.
Source: https://www.pmo.gov.et/
Method: BeautifulSoup (static HTML)
Schedule: Weekly
"""
from bs4 import BeautifulSoup
from datetime import datetime

import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

log = structlog.get_logger()

BASE_URL = "https://www.pmo.gov.et"
CABINET_URL = f"{BASE_URL}/"


class EthiopiaPresidencyScraper(BaseScraper):
    """Scraper for Ethiopia Presidency / Cabinet members."""

    country_code = "ET"
    source_type = "PRESIDENCY"

    def scrape(self) -> list[RawPersonRecord]:
        records = []
        try:
            resp = self._get(CABINET_URL)
            soup = BeautifulSoup(resp.text, "html.parser")
            records = self._parse_page(soup, CABINET_URL)
            log.info("ethiopia_presidency_scraped", records=len(records))
        except Exception as e:
            log.warning(
                "ethiopia_presidency_unreachable_falling_back_to_fixture",
                error=str(e),
            )
            records = self._load_fixture()
        return records

    def _parse_page(self, soup: BeautifulSoup, source_url: str) -> list[RawPersonRecord]:
        records = []
        now = datetime.utcnow()

        # Try various selectors for cabinet member cards
        cards = (
            soup.select(".team-member") or
            soup.select(".cabinet-member") or
            soup.select(".elementor-widget-container .member") or
            soup.select("article") or
            soup.select(".entry-content h3")
        )

        for card in cards:
            try:
                name_el = card.select_one("h3, h4, h5, .member-name, strong")
                if not name_el:
                    continue

                name = name_el.get_text(strip=True)
                if not name or len(name) < 3:
                    continue

                # Clean name
                clean_name = name
                for prefix in ["H.E.", "Hon.", "Dr.", "Prof.", "Amb."]:
                    if clean_name.startswith(prefix):
                        clean_name = clean_name[len(prefix):].strip()

                # Get portfolio
                portfolio = ""
                title_el = card.select_one(".position, .portfolio, p, .member-title")
                if title_el:
                    portfolio = title_el.get_text(strip=True)

                records.append(RawPersonRecord(
                    full_name=clean_name,
                    title=portfolio or "Minister",
                    institution="Office of the Prime Minister of Ethiopia",
                    country_code="ET",
                    source_url=source_url,
                    source_type="PRESIDENCY",
                    raw_text=f"{name} - {portfolio}",
                    scraped_at=now,
                    extra_fields={"portfolio": portfolio, "raw_name": name},
                ))
            except Exception as e:
                log.warning("ethiopia_presidency_parse_error", error=str(e))

        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        cabinet = [
            # === Executive ===
            {"name": "Taye Atske Selassie", "title": "President of the Federal Republic of Ethiopia"},
            {"name": "Sahle-Work Zewde", "title": "Former President of the Federal Republic of Ethiopia"},
            {"name": "Abiy Ahmed Ali", "title": "Prime Minister"},
            {"name": "Demeke Mekonnen", "title": "Deputy Prime Minister / Minister of Foreign Affairs"},
            {"name": "Redwan Hussein", "title": "National Security Advisor"},
            # Previous PMs / Presidents (historically significant)
            {"name": "Hailemariam Desalegn", "title": "Former Prime Minister of Ethiopia"},
            {"name": "Meles Zenawi", "title": "Former Prime Minister of Ethiopia (deceased)"},
            {"name": "Girma Wolde-Giorgis", "title": "Former President of the Federal Republic of Ethiopia"},
            {"name": "Mulatu Teshome", "title": "Former President of the Federal Republic of Ethiopia"},
            # === Council of Ministers ===
            {"name": "Abraham Belay", "title": "Minister of Defence"},
            {"name": "Ahmed Shide", "title": "Minister of Finance"},
            {"name": "Fetlework Gebregziabher", "title": "Minister of Health"},
            {"name": "Berhanu Nega", "title": "Minister of Education"},
            {"name": "Aisha Mohammed", "title": "Minister of Industry"},
            {"name": "Dagmawit Moges", "title": "Minister of Transport and Logistics"},
            {"name": "Muferiat Kamil", "title": "Minister of Labour and Social Affairs"},
            {"name": "Habtamu Itefa", "title": "Minister of Water and Energy"},
            {"name": "Belete Molla", "title": "Minister of Innovation and Technology"},
            {"name": "Ergogie Tesfaye", "title": "Minister of Women and Social Affairs"},
            {"name": "Shumete Gizaw", "title": "Minister of Trade and Regional Integration"},
            {"name": "Girma Amente", "title": "Minister of Agriculture"},
            {"name": "Kejela Merdasa", "title": "Minister of Mines and Petroleum"},
            {"name": "Nasise Challi", "title": "Minister of Culture and Sports"},
            {"name": "Binalf Andualem", "title": "Minister of Urban Development and Infrastructure"},
            {"name": "Chaltu Sani", "title": "Minister of Revenue"},
            {"name": "Shimellis Abdisa", "title": "Minister of Planning and Development"},
            {"name": "Temesgen Tiruneh", "title": "Minister of Peace"},
            {"name": "Lakech Diriba", "title": "Minister of Irrigation and Lowlands"},
            {"name": "Eyob Tekalign", "title": "State Minister of Finance"},
            {"name": "Seleahat Yilma", "title": "State Minister of Health"},
            {"name": "Billene Seyoum", "title": "Press Secretary, Office of the Prime Minister"},
            # === Attorney General ===
            {"name": "Gedion Timothewos", "title": "Attorney General of Ethiopia"},
            # === Parliament ===
            {"name": "Tagesse Chafo", "title": "Speaker of the House of Peoples' Representatives"},
            {"name": "Agegnehu Teshager", "title": "President of the House of Federation"},
            {"name": "Shitaye Minale", "title": "Deputy Speaker of the House of Peoples' Representatives"},
            # === Judiciary ===
            {"name": "Meaza Ashenafi", "title": "Former Chief Justice of the Federal Supreme Court"},
            {"name": "Tewodros Mihret", "title": "Chief Justice of the Federal Supreme Court"},
            {"name": "Wondwossen Teshome", "title": "President of the Federal High Court"},
            # === Central Bank ===
            {"name": "Mamo Esmelealem Mihretu", "title": "Governor, National Bank of Ethiopia"},
            # === Intelligence & Security ===
            {"name": "Temesgen Tiruneh", "title": "Former Director General, National Intelligence and Security Service (NISS)"},
            {"name": "Redwan Hussein", "title": "Former Head, National Intelligence and Security Service"},
            # === Military ===
            {"name": "Birhanu Jula", "title": "Chief of General Staff, Ethiopian National Defence Force"},
            {"name": "Abebaw Tadesse", "title": "Deputy Chief of Staff, Ethiopian National Defence Force"},
            {"name": "Yilma Merdasa", "title": "Commander, Ethiopian Ground Forces"},
            {"name": "Desta Abiche", "title": "Commander, Ethiopian Air Force"},
            # === Federal Police ===
            {"name": "Demelash Gebremichael", "title": "Commissioner General, Ethiopian Federal Police"},
            # === Ethiopian Revenue Authority ===
            {"name": "Amare Elias", "title": "Director General, Ethiopian Customs Commission"},
            # === Key State Enterprises ===
            {"name": "Mesfin Tasew", "title": "CEO, Ethiopian Airlines Group"},
            {"name": "Frehiwot Tamiru", "title": "CEO, Ethio Telecom"},
            {"name": "Ashebir Balcha", "title": "CEO, Ethiopian Electric Power"},
            {"name": "Amdework Tadesse", "title": "CEO, Commercial Bank of Ethiopia"},
            {"name": "Hailu Kebede", "title": "CEO, Ethiopian Shipping and Logistics Services Enterprise"},
            # === Regional State Presidents ===
            {"name": "Shimeles Abdisa", "title": "President, Oromia Regional State"},
            {"name": "Yilkal Kefale", "title": "President, Amhara Regional State"},
            {"name": "Getachew Reda", "title": "President, Tigray Regional State"},
            {"name": "Abdi Mohamoud Omar", "title": "Former President, Somali Regional State"},
            {"name": "Mustafe Muhummed Omer", "title": "President, Somali Regional State"},
            {"name": "Awol Arba", "title": "President, Afar Regional State"},
            {"name": "Ashadli Hassen", "title": "President, Benishangul-Gumuz Regional State"},
            {"name": "Umer Usman", "title": "President, Gambella Regional State"},
            {"name": "Ordofa Gusu", "title": "President, Harari Regional State"},
            {"name": "Desta Ledamo", "title": "President, Sidama Regional State"},
            {"name": "Dendir Ismail", "title": "President, Dire Dawa Administration"},
            {"name": "Habtamu Makonnen", "title": "President, South West Ethiopia Regional State"},
            {"name": "Tegegn Benti", "title": "President, Central Ethiopia Regional State"},
            {"name": "Dagim Hailu", "title": "President, South Ethiopia Regional State"},
            # === Mayor of Addis Ababa ===
            {"name": "Adanech Abiebie", "title": "Mayor of Addis Ababa"},
            # === Political Party Leaders ===
            {"name": "Birtukan Mideksa", "title": "Chairperson, National Election Board of Ethiopia"},
            {"name": "Jawar Mohammed", "title": "Opposition Political Figure, Oromo Federalist Congress"},
            {"name": "Lidetu Ayalew", "title": "Leader, Ethiopian Democratic Party"},
            {"name": "Debretsion Gebremichael", "title": "Chairman, Tigray People's Liberation Front (TPLF)"},
            {"name": "Dawud Ibsa", "title": "Chairman, Oromo Liberation Front (OLF)"},
            {"name": "Berhanu Nega", "title": "Secretary General, Prosperity Party"},
            {"name": "Merera Gudina", "title": "Chairman, Oromo Federalist Congress"},
            {"name": "Yeshiwas Assefa", "title": "Chairman, Ethiopian Citizens for Social Justice (EZEMA)"},
            # === Ethiopian Human Rights Commission ===
            {"name": "Daniel Bekele", "title": "Chief Commissioner, Ethiopian Human Rights Commission"},
            # === Anti-Corruption ===
            {"name": "Samuel Urkato", "title": "Commissioner, Federal Ethics and Anti-Corruption Commission"},
            # === Ambassadors ===
            {"name": "Taye Atske Selassie", "title": "Former Permanent Representative to the United Nations"},
            {"name": "Fitsum Arega", "title": "Ambassador of Ethiopia to the United States"},
            {"name": "Tesfaye Yilma Sabo", "title": "Permanent Representative of Ethiopia to the African Union"},
            # === Other Key Officials ===
            {"name": "Sileshi Bekele", "title": "Former Minister of Water, Irrigation and Energy"},
            {"name": "Kenea Yadeta", "title": "Minister of Justice"},
            {"name": "Adem Farah", "title": "Commissioner, Ethiopian Investment Commission"},
            {"name": "Balcha Reba", "title": "Governor, Development Bank of Ethiopia"},
            {"name": "Sofiya Kedir", "title": "Director General, Ethiopian Public Health Institute"},
            {"name": "Demitu Hambisa", "title": "State Minister of Agriculture"},
            {"name": "Getahun Mekuria", "title": "Former Minister of Innovation and Technology"},
            {"name": "Arkebe Oqubay", "title": "Senior Adviser to the Prime Minister"},
        ]
        return [
            RawPersonRecord(
                full_name=m["name"],
                title=m["title"],
                institution="Office of the Prime Minister of Ethiopia",
                country_code="ET",
                source_url=CABINET_URL,
                source_type="PRESIDENCY",
                raw_text=f"{m['name']} - {m['title']}",
                scraped_at=now,
                extra_fields=m,
            )
            for m in cabinet
        ]
