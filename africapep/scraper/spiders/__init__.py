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
from africapep.scraper.spiders.tanzania_parliament import TanzaniaParliamentScraper
from africapep.scraper.spiders.namibia_parliament import NamibiaParliamentScraper
from africapep.scraper.spiders.cameroon_presidency import CameroonPresidencyScraper
from africapep.scraper.spiders.cotedivoire_parliament import CoteDIvoireParliamentScraper
from africapep.scraper.spiders.malawi_presidency import MalawiPresidencyScraper
from africapep.scraper.spiders.zambia_parliament import ZambiaParliamentScraper
from africapep.scraper.spiders.egypt_presidency import EgyptPresidencyScraper
from africapep.scraper.spiders.morocco_presidency import MoroccoPresidencyScraper
from africapep.scraper.spiders.botswana_parliament import BotswanaParliamentScraper
from africapep.scraper.spiders.zimbabwe_parliament import ZimbabweParliamentScraper
from africapep.scraper.spiders.mozambique_presidency import MozambiquePresidencyScraper
from africapep.scraper.spiders.angola_presidency import AngolaPresidencyScraper
from africapep.scraper.spiders.drc_parliament import DRCParliamentScraper
from africapep.scraper.spiders.tunisia_presidency import TunisiaPresidencyScraper
from africapep.scraper.spiders.gambia_presidency import GambiaPresidencyScraper
from africapep.scraper.spiders.sierraleone_presidency import SierraLeonePresidencyScraper
from africapep.scraper.spiders.algeria_presidency import AlgeriaPresidencyScraper
from africapep.scraper.spiders.benin_presidency import BeninPresidencyScraper
from africapep.scraper.spiders.burkinafaso_presidency import BurkinaFasoPresidencyScraper
from africapep.scraper.spiders.burundi_presidency import BurundiPresidencyScraper
from africapep.scraper.spiders.capeverde_presidency import CapeVerdePresidencyScraper
from africapep.scraper.spiders.car_presidency import CARPresidencyScraper
from africapep.scraper.spiders.chad_presidency import ChadPresidencyScraper
from africapep.scraper.spiders.comoros_presidency import ComorosPresidencyScraper
from africapep.scraper.spiders.congo_presidency import CongoPresidencyScraper
from africapep.scraper.spiders.djibouti_presidency import DjiboutiPresidencyScraper
from africapep.scraper.spiders.eqguinea_presidency import EqGuineaPresidencyScraper
from africapep.scraper.spiders.eritrea_presidency import EritreaPresidencyScraper
from africapep.scraper.spiders.eswatini_presidency import EswatiniPresidencyScraper
from africapep.scraper.spiders.gabon_presidency import GabonPresidencyScraper
from africapep.scraper.spiders.guinea_presidency import GuineaPresidencyScraper
from africapep.scraper.spiders.guineabissau_presidency import GuineaBissauPresidencyScraper
from africapep.scraper.spiders.lesotho_presidency import LesothoPresidencyScraper
from africapep.scraper.spiders.liberia_presidency import LiberiaPresidencyScraper
from africapep.scraper.spiders.libya_presidency import LibyaPresidencyScraper
from africapep.scraper.spiders.madagascar_presidency import MadagascarPresidencyScraper
from africapep.scraper.spiders.mali_presidency import MaliPresidencyScraper
from africapep.scraper.spiders.mauritania_presidency import MauritaniaPresidencyScraper
from africapep.scraper.spiders.mauritius_presidency import MauritiusPresidencyScraper
from africapep.scraper.spiders.niger_presidency import NigerPresidencyScraper
from africapep.scraper.spiders.saotome_presidency import SaoTomePresidencyScraper
from africapep.scraper.spiders.seychelles_presidency import SeychellesPresidencyScraper
from africapep.scraper.spiders.somalia_presidency import SomaliaPresidencyScraper
from africapep.scraper.spiders.southsudan_presidency import SouthSudanPresidencyScraper
from africapep.scraper.spiders.sudan_presidency import SudanPresidencyScraper
from africapep.scraper.spiders.togo_presidency import TogoPresidencyScraper

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
    TanzaniaParliamentScraper,
    NamibiaParliamentScraper,
    CameroonPresidencyScraper,
    CoteDIvoireParliamentScraper,
    MalawiPresidencyScraper,
    ZambiaParliamentScraper,
    EgyptPresidencyScraper,
    MoroccoPresidencyScraper,
    BotswanaParliamentScraper,
    ZimbabweParliamentScraper,
    MozambiquePresidencyScraper,
    AngolaPresidencyScraper,
    DRCParliamentScraper,
    TunisiaPresidencyScraper,
    GambiaPresidencyScraper,
    SierraLeonePresidencyScraper,
    AlgeriaPresidencyScraper,
    BeninPresidencyScraper,
    BurkinaFasoPresidencyScraper,
    BurundiPresidencyScraper,
    CapeVerdePresidencyScraper,
    CARPresidencyScraper,
    ChadPresidencyScraper,
    ComorosPresidencyScraper,
    CongoPresidencyScraper,
    DjiboutiPresidencyScraper,
    EqGuineaPresidencyScraper,
    EritreaPresidencyScraper,
    EswatiniPresidencyScraper,
    GabonPresidencyScraper,
    GuineaPresidencyScraper,
    GuineaBissauPresidencyScraper,
    LesothoPresidencyScraper,
    LiberiaPresidencyScraper,
    LibyaPresidencyScraper,
    MadagascarPresidencyScraper,
    MaliPresidencyScraper,
    MauritaniaPresidencyScraper,
    MauritiusPresidencyScraper,
    NigerPresidencyScraper,
    SaoTomePresidencyScraper,
    SeychellesPresidencyScraper,
    SomaliaPresidencyScraper,
    SouthSudanPresidencyScraper,
    SudanPresidencyScraper,
    TogoPresidencyScraper,
]
