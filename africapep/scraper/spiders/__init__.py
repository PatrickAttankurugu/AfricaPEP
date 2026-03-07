"""AfricaPEP scraper spiders — all country/source scrapers."""

from africapep.scraper.spiders.ghana_parliament import GhanaParliamentScraper
from africapep.scraper.spiders.ghana_presidency import GhanaPresidencyScraper
from africapep.scraper.spiders.ghana_ec import GhanaECScraper
from africapep.scraper.spiders.ghana_gazette import GhanaGazetteScraper
from africapep.scraper.spiders.ghana_judiciary import GhanaJudiciaryScraper
from africapep.scraper.spiders.nigeria_nass import NigeriaNASSScraper
from africapep.scraper.spiders.nigeria_presidency import NigeriaPresidencyScraper
from africapep.scraper.spiders.nigeria_inec import NigeriaINECScraper
from africapep.scraper.spiders.nigeria_judiciary import NigeriaJudiciaryScraper
from africapep.scraper.spiders.kenya_parliament import KenyaParliamentScraper
from africapep.scraper.spiders.kenya_presidency import KenyaPresidencyScraper
from africapep.scraper.spiders.kenya_gazette import KenyaGazetteScraper
from africapep.scraper.spiders.southafrica_parliament import SouthAfricaParliamentScraper
from africapep.scraper.spiders.rwanda_parliament import RwandaParliamentScraper
from africapep.scraper.spiders.southafrica_presidency import SouthAfricaPresidencyScraper
from africapep.scraper.spiders.ethiopia_presidency import EthiopiaPresidencyScraper
from africapep.scraper.spiders.tanzania_presidency import TanzaniaPresidencyScraper
from africapep.scraper.spiders.senegal_presidency import SenegalPresidencyScraper
from africapep.scraper.spiders.uganda_parliament import UgandaParliamentScraper

ALL_SCRAPERS = [
    GhanaParliamentScraper,
    GhanaPresidencyScraper,
    GhanaECScraper,
    GhanaGazetteScraper,
    GhanaJudiciaryScraper,
    NigeriaNASSScraper,
    NigeriaPresidencyScraper,
    NigeriaINECScraper,
    NigeriaJudiciaryScraper,
    KenyaParliamentScraper,
    KenyaPresidencyScraper,
    KenyaGazetteScraper,
    SouthAfricaParliamentScraper,
    RwandaParliamentScraper,
    SouthAfricaPresidencyScraper,
    UgandaParliamentScraper,
    EthiopiaPresidencyScraper,
    TanzaniaPresidencyScraper,
    SenegalPresidencyScraper,
]
